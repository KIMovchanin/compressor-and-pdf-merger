from __future__ import annotations
from pathlib import Path
from os.path import isfile, isdir
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLineEdit, QLabel, QComboBox, QSpinBox, QMessageBox, QGroupBox, QFormLayout
)
from compressor_and_pdf_merger.services.pdf_convert import (
    pdf_to_images, pdf_to_pptx_snapshots, pdf_to_text
)
from compressor_and_pdf_merger.storage import db
from compressor_and_pdf_merger.services.settings import Settings



class PdfConvertTab(QWidget):
    entry_logged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)

        in_row = QHBoxLayout()
        self.ed_in = QLineEdit()
        self.ed_in.setPlaceholderText("Выберите PDF...")
        self.btn_in = QPushButton("Обзор...")
        in_row.addWidget(self.ed_in, 1)
        in_row.addWidget(self.btn_in)
        root.addLayout(in_row)

        grp = QGroupBox("Конвертация")
        form = QFormLayout(grp)

        self.cmb_kind = QComboBox()
        self.cmb_kind.addItems(["Изображения (JPG)", "Изображения (PNG)", "PPTX (снимки)", "TXT"])
        form.addRow(QLabel("Формат:"), self.cmb_kind)

        self.ed_range = QLineEdit()
        self.ed_range.setPlaceholderText("Диапазон страниц, напр. 1-3,5")
        form.addRow(QLabel("Диапазон:"), self.ed_range)

        self.sp_dpi = QSpinBox()
        self.sp_dpi.setRange(72, 600)
        self.sp_dpi.setValue(144)
        form.addRow(QLabel("DPI (для изображений/слайдов):"), self.sp_dpi)

        out_row = QHBoxLayout()
        self.ed_out = QLineEdit()
        self.ed_out.setPlaceholderText("Папка/файл для сохранения...")
        self.btn_out = QPushButton("Обзор...")
        out_row.addWidget(self.ed_out, 1)
        out_row.addWidget(self.btn_out)

        root.addWidget(grp)
        root.addLayout(out_row)

        self.btn_go = QPushButton("Конвертировать")
        root.addWidget(self.btn_go)

        self.btn_in.clicked.connect(self._choose_in)
        self.btn_out.clicked.connect(self._choose_out)
        self.btn_go.clicked.connect(self._on_go)
        self.ed_in.textChanged.connect(lambda _: self._auto_out_name())
        self.cmb_kind.currentTextChanged.connect(lambda _: self._auto_out_name())

        if Settings and hasattr(Settings, "pdf_default_dir"):
            d = Settings.pdf_default_dir() or ""
            if d and not self.ed_out.text().strip():
                self.ed_out.setText(str(Path(d)))


    def _src(self) -> Path | None:
        t = self.ed_in.text().strip()
        return Path(t) if t and isfile(t) else None


    def _default_out_for(self) -> str:
        src = self._src()
        if not src:
            return self.ed_out.text().strip() or ""
        stem = src.stem
        kind = self.cmb_kind.currentText()
        if kind == "Изображения (JPG)":
            return str(src.with_name(f"{stem}_images_jpg"))
        if kind == "Изображения (PNG)":
            return str(src.with_name(f"{stem}_images_png"))
        if kind == "PPTX (снимки)":
            return str(src.with_name(f"{stem}_converted.pptx"))
        if kind == "TXT":
            return str(src.with_name(f"{stem}_converted.txt"))
        return str(src.with_name(f"{stem}_converted"))


    def _auto_out_name(self):
        d = self._default_out_for()
        if d and (not self.ed_out.text().strip() or Path(self.ed_out.text()).parent == Path(self._src().parent if self._src() else ".")):
            self.ed_out.setText(d)


    def _choose_in(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Выбрать PDF", "", "PDF (*.pdf)")
        if fn:
            self.ed_in.setText(fn)


    def _choose_out(self):
        src = self._src()
        if not src:
            d = QFileDialog.getExistingDirectory(self, "Папка назначения", self.ed_out.text() or "")
            if d:
                self.ed_out.setText(d)
            return
        default = self._default_out_for()
        kind = self.cmb_kind.currentText()
        if "Изображения" in kind:
            d = QFileDialog.getExistingDirectory(self, "Папка назначения", default)
            if d:
                self.ed_out.setText(d)
        elif kind == "TXT":
            fn, _ = QFileDialog.getSaveFileName(self, "Сохранить как", default, "TXT (*.txt)")
            if fn:
                if not fn.lower().endswith(".txt"):
                    fn += ".txt"
                self.ed_out.setText(fn)
        elif kind == "PPTX (снимки)":
            fn, _ = QFileDialog.getSaveFileName(self, "Сохранить как", default, "PPTX (*.pptx)")
            if fn:
                if not fn.lower().endswith(".pptx"):
                    fn += ".pptx"
                self.ed_out.setText(fn)


    def _on_go(self):
        src = self._src()
        if not src:
            QMessageBox.warning(self, "Нет файла", "Выберите входной PDF.")
            return
        kind = self.cmb_kind.currentText()
        rng = self.ed_range.text().strip() or None
        dpi = int(self.sp_dpi.value())
        try:
            if kind.startswith("Изображения"):
                out_dir = self.ed_out.text().strip() or self._default_out_for()
                fmt = "jpg" if "JPG" in kind else "png"
                files = pdf_to_images(src, out_dir, fmt=fmt, dpi=dpi, page_range=rng)
                text = f"PDF→{fmt.upper()}: {len(files)} файлов в \"{out_dir}\""
                self.entry_logged.emit(text)
                db.add_history(tab="PDF", action=f"Convert → {fmt.upper()}", src_name=src.name, out_path=out_dir)
                QMessageBox.information(self, "Готово", text)
            elif kind == "PPTX (снимки)":
                out_file = self.ed_out.text().strip() or self._default_out_for()
                if not out_file.lower().endswith(".pptx"):
                    out_file += ".pptx"
                res = pdf_to_pptx_snapshots(src, out_file, dpi=dpi)
                text = f"PDF→PPTX (снимки): \"{res}\""
                self.entry_logged.emit(text)
                db.add_history(tab="PDF", action="Convert → PPTX(snap)", src_name=src.name, out_path=res)
                QMessageBox.information(self, "Готово", text)
            elif kind == "TXT":
                out_file = self.ed_out.text().strip() or self._default_out_for()
                res = pdf_to_text(src, out_file)
                text = f"PDF→TXT: \"{res}\""
                self.entry_logged.emit(text)
                db.add_history(tab="PDF", action="Convert → TXT", src_name=src.name, out_path=res)
                QMessageBox.information(self, "Готово", text)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
