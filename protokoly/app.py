"""Vstupní bod GUI aplikace."""
from __future__ import annotations

import os
import sys

APP_ID = "cz.prosecurity.FluffyDoc"


def _cesta_ikony() -> str | None:
    """Najde ikonu jak při běhu ze zdrojáků, tak ze zabaleného .exe/Flatpaku."""
    zaklad = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    for jmeno in ("assets/icon-256.png", "assets/icon.ico", "icon-256.png"):
        cesta = os.path.join(zaklad, jmeno)
        if os.path.isfile(cesta):
            return cesta
    return None


def main() -> int:
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    from .models.storage import Storage
    from .ui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Fluffy-Doc")
    app.setDesktopFileName(APP_ID)
    ikona = _cesta_ikony()
    if ikona:
        app.setWindowIcon(QIcon(ikona))

    okno = MainWindow(Storage())
    okno.show()

    # smoke test zabaleného buildu: otevři a hned ukonči
    if os.environ.get("FLUFFY_DOC_SMOKE"):
        from PySide6.QtCore import QTimer

        QTimer.singleShot(400, app.quit)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
