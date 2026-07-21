"""Společná logika zástupných polí (placeholderů).

Placeholder má tvar ``{{klic}}`` – např. ``{{seriove_cislo}}``.
Mezery uvnitř jsou povolené: ``{{ seriove_cislo }}``.
Klíč smí obsahovat i českou diakritiku, např. ``{{Značka_telefonu}}``.
"""
from __future__ import annotations

import re
import unicodedata

# ``\w`` v Pythonu 3 zahrnuje i Unicode písmena (č, ř, í, é, ž, á …) a ``_``.
PLACEHOLDER_RE = re.compile(r"\{\{\s*(\w+)\s*\}\}", re.UNICODE)


def normalizuj(text: str) -> str:
    """Sjednotí Unicode na složený tvar (NFC).

    LibreOffice (a některé systémy) ukládají diakritiku rozloženě (NFD),
    tj. ``č`` = ``c`` + kombinující háček. Kombinující značka není „slovní
    znak“, takže by se placeholder ``{{Značka}}`` vůbec nenašel. Po
    normalizaci na NFC je klíč souvislé slovo a vše sedí.
    """
    return unicodedata.normalize("NFC", text)


def najdi_klice(text: str) -> list[str]:
    """Vrátí klíče placeholderů v textu v pořadí výskytu (bez duplicit)."""
    return list(dict.fromkeys(PLACEHOLDER_RE.findall(normalizuj(text))))


def obal(klic: str) -> str:
    """Vrátí zápis placeholderu pro daný klíč, tj. ``{{klic}}``."""
    return "{{" + klic + "}}"
