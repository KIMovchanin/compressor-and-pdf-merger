from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox, QHBoxLayout, QFileDialog, QGroupBox
from compressor_and_pdf_merger.services.settings import Settings

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        lay = QVBoxLayout(self)

        grp = QGroupBox("Фото: значения по умолчанию")
        g = QVBoxLayout(grp)

        row_dir = QHBoxLayout()
        self.ed_dir = QLineEdit(Settings.images_default_dir())
        self.ed_dir.setPlaceholderText("Папка для сохранения по умолчанию...")
        btn_dir = QPushButton("Выбрать...")
        row_dir.addWidget(self.ed_dir)
        row_dir.addWidget(btn_dir)
        g.addLayout(row_dir)

        self.cb_strip = QCheckBox("Удалять метаданные по умолчанию")
        self.cb_strip.setChecked(Settings.images_strip_meta())
        g.addWidget(self.cb_strip)

        lay.addWidget(grp)
        lay.addStretch(1)

        btn_dir.clicked.connect(self._choose_dir)
        self.ed_dir.textChanged.connect(Settings.set_images_default_dir)
        self.cb_strip.toggled.connect(Settings.set_images_strip_meta)

    def _choose_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Выбрать папку по умолчанию")
        if d:
            self.ed_dir.setText(d)
