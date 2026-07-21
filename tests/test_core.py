"""Testy jádra: skenování placeholderů a vyplňování .docx i .odt."""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docx import Document

from protokoly.core import Generator, najdi_klice
from protokoly.core import docx_engine, odt_engine
from protokoly.models import Field, FieldType, Template


# ---- placeholder regex -----------------------------------------------
def test_najdi_klice_poradi_a_bez_duplicit():
    text = "SN: {{seriove_cislo}} model {{ model }} a znovu {{seriove_cislo}}"
    assert najdi_klice(text) == ["seriove_cislo", "model"]


# ---- pomocníci --------------------------------------------------------
def _docx_se_sablonou(cesta):
    doc = Document()
    doc.add_paragraph("Sériové číslo: {{seriove_cislo}}")
    # placeholder rozdělený do více runů (simulace Wordu)
    p = doc.add_paragraph()
    p.add_run("Model: {{mo")
    p.add_run("del}} konec")
    doc.add_paragraph("Poznámka: {{poznamka}}")
    doc.save(cesta)


def _odt_se_sablonou(cesta):
    content = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"'
        ' xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2">'
        "<office:body><office:text>"
        "<text:p>Sériové číslo: {{seriove_cislo}}</text:p>"
        "<text:p>Model: {{model}}</text:p>"
        "<text:p>Poznámka: {{poznamka}}</text:p>"
        "</office:text></office:body></office:document-content>"
    )
    with zipfile.ZipFile(cesta, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("mimetype", "application/vnd.oasis.opendocument.text", zipfile.ZIP_STORED)
        z.writestr("content.xml", content)


def _text_docx(cesta):
    return "\n".join(p.text for p in Document(cesta).paragraphs)


def _text_odt(cesta):
    with zipfile.ZipFile(cesta) as z:
        return z.read("content.xml").decode("utf-8")


# ---- docx -------------------------------------------------------------
def test_docx_scan_a_fill(tmp_path):
    sablona = tmp_path / "s.docx"
    _docx_se_sablonou(str(sablona))

    assert set(docx_engine.scan(str(sablona))) == {"seriove_cislo", "model", "poznamka"}

    vystup = tmp_path / "out.docx"
    docx_engine.fill(str(sablona), {
        "seriove_cislo": "SN-123",
        "model": "ThinkPad X1",     # rozdělený placeholder
        "poznamka": "řádek 1\nřádek 2",
    }, str(vystup))

    text = _text_docx(str(vystup))
    assert "SN-123" in text
    assert "ThinkPad X1 konec" in text     # okolní text zachován
    assert "{{" not in text
    assert "řádek 1" in text and "řádek 2" in text


# ---- odt --------------------------------------------------------------
def test_odt_scan_a_fill(tmp_path):
    sablona = tmp_path / "s.odt"
    _odt_se_sablonou(str(sablona))

    assert set(odt_engine.scan(str(sablona))) == {"seriove_cislo", "model", "poznamka"}

    vystup = tmp_path / "out.odt"
    odt_engine.fill(str(sablona), {
        "seriove_cislo": "SN-9 & spol.",   # XML-escaping
        "model": "Dell",
        "poznamka": "a\nb",
    }, str(vystup))

    xml = _text_odt(str(vystup))
    assert "SN-9 &amp; spol." in xml
    assert "<text:line-break/>" in xml
    assert "{{" not in xml
    # mimetype zůstal nekomprimovaný
    with zipfile.ZipFile(str(vystup)) as z:
        assert z.getinfo("mimetype").compress_type == zipfile.ZIP_STORED


# ---- generator + validace polí ---------------------------------------
def test_generator_validuje_povinne(tmp_path):
    sablona_doc = tmp_path / "s.docx"
    _docx_se_sablonou(str(sablona_doc))
    t = Template(nazev="Test", dokument="s.docx", slozka=str(tmp_path), pole=[
        Field("seriove_cislo", "S/N", FieldType.TEXT, povinne=True),
        Field("model", "Model", FieldType.TEXT),
        Field("poznamka", "Poznámka", FieldType.MULTILINE),
    ])

    import pytest
    with pytest.raises(Exception):
        Generator.generuj(t, {"model": "X"}, str(tmp_path / "o.docx"))

    out = Generator.generuj(t, {"seriove_cislo": "SN-1", "model": "X", "poznamka": ""},
                            str(tmp_path / "o.docx"))
    assert os.path.isfile(out)


def test_checkbox_formatovani():
    f = Field("souhlas", "Souhlas", FieldType.CHECKBOX)
    assert f.naformatuj("ano") == "☒ Ano"
    assert f.naformatuj("") == "☐ Ne"
