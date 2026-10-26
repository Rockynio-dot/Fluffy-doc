#!/usr/bin/env bash
# Přidá Fluffy-Doc mezi aplikace (GNOME/KDE) s ikonou – pro běh ze zdrojáků.
# Spuštění:  ./nainstaluj-ikonu.sh
set -euo pipefail

APPID="cz.prosecurity.FluffyDoc"

# složka projektu = kde leží tenhle skript
REPO="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

# python z virtuálního prostředí, jinak systémový
if [ -x "$REPO/.venv/bin/python" ]; then
    PY="$REPO/.venv/bin/python"
else
    PY="$(command -v python3 || command -v python)"
    echo "⚠  Virtuální prostředí .venv nenalezeno, použiju $PY."
    echo "   Pokud appka nenaběhne, vytvoř ho: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
fi

# --- ikony do uživatelského motivu ---
install -Dm644 "$REPO/assets/icon-256.png" \
    "$HOME/.local/share/icons/hicolor/256x256/apps/$APPID.png"
install -Dm644 "$REPO/assets/icon-128.png" \
    "$HOME/.local/share/icons/hicolor/128x128/apps/$APPID.png"
install -Dm644 "$REPO/assets/icon.svg" \
    "$HOME/.local/share/icons/hicolor/scalable/apps/$APPID.svg"

# --- položka v nabídce aplikací ---
DESKTOP="$HOME/.local/share/applications/$APPID.desktop"
mkdir -p "$(dirname "$DESKTOP")"
cat > "$DESKTOP" <<EOF
[Desktop Entry]
Type=Application
Name=Fluffy-Doc
GenericName=Generátor předávacích protokolů
Comment=Tvorba předávacích protokolů z šablon (.docx / .odt)
Exec=$PY -m protokoly
Path=$REPO
Icon=$APPID
Categories=Office;
Keywords=protokol;šablona;docx;odt;předání;
Terminal=false
StartupNotify=true
EOF
chmod +x "$DESKTOP" 2>/dev/null || true

# --- obnov cache (ať se ikona a položka hned objeví) ---
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor" 2>/dev/null || true

echo
echo "✅ Hotovo. Appka „Fluffy-Doc“ je v nabídce aplikací."
echo "   (V GNOME stiskni Super a napiš „Fluffy“. Kdyby se hned neukázala,"
echo "    odhlas se a přihlas, nebo restartuj GNOME Shell.)"
