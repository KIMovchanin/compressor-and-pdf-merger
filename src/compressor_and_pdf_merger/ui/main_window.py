from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QTabWidget,
    QVBoxLayout, QLabel
)
from .tab_history import HistoryTab
from .tab_image import ImageTab
from .tab_settings import SettingsTab
from .tab_pdf import PDFTab
from .tab_audio import AudioTab
from .tab_video import VideoTab
from compressor_and_pdf_merger.services.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compressor & PDF Merger")
        self.resize(800, 600)

        geo = Settings.window_geometry()
        if geo:
            self.restoreGeometry(geo)

        tabs = QTabWidget()
        self.setCentralWidget(tabs)

        self.pdf_tab = PDFTab()
        self.image_tab = ImageTab()
        self.video_tab = VideoTab()
        self.audio_tab = AudioTab()
        self.history_tab = HistoryTab()
        self.settings_tab = SettingsTab()

        tabs.addTab(self.pdf_tab, "PDF")
        tabs.addTab(self.image_tab, "Фото")
        tabs.addTab(self.video_tab, "Видео")
        tabs.addTab(self.audio_tab, "Аудио")
        tabs.addTab(self.history_tab, "История")
        tabs.addTab(self.settings_tab, "Настройки")

        self.image_tab.entry_logged.connect(self.history_tab.add_entry)
        self.video_tab.entry_logged.connect(self.history_tab.add_entry)

    def closeEvent(self, e):
        Settings.set_window_geometry(self.saveGeometry())
        super().closeEvent(e)