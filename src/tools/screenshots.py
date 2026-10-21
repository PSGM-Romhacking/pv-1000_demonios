#!/usr/bin/env python3
"""Takes the README screenshots: screenshots/<lang>/*.png.

Plays the ROM with the test bot (Mil Capivaras "hw" model) along the route of ending FA1,
always on the 1st option, and photographs some screens. The shot is the 224 × 224 frame
(columns 2–29 and 16 rows of border at the top and bottom), scaled up 2 times.

Usage:  python3 src/tools/screenshots.py      (or: make screenshots; needs make roms first)
"""
import subprocess
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent.parent
DRIVER = ROOT / "src" / "tools" / "driver" / "target" / "release" / "rom_driver"
# screens on the FA1 route: name -> how many choices after "Start"
ROUTE = {"room": 3, "street": 6, "apothecary": 7, "laura": 13, "hands": 20}


def screenshots(lang):
    out = ROOT / "screenshots" / lang
    out.mkdir(parents=True, exist_ok=True)
    rom = ROOT / "build" / f"demonios_{lang}.bin"
    with tempfile.TemporaryDirectory() as tmp:
        shots = {}
        cmds = ["hw", "frames 120", f"shot {tmp}/title.ppm"]
        cmds += ["press down", "press f1", "frames 10", f"shot {tmp}/author.ppm"]
        cmds += ["press f1"] * 4 + ["frames 30", "press f1"]          # back to the title
        step = {i: name for name, i in ROUTE.items()}
        for i in range(1, max(ROUTE.values()) + 1):
            cmds.append("choose 0")
            if i in step:
                cmds.append(f"shot {tmp}/{step[i]}.ppm")
        cmds += ["finish", "frames 30", f"shot {tmp}/ending.ppm"]
        subprocess.run([str(DRIVER), str(rom)], input="\n".join(cmds) + "\n", text=True,
                       check=True, capture_output=True)
        for f in sorted(Path(tmp).glob("*.ppm")):
            im = Image.open(f)
            im.resize((im.width * 2, im.height * 2), Image.NEAREST).save(out / f"{f.stem}.png")
            shots[f.stem] = out / f"{f.stem}.png"
    print(f"{lang}: {', '.join(shots)}")


if __name__ == "__main__":
    for lang in ("pt", "en", "es"):
        screenshots(lang)
