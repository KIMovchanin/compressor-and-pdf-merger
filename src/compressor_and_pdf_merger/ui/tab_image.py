from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QRadioButton,
    QHBoxLayout, QSlider, QLabel, QPushButton,
    QListWidget, QFileDialog, QMessageBox,
    QLineEdit
)
from PyQt6.QtCore import Qt
import os
from compressor_and_pdf_merger.services.images import compress_image_stub

class ImageTab(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        group = QGroupBox("Режим сжатия")
        group_layout = QVBoxLayout()

        self.rb_max = QRadioButton("Максимальное сжатие")
        self.rb_min = QRadioButton("Минимальная потеря качества")
        self.rb_custom = QRadioButton("Свои настройки")
        self.rb_min.setChecked(True)

        group_layout.addWidget(self.rb_max)
        group_layout.addWidget(self.rb_min)
        group_layout.addWidget(self.rb_custom)

        slider_row = QHBoxLayout()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(45)
        self.slider.setEnabled(False)
        self.lbl_value = QLabel("Сжать на: 45%")

        slider_row.addWidget(self.slider)
        slider_row.addWidget(self.lbl_value)
        group_layout.addLayout(slider_row)

        group.setLayout(group_layout)
        layout.addWidget(group)

        btn_row = QHBoxLayout()

        self.btn_add = QPushButton("Добавить файлы…")
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
        self.out_dir.setPlaceholderText("Папка для сохранения…")
        btn_browse = QPushButton("Выбрать…")
        out_row.addWidget(self.out_dir)
        out_row.addWidget(btn_browse)
        layout.addLayout(out_row)

        self.btn_compress = QPushButton("Сжать")
        layout.addWidget(self.btn_compress)

        self.rb_custom.toggled.connect(self.slider.setEnabled)
        self.slider.valueChanged.connect(lambda text: self.lbl_value.setText(f"Сжать на: {text}%"))
        self.btn_add.clicked.connect(self.on_add_files)
        self.btn_remove.clicked.connect(self.on_remove_selected)
        self.btn_clear.clicked.connect(self.file_list.clear)
        self.btn_compress.clicked.connect(self.on_compress_clicked)
        btn_browse.clicked.connect(self.on_choose_out_dir)

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
            return 70
        if self.rb_min.isChecked():
            return 20
        return self.slider.value()

    def current_mode(self) -> str:
        if self.rb_max.isChecked():
            return "max"
        if self.rb_min.isChecked():
            return "min"
        return "custom"

    def on_compress_clicked(self):
        files = self.selected_files()
        if not files:
            QMessageBox.warning(self, "Нет файлов", "Добавьте хотя бы один файл для сжатия.")
            return

        out_dir = self.out_dir.text().strip()
        if not out_dir:
            QMessageBox.warning(self, "Нет папки", "Выберите папку для сохранения.")
            return
        if not os.path.isdir(out_dir):
            QMessageBox.warning(self, "Папка не найдена", "Указанная папка не существует.")
            return

        mode = self.current_mode()
        percent = self.current_percent()

        out_files = []
        for f in files:
            new_path = compress_image_stub(f, out_dir, percent)
            out_files.append(new_path)

        QMessageBox.information(
            self,
            "Готово",
            f"Обработано файлов: {len(out_files)}\n"
            f"Примеры:\n" + "\n".join(out_files[:5])
        )

        text = (
                f"Режим: {mode}\n"
                f"Сжать на: {percent}%\n"
                f"Куда: {out_dir}\n"
                f"Файлов: {len(files)}\n\n"
                + "\n".join(files[:10]) + ("...\n" if len(files) > 10 else "")
        )

        QMessageBox.information(self, "Предварительный запуск", text)

    def on_choose_out_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Куда сохранить?")
        if d:
            self.out_dir.setText(d)

