; Image decompressors (formats in src/tools/image_codec.py). Included by game.asm,
; which defines MAP, PCG and the LZ_* variables in RAM.

; Map in RLE with "copy from above": HL = data. Writes 20 x 11 tiles starting at
; column 6 of row 0.
map_unpack:
        ld de,MAP+6
        ld c,20             ; columns left in the row
        ld a,220
        ld (LZ_REST),a
mu_loop:
        ld a,(LZ_REST)
        or a
        ret z
        ld a,(hl)
        inc hl
        or a
        jr z,mu_command
        call mu_put
        jr mu_loop
mu_command:
        ld a,(hl)
        inc hl
        bit 7,a
        jr nz,mu_above
        ld b,a              ; 00 n v: v repeated n times
        ld a,(hl)
        inc hl
mu_repeat:
        push af
        call mu_put
        pop af
        djnz mu_repeat
        jr mu_loop
mu_above:
        and 0x7F            ; 00 80|n: copies n tiles from the row above
        ld b,a
mu_above_loop:
        push hl
        ld hl,-32
        add hl,de
        ld a,(hl)
        pop hl
        call mu_put
        djnz mu_above_loop
        jr mu_loop

; puts tile A on screen and advances; at the end of the row, skips the 12 columns outside
; the image. Preserves B and HL.
mu_put: ld (de),a
        inc de
        dec c
        jr nz,mup_count
        ld c,20
        push hl
        ld hl,12
        add hl,de
        ex de,hl
        pop hl
mup_count:
        ld a,(LZ_REST)
        dec a
        ld (LZ_REST),a
        ret

; PCG in LZSS: HL = data, A = number of tiles. Writes 24 bytes per tile (red, green,
; blue) starting at PCG+8, skipping the 8 bytes of each tile's unused plane. The
; references count positions in that stream of 24-byte steps.
pcg_unpack:
        or a
        ret z
        push hl
        ld e,a              ; LZ_REST16 = A * 24
        ld d,0
        ld h,d
        ld l,e
        add hl,hl
        add hl,de
        add hl,hl
        add hl,hl
        add hl,hl
        ld (LZ_REST16),hl
        ld hl,0
        ld (LZ_POS),hl
        pop hl
        ld de,PCG+8
        ld a,24
        ld (LZ_DOFF),a
        xor a
        ld (LZ_NBITS),a
pu_loop:
        push hl
        ld hl,(LZ_REST16)
        ld a,h
        or l
        pop hl
        ret z
        ld a,(LZ_NBITS)     ; next bit of the flags
        or a
        jr nz,pu_bit
        ld a,(hl)
        inc hl
        ld (LZ_FLAGS),a
        ld a,8
pu_bit: dec a
        ld (LZ_NBITS),a
        ld a,(LZ_FLAGS)
        rrca
        ld (LZ_FLAGS),a
        jr nc,pu_ref
        ld a,(hl)           ; literal
        inc hl
        call pu_put
        jr pu_loop
pu_ref: ld c,(hl)           ; reference: distance - 1 (12 bits), length - 3 (4 bits)
        inc hl
        ld a,(hl)
        inc hl
        push hl
        ld b,a
        and 0x0F
        add a,3
        ld (LZ_LEN),a
        ld a,b
        rrca
        rrca
        rrca
        rrca
        and 0x0F
        ld b,a
        inc bc              ; BC = distance
        ld hl,(LZ_POS)
        or a
        sbc hl,bc           ; HL = source position in the stream
        ld bc,PCG+8         ; BC = source tile: position / 24
pu_div: ld a,h
        or a
        jr nz,pu_sub
        ld a,l
        cp 24
        jr c,pu_rem
pu_sub: ld a,l
        sub 24
        ld l,a
        ld a,h
        sbc a,0
        ld h,a
        ld a,c
        add a,32
        ld c,a
        jr nc,pu_div
        inc b
        jr pu_div
pu_rem:
        ld a,24             ; L = byte within the tile
        sub l
        ld (LZ_SOFF),a
        ld h,0
        add hl,bc           ; HL = source in the PCG RAM
        ld a,(LZ_LEN)
        ld b,a
pu_copy:
        ld a,(hl)
        inc hl
        push af
        ld a,(LZ_SOFF)
        dec a
        jr nz,pu_soff
        push bc
        ld bc,8
        add hl,bc
        pop bc
        ld a,24
pu_soff:
        ld (LZ_SOFF),a
        pop af
        call pu_put
        djnz pu_copy
        pop hl
        jp pu_loop

; puts byte A in the PCG and advances (skipping the unused plane). Preserves BC and HL.
pu_put: ld (de),a
        inc de
        push hl
        ld a,(LZ_DOFF)
        dec a
        jr nz,pup_doff
        ld hl,8
        add hl,de
        ex de,hl
        ld a,24
pup_doff:
        ld (LZ_DOFF),a
        ld hl,(LZ_POS)
        inc hl
        ld (LZ_POS),hl
        ld hl,(LZ_REST16)
        dec hl
        ld (LZ_REST16),hl
        pop hl
        ret
