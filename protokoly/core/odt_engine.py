"""Skenování a vyplňování šablon ve formátu .odt (OpenDocument Text).

ODT je ZIP archiv, obsah leží v ``content.xml`` (tělo) a ``styles.xml``
(záhlaví/zápatí). Nepotřebujeme žádnou externí knihovnu – pracujeme přímo
s XML, jen placeholder ``{{klic}}`` nahradíme za XML-escapovanou hodnotu.

Poznámka: aby engine placeholder našel i po vyplnění, musí být v ODT
souboru zapsaný jako souvislý text (což je běžné, pokud dovnitř
``{{ }}`` neaplikuješ různé formátování). Víceřádkové hodnoty se převádějí
na ODF zalomení řádku ``<text:line-break/>``.
"""
from __future__ import annotations

import re
import zipfile
from xml.sax.saxutils import escape

from .placeholder import PLACEHOLDER_RE, najdi_klice, normalizuj

_CASTI = ("content.xml", "styles.xml")

# jakýkoli <text:span …> nebo </text:span> – LibreOffice do nich placeholder
# často zabalí (i vnořeně) kvůli formátování / kontrole pravopisu
_SPAN_TAG = re.compile(r"</?text:span\b[^>]*>")
# placeholder, který může uvnitř obsahovat XML značky (ale ne konec odstavce)
_PLACEHOLDER_S_TAGY = re.compile(r"\{\{(?:(?!</text:p>).)*?\}\}", re.DOTALL)


def scan(cesta: str) -> list[str]:
    """Vrátí seznam klíčů placeholderů použitých v dokumentu."""
    klice: list[str] = []
    with zipfile.ZipFile(cesta) as z:
        for cast in _CASTI:
            if cast in z.namelist():
                xml = z.read(cast).decode("utf-8")
                klice.extend(najdi_klice(_jen_text(xml)))
    return list(dict.fromkeys(klice))


def fill(cesta_sablony: str, hodnoty: dict[str, str], cesta_vystupu: str) -> str:
    """Vyplní šablonu hodnotami a uloží výsledek. Vrací cestu k výstupu."""
    with zipfile.ZipFile(cesta_sablony) as z:
        polozky = {info.filename: z.read(info.filename) for info in z.infolist()}
        infolist = z.infolist()

    for cast in _CASTI:
        if cast in polozky:
            xml = polozky[cast].decode("utf-8")
            xml = normalizuj(xml)          # NFD → NFC, ať klíče s diakritikou sedí
            xml = _slouc_rozdelene(xml)
            polozky[cast] = _nahrad(xml, hodnoty).encode("utf-8")

    with zipfile.ZipFile(cesta_vystupu, "w", zipfile.ZIP_DEFLATED) as z:
        # 'mimetype' musí být první a nekomprimovaný (požadavek ODF)
        if "mimetype" in polozky:
            z.writestr(_info("mimetype"), polozky["mimetype"], zipfile.ZIP_STORED)
        for info in infolist:
            if info.filename == "mimetype":
                continue
            z.writestr(info.filename, polozky[info.filename])
    return cesta_vystupu


def _slouc_rozdelene(xml: str) -> str:
    """Spojí placeholder, který LibreOffice rozdělil do více ``<text:span>``.

    Uvnitř každého úseku ``{{ … }}`` odstraní všechny span-značky (i vnořené),
    takže se placeholder stane souvislým textem ``{{klic}}``. Vnější span
    (otevřený před ``{{`` a zavřený za ``}}``) zůstane, XML tak zůstává validní.
    Úsek se nikdy nerozšíří přes konec odstavce (``</text:p>``).
    """
    def oprav(shoda: re.Match) -> str:
        return _SPAN_TAG.sub("", shoda.group(0))

    return _PLACEHOLDER_S_TAGY.sub(oprav, xml)


def _nahrad(xml: str, hodnoty: dict[str, str]) -> str:
    def repl(shoda: re.Match) -> str:
        klic = shoda.group(1)
        if klic not in hodnoty:
            return shoda.group(0)
        return _odf_text(hodnoty[klic])

    return PLACEHOLDER_RE.sub(repl, xml)


def _odf_text(hodnota: str) -> str:
    """XML-escapovaná hodnota se zalomením řádků jako <text:line-break/>."""
    radky = str(hodnota).split("\n")
    return "<text:line-break/>".join(escape(r) for r in radky)


def _jen_text(xml: str) -> str:
    """Zahodí XML značky, ať scan nezachytí placeholdery uvnitř atributů."""
    return re.sub(r"<[^>]+>", "", xml)


def _info(nazev: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(nazev)
    info.compress_type = zipfile.ZIP_STORED
    return info
