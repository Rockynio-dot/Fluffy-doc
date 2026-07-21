#!/usr/bin/env python3
"""Spouštěč aplikace – vstupní bod pro PyInstaller (.exe) i běžné spuštění."""
import sys

from protokoly.app import main

if __name__ == "__main__":
    sys.exit(main())
