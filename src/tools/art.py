#!/usr/bin/env python3
"""Draws the game's source images in src/art/*.png: 160 × 88 px (20 × 11 tiles), in the 8
digital colors of the PV-1000.

The images are made by code, with simple shapes, screens aligned to the grid and
flat areas, to use few distinct tiles. Fitting them into the ROM's tile
budget is the job of src/tools/tiles.py.

Color rule: YELLOW is reserved for ending FA1 (maos). The flames and the light in the
other screens are red and white.

Usage:  python3 src/tools/art.py [name ...]      (no names: draws them all)
"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

IW, IH = 160, 88
# index = PV-1000 bits: 1 red, 2 green, 4 blue
K, R, G, Y, B, M, C, W = range(8)
RGB = [(0, 0, 0), (255, 0, 0), (0, 255, 0), (255, 255, 0),
       (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)]

_yy, _xx = np.mgrid[0:IH, 0:IW]
PATTERNS = {
    "solid": np.ones((IH, IW), bool),
    "checker": (_xx + _yy) % 2 == 0,                # 50%
    "sparse": (_xx % 2 == 0) & (_yy % 2 == 0),      # 25%
    "rare": (_xx % 4 == 0) & (_yy % 4 == 2),        # 6%
    "rows": _yy % 2 == 0,
    "cols": _xx % 2 == 0,
    "weave": ((_xx + 2 * (_yy // 2)) % 4 == 0) & (_yy % 2 == 0),  # 12%
}


class Canvas:
    def __init__(self, background=K):
        self.a = np.full((IH, IW), background, np.uint8)

    def _mask(self, draw):
        m = Image.new("L", (IW, IH), 0)
        draw(ImageDraw.Draw(m))
        return np.array(m) > 0

    def paint(self, mask, color, pattern="solid", background=None):
        """Paints `color` where the mask and the pattern coincide; with `background`, paints the
        rest of the mask with it (without `background`, the rest stays as it was)."""
        p = PATTERNS[pattern]
        self.a[mask & p] = color
        if background is not None:
            self.a[mask & ~p] = background

    def rect(self, x0, y0, x1, y1, color, pattern="solid", background=None):
        self.paint(self._mask(lambda d: d.rectangle((x0, y0, x1, y1), fill=255)), color, pattern, background)

    def poly(self, pts, color, pattern="solid", background=None):
        self.paint(self._mask(lambda d: d.polygon(pts, fill=255)), color, pattern, background)

    def ellipse(self, x0, y0, x1, y1, color, pattern="solid", background=None):
        self.paint(self._mask(lambda d: d.ellipse((x0, y0, x1, y1), fill=255)), color, pattern, background)

    def ring(self, x0, y0, x1, y1, color, width=1):
        self.paint(self._mask(lambda d: d.ellipse((x0, y0, x1, y1), outline=255, width=width)), color)

    def line(self, pts, color, width=1):
        self.paint(self._mask(lambda d: d.line(pts, fill=255, width=width)), color)

    def frame(self, x0, y0, x1, y1, color, width=1):
        self.paint(self._mask(lambda d: d.rectangle((x0, y0, x1, y1), outline=255, width=width)), color)

    def px(self, x, y, color):
        if 0 <= x < IW and 0 <= y < IH:
            self.a[y, x] = color

    def save(self, path):
        img = Image.new("P", (IW, IH))
        img.putdata(self.a.flatten().tolist())
        img.putpalette([v for c in RGB for v in c])
        img.save(path)


def flame(t, x, y):
    """Candle flame (no yellow): red halo, white core. (x, y) = base of the flame."""
    t.ellipse(x - 3, y - 8, x + 3, y, R)
    t.ellipse(x - 1, y - 6, x + 1, y - 1, W)


# ------------------------------------------------------------------ the scenes

def quarto():
    t = Canvas()
    t.rect(0, 0, 159, 63, B, "sparse")                 # wall
    t.rect(0, 64, 159, 87, K)
    for y in range(66, 88, 6):                         # floorboards
        t.line([(0, y), (159, y)], B)
    t.rect(0, 62, 159, 63, B)                          # skirting board
    # window: only darkness outside
    t.rect(16, 8, 55, 47, B)
    t.rect(19, 11, 52, 44, K)
    t.rect(35, 11, 36, 44, B)
    t.rect(19, 27, 52, 28, B)
    t.rect(14, 48, 57, 49, W)                          # sill
    # wall clock, stopped
    t.ellipse(92, 6, 116, 30, K)
    t.ring(92, 6, 116, 30, W)
    for i in range(12):
        a = i * math.pi / 6
        t.px(round(104 + 10 * math.sin(a)), round(18 - 10 * math.cos(a)), W)
    t.line([(104, 18), (104, 10)], W)                  # twenty past midnight
    t.line([(104, 18), (109, 21)], R)
    # table
    t.rect(80, 54, 151, 57, R)
    t.rect(84, 58, 87, 79, R)
    t.rect(144, 58, 147, 79, R)
    t.rect(80, 54, 151, 54, R, "checker", W)
    # manuscript on the table
    t.poly([(92, 53), (120, 53), (118, 49), (94, 49)], W)
    for x in range(97, 116, 4):
        t.line([(x, 51), (x + 2, 51)], K)
    # candle
    t.rect(132, 42, 135, 53, W)
    t.rect(129, 52, 138, 53, C)
    flame(t, 133, 41)
    t.ellipse(113, 22, 153, 62, R, "rare")             # the little light there is
    t.rect(132, 42, 135, 53, W)
    flame(t, 133, 41)
    return t


def janela():
    t = Canvas()
    # rooftops against a sky without a single star
    t.poly([(0, 52), (16, 40), (40, 40), (48, 48), (48, 88), (0, 88)], B, "checker")
    t.poly([(48, 56), (64, 44), (88, 44), (88, 88), (48, 88)], B, "sparse")
    t.rect(88, 24, 111, 88, B, "checker")              # tower
    t.poly([(86, 24), (100, 8), (113, 24)], B, "checker")
    t.rect(99, 2, 100, 8, W)
    t.rect(96, 4, 103, 5, W)
    t.poly([(112, 48), (136, 36), (160, 48), (160, 88), (112, 88)], B, "checker")
    t.rect(24, 30, 29, 40, B, "checker")               # chimneys
    t.rect(140, 30, 145, 40, B, "checker")
    for x, y in ((8, 60), (24, 60), (8, 72), (32, 72), (56, 64), (72, 64), (120, 60),
                 (136, 60), (144, 72), (96, 40), (96, 56)):
        t.rect(x, y, x + 5, y + 6, K)                  # dark windows
    # the frame of the bedroom window
    t.rect(0, 0, 159, 3, W, "checker", B)
    t.rect(0, 0, 3, 87, W, "checker", B)
    t.rect(156, 0, 159, 87, W, "checker", B)
    t.rect(78, 0, 81, 79, W, "checker", B)
    t.rect(0, 80, 159, 87, W, "checker", B)
    return t


def escada():
    t = Canvas()
    t.rect(0, 0, 159, 87, B, "sparse")                 # wall of the town house
    # steps rising from left to right
    for i in range(9):
        x0, y = 8 * i, 80 - 8 * i
        t.rect(x0, y, 103, y + 7, K)
        t.rect(x0, y, 103, y, C)
    t.rect(0, 80, 159, 87, K)
    t.line([(0, 80), (159, 80)], C)
    # handrail and balusters
    t.line([(0, 56), (80, 0)], W, 2)
    for i in range(1, 10):
        x = 8 * i
        t.line([(x, 80 - 8 * i), (x, 56 - round(x * 0.7))], W)
    # the doorman, motionless
    t.rect(118, 38, 137, 41, R)
    t.ellipse(121, 40, 134, 54, W, "checker", M)
    t.px(125, 46, K)
    t.px(130, 46, K)
    t.rect(116, 55, 139, 79, R, "checker", K)
    t.rect(126, 55, 129, 79, W)
    t.rect(116, 80, 139, 80, R)
    # street door, open to the dark
    t.rect(144, 16, 159, 79, K)
    t.frame(143, 15, 159, 80, R, 2)
    return t


def rua():
    t = Canvas()
    # facades in perspective (vanishing point at 80,40)
    t.poly([(0, 0), (64, 28), (64, 52), (0, 88)], B, "checker")
    t.poly([(160, 0), (96, 28), (96, 52), (160, 88)], B, "sparse")
    for x0, x1 in ((6, 14), (24, 32), (42, 50)):
        def y(x, base):
            return base + (x / 64) * (28 - base) if base < 40 else base + (x / 64) * (52 - base)
        t.poly([(x0, y(x0, 8) + 6), (x1, y(x1, 8) + 6), (x1, y(x1, 8) + 22), (x0, y(x0, 8) + 22)], K)
        xr0, xr1 = 160 - x1, 160 - x0
        t.poly([(xr0, y(x1, 8) + 6), (xr1, y(x0, 8) + 6), (xr1, y(x0, 8) + 22), (xr0, y(x1, 8) + 22)], K)
    t.rect(64, 28, 96, 52, K)
    t.rect(72, 36, 88, 52, B, "rare")                  # the end of the street, almost nothing
    # paving
    t.poly([(0, 88), (64, 52), (96, 52), (160, 88)], K)
    for i in range(1, 6):
        t.line([(80, 52), (80 + (i - 3) * 40, 88)], B)
    for y in (56, 61, 68, 77):
        w = (y - 52) * 80 // 36
        t.line([(80 - w, y), (80 + w, y)], B)
    # gas street lamps, unlit
    for x, top in ((20, 20), (140, 20)):
        t.rect(x, top, x + 1, 84, C)
        t.rect(x - 3, top - 8, x + 4, top - 1, K)
        t.frame(x - 3, top - 8, x + 4, top - 1, C)
        t.rect(x - 4, top - 10, x + 5, top - 9, C)
    return t


def igreja():
    t = Canvas()
    t.rect(0, 80, 159, 87, B, "sparse")                # churchyard
    t.rect(32, 32, 127, 79, B, "checker")              # nave
    t.poly([(28, 32), (80, 12), (132, 32)], B, "sparse")
    t.rect(64, 4, 95, 31, B, "checker")                # tower
    t.poly([(62, 4), (80, -10), (97, 4)], B, "sparse")
    t.rect(79, 0, 80, 3, W)
    # belfry with the silent bell
    t.rect(72, 10, 87, 27, K)
    t.ellipse(72, 6, 87, 16, K)
    t.poly([(76, 24), (79, 14), (80, 14), (83, 24)], C)
    t.rect(75, 24, 84, 25, W)
    # rose window
    t.ellipse(72, 36, 87, 51, K)
    t.ring(72, 36, 87, 51, M)
    t.line([(80, 37), (80, 50)], M)
    t.line([(73, 44), (86, 44)], M)
    # door
    t.rect(68, 60, 91, 79, K)
    t.ellipse(68, 54, 91, 66, K)
    t.rect(79, 60, 80, 79, R)
    # side windows
    for x in (44, 108):
        t.rect(x, 44, x + 7, 63, K)
        t.ellipse(x, 40, x + 7, 48, K)
    t.rect(24, 78, 135, 79, W, "checker", B)           # steps
    return t


def botica():
    t = Canvas()
    t.rect(0, 0, 159, 87, B, "rare")
    # jars aligned to the tile grid and in few styles: equal jars on the same
    # shelf become the same tile (saves ROM)
    jars = [(G, "checker"), (C, "solid"), (M, "checker"), (R, "checker")]
    for row, y in enumerate((16, 32, 48)):
        t.rect(0, y, 159, y + 1, R)                    # shelves
        for i, x in enumerate(range(0, 160, 16)):
            color, pat = jars[(i + row) % len(jars)]
            if (i + row) % 4 == 3 or (y == 48 and 96 <= x <= 112):       # (the lamp goes there)
                continue
            t.rect(x + 1, y - 9, x + 6, y - 1, color, pat, K)
            t.rect(x + 2, y - 11, x + 5, y - 10, W)
    # counter
    t.rect(0, 60, 159, 87, R, "checker", K)
    t.rect(0, 58, 159, 59, W)
    for x in range(16, 160, 32):
        t.rect(x, 64, x + 23, 83, K)
        t.frame(x, 64, x + 23, 83, R)
    # the lamp
    t.rect(100, 52, 115, 57, C)
    t.ellipse(102, 36, 113, 52, K)
    t.ring(102, 36, 113, 52, W)
    t.rect(105, 30, 110, 35, C)
    t.rect(107, 26, 108, 29, C)
    # the bread
    t.ellipse(24, 48, 52, 57, R, "checker", W)
    t.line([(30, 51), (34, 50)], K)
    t.line([(38, 51), (42, 50)], K)
    return t


def laura_casa():
    t = Canvas()
    t.rect(24, 12, 135, 79, B, "sparse")               # town house
    t.poly([(16, 12), (80, 0), (144, 12)], B, "checker")
    t.rect(16, 12, 143, 13, W, "checker", B)
    t.rect(24, 44, 135, 45, W, "checker", B)           # cornice between the floors
    # upper windows: one is lit
    for x in (36, 68, 100):
        t.rect(x, 20, x + 15, 39, K)
        t.frame(x - 1, 19, x + 16, 40, C)
    t.rect(68, 20, 83, 39, R, "weave")
    t.rect(75, 20, 76, 39, C)
    t.rect(68, 28, 83, 28, C)
    for x in (36, 100):
        t.rect(x + 7, 20, x + 8, 39, C)
    # door and lower windows
    t.rect(68, 52, 91, 79, R, "checker", K)
    t.ellipse(68, 46, 91, 58, R, "checker", K)
    t.rect(79, 52, 80, 79, K)
    t.px(76, 66, W)
    t.px(83, 66, W)
    for x in (36, 108):
        t.rect(x, 52, x + 15, 71, K)
        t.frame(x - 1, 51, x + 16, 72, C)
    t.rect(0, 80, 159, 87, K)
    t.rect(60, 80, 99, 83, W, "checker", B)            # doorstep
    return t


def laura():
    t = Canvas()
    # (no dithered halo around: its edges used up too many different tiles)
    # hair behind
    t.ellipse(52, 6, 108, 70, B, "checker", K)
    t.poly([(54, 40), (50, 88), (110, 88), (106, 40)], B, "checker", K)
    # neck and shoulders
    t.rect(74, 54, 85, 68, W, "checker", M)
    t.poly([(36, 88), (48, 70), (70, 64), (90, 64), (112, 70), (124, 88)], M, "checker", K)
    t.poly([(68, 64), (80, 76), (92, 64)], W, "checker", M)
    # face
    t.ellipse(62, 14, 98, 58, W)
    # half-light from the lamp, coming from the left: a crescent moon on the right edge of the
    # face (the face minus the same face shifted to the left)
    face = t._mask(lambda d: d.ellipse((62, 14, 98, 58), fill=255))
    lit = t._mask(lambda d: d.ellipse((56, 12, 92, 60), fill=255))
    t.paint(face & ~lit, M, "sparse")
    t.poly([(58, 26), (66, 8), (94, 8), (102, 26), (96, 18), (80, 14), (64, 18)], B, "checker", K)
    t.rect(68, 30, 75, 30, K)                          # eyebrows
    t.rect(85, 30, 92, 30, K)
    t.rect(69, 33, 74, 35, K)                          # eyes
    t.rect(86, 33, 91, 35, K)
    t.px(71, 34, C)
    t.px(88, 34, C)
    t.line([(80, 36), (78, 44), (81, 45)], M)
    t.rect(75, 49, 85, 50, R)
    t.rect(77, 51, 83, 51, M)
    return t


def sala():
    t = Canvas()
    t.rect(0, 0, 159, 63, B, "sparse")
    t.rect(0, 64, 159, 87, K)
    for y in range(66, 88, 6):
        t.line([(0, y), (159, y)], B)
    # the piano, silent
    t.rect(8, 24, 79, 77, K)
    t.frame(8, 24, 79, 77, R)
    t.rect(8, 24, 79, 27, R, "checker", K)
    t.rect(12, 50, 75, 57, W)
    for x in range(15, 75, 4):
        t.rect(x, 50, x, 57, K)
    for x in range(14, 74, 8):                         # black keys
        t.rect(x, 50, x + 2, 53, K)
    t.rect(10, 58, 77, 59, R)
    t.rect(12, 76, 15, 81, R)
    t.rect(72, 76, 75, 81, R)
    t.rect(32, 32, 55, 45, W, "weave")                 # sheet music
    t.frame(32, 32, 55, 45, W)
    # the unlit candlestick
    t.rect(66, 12, 67, 23, C)
    t.rect(62, 22, 71, 23, C)
    t.rect(65, 9, 68, 11, W)
    # closed window and the armchair
    t.rect(104, 8, 143, 47, K)
    t.frame(103, 7, 144, 48, C, 2)
    t.rect(123, 8, 124, 47, C)
    t.rect(100, 56, 151, 79, M, "checker", K)
    t.rect(100, 48, 107, 79, M, "checker", R)
    t.rect(144, 48, 151, 79, M, "checker", R)
    t.rect(108, 64, 143, 67, R)
    return t


def maos():
    t = Canvas()
    t.ellipse(24, -16, 136, 104, Y, "rare")            # the last light (the only yellow)
    # sleeves
    t.poly([(0, 40), (40, 36), (52, 48), (44, 64), (0, 72)], B, "checker", K)
    t.poly([(160, 36), (116, 34), (104, 48), (114, 64), (160, 68)], M, "checker", K)
    # left hand, coming from the left
    t.poly([(44, 40), (64, 36), (84, 38), (88, 44), (84, 54), (60, 60), (46, 60)], W)
    for y in (40, 44, 48, 52):
        t.line([(70, y), (88, y + 1)], Y)
    # right hand, on top, holding
    t.poly([(112, 38), (96, 34), (76, 40), (70, 46), (74, 52), (96, 58), (112, 60)], W, "sparse", M)
    for y in (42, 46, 50):
        t.line([(74, y + 1), (90, y)], K)
    t.line([(76, 40), (96, 34)], K)
    t.line([(74, 52), (96, 58)], K)
    t.poly([(64, 36), (60, 30), (66, 28), (72, 36)], W)  # thumb
    return t


def bonde():
    t = Canvas()
    t.line([(0, 4), (159, 4)], C)                      # overhead wire
    t.line([(96, 4), (112, 22)], C, 2)                 # trolley pole
    t.rect(16, 24, 143, 67, G, "checker", K)
    t.rect(12, 22, 147, 25, G)
    t.rect(16, 64, 143, 67, G)
    for x in range(24, 136, 16):
        t.rect(x, 30, x + 11, 45, K)                   # empty windows
        t.frame(x - 1, 29, x + 12, 46, W)
    t.rect(28, 52, 131, 55, W, "checker", G)           # destination sign
    t.rect(60, 52, 99, 55, K)
    for x in (32, 120):
        t.ellipse(x, 64, x + 15, 79, K)
        t.ring(x, 64, x + 15, 79, W)
        t.px(x + 7, 71, W)
    t.rect(0, 80, 159, 81, W)                          # rail
    t.rect(0, 82, 159, 87, B, "sparse")
    return t


def cais():
    t = Canvas()
    t.rect(0, 0, 159, 39, K)
    t.rect(0, 40, 159, 71, B)                          # the still sea, smooth
    t.line([(0, 40), (159, 40)], C)
    # boats standing still, not rocking
    for x, w in ((24, 24), (104, 32)):
        t.poly([(x, 44), (x + w, 44), (x + w - 4, 50), (x + 4, 50)], K)
        t.rect(x + w // 2, 18, x + w // 2, 43, W)
        t.poly([(x + w // 2 + 1, 20), (x + w // 2 + 1, 40), (x + w // 2 + 10, 40)], W, "checker", K)
        t.poly([(x + 4, 51), (x + w - 4, 51), (x + w - 6, 53), (x + 6, 53)], K)  # reflection
    # the stone quay
    t.rect(0, 72, 159, 87, W, "checker", B)
    for y in (72, 80):
        t.line([(0, y), (159, y)], K)
    for x in range(0, 160, 16):
        t.line([(x + (8 if (x // 16) % 2 else 0), 73), (x + (8 if (x // 16) % 2 else 0), 79)], K)
        t.line([(x, 81), (x, 87)], K)
    t.rect(124, 60, 135, 72, K)                        # mooring bollard
    t.rect(122, 58, 137, 61, R, "checker", K)
    t.line([(130, 64), (150, 72)], W)
    return t


def mata():
    """The windless forest. Everything aligned to the 8-pixel grid (canopy in a band, trunks in
    tile columns, ferns every 32 px), so that the tiles repeat."""
    t = Canvas()
    t.rect(0, 0, 159, 87, G, "rare")
    t.rect(0, 0, 159, 23, G, "checker", K)             # the canopy, closed
    for x, y in ((0, 31), (24, 39), (56, 31), (88, 39), (120, 31), (144, 39)):
        t.rect(x, 24, x + 15, y, G, "checker", K)      # hanging foliage
    for x, w in ((8, 8), (40, 16), (80, 8), (112, 16), (144, 8)):
        t.rect(x, 24, x + w - 1, 87, K)                # trunks
    t.rect(0, 80, 159, 87, G, "weave")
    for x in range(4, 160, 32):                        # motionless ferns
        t.poly([(x, 87), (x + 6, 70), (x + 12, 87)], G, "sparse")
    return t


def gruta():
    t = Canvas()
    t.rect(0, 0, 159, 87, W, "sparse", B)              # rock
    t.rect(0, 0, 159, 87, B, "weave")
    t.ellipse(20, 6, 140, 140, K)                      # the mouth, wide and deep
    for x in range(44, 116, 12):                       # stalactites (inside the mouth)
        h = 6 + (x * 7) % 9
        t.poly([(x, 13), (x + 6, 13), (x + 3, 13 + h)], W, "checker", B)
    t.poly([(0, 80), (40, 72), (60, 88), (0, 88)], W, "checker", B)
    t.poly([(160, 76), (112, 74), (100, 88), (160, 88)], W, "checker", B)
    t.ellipse(70, 70, 90, 80, B, "sparse")             # the rock
    return t


def manuscrito():
    t = Canvas()
    t.rect(0, 0, 159, 87, R, "rare")                   # the table under the candle
    t.rect(28, 4, 123, 83, W)                          # the page
    t.rect(124, 6, 125, 85, B, "checker")
    t.rect(30, 84, 125, 85, B, "checker")
    import random
    rnd = random.Random(7)
    for y in range(12, 76, 6):                         # handwritten lines
        x = 34
        end = 116 if y < 70 else 70
        while x < end:
            n = rnd.randint(3, 12)
            t.rect(x, y, min(x + n, end), y + 1, K, "checker" if rnd.random() < .3 else "solid")
            x += n + 3
    # inkwell and quill
    t.ellipse(132, 64, 155, 83, K)
    t.ring(132, 64, 155, 83, C)
    t.rect(138, 58, 149, 65, C)
    t.line([(140, 60), (156, 20)], W, 2)
    t.poly([(150, 34), (160, 10), (158, 34)], W, "checker", C)
    # candle stub
    t.rect(6, 62, 13, 79, W)
    t.rect(2, 80, 17, 82, C)
    flame(t, 9, 61)
    return t


def abertura():
    """Title screen: the pocket watch stopped at midnight over the darkened town.
    Takes only 10 tile rows (80 px); the last row stays black, so that the screen's text
    can move up one row."""
    t = Canvas()
    # rooftops seen from the lookout
    t.poly([(0, 64), (20, 56), (44, 56), (56, 62), (56, 80), (0, 80)], B, "checker")
    t.poly([(56, 66), (72, 58), (96, 58), (104, 64), (104, 80), (56, 80)], B, "sparse")
    t.poly([(104, 62), (124, 54), (148, 54), (160, 60), (160, 80), (104, 80)], B, "checker")
    t.rect(28, 48, 33, 56, B, "checker")
    t.rect(130, 46, 135, 54, B, "checker")
    for x, y in ((12, 68), (36, 66), (76, 70), (116, 66), (140, 68)):
        t.rect(x, y, x + 5, y + 5, K)
    # the chain and the watch
    t.line([(80, 0), (80, 5)], C)
    t.ellipse(76, 4, 84, 10, K)
    t.ring(76, 4, 84, 10, C)
    t.ellipse(58, 9, 102, 53, K)
    t.ring(58, 9, 102, 53, W, 2)
    t.ring(62, 13, 98, 49, C)
    for i in range(12):
        a_ = i * math.pi / 6
        t.px(round(80 + 15 * math.sin(a_)), round(31 - 15 * math.cos(a_)), W)
    t.line([(80, 31), (80, 18)], W, 2)             # midnight: both hands together
    t.line([(80, 31), (80, 22)], R)
    t.rect(79, 30, 81, 32, W)
    t.rect(0, 80, 159, 87, K)                      # last tile row: empty
    return t


def fim():
    """Ending screen, the same for all endings: the snuffed candle on the table. Takes only 10
    tile rows (80 px), like the opening."""
    t = Canvas()                                   # black wall: the light is gone
    t.rect(0, 56, 159, 79, R, "checker", K)        # the table
    t.rect(0, 56, 159, 57, R)
    # the bundle of pages, closed
    t.rect(24, 48, 63, 55, W)
    t.rect(26, 46, 61, 47, W, "checker", K)
    t.rect(24, 52, 63, 52, K, "sparse")
    # the candlestick and the candle stub
    t.rect(88, 52, 111, 55, C)
    t.rect(97, 42, 102, 51, W)
    t.px(99, 41, K)
    # the thread of smoke
    for i, y in enumerate(range(39, 2, -3)):
        x = 99 + round(4 * math.sin(i * 0.9))
        t.rect(x, y - 1, x, y, W, "checker")
    t.rect(0, 80, 159, 87, K)                      # last tile row: empty
    return t


def portrait(width=8, height=11, levels=(0, 0.33, 0.75, 1), colors=None, dither=True, row=0):
    """The portrait of Aluísio Azevedo, converted from the photograph in
    src/art/sources/aluisio-azevedo.jpg (source: Academia Brasileira de Letras,
    academia.org.br), in `width` x `height` tiles in the middle of the image area, starting at
    tile row `row`; the rest stays black. `levels`: brightness of each tone (0 to 1), in the
    order of `colors`. Used by autor() and by src/tools/portraits.py (the reduced versions)."""
    from PIL import ImageEnhance, ImageOps
    colors = colors or [K, R, Y, W]
    w, h = width * 8, height * 8
    photo = Image.open(Path(__file__).resolve().parent.parent / "art" / "sources" / "aluisio-azevedo.jpg")
    g = ImageOps.autocontrast(photo.convert("L"), cutoff=2).resize((w, h), Image.LANCZOS)
    g = np.array(ImageEnhance.Contrast(g).enhance(1.3), float) / 255
    levels = np.array(levels)
    bayer = np.array([[0, 2], [3, 1]]) / 4 - 0.375
    x0, y0 = (20 - width) // 2 * 8, row * 8
    t = Canvas()
    for y in range(h):
        for x in range(w):
            v = g[y, x] + (bayer[y % 2, x % 2] / (len(levels) - 1) if dither else 0)
            t.a[y0 + y, x0 + x] = colors[int(np.abs(levels - v).argmin())]
    return t


def autor():
    """"About the author" screen: the portrait in 4-tone sepia (black, red, yellow,
    white), without dithering, in 8 x 11 tiles. Chosen on 2026-10-19 in the test ROM
    of src/tools/portraits.py: ~90 bytes less than the dithered version."""
    return portrait(dither=False)


# the function names are the image IDs (src/art/<name>.png)
SCENES = {f.__name__: f for f in (quarto, janela, escada, rua, igreja, botica, laura_casa,
                                   laura, sala, maos, bonde, cais, mata, gruta, manuscrito,
                                   abertura, fim, autor)}


def main():
    folder = Path(__file__).resolve().parent.parent / "art"
    folder.mkdir(exist_ok=True)
    for name in sys.argv[1:] or SCENES:
        SCENES[name]().save(folder / f"{name}.png")
    print(f"{folder}: {len(sys.argv[1:] or SCENES)} image(s)")


if __name__ == "__main__":
    main()
