from __future__ import annotations
from pathlib import Path
from typing import Callable
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QPushButton, QFileDialog,
    QGroupBox, QSlider, QLabel, QComboBox, QLineEdit, QMessageBox,
    QCheckBox, QSpinBox, QFormLayout, QProgressDialog
)
from compressor_and_pdf_merger.services.video import compress_video_crf
from compressor_and_pdf_merger.storage import db
from compressor_and_pdf_merger.ui.worker import BatchWorker
from os.path import isdir


class VideoTab(QWidget):
    entry_logged = pyqtSignal(str)

    def __init__(self) -> None:
        super().__init__()
        self._thread: QThread | None = None
        self._worker: BatchWorker | None = None
        self._progress: QProgressDialog | None = None

        layout = QVBoxLayout(self)

        grp = QGroupBox("Сжать (CRF)")
        g = QVBoxLayout()

        row_crf = QHBoxLayout()
        self.sld_crf = QSlider(Qt.Orientation.Horizontal)
        self.sld_crf.setRange(18, 32)
        self.sld_crf.setValue(30)
        self.lbl_crf = QLabel(f"CRF: {self.sld_crf.value()}")
        self.sld_crf.valueChanged.connect(lambda v: self.lbl_crf.setText(f"CRF: {v}"))
        row_crf.addWidget(self.sld_crf)
        row_crf.addWidget(self.lbl_crf)
        g.addLayout(row_crf)

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

        row_codec = QHBoxLayout()
        self.cmb_codec = QComboBox()
        self.cmb_codec.addItems(["H.264", "H.265"])
        self.cmb_codec.setCurrentText("H.264")
        row_codec.addWidget(QLabel("Кодек:"))
        row_codec.addWidget(self.cmb_codec)
        g.addLayout(row_codec)

        grp.setLayout(g)
        layout.addWidget(grp)

        adv = QGroupBox("Дополнительные параметры")
        form = QFormLayout()

        # FPS
        self.cb_fps = QCheckBox("Задать FPS")
        self.sp_fps = QSpinBox()
        self.sp_fps.setRange(1, 300)
        self.sp_fps.setValue(24)
        self.sp_fps.setEnabled(False)
        self.cb_fps.toggled.connect(self.sp_fps.setEnabled)
        form.addRow(self.cb_fps, self.sp_fps)

        # p
        self.cb_p = QCheckBox("Целевая высота (p)")
        self.sp_p = QSpinBox()
        self.sp_p.setRange(10, 2050)
        self.sp_p.setSingleStep(10)
        self.sp_p.setValue(480)
        self.sp_p.setEnabled(False)
        self.cb_p.toggled.connect(self.sp_p.setEnabled)
        form.addRow(self.cb_p, self.sp_p)

        # scale
        self.cb_scale = QCheckBox("Масштаб, % от оригинала")
        self.sp_scale = QSpinBox()
        self.sp_scale.setRange(1, 100)
        self.sp_scale.setValue(65)
        self.sp_scale.setEnabled(False)
        self.cb_scale.toggled.connect(self.sp_scale.setEnabled)
        form.addRow(self.cb_scale, self.sp_scale)

        adv.setLayout(form)
        layout.addWidget(adv)

        btn_row = QHBoxLayout()
        self.btn_add = QPushButton("Добавить видео")
        self.btn_remove = QPushButton("Удалить выбранное")
        self.btn_clear = QPushButton("Очистить список")
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_remove)
        btn_row.addWidget(self.btn_clear)
        layout.addLayout(btn_row)

        self.list = QListWidget()
        layout.addWidget(self.list)

        out_row = QHBoxLayout()
        self.ed_out = QLineEdit()
        self.ed_out.setPlaceholderText("Папка для сохранения...")
        self.btn_out = QPushButton("Выбрать")
        out_row.addWidget(self.ed_out)
        out_row.addWidget(self.btn_out)
        layout.addLayout(out_row)

        self.btn_run = QPushButton("Сжать")
        layout.addWidget(self.btn_run)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_remove.clicked.connect(self._on_remove)
        self.btn_clear.clicked.connect(self.list.clear)
        self.btn_out.clicked.connect(self._on_choose_out)
        self.btn_run.clicked.connect(self._on_run)


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


    def _show_result(self, title: str, ok: list[str], fail: list[str]) -> None:
        msg = [f"Успешно: {len(ok)}"]
        if fail:
            msg.append(f"Ошибок: {len(fail)}")
            msg.extend(["", "Проблемные:", *fail[:5]])
        QMessageBox.information(self, title, "\n".join(msg))


    def _handle_success(self, title: str, log_template: str, src: str, outp: str) -> None:
        self.entry_logged.emit(log_template.format(name=Path(src).name, out=outp))
        db.add_history(tab="Видео", action=self._title_to_action(title), src_name=Path(src).name, out_path=outp)


    @staticmethod
    def _title_to_action(title: str) -> str:
        if "CRF" in title or "Сжатие" in title:
            return "сжатие (CRF)"
        return title.lower()


    def _on_add(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выбрать видео",
            "",
            "Видео (*.mp4 *.mov *.mkv *.avi *.webm *.m4v)"
        )
        for f in files:
            self.list.addItem(f)


    def _on_remove(self):
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))


    def _on_choose_out(self):
        d = QFileDialog.getExistingDirectory(self, "Куда сохранить?")
        if d:
            self.ed_out.setText(d)


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

        self._run_batch(
            title="Сжатие видео (CRF) завершено",
            files=files,
            func=lambda f: compress_video_crf(
                f, out_dir,
                crf=crf,
                preset=preset,
                codec=codec,
                audio_bitrate="128k",
                strip_metadata=True,
                target_fps=target_fps,
                target_height_p=target_height_p,
                scale_percent=scale_percent
            ),
            log_template='Из вкладки «Видео»: CRF={}, preset={}, codec={}, {}{}{}"{{name}}" → "{{out}}"'.format(
                crf, preset, self.cmb_codec.currentText(),
                f'FPS={target_fps} ' if target_fps else '',
                f'Height={target_height_p}p ' if target_height_p else '',
                f'Scale={scale_percent}% ' if (scale_percent and not target_height_p) else ''
            )
        )

    def _run_batch(self, title: str, files: list[str], func: Callable[[str], str], log_template: str) -> None:
        if not files:
            self._show_result(title, [], [])
            return
        if self._thread is not None:
            QMessageBox.warning(self, "Занято", "Пожалуйста, дождитесь завершения текущей операции.")
            return

        self._set_controls_enabled(False)

        self._progress = QProgressDialog(f"{title}...", "Отмена", 0, 100, self)
        self._progress.setWindowTitle(title)
        self._progress.setAutoClose(False)
        self._progress.setAutoReset(False)
        self._progress.setValue(0)

        self._thread = QThread(self)
        self._worker = BatchWorker(files, func)
        self._worker.moveToThread(self._thread)

        ok: list[str] = []
        fail: list[str] = []

        self._worker.progress.connect(self._progress.setValue)

        def on_done(src: str, outp: str):
            ok.append(outp)
            self._handle_success(title, log_template, src, outp)

        def on_fail(src: str, err: str):
            fail.append(f"{src} - {err}")

        self._worker.file_done.connect(on_done)
        self._worker.file_fail.connect(on_fail)

        def cleanup():
            if self._progress:
                self._progress.close()
            self._set_controls_enabled(True)
            self._show_result(title, ok, fail)

            if self._thread:
                self._thread.quit()
                self._thread.wait()

            if self._worker:
                self._worker.deleteLater()
            if self._thread:
                self._thread.deleteLater()

            self._worker = None
            self._thread = None
            self._progress = None

        self._worker.finished.connect(cleanup)
        self._progress.canceled.connect(self._worker.cancel)

        self._thread.started.connect(self._worker.run)
        self._thread.start()
        self._progress.show()


