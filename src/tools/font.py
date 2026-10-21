"""The game's 5×7 font, as PV-1000 tiles (imported by src/tools/tiles.py).

The same drawings as the controller test ROM (../pv-1000_control_test_rom), plus the
letters that were missing (J, K, Q, Z), punctuation and the Portuguese accented capitals.

Tile codes:
  0x20–0x5F  ASCII (capitals only), white text;
  0x02–0x0C  Portuguese accented capitals (ACCENTS): accent on 2 rows, 1 row of spacing
             and the letter shrunk to 4 rows (LOWERED), with its baseline level with the others;
             Á is 0x19;
  0x0D–0x10  Spanish: Ñ Ü ¿ ¡ (EXTRAS);
  0x11–0x17  interface (UI): separator, humanity bar, cursor, "more", heart;
  0x18       em dash (—), as wide as the tile;
  0x1A–0x1D  free.
Tile 0x01 is left out: in bank 0 it holds the interrupt vector (0x0038).
Bytes 0x1E and 0x1F also serve, in the ROM text, as "new line" and "new page"
(they are never written to the screen).
Tiles 0x02–0x5F sit together in the ROM, from 0x0040 to 0x0BFF of each bank.
"""

FONT = {
    " ": [], "-": ["", "", "", "#####"], ":": ["", "##", "##", "", "##", "##"],
    ".": ["", "", "", "", "", "##", "##"], ",": ["", "", "", "", "", " ##", " ##", "##"],
    ";": ["", "##", "##", "", "", " ##", " ##", "##"],
    "!": ["  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "", "  #  "],
    "?": [" ### ", "#   #", "    #", "   # ", "  #  ", "", "  #  "],
    "/": ["    #", "    #", "   # ", "  #  ", " #   ", "#    ", "#    "],
    "'": ["  #  ", "  #  ", " #   "], '"': [" # # ", " # # "],
    "(": ["   # ", "  #  ", " #   ", " #   ", " #   ", "  #  ", "   # "],
    ")": [" #   ", "  #  ", "   # ", "   # ", "   # ", "  #  ", " #   "],
    "<": ["   # ", "  #  ", " #   ", "#    ", " #   ", "  #  ", "   # "],
    ">": [" #   ", "  #  ", "   # ", "    #", "   # ", "  #  ", " #   "],
    "0": [" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "],
    "1": ["  #  ", " ##  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "2": [" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"],
    "3": ["#####", "   # ", "  #  ", "   # ", "    #", "#   #", " ### "],
    "4": ["   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "],
    "5": ["#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "],
    "6": ["  ## ", " #   ", "#    ", "#### ", "#   #", "#   #", " ### "],
    "7": ["#####", "    #", "   # ", "  #  ", " #   ", " #   ", " #   "],
    "8": [" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "],
    "9": [" ### ", "#   #", "#   #", " ####", "    #", "   # ", " ##  "],
    "A": [" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "B": ["#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "],
    "C": [" ### ", "#   #", "#    ", "#    ", "#    ", "#   #", " ### "],
    "D": ["#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "],
    "E": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"],
    "F": ["#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "],
    "G": [" ### ", "#   #", "#    ", "# ###", "#   #", "#   #", " ####"],
    "H": ["#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"],
    "I": [" ### ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", " ### "],
    "J": ["  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "],
    "K": ["#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"],
    "L": ["#    ", "#    ", "#    ", "#    ", "#    ", "#    ", "#####"],
    "M": ["#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"],
    "N": ["#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"],
    "O": [" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "P": ["#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "],
    "Q": [" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"],
    "R": ["#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"],
    "S": [" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "],
    "T": ["#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
    "U": ["#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "],
    "V": ["#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "],
    "W": ["#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"],
    "X": ["#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"],
    "Y": ["#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "],
    "Z": ["#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"],
}

MARKS = {"´": ["    #", "   # "], "`": [" #   ", "  #  "], "^": ["  #  ", " # # "],
         "~": [" ## #", "# ## "], "¨": [" # # ", ""]}
LOWERED = {  # the accentable letters in 4 rows (leaves room for the accent)
    "A": [" ### ", "#   #", "#####", "#   #"], "E": ["#####", "#### ", "#    ", "#####"],
    "I": [" ### ", "  #  ", "  #  ", " ### "], "O": [" ### ", "#   #", "#   #", " ### "],
    "U": ["#   #", "#   #", "#   #", " ### "], "N": ["#   #", "##  #", "#  ##", "#   #"],
}
ACCENTS = {  # accented letter: (base letter, mark); code = 0x01 + position (Á: 0x19)
    "Á": ("A", "´"), "À": ("A", "`"), "Â": ("A", "^"), "Ã": ("A", "~"),
    "É": ("E", "´"), "Ê": ("E", "^"), "Í": ("I", "´"), "Ó": ("O", "´"),
    "Ô": ("O", "^"), "Õ": ("O", "~"), "Ú": ("U", "´"), "Ç": ("C", ","),
}
ACCENT_CODE = {ch: 0x01 + i for i, ch in enumerate(ACCENTS)} | {"Á": 0x19}

# Spanish: Ñ and Ü built like the accented ones; ¿ and ¡ drawn whole
EXTRAS = {"Ñ": 0x0D, "Ü": 0x0E, "¿": 0x0F, "¡": 0x10}
EXTRA_DRAWING = {
    "¿": ["  #  ", "", "  #  ", " #   ", "#    ", "#   #", " ### "],
    "¡": ["  #  ", "", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "],
}

# interface: code -> (color, 8 rows of 8 columns)
K, R, G, Y, B, M, C, W = range(8)
UI = {
    0x11: (B, ["", "", "", "########"]),                                       # separator
    0x12: (W, ["", " ###### ", " ###### ", " ###### ", " ###### ", " ###### ", " ###### "]),  # full bar
    0x13: (R, ["", " ###### ", " ###### ", " ###### ", " ###### ", " ###### ", " ###### "]),  # full bar, low humanity
    0x14: (B, ["", " ###### ", " #    # ", " #    # ", " #    # ", " #    # ", " ###### "]),  # empty bar
    0x15: (Y, [" #     ", " ##    ", " ###   ", " ####  ", " ###   ", " ##    ", " #     "]),  # cursor
    0x16: (Y, ["", " ##### ", " ##### ", "  ###  ", "  ###  ", "   #   "]),            # more
    0x17: (M, ["", " ## ## ", "#######", "#######", " ##### ", "  ###  ", "   #   "]),    # heart
    0x18: (W, ["", "", "", "########"]),                                       # em dash
}
EM_DASH = 0x18
UI_CODES = {"SEPARATOR": 0x11, "BAR": 0x12, "BAR_LOW": 0x13, "BAR_EMPTY": 0x14,
            "CURSOR": 0x15, "MORE": 0x16, "HEART": 0x17}
NEW_LINE, NEW_PAGE = 0x1E, 0x1F


def rows(ch):
    """The 8 rows (5 columns) of a character, with the accented ones already built."""
    if ch in EXTRA_DRAWING:
        return EXTRA_DRAWING[ch] + [""]
    if ch == "Ñ":
        return MARKS["~"] + [""] + LOWERED["N"] + [""]
    if ch == "Ü":
        return MARKS["¨"] + [""] + LOWERED["U"] + [""]
    if ch in ACCENTS:
        base, mark = ACCENTS[ch]
        g = FONT[base]
        if mark == ",":                          # Ç: the whole letter and the cedilla below
            return g[:6] + [" ### ", "  #  "]
        # mark on rows 0–1, one blank row and the letter in 4 rows, with its baseline
        # level with the others
        return MARKS[mark] + [""] + LOWERED[base] + [""]
    g = FONT.get(ch, [])
    return g + [""] * (8 - len(g))


def pattern(ch, color=7):
    """The tile's 32 bytes: unused plane, red, green, blue (bit 7 = leftmost pixel)."""
    plane = [sum(0x40 >> i for i, c in enumerate(r.ljust(5)) if c == "#") for r in rows(ch)[:8]]
    return [0] * 8 + [b if color & 1 else 0 for b in plane] + \
        [b if color & 2 else 0 for b in plane] + [b if color & 4 else 0 for b in plane]


def ui_pattern(color, drawing):
    plane = [sum(0x80 >> i for i, c in enumerate(r.ljust(8)) if c == "#") for r in (drawing + [""] * 8)[:8]]
    return [0] * 8 + [b if color & 1 else 0 for b in plane] + \
        [b if color & 2 else 0 for b in plane] + [b if color & 4 else 0 for b in plane]


def code(ch):
    if ch in ACCENT_CODE:
        return ACCENT_CODE[ch]
    if ch in EXTRAS:
        return EXTRAS[ch]
    if ch == "—":
        return EM_DASH
    if ch in FONT:                         # only what has a drawing (the rest would come out blank)
        return ord(ch)
    raise ValueError(f"character without a tile: {ch!r}")


def encode(text):
    return [code(ch) for ch in text.upper()]


def free_codes():
    """Codes 0x01–0x5F without a drawing (never shown on screen): the game stores data in
    their 32 pattern bytes. The space (0x20) is left out: it is the blank tile."""
    t = tiles()
    return [c for c in range(0x02, 0x60) if c != 0x20 and not any(t[c - 1])]


def tiles():
    """The patterns of tiles 0x01–0x5F, in order (the ones without a drawing are blank)."""
    by_code = {code(ch): ch for ch in list(FONT) + list(ACCENTS) + list(EXTRAS)}
    out = []
    for c in range(0x01, 0x60):
        if c in UI:
            out.append(ui_pattern(*UI[c]))
        else:
            out.append(pattern(by_code[c]) if c in by_code else [0] * 32)
    return out
