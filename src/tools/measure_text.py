#!/usr/bin/env python3
"""Measures how much the script text shrinks with compression schemes that a Z80 can
undo letter by letter, writing straight to the screen (no buffer: there are only 256 bytes of RAM).
Only measures: changes nothing.

The measured text is what goes into the ROM: scene texts, options, item and ending
names, in upper case, with the game font's codes.
Line breaks become a space (wrapping is done on the fly); "---" (page) becomes a code.

Schemes:
  raw        1 byte per character
  6 bits     each character in 6 bits (fits if there are at most 64 symbols)
  bpe        frequent byte pairs become a new code, recursively
             (byte pair encoding); the dictionary (2 bytes per code) is counted.
             Decompression: small stack, one letter at a time
  huffman    variable-length codes per character (tree included in the count)
  bpe+huff   both together
  zlib -9    reference; LZ needs to reread what was already output, bad with text wrapped on screen

Usage:  python3 src/tools/measure_text.py [script.yaml]
"""
import heapq
import re
import sys
import zlib
from collections import Counter
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
PAGE = 0x0D
REPLACEMENTS = {"–": "-", "…": "...", "“": '"', "”": '"', "‘": "'", "’": "'",
                "È": "E", "Ì": "I", "Ò": "O", "Ù": "U", "Ü": "U", "Û": "U", "Î": "I"}


def texts(script):
    """All the strings that go into the ROM."""
    g = script.get("game", {})
    for k in ("title", "subtitle"):
        if g.get(k):
            yield g[k]
    yield from (script.get("items") or {}).values()
    for e in (script.get("endings") or {}).values():
        yield e["name"]
    for scene in (script.get("scenes") or {}).values():
        if scene.get("text"):
            yield scene["text"]
        for t in scene.get("variants") or []:
            if t.get("text"):
                yield t["text"]
        for o in scene.get("options") or []:
            yield o["text"]


def encode(text, missing):
    out = []
    for page in re.split(r"\n\s*---\s*\n", text.strip()):
        if out:
            out.append(PAGE)
        s = " ".join(page.split()).upper()
        for ch in s:
            ch = REPLACEMENTS.get(ch, ch)
            for c in ch:
                try:
                    out.append(font.code(c))
                except ValueError:
                    missing[c] += 1
                    out.append(ord("?"))
    return out


def bpe(strings, free):
    """Byte pair encoding over several strings. Returns (strings, number of codes)."""
    strings = [list(c) for c in strings]
    used = 0
    for new in free:
        pairs = Counter()
        for c in strings:
            pairs.update(zip(c, c[1:]))
        if not pairs:
            break
        (a, b), n = pairs.most_common(1)[0]
        if n - 2 < 2:                         # saves n, costs 2 in the dictionary
            break
        for i, c in enumerate(strings):
            r, k = [], 0
            while k < len(c):
                if k + 1 < len(c) and c[k] == a and c[k + 1] == b:
                    r.append(new)
                    k += 2
                else:
                    r.append(c[k])
                    k += 1
            strings[i] = r
        used += 1
    return strings, used


def huffman_bits(counts):
    """Total bits with Huffman codes for the given counts."""
    if len(counts) == 1:
        return sum(counts.values())
    h = [(n, i, None) for i, n in enumerate(counts.values())]
    heapq.heapify(h)
    depth = {i: 0 for i in range(len(counts))}
    groups = {i: [i] for i in range(len(counts))}
    nxt = len(counts)
    while len(h) > 1:
        n1, i1, _ = heapq.heappop(h)
        n2, i2, _ = heapq.heappop(h)
        for g in groups[i1] + groups[i2]:
            depth[g] += 1
        groups[nxt] = groups.pop(i1) + groups.pop(i2)
        heapq.heappush(h, (n1 + n2, nxt, None))
        nxt += 1
    return sum(n * depth[i] for i, n in enumerate(counts.values()))


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "src" / "script" / "demonios.yaml"
    script = yaml.safe_load(path.read_text())
    missing = Counter()
    strings = [encode(t, missing) + [0] for t in texts(script)]   # 0 = end of string
    flat = [x for c in strings for x in c]
    symbols = Counter(flat)
    raw = len(flat)
    n_scenes = len(script.get("scenes") or {})

    res = {"raw": raw}
    res["6 bits"] = (raw * 6 + 7) // 8 if len(symbols) <= 64 else None
    free = [v for v in range(1, 256) if v not in symbols]
    c_bpe, n_dic = bpe(strings, free)
    flat_bpe = [x for c in c_bpe for x in c]
    res["bpe"] = len(flat_bpe) + 2 * n_dic
    tree = lambda counts: 2 * len(counts)          # noqa: E731  (approximate cost of the tree)
    res["huffman"] = (huffman_bits(symbols) + 7) // 8 + tree(symbols)
    counts_bpe = Counter(flat_bpe)
    res["bpe+huff"] = (huffman_bits(counts_bpe) + 7) // 8 + tree(counts_bpe) + 2 * n_dic
    res["zlib -9"] = len(zlib.compress(bytes(flat), 9))

    print(f"{path.name}: {n_scenes} scenes, {len(strings)} strings, {len(symbols)} distinct symbols")
    if missing:
        print("  no tile in the font (became '?'):", dict(missing))
    print(f"  bpe: {n_dic} dictionary codes out of {len(free)} free")
    print()
    print(f"{'scheme':10s} {'bytes':>6s}  {'of raw':>6s}   per scene")
    for k, v in res.items():
        if v is None:
            print(f"{k:10s}    (more than 64 symbols)")
            continue
        print(f"{k:10s} {v:6d}  {100 * v / raw:5.1f}%   {v / n_scenes:6.0f}")
    print()
    print("Projection for the full script (~16 KB raw, ~53 scenes), at the same rate:")
    for k in ("bpe", "bpe+huff"):
        print(f"  {k:9s} ~{16 * 1024 * res[k] / raw / 1024:4.1f} KB")


if __name__ == "__main__":
    main()
