"""Script languages (imported by src/tools/script.py and src/tools/rom.py).

The base script (src/script/demonios.yaml) has the text in Portuguese and has everything: scenes,
conditions, effects and texts. Each other language is a file with only the texts,
src/script/demonios.<lang>.yaml, which replaces those of the base:

  game:      { title, subtitle, about }
  interface: { start, credits, continue, ... }   (the same keys as the base)
  stopwords: [ ... ]   (the words that vanish from the text at low humanity)
  items:     { RELOGIO: name, ... }
  endings:   { F1: name, ... }
  scenes:
    scene_name:
      text: |             the default text
      variants: [ ... ]   the variants, in the base's order (only if the base has them)
      options: [ ... ]    the option texts, in the base's order (only if the base has them)

This way the logic (targets, conditions, effects) lives in one place only and does not
diverge between languages. load() checks that the translation has exactly what the base has.
"""
import copy
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
LANGUAGES = ("pt", "en", "es")


def script_path(lang):
    return ROOT / "src" / "script" / ("demonios.yaml" if lang == "pt" else f"demonios.{lang}.yaml")


def as_list(v):
    return [] if v is None else v if isinstance(v, list) else [v]


def load(lang="pt", base=None):
    """The full script in the requested language. Returns (script, errors)."""
    base = base or yaml.safe_load(script_path("pt").read_text(encoding="utf-8"))
    if lang == "pt":
        return base, []
    tr = yaml.safe_load(script_path(lang).read_text(encoding="utf-8")) or {}
    script = copy.deepcopy(base)
    errors = []

    def replace(where, target, keys, source):
        for k in keys:
            if k not in (source or {}):
                errors.append(f"{lang}: missing {where}.{k}")
            else:
                target[k] = source[k]
        for k in source or {}:
            if k not in keys:
                errors.append(f"{lang}: {where}.{k} does not exist in the base script")

    replace("game", script["game"], ["title", "subtitle", "about"], tr.get("game"))
    replace("interface", script["interface"], list(base["interface"]), tr.get("interface"))
    replace("items", script["items"], list(base["items"]), tr.get("items"))
    if "stopwords" not in tr:
        errors.append(f"{lang}: missing stopwords")
    else:
        script["stopwords"] = tr["stopwords"]
    names = {}
    replace("endings", names, list(base["endings"]), tr.get("endings"))
    for k, v in names.items():
        script["endings"][k]["name"] = v

    tr_scenes = tr.get("scenes") or {}
    for name, scene in script["scenes"].items():
        t = tr_scenes.get(name)
        if t is None:
            errors.append(f"{lang}: missing scene {name}")
            continue
        if "text" not in t:
            errors.append(f"{lang}: scenes.{name}: missing text")
        else:
            scene["text"] = t["text"]
        for key in ("variants", "options"):
            orig, new = as_list(scene.get(key)), as_list(t.get(key))
            if len(orig) != len(new):
                errors.append(f"{lang}: scenes.{name}.{key}: {len(new)} texts, the base has {len(orig)}")
                continue
            for o, n in zip(orig, new):
                o["text"] = n
        for k in t:
            if k not in ("text", "variants", "options"):
                errors.append(f"{lang}: scenes.{name}.{k}: only texts go into the translation")
    for name in tr_scenes:
        if name not in script["scenes"]:
            errors.append(f"{lang}: scene {name} does not exist in the base script")
    return script, errors
