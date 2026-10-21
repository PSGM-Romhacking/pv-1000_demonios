#!/usr/bin/env python3
"""The cartridge cover (395 × 600), following the Mil Capivaras homebrew covers: the
blue template (the Tutankham cover with the red swapped for blue) and, in place of the
illustration, an artwork: the portrait of Aluísio Azevedo as a ghost in the starless sky,
over the silhouette of the dead town, with one window lit by a candle.

Output: screenshots/cover.png.  Usage:  python3 src/tools/cover.py
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = ROOT.parent / "mil_capivaras/apps/mil_capivaras/assets/covers/template-homebrew.png"
PORTRAIT = ROOT / "src" / "art" / "sources" / "aluisio-azevedo.jpg"
TOP, BOT = 49, 500                      # the illustration takes rows 49..499
SIGNATURE = "PÉRICLES S. 2026"
BLUE = (13, 13, 179)                    # the color of the template's bands
DIRTY = [(44, TOP), (BOT, BOT + 5)]     # template rows with leftovers of the original art's border
WIDTH, HEIGHT = 395, BOT - TOP


def logo(txt, color, k):
    """the text in the game font, enlarged k times. Accented letters use the full letter with
    the accent on top, outside the line (on screen, the 8 × 8 tile forces the letter to shrink)"""
    im = Image.new("RGBA", (len(txt) * 8, 10), (0, 0, 0, 0))
    px = im.load()
    for i, ch in enumerate(txt):
        if ch in font.ACCENTS:
            base, mark = font.ACCENTS[ch]
            glyph = font.MARKS[mark] + [""] + font.FONT[base]
        else:
            glyph = ["", "", ""] + font.FONT.get(ch, [])
        for y, line in enumerate(glyph):
            for x, c in enumerate(line.ljust(5)):
                if c == "#":
                    px[i * 8 + x + 1, y] = color
    return im.resize((im.width * k, im.height * k), Image.NEAREST)


def sky():
    """gradient from black (top) to a very dark blue (horizon)"""
    y = np.linspace(0, 1, HEIGHT)[:, None, None]
    top, bottom = np.array([4, 4, 8]), np.array([18, 22, 46])
    a = (top + (bottom - top) * y ** 1.6) * np.ones((1, WIDTH, 1))
    return Image.fromarray(a.astype(np.uint8))


def ghost():
    """the portrait in sepia, with boosted contrast, fading at the edges"""
    r = Image.open(PORTRAIT).convert("L")
    height = 300
    r = r.resize((round(r.width * height / r.height), height), Image.LANCZOS)
    a = np.asarray(r).astype(float) / 255
    a = np.clip((a - 0.25) / 0.6, 0, 1) ** 1.3                  # contrast
    sepia = np.stack([a * 205 + 10, a * 150 + 6, a * 95 + 4], -1)
    h, w = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    # mask: ellipse that fades at the edges and a strong gradient at the bottom (the chest turns to mist)
    d = np.sqrt(((xx - w / 2) / (w * 0.48)) ** 2 + ((yy - h * 0.42) / (h * 0.55)) ** 2)
    m = np.clip((1 - d) / 0.7, 0, 1) ** 1.5 * np.clip((h * 0.95 - yy) / (h * 0.45), 0, 1)
    m = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(10)))
    rgba = np.dstack([sepia, m * 0.85]).astype(np.uint8)
    return Image.fromarray(rgba)


def town(draw, ground):
    """silhouette of the old houses and of the cathedral tower; returns the lit window (x, y)"""
    color = (6, 7, 14)
    rnd = random.Random(1893)
    x = -10
    windows = []
    while x < WIDTH + 10:
        w = rnd.randint(34, 62)
        h = rnd.randint(55, 105)
        top = ground - h
        draw.rectangle((x, top, x + w, ground), fill=color)
        if rnd.random() < 0.6:                                  # gable roof
            draw.polygon([(x - 3, top), (x + w // 2, top - rnd.randint(12, 22)),
                          (x + w + 3, top)], fill=color)
        for wy in range(top + 12, ground - 14, 24):             # dark windows
            for wx in range(x + 7, x + w - 8, 14):
                windows.append((wx, wy))
        x += w - rnd.randint(0, 4)                              # always touching, no gap
    # the church tower, with the cross
    tx, tw, th = 255, 36, 190
    draw.rectangle((tx, ground - th, tx + tw, ground), fill=color)
    draw.polygon([(tx - 4, ground - th), (tx + tw // 2, ground - th - 48),
                  (tx + tw + 4, ground - th)], fill=color)
    cx, cy = tx + tw // 2, ground - th - 48
    draw.rectangle((cx - 1, cy - 18, cx + 1, cy), fill=color)
    draw.rectangle((cx - 7, cy - 13, cx + 7, cy - 11), fill=color)
    for wx, wy in windows:
        draw.rectangle((wx, wy, wx + 5, wy + 9), fill=(12, 14, 26))
    return (78, ground - 52)


def main():
    cover = Image.open(TEMPLATE).convert("RGB")
    for y0, y1 in DIRTY:
        ImageDraw.Draw(cover).rectangle((0, y0, WIDTH - 1, y1 - 1), fill=BLUE)
    artwork = sky()
    f = ghost()
    fx, fy = (WIDTH - f.width) // 2 - 55, 70                # left of the tower
    # the aura: a wide sepia glow behind the face, reaching up to the tower's cross
    aura = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    cx, cy = fx + f.width // 2, fy + 125
    ImageDraw.Draw(aura).ellipse((cx - 150, cy - 125, cx + 150, cy + 125), fill=(120, 80, 40, 75))
    aura = aura.filter(ImageFilter.GaussianBlur(40))
    artwork.paste(aura, (0, 0), aura)
    artwork.paste(f, (fx, fy), f)

    # the town, with a mist over the foot of the buildings
    ground = HEIGHT - 6
    layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    wx, wy = town(ImageDraw.Draw(layer), ground)
    artwork.paste(layer, (0, 0), layer)

    # the lit window: the candle and the glow around it
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    ImageDraw.Draw(glow).ellipse((wx - 26, wy - 26, wx + 32, wy + 36), fill=(255, 170, 60, 70))
    glow = glow.filter(ImageFilter.GaussianBlur(12))
    artwork.paste(glow, (0, 0), glow)
    d = ImageDraw.Draw(artwork)
    d.rectangle((wx, wy, wx + 7, wy + 11), fill=(255, 196, 90))
    d.rectangle((wx + 3, wy + 4, wx + 4, wy + 9), fill=(255, 245, 210))    # the candle
    d.line((wx, wy + 5, wx + 7, wy + 5), fill=(60, 40, 20))                # the window's cross bar
    d.line((wx + 3, wy, wx + 3, wy + 3), fill=(60, 40, 20))

    # the ground
    d.rectangle((0, ground, WIDTH, HEIGHT), fill=(3, 3, 6))

    # the logo: the game font, with a blood-red shadow
    lg = logo("DEMÔNIOS", (240, 236, 224, 255), 5)
    shadow = logo("DEMÔNIOS", (150, 12, 12, 255), 5)
    lx, ly = (WIDTH - lg.width) // 2, 6
    artwork.paste(shadow, (lx + 4, ly + 4), shadow)
    artwork.paste(lg, (lx, ly), lg)
    sub = logo("ALUÍSIO AZEVEDO", (200, 150, 95, 255), 2)
    artwork.paste(sub, ((WIDTH - sub.width) // 2, ly + lg.height + 6), sub)

    cover.paste(artwork, (0, TOP))
    fnt = ImageFont.truetype("/usr/share/fonts/google-noto/NotoSans-Bold.ttf", 13)
    ImageDraw.Draw(cover).text((WIDTH - 10, BOT - 8), SIGNATURE, fill=(150, 150, 150),
                               font=fnt, anchor="rb")   # in place of the other covers' "© INUFUTO"
    output = ROOT / "screenshots" / "cover.png"
    cover.save(output)
    print(f"{output.relative_to(ROOT)}: {cover.width} × {cover.height}")


if __name__ == "__main__":
    main()
