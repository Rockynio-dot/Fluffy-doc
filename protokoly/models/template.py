"""Šablona = dokument (.docx/.odt) + definice polí."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from .field import Field


@dataclass
class Template:
    """Šablona předávacího protokolu.

    Metadata (název, popis, definice polí) se ukládají do ``sablona.json``,
    vedle něj leží samotný dokument (``dokument.docx`` nebo ``dokument.odt``).
    """

    nazev: str
    dokument: str                       # název souboru dokumentu (relativně ke složce šablony)
    popis: str = ""
    pole: list[Field] = field(default_factory=list)
    slozka: str | None = None           # absolutní cesta ke složce šablony (nastaví storage)

    # ---- práce s poli -------------------------------------------------
    def klice(self) -> list[str]:
        return [p.klic for p in self.pole]

    def pole_dle_klice(self, klic: str) -> Field | None:
        return next((p for p in self.pole if p.klic == klic), None)

    def synchronizuj_s_placeholdery(self, placeholdery: list[str]) -> tuple[list[str], list[str]]:
        """Sladí definici polí s placeholdery nalezenými v dokumentu.

        Přidá pole pro nové placeholdery a vrátí dvojici
        ``(pridane, osirele)`` – nově přidané klíče a klíče polí,
        které v dokumentu už nejsou.
        """
        existujici = set(self.klice())
        v_dokumentu = list(dict.fromkeys(placeholdery))  # zachovej pořadí, bez duplicit

        pridane = [k for k in v_dokumentu if k not in existujici]
        for klic in pridane:
            self.pole.append(Field(klic=klic))

        osirele = [k for k in existujici if k not in set(v_dokumentu)]
        return pridane, osirele

    def cesta_dokumentu(self) -> str:
        if not self.slozka:
            raise ValueError("Šablona nemá nastavenou složku (slozka).")
        return os.path.join(self.slozka, self.dokument)

    @property
    def format(self) -> str:
        """Přípona dokumentu bez tečky, např. ``docx`` nebo ``odt``."""
        return os.path.splitext(self.dokument)[1].lstrip(".").lower()

    # ---- serializace --------------------------------------------------
    def to_dict(self) -> dict[str, Any]:
        return {
            "nazev": self.nazev,
            "popis": self.popis,
            "dokument": self.dokument,
            "pole": [p.to_dict() for p in self.pole],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any], slozka: str | None = None) -> "Template":
        return cls(
            nazev=data["nazev"],
            dokument=data["dokument"],
            popis=data.get("popis", ""),
            pole=[Field.from_dict(p) for p in data.get("pole", [])],
            slozka=slozka,
        )
