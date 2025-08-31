from __future__ import annotations
from PyQt6.QtCore import QObject, pyqtSignal
from typing import Callable

class BatchWorker(QObject):
    progress = pyqtSignal(int)
    file_done = pyqtSignal(str, str)
    file_fail = pyqtSignal(str, str)
    finished  = pyqtSignal()

    def __init__(self, files: list[str], func: Callable[[str], str]):
        super().__init__()
        self._files = files
        self._func = func
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        total = len(self._files) or 1
        for i, f in enumerate(self._files, start=1):
            if self._cancelled:
                break
            try:
                out_path = self._func(f)
                self.file_done.emit(f, out_path)
            except Exception as e:
                self.file_fail.emit(f, str(e))
            self.progress.emit(int(i * 100 / total))
        self.finished.emit()
