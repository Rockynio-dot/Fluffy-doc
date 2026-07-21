"""Ukládání šablon a evidence vygenerovaných protokolů do lokálních souborů.

Struktura dat::

    data/
      sablony/
        <slug>/
          sablona.json      # metadata + definice polí
          dokument.docx     # (nebo .odt) samotná šablona
      vystup/
        <slug>/
          2026-07-21_153000_seriove-cislo.docx
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import unicodedata
from datetime import datetime

from .template import Template

META_SOUBOR = "sablona.json"


def vychozi_datovy_adresar() -> str:
    """Výchozí umístění dat.

    Priorita:
    1. proměnná prostředí ``FLUFFY_DOC_DATA`` (má přednost vždy),
    2. u nainstalované aplikace (.exe / Flatpak / frozen) uživatelský datový
       adresář (Windows ``%APPDATA%``, Linux ``$XDG_DATA_HOME``, …),
    3. při běhu ze zdrojáků složka ``data`` vedle projektu (pohodlné pro vývoj).
    """
    import sys

    base = os.environ.get("FLUFFY_DOC_DATA")
    if base:
        return base

    nainstalovano = getattr(sys, "frozen", False) or bool(os.environ.get("FLATPAK_ID"))
    if nainstalovano:
        return os.path.join(_uzivatelsky_datovy_adresar(), "FluffyDoc")
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def _uzivatelsky_datovy_adresar() -> str:
    if sys.platform.startswith("win"):
        return os.environ.get("APPDATA") or os.path.expanduser("~")
    if sys.platform == "darwin":
        return os.path.expanduser("~/Library/Application Support")
    return os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share")


class Storage:
    def __init__(self, datovy_adresar: str | None = None) -> None:
        self.datovy_adresar = datovy_adresar or vychozi_datovy_adresar()
        self.sablony_dir = os.path.join(self.datovy_adresar, "sablony")
        self.vystup_dir = os.path.join(self.datovy_adresar, "vystup")
        os.makedirs(self.sablony_dir, exist_ok=True)
        os.makedirs(self.vystup_dir, exist_ok=True)

    # ---- šablony ------------------------------------------------------
    def seznam_sablon(self) -> list[Template]:
        sablony: list[Template] = []
        for nazev in sorted(os.listdir(self.sablony_dir)):
            slozka = os.path.join(self.sablony_dir, nazev)
            meta = os.path.join(slozka, META_SOUBOR)
            if os.path.isfile(meta):
                sablony.append(self._nacti_z_meta(meta, slozka))
        return sablony

    def nacti_sablonu(self, slug: str) -> Template:
        slozka = os.path.join(self.sablony_dir, slug)
        meta = os.path.join(slozka, META_SOUBOR)
        if not os.path.isfile(meta):
            raise FileNotFoundError(f"Šablona '{slug}' neexistuje.")
        return self._nacti_z_meta(meta, slozka)

    def _nacti_z_meta(self, meta_cesta: str, slozka: str) -> Template:
        with open(meta_cesta, encoding="utf-8") as f:
            data = json.load(f)
        return Template.from_dict(data, slozka=slozka)

    def uloz_sablonu(self, sablona: Template, zdrojovy_dokument: str | None = None) -> Template:
        """Uloží šablonu. ``zdrojovy_dokument`` je cesta k Word/ODT souboru,
        který se zkopíruje do složky šablony (jen při zakládání/výměně)."""
        slug = slugify(sablona.nazev)
        slozka = os.path.join(self.sablony_dir, slug)
        os.makedirs(slozka, exist_ok=True)
        sablona.slozka = slozka

        if zdrojovy_dokument:
            pripona = os.path.splitext(zdrojovy_dokument)[1].lower()
            sablona.dokument = f"dokument{pripona}"
            cil = os.path.join(slozka, sablona.dokument)
            if os.path.abspath(zdrojovy_dokument) != os.path.abspath(cil):
                shutil.copyfile(zdrojovy_dokument, cil)

        with open(os.path.join(slozka, META_SOUBOR), "w", encoding="utf-8") as f:
            json.dump(sablona.to_dict(), f, ensure_ascii=False, indent=2)
        return sablona

    def smaz_sablonu(self, slug: str) -> None:
        slozka = os.path.join(self.sablony_dir, slug)
        if os.path.isdir(slozka):
            shutil.rmtree(slozka)

    # ---- výstupy ------------------------------------------------------
    def cesta_pro_vystup(self, sablona: Template, oznaceni: str = "") -> str:
        slug = slugify(sablona.nazev)
        slozka = os.path.join(self.vystup_dir, slug)
        os.makedirs(slozka, exist_ok=True)
        casova = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        cast = f"_{slugify(oznaceni)}" if oznaceni else ""
        nazev = f"{casova}{cast}.{sablona.format}"
        return os.path.join(slozka, nazev)


def slugify(text: str) -> str:
    """Bezpečný název pro souborový systém (bez diakritiky a mezer)."""
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text or "sablona"
