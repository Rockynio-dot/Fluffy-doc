# Fluffy-Doc — generátor předávacích protokolů

Desktopová aplikace (Python + Qt) pro tvorbu **předávacích protokolů** k PC/NTB,
mobilním telefonům, SIM kartám apod. Šablonu si připravíš ve Wordu nebo v ODT,
místa k vyplnění označíš zástupnými poli `{{klic}}` a v appce je pak jen
vyplníš do formuláře — vygeneruje se hotový dokument ve formátu **`.docx`**
i **`.odt`** (OpenDocument).

## Jak to funguje

1. **Šablona** = dokument (`.docx`/`.odt`) + definice polí (JSON).
   V dokumentu napíšeš zástupná pole, např.:

   ```
   Sériové číslo: {{seriove_cislo}}
   Model:         {{model}}
   ```

2. Aplikace dokument **naskenuje**, najde všechna pole `{{...}}` a nabídne
   je ke správě (popisek, typ, povinnost, výběr z možností, výchozí hodnota).

3. Při generování se vyplní **formulář** poskládaný podle polí a vznikne
   hotový protokol ve složce `data/vystup/`.

## Instalace

```bash
python -m venv .venv
# Windows:  .venv\Scripts\activate
# Linux/mac: source .venv/bin/activate
pip install -r requirements.txt
```

> Poznámka: pro ODT není potřeba žádná knihovna navíc — pracuje se přímo
> s ODF (ZIP + XML). `.docx` využívá `python-docx`, GUI běží na `PySide6`.

## Spuštění

```bash
# (jednorázově) vytvoř ukázkové šablony PC/NTB, telefon, SIM:
python examples/vytvor_ukazkove_sablony.py

# spusť aplikaci:
python -m protokoly
```

Po instalaci přes `pip install .` je k dispozici i příkaz `fluffy-doc`.

## Práce se šablonami

### Vytvoření šablony
1. V appce klikni na **➕ Nová šablona**.
2. Zadej název, popis a vyber dokument (`.docx` nebo `.odt`), který máš
   připravený se zástupnými poli `{{klic}}`.
3. Klikni na **↻ Načíst pole z dokumentu** — pole se doplní do tabulky.
4. U každého pole nastav **popisek**, **typ** (text, datum, číslo, výběr,
   ano/ne, víceřádkový text), **povinnost**, případně **možnosti** a
   **výchozí hodnotu**.
5. **Uložit**.

### Zápis polí v dokumentu
- Placeholder má tvar `{{klic}}`; klíč smí obsahovat písmena, číslice a `_`.
- Stejný klíč můžeš použít vícekrát — vyplní se všude stejně.
- Doporučení pro `.odt`: nech `{{ }}` jako souvislý text (neaplikuj uvnitř
  různé formátování), aby se placeholder spolehlivě našel.

### Typy polí
| Typ | Chování |
|-----|---------|
| Text | jednořádkový text |
| Víceřádkový text | zalomení řádků se přenese do dokumentu |
| Číslo | validace na číslo |
| Datum | výběr z kalendáře, formát `DD.MM.RRRR` |
| Výběr z možností | rozbalovací seznam (pole *Možnosti*, oddělené `;`) |
| Ano/Ne | zaškrtávátko → do dokumentu se vloží `☒ Ano` / `☐ Ne` |

## Uložení dat

Vše je v lokálních souborech (výchozí složka `data/`, lze změnit proměnnou
prostředí `FLUFFY_DOC_DATA`):

```
data/
  sablony/<nazev>/sablona.json   # definice polí
  sablony/<nazev>/dokument.docx  # (nebo .odt) samotná šablona
  vystup/<nazev>/...             # vygenerované protokoly
```

Snadno se to zálohuje i sdílí přes síťový disk.

## Struktura projektu

```
protokoly/
  models/     # Field, Template, ukládání do souborů
  core/       # skenování a vyplňování .docx (docx_engine) a .odt (odt_engine)
  ui/         # Qt GUI: hlavní okno, editor šablon, vyplňovací formulář
  app.py      # vstupní bod
examples/     # generátor ukázkových šablon
tests/        # testy jádra (pytest)
```

## Testy

```bash
pip install pytest
python -m pytest
```
