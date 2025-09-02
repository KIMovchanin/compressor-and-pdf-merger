from __future__ import annotations
from pathlib import Path
from typing import Callable, Optional
from os.path import isdir
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QFileDialog,
    QGroupBox, QSlider, QLabel, QComboBox, QLineEdit, QMessageBox,
    QSpinBox, QFormLayout, QCheckBox
)
from compressor_and_pdf_merger.services.video import (
    compress_video_crf,
    probe_video,
)
from compressor_and_pdf_merger.storage import db
from compressor_and_pdf_merger.services.safe_progress import SafeProgressDialog

from compressor_and_pdf_merger.services.settings import Settings


class VideoTab(QWidget):
    entry_logged = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()

        self._timer: Optional[QTimer] = None
        self._progress = None

        root = QVBoxLayout(self)

        grp = QGroupBox("Сжать (CRF)")
        g = QVBoxLayout()

        # CRF
        row_crf = QHBoxLayout()
        self.sld_crf = QSlider(Qt.Orientation.Horizontal)
        self.sld_crf.setRange(18, 32)
        self.sld_crf.setValue(30)
        self.lbl_crf = QLabel(f"CRF: {self.sld_crf.value()}")
        self.sld_crf.valueChanged.connect(lambda v: self.lbl_crf.setText(f"CRF: {v}"))
        row_crf.addWidget(self.sld_crf, 1)
        row_crf.addWidget(self.lbl_crf)
        g.addLayout(row_crf)

        # Preset
        row_preset = QHBoxLayout()
        self.cmb_preset = QComboBox()
        self.cmb_preset.addItems([
            "ultrafast", "superfast", "veryfast", "faster",
            "fast", "medium", "slow", "slower", "veryslow"
        ])
        self.cmb_preset.setCurrentText("medium")
        row_preset.addWidget(QLabel("Preset:"))
        row_preset.addWidget(self.cmb_preset)
        g.addLayout(row_preset)

        # Codec
        row_codec = QHBoxLayout()
        self.cmb_codec = QComboBox()
        self.cmb_codec.addItems(["H.264", "H.265"])
        self.cmb_codec.setCurrentText("H.264")
        row_codec.addWidget(QLabel("Кодек:"))
        row_codec.addWidget(self.cmb_codec)
        g.addLayout(row_codec)

        grp.setLayout(g)
        root.addWidget(grp)

        adv = QGroupBox("Дополнительные параметры")
        form = QFormLayout()

        # FPS
        self.cb_fps = QCheckBox("Задать FPS")
        self.sp_fps = QSpinBox()
        self.sp_fps.setRange(1, 300)
        self.sp_fps.setValue(24)
        self.sp_fps.setEnabled(False)  # блокировано, пока галки нет
        self.cb_fps.toggled.connect(self.sp_fps.setEnabled)
        form.addRow(self.cb_fps, self.sp_fps)

        # p
        self.cb_p = QCheckBox("Целевая высота (p)")
        self.sp_p = QSpinBox()
        self.sp_p.setRange(10, 4000)
        self.sp_p.setSingleStep(10)
        self.sp_p.setValue(480)
        self.sp_p.setEnabled(False)

        # %
        self.cb_scale = QCheckBox("Масштаб, % от оригинала")
        self.sp_scale = QSpinBox()
        self.sp_scale.setRange(1, 100)
        self.sp_scale.setValue(65)
        self.sp_scale.setEnabled(False)

        self.cb_p.toggled.connect(self.sp_p.setEnabled)
        self.cb_scale.toggled.connect(self.sp_scale.setEnabled)

        def _toggle_p(v: bool):
            if v:
                if self.cb_scale.isChecked():
                    self.cb_scale.setChecked(False)
                self.sp_scale.setEnabled(False)

        def _toggle_scale(v: bool):
            if v:
                if self.cb_p.isChecked():
                    self.cb_p.setChecked(False)
                self.sp_p.setEnabled(False)

        self.cb_p.toggled.connect(_toggle_p)
        self.cb_scale.toggled.connect(_toggle_scale)

        form.addRow(self.cb_p, self.sp_p)
        form.addRow(self.cb_scale, self.sp_scale)

        adv.setLayout(form)
        root.addWidget(adv)

        row_btns = QHBoxLayout()
        self.btn_add = QPushButton("Добавить видео")
        self.btn_remove = QPushButton("Удалить выбранное")
        self.btn_clear = QPushButton("Очистить список")
        row_btns.addWidget(self.btn_add)
        row_btns.addWidget(self.btn_remove)
        row_btns.addWidget(self.btn_clear)
        root.addLayout(row_btns)

        self.list = QListWidget()
        root.addWidget(self.list)

        out_row = QHBoxLayout()
        self.ed_out = QLineEdit()
        self.ed_out.setPlaceholderText("Папка для сохранения...")
        self.btn_out = QPushButton("Выбрать")
        out_row.addWidget(self.ed_out, 1)
        out_row.addWidget(self.btn_out)
        root.addLayout(out_row)

        if Settings and hasattr(Settings, "video_default_dir"):
            default_dir = Settings.video_default_dir() or ""
            if default_dir and not self.ed_out.text().strip():
                self.ed_out.setText(default_dir)

        self.btn_run = QPushButton("Сжать")
        root.addWidget(self.btn_run)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_remove.clicked.connect(self._on_remove)
        self.btn_clear.clicked.connect(self.list.clear)
        self.btn_out.clicked.connect(self._on_choose_out)
        self.btn_run.clicked.connect(self._on_run)  # синхронный запуск одного файла

        for cb, sp in [(self.cb_fps, self.sp_fps), (self.cb_p, self.sp_p), (self.cb_scale, self.sp_scale)]:
            sp.setEnabled(cb.isChecked())


    def _set_controls_enabled(self, enabled: bool) -> None:
        for w in (
            self.sld_crf, self.cmb_preset, self.cmb_codec,
            self.cb_fps, self.sp_fps,
            self.cb_p, self.sp_p,
            self.cb_scale, self.sp_scale,
            self.btn_add, self.btn_remove, self.btn_clear,
            self.ed_out, self.btn_out, self.btn_run, self.list
        ):
            w.setEnabled(enabled)


    def _selected_files(self) -> list[str]:
        return [self.list.item(i).text() for i in range(self.list.count())]


    def _get_files_and_outdir(self) -> tuple[list[str], str] | None:
        files = self._selected_files()
        if not files:
            QMessageBox.warning(self, "Нет файлов", "Добавьте хотя бы один файл.")
            return None
        out_dir = self.ed_out.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "Нет папки", "Выберите папку для сохранения.")
            return None
        if not isdir(out_dir):
            QMessageBox.warning(self, "Папка не найдена", "Указанная папка не существует.")
            return None
        return files, out_dir


    @staticmethod
    def _title_to_action(title: str) -> str:
        if "CRF" in title or "Сжатие" in title:
            return "сжатие (CRF)"
        return title.lower()


    def _show_result(self, title: str, ok: list[str], fail: list[str]) -> None:
        msg = [f"Успешно: {len(ok)}"]
        if fail:
            msg.append(f"Ошибок: {len(fail)}")
            msg.extend(["", "Проблемные:", *fail[:5]])
        QMessageBox.information(self, title, "\n".join(msg))


    def _handle_success(self, title: str, log_template: str, src: str, outp: str) -> None:
        self.entry_logged.emit(log_template.format(name=Path(src).name, out=outp))
        db.add_history(
            tab="Видео",
            action=self._title_to_action(title),
            src_name=Path(src).name,
            out_path=outp
        )


    def _log_and_emit(self, text: str, src_name: str, out_path: str) -> None:
        db.add_history(tab="Видео", action="Сжатие (CRF)", src_name=src_name, out_path=out_path)
        self.entry_logged.emit(text)


    def _update_limits_from_files(self) -> None:
        files = self._selected_files()
        if not files:
            return
        try:
            infos = [probe_video(f) for f in files]
            fps_vals = [i.fps for i in infos if getattr(i, "fps", 0) and i.fps > 0]
            if fps_vals:
                max_fps_allowed = max(1, int(min(fps_vals)))
                self.sp_fps.setMaximum(max_fps_allowed)
                if self.sp_fps.value() > max_fps_allowed:
                    self.sp_fps.setValue(max_fps_allowed)
            heights = [i.height for i in infos if getattr(i, "height", 0)]
            if heights:
                max_h_allowed = int(min(heights))
                self.sp_p.setMaximum(max_h_allowed)
                if self.sp_p.value() > max_h_allowed:
                    self.sp_p.setValue(max_h_allowed)
        except Exception as e:
            QMessageBox.warning(self, "Предупреждение", f"Не удалось прочитать характеристики видео:\n{e}")


    def _on_add(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Выбрать видео", "",
            "Видео (*.mp4 *.mov *.mkv *.avi *.webm *.m4v)"
        )
        for f in files:
            self.list.addItem(f)
        if files:
            self._update_limits_from_files()


    def _on_remove(self):
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))
        self._update_limits_from_files()


    def _on_choose_out(self):
        d = QFileDialog.getExistingDirectory(self, "Куда сохранить?", self.ed_out.text() or "")
        if d:
            self.ed_out.setText(d)
            if Settings and hasattr(Settings, "set_video_default_dir"):
                Settings.set_video_default_dir(d)


    def _on_run(self):
        data = self._get_files_and_outdir()
        if not data:
            return
        files, out_dir = data

        crf = int(self.sld_crf.value())
        preset = self.cmb_preset.currentText()
        codec = "h265" if self.cmb_codec.currentText().lower().startswith("h.265") else "h264"

        target_fps = self.sp_fps.value() if self.cb_fps.isChecked() else None
        target_height_p = self.sp_p.value() if self.cb_p.isChecked() else None
        scale_percent = self.sp_scale.value() if self.cb_scale.isChecked() else None

        try:
            outp = compress_video_crf(
                files[0], out_dir,
                crf=crf, preset=preset, codec=codec,
                audio_bitrate="128k", strip_metadata=True,
                target_fps=target_fps,
                target_height_p=target_height_p,
                scale_percent=scale_percent,
                ensure_not_larger=True
            )

            name = Path(files[0]).name
            log_template = 'Из вкладки «Видео»: CRF={}, preset={}, codec={}, {}{}{}"{{name}}" -> "{{out}}"'.format(
                crf, preset, self.cmb_codec.currentText(),
                f'FPS={target_fps} ' if target_fps else '',
                f'Height={target_height_p}p ' if target_height_p else '',
                f'Scale={scale_percent}% ' if (scale_percent and not target_height_p) else ''
            )
            text = log_template.format(name=name, out=outp)
            self._log_and_emit(text, name, outp)

            QMessageBox.information(self, "Готово", text)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


    def _run_batch(self, title: str, files: list[str], func: Callable[[str], str], log_template: str) -> None:
        if not files:
            self._show_result(title, [], [])
            return
        if SafeProgressDialog is None:
            QMessageBox.warning(self, "Недоступно", "SafeProgressDialog не найден.")
            return

        self._set_controls_enabled(False)
        self._progress = SafeProgressDialog(title, self)
        self._progress.setValue(0)
        self._progress.show()

        import threading, queue
        q: queue.Queue = queue.Queue()
        ok, fail = [], []

        def worker():
            total = len(files) or 1
            for i, f in enumerate(files, start=1):
                try:
                    outp = func(f)
                    q.put(("done", f, outp))
                except Exception as e:
                    q.put(("fail", f, str(e)))
                q.put(("progress", int(i * 100 / total)))
            q.put(("finished",))

        self._cancel = False
        self._progress.canceled.connect(lambda: setattr(self, "_cancel", True))
        t = threading.Thread(target=worker, daemon=True)
        t.start()

        self._timer = QTimer(self)
        self._timer.setInterval(50)

        def pump():
            import queue as _q
            try:
                while True:
                    kind, *rest = q.get_nowait()
                    if kind == "progress":
                        self._progress.setValue(rest[0])
                    elif kind == "done":
                        src, outp = rest
                        ok.append(outp)
                        try:
                            self._handle_success(title, log_template, src, outp)
                        except Exception as e:
                            fail.append(f"{src} - postprocess: {e}")
                    elif kind == "fail":
                        src, err = rest
                        fail.append(f"{src} - {err}")
                    elif kind == "finished":
                        self._timer.stop()
                        self._progress.close()
                        self._set_controls_enabled(True)
                        self._show_result(title, ok, fail)
                        return
            except _q.Empty:
                pass

        self._timer.timeout.connect(pump)
        self._timer.start()
