from PyQt6.QtWidgets import QMainWindow, QTabWidget
from .tab_history import HistoryTab
from .tab_image import ImageTab
from .tab_settings import SettingsTab
from .tab_pdf_merge import PdfMergeTab
from .tab_pdf_compress import PdfCompressTab
from .tab_pdf_convert import PdfConvertTab
from .tab_audio import AudioTab
from .tab_video import VideoTab
from compressor_and_pdf_merger.services.settings import Settings


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compressor & PDF Merger")
        self.resize(1000, 700)

        geo = Settings.window_geometry()
        if geo:
            self.restoreGeometry(geo)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.pdf_merge_tab = PdfMergeTab()
        self.pdf_compress_tab = PdfCompressTab()
        self.pdf_convert_tab = PdfConvertTab()

        self.image_tab = ImageTab()
        self.video_tab = VideoTab()
        self.audio_tab = AudioTab()
        self.history_tab = HistoryTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.pdf_merge_tab, "PDF: объединить")
        self.tabs.addTab(self.pdf_compress_tab, "PDF: сжать")
        self.tabs.addTab(self.pdf_convert_tab, "PDF: конвертировать")
        self.tabs.addTab(self.image_tab, "Фото")
        self.tabs.addTab(self.video_tab, "Видео")
        self.tabs.addTab(self.audio_tab, "Аудио")
        self.tabs.addTab(self.history_tab, "История")
        self.tabs.addTab(self.settings_tab, "Настройки")

        self.image_tab.entry_logged.connect(self.history_tab.add_entry)
        self.video_tab.entry_logged.connect(self.history_tab.add_entry)
        self.audio_tab.entry_logged.connect(self.history_tab.add_entry)
        self.pdf_merge_tab.entry_logged.connect(self.history_tab.add_entry)
        self.pdf_compress_tab.entry_logged.connect(self.history_tab.add_entry)
        self.pdf_convert_tab.entry_logged.connect(self.history_tab.add_entry)

        self.history_tab.load_from_db()

    def closeEvent(self, e):
        Settings.set_window_geometry(self.saveGeometry())
        super().closeEvent(e)
