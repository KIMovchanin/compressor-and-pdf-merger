from __future__ import annotations
from pathlib import Path
from os.path import isfile, isdir
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLineEdit, QLabel, QComboBox, QSpinBox, QCheckBox, QMessageBox, QGroupBox, QFormLayout
)
from compressor_and_pdf_merger.services.pdf_convert import (
    pdf_to_images, pdf_to_office, pdf_to_pptx_snapshots, pdf_to_text
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
        in_row.addWidget(self.ed_in, 1); in_row.addWidget(self.btn_in)
        root.addLayout(in_row)

        grp = QGroupBox("Конвертация")
        form = QFormLayout(grp)

        self.cmb_kind = QComboBox()
        self.cmb_kind.addItems(["Изображения (JPG)", "Изображения (PNG)", "DOCX", "RTF", "XLSX", "PPTX (LibreOffice)", "PPTX (снимки)", "TXT"])
        form.addRow(QLabel("Формат:"), self.cmb_kind)

        self.ed_range = QLineEdit()
        self.ed_range.setPlaceholderText("Диапазон страниц, напр. 1-3,5 (пусто = все)")
        form.addRow(QLabel("Диапазон:"), self.ed_range)

        self.sp_dpi = QSpinBox(); self.sp_dpi.setRange(72, 600); self.sp_dpi.setValue(144)
        form.addRow(QLabel("DPI (для изображений):"), self.sp_dpi)

        self.cb_ocr = QCheckBox("OCR для сканов (ocrmypdf + Tesseract)")
        self.ed_lang = QLineEdit("eng")
        form.addRow(self.cb_ocr, self.ed_lang)

        out_row = QHBoxLayout()
        self.ed_out = QLineEdit()
        self.ed_out.setPlaceholderText("Папка/файл для сохранения…")
        self.btn_out = QPushButton("Обзор…")
        out_row.addWidget(self.ed_out, 1); out_row.addWidget(self.btn_out)

        root.addWidget(grp)
        root.addLayout(out_row)

        if Settings and hasattr(Settings, "pdf_default_dir"):
            d = Settings.pdf_default_dir() or ""
            if d and not self.ed_out.text().strip():
                self.ed_out.setText(str(Path(d)))

        self.btn_go = QPushButton("Конвертировать")
        root.addWidget(self.btn_go)

        self.btn_in.clicked.connect(self._choose_in)
        self.btn_out.clicked.connect(self._choose_out)
        self.btn_go.clicked.connect(self._on_go)


    def _choose_in(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Выбрать PDF", "", "PDF (*.pdf)")
        if fn:
            self.ed_in.setText(fn)


    def _choose_out(self):
        kind = self.cmb_kind.currentText()
        if "Изображения" in kind or kind == "TXT":
            d = QFileDialog.getExistingDirectory(self, "Папка назначения", self.ed_out.text() or "")
            if d:
                self.ed_out.setText(d)
        else:
            default_name = Path(self.ed_in.text() or "out").with_suffix(self._ext_for_kind(kind)).name
            fn, _ = QFileDialog.getSaveFileName(self, "Сохранить как", str(Path(self.ed_out.text() or "") / default_name), f"*{self._ext_for_kind(kind)}")
            if fn:
                self.ed_out.setText(fn)


    def _ext_for_kind(self, kind: str) -> str:
        return {
            "DOCX": ".docx",
            "RTF": ".rtf",
            "XLSX": ".xlsx",
            "PPTX (LibreOffice)": ".pptx",
            "PPTX (снимки)": ".pptx",
            "TXT": ".txt",
        }.get(kind, ".pdf")


    def _on_go(self):
        src = self.ed_in.text().strip()
        if not (src and isfile(src)):
            QMessageBox.warning(self, "Нет файла", "Выберите входной PDF.")
            return

        kind = self.cmb_kind.currentText()
        rng = self.ed_range.text().strip() or None
        dpi = int(self.sp_dpi.value())

        try:
            if kind.startswith("Изображения"):
                out_dir = self.ed_out.text().strip()
                if not (out_dir and isdir(out_dir)):
                    QMessageBox.warning(self, "Нет папки", "Укажите папку для изображений.")
                    return
                fmt = "jpg" if "JPG" in kind else "png"
                files = pdf_to_images(src, out_dir, fmt=fmt, dpi=dpi, page_range=rng)
                text = f"PDF→{fmt.upper()}: {len(files)} файлов в \"{out_dir}\""
                self.entry_logged.emit(text)
                db.add_history(tab="PDF", action=f"Convert → {fmt.upper()}", src_name=Path(src).name, out_path=out_dir)
                QMessageBox.information(self, "Готово", text)

            elif kind in ("DOCX", "RTF", "XLSX", "PPTX (LibreOffice)"):
                out_file = self.ed_out.text().strip()
                if not out_file:
                    QMessageBox.warning(self, "Нет пути", "Укажите файл назначения.")
                    return
                k = "docx" if kind == "DOCX" else "rtf" if kind == "RTF" else "xlsx" if kind == "XLSX" else "pptx"
                res = pdf_to_office(src, Path(out_file).parent, kind=k)
                # если LibreOffice поменял имя, просто сообщим фактический путь
                text = f"PDF→{k.upper()}: \"{res}\""
                self.entry_logged.emit(text)
                db.add_history(tab="PDF", action=f"Convert → {k.upper()}", src_name=Path(src).name, out_path=res)
                QMessageBox.information(self, "Готово", text)

            elif kind == "PPTX (снимки)":
                out_file = self.ed_out.text().strip()
                if not out_file:
                    QMessageBox.warning(self, "Нет пути", "Укажите файл назначения.")
                    return
                if not out_file.lower().endswith(".pptx"):
                    out_file += ".pptx"
                res = pdf_to_pptx_snapshots(src, out_file, dpi=dpi)
                text = f"PDF→PPTX (снимки): \"{res}\""
                self.entry_logged.emit(text)
                db.add_history(tab="PDF", action="Convert → PPTX(snap)", src_name=Path(src).name, out_path=res)
                QMessageBox.information(self, "Готово", text)

            elif kind == "TXT":
                out_dir_or_file = self.ed_out.text().strip()
                if not out_dir_or_file:
                    QMessageBox.warning(self, "Нет пути", "Укажите папку/файл назначения.")
                    return
                out_file = out_dir_or_file
                if isdir(out_dir_or_file):
                    out_file = str(Path(out_dir_or_file) / (Path(src).stem + ".txt"))
                res = pdf_to_text(src, out_file, ocr=self.cb_ocr.isChecked(), ocr_lang=self.ed_lang.text().strip() or "eng")
                text = f"PDF→TXT: \"{res}\""
                self.entry_logged.emit(text)
                db.add_history(tab="PDF", action="Convert → TXT", src_name=Path(src).name, out_path=res)
                QMessageBox.information(self, "Готово", text)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
