from PyQt6.QtWidgets import QDialog, QVBoxLayout, QProgressBar, QPushButton
from PyQt6.QtCore import pyqtSignal, Qt

class SafeProgressDialog(QDialog):
    canceled = pyqtSignal()

    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)
        self.setMinimumWidth(420)

        self.bar = QProgressBar(self)
        self.bar.setRange(0, 100)
        self.btn = QPushButton("Отмена", self)
        self.btn.clicked.connect(self.canceled.emit)

        lay = QVBoxLayout(self)
        lay.addWidget(self.bar)
        lay.addWidget(self.btn)

    def setValue(self, v: int):
        self.bar.setValue(v)
