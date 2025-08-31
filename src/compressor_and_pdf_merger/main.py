import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from compressor_and_pdf_merger.ui.main_window import MainWindow
from compressor_and_pdf_merger.storage.db import init_db

def main():
    app = QApplication(sys.argv)
    init_db()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()