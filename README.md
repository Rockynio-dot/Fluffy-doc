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

Na Linuxu Qt (PySide6) potřebuje pár systémových knihoven. Když GUI spadne na
`libEGL.so.1: cannot open shared object file`, doinstaluj je:

```bash
# Fedora:
sudo dnf install libglvnd-egl mesa-libGL libxkbcommon dbus-libs
# Debian/Ubuntu:
sudo apt install libegl1 libgl1 libxkbcommon0 libdbus-1-3 libglib2.0-0
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
- Placeholder má tvar `{{klic}}`; klíč smí obsahovat písmena (**včetně české
  diakritiky**, např. `{{Značka_telefonu}}`), číslice a `_`.
- Stejný klíč můžeš použít vícekrát — vyplní se všude stejně.
- **Tip:** v editoru šablony i v pravém panelu hlavního okna stačí kliknout na
  `{{klic}}` a rovnou se zkopíruje do schránky — pak jen `Ctrl+V` do dokumentu.
- ODT z LibreOffice, kde je placeholder rozdělený (např. kvůli kontrole
  pravopisu), appka zvládne — části `{{ }}` si sama spojí.

### Typy polí
| Typ | Chování |
|-----|---------|
| Text | jednořádkový text |
| Víceřádkový text | zalomení řádků se přenese do dokumentu |
| Číslo | validace na číslo |
| Datum | výběr z kalendáře, formát `DD.MM.RRRR` |
| Výběr z možností | rozbalovací seznam (pole *Možnosti*, oddělené `;`) |
| Ano/Ne | zaškrtávátko → do dokumentu se vloží `☒ Ano` / `☐ Ne` |
| Automatické číslo | číslo protokolu z čítače, viz níže |

### Automatické číslování protokolů
Číslo protokolu se umí generovat samo a **čítač i vzor se pamatují u každé
šablony zvlášť** (v jejím `sablona.json`).

1. Přidej pole typu **Automatické číslo** (např. klíč `cislo_protokolu`).
2. Do sloupce **Výchozí / Vzor čísla** napiš vzor, např.
   `PST-{rok}-{poradi:04d}` → `PST-2026-0007`.
   Použitelné značky: `{poradi}`, `{rok}`, `{mesic}`, `{den}`
   (lze i s formátem, třeba `{poradi:04d}` = čtyřmístné číslo).
3. Ve formuláři se další číslo předvyplní a je jen ke čtení; po vygenerování
   se **čítač automaticky posune o 1**.
4. Aktuální stav čítače (a tím i další číslo) můžeš kdykoli ručně nastavit
   v editoru šablony u položky *Čítač protokolu*.

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

## Balíčkování a instalace

Hotové balíčky vznikají v GitHub Actions a přikládají se k **Releases**.
Nové vydání se spustí štítkem (tagem):

```bash
git tag v0.1.0
git push origin v0.1.0   # spustí build .exe i Flatpaku a vytvoří Release
```

### Windows (.exe)
- **Uživatel:** stáhni `FluffyDoc.exe` z Releases a spusť (jeden soubor, bez
  instalace). Data se ukládají do `%APPDATA%\FluffyDoc`.
- **Lokální build:**
  ```bash
  pip install -r requirements.txt pyinstaller
  python assets/vytvor_ikony.py          # vygeneruje ikony
  pyinstaller FluffyDoc.spec --noconfirm
  # výstup: dist/FluffyDoc.exe
  ```

### Linux (Flatpak)
- **Uživatel:**
  ```bash
  flatpak install --user FluffyDoc.flatpak
  flatpak run cz.prosecurity.FluffyDoc
  ```
- **Lokální build:**
  ```bash
  flatpak install flathub org.freedesktop.Platform//23.08 org.freedesktop.Sdk//23.08
  flatpak-builder --user --install --force-clean build-dir \
      packaging/flatpak/cz.prosecurity.FluffyDoc.yaml
  ```
  Data se ukládají do `~/.var/app/cz.prosecurity.FluffyDoc/`.

  > Závislosti (PySide6, python-docx) se instalují přes pip, proto build
  > potřebuje síť. Pro interní/CI použití je to v pořádku; pro Flathub by bylo
  > nutné dodat wheels jako offline zdroje.

### Umístění dat
| Prostředí | Složka s daty |
|-----------|---------------|
| Vývoj (ze zdrojáků) | `data/` v projektu |
| Windows `.exe` | `%APPDATA%\FluffyDoc` |
| Flatpak | `~/.var/app/cz.prosecurity.FluffyDoc/…` |
| Kdekoli | přepíše proměnná `FLUFFY_DOC_DATA` |

## Struktura projektu

```
protokoly/
  models/     # Field, Template, ukládání do souborů
  core/       # skenování a vyplňování .docx (docx_engine) a .odt (odt_engine)
  ui/         # Qt GUI: hlavní okno, editor šablon, vyplňovací formulář
  app.py      # vstupní bod
run.py        # spouštěč pro PyInstaller
FluffyDoc.spec # PyInstaller (onefile .exe)
assets/       # ikony (SVG/PNG/ICO) + generátor ikon
packaging/
  linux/      # .desktop a AppStream metainfo
  flatpak/    # Flatpak manifest
.github/workflows/  # CI (testy) + build .exe a Flatpaku
examples/     # generátor ukázkových šablon
tests/        # testy jádra (pytest)
```

## Testy

```bash
pip install pytest
python -m pytest
```
