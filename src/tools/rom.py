#!/usr/bin/env python3
"""Converts the script (YAML) into ROM data: src/rom/generated/script.asm.

Validates with src/tools/script.py first; on error, generates nothing. The Z80 engine
(src/rom/game.asm) interprets this data.

Format (all lists in order; scene, item, flag, ending and counter numbers are
indices in YAML order):

  scene:  db info        bit 0 dark, 1 own light, 2 ending, 3 auto, 4 has image
          db route       0 common, 1 A, 2 B, 3 C
          db image       index into IMAGES (0xFF = none)
          db target      ending number (if ending) or next scene (if auto)
          <effect>       on_enter
          db n           text variants, each one: <condition> <effect> dw text
          dw text        the default text
          db n           options, each one: db else, <condition>, <effect>, db goto, dw text

  condition (ends in 0; all must hold):
          01 m has   02 m lacks   03 m flag   04 m no_flag   (m = bit mask)
          05 n hum_min   06 n hum_max   07 n bond_min   08 n bond_max
          09 k n count_min   0A k n count_max   0B n endings_min
  effect (ends in 0; applied in this order):
          01 m gain   02 m lose   03 m flag   04 m unflag   05 d bond
          06 k d add   07 d hum   08 protect

  text:   font codes; 0x1E = new line, 0x1F = new page, 0 = end. The lines
          come already wrapped at 28 columns; pagination is
          done on the fly, because the height of the text area depends on the options.
          Compressed with BPE: bytes 0x60–0xFF are pairs (table `dic`, 2 bytes per
          code), expanded recursively. The control codes (0, 0x1E,
          0x1F) never go into a pair, so pagination always stops between two bytes
          of the compressed text.

Usage:  python3 src/tools/rom.py [script.yaml] [--lang pt|en|es]
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font  # noqa: E402
import languages  # noqa: E402
import tiles  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent
COLUMNS = 28
ROUTES = {None: 0, "A": 1, "B": 2, "C": 3}
# label in the engine -> key in the script's `interface` (each language has its own texts)
FIXED_TEXTS = {
    "txt_start": "start", "txt_credits": "credits", "txt_continue": "continue",
    "txt_end": "end", "txt_no_exit": "no_exit", "txt_inventory": "inventory",
    "txt_nothing": "nothing", "txt_closes": "closes", "txt_end_big": "end_big",
    "txt_back_to_title": "back_to_title", "txt_pause": "pause",
    "txt_about_menu": "about", "txt_back": "back",
}
FIRST_PAIR = 0x60
CONTROLS = {0, font.NEW_LINE, font.NEW_PAGE}
# ending types: they only pick the ending screen music (the type is not shown in the game)
TYPES = ("good", "normal", "bad", "true_end")


def as_list(v):
    return [] if v is None else v if isinstance(v, list) else [v]


def wrap(text, w=COLUMNS):
    """Wraps the text into lines of up to `w` characters, word by word."""
    out = []
    for par in text.split("\n"):
        line = ""
        for p in par.split():
            if not line:
                line = p
            elif len(line) + 1 + len(p) <= w:
                line += " " + p
            else:
                out.append(line)
                line = p
        out.append(line)
    return out


class Generator:
    def __init__(self, script):
        self.script = script
        self.items = list(script["items"])
        self.flags = as_list(script["flags"])
        self.endings = list(script["endings"])
        self.scenes = list(script["scenes"])
        self.images = [n for n, _, _ in tiles.IMAGES]
        self.counters = []
        self.texts = []                       # (label, bytes, sample)
        self.cache = {}
        self.aliases = {}                     # text label -> other names for it

    def counter(self, name):
        if name not in self.counters:
            self.counters.append(name)
        return self.counters.index(name)

    def mask(self, names, universe):
        return sum(1 << universe.index(n) for n in as_list(names))

    def cond(self, cnd):
        cnd = cnd or {}
        b = []
        for op, key, univ in ((1, "has", self.items), (2, "lacks", self.items),
                              (3, "flag", self.flags), (4, "no_flag", self.flags)):
            if cnd.get(key):
                b += [op, self.mask(cnd[key], univ)]
        for op, key in ((5, "hum_min"), (6, "hum_max"), (7, "bond_min"), (8, "bond_max")):
            if cnd.get(key) is not None:
                b += [op, cnd[key]]
        for op, key in ((9, "count_min"), (10, "count_max")):
            for k, n in (cnd.get(key) or {}).items():
                b += [op, self.counter(k), n]
        if cnd.get("endings_min") is not None:
            b += [11, cnd["endings_min"]]
        return b + [0]

    def effect(self, ef):
        ef = ef or {}
        b = []
        for op, key, univ in ((1, "gain", self.items), (2, "lose", self.items),
                              (3, "flag", self.flags), (4, "unflag", self.flags)):
            if ef.get(key):
                b += [op, self.mask(ef[key], univ)]
        if ef.get("bond"):
            b += [5, ef["bond"] & 0xFF]
        for k, n in (ef.get("add") or {}).items():
            b += [6, self.counter(k), n & 0xFF]
        if ef.get("hum"):
            b += [7, ef["hum"] & 0xFF]
        if ef.get("protect"):
            b += [8]
        return b + [0]

    def encode(self, s, where):
        try:
            return font.encode(s)
        except ValueError as e:
            sys.exit(f"{where}: {e}")

    def fixed(self, label, txt):
        self.texts.append((label, self.encode(txt, label) + [0], txt))

    def bpe(self):
        """Compresses all the texts together; returns the dictionary [(a, b), ...]."""
        strings = [b for _, b, _ in self.texts]
        dic = []
        while FIRST_PAIR + len(dic) <= 0xFF:
            pairs = {}
            for c in strings:
                for a, b in zip(c, c[1:]):
                    if a not in CONTROLS and b not in CONTROLS:
                        pairs[(a, b)] = pairs.get((a, b), 0) + 1
            if not pairs:
                break
            pair, n = max(pairs.items(), key=lambda kv: kv[1])
            if n < 4:                     # saves n bytes, costs 2 in the dictionary
                break
            new = FIRST_PAIR + len(dic)
            dic.append(pair)
            for i, c in enumerate(strings):
                out, k = [], 0
                while k < len(c):
                    if k + 1 < len(c) and (c[k], c[k + 1]) == pair:
                        out.append(new)
                        k += 2
                    else:
                        out.append(c[k])
                        k += 1
                strings[i] = out
        def expand(c):
            return [y for x in c for y in (expand(dic[x - FIRST_PAIR]) if x >= FIRST_PAIR else [x])]
        for (_, original, _), c in zip(self.texts, strings):
            assert expand(c) == original, "BPE: the round trip does not match"
        self.texts = [(r, c, a) for (r, _, a), c in zip(self.texts, strings)]
        return dic

    def text(self, t, where, single_line=False):
        """Label of a text (repeated ones are stored only once)."""
        t = t.strip().upper()
        if single_line:
            b = self.encode(t, where)
        else:
            b = []
            for i, block in enumerate(re.split(r"\n\s*---\s*\n", t)):
                if i:
                    b.append(font.NEW_PAGE)
                for j, line in enumerate(wrap(block.strip())):
                    if j:
                        b.append(font.NEW_LINE)
                    b += self.encode(line, where)
        b.append(0)
        key = bytes(b)
        if key not in self.cache:
            self.cache[key] = f"t{len(self.texts)}"
            self.texts.append((self.cache[key], b, t.split("\n")[0][:50]))
        return self.cache[key]

    def scene(self, name, c):
        info = (1 if c.get("dark") else 0) | (2 if c.get("light") else 0) | \
               (4 if c.get("ending") else 0) | (8 if c.get("auto") else 0)
        img = c.get("image")
        has_img = img and img != "none"
        if has_img:
            info |= 16
        target = self.endings.index(c["ending"]) if c.get("ending") else \
            self.scenes.index(c["auto"]) if c.get("auto") else 0
        out = [f"; {name}", f"c_{name}:",
               f"    db 0x{info:02X},{ROUTES[c.get('route')]},"
               f"{self.images.index(img) if has_img else 0xFF},{target}",
               db(self.effect(c.get("on_enter")))]
        vs = as_list(c.get("variants"))
        out.append(f"    db {len(vs)}")
        for i, v in enumerate(vs):
            out += [db(self.cond(v.get("if"))), db(self.effect(v.get("effect"))),
                    f"    dw {self.text(v['text'], f'{name}.variants[{i}]')}"]
        out.append(f"    dw {self.text(c['text'], name)}")
        ops = as_list(c.get("options"))
        out.append(f"    db {len(ops)}")
        for i, op in enumerate(ops):
            out += [f"    db {1 if op.get('else') else 0}", db(self.cond(op.get("if"))),
                    db(self.effect(op.get("effect"))),
                    f"    db {self.scenes.index(op['goto'])}",
                    f"    dw {self.text(op['text'], f'{name}.options[{i}]', True)}  ; {op['text']}"]
        return out

    def generate(self):
        g = self.script["game"]
        out = ["; GENERATED by src/tools/rom.py from the script: do not edit by hand.",
               "",
               f"N_SCENES: equ {len(self.scenes)}",
               f"START_SCENE: equ {self.scenes.index(g['start'])}",
               f"HUM_START: equ {g['humanity']}",
               f"BOND_START: equ {g['bond']}",
               f"N_ITEMS: equ {len(self.items)}",
               f"N_ENDINGS: equ {len(self.endings)}", ""]
        body = []
        for name in self.scenes:
            body += self.scene(name, self.script["scenes"][name]) + [""]
        out += ["cond_light:", db(self.cond(g.get("light"))),
                "cond_dark:", db(self.cond(g.get("dark_costs")))]
        z = g.get("on_zero") or {}
        out += ["; when humanity reaches zero: destination by route (common, A, B, C)",
                "on_zero: db " + ",".join(str(self.scenes.index(z[r]) if z.get(r) else 0xFF)
                                          for r in ("common", "A", "B", "C"))]
        out += ["; forget: item mask, maximum humanity; ends in 0", "tab_forget:"]
        for e in as_list(g.get("forget")):
            out.append(f"    db {self.mask(e['item'], self.items)},{e['hum_max']}")
        out += ["    db 0", "", "tab_scenes:"]
        out += [f"    dw c_{n}" for n in self.scenes]
        out += [""] + body
        out += ["; item names, in bit order", "tab_items:"]
        out += [f"    dw {self.text(v, f'items.{k}', True)}  ; {v}" for k, v in self.script["items"].items()]
        out += ["; type of each ending (order of TYPES), to pick the ending screen music",
                "tab_ending_type: db " + ",".join(str(list(TYPES).index(f["type"]))
                                                  for f in self.script["endings"].values())]
        out += ["; name of each ending (the type is not shown; it only picks the music)", "tab_endings:"]
        out += [f"    dw {self.text(f['name'], f'endings.{k}', True)}  ; {k}"
                for k, f in self.script["endings"].items()]
        out += ["; stopwords (vanish at humanity 2 or less): length, codes...; 0",
                "stopwords:"]
        for w in self.script.get("stopwords") or []:
            b = self.encode(str(w).upper(), "stopwords")
            out.append(db([len(b)] + b) + f"  ; {w}")
        out.append("    db 0")
        # the "About the author" screen: label txt_about next to the text (z80asm does not
        # resolve an equ that points to a label defined later)
        self.aliases.setdefault(self.text(g["about"], "game.about"), []).append("txt_about")
        sub = wrap(g.get("subtitle", "").upper())
        out += ["; title screen subtitle, line by line; ends in dw 0", "subtitle:"]
        out += [f"    dw {self.text(l, 'subtitle', True)}" for l in sub] + ["    dw 0"]
        interface = self.script["interface"]
        self.fixed("txt_title", " ".join(g["title"].upper()))     # "D E M Ô N I O S"
        for label, key in FIXED_TEXTS.items():
            self.fixed(label, interface[key].upper())
        self.raw = sum(len(b) for _, b, _ in self.texts)
        dic = self.bpe()
        depth = {}

        def depth_of(c):
            if c < FIRST_PAIR:
                return 0
            if c not in depth:
                a, b = dic[c - FIRST_PAIR]
                depth[c] = 1 + max(depth_of(a), depth_of(b))
            return depth[c]
        self.max_depth = max((depth_of(FIRST_PAIR + i) for i in range(len(dic))), default=0)
        if self.max_depth > 20:
            sys.exit(f"BPE with depth {self.max_depth}: the Z80 stack cannot take it")
        self.dic = dic
        out += ["", f"; BPE dictionary: {len(dic)} pairs (codes 0x{FIRST_PAIR:02X}-"
                    f"0x{FIRST_PAIR + len(dic) - 1:02X}), maximum depth {self.max_depth}",
                f"FIRST_PAIR: equ 0x{FIRST_PAIR:02X}", "dic:"]
        out += [db([x for p in dic[i:i + 12] for x in p]) for i in range(0, len(dic), 12)]
        # short texts go into the font tiles without a drawing (40 slots of 32 bytes
        # in both banks; see font.free_codes); the rest stays in the main area
        self.slots = {(bank, c): [] for bank in (0, 1) for c in font.free_codes()}
        free = {k: 32 for k in self.slots}
        rest = []
        for t in sorted(self.texts, key=lambda t: -len(t[1])):
            slot = next((k for k in self.slots if free[k] >= len(t[1]) and not self.aliases.get(t[0])), None)
            if slot:
                self.slots[slot].append(t)
                free[slot] -= len(t[1])
            else:
                rest.append(t)
        self.in_font = sum(len(b) for v in self.slots.values() for _, b, _ in v)
        out += ["", "; texts (compressed); the short ones are in generated/font_b0.asm and font_b1.asm"]
        for label, b, sample in sorted(rest, key=lambda t: int(t[0][1:]) if t[0][1:].isdigit() else 0):
            out += [f"{a}:" for a in self.aliases.get(label, [])]
            out += [f"{label}:  ; {sample}"] + [db(b[i:i + 24]) for i in range(0, len(b), 24)]
        seen = f"{self.script['interface']['endings_seen'].upper()}: 0/{len(self.endings)}"
        out += ["; uncompressed: it is copied to RAM and the number is replaced",
                f"txt_seen:  ; {seen}", db(font.encode(seen) + [0]),
                f"TXT_SEEN_LEN: equ {len(seen) + 1}", f"TXT_SEEN_K: equ {seen.index('0')}"]
        if len(self.counters) > 8:
            sys.exit(f"{len(self.counters)} counters; RAM reserves 8")
        return out


def db(b):
    return "    db " + ",".join(f"0x{x:02X}" for x in b)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("script", nargs="?", default=ROOT / "src" / "script" / "demonios.yaml", type=Path)
    ap.add_argument("--lang", default="pt", choices=languages.LANGUAGES)
    a = ap.parse_args()
    r = subprocess.run([sys.executable, str(ROOT / "src" / "tools" / "script.py"), str(a.script),
                        "--lang", a.lang], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stdout + r.stderr)
    script, _ = languages.load(a.lang, yaml.safe_load(a.script.read_text(encoding="utf-8")))
    g = Generator(script)
    out = g.generate()
    dest = ROOT / "src" / "rom" / "generated" / "script.asm"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(out) + "\n")
    # the game font, with the short texts in the tiles without a drawing
    font_tiles = font.tiles()
    for bank in (0, 1):
        f = ["; GENERATED by src/tools/rom.py: the font (tiles 0x02-0x5F) with short texts stored",
             "; in the tiles without a drawing, which never show on screen."]
        for c in range(0x02, 0x60):
            slot = g.slots.get((bank, c))
            if slot is None:
                f += [f"; tile 0x{c:02X}", db(font_tiles[c - 1])]
                continue
            f.append(f"; tile 0x{c:02X}: no drawing, holds texts")
            used = 0
            for label, b, sample in slot:
                f += [f"{label}:  ; {sample}", db(b)]
                used += len(b)
            if used < 32:
                f.append(f"    ds {32 - used}")
        (dest.parent / f"font_b{bank}.asm").write_text("\n".join(f) + "\n")
    n_text = sum(len(b) for _, b, _ in g.texts) + 2 * len(g.dic)
    print(f"{dest.relative_to(ROOT)}: {len(g.scenes)} scenes, {len(g.texts)} texts: {g.raw} bytes "
          f"-> {n_text} with the dictionary ({len(g.dic)} pairs, depth {g.max_depth}); "
          f"{len(g.counters)} counter(s); {g.in_font} bytes of text in the tiles without a drawing")


if __name__ == "__main__":
    main()
