"""Dialog pro vytvoření / úpravu šablony a její pole."""
from __future__ import annotations

import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog,
    QFormLayout, QHBoxLayout, QHeaderView, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from ..core.generator import Generator, GeneratorError
from ..core.placeholder import obal
from ..models import Field, FieldType, Template
from ..models.storage import Storage

TYPY = list(FieldType)


class TemplateEditor(QDialog):
    """Vytvoření nové nebo úprava existující šablony."""

    def __init__(self, storage: Storage, sablona: Template | None = None, parent=None) -> None:
        super().__init__(parent)
        self.storage = storage
        self.sablona = sablona
        self._novy_dokument: str | None = None  # cesta k nově vybranému souboru
        self.setWindowTitle("Nová šablona" if sablona is None else f"Úprava – {sablona.nazev}")
        self.resize(760, 560)
        self._postav()
        if sablona:
            self._nacti(sablona)

    # ---- UI -----------------------------------------------------------
    def _postav(self) -> None:
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.ed_nazev = QLineEdit()
        self.ed_popis = QLineEdit()
        form.addRow("Název šablony *", self.ed_nazev)
        form.addRow("Popis", self.ed_popis)

        radek_dok = QHBoxLayout()
        self.lbl_dokument = QLabel("(žádný dokument)")
        self.lbl_dokument.setStyleSheet("color: gray;")
        btn_vybrat = QPushButton("Vybrat dokument (.docx / .odt)…")
        btn_vybrat.clicked.connect(self._vyber_dokument)
        radek_dok.addWidget(self.lbl_dokument, 1)
        radek_dok.addWidget(btn_vybrat)
        form.addRow("Dokument šablony *", self._obal(radek_dok))
        layout.addLayout(form)

        napoveda = QLabel(
            "V dokumentu označ místa k vyplnění zápisem <b>{{klic}}</b>, "
            "např. <b>{{seriove_cislo}}</b>. Tlačítkem níže je načteš do tabulky polí. "
            "Klíč lze i s diakritikou (<b>{{Značka_telefonu}}</b>). "
            "Kliknutím na buňku ve sloupci <b>Klíč</b> zkopíruješ <b>{{klic}}</b> do schránky."
        )
        napoveda.setWordWrap(True)
        napoveda.setStyleSheet("color: #555; padding: 4px 0;")
        layout.addWidget(napoveda)

        radek_scan = QHBoxLayout()
        btn_scan = QPushButton("↻ Načíst pole z dokumentu")
        btn_scan.clicked.connect(self._nacti_pole_z_dokumentu)
        btn_pridej = QPushButton("+ Přidat pole ručně")
        btn_pridej.clicked.connect(lambda: self._pridej_radek(Field(klic="nove_pole")))
        btn_smaz = QPushButton("– Odebrat vybrané")
        btn_smaz.clicked.connect(self._smaz_radek)
        radek_scan.addWidget(btn_scan)
        radek_scan.addWidget(btn_pridej)
        radek_scan.addWidget(btn_smaz)
        radek_scan.addStretch(1)
        layout.addLayout(radek_scan)

        self.tabulka = QTableWidget(0, 6)
        self.tabulka.setHorizontalHeaderLabels(
            ["Klíč ({{...}})", "Popisek", "Typ", "Povinné", "Možnosti (; )", "Výchozí / Vzor čísla"]
        )
        self.tabulka.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.tabulka.verticalHeader().setVisible(False)
        self.tabulka.cellClicked.connect(self._kopiruj_klic)
        layout.addWidget(self.tabulka, 1)

        # --- automatické číslování protokolů (per šablona) ---
        cislo = QHBoxLayout()
        cislo.addWidget(QLabel("Čítač protokolu – poslední použité číslo:"))
        self.spin_citac = QSpinBox()
        self.spin_citac.setMaximum(10_000_000)
        self.spin_citac.setToolTip("Další vygenerovaný protokol dostane číslo o 1 vyšší.")
        cislo.addWidget(self.spin_citac)
        cislo.addStretch(1)
        layout.addLayout(cislo)

        napoveda_auto = QLabel(
            "Automatické číslo: přidej pole typu <b>Automatické číslo</b> a do sloupce "
            "<b>Vzor čísla</b> napiš vzor, např. <code>PST-{rok}-{poradi:04d}</code> → "
            "<code>PST-2026-0007</code>. Placeholdery: <code>{poradi}</code>, "
            "<code>{rok}</code>, <code>{mesic}</code>, <code>{den}</code>. "
            "Čítač i vzor se pamatují u každé šablony zvlášť."
        )
        napoveda_auto.setWordWrap(True)
        napoveda_auto.setStyleSheet("color: #555; padding: 2px 0;")
        layout.addWidget(napoveda_auto)

        self.status = QLabel("")
        self.status.setStyleSheet("color: #2a7; padding: 2px 0;")
        layout.addWidget(self.status)

        btns = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        btns.accepted.connect(self._uloz)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @staticmethod
    def _obal(layout) -> QWidget:
        w = QWidget()
        w.setLayout(layout)
        return w

    # ---- naplnění -----------------------------------------------------
    def _nacti(self, s: Template) -> None:
        self.ed_nazev.setText(s.nazev)
        self.ed_popis.setText(s.popis)
        self.lbl_dokument.setText(s.dokument)
        self.lbl_dokument.setStyleSheet("color: black;")
        self.spin_citac.setValue(s.citac)
        for f in s.pole:
            self._pridej_radek(f)

    def _pridej_radek(self, f: Field) -> None:
        r = self.tabulka.rowCount()
        self.tabulka.insertRow(r)
        polozka_klic = QTableWidgetItem(f.klic)
        polozka_klic.setToolTip("Klikni pro zkopírování {{" + f.klic + "}} do schránky")
        self.tabulka.setItem(r, 0, polozka_klic)
        self.tabulka.setItem(r, 1, QTableWidgetItem(f.popisek))

        combo = QComboBox()
        for t in TYPY:
            combo.addItem(t.popisek, t.value)
        combo.setCurrentIndex(TYPY.index(f.typ))
        self.tabulka.setCellWidget(r, 2, combo)

        chk = QCheckBox()
        chk.setChecked(f.povinne)
        obal = QWidget()
        lay = QHBoxLayout(obal)
        lay.addWidget(chk)
        lay.setAlignment(Qt.AlignCenter)
        lay.setContentsMargins(0, 0, 0, 0)
        obal.setProperty("checkbox", chk)
        self.tabulka.setCellWidget(r, 3, obal)

        self.tabulka.setItem(r, 4, QTableWidgetItem("; ".join(f.moznosti)))
        self.tabulka.setItem(r, 5, QTableWidgetItem(f.vychozi))

    def _smaz_radek(self) -> None:
        for idx in sorted({i.row() for i in self.tabulka.selectedIndexes()}, reverse=True):
            self.tabulka.removeRow(idx)

    def _kopiruj_klic(self, radek: int, sloupec: int) -> None:
        if sloupec != 0:
            return
        polozka = self.tabulka.item(radek, 0)
        klic = polozka.text().strip() if polozka else ""
        if not klic:
            return
        QApplication.clipboard().setText(obal(klic))
        self.status.setText(f"Zkopírováno do schránky: {obal(klic)}  – vlož do dokumentu (Ctrl+V).")

    # ---- akce ---------------------------------------------------------
    def _vyber_dokument(self) -> None:
        cesta, _ = QFileDialog.getOpenFileName(
            self, "Vyber dokument šablony", "", "Dokumenty (*.docx *.odt)"
        )
        if cesta:
            self._novy_dokument = cesta
            self.lbl_dokument.setText(os.path.basename(cesta))
            self.lbl_dokument.setStyleSheet("color: black;")

    def _aktualni_dokument(self) -> str | None:
        if self._novy_dokument:
            return self._novy_dokument
        if self.sablona:
            return self.sablona.cesta_dokumentu()
        return None

    def _nacti_pole_z_dokumentu(self) -> None:
        cesta = self._aktualni_dokument()
        if not cesta or not os.path.isfile(cesta):
            QMessageBox.warning(self, "Chybí dokument", "Nejdřív vyber dokument šablony.")
            return
        try:
            klice = Generator.scan(cesta)
        except GeneratorError as e:
            QMessageBox.critical(self, "Chyba", str(e))
            return
        existujici = {self.tabulka.item(r, 0).text() for r in range(self.tabulka.rowCount())}
        pridano = 0
        for klic in klice:
            if klic not in existujici:
                self._pridej_radek(Field(klic=klic))
                pridano += 1
        QMessageBox.information(
            self, "Načteno",
            f"Nalezeno {len(klice)} polí v dokumentu, nově přidáno {pridano}."
            if klice else "V dokumentu nebyla nalezena žádná pole {{...}}.",
        )

    def _posbirej_pole(self) -> list[Field]:
        pole = []
        for r in range(self.tabulka.rowCount()):
            klic = (self.tabulka.item(r, 0).text() if self.tabulka.item(r, 0) else "").strip()
            if not klic:
                continue
            combo: QComboBox = self.tabulka.cellWidget(r, 2)
            chk: QCheckBox = self.tabulka.cellWidget(r, 3).property("checkbox")
            moznosti = [m.strip() for m in (self.tabulka.item(r, 4).text() if self.tabulka.item(r, 4) else "").split(";") if m.strip()]
            pole.append(Field(
                klic=klic,
                popisek=self.tabulka.item(r, 1).text() if self.tabulka.item(r, 1) else "",
                typ=FieldType(combo.currentData()),
                povinne=chk.isChecked(),
                moznosti=moznosti,
                vychozi=self.tabulka.item(r, 5).text() if self.tabulka.item(r, 5) else "",
            ))
        return pole

    def _uloz(self) -> None:
        nazev = self.ed_nazev.text().strip()
        if not nazev:
            QMessageBox.warning(self, "Chybí název", "Zadej název šablony.")
            return
        if not self._aktualni_dokument():
            QMessageBox.warning(self, "Chybí dokument", "Vyber dokument šablony.")
            return

        sablona = Template(
            nazev=nazev,
            dokument=self.sablona.dokument if self.sablona else "dokument.docx",
            popis=self.ed_popis.text().strip(),
            citac=self.spin_citac.value(),
            pole=self._posbirej_pole(),
        )
        try:
            self.storage.uloz_sablonu(sablona, zdrojovy_dokument=self._novy_dokument)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Chyba při ukládání", str(e))
            return
        self.sablona = sablona
        self.accept()
