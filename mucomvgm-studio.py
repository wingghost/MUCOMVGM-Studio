from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication

from mvs.config import APP_NAME, APP_ORG
from mvs.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setOrganizationName(APP_ORG)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
