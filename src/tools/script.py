#!/usr/bin/env python3
"""script.py: validates the YAML script.

Usage:
    python3 src/tools/script.py [SCRIPT.yaml] [--lang pt|en|es]
    python3 src/tools/script.py --stats         # also lists the text size per scene

Errors (missing target, undeclared item...) exit with code 1 and stop
make rom from building the ROM. Warnings (unreachable scene, ending with no scene...) are
only shown. The format is in docs/technical.pt-BR.md (Script format). Needs PyYAML.
"""
import argparse
import re
import sys
from collections import deque
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import languages  # noqa: E402
import measure_text  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent.parent

# items, flags and seen endings take one byte each in the ROM's RAM
MAX_ITEMS, MAX_FLAGS, MAX_ENDINGS, MAX_OPTIONS = 8, 8, 8, 4
COLUMNS = 28                  # visible columns on the TV: 2–29 (see docs/technical.pt-BR.md)
ENDING_TYPES = {"good", "normal", "bad", "true_end"}

SCENE_KEYS = {"act", "route", "image", "light", "dark", "on_enter", "text", "variants",
              "options", "auto", "ending"}
EFFECT_KEYS = {"gain", "lose", "flag", "unflag", "hum", "bond", "protect", "add"}
COND_KEYS = {"has", "lacks", "flag", "no_flag", "hum_min", "hum_max", "bond_min",
             "bond_max", "count_min", "count_max", "endings_min"}
OPTION_KEYS = {"text", "if", "else", "effect", "goto"}

class Report:
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warning(self, where, msg):
        self.warnings.append(f"{where}: {msg}")


def as_list(v):
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def wrapped_lines(text, columns=COLUMNS):
    """How many lines the text takes when wrapped at `columns` (same rule as the ROM)."""
    total = 0
    for paragraph in text.split("\n"):
        line = 0
        for word in paragraph.split():
            if line == 0:
                line = len(word)
                total += 1
            elif line + 1 + len(word) <= columns:
                line += 1 + len(word)
            else:
                line = len(word)
                total += 1
        if line == 0:
            total += 1
    return total


def scene_texts(scene):
    yield scene.get("text") or ""
    for t in as_list(scene.get("variants")):
        yield t.get("text") or ""


def validate(path, script, rep):
    game = script.get("game") or {}
    items = script.get("items") or {}
    flags = as_list(script.get("flags"))
    endings = script.get("endings") or {}
    scenes = script.get("scenes") or {}

    if len(items) > MAX_ITEMS:
        rep.error("items", f"{len(items)} items; the ROM holds {MAX_ITEMS}")
    if len(flags) > MAX_FLAGS:
        rep.error("flags", f"{len(flags)} flags; the ROM holds {MAX_FLAGS}")
    if len(endings) > MAX_ENDINGS:
        rep.error("endings", f"{len(endings)} endings; the ROM holds {MAX_ENDINGS}")
    for eid, e in endings.items():
        if (e or {}).get("type") not in ENDING_TYPES:
            rep.error(f"endings.{eid}", f"type must be one of {sorted(ENDING_TYPES)}")

    def scene_exists(where, name):
        if name not in scenes:
            rep.error(where, f"scene '{name}' does not exist")

    scene_exists("game.start", game.get("start"))
    for route, target in (game.get("on_zero") or {}).items():
        scene_exists(f"game.on_zero.{route}", target)
    if "pontos_senha" in game:
        rep.error("game.pontos_senha", "the game has no password anymore (2026-10-18); remove the key")
    for e in as_list(game.get("forget")):
        if e.get("item") not in items:
            rep.error("game.forget", f"item '{e.get('item')}' not declared")

    def check_items(where, names):
        for n in as_list(names):
            if n not in items:
                rep.error(where, f"item '{n}' not declared")

    def check_flags(where, names):
        for n in as_list(names):
            if n not in flags:
                rep.error(where, f"flag '{n}' not declared")

    def check_cond(where, cond):
        if not isinstance(cond, dict):
            rep.error(where, "'if' must be a mapping")
            return
        for k in cond:
            if k not in COND_KEYS:
                rep.error(where, f"unknown condition '{k}'")
        check_items(where, cond.get("has"))
        check_items(where, cond.get("lacks"))
        check_flags(where, cond.get("flag"))
        check_flags(where, cond.get("no_flag"))

    def check_effect(where, eff):
        if not isinstance(eff, dict):
            rep.error(where, "effect must be a mapping")
            return
        for k in eff:
            if k not in EFFECT_KEYS:
                rep.error(where, f"unknown effect '{k}'")
        check_items(where, eff.get("gain"))
        check_items(where, eff.get("lose"))
        check_flags(where, eff.get("flag"))
        check_flags(where, eff.get("unflag"))

    for key in ("light", "dark_costs"):
        if game.get(key):
            check_cond(f"game.{key}", game[key])

    used_endings = {}
    for name, scene in scenes.items():
        where = f"scenes.{name}"
        if not isinstance(scene, dict):
            rep.error(where, "scene must be a mapping")
            continue
        for k in scene:
            if k not in SCENE_KEYS:
                rep.error(where, f"unknown field '{k}'")
        if not scene.get("text"):
            rep.error(where, "missing 'text' (the default text)")
        if scene.get("on_enter"):
            check_effect(f"{where}.on_enter", scene["on_enter"])
        for i, t in enumerate(as_list(scene.get("variants"))):
            check_cond(f"{where}.variants[{i}]", t.get("if") or {})
            if t.get("effect"):
                check_effect(f"{where}.variants[{i}]", t["effect"])
        for t in scene_texts(scene):
            for word in t.split():
                if len(word) > COLUMNS:
                    rep.error(where, f"word longer than {COLUMNS} columns: '{word}'")

        exits = sum(bool(scene.get(k)) for k in ("options", "auto", "ending"))
        if exits != 1:
            rep.error(where, "needs exactly one of 'options', 'auto' and 'ending'")
        if scene.get("auto"):
            scene_exists(f"{where}.auto", scene["auto"])
        if scene.get("ending"):
            eid = scene["ending"]
            if eid not in endings:
                rep.error(where, f"ending '{eid}' not declared")
            used_endings.setdefault(eid, []).append(name)
        options = as_list(scene.get("options"))
        if len(options) > MAX_OPTIONS:
            rep.error(where, f"{len(options)} options; the screen holds {MAX_OPTIONS}")
        for i, op in enumerate(options):
            o = f"{where}.options[{i}]"
            for k in op:
                if k not in OPTION_KEYS:
                    rep.error(o, f"unknown field '{k}'")
            if not op.get("text"):
                rep.error(o, "missing 'text'")
            elif len(op["text"]) > COLUMNS - 2:          # cursor and space before the text
                rep.error(o, f"option text exceeds {COLUMNS - 2} columns")
            if op.get("else") and i == 0:
                rep.error(o, "'else' on the first option has nothing to refer to")
            scene_exists(o, op.get("goto"))
            if op.get("if"):
                check_cond(o, op["if"])
            if op.get("effect"):
                check_effect(o, op["effect"])

    for eid in endings:
        if eid not in used_endings:
            rep.warning(f"endings.{eid}", "no scene leads to this ending")

    # reachability ignoring conditions: whatever is not reachable even so is orphaned
    seen, queue = set(), deque([game.get("start")])
    zero_targets = list((game.get("on_zero") or {}).values())
    while queue:
        n = queue.popleft()
        if n in seen or n not in scenes:
            continue
        seen.add(n)
        c = scenes[n]
        queue.extend([c.get("auto")] if c.get("auto") else [])
        queue.extend(op.get("goto") for op in as_list(c.get("options")))
        queue.extend(zero_targets)
    for n in scenes:
        if n not in seen:
            rep.warning(f"scenes.{n}", "unreachable from the start")


def scene_size(scene):
    """Characters of the scene that go into the ROM: text, variants and options (without the
    page marks)."""
    ts = list(scene_texts(scene)) + [op.get("text") or "" for op in as_list(scene.get("options"))]
    return sum(len(re.sub(r"\n\s*---\s*\n", " ", t)) for t in ts)


def rom_size(script, rep):
    """How much the text takes compressed (an estimate; only `make rom` knows the real
    free space). Returns (compressed bytes, raw bytes)."""
    missing = measure_text.Counter()
    strings = [measure_text.encode(t, missing) + [0] for t in measure_text.texts(script)]
    if missing:
        rep.warning("text", f"characters without a tile in the font: {''.join(sorted(missing))}")
    raw = sum(len(c) for c in strings)
    symbols = {x for c in strings for x in c}
    comp, n_dic = measure_text.bpe(strings, [v for v in range(1, 256) if v not in symbols])
    return sum(len(c) for c in comp) + 2 * n_dic, raw


def statistics(script):
    lines = []
    total = 0
    for name, scene in (script.get("scenes") or {}).items():
        n = scene_size(scene)
        total += n
        lines.append(f"  {name:16} {n:5} chars")
    lines.append(f"  {'TOTAL':16} {total:5} chars")
    return lines, total


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("script", nargs="?", default=ROOT / "src" / "script" / "demonios.yaml", type=Path)
    ap.add_argument("--stats", action="store_true", help="list the text size per scene")
    ap.add_argument("--lang", default="pt", choices=languages.LANGUAGES,
                    help="apply src/script/demonios.<lang>.yaml over the base script")
    a = ap.parse_args()

    with open(a.script, encoding="utf-8") as f:
        script = yaml.safe_load(f)

    rep = Report()
    script, lang_errors = languages.load(a.lang, script)
    for e in lang_errors:
        rep.error("translation", e)
    for w in script.get("stopwords") or []:
        if not isinstance(w, str):
            rep.error("stopwords", f"{w!r} is not text: quote it (in YAML, no/on/yes become booleans)")
    for k, v in (script.get("interface") or {}).items():
        if len(str(v)) > COLUMNS - 2:
            rep.error(f"interface.{k}", f"exceeds {COLUMNS - 2} columns")
    validate(a.script, script, rep)
    lines, total = statistics(script)
    compressed, raw = rom_size(script, rep) if not rep.errors else (0, 0)

    for e in rep.warnings:
        print(f"warning: {e}")
    for e in rep.errors:
        print(f"ERROR:  {e}", file=sys.stderr)
    if a.stats:
        print("\n".join(lines))
    n = len(script.get("scenes") or {})
    print(f"{a.script.name} [{a.lang}]: {n} scenes, {total} characters of text, "
          f"{len(rep.errors)} error(s), {len(rep.warnings)} warning(s)")
    if compressed:
        print(f"text for the ROM: {raw} bytes -> ~{compressed} compressed "
              f"(the real free space shows up in make rom)")
    if rep.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
