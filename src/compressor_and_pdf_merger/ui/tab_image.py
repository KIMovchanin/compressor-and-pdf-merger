from functools import partial

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QRadioButton,
    QHBoxLayout, QSlider, QLabel, QPushButton,
    QListWidget, QFileDialog, QMessageBox,
    QLineEdit, QInputDialog, QCheckBox, QDialog,
    QComboBox, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
import os
from compressor_and_pdf_merger.services.images import compress_image, resize_image, ConvertOptions, convert_image_format
from pathlib import Path
from compressor_and_pdf_merger.storage import db
from typing import Callable


class ImageTab(QWidget):
    entry_logged = pyqtSignal(str)

    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        group = QGroupBox("Режим сжатия")
        group_layout = QVBoxLayout()

        self.rb_max = QRadioButton("Максимальное сжатие")
        self.rb_min = QRadioButton("Оптимальная потеря качества")
        self.rb_custom = QRadioButton("Свои настройки")
        self.rb_min.setChecked(True)

        group_layout.addWidget(self.rb_max)
        group_layout.addWidget(self.rb_min)
        group_layout.addWidget(self.rb_custom)

        slider_row = QHBoxLayout()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        # 5 - minimum changes
        # 95 - maximum changes
        self.slider.setValue(20)
        self.slider.setEnabled(False)
        self.lbl_value = QLabel("Процент сжатия: 20%")

        slider_row.addWidget(self.slider)
        slider_row.addWidget(self.lbl_value)
        group_layout.addLayout(slider_row)

        group.setLayout(group_layout)
        layout.addWidget(group)

        btn_row = QHBoxLayout()

        self.btn_add = QPushButton("Добавить файлы")
        self.btn_remove = QPushButton("Удалить выбранные")
        self.btn_clear = QPushButton("Очистить список")

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_remove)
        btn_row.addWidget(self.btn_clear)

        layout.addLayout(btn_row)

        self.file_list = QListWidget()
        layout.addWidget(self.file_list)

        out_row = QHBoxLayout()
        self.out_dir = QLineEdit()
        self.out_dir.setPlaceholderText("Папка для сохранения...")
        btn_browse = QPushButton("Выбрать")
        out_row.addWidget(self.out_dir)
        out_row.addWidget(btn_browse)
        layout.addLayout(out_row)

        self.cb_strip_meta = QCheckBox("Удалить мета-данные (геопозиция, дата и т.п.)")
        layout.addWidget(self.cb_strip_meta)

        self.btn_compress = QPushButton("Сжать")
        layout.addWidget(self.btn_compress)

        self.btn_resize = QPushButton("Изменить размер")
        layout.addWidget(self.btn_resize)

        self.btn_format = QPushButton("Изменить формат")
        layout.addWidget(self.btn_format)

        self.rb_custom.toggled.connect(self.slider.setEnabled)
        self.slider.valueChanged.connect(lambda text: self.lbl_value.setText(f"Процент сжатия: {text}%"))
        self.btn_add.clicked.connect(self.on_add_files)
        self.btn_remove.clicked.connect(self.on_remove_selected)
        self.btn_clear.clicked.connect(self.file_list.clear)
        self.btn_compress.clicked.connect(self.on_compress_clicked)
        btn_browse.clicked.connect(self.on_choose_out_dir)
        self.btn_resize.clicked.connect(self.on_resize_clicked)
        self.rb_max.toggled.connect(self._sync_slider_state)
        self.rb_min.toggled.connect(self._sync_slider_state)
        self.rb_custom.toggled.connect(self._sync_slider_state)
        self._sync_slider_state()
        self.btn_format.clicked.connect(self.on_format_clicked)


    def on_add_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выбрать изображение",
            "",
            "Изображения (*.jpg *.jpeg *.png *.bmp *.webp *.tiff)"
        )

        for f in files:
            self.file_list.addItem(f)


    def on_remove_selected(self):
        for item in self.file_list.selectedItems():
            self.file_list.takeItem(self.file_list.row(item))


    def selected_files(self) -> list[str]:
        return [self.file_list.item(i).text() for i in range(self.file_list.count())]


    def current_percent(self) -> int:
        if self.rb_max.isChecked():
            return 100
        if self.rb_min.isChecked():
            return 20
        return self.slider.value()


    def current_mode(self) -> str:
        if self.rb_max.isChecked():
            return "max"
        if self.rb_min.isChecked():
            return "min"
        return "custom"


    def _sync_slider_state(self):
        is_custom = self.rb_custom.isChecked()
        self.slider.setEnabled(is_custom)
        if not is_custom:
            self.slider.setValue(20 if self.rb_min.isChecked() else 100)
        self.lbl_value.setText(f"Процент сжатия: {self.slider.value()}%")


    def _get_files_and_outdir(self) -> tuple[list[str], str] | None:
        files = self.selected_files()
        if not files:
            QMessageBox.warning(self, "Нет файлов", "Добавьте хотя бы один файл.")
            return None

        out_dir = self.out_dir.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "Нет папки", "Выберите папку для сохранения.")
            return None

        if not os.path.isdir(out_dir):
            QMessageBox.warning(self, "Папка не найдена", "Указанная папка не существует.")
            return None

        return files, out_dir


    def _apply_to_files(self, files: list[str], func, on_success=None) -> tuple[list[str], list[str]]:
        ok, fail = [], []
        for f in files:
            try:
                out_path = func(f)
                ok.append(out_path)
                if on_success:
                    on_success(f, out_path)
            except Exception as e:
                fail.append(f"{f} — {e}")
        return ok, fail


    def _show_result(self, title: str, ok: list[str], fail: list[str]) -> None:
        msg = [f"Успешно: {len(ok)}"]
        if fail:
            msg.append(f"Ошибок: {len(fail)}")
            msg.extend(["", "Проблемные:", *fail[:5]])
        QMessageBox.information(self, title, "\n".join(msg))


    def _ask_animated_confirm(self) -> bool:
        reply = QMessageBox.question(
            self,
            "Анимация",
            "Выбран анимированный файл. Обработать только первый кадр?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        return reply == QMessageBox.StandardButton.Yes


    @staticmethod
    def title_to_action(title: str) -> str:
        if "Сжатие" in title: return "сжатие"
        if "размера" in title: return "изменение размера"
        if "формата" in title: return "изменение формата"
        return title.lower()


    def _handle_success(self, title: str, log_template: str, src: str, outp: str):
        self.entry_logged.emit(log_template.format(name=Path(src).name, out=outp))

        db.add_history(
            tab="Фото",
            action=self.title_to_action(title),
            src_name=Path(src).name,
            out_path=outp,
        )


    def _run_batch(self, title: str, files: list[str], func: Callable[[str], str], log_template: str) -> None:
        on_success = partial(self._handle_success, title, log_template)
        ok, fail = self._apply_to_files(files, func, on_success=on_success)
        self._show_result(title, ok, fail)


    def on_compress_clicked(self):
        data = self._get_files_and_outdir()
        if not data:
            return
        files, out_dir = data
        percent = self.current_percent()
        strip = self.cb_strip_meta.isChecked()

        self._run_batch(
            "Сжатие завершено",
            files,
            lambda f: compress_image(f, out_dir, percent, strip_metadata=strip),
            'Из вкладки «Фото»: сжатие "{name}". Сохранено в: "{out}".'
        )


    def on_choose_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Куда сохранить?")
        if d:
            self.out_dir.setText(d)


    def on_resize_clicked(self):
        data = self._get_files_and_outdir()
        if not data:
            return
        files, out_dir = data

        percent, ok = QInputDialog.getInt(
            self, "Масштаб", "Во сколько процентов от исходника?", 50, 1, 1000, 1
        )
        if not ok:
            return

        strip = self.cb_strip_meta.isChecked()

        self._run_batch(
            "Изменение размера завершено",
            files,
            lambda f: resize_image(f, out_dir, scale_percent=percent, strip_metadata=strip),
            'Из вкладки «Фото»: изменение размера "{name}". Сохранено в: "{out}".'
        )


    def on_format_clicked(self):
        data = self._get_files_and_outdir()
        if not data:
            return
        files, out_dir = data

        dlg = ImageFormatDialog(self, files_count=len(files))
        if dlg.exec() != QDialog.DialogCode.Accepted:
            return

        target = dlg.selected_format()
        use_compress = dlg.apply_compression()
        percent = self.current_percent() if use_compress else None
        strip = self.cb_strip_meta.isChecked()

        opts = ConvertOptions(
            target=target,
            apply_percent=percent,
            strip_metadata=strip,
        )

        self._run_batch(
            "Изменение формата завершено",
            files,
            lambda f: convert_image_format(f, out_dir, opts, on_animated_confirm=self._ask_animated_confirm),
            'Из вкладки «Фото»: изменение формата "{name}". Сохранено в: "{out}".'
        )

class ImageFormatDialog(QDialog):
    def __init__(self, parent=None, files_count: int = 0):
        super().__init__(parent)
        self.setWindowTitle("Изменить формат")
        layout = QVBoxLayout(self)

        self.combo = QComboBox()
        items = [("JPEG (.jpg)", "jpeg"), ("PNG (.png)", "png"), ("WebP (.webp)", "webp"), ("TIFF (.tiff)", "tiff")]
        for text, data in items:
            self.combo.addItem(text, userData=data)
        layout.addWidget(QLabel(f"Будет обработано файлов: {files_count}"))
        layout.addWidget(QLabel("Формат назначения:"))
        layout.addWidget(self.combo)

        self.cb_apply_compress = QCheckBox("Применить текущие настройки сжатия")
        self.cb_apply_compress.setChecked(False)
        layout.addWidget(self.cb_apply_compress)

        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def selected_format(self) -> str:
        # "jpeg" "png" "webp" "tiff"
        return self.combo.currentData()

    def apply_compression(self) -> bool:
        return self.cb_apply_compress.isChecked()
