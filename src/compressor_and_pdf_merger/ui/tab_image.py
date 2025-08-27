from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QRadioButton,
    QHBoxLayout, QSlider, QLabel, QPushButton,
    QListWidget, QFileDialog, QMessageBox,
    QLineEdit, QInputDialog
)
from PyQt6.QtCore import Qt
import os
from compressor_and_pdf_merger.services.images import compress_image, resize_image


class ImageTab(QWidget):
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
        self.slider.setValue(65)
        self.slider.setEnabled(False)
        self.lbl_value = QLabel("Процент сжатия: 65%")

        slider_row.addWidget(self.slider)
        slider_row.addWidget(self.lbl_value)
        group_layout.addLayout(slider_row)

        group.setLayout(group_layout)
        layout.addWidget(group)

        btn_row = QHBoxLayout()

        self.btn_add = QPushButton("Добавить файлы")
        self.btn_remove = QPushButton("Удалить выбранные")
        self.btn_clear = QPushButton("Очистить список")

        layout.addWidget(self.btn_add)
        layout.addWidget(self.btn_remove)
        layout.addWidget(self.btn_clear)

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


        self.btn_compress = QPushButton("Сжать")
        layout.addWidget(self.btn_compress)

        self.btn_resize = QPushButton("Изменить размер")
        layout.addWidget(self.btn_resize)

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


    def _apply_to_files(self, files: list[str], func) -> tuple[list[str], list[str]]:
        ok, fail = [], []
        for f in files:
            try:
                out_path = func(f)
                ok.append(out_path)
            except Exception as e:
                fail.append(f"{f} — {e}")
        return ok, fail


    def _show_result(self, title: str, ok: list[str], fail: list[str]) -> None:
        msg = [f"Успешно: {len(ok)}"]
        if fail:
            msg.append(f"Ошибок: {len(fail)}")
            msg.extend(["", "Проблемные:", *fail[:5]])
        QMessageBox.information(self, title, "\n".join(msg))


    def on_compress_clicked(self):
        data = self._get_files_and_outdir()
        if not data:
            return
        files, out_dir = data

        percent = self.current_percent()

        ok, fail = self._apply_to_files(
            files,
            lambda f: compress_image(f, out_dir, percent)
        )
        self._show_result("Сжатие завершено", ok, fail)


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

        ok_list, fail = self._apply_to_files(
            files,
            lambda f: resize_image(f, out_dir, scale_percent=percent)
        )
        self._show_result("Изменение размера завершено", ok_list, fail)

