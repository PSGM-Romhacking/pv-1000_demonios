# Technical

**English** · [Português](technical.pt-BR.md) · [Español](technical.es.md)

For anyone who wants to make their own version of the game: fix it, translate it, change
the rules or tell a different story. To just play, the [README](../README.md) is enough.
Updated 2026-10-19.

- [Make your own version](#make-your-own-version): what to install, how to build the ROM, what to edit
- [Mechanics](#mechanics): humanity, bond and items, with the numbers; screen layout
- [Script format](#script-format): scenes, options, conditions, effects, interface
- [Languages](#languages): the three versions and the space each one uses; a simulation of 10 other languages
- [Console, ROM and engine](#console-rom-and-engine): the console, the ROM map, image and text compression, the engine, sound, tests, release

## Make your own version

Everything is generated from text files: the script in YAML, the images drawn by code and
the music written as notes. You can fix the text, translate it into another language or
replace the whole story, and build a new ROM.

**You need:** Python 3 with PyYAML, Pillow and NumPy; and `z80asm` (the GNU assembler,
package `z80asm` on Debian, Fedora and Arch).

```sh
make validate        # check the script without building anything
make roms           # build the three ROMs in build/
make rom GAME_LANG=en  # a single language (pt, en or es)
make play          # build and open in MAME (EMULATOR=... to use another one)
make gallery        # a ROM that shows the 18 images, one by one
```

| To… | Edit | See |
|---|---|---|
| fix or change the text | `src/script/demonios.yaml` (and the `.en`, `.es` translations) | [script format](#script-format) |
| translate into another language | create `src/script/demonios.<lang>.yaml` | [languages](#languages) |
| change the rules | the script (conditions and effects) | [mechanics](#mechanics) |
| change the images | `src/tools/art.py` | [console, ROM and engine](#console-rom-and-engine) |
| change the music | `src/tools/music.py` | [console, ROM and engine](#console-rom-and-engine) |

`make rom` validates the script first (destinations, items, line widths, reachable
endings) and shows how much of the 32 KB is left.

### Tests (optional)

For anyone touching the engine:

```sh
make mame [GAME_LANG=en]   # the ROM in MAME × in the Mil Capivaras core, screen by screen
```

Requires Rust (cargo), MAME as a Flatpak (`org.mamedev.MAME`) and the Mil Capivaras source
in `../mil_capivaras`. Mil Capivaras is an emulator that has not been published yet: for
now, only the author runs this test.

## Mechanics

The rules with the actual numbers (**mild spoilers**: what leads to each route and ending).
For players, spoiler-free: the [README](../README.md#how-it-works).

### The scene is the unit of everything

Each scene has:

- **image:** one of the illustrations (several scenes share the same one) or none;
- **text:** one or more pages (Fire 1 advances), with variants that depend on the state;
- **options:** 1 to 4, each with a destination and, optionally, a condition and an
  effect; or "Continue" (a scene that moves on by itself) or "End" (an ending scene);
- **on enter:** automatic effects (gain an item, set a flag, change humanity or bond).

### Game state

Lives only in the console's RAM (no password, no battery):

| Field | Range | Notes |
|---|---|---|
| humanity (H) | 0–7, starts at 7 | shown on the bar next to the separator (red at 2 or less) |
| bond (L) | 0–7, starts at 2 | the affection between the narrator and Laura; **hidden** |
| items | 6 (1 bit each) | watch, manuscript, lantern, key, portrait, bread |
| flags | 8 (1 bit each) | reread the manuscript, the oil ran out, saw the church... |
| counters | 2 | how many times he waited for daylight, how many times he looked for someone |
| endings seen | 7 bits | carried across playthroughs while the console stays on |

### Humanity

How much of the narrator is left. It is the story's clock.

- **Drops** with escapist or selfish choices (waiting, looking for others, keeping
  silent), with darkness without a lantern (only until the oil runs out), at fixed points
  in the story (reaching Laura's house, the oil running out without a lantern, the pier,
  the forgotten name) and when taking the key from the porter's hand.
- **"Protects"** (the next loss does not happen): rereading the manuscript, remembering
  in the church, sharing the bread, remembering with Laura, telling her a story,
  remembering the name for her.
- **Decides endings:** route C needs H ≥ 4 at the lock; FA1 needs H ≥ 3 at the end; at
  H = 0 the game cuts to an ending (FB2, or FA2 on route A, or FC on route C).
- **Erases items:** at H ≤ 2 the narrator forgets the watch and the key; at H ≤ 1, the
  portrait and the manuscript.
- **Degrades the text:**
  - H 5–7: full text;
  - H 3–4: only the first sentence of each page;
  - H 1–2: no punctuation and no stopwords (articles, prepositions, conjunctions); the
    options too.
  Route C (the account is being written) and the author screen do not degrade.

### Bond

The affection between the narrator and Laura, hidden as in a visual novel.

- **Rises:** going straight to her house, entering through the door with the key,
  listening and answering calmly, sharing the bread, giving her the portrait, remembering
  the past.
- **Falls:** detouring through the church, entering through the window, lying ("dawn will
  come tomorrow"), eating the bread alone, pulling her along without stopping, pretending
  not to notice.
- **Decides the routes:** "We stay" (route A) needs L ≥ 5; "We write" (route C) needs
  L ≥ 5, having reread the manuscript and H ≥ 4; with low L, "We stay" turns into a quarrel
  and leads to route B.
- **Decides endings:** FA1 needs L ≥ 6; on route B, L < 3 at the pier leads to FB2.
- **Laura falls silent before the narrator:** with low bond (L ≤ 2 in the bread
  conversation, L ≤ 5 when forgetting the name on route A, L ≤ 3 at the pier on route B),
  she loses the thought that passed from forehead to forehead. The following scenes change
  (the portrait, the lock, the quarrel, rehearsing the words, the woods, the dictation on
  route C). It foreshadows what awaits the narrator; with high bond, she keeps talking
  longer. Only the text changes, not the endings.

### Item choices

- **Portrait** (at the bedroom door): take it or leave it. Giving it to Laura is worth
  bond +2.
- **Key** (in the dead porter's hand): taking it costs humanity −1; without it, the way
  into Laura's house is through the window (bond −1 instead of +1).
- **Apothecary:** take the bread or the lantern, not both. The bread is for Laura; the
  lantern avoids the cost of darkness and spares humanity when the oil runs out.

### Screen layout (32 × 24 tiles; the TV shows columns 2–29)

```
 0 ┌──────────────────────────────┐
   │      imagem 20 x 11 tiles    │   rows 0–10 (columns 6–25)
11 │                              │
12 ├───────────────────── ▮▮▮▯▯▯▯ ┤   separator + humanity
13 │ A VELA SE APAGOU NO PRIMEIRO │
   │ PASSO. TREVA, SÓ TREVA:      │   rows 13–19: text (7 x 28)
19 │ NENHUM LAMPIÃO...          ▼ │   ▼ = more pages follow
20 ├──────────────────────────────┤
21 │ ▶ IR DIRETO À CASA DE LAURA  │
22 │   CORTAR PELO LARGO DA SÉ    │   rows 21–23: up to 3 options
23 │                              │   (with 4 options, the text loses a row)
   └──────────────────────────────┘
```

- **Scene without an image:** the text starts on row 1.
- **Title and ending:** the image takes 10 rows and the text starts on row 12.

## Script format

The script lives in `src/script/*.yaml`: it is the single source of the ROM. After
editing, run `make validate` (or just `make rom`, which validates before building).

The keys (the commands) are in English, for anyone translating or writing another story;
the text and the names of scenes, items, flags and endings are free.

### Header

```yaml
game:
  title: DEMÔNIOS
  subtitle: ...
  about: |                       # the "About the author" screen (pages separated by ---)
  start: quarto                  # first scene
  humanity: 7                    # starting humanity (0–7)
  bond: 2                        # starting bond (0–7)
  on_zero: { common: x, A: y }   # humanity 0: go to this scene, depending on the route
  forget:                        # items that vanish at low humanity
    - { item: RELOGIO, hum_max: 2 }
  light: { has: LAMPIAO, no_flag: OLEO_ACABOU }   # condition for "has light"
  dark_costs: { no_flag: OLEO_ACABOU }            # when darkness costs humanity

items:   { RELOGIO: relógio parado, ... }     # max. 8
flags:   [LEMBROU, ...]                       # max. 8
endings: { F1: { name: A Vela, type: bad } }  # max. 8; type: good, normal, bad, true_end
```

The limits come from the ROM's RAM: items, flags and endings seen take one byte each. The
game has no password (decided on 2026-10-18).

### Scene

```yaml
  nome_da_cena:          # the name is free (scenes:)
    act: 2                # act
    route: A              # A, B, C; no route = common (decides the on_zero destination)
    image: rua            # src/art/rua.png; "none" = text-only scene
    dark: true            # no light: image in blue outlines and, if dark_costs, −1 hum
    light: true           # the scene has its own light (candle), ignores darkness
    on_enter: { ... }     # effect on entering
    text: |               # default text (required)
      Parágrafo. Quebra de linha simples é respeitada.
      ---
      Página nova.
    variants:             # variants: the first whose condition holds replaces the text
      - if: { hum_max: 2 }
        effect: { ... }   # optional: applied if this variant is the one chosen
        text: |
          ...
    # and exactly ONE of these three:
    options: [ ... ]      # up to 4
    auto: proxima_cena    # no choice: "Continue"
    ending: F1            # ending screen
```

### Option

```yaml
      - text: Abrir o portão      # up to 26 columns (cursor + space + 26 = 28 visible)
        if: { has: CHAVE }        # hidden if the condition fails
        effect: { bond: +1 }
        goto: outra_cena
      - text: Abrir o portão
        else: true                # shown only if the previous option was hidden
        goto: outra_cena
```

### Conditions (`if`)

All keys must hold at the same time.

| Key | Example | Holds when |
|---|---|---|
| `has` / `lacks` | `has: [CHAVE, PAO]` | has all / has none |
| `flag` / `no_flag` | `flag: LEMBROU` | all set / none set |
| `hum_min` / `hum_max` | `hum_min: 3` | humanity ≥ / ≤ |
| `bond_min` / `bond_max` | `bond_min: 5` | bond ≥ / ≤ |
| `count_min` / `count_max` | `count_min: { ESPERA: 2 }` | counter ≥ / ≤ |
| `endings_min` | `endings_min: 2` | endings already seen (memory) ≥ |

### Effects (`effect`, `on_enter`)

| Key | Example | Does |
|---|---|---|
| `gain` / `lose` | `gain: [PAO]` | adds / removes items |
| `flag` / `unflag` | `flag: [BRIGA]` | sets / clears flags |
| `hum` | `hum: -1` | changes humanity (0–7) |
| `bond` | `bond: +2` | changes bond (0–7) |
| `protect` | `protect: true` | cancels the next humanity loss |
| `add` | `add: { ESPERA: 1 }` | adds to a counter |

### Degrading text

At humanity 3–4, only the first sentence of each page is shown; at 1–2, the text loses
its punctuation and the words in `stopwords` (articles, prepositions, conjunctions). The
options follow the same rule at level 1–2. Route C and the author screen do not degrade.

```yaml
stopwords: ["o", "a", "de", "no", ...]   # always quoted: in YAML, no/on become booleans
```

Write with this in mind: the first sentence of each page should stand on its own, and
words that carry meaning should not be on the list.

### Interface texts and other languages

The script's `interface:` section holds the ROM's fixed texts:

| Key | Text in pt |
|---|---|
| `start` | Iniciar |
| `credits` | Péricles S. - 2026 |
| `continue` | Continuar |
| `end` / `end_big` | Fim / F I M |
| `no_exit` | (sem saída) |
| `inventory` / `nothing` | Inventário / (nada) |
| `closes` | Fire 1 ou 2 fecha |
| `pause` / `back_to_title` | Pausa / Voltar ao título |
| `endings_seen` | Finais vistos |
| `about` / `back` | Sobre o autor / Voltar |

The title screen shows `game.title` with spaces between the letters.

Other languages live in `src/script/demonios.<lang>.yaml`, with the texts only, in the
same order as the base script (format at the top of `src/tools/languages.py`):

```yaml
game:      { title: DEMÔNIOS, subtitle: after the story by ..., about: ... }
interface: { start: Start, ... }
stopwords: ["the", "a", ...]
items:     { RELOGIO: pocket watch, ... }
endings:   { F1: The Candle, ... }
scenes:
  quarto:
    text: |
      I woke without knowing...
    options: [Reread what I wrote, Go to the window]
```

Changed a scene in the base script (new option, new variant)? The validator flags the
translation until it has the matching text: `make validate GAME_LANG=en`.

### What the validator checks

Existing destinations, declared items and flags, RAM limits, number of options, width of
options and words, and a warning for an unreachable scene or an ending without a scene.
It does not test the conditions: for that, play the ROM.

It also checks the translations (same scenes, variants and options as the base script),
the stopwords (they must be text) and the width of the interface texts, and warns about
characters with no glyph in the font. At the end, it shows how much space the compressed
text takes.

**Space:** the real limit is the ROM's free space, which only the build knows: `make rom`
(or `make roms`) shows the free bytes for each language. About 600 to 700 bytes are left
today. `make stats` lists the size of each scene.

## Languages

One 32 KB ROM per language, no mapper (see [Console, ROM and engine](#console-rom-and-engine)).
To add a language: create `src/script/demonios.<lang>.yaml` (format in
[Interface texts and other languages](#interface-texts-and-other-languages)) and run
`make rom GAME_LANG=<lang>`.

### Existing versions

| Language | File (No-Intro) | Raw text | Compressed | Free in ROM |
|---|---|---|---|---|
| Portuguese | `Demonios (World) (Pt) (Aftermarket) (Unl).bin` | 10 554 bytes | 5 801 bytes | **614 bytes** |
| English | `Demonios (World) (En) (Aftermarket) (Unl).bin` | 11 173 bytes | 5 893 bytes (+1.6%) | **551 bytes** |
| Spanish | `Demonios (World) (Es) (Aftermarket) (Unl).bin` | 10 997 bytes | 5 982 bytes (+3.1%) | **477 bytes** |

These numbers already include the five image changes of 2026-10-19 (ending screen with a
black wall, Laura's house without the lamppost, simplified woods, larger cave, pier water
without dithering), which are in the ROMs.

"Free" means the ROM's core area (0x4000–0x7FFF), which `make rom` reports. Beyond that,
the font tiles with no glyph still hold about 600 bytes, but only for short texts (up to
32 compressed bytes each).

### Simulation: 10 other languages

Limits of each ROM: **94 letter glyphs** (font codes 0x02–0x5F; the remaining tiles
belong to the images), text written left to right in 8 × 8 tiles, and the free space
above. A language fits without cuts if its compressed text grows by up to about **+11%**
over Portuguese (614 bytes over 5 801).

| Language | Distinct letters | Fits in 94? | Text vs. Portuguese | Fits in space? | Verdict |
|---|---|---|---|---|---|
| Japanese | kana only: ~70 | yes | ~ −20% | yes, with ~1.8 KB to spare | **feasible**, as in Famicom games; the particles (は が を に の) become the stopwords |
| Italian | Latin + 6 accents | yes | ~ +5% | yes (~311 bytes to spare) | **feasible** |
| Russian | Cyrillic, 33 letters | yes (replacing the Latin ones) | ~ +5% | yes (~311 bytes to spare) | **feasible**, with its own font |
| Indonesian | Latin, no accents | yes | ~ +10% | yes, just barely (~21 bytes to spare) | **feasible** |
| French | Latin + ~14 (é è ê ç œ…) | yes | ~ +12% | almost: cut ~1.5% of the text | feasible with a minimal cut |
| German | Latin + Ä Ö Ü ß | yes | ~ +18% | no: cut ~7% | feasible with cuts; long words strain the 28 columns |
| Arabic | 28 letters × up to 4 forms ≈ 110 | **no** | ~ −5% | yes | **hard**: right to left (engine changes) and joined letters that do not fit in 94 glyphs |
| Hindi | Devanagari, hundreds of combinations | **no** | — | — | **not feasible**; romanized only |
| Korean | 300–500 distinct syllables | **no** | — | — | **not feasible**; syllables assembled from parts become illegible |
| Mandarin | 600–800 distinct characters | **no** | — | — | **not feasible**: illegible at 8 × 8 and no space; pinyin only |

Notes:

- The size percentages are estimates for a typical translation, not measurements. The
  measured ones (English +1.6%, Spanish +3.1%) show the estimates tend to be pessimistic
  for this text, which is short and plain.
- Each new language needs **its own font** (only its letters). Today the three ROMs share
  the same font, with the Portuguese and Spanish accents.
- For languages that do not fit, the alternative to cutting text is dropping the "About
  the author" screen from that version: it frees about 900 bytes (the portrait and the
  biography), enough for all the Latin-script languages, German included.

## Console, ROM and engine

### The console

The **Casio PV-1000** (1983) has a Z80 at 3.58 MHz, no BIOS (the cartridge starts running
at `0x0000`), 1 KB of RAM and a video chip that only draws 8 × 8 tiles.

| Address / port | What |
|---|---|
| `0x0000–0x7FFF` | cartridge (ROM), 32 KB |
| `0xB800–0xBAFF` | 32 × 24 tile map (768 bytes) |
| `0xBB00–0xBBFF` | work RAM (256 bytes) |
| `0xBC00–0xBFFF` | PCG: patterns for tiles `0xE0–0xFF` (32 tiles), defined by the program |
| `0xF8–0xFA` | 3 square-wave channels: frequency = 8739 Hz / (63 − n); 63 = mute |
| `0xFB` | enables sound |
| `0xFC` | bit 0 = a new frame has started; read only in the interrupt (polling it loses frames on the MiSTer core) |
| `0xFD` | joystick matrix: write the row (1, 2, 4 or 8) and read the bits |
| `0xFE` | PCG address (the game writes `0xB8`) |
| `0xFF` | bit 5 = pattern bank, bit 4 = ROM-only patterns, bits 2–0 = border color |

**Tiles.** Each pattern is 32 bytes: 8 for an unused plane and 8 for each plane (red,
green, blue). Each pixel can be any of the 8 colors. A tile `N < 0xE0` comes from ROM, at
`N × 32` (plus `0x2000` with bit 5 of port FF set): 2 banks of 224 patterns. The bank
applies to the whole screen, so font and image share the same bank.

**Visible area.** The TV shows columns 2 to 29 of the map (224 pixels). The text uses
those 28 columns.

**Controller.** Matrix row 8: bit 1 = Fire 1, bit 0 = Fire 2 (names from the MiSTer core).
The controller has a switch that swaps the two buttons, and MAME calls bit 0 "Button 1".

### Why 32 KB, no mapper, one ROM per language

The game has to run everywhere: MAME, MiSTer, any other emulator, as well as the original
console. No Casio PV-1000 game uses bank switching and no emulator supports it, so the ROM
stays within the 32 KB the Z80 sees directly.
Each language (pt, en, es) is a ROM with the same structure; only the text changes.

### ROM map

| Range | Contents |
|---|---|
| `0x0000–0x003F` | header, jump to the engine and interrupt vector (`0x0038`) |
| `0x0040–0x0BFF` | bank 0: font and interface (tiles `0x02–0x5F`) |
| `0x0C00–0x1BFF` | bank 0: 128 patterns shared by the images (tiles `0x60–0xDF`) |
| `0x1C00–0x1FFF` | compressed images (tiles ≥ `0xE0` never come from here, so the space is free) |
| `0x2040–0x3BFF` | bank 1: the same font and another 128 patterns |
| `0x3C00–0x3FFF` | compressed images |
| `0x4000–0x7FFF` | engine (~2.9 KB), script and text (~6.3 KB), music (~0.3 KB), decompressor, rest of the images |

Free space in the core area: **614 bytes (pt), 551 (en), 477 (es)**. `make rom` shows the
breakdown. The 20 font tiles with no glyph hold another ~700 bytes of short texts (item
names, interface), up to 32 bytes each (`font.free_codes()`).

### Images

`src/tools/art.py` draws the 18 images in `src/art/` (160 × 88 pixels, 8 colors; the
author's portrait is smaller). `src/tools/tiles.py` converts them for the hardware:

1. Each image is 20 × 11 tiles. Tiles repeated across the images of a bank make up the
   ROM's **128 shared patterns**.
2. The unique tiles that stand out the most go to the **PCG** (up to 32 per image),
   loaded into RAM on entering the scene.
3. The rest are replaced by the closest pattern (changing 0 to ~1.5 % of the pixels).
4. **Compression:** the map uses RLE with "copy from the row above" (read from VRAM
   itself, no buffer); the PCG uses LZSS (12-bit distance, 4-bit length, 24 useful bytes
   per tile). About 53 % smaller than raw.
5. The compressed blocks are packed into the free 1 KB areas (`0x1C00`, `0x3C00`) by best
   subset sum; the rest goes into the core area.

Switching to a scene with an image takes about 6 frames (0.1 s). Consecutive scenes with
the same image do not redraw it.

### Font

`src/tools/font.py`: 5 × 7 letters in 8 × 8 tiles, uppercase only.

| Codes | What |
|---|---|
| `0x01` | none: in bank 0, its bytes hold the interrupt vector (`0x0038`) |
| `0x02–0x0C`, `0x19` | Portuguese accented capitals (Á is `0x19`): accent on 2 rows, 1 blank row and the letter on 4 |
| `0x0D–0x10` | Spanish: Ñ Ü ¿ ¡ |
| `0x11–0x17` | interface: separator, humanity bar, cursor, "more", heart |
| `0x18` | em dash (—) |
| `0x20–0x5F` | ASCII |

In the compressed text, `0x1E` and `0x1F` mean "new line" and "new page".

### Text

`src/tools/rom.py` generates `src/rom/generated/script.asm` from the script (the data
format is described at the top of the file):

- lines come pre-wrapped at 28 columns; pagination happens at runtime, because the height
  of the text area depends on the number of options;
- **BPE compression:** bytes `0x60–0xFF` are byte pairs (2 bytes per code in the
  dictionary), expanded recursively, one letter at a time, straight to the screen.
  Control codes never go into a pair. In Portuguese: 10 554 → 5 801 bytes;
- **degrading text** (low humanity): the engine strips sentences, punctuation and
  stopwords at runtime and rewraps the lines at 28 columns (`dt_degraded`).

### Engine

`src/rom/game.asm` interprets the script: scenes, text variants, options with conditions
and effects, humanity, bond, items, flags, counters, darkness, inventory, pause, title,
"About the author" and the ending screen. The rules are in [Mechanics](#mechanics).

The game's RAM (`0xBB00–0xBBFF`) uses fixed addresses, described at the top of
`game.asm`: the automated test reads the state from there.

### Sound

`src/tools/music.py` writes the music as notes and generates `src/rom/generated/music.asm`.
There is music only on the title and ending screens (one per ending type), on channels 2
and 3; the story itself is silent, which is the tale's theme. Channel 1 is kept for beeps.
Notes range from C#3 to A4, where the console's tuning is off by at most ~28 cents, and
each piece is transposed to the key where it is least out of tune.

### Tests

| Tool | What it checks |
|---|---|
| `src/tools/script.py` | the script: destinations, items, flags, widths, reachable endings |
| `src/tools/languages.py` | translations have the same scenes, variants and options as the Portuguese |
| `src/tools/test_mame.py` | ROM in MAME × in Mil Capivaras ("hw" model): the screen after each button press, pixel by pixel |

The bot that drives the ROM is in `src/tools/driver/` (Rust). It uses the Mil
Capivaras core (not yet published) and expects to find it in `../mil_capivaras`. The same
bot takes the README screenshots (`make screenshots`).

Result on 2026-10-19 with MAME 0.289: 3 918 screens, no differences. MAME shows 10 extra
rows of border at the top. MAME's own snapshots (F12) stretch the image to the TV aspect
ratio and crop a few pixels from the first and last columns; the game's frame does not.

### Release

A `v*` tag triggers `.github/workflows/release.yml`, which runs `make check dist` and
attaches the zips to the release. `make check` compares the ROMs' CRC32 with the ones in
the Makefile.

The build is reproducible: the distances between tiles (`tiles.py`) are computed with
integers.

### To check on real hardware

- TV overscan: if it crops column 2 or 29, move the text to 26 columns.
- Image drawing time and sound, on a 32 KB cartridge.
