from __future__ import annotations
from pathlib import Path
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
        self.ed_img_dir.setPlaceholderText("Папка для сохранения изображений…")
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
        self.ed_vid_dir = QLineEdit(Settings.video_default_dir())
        self.ed_vid_dir.setPlaceholderText("Папка для сохранения сжатых видео…")
        btn_vid_dir = QPushButton("Выбрать…")
        row_vid_dir.addWidget(QLabel("Папка:"))
        row_vid_dir.addWidget(self.ed_vid_dir, 1)
        row_vid_dir.addWidget(btn_vid_dir)
        vid_lay.addLayout(row_vid_dir)

        layout.addWidget(grp_vid)

        grp_aud = QGroupBox("Аудио — значения по умолчанию")
        aud_lay = QFormLayout(grp_aud)

        aud_dir_row = QHBoxLayout()
        self.ed_aud_dir = QLineEdit(Settings.audio_default_dir())
        self.ed_aud_dir.setPlaceholderText("Папка для сохранения аудио…")
        btn_aud_dir = QPushButton("Выбрать…")
        aud_dir_row.addWidget(self.ed_aud_dir, 1)
        aud_dir_row.addWidget(btn_aud_dir)
        aud_lay.addRow(QLabel("Папка:"), aud_dir_row)

        self.cmb_aud_codec = QComboBox()
        self.cmb_aud_codec.addItems(["Opus", "AAC", "MP3", "FLAC"])
        name_map = {"opus": "Opus", "aac": "AAC", "mp3": "MP3", "flac": "FLAC"}
        self.cmb_aud_codec.setCurrentText(name_map.get(Settings.audio_default_codec(), "Opus"))
        aud_lay.addRow(QLabel("Формат по умолчанию:"), self.cmb_aud_codec)

        layout.addWidget(grp_aud)

        grp_pdf = QGroupBox("PDF — значения по умолчанию")
        pdf_lay = QVBoxLayout(grp_pdf)

        row_pdf_dir = QHBoxLayout()
        self.ed_pdf_dir = QLineEdit(Settings.pdf_default_dir())
        self.ed_pdf_dir.setPlaceholderText("Папка для PDF-операций…")
        btn_pdf_dir = QPushButton("Выбрать…")
        row_pdf_dir.addWidget(QLabel("Папка:"))
        row_pdf_dir.addWidget(self.ed_pdf_dir, 1)
        row_pdf_dir.addWidget(btn_pdf_dir)
        pdf_lay.addLayout(row_pdf_dir)

        layout.addWidget(grp_pdf)

        grp_tools = QGroupBox("Внешние утилиты и OCR")
        tools = QFormLayout(grp_tools)

        tools_row_so = QHBoxLayout()
        self.ed_soffice = QLineEdit(Settings.path_soffice())
        self.ed_soffice.setPlaceholderText("Путь к soffice (LibreOffice), если не в PATH…")
        btn_soffice = QPushButton("Найти…")
        tools_row_so.addWidget(self.ed_soffice, 1)
        tools_row_so.addWidget(btn_soffice)
        tools.addRow(QLabel("LibreOffice:"), tools_row_so)

        tools_row_gs = QHBoxLayout()
        self.ed_gs = QLineEdit(Settings.path_ghostscript())
        self.ed_gs.setPlaceholderText("Путь к gs/gswin64c, если не в PATH…")
        btn_gs = QPushButton("Найти…")
        tools_row_gs.addWidget(self.ed_gs, 1)
        tools_row_gs.addWidget(btn_gs)
        tools.addRow(QLabel("Ghostscript:"), tools_row_gs)

        self.ed_ocr_lang = QLineEdit(Settings.ocr_lang_default())
        tools.addRow(QLabel("Язык OCR по умолчанию:"), self.ed_ocr_lang)

        layout.addWidget(grp_tools)
        layout.addStretch(1)

        btn_img_dir.clicked.connect(self._choose_img_dir)
        self.ed_img_dir.textChanged.connect(Settings.set_images_default_dir)
        self.cb_strip_meta.toggled.connect(Settings.set_images_strip_meta)

        btn_vid_dir.clicked.connect(self._choose_vid_dir)
        self.ed_vid_dir.textChanged.connect(Settings.set_video_default_dir)

        btn_aud_dir.clicked.connect(self._choose_aud_dir)
        self.ed_aud_dir.textChanged.connect(Settings.set_audio_default_dir)
        self.cmb_aud_codec.currentTextChanged.connect(lambda t: Settings.set_audio_default_codec(t.lower()))

        btn_pdf_dir.clicked.connect(self._choose_pdf_dir)
        self.ed_pdf_dir.textChanged.connect(Settings.set_pdf_default_dir)

        btn_soffice.clicked.connect(self._choose_soffice)
        btn_gs.clicked.connect(self._choose_gs)
        self.ed_soffice.textChanged.connect(Settings.set_path_soffice)
        self.ed_gs.textChanged.connect(Settings.set_path_ghostscript)
        self.ed_ocr_lang.textChanged.connect(Settings.set_ocr_lang_default)


    def _choose_img_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Папка для изображений", self.ed_img_dir.text().strip())
        if d:
            self.ed_img_dir.setText(d)

    def _choose_vid_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Папка для видео", self.ed_vid_dir.text().strip())
        if d:
            self.ed_vid_dir.setText(d)

    def _choose_aud_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Папка для аудио", self.ed_aud_dir.text().strip())
        if d:
            self.ed_aud_dir.setText(d)

    def _choose_pdf_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Папка для PDF", self.ed_pdf_dir.text().strip())
        if d:
            self.ed_pdf_dir.setText(d)

    def _choose_soffice(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Указать soffice (LibreOffice)", "", "Все файлы (*)")
        if fn:
            self.ed_soffice.setText(fn)

    def _choose_gs(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Указать Ghostscript (gs/gswin64c)", "", "Все файлы (*)")
        if fn:
            self.ed_gs.setText(fn)
