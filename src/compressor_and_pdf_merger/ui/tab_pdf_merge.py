from __future__ import annotations
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QListWidget, QPushButton,
    QHBoxLayout, QFileDialog, QLineEdit, QMessageBox, QGroupBox, QFormLayout, QCheckBox, QSpinBox
)
from compressor_and_pdf_merger.services.pdf_merge import merge_any_to_pdf
from compressor_and_pdf_merger.storage import db
from compressor_and_pdf_merger.services.settings import Settings



class ReorderList(QListWidget):
    def __init__(self):
        super().__init__()
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)


class PdfMergeTab(QWidget):
    entry_logged = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)

        root.addWidget(QLabel("Порядок страниц = порядок файлов в списке (можно перетаскивать)."))

        self.list = ReorderList()
        root.addWidget(self.list)

        btns = QHBoxLayout()
        self.btn_add = QPushButton("Добавить файлы")
        self.btn_del = QPushButton("Удалить выбранные")
        self.btn_clear = QPushButton("Очистить список")
        btns.addWidget(self.btn_add)
        btns.addWidget(self.btn_del)
        btns.addWidget(self.btn_clear)
        root.addLayout(btns)

        grp = QGroupBox("Вывод")
        form = QFormLayout(grp)
        self.cb_a4 = QCheckBox("Привести все страницы к A4 (с белыми полями)")
        self.cb_a4.setChecked(False)
        self.sp_margin = QSpinBox()
        self.sp_margin.setRange(0, 50)
        self.sp_margin.setValue(10)
        self.sp_margin.setSuffix(" мм")
        self.sp_margin.setEnabled(self.cb_a4.isChecked())
        self.cb_a4.toggled.connect(self.sp_margin.setEnabled)
        form.addRow(self.cb_a4, self.sp_margin)
        root.addWidget(grp)

        out_row = QHBoxLayout()
        self.ed_out = QLineEdit()
        self.ed_out.setPlaceholderText("Куда сохранить итоговый PDF...")
        self.btn_out = QPushButton("Обзор...")
        out_row.addWidget(self.ed_out, 1)
        out_row.addWidget(self.btn_out)
        root.addLayout(out_row)

        self.btn_merge = QPushButton("Объединить в PDF")
        root.addWidget(self.btn_merge)

        if Settings and hasattr(Settings, "pdf_default_dir"):
            d = Settings.pdf_default_dir() or ""
            if d and not self.ed_out.text().strip():
                self.ed_out.setText(str(Path(d) / "merged.pdf"))

        self.btn_add.clicked.connect(self._on_add)
        self.btn_del.clicked.connect(self._on_del)
        self.btn_clear.clicked.connect(self._on_clear)
        self.btn_out.clicked.connect(self._on_choose_out)
        self.btn_merge.clicked.connect(self._on_merge)
        self.list.model().rowsInserted.connect(lambda *_: self._maybe_autoname())


    def _maybe_autoname(self):
        if self.ed_out.text().strip():
            return
        if self.list.count() == 0:
            return
        first = Path(self.list.item(0).text())
        default_name = first.stem + "_merged.pdf"
        self.ed_out.setText(str(first.with_name(default_name)))


    def _selected_files(self) -> list[str]:
        return [self.list.item(i).text() for i in range(self.list.count())]


    def _on_add(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Добавить файлы",
            "",
            "Поддерживаемые (*.pdf *.jpg *.jpeg *.png *.webp *.tif *.tiff *.bmp)"
        )
        for f in files:
            self.list.addItem(f)
        self._maybe_autoname()


    def _on_del(self):
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))


    def _on_clear(self):
        self.list.clear()


    def _on_choose_out(self):
        base = "merged.pdf"
        if self.list.count() > 0:
            first = Path(self.list.item(0).text())
            base = str(first.with_name(first.stem + "_merged.pdf"))
        fn, _ = QFileDialog.getSaveFileName(self, "Сохранить как", self.ed_out.text() or base, "PDF (*.pdf)")
        if fn:
            if not fn.lower().endswith(".pdf"):
                fn += ".pdf"
            self.ed_out.setText(fn)


    def _on_merge(self):
        if self.list.count() == 0:
            QMessageBox.warning(self, "Нет файлов", "Добавьте хотя бы один файл.")
            return
        out = self.ed_out.text().strip()
        if not out:
            QMessageBox.warning(self, "Нет пути", "Укажите файл для сохранения.")
            return
        if not out.lower().endswith(".pdf"):
            out += ".pdf"
            self.ed_out.setText(out)
        inputs = self._selected_files()
        try:
            res = merge_any_to_pdf(
                inputs,
                out,
                fit_to_a4=self.cb_a4.isChecked(),
                fit_margin_mm=self.sp_margin.value(),
            )
            out_for_history = res or out
            text = f"PDF: объединено {len(inputs)} → \"{out_for_history}\""
            self.entry_logged.emit(text)
            db.add_history(tab="PDF", action="Объединение", src_name=f"{len(inputs)} файлов", out_path=out_for_history)
            QMessageBox.information(self, "Готово", text)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
