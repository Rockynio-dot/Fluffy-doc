"""Dialog pro vyplnění polí šablony a vygenerování dokumentu."""
from __future__ import annotations

import os
import subprocess
import sys

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDateEdit, QDialog, QFormLayout, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPlainTextEdit, QPushButton, QScrollArea, QVBoxLayout,
    QWidget,
)

from ..core.generator import Generator, GeneratorError
from ..models import FieldType, Template
from ..models.storage import Storage


class FillDialog(QDialog):
    """Formulář poskládaný podle definic polí šablony."""

    def __init__(self, storage: Storage, sablona: Template, parent=None) -> None:
        super().__init__(parent)
        self.storage = storage
        self.sablona = sablona
        self.widgety: dict[str, QWidget] = {}
        self.vygenerovano: str | None = None
        self.setWindowTitle(f"Vyplnit – {sablona.nazev}")
        self.resize(560, 640)
        self._postav()

    def _postav(self) -> None:
        layout = QVBoxLayout(self)

        nadpis = QLabel(f"<b>{self.sablona.nazev}</b>")
        layout.addWidget(nadpis)
        if self.sablona.popis:
            p = QLabel(self.sablona.popis)
            p.setStyleSheet("color: gray;")
            layout.addWidget(p)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        vnitrek = QWidget()
        form = QFormLayout(vnitrek)

        for pole in self.sablona.pole:
            w = self._widget_pro(pole)
            self.widgety[pole.klic] = w
            popisek = pole.popisek + (" *" if pole.povinne else "")
            form.addRow(popisek, w)

        scroll.setWidget(vnitrek)
        layout.addWidget(scroll, 1)

        radek = QHBoxLayout()
        radek.addStretch(1)
        btn_zrus = QPushButton("Zavřít")
        btn_zrus.clicked.connect(self.reject)
        btn_gen = QPushButton("Vygenerovat dokument")
        btn_gen.setDefault(True)
        btn_gen.clicked.connect(self._generuj)
        radek.addWidget(btn_zrus)
        radek.addWidget(btn_gen)
        layout.addLayout(radek)

    def _widget_pro(self, pole) -> QWidget:
        if pole.typ == FieldType.AUTO:
            w = QLineEdit()
            w.setReadOnly(True)
            w.setText(pole.format_auto(self.sablona.citac + 1))
            w.setStyleSheet("color: gray; font-style: italic;")
            w.setToolTip("Vyplní se automaticky při generování.")
            return w
        if pole.typ == FieldType.MULTILINE:
            w = QPlainTextEdit()
            w.setPlainText(pole.vychozi)
            w.setMaximumHeight(80)
            return w
        if pole.typ == FieldType.CHOICE:
            w = QComboBox()
            w.addItem("")
            w.addItems(pole.moznosti)
            if pole.vychozi:
                w.setCurrentText(pole.vychozi)
            return w
        if pole.typ == FieldType.CHECKBOX:
            w = QCheckBox("Ano")
            w.setChecked(pole.vychozi.strip().lower() in {"ano", "1", "true", "x"})
            return w
        if pole.typ == FieldType.DATE:
            w = QDateEdit()
            w.setDisplayFormat("dd.MM.yyyy")
            w.setCalendarPopup(True)
            w.setDate(QDate.currentDate())
            return w
        w = QLineEdit()
        w.setText(pole.vychozi)
        return w

    def _hodnota(self, pole, w) -> str:
        if pole.typ == FieldType.AUTO:
            return pole.format_auto(self.sablona.citac + 1)
        if pole.typ == FieldType.MULTILINE:
            return w.toPlainText()
        if pole.typ == FieldType.CHOICE:
            return w.currentText()
        if pole.typ == FieldType.CHECKBOX:
            return "ano" if w.isChecked() else ""
        if pole.typ == FieldType.DATE:
            return w.date().toString("dd.MM.yyyy")
        return w.text()

    def _generuj(self) -> None:
        hodnoty = {p.klic: self._hodnota(p, self.widgety[p.klic]) for p in self.sablona.pole}
        # označení souboru: auto-číslo > sériové číslo > číslo protokolu
        auto = next((p.klic for p in self.sablona.pole if p.typ == FieldType.AUTO), None)
        oznaceni = (
            (hodnoty.get(auto) if auto else "")
            or hodnoty.get("seriove_cislo")
            or hodnoty.get("cislo_protokolu")
            or ""
        )
        cesta = self.storage.cesta_pro_vystup(self.sablona, oznaceni)
        try:
            Generator.generuj(self.sablona, hodnoty, cesta)
        except GeneratorError as e:
            QMessageBox.warning(self, "Zkontroluj pole", str(e))
            return
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Chyba", str(e))
            return

        # po úspěšném vygenerování posuň čítač automatického čísla
        if self.sablona.ma_auto_cislo():
            self.sablona.citac += 1
            try:
                self.storage.uloz_sablonu(self.sablona)
            except Exception:  # noqa: BLE001
                pass

        self.vygenerovano = cesta
        odpoved = QMessageBox.question(
            self, "Hotovo",
            f"Dokument byl vytvořen:\n{cesta}\n\nOtevřít ho teď?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes,
        )
        if odpoved == QMessageBox.Yes:
            _otevri(cesta)
        self.accept()


def _otevri(cesta: str) -> None:
    try:
        if sys.platform.startswith("win"):
            os.startfile(cesta)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.run(["open", cesta], check=False)
        else:
            subprocess.run(["xdg-open", cesta], check=False)
    except Exception:  # noqa: BLE001
        pass
