# Demônios (pv-1000_demonios)
#   make validate    checks the script without building the ROM (needs PyYAML)
#   make stats       same, listing the text size per scene
#   make art         redraws src/art/*.png (src/tools/art.py)
#   make gallery     converts the art into tiles and builds build/gallery.bin (needs
#                    Pillow, NumPy and z80asm)
#   make play-gallery  opens the gallery in the emulator
#   make rom         builds the game: build/demonios_<GAME_LANG>.bin
#   make roms        builds the three languages (pt, en, es)
#   make check       builds the three and compares the CRC32 with the published version's
#   make dist        zips each ROM with the No-Intro name inside, for the release
#   make play        opens the game in the emulator (default: MAME as Flatpak; EMULATOR=... changes it)
#   make mame        compares the ROM in MAME and on the Mil Capivaras core, screen by screen
#   make screenshots takes the README screenshots (screenshots/<lang>/)
#   make cover       draws the cartridge cover (screenshots/cover.png)
#   make portraits   test ROM with reduced versions of the author's portrait
#                    (build/portraits.bin; make play-portraits opens it in the emulator)
#
# GAME_LANG=pt|en|es picks the language (default: pt) in validate, stats, rom and play.
# The translations live in src/script/demonios.<lang>.yaml (only the texts).

SCRIPT := src/script/demonios.yaml

GALLERY := build/gallery.bin
EMULATOR ?= flatpak run org.mamedev.MAME pv1000 -cart

GAME_LANG ?= pt
ROM := build/demonios_$(GAME_LANG).bin

.PHONY: validate stats art gallery play-gallery rom roms play check dist mame screenshots cover portraits play-portraits
validate:
	python3 src/tools/script.py $(SCRIPT) --lang $(GAME_LANG)

stats:
	python3 src/tools/script.py $(SCRIPT) --lang $(GAME_LANG) --stats

art:
	python3 src/tools/art.py

gallery: $(GALLERY)
$(GALLERY): src/rom/gallery.asm src/tools/tiles.py src/tools/font.py $(wildcard src/art/*.png)
	python3 src/tools/tiles.py
	mkdir -p build
	z80asm -I src/rom -o $@ src/rom/gallery.asm
	@echo "$@: $$(stat -c %s $@) bytes"

play-gallery: $(GALLERY)
	$(EMULATOR) $(abspath $(GALLERY))

rom: $(GALLERY)
	python3 src/tools/rom.py $(SCRIPT) --lang $(GAME_LANG)
	python3 src/tools/music.py
	z80asm -I src/rom -o $(ROM) src/rom/game.asm
	@python3 -c 'import sys; d = open(sys.argv[1], "rb").read(); n = len(d[0x4000:].rstrip(bytes(1))); print(f"{sys.argv[1]}: {0x4000 - n} bytes free in the middle (0x4000-0x7FFF)")' $(ROM)

roms:
	$(MAKE) rom GAME_LANG=pt
	$(MAKE) rom GAME_LANG=en
	$(MAKE) rom GAME_LANG=es

# CRC32 of the published version (pt en es): update when the game changes
CRC_pt := b87e2293
CRC_en := b0b1390b
CRC_es := 7f8f2ccf
CRC32 = python3 -c 'import sys,zlib;print(format(zlib.crc32(open(sys.argv[1],"rb").read()),"08x"))'

check: roms
	@for l in pt en es; do \
	  c=$$($(CRC32) build/demonios_$$l.bin); \
	  case $$l in pt) e=$(CRC_pt);; en) e=$(CRC_en);; es) e=$(CRC_es);; esac; \
	  if [ "$$c" = "$$e" ]; then echo "OK $$l: CRC32 $$c"; else echo "$$l: CRC32 $$c, differs from $$e"; exit 1; fi; \
	done

# GitHub renames attachments with spaces or parentheses: the No-Intro name goes inside the zip
dist: roms
	@for p in "pt Pt" "en En" "es Es"; do set -- $$p; \
	  python3 -c 'import sys,zipfile;zipfile.ZipFile(sys.argv[1],"w",zipfile.ZIP_DEFLATED).write(sys.argv[2],sys.argv[3])' \
	    build/demonios_$$1.zip build/demonios_$$1.bin "Demonios (World) ($$2) (Aftermarket) (Unl).bin"; \
	  echo "build/demonios_$$1.zip: $$(stat -c %s build/demonios_$$1.zip) bytes"; \
	done

play: rom
	$(EMULATOR) $(abspath $(ROM))

screenshots: roms
	python3 src/tools/screenshots.py

cover:
	python3 src/tools/cover.py

# the ROM in MAME (Flatpak) × on Mil Capivaras: screen by screen, pixel by pixel
mame: rom
	python3 src/tools/test_mame.py --lang $(GAME_LANG) --random 5

portraits:
	python3 src/tools/portraits.py

play-portraits: portraits
	$(EMULATOR) $(abspath build/portraits.bin)
