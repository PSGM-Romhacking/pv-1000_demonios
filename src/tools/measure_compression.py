#!/usr/bin/env python3
"""Measures how much the image data (20 × 11 maps and PCG patterns) shrinks with
compression schemes that a Z80 can undo. Only measures: does not change the ROM.

Schemes:
  maps
    rle        0x00 n v = v repeated n times (code 0 never appears in a map)
    rle+up     same, plus 0x00 0x80|n = copy n tiles from the row above (the screen is already
               in VRAM; no buffer at all, there are only 256 bytes of free RAM)
  pcg
    2colors    tile with up to 2 colors: 1 byte (foreground, background) + 8 of mask; tile of a
               single color: 1 byte; the others: 1 + 24
  lz           simple LZSS (1 flag bit per item, reference = 2 bytes: distance
               up to 4096 and length 3–18), applied after the schemes above
  zlib -9      reference for the best possible, not feasible on the Z80

Usage:  python3 src/tools/measure_compression.py
"""
import sys
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font  # noqa: E402
import tiles  # noqa: E402


def data():
    fixed = {}
    for c, b in sorted(enumerate(font.tiles(), start=1), key=lambda cb: (cb[0] < 0x20, cb[0])):
        fixed.setdefault(bytes(b), c)
    output = {}
    for bank in (0, 1):
        names = [n for n, _, b in tiles.IMAGES if b == bank]
        _, by_name, _ = tiles.build_bank(names, fixed)
        output.update(by_name)
    return [(n, *output[n]) for n, _, _ in tiles.IMAGES]


def rle(tmap, up=False):
    out, i = [], 0
    while i < len(tmap):
        if up and i >= tiles.WIDTH:
            n = 0
            while i + n < len(tmap) and tmap[i + n] == tmap[i + n - tiles.WIDTH] and n < 127:
                n += 1
            if n >= 3:
                out += [0x00, 0x80 | n]
                i += n
                continue
        n = 1
        while i + n < len(tmap) and tmap[i + n] == tmap[i] and n < 127:
            n += 1
        if n >= 4:
            out += [0x00, n, tmap[i]]
        else:
            out += tmap[i:i + n]
        i += n
    return out


def pcg_2colors(pcg):
    out = []
    for b in pcg:
        t = tiles.from_bytes(b)
        colors = sorted(set(t.flatten().tolist()))
        if len(colors) == 1:
            out += [0x80 | colors[0]]
        elif len(colors) == 2:
            fg, bg = colors[1], colors[0]
            out += [fg << 3 | bg] + [sum(0x80 >> x for x in range(8) if t[y, x] == fg) for y in range(8)]
        else:
            out += [0xC0] + b[8:]
    return out


def lzss(data_, window=4096, minimum=3, maximum=18):
    """Size in bytes of the output of a greedy LZSS (Okumura-style format)."""
    size, i, items = 0, 0, 0
    while i < len(data_):
        best, start = 0, max(0, i - window)
        for j in range(start, i):
            k = 0
            while k < maximum and i + k < len(data_) and data_[j + k] == data_[i + k]:
                k += 1
            if k > best:
                best = k
        if best >= minimum:
            size += 2
            i += best
        else:
            size += 1
            i += 1
        items += 1
    return size + (items + 7) // 8


def main():
    imgs = data()
    cols = ["raw", "rle", "rle+up", "2colors", "lz", "rle+up+lz", "2colors+lz", "zlib"]
    tot = {c: [0, 0] for c in cols}            # [maps, pcg]
    print(f"{'image':11s} {'map: raw rle +up lz zlib':>32s}   {'pcg: raw 2colors lz 2c+lz zlib':>34s}")
    for name, tmap, pcg in imgs:
        m_raw = len(tmap)
        m_rle = len(rle(tmap))
        m_up = len(rle(tmap, True))
        m_lz = lzss(tmap)
        m_up_lz = lzss(rle(tmap, True))
        m_z = len(zlib.compress(bytes(tmap), 9))
        p_flat = [x for b in pcg for x in b[8:]]
        p_raw = len(p_flat)
        p_2c = pcg_2colors(pcg)
        p_lz = lzss(p_flat)
        p_2c_lz = lzss(p_2c)
        p_z = len(zlib.compress(bytes(p_flat), 9))
        for c, (m, p) in {"raw": (m_raw, p_raw), "rle": (m_rle, p_raw), "rle+up": (m_up, p_raw),
                          "2colors": (m_up, len(p_2c)), "lz": (m_lz, p_lz),
                          "rle+up+lz": (min(m_up, m_up_lz), p_lz),
                          "2colors+lz": (min(m_up, m_up_lz), min(len(p_2c), p_2c_lz)),
                          "zlib": (m_z, p_z)}.items():
            tot[c][0] += m
            tot[c][1] += p
        print(f"{name:11s} {m_raw:4d} {m_rle:4d} {m_up:4d} {m_lz:4d} {m_z:4d}"
              f"        {p_raw:4d} {len(p_2c):4d} {p_lz:4d} {p_2c_lz:4d} {p_z:4d}")
    base = sum(tot["raw"])
    print()
    print(f"{'scheme (maps + pcg)':26s} {'maps':>6s} {'pcg':>6s} {'total':>6s}  savings")
    for c in cols:
        m, p = tot[c]
        print(f"{c:26s} {m:6d} {p:6d} {m + p:6d}  {base - m - p:5d} B ({100 * (base - m - p) / base:4.1f}%)")


if __name__ == "__main__":
    main()
