"""Image compression for the ROM (imported by src/tools/tiles.py). The formats are the
ones src/rom/decompress.asm undoes; the decompressors here serve as a reference and as a
round-trip check on every build.

Map (20 × 11 tile codes, in row order), RLE with "copy from above":
  b != 0          tile b
  00 n v          v repeated n times (n = 1–127)
  00 80|n         copies n tiles from the row above (already in VRAM)
  The size is fixed (220), so there is no end marker. Code 0 never goes into a map.

PCG (24 bytes per tile: red, green, blue; the unused plane is left out), LZSS:
  every 8 items, 1 flag byte (bit 0 first): 1 = literal (1 byte),
  0 = reference (2 bytes): byte 1 = (distance - 1) & 0xFF,
                           byte 2 = ((distance - 1) >> 8) << 4 | (length - 3)
  distance 1–4096, length 3–18. The total size (number of tiles × 24) is known.
"""

WIDTH = 20
MIN, MAX, WINDOW = 3, 18, 4096


def rle_map(tilemap):
    out, i = [], 0
    while i < len(tilemap):
        if i >= WIDTH:
            n = 0
            while i + n < len(tilemap) and tilemap[i + n] == tilemap[i + n - WIDTH] and n < 127:
                n += 1
            if n >= 3:
                out += [0x00, 0x80 | n]
                i += n
                continue
        n = 1
        while i + n < len(tilemap) and tilemap[i + n] == tilemap[i] and n < 127:
            n += 1
        if n >= 4:
            out += [0x00, n, tilemap[i]]
        else:
            out += tilemap[i:i + n]
        i += n
    return out


def unrle_map(data, total=220):
    out, i = [], 0
    while len(out) < total:
        b = data[i]
        i += 1
        if b:
            out.append(b)
        elif data[i] & 0x80:
            for _ in range(data[i] & 0x7F):
                out.append(out[len(out) - WIDTH])
            i += 1
        else:
            out += [data[i + 1]] * data[i]
            i += 2
    return out


def lzss(data):
    """Greedy, with one step of lookahead (lazy matching): if the next position has a
    longer reference, emit a literal first."""
    def best(i):
        bl, bd = 0, 0
        for j in range(max(0, i - WINDOW), i):
            k = 0
            while k < MAX and i + k < len(data) and data[j + k] == data[i + k]:
                k += 1
            if k > bl:
                bl, bd = k, i - j
        return bl, bd

    items, i = [], 0
    while i < len(data):
        t, d = best(i)
        if t >= MIN and i + 1 < len(data):
            t2, _ = best(i + 1)
            if t2 > t + 1:
                t = 0
        if t >= MIN:
            items.append((t, d))
            i += t
        else:
            items.append(data[i])
            i += 1
    out = []
    for k in range(0, len(items), 8):
        group = items[k:k + 8]
        flags = sum(1 << b for b, it in enumerate(group) if isinstance(it, int))
        out.append(flags)
        for it in group:
            if isinstance(it, int):
                out.append(it)
            else:
                t, d = it
                out += [(d - 1) & 0xFF, ((d - 1) >> 8) << 4 | (t - MIN)]
    return out


def unlzss(data, total):
    out, i, bits, n = [], 0, 0, 0
    while len(out) < total:
        if n == 0:
            bits, n = data[i], 8
            i += 1
        lit = bits & 1
        bits >>= 1
        n -= 1
        if lit:
            out.append(data[i])
            i += 1
        else:
            d = (data[i] | (data[i + 1] >> 4) << 8) + 1
            t = (data[i + 1] & 0x0F) + MIN
            i += 2
            for _ in range(t):
                out.append(out[-d])
    return out
