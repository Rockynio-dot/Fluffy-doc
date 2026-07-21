#!/usr/bin/env python3
"""Vygeneruje rastrové ikony (PNG + Windows ICO) z jednoduchého vektoru.

Kreslí se přímo v Pillow (nezávisí na rsvg/inkscape). Motiv odpovídá
assets/icon.svg – modrý dokument se zlatým zaškrtnutím.
"""
from __future__ import annotations

import os

from PIL import Image, ImageDraw

ZDE = os.path.dirname(os.path.abspath(__file__))


def _kresli(velikost: int) -> Image.Image:
    # kresli ve velkém a zmenši (antialiasing)
    s = 1024
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m = s / 256.0

    def sc(*xs):
        return [x * m for x in xs]

    # pozadí – svislý přechod modré
    horni, dolni = (36, 114, 209), (18, 83, 159)
    plocha = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    pd = ImageDraw.Draw(plocha)
    for y in range(s):
        t = y / s
        barva = tuple(int(horni[i] + (dolni[i] - horni[i]) * t) for i in range(3)) + (255,)
        pd.line([(0, y), (s, y)], fill=barva)
    maska = Image.new("L", (s, s), 0)
    ImageDraw.Draw(maska).rounded_rectangle(sc(8, 8, 248, 248), radius=48 * m, fill=255)
    img.paste(plocha, (0, 0), maska)

    # dokument
    d.rounded_rectangle(sc(72, 52, 176, 208), radius=8 * m, fill=(255, 255, 255, 255))
    d.polygon(sc(144, 52, 176, 84, 144, 84), fill=(207, 224, 245, 255))

    # řádky (pole)
    for y, w in ((104, 72), (128, 72), (152, 44)):
        d.rounded_rectangle(sc(92, y, 92 + w, y + 10), radius=5 * m, fill=(199, 212, 230, 255))

    # zlaté zaškrtnutí
    d.ellipse(sc(134, 142, 202, 210), fill=(245, 184, 0, 255))
    d.line(sc(152, 176, 163, 188, 185, 163), fill=(18, 83, 159, 255),
           width=int(9 * m), joint="curve")

    return img.resize((velikost, velikost), Image.LANCZOS)


def main() -> None:
    for v in (16, 32, 48, 64, 128, 256, 512):
        _kresli(v).save(os.path.join(ZDE, f"icon-{v}.png"))
    # Windows ICO s více velikostmi
    _kresli(256).save(
        os.path.join(ZDE, "icon.ico"),
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
    )
    print("Ikony vytvořeny v", ZDE)


if __name__ == "__main__":
    main()
