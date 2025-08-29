from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel,
    QListWidget, QPushButton, QHBoxLayout
)
from PyQt6.QtCore import QDateTime, Qt

class HistoryTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        self.empty_lbl = QLabel("Пока вы не производили никаких действий.")
        self.list = QListWidget()
        self.list.hide()

        self.list.setWordWrap(True)
        self.list.setTextElideMode(Qt.TextElideMode.ElideNone)
        self.list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.list.setResizeMode(self.list.ResizeMode.Adjust)

        btn_row = QHBoxLayout()
        self.btn_clear = QPushButton("Очистить историю")
        btn_row.addWidget(self.btn_clear)
        btn_row.addStretch(1)

        layout.addWidget(self.empty_lbl)
        layout.addWidget(self.list)
        layout.addLayout(btn_row)

        self.btn_clear.clicked.connect(self.clear_history)

    def add_entry(self, text: str):
        ts = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")
        self.empty_lbl.hide()
        self.list.show()

        idx = self.list.count() + 1
        line = f"{idx}. [{ts}]\n{text}"

        self.list.addItem(line)
        self.list.scrollToBottom()

    def clear_history(self):
        self.list.clear()
        self.list.hide()
        self.empty_lbl.show()
