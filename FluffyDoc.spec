# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec – jeden spustitelný soubor (onefile), okenní aplikace.

Build:
    pyinstaller FluffyDoc.spec
Výstup:
    dist/FluffyDoc(.exe)
"""
import sys

from PyInstaller.utils.hooks import collect_data_files

# python-docx si nese výchozí šablonu default.docx jako datový soubor
datas = collect_data_files("docx")
# ikony a vektor pro okno aplikace
datas += [("assets/icon-256.png", "assets"), ("assets/icon.ico", "assets")]

icon = "assets/icon.ico" if sys.platform.startswith("win") else "assets/icon-256.png"

a = Analysis(
    ["run.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "PySide6.QtQuick", "PySide6.Qt3DCore"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="FluffyDoc",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # okenní aplikace (bez konzole)
    disable_windowed_traceback=False,
    icon=icon,
)
