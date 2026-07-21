"""Definice jednoho pole šablony."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Any


class FieldType(str, Enum):
    """Podporované typy polí."""

    TEXT = "text"            # jednořádkový text
    MULTILINE = "multiline"  # víceřádkový text
    NUMBER = "number"        # číslo
    DATE = "date"            # datum (formát DD.MM.RRRR)
    CHOICE = "choice"        # výběr z možností
    CHECKBOX = "checkbox"    # ano/ne
    AUTO = "auto"            # automatické číslo protokolu (čítač)

    @property
    def popisek(self) -> str:
        return {
            FieldType.TEXT: "Text",
            FieldType.MULTILINE: "Víceřádkový text",
            FieldType.NUMBER: "Číslo",
            FieldType.DATE: "Datum",
            FieldType.CHOICE: "Výběr z možností",
            FieldType.CHECKBOX: "Ano/Ne",
            FieldType.AUTO: "Automatické číslo",
        }[self]


@dataclass
class Field:
    """Jedno pole šablony, na které se v dokumentu odkazuje přes ``{{klic}}``."""

    klic: str                                    # identifikátor v dokumentu, např. "seriove_cislo"
    popisek: str = ""                            # co se zobrazí v appce, např. "Sériové číslo"
    typ: FieldType = FieldType.TEXT
    povinne: bool = False
    vychozi: str = ""                            # výchozí hodnota
    moznosti: list[str] = field(default_factory=list)  # pro typ CHOICE

    def __post_init__(self) -> None:
        if isinstance(self.typ, str):
            self.typ = FieldType(self.typ)
        if not self.popisek:
            # z "seriove_cislo" uděláme "Seriove cislo"
            self.popisek = self.klic.replace("_", " ").strip().capitalize()

    # ---- validace vyplněné hodnoty ------------------------------------
    def validuj(self, hodnota: str) -> str | None:
        """Vrátí chybovou hlášku, nebo ``None`` když je hodnota v pořádku."""
        if self.typ == FieldType.AUTO:
            return None  # generuje se automaticky, nevaliduje se
        hodnota = (hodnota or "").strip()
        if self.povinne and not hodnota and self.typ != FieldType.CHECKBOX:
            return f"Pole „{self.popisek}“ je povinné."
        if not hodnota:
            return None
        if self.typ == FieldType.NUMBER:
            try:
                float(hodnota.replace(",", "."))
            except ValueError:
                return f"Pole „{self.popisek}“ musí být číslo."
        if self.typ == FieldType.DATE:
            if not _je_datum(hodnota):
                return f"Pole „{self.popisek}“ musí být datum ve formátu DD.MM.RRRR."
        if self.typ == FieldType.CHOICE and self.moznosti and hodnota not in self.moznosti:
            return f"Pole „{self.popisek}“ musí být jedna z možností: {', '.join(self.moznosti)}."
        return None

    def naformatuj(self, hodnota: str) -> str:
        """Připraví hodnotu k vložení do dokumentu."""
        hodnota = (hodnota or "").strip()
        if not hodnota and self.vychozi:
            hodnota = self.vychozi
        if self.typ == FieldType.CHECKBOX:
            return "☒ Ano" if _je_pravda(hodnota) else "☐ Ne"
        return hodnota

    def format_auto(self, poradi: int, kdy: date | None = None) -> str:
        """Sestaví hodnotu automatického čísla podle vzoru ve ``vychozi``.

        Ve vzoru lze použít ``{poradi}`` (pořadové číslo), ``{rok}``,
        ``{mesic}`` a ``{den}`` – včetně formátování, např.
        ``PST-{rok}-{poradi:04d}`` → ``PST-2026-0007``.
        Když vzor chybí, použije se čtyřmístné pořadové číslo.
        """
        kdy = kdy or date.today()
        vzor = self.vychozi or "{poradi:04d}"
        try:
            return vzor.format(poradi=poradi, rok=kdy.year, mesic=kdy.month, den=kdy.day)
        except (KeyError, ValueError, IndexError):
            return str(poradi)

    # ---- serializace --------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "klic": self.klic,
            "popisek": self.popisek,
            "typ": self.typ.value,
            "povinne": self.povinne,
            "vychozi": self.vychozi,
            "moznosti": list(self.moznosti),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Field":
        return cls(
            klic=data["klic"],
            popisek=data.get("popisek", ""),
            typ=FieldType(data.get("typ", "text")),
            povinne=bool(data.get("povinne", False)),
            vychozi=data.get("vychozi", ""),
            moznosti=list(data.get("moznosti", [])),
        )


def _je_pravda(hodnota: str) -> bool:
    return hodnota.strip().lower() in {"ano", "yes", "true", "1", "x", "☒"}


def _je_datum(hodnota: str) -> bool:
    for sep in (".", "/", "-"):
        casti = hodnota.replace(" ", "").split(sep)
        if len(casti) == 3:
            try:
                d, m, r = (int(c) for c in casti)
                date(r if r > 31 else 2000 + r if r < 100 else r, m, d)
                return True
            except (ValueError, TypeError):
                continue
    return False
