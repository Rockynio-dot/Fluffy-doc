"""Sjednocené rozhraní nad engine pro .docx a .odt."""
from __future__ import annotations

import os

from ..models.template import Template
from . import docx_engine, odt_engine


class GeneratorError(Exception):
    pass


_ENGINY = {
    "docx": docx_engine,
    "odt": odt_engine,
}


def _engine_pro(cesta: str):
    pripona = os.path.splitext(cesta)[1].lstrip(".").lower()
    engine = _ENGINY.get(pripona)
    if engine is None:
        raise GeneratorError(
            f"Nepodporovaný formát '.{pripona}'. Podporováno: {', '.join(_ENGINY)}."
        )
    return engine


class Generator:
    """Skenuje placeholdery a generuje vyplněné dokumenty."""

    @staticmethod
    def scan(cesta_dokumentu: str) -> list[str]:
        return _engine_pro(cesta_dokumentu).scan(cesta_dokumentu)

    @staticmethod
    def generuj(sablona: Template, hodnoty_dle_klice: dict[str, str], cesta_vystupu: str) -> str:
        """Vyplní šablonu. ``hodnoty_dle_klice`` jsou syrové hodnoty z formuláře;
        naformátování a validace proběhne podle definic polí."""
        cesta_sablony = sablona.cesta_dokumentu()
        if not os.path.isfile(cesta_sablony):
            raise GeneratorError(f"Dokument šablony nenalezen: {cesta_sablony}")

        chyby = []
        pripravene: dict[str, str] = {}
        for pole in sablona.pole:
            surova = hodnoty_dle_klice.get(pole.klic, "")
            chyba = pole.validuj(surova)
            if chyba:
                chyby.append(chyba)
            pripravene[pole.klic] = pole.naformatuj(surova)

        # klíče, které jsou v dokumentu, ale nemají definici pole – vyplň tak jak přišly
        for klic, hodnota in hodnoty_dle_klice.items():
            pripravene.setdefault(klic, str(hodnota))

        if chyby:
            raise GeneratorError("\n".join(chyby))

        engine = _engine_pro(cesta_sablony)
        os.makedirs(os.path.dirname(os.path.abspath(cesta_vystupu)), exist_ok=True)
        return engine.fill(cesta_sablony, pripravene, cesta_vystupu)
