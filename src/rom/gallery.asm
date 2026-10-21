; Gallery: the images of "Demônios" as the game will show them, in a 32 KB ROM for the
; Casio PV-1000. Fire 1 (or the right arrow) moves on to the next image; Fire 2
; (or the left arrow) goes back to the previous one.
;
; Build with `make gallery` (generates the tiles with src/tools/tiles.py and calls z80asm).
;
; ROM map (the same one the game will use, see docs/technical.md):
;   0x0000-0x001F  header (tile 0x00 of bank 0 is never shown)
;   0x0020-0x0BFF  bank 0, tiles 0x01-0x5F: the font
;   0x0C00-0x1BFF  bank 0, tiles 0x60-0xDF: patterns of the bank 0 images
;   0x1C00-0x1FFF  compressed images (part)
;   0x2020-0x2BFF  bank 1: the same font
;   0x2C00-0x3BFF  bank 1: patterns of the bank 1 images
;   0x3C00-0x3FFF  compressed images (part)
;   0x4000-0x7FFF  program, captions and the rest of the images
;
; The images are the same compressed data as in the game (src/tools/image_codec.py),
; unpacked by src/rom/decompress.asm.
;
; The image sits on rows 0-10, columns 6-25 of the map, as in the game.

MAP:    equ 0xB800          ; tile map, 32 x 24
PCG:    equ 0xBC00          ; patterns of tiles 0xE0-0xFF, 32 bytes each
CURRENT: equ 0xBB00         ; the image shown (0 to N_IMAGES - 1)
PREVIOUS: equ 0xBB01        ; buttons in the previous frame (to catch only the press)
BEEP:   equ 0xBB02          ; frames left until the beep goes quiet
LZ_REST:    equ 0xBB10      ; decompressor variables
LZ_REST16:  equ 0xBB11
LZ_POS:     equ 0xBB13
LZ_DOFF:    equ 0xBB15
LZ_SOFF:    equ 0xBB16
LZ_NBITS:   equ 0xBB17
LZ_FLAGS:   equ 0xBB18
LZ_LEN:     equ 0xBB19

; ------------------------------------------------------------------ header
        org 0x0000
        di
        ld sp,0xBC00        ; stack in the work RAM: 0xBC00 onwards is the PCG
        jp start

; ------------------------------------------------------------------ bank 0
        ds 0x0020-$
        include "generated/font.asm"
        ds 0x0C00-$
        include "generated/bank0.asm"
        ds 0x1C00-$
        include "generated/img_1c00.asm"

; ------------------------------------------------------------------ bank 1
        ds 0x2020-$
        include "generated/font.asm"
        ds 0x2C00-$
        include "generated/bank1.asm"
        ds 0x3C00-$
        include "generated/img_3c00.asm"

; ------------------------------------------------------------------ program
        ds 0x4000-$
start:
        xor a
        out (0xFF),a        ; black border, bank 0
        ld a,0xB8
        out (0xFE),a        ; map at 0xB800 and PCG at 0xBC00 (on the real console; the
                            ; MiSTer core already uses these fixed addresses)
        ld a,63
        out (0xF8),a        ; the three sound channels muted
        out (0xF9),a
        out (0xFA),a
        ld a,0x02
        out (0xFB),a        ; sound on
        ld a,0x01
        out (0xFC),a        ; enables the new frame flag (bit 0 of port FC)

        ld hl,MAP           ; clears the screen
        ld (hl),0x20
        ld de,MAP+1
        ld bc,32*24-1
        ldir
        ld hl,fixed
        call print_texts

        xor a
        ld (CURRENT),a
        ld (BEEP),a
        ld (PREVIOUS),a
        call show

main_loop:
        in a,(0xFC)         ; waits for a new frame
        and 1
        jr z,main_loop

        ld a,(BEEP)         ; the beep lasts a few frames
        or a
        jr z,buttons
        dec a
        ld (BEEP),a
        jr nz,buttons
        ld a,63
        out (0xF8),a

buttons: ld a,8             ; matrix row 3: bit 1 = Fire 1, bit 0 = Fire 2
        out (0xFD),a
        call settle
        in a,(0xFD)
        and 3
        ld c,a
        ld a,2              ; row 1 (FD=2): bit 1 = right (counts as Fire 1)
        out (0xFD),a
        call settle
        in a,(0xFD)
        and 2
        or c
        ld c,a
        ld a,4              ; row 2 (FD=4): bit 0 = left (counts as Fire 2)
        out (0xFD),a
        call settle
        in a,(0xFD)
        and 1
        or c
        ld c,a

        ld a,(PREVIOUS)     ; only what was just pressed
        cpl
        and c
        ld b,a
        ld a,c
        ld (PREVIOUS),a
        bit 1,b
        jr nz,next_image
        bit 0,b
        jr nz,prev_image
        jr main_loop

next_image:
        ld a,(CURRENT)
        inc a
        cp N_IMAGES
        jr c,switch_image
        xor a
        jr switch_image
prev_image:
        ld a,(CURRENT)
        or a
        jr nz,step_back
        ld a,N_IMAGES
step_back: dec a
switch_image: ld (CURRENT),a
        call show
        jr main_loop

; Shows the CURRENT image: switches the bank, unpacks the PCG patterns and the map, writes
; the caption.
show:
        ld a,(CURRENT)      ; IX = images + CURRENT * 8
        ld l,a
        ld h,0
        add hl,hl
        add hl,hl
        add hl,hl
        ld de,images
        add hl,de
        push hl
        pop ix

        ld a,40             ; short beep on channel 1
        out (0xF8),a
        ld a,3
        ld (BEEP),a

        ld a,(ix+0)         ; the image's pattern bank
        out (0xFF),a

        ld l,(ix+4)         ; PCG
        ld h,(ix+5)
        ld a,(ix+1)
        call pcg_unpack
        ld l,(ix+2)         ; map: 20 x 11 starting at column 6
        ld h,(ix+3)
        call map_unpack

        ld hl,MAP+13*32     ; clears rows 13-17
        ld (hl),0x20
        ld de,MAP+13*32+1
        ld bc,5*32-1
        ldir
        ld l,(ix+6)
        ld h,(ix+7)
        ; falls through into `print_texts`

; Writes texts: (map address, codes, 0)..., terminated by address 0.
print_texts: ld e,(hl)
        inc hl
        ld d,(hl)
        inc hl
        ld a,d
        or e
        ret z
pt_char:
        ld a,(hl)
        inc hl
        or a
        jr z,print_texts
        ld (de),a
        inc de
        jr pt_char

; Waits ~180 cycles for the joystick matrix to settle after switching rows
; (on the real console; it makes no difference in emulators). Same as the controller
; test ROM.
settle:
        ld b,12
s_loop: djnz s_loop
        ret

        include "decompress.asm"
        include "generated/images.asm"
        include "generated/texts.asm"
        include "generated/img_rest.asm"

        ds 0x8000-$
