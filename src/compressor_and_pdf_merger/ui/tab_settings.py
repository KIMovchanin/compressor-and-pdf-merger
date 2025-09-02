from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QHBoxLayout, QFileDialog, QGroupBox, QComboBox, QFormLayout
)
from compressor_and_pdf_merger.services.settings import Settings


class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        grp_img = QGroupBox("Фото — значения по умолчанию")
        img_lay = QVBoxLayout(grp_img)

        row_img_dir = QHBoxLayout()
        self.ed_img_dir = QLineEdit(Settings.images_default_dir())
        self.ed_img_dir.setPlaceholderText("Папка для сохранения изображений...")
        btn_img_dir = QPushButton("Выбрать…")
        row_img_dir.addWidget(QLabel("Папка:"))
        row_img_dir.addWidget(self.ed_img_dir, 1)
        row_img_dir.addWidget(btn_img_dir)
        img_lay.addLayout(row_img_dir)

        self.cb_strip_meta = QCheckBox("Удалять метаданные (EXIF)")
        self.cb_strip_meta.setChecked(Settings.images_strip_meta())
        img_lay.addWidget(self.cb_strip_meta)

        layout.addWidget(grp_img)

        grp_vid = QGroupBox("Видео — значения по умолчанию")
        vid_lay = QVBoxLayout(grp_vid)

        row_vid_dir = QHBoxLayout()
        self.ed_vid_dir = QLineEdit(getattr(Settings, "video_default_dir", lambda: "")())
        self.ed_vid_dir.setPlaceholderText("Папка для сохранения сжатых видео...")
        btn_vid_dir = QPushButton("Выбрать…")
        row_vid_dir.addWidget(QLabel("Папка:"))
        row_vid_dir.addWidget(self.ed_vid_dir, 1)
        row_vid_dir.addWidget(btn_vid_dir)
        vid_lay.addLayout(row_vid_dir)

        layout.addWidget(grp_vid)

        grp_aud = QGroupBox("Аудио — значения по умолчанию")
        aud_lay = QFormLayout(grp_aud)

        aud_dir_row = QHBoxLayout()
        self.ed_aud_dir = QLineEdit(getattr(Settings, "audio_default_dir", lambda: "")())
        self.ed_aud_dir.setPlaceholderText("Папка для сохранения аудио...")
        btn_aud_dir = QPushButton("Выбрать…")
        aud_dir_row.addWidget(self.ed_aud_dir, 1)
        aud_dir_row.addWidget(btn_aud_dir)
        aud_lay.addRow(QLabel("Папка:"), aud_dir_row)

        self.cmb_aud_codec = QComboBox()
        self.cmb_aud_codec.addItems(["Opus", "AAC", "MP3", "FLAC"])
        cur_codec = getattr(Settings, "audio_default_codec", lambda: "opus")()
        name_map = {"opus": "Opus", "aac": "AAC", "mp3": "MP3", "flac": "FLAC"}
        self.cmb_aud_codec.setCurrentText(name_map.get(cur_codec, "Opus"))
        aud_lay.addRow(QLabel("Формат по умолчанию:"), self.cmb_aud_codec)

        layout.addWidget(grp_aud)
        layout.addStretch(1)

        btn_img_dir.clicked.connect(self._choose_img_dir)
        self.ed_img_dir.textChanged.connect(Settings.set_images_default_dir)
        self.cb_strip_meta.toggled.connect(Settings.set_images_strip_meta)

        btn_vid_dir.clicked.connect(self._choose_vid_dir)
        if hasattr(Settings, "set_video_default_dir"):
            self.ed_vid_dir.textChanged.connect(Settings.set_video_default_dir)

        btn_aud_dir.clicked.connect(self._choose_aud_dir)
        if hasattr(Settings, "set_audio_default_dir"):
            self.ed_aud_dir.textChanged.connect(Settings.set_audio_default_dir)
        if hasattr(Settings, "set_audio_default_codec"):
            self.cmb_aud_codec.currentTextChanged.connect(
                lambda t: Settings.set_audio_default_codec(t.lower())
            )


    def _choose_img_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Папка для изображений", self.ed_img_dir.text().strip()
        )
        if d:
            self.ed_img_dir.setText(d)


    def _choose_vid_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Папка для видео", self.ed_vid_dir.text().strip()
        )
        if d:
            self.ed_vid_dir.setText(d)


    def _choose_aud_dir(self):
        d = QFileDialog.getExistingDirectory(
            self, "Папка для аудио", self.ed_aud_dir.text().strip()
        )
        if d:
            self.ed_aud_dir.setText(d)
