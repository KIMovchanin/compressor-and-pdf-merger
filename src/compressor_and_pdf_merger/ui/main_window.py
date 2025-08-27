from PyQt6.QtWidgets import QMainWindow, QWidget, QTabWidget, QVBoxLayout, QLabel

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Compressor & PDF Merger")
        self.resize(800, 600)

        tabs = QTabWidget()

        # pdf tab
        pdf_tab = QWidget()
        pdf_layout = QVBoxLayout()
        pdf_layout.addWidget(QLabel("Здесь будет работа с PDF"))
        pdf_tab.setLayout(pdf_layout)
        tabs.addTab(pdf_tab, "PDF")

        # image tab
        image_tab = QWidget()
        image_layout = QVBoxLayout()
        image_layout.addWidget(QLabel("Здесь будет работа с изображениями"))
        image_tab.setLayout(image_layout)
        tabs.addTab(image_tab, "Фото")

        # video tab
        video_tab = QWidget()
        video_layout = QVBoxLayout()
        video_layout.addWidget(QLabel("Здесь будет работа с видео"))
        video_tab.setLayout(video_layout)
        tabs.addTab(video_tab, "Видео")

        # audio tab
        audio_tab = QWidget()
        audio_layout = QVBoxLayout()
        audio_layout.addWidget(QLabel("Здесь будет работа с аудио"))
        audio_tab.setLayout(audio_layout)
        tabs.addTab(audio_tab, "Аудио")

        self.setCentralWidget(tabs)