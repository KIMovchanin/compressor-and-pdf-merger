from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QHBoxLayout, QFileDialog, QGroupBox
)
from compressor_and_pdf_merger.services.settings import Settings


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Photo
        grp_img = QGroupBox("Фото: значения по умолчанию")
        img_lay = QVBoxLayout(grp_img)

        row_img_dir = QHBoxLayout()
        self.ed_img_dir = QLineEdit(Settings.images_default_dir())
        self.ed_img_dir.setPlaceholderText("Папка для сохранения изображений по умолчанию...")
        btn_img_dir = QPushButton("Выбрать…")
        row_img_dir.addWidget(self.ed_img_dir, 1)
        row_img_dir.addWidget(btn_img_dir)
        img_lay.addLayout(row_img_dir)

        self.cb_strip_meta = QCheckBox("Удалять метаданные по умолчанию")
        self.cb_strip_meta.setChecked(Settings.images_strip_meta())
        img_lay.addWidget(self.cb_strip_meta)

        layout.addWidget(grp_img)

        # Video
        grp_vid = QGroupBox("Видео: значения по умолчанию")
        vid_lay = QVBoxLayout(grp_vid)

        row_vid_dir = QHBoxLayout()
        self.ed_vid_dir = QLineEdit(getattr(Settings, "video_default_dir", lambda: "")())
        self.ed_vid_dir.setPlaceholderText("Папка для сохранения сжатых видео по умолчанию...")
        btn_vid_dir = QPushButton("Выбрать…")
        row_vid_dir.addWidget(self.ed_vid_dir, 1)
        row_vid_dir.addWidget(btn_vid_dir)
        vid_lay.addLayout(row_vid_dir)

        layout.addWidget(grp_vid)

        layout.addStretch(1)

        # Photo
        btn_img_dir.clicked.connect(self._choose_img_dir)
        self.ed_img_dir.textChanged.connect(Settings.set_images_default_dir)
        self.cb_strip_meta.toggled.connect(Settings.set_images_strip_meta)

        # Video
        btn_vid_dir.clicked.connect(self._choose_vid_dir)
        if hasattr(Settings, "set_video_default_dir"):
            self.ed_vid_dir.textChanged.connect(Settings.set_video_default_dir)


    def _choose_img_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Папка для сохранения изображений по умолчанию", self.ed_img_dir.text().strip()
        )
        if d:
            self.ed_img_dir.setText(d)

    def _choose_vid_dir(self):
        current = self.ed_vid_dir.text().strip()
        d = QFileDialog.getExistingDirectory(
            self, "Папка для сохранения сжатых видео по умолчанию", current
        )
        if d:
            self.ed_vid_dir.setText(d)
