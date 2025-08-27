from __future__ import annotations

import sys
import os
from typing import List

from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QTabWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog, QLabel, QGroupBox,
    QRadioButton, QSlider, QLineEdit, QMessageBox, QStackedWidget, QToolButton,
    QStyle, QSpacerItem, QSizePolicy
)

SUPPORTED_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}
SUPPORTED_VIDEO_EXT = {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm"}
SUPPORTED_AUDIO_EXT = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac"}
SUPPORTED_PDF_EXT = {".pdf"}


def is_supported(path: str, allowed: set[str]) -> bool:
    return os.path.splitext(path)[1].lower() in allowed


class DraggableFileList(QListWidget):
    def __init__(self, allowed_ext: set[str] | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.allowed_ext = allowed_ext
        self.setMinimumHeight(180)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event: QDropEvent):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isfile(path):
                    if self.allowed_ext is None or is_supported(path, self.allowed_ext):
                        self.addItem(path)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def items(self) -> List[str]:
        return [self.item(i).text() for i in range(self.count())]

    def remove_selected(self):
        for item in self.selectedItems():
            self.takeItem(self.row(item))


class CompressionTab(QWidget):
    def __init__(self, title: str, allowed_ext: set[str]):
        super().__init__()
        self.title = title
        self.allowed_ext = allowed_ext
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        presets = QGroupBox("Режим сжатия")
        ph = QVBoxLayout(presets)

        self.rb_max = QRadioButton("Максимальное сжатие (≈60–80%)")
        self.rb_min = QRadioButton("Минимальная потеря качества")
        self.rb_custom = QRadioButton("Свои настройки")
        self.rb_min.setChecked(True)

        ph.addWidget(self.rb_max)
        ph.addWidget(self.rb_min)
        ph.addWidget(self.rb_custom)

        custom_row = QHBoxLayout()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(25)  # 25% сжатия по умолчанию
        self.slider.setEnabled(False)
        self.lbl_slider = QLabel("Сжать на: 25%")
        custom_row.addWidget(self.slider)
        custom_row.addWidget(self.lbl_slider)
        ph.addLayout(custom_row)

        self.rb_custom.toggled.connect(self.slider.setEnabled)
        self.slider.valueChanged.connect(lambda v: self.lbl_slider.setText(f"Сжать на: {v}%"))

        root.addWidget(presets)

        controls = QHBoxLayout()
        self.btn_add = QPushButton("Добавить файлы…")
        self.btn_remove = QPushButton("Удалить выбранные")
        self.btn_clear = QPushButton("Очистить список")
        controls.addWidget(self.btn_add)
        controls.addWidget(self.btn_remove)
        controls.addWidget(self.btn_clear)
        root.addLayout(controls)

        self.list_files = DraggableFileList(self.allowed_ext)
        self.list_files.setToolTip("Перетащите файлы сюда")
        root.addWidget(self.list_files)

        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Папка сохранения:"))
        self.out_dir = QLineEdit()
        self.out_dir.setPlaceholderText("не выбрано")
        btn_browse_out = QPushButton("Выбрать…")
        btn_browse_out.clicked.connect(self.choose_output_dir)
        out_row.addWidget(self.out_dir)
        out_row.addWidget(btn_browse_out)
        root.addLayout(out_row)

        self.btn_process = QPushButton("Сжать")
        self.btn_process.setMinimumHeight(36)
        root.addWidget(self.btn_process)

        self.btn_add.clicked.connect(self.add_files)
        self.btn_remove.clicked.connect(self.list_files.remove_selected)
        self.btn_clear.clicked.connect(self.list_files.clear)
        self.btn_process.clicked.connect(self.process)

    def add_files(self):
        filter_map = {
            SUPPORTED_IMAGE_EXT: "Изображения (*.jpg *.jpeg *.png *.bmp *.webp *.tiff)",
            SUPPORTED_VIDEO_EXT: "Видео (*.mp4 *.mkv *.mov *.avi *.wmv *.webm)",
            SUPPORTED_AUDIO_EXT: "Аудио (*.mp3 *.wav *.flac *.ogg *.m4a *.aac)",
        }
        file_filter = filter_map.get(self.allowed_ext, "Все файлы (*.*)")
        files, _ = QFileDialog.getOpenFileNames(self, f"Добавить файлы — {self.title}", "", file_filter)
        for f in files:
            if is_supported(f, self.allowed_ext):
                self.list_files.addItem(f)

    def choose_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Выбрать папку для сохранения")
        if d:
            self.out_dir.setText(d)

    def preset_mode(self) -> tuple[str, int]:
        if self.rb_max.isChecked():
            return ("max", 80)
        if self.rb_min.isChecked():
            return ("min", 20)
        return ("custom", self.slider.value())

    def process(self):
        files = self.list_files.items()
        if not files:
            QMessageBox.warning(self, "Нет файлов", "Добавьте файлы для обработки.")
            return
        out_dir = self.out_dir.text().strip() or os.path.dirname(files[0])
        mode, percent = self.preset_mode()

        QMessageBox.information(
            self,
            "Задача поставлена",
            f"Тип: {self.title}\nФайлов: {len(files)}\nРежим: {mode}\nСжать на: {percent}%\nВыход: {out_dir}")


class ImageTab(CompressionTab):
    def __init__(self):
        super().__init__("Фото", SUPPORTED_IMAGE_EXT)


class VideoTab(CompressionTab):
    def __init__(self):
        super().__init__("Видео", SUPPORTED_VIDEO_EXT)


class AudioTab(CompressionTab):
    def __init__(self):
        super().__init__("Аудио", SUPPORTED_AUDIO_EXT)


class PDFTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)

        switch_row = QHBoxLayout()
        self.btn_mode_compress = QPushButton("Сжать PDF")
        self.btn_mode_merge = QPushButton("Объединить в PDF")
        self.btn_mode_compress.setCheckable(True)
        self.btn_mode_merge.setCheckable(True)
        self.btn_mode_compress.setChecked(True)
        switch_row.addWidget(self.btn_mode_compress)
        switch_row.addWidget(self.btn_mode_merge)
        switch_row.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        root.addLayout(switch_row)

        self.stack = QStackedWidget()
        self.page_compress = self._build_compress_page()
        self.page_merge = self._build_merge_page()
        self.stack.addWidget(self.page_compress)
        self.stack.addWidget(self.page_merge)
        root.addWidget(self.stack)

        self.btn_mode_compress.clicked.connect(lambda: self._set_mode(0))
        self.btn_mode_merge.clicked.connect(lambda: self._set_mode(1))

    def _set_mode(self, idx: int):
        self.stack.setCurrentIndex(idx)
        self.btn_mode_compress.setChecked(idx == 0)
        self.btn_mode_merge.setChecked(idx == 1)

    def _build_compress_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        presets = QGroupBox("Режим сжатия")
        ph = QVBoxLayout(presets)
        self.rb_max = QRadioButton("Максимальное сжатие (≈60–80%)")
        self.rb_min = QRadioButton("Минимальная потеря качества")
        self.rb_custom = QRadioButton("Свои настройки")
        self.rb_min.setChecked(True)
        ph.addWidget(self.rb_max)
        ph.addWidget(self.rb_min)
        ph.addWidget(self.rb_custom)

        custom_row = QHBoxLayout()
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(25)
        self.slider.setEnabled(False)
        self.lbl_slider = QLabel("Сжать на: 25%")
        custom_row.addWidget(self.slider)
        custom_row.addWidget(self.lbl_slider)
        ph.addLayout(custom_row)
        self.rb_custom.toggled.connect(self.slider.setEnabled)
        self.slider.valueChanged.connect(lambda v: self.lbl_slider.setText(f"Сжать на: {v}%"))
        layout.addWidget(presets)

        controls = QHBoxLayout()
        self.btn_add = QPushButton("Добавить PDF…")
        self.btn_remove = QPushButton("Удалить выбранные")
        self.btn_clear = QPushButton("Очистить список")
        controls.addWidget(self.btn_add)
        controls.addWidget(self.btn_remove)
        controls.addWidget(self.btn_clear)
        layout.addLayout(controls)

        self.list_pdfs = DraggableFileList(SUPPORTED_PDF_EXT)
        layout.addWidget(self.list_pdfs)

        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Папка сохранения:"))
        self.out_dir = QLineEdit()
        self.out_dir.setPlaceholderText("не выбрано")
        btn_browse_out = QPushButton("Выбрать…")
        btn_browse_out.clicked.connect(self._choose_output_dir)
        out_row.addWidget(self.out_dir)
        out_row.addWidget(btn_browse_out)
        layout.addLayout(out_row)

        self.btn_process = QPushButton("Сжать")
        self.btn_process.clicked.connect(self._process_compress)
        layout.addWidget(self.btn_process)

        self.btn_add.clicked.connect(self._add_pdfs)
        self.btn_remove.clicked.connect(self.list_pdfs.remove_selected)
        self.btn_clear.clicked.connect(self.list_pdfs.clear)

        return page

    def _add_pdfs(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выбрать PDF", "", "PDF (*.pdf)")
        for f in files:
            if is_supported(f, SUPPORTED_PDF_EXT):
                self.list_pdfs.addItem(f)

    def _choose_output_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Выбрать папку для сохранения")
        if d:
            self.out_dir.setText(d)

    def _preset(self) -> tuple[str, int]:
        if self.rb_max.isChecked():
            return ("max", 80)
        if self.rb_min.isChecked():
            return ("min", 20)
        return ("custom", self.slider.value())

    def _process_compress(self):
        files = [self.list_pdfs.item(i).text() for i in range(self.list_pdfs.count())]
        if not files:
            QMessageBox.warning(self, "Нет файлов", "Добавьте PDF-файлы для сжатия.")
            return
        mode, percent = self._preset()
        out_dir = self.out_dir.text().strip() or os.path.dirname(files[0])
        QMessageBox.information(self, "Задача поставлена",
                                f"PDF cжатие\nФайлов: {len(files)}\nРежим: {mode}\nСжать на: {percent}%\nВыход: {out_dir}")

    def _build_merge_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)

        controls = QHBoxLayout()
        btn_add = QPushButton("Добавить файлы…")
        btn_remove = QPushButton("Удалить выбранные")
        btn_clear = QPushButton("Очистить список")
        controls.addWidget(btn_add)
        controls.addWidget(btn_remove)
        controls.addWidget(btn_clear)
        layout.addLayout(controls)

        self.list_merge = DraggableFileList(SUPPORTED_PDF_EXT)
        self.list_merge.setToolTip("Перетащите PDF сюда. Можно менять порядок.")
        layout.addWidget(self.list_merge)

        move_row = QHBoxLayout()
        btn_up = QToolButton()
        btn_down = QToolButton()
        btn_up.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowUp))
        btn_down.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        btn_up.setToolTip("Поднять выше")
        btn_down.setToolTip("Опустить ниже")
        move_row.addWidget(QLabel("Порядок страниц:"))
        move_row.addWidget(btn_up)
        move_row.addWidget(btn_down)
        move_row.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        layout.addLayout(move_row)

        out_row = QHBoxLayout()
        out_row.addWidget(QLabel("Итоговый файл PDF:"))
        self.out_file = QLineEdit()
        self.out_file.setPlaceholderText("например, merged.pdf")
        btn_browse = QPushButton("Выбрать…")
        out_row.addWidget(self.out_file)
        out_row.addWidget(btn_browse)
        layout.addLayout(out_row)

        btn_merge = QPushButton("Объединить")
        layout.addWidget(btn_merge)

        btn_add.clicked.connect(self._merge_add)
        btn_remove.clicked.connect(self.list_merge.remove_selected)
        btn_clear.clicked.connect(self.list_merge.clear)
        btn_browse.clicked.connect(self._choose_out_file)
        btn_up.clicked.connect(lambda: self._move_selected(-1))
        btn_down.clicked.connect(lambda: self._move_selected(1))
        btn_merge.clicked.connect(self._do_merge_stub)

        return page

    def _merge_add(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Выбрать PDF для объединения", "", "PDF (*.pdf)")
        for f in files:
            if is_supported(f, SUPPORTED_PDF_EXT):
                self.list_merge.addItem(f)

    def _choose_out_file(self):
        name, _ = QFileDialog.getSaveFileName(self, "Сохранить как", "merged.pdf", "PDF (*.pdf)")
        if name:
            if not name.lower().endswith(".pdf"):
                name += ".pdf"
            self.out_file.setText(name)

    def _move_selected(self, delta: int):
        rows = sorted([self.list_merge.row(i) for i in self.list_merge.selectedItems()])
        if not rows:
            return
        if delta > 0:
            rows = rows[::-1]
        for r in rows:
            new_r = r + delta
            if 0 <= new_r < self.list_merge.count():
                item = self.list_merge.takeItem(r)
                self.list_merge.insertItem(new_r, item)
                item.setSelected(True)

    def _do_merge_stub(self):
        files = [self.list_merge.item(i).text() for i in range(self.list_merge.count())]
        if len(files) < 2:
            QMessageBox.warning(self, "Мало файлов", "Добавьте минимум два PDF для объединения.")
            return
        out_file = self.out_file.text().strip()
        if not out_file:
            QMessageBox.warning(self, "Нет пути", "Укажите имя итогового файла PDF.")
            return
        QMessageBox.information(self, "Задача поставлена",
                                f"Объединение PDF\nФайлов: {len(files)}\nРезультат: {out_file}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Compressor & PDF Tools (PyQt6)")
        self.resize(900, 640)

        tabs = QTabWidget()
        tabs.addTab(PDFTab(), "PDF")
        tabs.addTab(ImageTab(), "Фото")
        tabs.addTab(VideoTab(), "Видео")
        tabs.addTab(AudioTab(), "Аудио")

        self.setCentralWidget(tabs)


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
