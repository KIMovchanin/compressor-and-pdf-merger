from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
)

class VideoTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.empty_lbl = QLabel("Здесь появится функционал позже.")
        layout.addWidget(self.empty_lbl)