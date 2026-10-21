#!/usr/bin/env python3
"""Runs the ROM in MAME (Flatpak org.mamedev.MAME, pv1000 driver) and on the Mil
Capivaras core ("hw" model) with the same buttons, and compares the screen after each
step, pixel by pixel.

MAME shows 10 extra rows of border at the top (244 rows against 224); the rest has to be
identical. MAME's own snapshots (F12) stretch the image to the TV aspect ratio and crop a
few pixels from the edges: that is why the comparison uses the raw frame (screen:pixels()).

Usage:  python3 src/tools/test_mame.py [--lang pt] [--random N]
"""
import argparse
import os
import random
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
DIR = Path.home() / ".cache" / "demonios_mame"
DRIVER = ROOT / "src" / "tools" / "driver" / "target" / "release" / "rom_driver"
WAIT = 60            # frames after each button (the game has finished drawing)


def fixed_route():
    p = [("-", 120), ("f1", WAIT), ("f2", WAIT), ("f2", WAIT), ("start", WAIT),
         ("down", WAIT), ("start", WAIT)]               # inventory; pause > back to title
    p += [("down", WAIT), ("f1", WAIT)] + [("f1", WAIT)] * 4         # about the author
    p += [("up", WAIT), ("f1", WAIT)] + [("f1", WAIT)] * 30          # 1st option until F1
    p += [("-", 1500), ("f1", WAIT)]                    # the ending music and the title
    return p


def random_route(seed, n=250):
    r = random.Random(seed)
    p = [("-", 120)]
    for _ in range(n):
        p.append((r.choice(["f1", "f1", "f1", "down", "down", "up", "f2"]), WAIT))
    return p


def mame(rom, steps):
    (DIR / "steps.txt").write_text("".join(f"{b} {q}\n" for b, q in steps))
    subprocess.run(["flatpak", "run", "org.mamedev.MAME", "pv1000", "-cart", str(Path(rom).resolve()),
                    "-video", "none", "-sound", "none", "-skip_gameinfo", "-nothrottle",
                    "-seconds_to_run", "3600", "-autoboot_script",
                    str(ROOT / "src" / "tools" / "test_mame.lua")],
                   check=True, capture_output=True, cwd=DIR)
    r = np.fromfile(DIR / "frames.raw", dtype=np.uint32).reshape(-1, 244, 224)
    return np.stack([(r >> 16) & 255, (r >> 8) & 255, r & 255], -1).astype(np.uint8)[:, 10:234]


def ours(rom, steps):
    cmds = ["hw"]
    for i, (b, q) in enumerate(steps):
        if b != "-":
            cmds.append(f"press_raw {b}")
        cmds += [f"frames {q}", f"shot {DIR}/n{i:04d}.ppm"]
    subprocess.run([str(DRIVER), str(rom)], input="\n".join(cmds) + "\n", text=True,
                   check=True)
    from PIL import Image
    return np.stack([np.array(Image.open(DIR / f"n{i:04d}.ppm").convert("RGB"))
                     for i in range(len(steps))])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--random", type=int, default=2)
    a = ap.parse_args()
    DIR.mkdir(parents=True, exist_ok=True)
    rom = ROOT / "build" / f"demonios_{a.lang}.bin"
    routes = [("fixed", fixed_route())] + [(f"random {s}", random_route(s))
                                           for s in range(1, a.random + 1)]
    failed = False
    for name, steps in routes:
        m, n = mame(rom, steps), ours(rom, steps)
        diff = [i for i in range(len(steps)) if not (m[i] == n[i]).all()]
        print(f"{a.lang} {name}: {len(steps)} screens, {len(diff)} different"
              + (f" (steps {diff[:10]})" if diff else ""))
        failed |= bool(diff)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
