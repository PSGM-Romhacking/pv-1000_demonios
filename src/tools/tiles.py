#!/usr/bin/env python3
"""Converts src/art/*.png into PV-1000 tiles, within the ROM budget, and writes:

  src/rom/generated/font.asm     tiles 0x01–0x5F of the font (go in both banks)
  src/rom/generated/bank0.asm    the 128 image patterns of bank 0 (tiles 0x60–0xDF)
  src/rom/generated/bank1.asm    same, bank 1
  src/rom/generated/images.asm   gallery: image table and fixed texts
  src/rom/generated/texts.asm    gallery: captions of each image
  src/rom/generated/img_*.asm    the compressed images for the game (src/tools/image_codec.py),
                             spread over the free areas of the ROM

Budget per bank (see docs/technical.pt-BR.md): 224 patterns in ROM, of which 0x01–0x5F are
the font; that leaves 128 (0x60–0xDF) for all the images of the bank. Each image also has
its 32 PCG tiles (0xE0–0xFF), copied to RAM when it comes in.

When the distinct tiles do not fit, the converter:
  1. puts in the PCG the tiles unique to each image that stand out the most from the others;
  2. merges the remaining similar tiles (the least used becomes the closest one) until
     128 fit. The distance compares the pixel colors and also the average of each
     neighborhood, so that a dither pattern looks like the flat color it imitates.

Usage:  python3 src/tools/tiles.py
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import image_codec  # noqa: E402
import font  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
WIDTH, HEIGHT = 20, 11                # the image, in tiles
FREE_ROM = 128                        # 0x60–0xDF
FIRST_ROM = 0x60
PCG_MAX = 32
RGB = np.array([(0, 0, 0), (255, 0, 0), (0, 255, 0), (255, 255, 0),
                (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255)], float)

# gallery order (the story's) and the bank of each image: bank 0 = the room and the
# city, bank 1 = Laura and what comes after
IMAGES = [
    ("quarto", "O QUARTO", 0), ("janela", "A JANELA", 0), ("manuscrito", "O MANUSCRITO", 0),
    ("escada", "A ESCADA", 0), ("rua", "A RUA", 0), ("igreja", "A IGREJA", 0),
    ("botica", "A BOTICA", 0), ("laura_casa", "A CASA DE LAURA", 0),
    ("laura", "LAURA", 1), ("sala", "A SALA", 1), ("maos", "AS MÃOS", 1),
    ("bonde", "O BONDE", 1), ("cais", "O CAIS", 1), ("mata", "A MATA", 1),
    ("gruta", "A GRUTA", 1),
    # fixed screens: title (opening) and ending, the same one for every ending
    ("abertura", "ABERTURA", 1), ("fim", "TELA DE FIM", 1),
    ("autor", "ALUÍSIO AZEVEDO", 1),
]


def read_image(name):
    img = Image.open(ROOT / "src" / "art" / f"{name}.png")
    if img.size != (WIDTH * 8, HEIGHT * 8):
        sys.exit(f"src/art/{name}.png: {img.size}, expected {(WIDTH * 8, HEIGHT * 8)}")
    rgb = np.array(img.convert("RGB"), float)
    idx = ((rgb[..., None, :] - RGB) ** 2).sum(-1).argmin(-1)      # closest color
    return idx.astype(np.uint8)


def cut(idx):
    """The image's 220 tiles, in row order, each one 8 × 8 color indices."""
    return [idx[r * 8:r * 8 + 8, c * 8:c * 8 + 8].copy() for r in range(HEIGHT) for c in range(WIDTH)]


def tile_bytes(t):
    """32 bytes in the PV-1000 format: unused plane, red, green, blue."""
    planes = [[sum(0x80 >> x for x in range(8) if t[y, x] & bit) for y in range(8)] for bit in (1, 2, 4)]
    return [0] * 8 + planes[0] + planes[1] + planes[2]


def from_bytes(b):
    t = np.zeros((8, 8), np.uint8)
    for k, bit in enumerate((1, 2, 4)):
        for y in range(8):
            for x in range(8):
                if b[8 + 8 * k + y] & (0x80 >> x):
                    t[y, x] |= bit
    return t


def vectors(ts):
    """For measuring distance: the pixel colors (weight 0.5) and the average of each 3 × 3
    neighborhood (weight 1.5). All multiplied by 6, so the math stays in integers."""
    c = (RGB[np.array(ts)] // 255).astype(np.int64)                # n, 8, 8, 3; 0 or 1
    p = np.pad(c, ((0, 0), (1, 1), (1, 1), (0, 0)), mode="edge")
    total = sum(p[:, dy:dy + 8, dx:dx + 8] for dy in range(3) for dx in range(3))
    return np.concatenate([c.reshape(len(ts), -1) * 3, total.reshape(len(ts), -1)], 1)


def distances(v):
    """Squared distance between every pair. In integers, exact: with floating point the
    matrix product (BLAS) rounds differently on each machine, and the near-exact ties
    changed the choice of tiles (the ROM came out different on GitHub)."""
    q = (v * v).sum(1)
    d = q[:, None] + q[None, :] - 2 * (v @ v.T)
    return d / 36


def build_bank(names, fixed):
    """Fits the images of one bank. `fixed`: {tile bytes: code} (the font).
    Returns (ROM patterns, {name: (code map, PCG patterns)}, report)."""
    unique, usage = {}, []                        # bytes → id; usage[id] = {name: count}
    positions = {}
    for name in names:
        ids = []
        for t in cut(read_image(name)):
            k = bytes(tile_bytes(t))
            if k not in unique:
                unique[k] = len(unique)
                usage.append({})
            i = unique[k]
            usage[i][name] = usage[i].get(name, 0) + 1
            ids.append(i)
        positions[name] = ids
    keys = list(unique)
    ts = [from_bytes(k) for k in keys]
    n = len(ts)
    is_fixed = np.array([k in fixed for k in keys])
    weight = np.array([sum(u.values()) for u in usage], float)

    # extra fixed targets: the font also serves as a destination for merges (the blank
    # 0x20, mainly), without spending a new pattern
    extras = [k for k in fixed if k not in unique]
    every = ts + [from_bytes(k) for k in extras]
    is_fixed = np.concatenate([is_fixed, np.ones(len(extras), bool)])
    weight = np.concatenate([weight, np.zeros(len(extras))])
    D = distances(vectors(every))
    np.fill_diagonal(D, np.inf)

    # 1. PCG: unique tiles that stand out the most, only as many as needed
    pcg = {name: [] for name in names}
    excess = int((~is_fixed[:n]).sum()) - FREE_ROM
    if excess > 0:
        isolation = D[:n].min(1) * weight[:n]
        candidates = sorted((i for i in range(n) if not is_fixed[i] and len(usage[i]) == 1),
                            key=lambda i: -isolation[i])
        for i in candidates:
            if excess <= 0:
                break
            name = next(iter(usage[i]))
            if len(pcg[name]) < PCG_MAX:
                pcg[name].append(i)
                excess -= 1
    in_pcg = {i for ids in pcg.values() for i in ids}

    # 2. merge similar ones until they fit
    active = np.array([i not in in_pcg for i in range(len(every))])
    target = list(range(len(every)))
    error = 0.0
    while int((active & ~is_fixed).sum()) > FREE_ROM:
        removable = active & ~is_fixed
        with np.errstate(invalid="ignore"):
            cost = D * weight[:, None]
        cost[~removable, :] = np.inf
        cost[:, ~active] = np.inf
        a, b = divmod(int(cost.argmin()), len(every))
        error += cost[a, b]
        target[a] = b
        weight[b] += weight[a]
        active[a] = False

    def final(i):
        while target[i] != i:
            i = target[i]
        return i

    rom = [i for i in range(n) if active[i] and not is_fixed[i]]
    rom_code = {i: FIRST_ROM + k for k, i in enumerate(rom)}
    patterns = [list(keys[i]) for i in rom]
    result = {}
    for name in names:
        pcg_code = {i: 0xE0 + k for k, i in enumerate(pcg[name])}
        tilemap = []
        for i in positions[name]:
            if i in pcg_code:
                tilemap.append(pcg_code[i])
                continue
            f = final(i)
            k = bytes(tile_bytes(every[f]))
            tilemap.append(fixed[k] if k in fixed else rom_code[f])
        result[name] = (tilemap, [list(keys[i]) for i in pcg[name]])
    report = {"distinct": n, "rom": len(rom), "pcg": len(in_pcg), "merges": int((~active).sum()) - len(in_pcg)}
    return patterns, result, report


def draw(tilemap, rom, pcg, font_tiles):
    """The image as the ROM shows it, built from the codes (checks the converter itself)."""
    img = np.zeros((HEIGHT * 8, WIDTH * 8), np.uint8)
    for p, c in enumerate(tilemap):
        if c >= 0xE0:
            b = pcg[c - 0xE0]
        elif c >= FIRST_ROM:
            b = rom[c - FIRST_ROM]
        else:
            b = font_tiles[c - 1]
        r, col = divmod(p, WIDTH)
        img[r * 8:r * 8 + 8, col * 8:col * 8 + 8] = from_bytes(b)
    return img


def db(values, per_line=16):
    return ["    db " + ",".join(f"0x{v:02X}" for v in values[i:i + per_line])
            for i in range(0, len(values), per_line)]


def main():
    generated = ROOT / "src" / "rom" / "generated"
    generated.mkdir(parents=True, exist_ok=True)
    header = "; GENERATED by src/tools/tiles.py: do not edit by hand."

    font_tiles = font.tiles()
    fixed = {}
    for c, b in sorted(enumerate(font_tiles, start=1), key=lambda cb: (cb[0] < 0x20, cb[0])):
        fixed.setdefault(bytes(b), c)       # the blank becomes 0x20 (space), not a free code
    out = [header, "; tiles 0x01-0x5F: the font (0x01-0x0C accented, 0x20-0x5F ASCII)", ""]
    for c, b in enumerate(font_tiles, start=1):
        out += [f"; tile 0x{c:02X}"] + db(b)
    (generated / "font.asm").write_text("\n".join(out) + "\n")

    results = {}
    for bank in (0, 1):
        names = [n for n, _, b in IMAGES if b == bank]
        patterns, result, report = build_bank(names, fixed)
        results.update({n: (bank, *result[n], patterns) for n in names})
        out = [header, f"; bank {bank}: {len(patterns)} of {FREE_ROM} image patterns (tiles 0x60-0xDF)", ""]
        for k in range(FREE_ROM):
            b = patterns[k] if k < len(patterns) else [0] * 32
            out += [f"; tile 0x{FIRST_ROM + k:02X}"] + db(b)
        (generated / f"bank{bank}.asm").write_text("\n".join(out) + "\n")
        print(f"bank {bank}: {len(names)} images, {report['distinct']} distinct tiles -> "
              f"{report['rom']}/{FREE_ROM} in ROM + {report['pcg']} in PCG, {report['merges']} merges")

    # gallery: uses the same compressed data as the game (img_*.asm)
    table = [header, "", f"N_IMAGES: equ {len(IMAGES) + 1}   ; + the font table", "",
             "; per image: port FF value (bank), number of PCG tiles, map, PCG (compressed),",
             "; caption", "images:"]
    texts = [header, "; captions: (map address, text, 0)..., ended by dw 0"]
    for i, (name, title, _) in enumerate(IMAGES):
        bank, tilemap, pcg, patterns = results[name]
        n_rom = len({c for c in tilemap if FIRST_ROM <= c < 0xE0})
        table += [f"    db 0x{bank << 5:02X},{len(pcg)}", f"    dw im_{name}_m,im_{name}_p,caption_{name}"]
        lines = [(13, title), (15, f"{i + 1:02d}/{len(IMAGES) + 1}"),
                 (17, f"BANCO {bank}  ROM {n_rom}  PCG {len(pcg)}")]
        texts += ["", f"caption_{name}:"]
        for row, txt in lines:
            texts += [f"    dw MAP+{row}*32+{16 - len(txt) // 2}  ; {txt}"] + db(font.encode(txt) + [0])
        texts += ["    dw 0"]

        img = draw(tilemap, patterns, pcg, font_tiles)
        orig = read_image(name)
        diff = int((orig != img).sum())
        print(f"  {name:11s} ROM {n_rom:3d}  PCG {len(pcg):2d}  pixels changed {diff:5d} ({100 * diff / orig.size:4.1f}%)")

    # the last gallery screen: the font table (base letters, accented letters and marks),
    # drawn with the font's own tiles, which are in both banks
    font_lines = ["", "A Á À Â Ã  E É Ê", "", "I Í  O Ó Ô Õ", "", "U Ú Ü  C Ç  N Ñ", "",
                  "? ¿ ! ¡ - — : ; , .", "", "0123456789", ""]
    font_map = []
    for line in font_lines:
        codes = font.encode(line) if line else []
        left = (WIDTH - len(codes)) // 2
        font_map += [0x20] * left + codes + [0x20] * (WIDTH - left - len(codes))
    table += ["    db 0x00,0", "    dw im_fonte_m,im_fonte_p,caption_fonte", "",
              "; the font table (extra gallery screen)", "im_fonte_m:"]
    table += db(image_codec.rle_map(font_map), 24) + ["im_fonte_p:"]
    n = len(IMAGES) + 1
    texts += ["", "caption_fonte:"]
    for row, txt in ((13, "A FONTE"), (15, f"{n:02d}/{n}"), (17, "ACENTOS E SINAIS")):
        texts += [f"    dw MAP+{row}*32+{16 - len(txt) // 2}  ; {txt}"] + db(font.encode(txt) + [0])
    texts += ["    dw 0"]

    table += ["", "; fixed gallery texts", "fixed:"]
    for row, txt in ((19, "FIRE 1 >  PRÓXIMA"), (21, "FIRE 2 <  ANTERIOR"), (23, "DEMÔNIOS: GALERIA")):
        table += [f"    dw MAP+{row}*32+{16 - len(txt) // 2}  ; {txt}"] + db(font.encode(txt) + [0])
    table += ["    dw 0"]
    (generated / "images.asm").write_text("\n".join(table) + "\n")
    (generated / "texts.asm").write_text("\n".join(texts) + "\n")
    game_images(results, generated, header)


# free areas of the game ROM for the image data (the rest goes in the main area, 0x4000+)
AREAS = [("img_1c00", 0x1C00, 0x2000), ("img_3c00", 0x3C00, 0x4000)]


def game_images(results, generated, header):
    """Compresses maps and PCG, checks the round trip and spreads the blocks over the areas."""
    blocks = []                                   # (label, bytes, comment)
    table = [header] + [f"IMG_{n.upper()}: equ {i}" for i, (n, _, _) in enumerate(IMAGES)]
    table += ["; per image: port FF value (bank), number of PCG tiles, map, PCG", "tab_img:"]
    for name, title, _ in IMAGES:
        bank, tilemap, pcg, _ = results[name]
        m = image_codec.rle_map(tilemap)
        raw = [x for b in pcg for x in b[8:]]
        z = image_codec.lzss(raw)
        assert image_codec.unrle_map(m) == tilemap, name
        assert image_codec.unlzss(z, len(raw)) == raw, name
        blocks += [(f"im_{name}_m", m, f"{title}: map"), (f"im_{name}_p", z, f"{title}: PCG")]
        table += [f"    db 0x{bank << 5:02X},{len(pcg)}", f"    dw im_{name}_m,im_{name}_p"]
    free = {a: end - start for a, start, end in AREAS}
    where = {a: [] for a, _, _ in AREAS}
    # each area gets the combination of blocks that fills it the most (subset sum);
    # what is left goes in the main area
    rest = list(blocks)
    for a, _, _ in AREAS:
        best = {0: []}                         # sum -> indices of the blocks that make it up
        for i, (_, b, _) in enumerate(rest):
            for total, idx in list(best.items()):
                new = total + len(b)
                if new <= free[a] and new not in best:
                    best[new] = idx + [i]
        choice = set(best[max(best)])
        where[a] = [b for i, b in enumerate(rest) if i in choice]
        free[a] -= max(best)
        rest = [b for i, b in enumerate(rest) if i not in choice]

    def write(fname, block_list):
        out = [header, "; compressed images (format in src/tools/image_codec.py)"]
        for label, b, comment in block_list:
            out += [f"{label}:  ; {comment}, {len(b)} bytes"] + db(b, 24)
        (generated / f"{fname}.asm").write_text("\n".join(out) + "\n")

    for a, _, _ in AREAS:
        write(a, where[a])
    write("img_rest", rest)
    (generated / "img_table.asm").write_text("\n".join(table) + "\n")
    total = sum(len(b) for _, b, _ in blocks)
    n_rest = sum(len(b) for _, b, _ in rest)
    print(f"game images: {total} compressed bytes; {total - n_rest} in the free areas, "
          f"{n_rest} in the main area")

if __name__ == "__main__":
    main()
