from __future__ import annotations
from pathlib import Path
from os.path import isfile
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QLineEdit, QLabel, QComboBox, QSpinBox, QCheckBox, QMessageBox, QGroupBox, QFormLayout
)
from compressor_and_pdf_merger.services.pdf_compress import compress_pdf
from compressor_and_pdf_merger.storage import db
from compressor_and_pdf_merger.services.settings import Settings


class PdfCompressTab(QWidget):
    entry_logged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)

        in_row = QHBoxLayout()
        self.ed_in = QLineEdit()
        self.ed_in.setPlaceholderText("Выберите PDF…")
        self.btn_in = QPushButton("Обзор…")
        in_row.addWidget(self.ed_in, 1); in_row.addWidget(self.btn_in)
        root.addLayout(in_row)

        grp = QGroupBox("Параметры сжатия")
        form = QFormLayout(grp)

        self.cmb_mode = QComboBox()
        self.cmb_mode.addItems(["Бережное (без потерь)", "С картинками (Ghostscript)"])
        self.cmb_mode.setCurrentIndex(0)
        form.addRow(QLabel("Режим:"), self.cmb_mode)

        self.sp_dpi = QSpinBox(); self.sp_dpi.setRange(72, 600); self.sp_dpi.setValue(144)
        self.sp_jpgq = QSpinBox(); self.sp_jpgq.setRange(20, 95); self.sp_jpgq.setValue(75)
        self.cb_gray = QCheckBox("В оттенки серого")

        def _toggle(_):
            en = (self.cmb_mode.currentIndex() == 1)
            self.sp_dpi.setEnabled(en); self.sp_jpgq.setEnabled(en); self.cb_gray.setEnabled(en)
        self.cmb_mode.currentIndexChanged.connect(_toggle); _toggle(0)

        form.addRow(QLabel("Целевой DPI:"), self.sp_dpi)
        form.addRow(QLabel("JPEG качество:"), self.sp_jpgq)
        form.addRow(self.cb_gray)
        self.cb_strip = QCheckBox("Удалить метаданные/вложения"); self.cb_strip.setChecked(True)
        form.addRow(self.cb_strip)
        self.cb_ensure = QCheckBox("Не больше исходного"); self.cb_ensure.setChecked(True)
        form.addRow(self.cb_ensure)

        root.addWidget(grp)

        out_row = QHBoxLayout()
        self.ed_out = QLineEdit()
        self.ed_out.setPlaceholderText("Куда сохранить...")
        self.btn_out = QPushButton("Обзор...")
        out_row.addWidget(self.ed_out, 1); out_row.addWidget(self.btn_out)
        root.addLayout(out_row)

        if Settings and hasattr(Settings, "pdf_default_dir"):
            d = Settings.pdf_default_dir() or ""
            if d and not self.ed_out.text().strip():
                self.ed_out.setText(str(Path(d) / "compressed.pdf"))

        self.btn_go = QPushButton("Сжать")
        root.addWidget(self.btn_go)

        self.btn_in.clicked.connect(self._choose_in)
        self.btn_out.clicked.connect(self._choose_out)
        self.btn_go.clicked.connect(self._on_go)

        self.ed_in.textChanged.connect(self._auto_out_name)


    def _default_out_for(self, in_path: str) -> str:
        p = Path(in_path)
        name = p.stem + "_compressed.pdf"
        return str(p.with_name(name))

    def _auto_out_name(self, txt: str):
        if not txt or not txt.lower().endswith(".pdf"):
            return
        out_cur = self.ed_out.text().strip()
        proposed = self._default_out_for(txt)
        if (not out_cur) or (Path(out_cur).parent == Path(txt).parent and out_cur.endswith("_compressed.pdf")):
            self.ed_out.setText(proposed)


    def _choose_in(self):
        fn, _ = QFileDialog.getOpenFileName(self, "Выбрать PDF", "", "PDF (*.pdf)")
        if fn:
            self.ed_in.setText(fn)


    def _choose_out(self):
        base = self._default_out_for(self.ed_in.text().strip()) if self.ed_in.text().strip() else "compressed.pdf"
        fn, _ = QFileDialog.getSaveFileName(self, "Сохранить как", base, "PDF (*.pdf)")
        if fn:
            if not fn.lower().endswith(".pdf"):
                fn += ".pdf"
            self.ed_out.setText(fn)


    def _on_go(self):
        src = self.ed_in.text().strip()
        dst = self.ed_out.text().strip()
        if not (src and isfile(src)):
            QMessageBox.warning(self, "Нет файла", "Выберите входной PDF.")
            return
        if not dst:
            QMessageBox.warning(self, "Нет пути", "Укажите путь сохранения.")
            return
        try:
            mode = "lossless" if self.cmb_mode.currentIndex() == 0 else "images"
            res = compress_pdf(
                src, dst,
                mode=mode,
                target_dpi=self.sp_dpi.value(),
                jpeg_quality=self.sp_jpgq.value(),
                grayscale=self.cb_gray.isChecked(),
                strip_metadata=self.cb_strip.isChecked(),
                ensure_not_larger=self.cb_ensure.isChecked(),
            )
            text = f"PDF: сжатие ({mode}) → \"{res}\""
            self.entry_logged.emit(text)
            db.add_history(tab="PDF", action="Сжатие", src_name=Path(src).name, out_path=res)
            QMessageBox.information(self, "Готово", text)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
