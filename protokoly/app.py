"""Vstupní bod GUI aplikace."""
from __future__ import annotations

import sys


def main() -> int:
    from PySide6.QtWidgets import QApplication

    from .models.storage import Storage
    from .ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Fluffy-Doc")

    okno = MainWindow(Storage())
    okno.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
