"""Hlavní okno aplikace – seznam šablon a akce nad nimi."""
from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QMainWindow, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from ..models.storage import Storage, slugify
from .fill_dialog import FillDialog
from .template_editor import TemplateEditor


class MainWindow(QMainWindow):
    def __init__(self, storage: Storage | None = None) -> None:
        super().__init__()
        self.storage = storage or Storage()
        self.setWindowTitle("Fluffy-Doc – generátor předávacích protokolů")
        self.resize(820, 520)
        self._postav()
        self._nacti_seznam()

    def _postav(self) -> None:
        stred = QWidget()
        self.setCentralWidget(stred)
        layout = QHBoxLayout(stred)

        # levý sloupec – seznam šablon
        levy = QVBoxLayout()
        levy.addWidget(QLabel("<b>Šablony</b>"))
        self.seznam = QListWidget()
        self.seznam.setSelectionMode(QAbstractItemView.SingleSelection)
        self.seznam.itemDoubleClicked.connect(lambda *_: self._vyplnit())
        self.seznam.currentItemChanged.connect(self._obnov_detail)
        levy.addWidget(self.seznam, 1)
        layout.addLayout(levy, 1)

        # pravý sloupec – detail + tlačítka
        pravy = QVBoxLayout()
        self.detail = QLabel("Vyber šablonu ze seznamu.")
        self.detail.setWordWrap(True)
        self.detail.setAlignment(Qt.AlignTop)
        self.detail.setTextInteractionFlags(Qt.TextSelectableByMouse)
        pravy.addWidget(self.detail, 1)

        btn_vyplnit = QPushButton("📝 Vyplnit a vygenerovat")
        btn_vyplnit.clicked.connect(self._vyplnit)
        btn_nova = QPushButton("➕ Nová šablona")
        btn_nova.clicked.connect(self._nova)
        btn_uprav = QPushButton("✏️ Upravit šablonu")
        btn_uprav.clicked.connect(self._upravit)
        btn_slozka = QPushButton("📂 Otevřít složku s výstupy")
        btn_slozka.clicked.connect(self._otevri_vystupy)
        btn_smaz = QPushButton("🗑 Smazat šablonu")
        btn_smaz.clicked.connect(self._smazat)

        for b in (btn_vyplnit, btn_nova, btn_uprav, btn_slozka, btn_smaz):
            pravy.addWidget(b)
        layout.addLayout(pravy, 1)

    # ---- data ---------------------------------------------------------
    def _nacti_seznam(self) -> None:
        self.seznam.clear()
        for s in self.storage.seznam_sablon():
            item = QListWidgetItem(s.nazev)
            item.setData(Qt.UserRole, slugify(s.nazev))
            self.seznam.addItem(item)
        if self.seznam.count():
            self.seznam.setCurrentRow(0)

    def _aktualni_slug(self) -> str | None:
        item = self.seznam.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _obnov_detail(self, *_) -> None:
        slug = self._aktualni_slug()
        if not slug:
            self.detail.setText("Vyber šablonu ze seznamu.")
            return
        s = self.storage.nacti_sablonu(slug)
        radky = "".join(
            f"<li><b>{p.popisek}</b> "
            f"<code>{{{{{p.klic}}}}}</code> – {p.typ.popisek}"
            f"{' (povinné)' if p.povinne else ''}</li>"
            for p in s.pole
        )
        self.detail.setText(
            f"<h3>{s.nazev}</h3>"
            f"<p style='color:gray'>{s.popis}</p>"
            f"<p>Dokument: <code>{s.dokument}</code> · Formát: {s.format.upper()}</p>"
            f"<p><b>Pole ({len(s.pole)}):</b></p><ul>{radky}</ul>"
        )

    # ---- akce ---------------------------------------------------------
    def _vyplnit(self) -> None:
        slug = self._aktualni_slug()
        if not slug:
            return
        s = self.storage.nacti_sablonu(slug)
        FillDialog(self.storage, s, self).exec()

    def _nova(self) -> None:
        dlg = TemplateEditor(self.storage, parent=self)
        if dlg.exec():
            self._nacti_seznam()

    def _upravit(self) -> None:
        slug = self._aktualni_slug()
        if not slug:
            return
        s = self.storage.nacti_sablonu(slug)
        dlg = TemplateEditor(self.storage, sablona=s, parent=self)
        if dlg.exec():
            self._nacti_seznam()

    def _smazat(self) -> None:
        slug = self._aktualni_slug()
        if not slug:
            return
        s = self.storage.nacti_sablonu(slug)
        if QMessageBox.question(
            self, "Smazat šablonu",
            f"Opravdu smazat šablonu „{s.nazev}“? Vygenerované dokumenty zůstanou zachovány.",
        ) == QMessageBox.Yes:
            self.storage.smaz_sablonu(slug)
            self._nacti_seznam()

    def _otevri_vystupy(self) -> None:
        cesta = self.storage.vystup_dir
        os.makedirs(cesta, exist_ok=True)
        if sys.platform.startswith("win"):
            os.startfile(cesta)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", cesta], check=False)
        else:
            subprocess.run(["xdg-open", cesta], check=False)
