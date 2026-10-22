; =====================================================================
;  GLADSHEIM -- engine v4
;  Ultima II-style overworld and towns, Bard's Tale-style 3D dungeons,
;  sprite monster portraits, party combat with experience and levels,
;  shops, puzzles, and a world of six dungeons. Keyboard only.
;
;  Build:  ./build.sh   (python3 gen.py; acme main.asm; d64)
;
;  Memory map
;    $0400-$07E7  graphics layer (40x25 glyph codes), drawn to the bitmap by render.asm
;    $0801-$1FFF  BASIC stub, engine core, compositor
;    $2000-$29FF  monster portraits as loaded; copied to $C400 at start, then this
;                 becomes the last-presented graphics ($2000), text ($2400), colours ($2800)
;    $3800-$3FFF  hires glyphs (font, tiles, walls, frame)
;    $4000-$4FFF  64x64 overworld
;    $5000-$57FF  town maps (2 x 32x32)
;    $5800-$58FF  game variables
;    $5A00-$5AFF  working copy of the current dungeon floor
;    $5B00        row redraw flags
;    $6000-$B3FF  combat, towns, panel, text, saves, generated tables, pristine floors
;                 (the part over $A000 sits under the BASIC ROM, which is switched out)
;    $B400-$BEFF  saved state of all 11 dungeon floors   $BF00 save copy of the variables
;    $C000-$C3FF  colour matrix (VIC bank 3), sprite pointers $C3F8
;    $C400-$CDFF  monster portraits
;    $E000-$FF3F  hires bitmap (RAM under the KERNAL)
; =====================================================================
!cpu 6502
!ifndef MUSIC { MUSIC = 1 }        ; acme -DMUSIC=0 builds the edition without music
!if MUSIC {
!to "build/proto.prg", cbm
!symbollist "build/proto.sym"
} else {
!to "build/proto_nomusic.prg", cbm
!symbollist "build/proto_nomusic.sym"
}

; ---------------------------------------------------------------- zero page
mode    = $10       ; 0 overworld, 1 dungeon, 2 town
px      = $11
py      = $12
dpx     = $13
dpy     = $14
ddir    = $15       ; 0 N, 1 E, 2 S, 3 W
dl      = $16
dst     = $18
cdst    = $1a
str     = $1c
src     = $1e
csrc    = $20
tx      = $22
ty      = $23
tmp     = $24
mlo     = $25
mhi     = $26
ecur    = $27
cnt     = $28
ch      = $29
col     = $2a
ysave   = $2b
textcol = $2c
rx      = $2d
ry      = $2e
cx      = $2f
cy      = $30
num     = $31

; ---------------------------------------------------------------- compositor (render.asm)
EMPTY   = $ff
VSCR    = $0400
PG      = $2000         ; graphics codes as last presented (over the portraits' load area)
VTX     = $2400         ; 40x25 characters
VTC     = $2800         ; 40x25 colours (= VTX + $0400)
MATRIX  = $c000         ; colour matrix (VIC bank 3)
BITMAP  = $e000         ; under the KERNAL ROM: the CPU writes RAM, the VIC reads RAM
SPRDST  = $c400
GLYPHS  = $3800         ; 256 x 8 hires glyphs (page aligned)
tdirty  = $5b00         ; 25 row flags

; zero page for the compositor
rg      = $40           ; VSCR row
rp      = $42           ; PG row
rm      = $44           ; MATRIX row
rt      = $46           ; VTX row
rc      = $48           ; VTC row
bm      = $4a           ; bitmap cell
gp      = $4c           ; glyph / font pointer
gq      = $4e           ; second font pointer
prow    = $50
pcol    = $51
pdirty  = $52
lcode   = $53
rcode   = $54
under   = $55           ; terrain under the party (its background colour shows)
brow    = $56           ; bitmap address of the row being presented
offmap  = $58           ; tile shown beyond the map's edge

; ---------------------------------------------------------------- variables
VARS    = $5800
hp      = VARS+$00      ; 4 party members: arden, mira, torvik, sela
maxhp   = VARS+$04
sp      = VARS+$08
maxsp   = VARS+$0c
action  = VARS+$10      ; 0 attack, 1 parry, 2 spell, 3 none
mhp     = VARS+$14      ; up to 4 monsters
nmon    = VARS+$18
mtype   = VARS+$19
gold    = VARS+$1a      ; 16-bit
level   = VARS+$1c      ; current dungeon floor (0..NUM_LEVELS-1)
dungeon = VARS+$1d      ; current dungeon
prevx   = VARS+$1e
prevy   = VARS+$1f
seed    = VARS+$20      ; 16-bit
mbi     = VARS+$22
cres    = VARS+$23      ; combat result: 0 won, 1 fled
csp     = VARS+$24
target  = VARS+$25
dmg     = VARS+$26
cur     = VARS+$27
mul_a   = VARS+$28
mul_n   = VARS+$29
inlen   = VARS+$2a
tmp2    = VARS+$2b
tmp3    = VARS+$2c
mcur    = VARS+$2d
cell    = VARS+$2e
incombat = VARS+$2f
pcount  = VARS+$30
n16     = VARS+$32      ; 16-bit scratch for number output
dpc     = VARS+$34
fcur    = VARS+$35
ndig    = VARS+$36
pz      = VARS+$37
dmg_hi  = VARS+$38
acnt    = VARS+$39      ; monster attacks left this round
ox      = VARS+$3a      ; map view origin and the party's place in it
oy      = VARS+$3b
pvx     = VARS+$3c
pvy     = VARS+$3d
mwidth  = VARS+$3e
pk      = VARS+$3f      ; panel key line index
pkrow   = VARS+$4c
rseed   = VARS+$4d      ; ow_draw: 5 * map row (terrain looks)
inbuf   = VARS+$40      ; 12
TEMPS   = $5900         ; scratch the save leaves out
incol   = TEMPS+0       ; input_at: where, and how many letters at most
inrow   = TEMPS+1
inmax   = TEMPS+2
htarget = TEMPS+3       ; whom Arden heals ($ff = the most wounded)
crm     = TEMPS+4       ; party creation: which hero
mbuf    = VARS+$50      ; 48-byte message builder
wpn     = VARS+$80      ; 4: weapon value
arm     = VARS+$84      ; 4: armour
bonus   = VARS+$88      ; 3: spell upgrades (heal, bolt, song)
shop    = VARS+$8b      ; global shop index (town*5 + n)
owx     = VARS+$8c
owy     = VARS+$8d
inshop  = VARS+$8e
itidx   = VARS+$8f
member  = VARS+$90
n3v     = VARS+$91
n3col   = VARS+$92
n3row   = VARS+$93
town    = VARS+$94
lvl     = VARS+$98      ; 4: character level 1-20
mgt     = VARS+$9c      ; 4: might (damage bonus from levels)
xp_l    = VARS+$a0      ; 4
xp_h    = VARS+$a4      ; 4
sigils  = VARS+$a8      ; bit per runestone
keys    = VARS+$a9      ; bit per dungeon
won     = VARS+$aa
insheet = VARS+$ab
pstate  = VARS+$b0      ; 16: lever progress per floor
xpgain  = VARS+$c0      ; 16-bit
ggain   = VARS+$c2      ; 16-bit
savepx  = VARS+$c4      ; overworld position, kept in the save
savepy  = VARS+$c5
savemagic = VARS+$c6    ; 2 bytes: 'K','4'

GETIN   = $ffe4
SPRITES = $2000        ; portraits as loaded; copied to SPRDST in bank 3
SPR_PTR = (SPRDST - MATRIX) / 64
VX      = 1            ; left edge of full-view text screens (shop, sheet, ending)
OWMAP   = $4000
DMAP    = $5a00
HICODE  = $6000

FRAMECOL = 6        ; hires colours must be 0-7 in multicolour text mode
TITLECOL = 7
HEADCOL  = 3
TEXTCOL  = 1
DEADCOL  = 2
PC       = 28       ; side panel column

C_FLOOR  = 0
C_WALL   = 1
C_STAIRS = 2
C_CHEST  = 3
C_DOOR   = 4
C_INSCR  = 5
C_LEVER  = 6        ; 6,7,8 = iron, bone, gold
C_DOWN   = 9
C_KEY    = 10
C_PLATE  = 11
C_LIT    = 12
C_SECRET = 13
C_QUEST  = 14       ; a quest item (which one: lvl_qid)

; ---------------------------------------------------------------- macros
!macro msg .s {
        lda #<.s
        ldx #>.s
        jsr message
}
!macro print .x, .y, .s, .c {
        lda #<.s
        sta str
        lda #>.s
        sta str+1
        lda #.c
        sta textcol
        ldx #.x
        ldy #.y
        jsr print_at
}
!macro printnum .x, .y, .v {
        lda .v
        ldx #.x
        ldy #.y
        jsr print_num2
}
!macro mbs .s {
        lda #<.s
        ldx #>.s
        jsr mb_str
}
!macro ptrmsg .tlo, .thi {      ; message from a pointer table indexed by X
        lda .tlo,x
        pha
        lda .thi,x
        tax
        pla
        jsr message
}

; ---------------------------------------------------------------- BASIC stub
*= $0801
        !word basend, 2026
        !byte $9e
        !text "2061"
        !byte 0
basend  !word 0

; ---------------------------------------------------------------- init
*= $080d
start
        ldx #$ff
        txs
        lda #$36            ; BASIC ROM out: code and tables run on past $A000
        sta $01
        lda #$80
        sta $0291           ; lock C= + SHIFT case switch
        sta $028a           ; key repeat for all keys
        lda #0
        sta $d020
        sta $d021
        jsr $ff90           ; SETMSG 0: no KERNAL "searching / loading" text
        jsr video_init      ; hires bitmap mode, blank layers
        jsr music_init
        lda #0              ; the wilds tune over the story and the party
        jsr music_start
        jsr sprites_init
        jsr new_game
        jsr draw_frame
        jsr draw_panel
        jsr draw_party
        jsr intro           ; carry set: load a saved game
        bcc .new
        jsr enter_world
        jsr load_game
        bcc main
.new    jsr create_party
        jsr enter_world
        +msg m_welcome1
        +msg m_welcome2
        +msg m_welcome3

main
        jsr music_sync      ; the wilds tune above ground, the dungeon tune below
        jsr getkey
        ldx mode
        cpx #1
        beq +
        jsr ow_key
        jmp main
+       jsr dg_key
        jmp main

enter_world
        lda #START_X
        sta px
        lda #START_Y
        sta py
        lda #0
        sta mode
        jsr ow_colors
        jsr ow_draw
        jmp ow_status

; wait for a key; stir the raster position into the RNG (real hardware)
getkey
        jsr present
-       jsr GETIN
        beq -
        pha
        lda $d012
        eor seed
        beq +
        sta seed
+       pla
        rts

!zone new_game
new_game
        ldx #3
.p      lda p_maxhp,x
        sta hp,x
        sta maxhp,x
        lda p_maxsp,x
        sta sp,x
        sta maxsp,x
        lda p_wpn,x
        sta wpn,x
        lda #1
        sta lvl,x
        lda #0
        sta arm,x
        sta mgt,x
        sta xp_l,x
        sta xp_h,x
        dex
        bpl .p
        lda #0
        sta bonus
        sta bonus+1
        sta bonus+2
        sta inshop
        sta insheet
        sta incombat
        sta gold+1
        sta sigils
        sta keys
        sta won
        ldx #3
.nm     txa
        pha
        jsr default_name
        pla
        tax
        dex
        bpl .nm
        lda #0
        ldx #15
.ps     sta pstate,x
        sta qs,x
        dex
        bpl .ps
        lda #60             ; a little starting coin for the shops
        sta gold
        lda #$a5
        sta seed
        lda #$3c
        sta seed+1
        rts                 ; (the floors arrive pristine in their save slots at $B400)

; copy one 256-byte page: A = source page, X = destination page
!zone copy_page
copy_page
        sta .s+2
        stx .d+2
        ldy #0
.s      lda $ff00,y
.d      sta $ff00,y
        iny
        bne .s
        rts

; =====================================================================
;  Random numbers: 16-bit xorshift
; =====================================================================
rnd
        lda seed+1
        lsr
        lda seed
        ror
        eor seed+1
        sta seed+1
        ror
        eor seed
        sta seed
        eor seed+1
        sta seed+1
        rts

; A = n -> A = random 0..n-1   (high byte of rnd * n)
!zone rnd_n
rnd_n
        sta mul_n
        jsr rnd
        sta mul_a
        lda #0
        ldx #8
        lsr mul_a
.l      bcc .s
        clc
        adc mul_n
.s      ror
        ror mul_a
        dex
        bne .l
        rts

; about 2/3 of a second
!zone pause
pause
        jsr present
        lda #2
        sta pcount
        ldx #0
        ldy #0
.l      dey
        bne .l
        dex
        bne .l
        dec pcount
        bne .l
        rts

; =====================================================================
;  Screen helpers
; =====================================================================
!zone draw_frame
draw_frame
        ldx #26             ; map/dungeon window: cells 0-27 x 0-19
.h      lda #CH_HLINE
        sta VSCR,x
        sta VSCR+19*40,x
        dex
        bne .h
        ldx #1
.v      lda scr_lo,x
        sta dst
        lda scr_hi,x
        sta dst+1
        lda #CH_VLINE
        ldy #0
        sta (dst),y
        ldy #27
        sta (dst),y
        inx
        cpx #19
        bne .v
        lda #CH_TL
        sta VSCR
        lda #CH_TR
        sta VSCR+27
        lda #CH_BL
        sta VSCR+19*40
        lda #CH_BR
        sta VSCR+19*40+27
        ldx #11             ; rule under the title
.u      lda #CH_HLINE
        sta VSCR+1*40+28,x
        dex
        bpl .u
        rts

; text cursor: dst/cdst = text layer position X (0-39), Y (0-24); marks the row for redraw
set_cursor
        txa
        clc
        adc tx_lo,y
        sta dst
        sta cdst
        lda tx_hi,y
        adc #0
        sta dst+1
        clc
        adc #>(VTC-VTX)
        sta cdst+1
        lda #1
        sta tdirty,y
        rts

; print $ff-terminated screen-code string (str) at X,Y in textcol
!zone print_at
print_at
        jsr set_cursor
        ldy #0
.l      lda (str),y
        cmp #$ff
        beq .d
        sta (dst),y
        lda textcol
        sta (cdst),y
        iny
        bne .l
.d      rts

; print A (0-99) as two digits at X,Y in textcol
!zone print_num2
print_num2
        sta num
        jsr set_cursor
        ldx #$2f
        lda num
        sec
.l      inx
        sbc #10
        bcs .l
        adc #10+$30
        ldy #1
        sta (dst),y
        txa
        dey
        sta (dst),y
        lda textcol
        sta (cdst),y
        iny
        sta (cdst),y
        rts

; A = 8-bit value -> print_u (X col, Y row, ndig digits)
pu8
        sta n16
        lda #0
        sta n16+1
; print n16 right-aligned in ndig digits (1-5), leading spaces, at X,Y in textcol
!zone print_u
print_u
        jsr set_cursor
        lda #0
        sta pz
        lda #5
        sec
        sbc ndig
        tax
        ldy #0
.digit  lda #0
        sta tmp2
.sub    lda n16
        sec
        sbc pw_lo,x
        pha
        lda n16+1
        sbc pw_hi,x
        bcc .done
        sta n16+1
        pla
        sta n16
        inc tmp2
        jmp .sub
.done   pla
        lda tmp2
        bne .nz
        cpx #4
        beq .nz
        lda pz
        bne .zero
        lda #32
        jmp .put
.zero   lda #0
.nz     ora #$30
        sta pz
.put    sta (dst),y
        lda textcol
        sta (cdst),y
        iny
        inx
        cpx #5
        bne .digit
        rts

; scroll the message log and print A/X string on the bottom line
!zone message
message
        sta str
        stx str+1
        ldx #37
.l      lda VTX+21*40+1,x
        sta VTX+20*40+1,x
        lda VTX+22*40+1,x
        sta VTX+21*40+1,x
        lda VTX+23*40+1,x
        sta VTX+22*40+1,x
        lda VTX+24*40+1,x
        sta VTX+23*40+1,x
        lda #32
        sta VTX+24*40+1,x
        lda #TEXTCOL        ; older lines turn white
        sta VTC+20*40+1,x
        sta VTC+21*40+1,x
        sta VTC+22*40+1,x
        sta VTC+23*40+1,x
        dex
        bpl .l
        lda #1
        sta tdirty+20
        sta tdirty+21
        sta tdirty+22
        sta tdirty+23
        lda #TITLECOL
        sta textcol
        ldx #1
        ldy #24
        jmp print_at

; ---------------------------------------------------------------------
;  Message builder: mb_start, then mb_str / mb_num / mb_u16 / mb_name /
;  mb_mon ..., then mb_end (prints) or cmsg (prints + pauses)
; ---------------------------------------------------------------------
mb_start
        lda #0
        sta mbi
        rts

mb_char
        ldx mbi
        sta mbuf,x
        inc mbi
        rts

!zone mb_str
mb_str
        sta str
        stx str+1
        ldy #0
.l      lda (str),y
        cmp #$ff
        beq .d
        jsr mb_char
        iny
        bne .l
.d      rts

mb_num                      ; A = 0..255
        sta n16
        lda #0
        sta n16+1
; n16 as decimal without leading zeros
!zone mb_u16
mb_u16
        lda #0
        sta pz
        ldx #0
.digit  lda #0
        sta tmp2
.sub    lda n16
        sec
        sbc pw_lo,x
        pha
        lda n16+1
        sbc pw_hi,x
        bcc .done
        sta n16+1
        pla
        sta n16
        inc tmp2
        jmp .sub
.done   pla
        lda tmp2
        bne .emit
        cpx #4
        beq .emit
        ldy pz
        beq .skip
.emit   ora #$30
        sta pz
        stx tmp3
        jsr mb_char
        ldx tmp3
.skip   inx
        cpx #5
        bne .digit
        rts

mb_name                     ; X = party member (without the padding)
        lda pname_lo,x
        pha
        lda pname_hi,x
        tax
        pla
        jsr mb_str
-       ldx mbi
        lda mbuf-1,x
        cmp #32
        bne +
        dec mbi
        bne -
+       rts

mb_mon                      ; current monster type, singular
        ldx mtype
        lda mname_lo,x
        pha
        lda mname_hi,x
        tax
        pla
        jmp mb_str

mb_mons                     ; plural
        ldx mtype
        lda mplur_lo,x
        pha
        lda mplur_hi,x
        tax
        pla
        jmp mb_str

mb_art                      ; "a " / "an " / "the "
        ldx mtype
        lda mart_lo,x
        pha
        lda mart_hi,x
        tax
        pla
        jmp mb_str

mb_end
        lda #$ff
        jsr mb_char
        lda #<mbuf
        ldx #>mbuf
        jmp message

cmsg
        jsr mb_end
        jmp pause


; =====================================================================
;  OVERWORLD (and town walking, mode 2)
; =====================================================================
ow_colors
        lda #9              ; brown
        sta $d022
        lda #15             ; light grey
        sta $d023
        rts

; tile at (tx,ty) -> A
!zone get_tile
get_tile
        lda mode
        cmp #2
        bne .ow
        lda tx              ; town: 32 wide, TOWN_H tall, grass outside
        cmp #32
        bcs .grass
        lda ty
        cmp #TOWN_H
        bcs .grass
        lsr
        lsr
        lsr
        ldx town
        clc
        adc town_page,x
        sta src+1
        lda ty
        asl
        asl
        asl
        asl
        asl
        ora tx
        sta src
        ldy #0
        lda (src),y
        rts
.grass  lda #T_GRASS
        rts
.ow     lda tx              ; overworld: off the map is ocean
        ora ty
        and #$c0
        beq +
        lda #T_WATER
        rts
+       lda ty
        lsr
        lsr
        clc
        adc #>OWMAP
        sta src+1
        lda ty
        asl
        asl
        asl
        asl
        asl
        asl
        ora tx
        sta src
        ldy #0
        lda (src),y
        rts

; 26 x 18 tiles, one cell each. Out in the wilds the party stays at view (13,9);
; in a town the view stops at the town's edges so as much of it shows as possible.
VIEW_W = 26
VIEW_H = 18
PLAYER_VX = 13
PLAYER_VY = 9
!zone ow_draw
ow_draw
        lda px              ; view origin
        sec
        sbc #PLAYER_VX
        sta ox
        lda py
        sec
        sbc #PLAYER_VY
        sta oy
        lda mode
        cmp #2
        bne .origin
        lda ox              ; town: clamp to 0 .. 32-VIEW_W
        bpl +
        lda #0
+       cmp #32-VIEW_W+1
        bcc +
        lda #32-VIEW_W
+       sta ox
        lda oy              ; and 0 .. TOWN_H-VIEW_H
        bpl +
        lda #0
+       cmp #TOWN_H-VIEW_H+1
        bcc +
        lda #TOWN_H-VIEW_H
+       sta oy
.origin lda px              ; where the party appears in the view
        sec
        sbc ox
        sta pvx
        lda py
        sec
        sbc oy
        sta pvy
        lda #T_WATER        ; beyond the edge: ocean in the wilds, grass round a town
        ldx mode
        beq +
        lda #T_GRASS
+       sta offmap
        lda #0
        sta ry
.row    ldx ry              ; dst = graphics layer, row 1+ry, column 1
        inx
        lda scr_lo,x
        clc
        adc #1
        sta dst
        lda scr_hi,x
        adc #0
        sta dst+1
        lda oy              ; src = this map row, or nothing if off the map
        clc
        adc ry
        sta ty
        jsr map_row
        lda ty              ; rseed = 5 * map row
        asl
        asl
        adc ty
        sta rseed
        lda #0
        sta rx
.col    lda ox
        clc
        adc rx
        tay
        lda offmap
        cpy mwidth
        bcs .got
        ldx src+1
        beq .got
        lda (src),y
.got    ldy rx
        cpy pvx
        bne .put
        ldx ry
        cpx pvy
        bne .put
        cmp under           ; new ground under the party: redraw that cell
        beq +
        sta under
        tya
        clc
        adc dst             ; PG address of this cell = dst + (PG - VSCR)
        sta gp
        lda dst+1
        adc #>(PG-VSCR)
        sta gp+1
        ldy #0
        lda #$fe
        sta (gp),y
        ldy rx
+       lda #T_PLAYER
.put    tax
        lda tvar,x          ; terrain with several looks: pick one from the map position
        bne .var
        lda tile_char,x
        sta (dst),y
        jmp .nx
.var    sta tmp2
        lda rx              ; rnd64[(x + 5y) & 63]
        clc
        adc ox
        adc rseed
        and #63
        tax
        lda rnd64,x
        clc
        adc tmp2
        tax
        lda vtab,x
        sta (dst),y
.nx
        inc rx
        lda rx
        cmp #VIEW_W
        beq +
        jmp .col
+       inc ry
        lda ry
        cmp #VIEW_H
        beq +
        jmp .row
+       rts

; src = start of map row ty (overworld or town); src+1 = 0 if the row is off the map.
; mwidth = row length
map_row
        lda mode
        cmp #2
        beq .town
        lda #64
        sta mwidth
        lda ty
        cmp #64
        bcs .none
        lsr
        lsr
        clc
        adc #>OWMAP
        sta src+1
        lda ty
        asl
        asl
        asl
        asl
        asl
        asl
        sta src
        rts
.town   lda #32
        sta mwidth
        lda ty
        cmp #TOWN_H
        bcs .none
        lsr
        lsr
        lsr
        ldx town
        clc
        adc town_page,x
        sta src+1
        lda ty
        asl
        asl
        asl
        asl
        asl
        sta src
        rts
.none   lda #0
        sta src+1
        rts

; place (dungeon or town) at (px,py) -> X = place index, N clear; N set if none
!zone which_place
which_place
        ldx #NUM_PLACES-1
.l      lda place_x,x
        cmp px
        bne .no
        lda place_y,x
        cmp py
        bne .no
        txa
        rts
.no     dex
        bpl .l
        rts

!zone ow_key
ow_key
        ldx px
        stx tx
        ldx py
        stx ty
        cmp #$57            ; W
        beq .up
        cmp #$91            ; CRSR up
        beq .up
        cmp #$53            ; S
        beq .down
        cmp #$11            ; CRSR down
        beq .down
        cmp #$41            ; A
        beq .left
        cmp #$9d            ; CRSR left
        beq .left
        cmp #$44            ; D
        beq .right
        cmp #$1d            ; CRSR right
        beq .right
        cmp #$45            ; E
        bne +
        jmp .enter
+       cmp #$43            ; C
        bne +
        jmp char_sheet
+       cmp #$48            ; H
        bne +
        jmp camp_heal
+       cmp #$3f            ; ?  all the keys
        bne +
        jmp help_screen
+       cmp #$4a            ; J  journal: the quest log
        bne +
        jmp quest_log
+       cmp #$4d            ; M  music off/on
        bne +
        jmp music_toggle
+       cmp #$56            ; V  save game
        bne +
        jmp save_game
+       cmp #$4c            ; L  load game
        bne +
        jmp load_game
+       rts
.up     dec ty
        lda #<m_north
        ldx #>m_north
        jmp .try
.down   inc ty
        lda #<m_south
        ldx #>m_south
        jmp .try
.left   dec tx
        lda #<m_west
        ldx #>m_west
        jmp .try
.right  inc tx
        lda #<m_east
        ldx #>m_east
.try    sta mlo
        stx mhi
        lda mode
        cmp #2
        bne .gt
        lda tx              ; walking out of town?
        cmp #32
        bcs .out
        lda ty
        cmp #TOWN_H
        bcc .gt
.out    jmp town_leave
.gt     jsr get_tile
        tax
        lda tile_pass,x
        bne .ok
        lda mode
        cmp #2
        bne +
        txa
        jmp town_bump       ; bumping into people, counters, signs
+       cpx #T_HUT          ; the hermit's hut
        bne +
        ldx #HERMIT_NPC
        jmp talk_script
+       +msg m_blocked
        rts
.ok     stx tmp
        lda tx
        sta px
        lda ty
        sta py
        lda mlo
        ldx mhi
        jsr message
        jsr ow_draw
        jsr ow_status
        lda mode
        beq +
        rts
+       lda tmp
        cmp #T_DUNGEON
        beq .place
        cmp #T_TOWN
        beq .place
        cmp #T_CASTLE
        bne +
        jmp castle_heal
+       rts
.place  jsr which_place
        bmi +
        lda place_kind,x
        bne .townmsg
        lda place_idx,x
        tax
        +ptrmsg dg_msg_lo, dg_msg_hi
+       rts
.townmsg
        lda place_idx,x
        tax
        +ptrmsg town_ent_lo, town_ent_hi
        rts
.enter  lda mode
        beq +
        rts
+       jsr which_place
        bmi .none
        lda place_kind,x
        bne .etown
        lda place_idx,x
        jmp dg_enter
.etown  lda place_idx,x
        jmp town_enter
.none   +msg m_nothing
        rts

castle_heal
        jsr restore_hp
        jsr draw_party
        +msg m_castle
        +msg m_healed
        rts

restore_hp                  ; living members only
        ldx #3
-       lda hp,x
        beq +
        lda maxhp,x
        sta hp,x
+       dex
        bpl -
        rts

restore_sp
        ldx #3
-       lda hp,x
        beq +
        lda maxsp,x
        sta sp,x
+       dex
        bpl -
        rts

; H outside combat: Arden heals the most wounded companion
!zone camp_heal
camp_heal
        lda hp
        beq .cant
        lda sp
        cmp #3
        bcc .cant
        lda #0
        sta cur
        jsr pick_heal
        ldx htarget
        bmi .auto
        lda hp,x            ; that one: hurt at all?
        cmp maxhp,x
        beq .well
        stx target
        jmp .cast
.auto   jsr most_wounded
        lda tmp2            ; anyone hurt at all?
        bne .cast
.well   +msg m_allwell
        rts
.cast   lda sp
        sec
        sbc #3
        sta sp
        jsr heal_target
        jmp draw_party
.cant   jsr mb_start
        ldx #0
        jsr mb_name
        +mbs s_canthl
        jmp mb_end

; =====================================================================
;  DUNGEON
; =====================================================================
dg_colors
        lda #11             ; dark grey: floor + mortar
        sta $d022
        lda #14             ; light blue: lit stone
        sta $d023
        rts

; A = dungeon index
!zone dg_enter
dg_enter
        sta dungeon
        tax
        lda dg_need,x       ; sealed by runestones?
        beq .open
        and sigils
        cmp dg_need,x
        beq .open
        +msg m_sealed1
        +msg m_sealed2
        rts
.open   lda #1
        sta mode
        ldx dungeon
        lda dg_first,x
        ldy #C_STAIRS
        jsr load_level
        jsr clear_view
        jsr dg_colors
        jsr dg_render
        jsr dg_status
        +msg m_descend
        rts

; A = floor, Y = cell kind to arrive on (stairs up or down)
!zone load_level
load_level
        sta level
        sty cell
        tax
        lda lvl_save_hi,x
        ldx #>DMAP
        jsr copy_page
        ldx #0
.find   lda DMAP,x
        cmp cell
        beq .got
        inx
        bne .find
.got    txa
        and #$0f
        sta dpx
        sta prevx
        txa
        lsr
        lsr
        lsr
        lsr
        sta dpy
        sta prevy
        lda #0              ; face the first open way
        sta ddir
.face   ldx ddir
        lda dpx
        clc
        adc fwd_dx,x
        sta cx
        lda dpy
        clc
        adc fwd_dy,x
        sta cy
        jsr dg_cell
        cmp #C_WALL
        beq .next
        cmp #C_SECRET
        beq .next
        rts
.next   inc ddir
        lda ddir
        cmp #4
        bne .face
        lda #0
        sta ddir
        rts

save_level
        ldx level
        lda lvl_save_hi,x
        tax
        lda #>DMAP
        jmp copy_page

; climb the stairs up: to the floor above, or out into daylight
!zone dg_leave
dg_leave
        jsr save_level
        ldx level
        lda lvl_top,x
        bne .surface
        dex
        txa
        ldy #C_DOWN
        jsr load_level
        jsr dg_render
        jsr dg_status
        +msg m_climb
        rts
.surface
        lda #0
        sta mode
        jsr ow_colors
        jsr ow_draw
        jsr ow_status
        +msg m_ascend
        rts

dg_descend
        jsr save_level
        ldx level
        inx
        txa
        ldy #C_STAIRS
        jsr load_level
        jsr dg_render
        jsr dg_status
        +msg m_deeper
        rts

!zone clear_view
clear_view
        ldx #1
.r      lda scr_lo,x
        sta dst
        lda tx_lo,x
        sta src
        lda scr_hi,x
        sta dst+1
        lda tx_hi,x
        sta src+1
        ldy #26
.c      lda #EMPTY
        sta (dst),y
        lda #32
        sta (src),y
        dey
        bne .c
        lda #1
        sta tdirty,x
        inx
        cpx #19
        bne .r
        rts

; X = index of (cx,cy) in the floor ; carry set if off the map
cell_index
        lda cx
        ora cy
        and #$f0
        beq +
        sec
        rts
+       lda cy
        asl
        asl
        asl
        asl
        ora cx
        tax
        clc
        rts

; dungeon cell at (cx,cy) -> A ; outside the floor counts as wall
dg_cell
        jsr cell_index
        bcc +
        lda #C_WALL
        rts
+       lda DMAP,x
        rts

; X = index of the party's own cell
here_index
        lda dpy
        asl
        asl
        asl
        asl
        ora dpx
        tax
        rts

clear_here
        jsr here_index
        lda #C_FLOOR
        sta DMAP,x
        jmp dg_render       ; whatever lay here is gone from the floor

; ---------------------------------------------------------------------
;  3D view: clear buffer to ceiling/floor, then paint wall pieces
;  back-to-front. Secret walls draw as walls; doors use the door pieces.
; ---------------------------------------------------------------------
!zone dg_render
dg_render
        ldx #0              ; ceiling over the top half, floor below
.clr    lda scr_lo+VIEW3D_Y,x
        clc
        adc #VIEW3D_X
        sta dst
        lda scr_hi+VIEW3D_Y,x
        adc #0
        sta dst+1
        lda #D_CEIL
        cpx #WIN_H/2
        bcc +
        lda #D_FLOOR
        cpx #11             ; floor seams at each depth boundary
        beq .ln
        cpx #13
        beq .ln
        cpx #15
        bne +
.ln     lda #D_FLOORLN
+       ldy #WIN_W-1
-       sta (dst),y
        dey
        bpl -
        inx
        cpx #WIN_H
        bne .clr

        lda #0
        sta ecur
.e      ldx ddir
        lda dir_base,x
        clc
        adc ecur
        tay
        lda elem_dx,y
        clc
        adc dpx
        sta cx
        lda elem_dy,y
        clc
        adc dpy
        sta cy
        jsr dg_cell
        ldx ecur
        cmp #C_WALL
        beq .wall
        cmp #C_SECRET
        beq .wall
        cmp #C_DOOR
        bne .skip
        lda door_lo,x
        sta dl
        lda door_hi,x
        sta dl+1
        jsr drawlist
        jmp .skip
.wall   lda elem_lo,x
        sta dl
        lda elem_hi,x
        sta dl+1
        jsr drawlist
.skip   inc ecur
        lda ecur
        cmp #NUM_ELEM
        bne .e
        ; fall through: what lies on the floor

; things on the floor straight ahead (here, 1 and 2 steps), drawn on the floor squares
!zone dg_items
dg_items
        lda dpx
        sta cx
        lda dpy
        sta cy
        lda #0
        sta ecur            ; distance
.d      jsr dg_cell
        ldx ecur
        beq .here           ; the square we stand on is always in sight
        cmp #C_WALL
        beq .done
        cmp #C_SECRET
        beq .done
        cmp #C_DOOR
        beq .done
.here   cmp #16             ; guardians ($80+) can't be seen
        bcs .next
        tay
        lda item_of,y
        bmi .next
        asl                 ; glyph = ITEM_BASE + item * 4 (+2 far away)
        asl
        cpx #2
        bne +
        ora #2
+       clc
        adc #ITEM_BASE
        ldy item_off,x
        sta VSCR+512,y
        clc
        adc #1
        sta VSCR+513,y
.next   ldx ddir
        lda cx
        clc
        adc fwd_dx,x
        sta cx
        lda cy
        clc
        adc fwd_dy,x
        sta cy
        inc ecur
        lda ecur
        cmp #3
        bne .d
.done   rts

; graphics-layer offsets (from VSCR+512) of the two middle floor cells, 0/1/2 steps ahead
item_off !byte (VIEW3D_Y+16)*40+VIEW3D_X+12-512, (VIEW3D_Y+14)*40+VIEW3D_X+12-512, (VIEW3D_Y+12)*40+VIEW3D_X+12-512

; run list at (dl): lo, hi, length, glyph ... terminated by hi = 0
!zone drawlist
drawlist
        ldy #0
.n      lda (dl),y
        sta dst
        iny
        lda (dl),y
        beq .done
        sta dst+1
        iny
        lda (dl),y
        sta cnt
        iny
        lda (dl),y
        iny
        sty ysave
        ldy cnt
        dey
.f      sta (dst),y
        dey
        bpl .f
        ldy ysave
        jmp .n
.done   rts

!zone dg_key
dg_key
        cmp #$57            ; W
        beq .fwd
        cmp #$91
        beq .fwd
        cmp #$51            ; Q  (not A: that's attack in combat)
        beq .left
        cmp #$9d
        beq .left
        cmp #$44            ; D
        beq .right
        cmp #$1d
        beq .right
        cmp #$53            ; S
        beq .back
        cmp #$11
        beq .back
        cmp #$45            ; E
        bne +
        jmp dg_use
+       cmp #$43            ; C
        bne +
        jmp char_sheet
+       cmp #$48            ; H
        bne +
        jmp camp_heal
+       cmp #$3f            ; ?
        bne +
        jmp help_screen
+       cmp #$4a            ; J  journal: the quest log
        bne +
        jmp quest_log
+       cmp #$4d            ; M  music off/on
        bne +
        jmp music_toggle
+       rts
.left   lda ddir
        sec
        sbc #1
        jmp .turn
.right  lda ddir
        clc
        adc #1
        jmp .turn
.back   lda ddir
        clc
        adc #2
.turn   and #3
        sta ddir
        jsr dg_render
        jmp dg_status

.fwd    ldx ddir
        lda dpx
        clc
        adc fwd_dx,x
        sta cx
        lda dpy
        clc
        adc fwd_dy,x
        sta cy
        jsr dg_cell
        cmp #C_WALL
        bne +
        +msg m_wall
        rts
+       cmp #C_DOOR
        bne +
        jmp door_bump
+       cmp #C_SECRET
        bne +
        jsr cell_index      ; an illusion: it was never there
        lda #C_FLOOR
        sta DMAP,x
        +msg m_illusion
        lda #C_FLOOR
+       sta cell
        lda dpx
        sta prevx
        lda dpy
        sta prevy
        lda cx
        sta dpx
        lda cy
        sta dpy
        jsr dg_render
        jsr dg_status
        jmp arrive

; what happens on arriving at a cell (value in `cell`)
!zone arrive
arrive
        lda cell
        bpl +
        jmp guardian
+       cmp #C_STAIRS
        bne +
        ldx level
        lda lvl_top,x
        beq .up
        +msg m_stairs
        rts
.up     +msg m_stairsup
        rts
+       cmp #C_DOWN
        bne +
        +msg m_stairsdn
        rts
+       cmp #C_CHEST
        bne +
        jmp open_chest
+       cmp #C_INSCR
        bne +
        jmp read_inscription
+       cmp #C_KEY
        bne +
        jmp pick_key
+       cmp #C_QUEST
        bne +
        jmp pick_quest
+       cmp #C_PLATE
        bne +
        jmp light_plate
+       cmp #C_LIT
        bne +
        +msg m_litrune
        rts
+       cmp #C_LEVER
        bcc .floor
        cmp #C_LEVER+3
        bcs .floor
        sec
        sbc #C_LEVER
        tax
        +ptrmsg lever_lo, lever_hi
        rts
.floor  jsr rnd             ; wandering monsters
        cmp #13
        bcc +
        rts
+       lda level
        asl
        asl
        sta tmp
        lda #4
        jsr rnd_n
        clc
        adc tmp
        tax
        lda lvl_rnd,x
        sta mtype
        tax
        lda mon_grp,x
        jsr rnd_n
        clc
        adc #1
        sta nmon
        +msg m_ambush
        jmp combat

; E: climb, descend, or pull a lever
!zone dg_use
dg_use
        jsr here_index
        lda DMAP,x
        cmp #C_STAIRS
        bne +
        jmp dg_leave
+       cmp #C_DOWN
        bne +
        jmp dg_descend
+       cmp #C_LEVER
        bcc +
        cmp #C_LEVER+3
        bcs +
        jmp pull_lever
+       +msg m_noexit
        rts

; --------------------------------------------------------------------- guardians
!zone guardian
guardian
        and #$7f
        tax
        lda guard_type,x
        sta mtype
        lda guard_count,x
        sta nmon
        +msg m_guard
        jsr combat
        lda cres
        bne .fled
        jmp clear_here
.fled   lda prevx           ; fled: back to where we came from
        sta dpx
        lda prevy
        sta dpy
        jsr dg_render
        jmp dg_status

; --------------------------------------------------------------------- chests, keys, runes
!zone open_chest
open_chest
        jsr clear_here
        +msg m_openchest
        ldx level
        lda lvl_cgold_lo,x
        clc
        adc gold
        sta gold
        lda lvl_cgold_hi,x
        adc gold+1
        sta gold+1
        jsr draw_party
        ldx level
        +ptrmsg lvl_chest1_lo, lvl_chest1_hi
        ldx level
        lda lvl_chest2_lo,x         ; "-" means no second line
        sta str
        lda lvl_chest2_hi,x
        sta str+1
        ldy #0
        lda (str),y
        cmp #'-'
        beq +
        ldx level
        +ptrmsg lvl_chest2_lo, lvl_chest2_hi
+       ldx level
        lda lvl_sigil,x
        bmi +
        tax
        lda bitmask,x
        ora sigils
        sta sigils
+       ldx level
        lda lvl_win,x
        beq +
        jmp the_end
+       rts

pick_key
        jsr clear_here
        ldx dungeon
        lda bitmask,x
        ora keys
        sta keys
        +msg m_key
        rts

!zone light_plate
light_plate
        jsr here_index
        lda #C_LIT
        sta DMAP,x
        jsr dg_render       ; the plate glows
        +msg m_rune
        ldx #0              ; any dark plates left?
.l      lda DMAP,x
        cmp #C_PLATE
        beq .more
        inx
        bne .l
        jsr open_doors
        +msg m_rumble
        rts
.more   rts

open_doors
        ldx #0
-       lda DMAP,x
        cmp #C_DOOR
        bne +
        lda #C_FLOOR
        sta DMAP,x
+       inx
        bne -
        jmp dg_render

read_inscription
        ldx level
        +ptrmsg lvl_insc1_lo, lvl_insc1_hi
        ldx level
        +ptrmsg lvl_insc2_lo, lvl_insc2_hi
        rts

; --------------------------------------------------------------------- doors / puzzles
; (cx,cy) = the door in front of the party
!zone door_bump
door_bump
        ldx level
        lda lvl_puzzle,x
        cmp #P_RIDDLE
        beq .riddle
        cmp #P_KEY
        bne .say
        ldx dungeon
        lda bitmask,x
        and keys
        beq .say
        jsr .open
        +msg m_keyturns
        rts
.say    ldx level
        +ptrmsg lvl_door1_lo, lvl_door1_hi
        ldx level
        +ptrmsg lvl_door2_lo, lvl_door2_hi
        rts
.riddle ldx level
        +ptrmsg lvl_door1_lo, lvl_door1_hi
        ldx level
        +ptrmsg lvl_door2_lo, lvl_door2_hi
        jsr input_word
        ldx level
        lda inlen
        cmp lvl_anslen,x
        bne .wrong
        lda lvl_ans_lo,x
        sta str
        lda lvl_ans_hi,x
        sta str+1
        ldy inlen
        dey
.cmp    lda inbuf,y
        cmp (str),y
        bne .wrong
        dey
        bpl .cmp
        jsr .open
        +msg m_mouth_ok
        rts
.wrong  +msg m_mouth_bad
        rts
.open   jsr cell_index      ; this door becomes floor
        lda #C_FLOOR
        sta DMAP,x
        jmp dg_render

; levers must be pulled iron (6), bone (7), gold (8)
!zone pull_lever
pull_lever
        sta cell
        ldx level
        lda pstate,x
        cmp #3
        bcc +
        +msg m_lever_stuck
        rts
+       lda cell
        sec
        sbc #C_LEVER
        ldx level
        cmp pstate,x
        bne .wrong
        inc pstate,x
        +msg m_clunk
        ldx level
        lda pstate,x
        cmp #3
        beq .open
        rts
.wrong  lda #0
        sta pstate,x
        +msg m_clang
        rts
.open   jsr open_doors
        +msg m_rumble
        rts

; read up to 10 letters, RETURN ends, DEL deletes -> inbuf / inlen
!zone input_word
input_word
        +msg m_prompt
        lda #3
        sta incol
        lda #24
        sta inrow
        lda #10
        sta inmax
; read letters into inbuf (inlen of them) at (incol, inrow), at most inmax; RETURN ends
input_at
        lda #0
        sta inlen
.draw   lda inlen
        clc
        adc incol
        tax
        ldy inrow
        jsr set_cursor
        ldy #0
        lda #'#'
        sta (dst),y
        lda #TITLECOL
        sta (cdst),y
.key    jsr getkey
        cmp #$0d
        beq .done
        cmp #$14
        beq .del
        cmp #$41
        bcc .key
        cmp #$5b
        bcs .key
        ldx inlen
        cpx inmax
        bcs .key
        sec
        sbc #$40            ; PETSCII letter -> screen code
        sta inbuf,x
        ldy #0
        sta (dst),y
        inc inlen
        jmp .draw
.del    ldx inlen
        beq .key
        ldy #0
        lda #32
        sta (dst),y
        dec inlen
        jmp .draw
.done   ldy #0
        lda #32
        sta (dst),y
        rts

; --------------------------------------------------------------------- sprites
sprites_init
        lda #0
        sta $d015
        sta $d010
        sta $d01b
        lda #$0f
        sta $d01c           ; multicolour
        sta $d017           ; double height
        sta $d01d           ; double width
        ldx #7
-       lda spr_pos,x
        sta $d000,x
        dex
        bpl -
        rts

show_monster
        ldx mtype
        lda mon_img,x
        asl
        asl
        clc
        adc #SPR_PTR
        sta MATRIX+$3f8
        adc #1
        sta MATRIX+$3f9
        adc #1
        sta MATRIX+$3fa
        adc #1
        sta MATRIX+$3fb
        lda mon_col,x
        sta $d027
        sta $d028
        sta $d029
        sta $d02a
        lda mon_mc1,x
        sta $d025
        lda mon_mc2,x
        sta $d026
        lda #$0f
        sta $d015
        rts

hide_monster
        lda #0
        sta $d015
        rts

; =====================================================================
;  Tables
; =====================================================================
scr_lo  !for r, 0, 24 { !byte <(VSCR + r*40) }
scr_hi  !for r, 0, 24 { !byte >(VSCR + r*40) }
pw_lo   !byte <10000, <1000, <100, <10, <1
pw_hi   !byte >10000, >1000, >100, >10, >1
bitmask !byte 1, 2, 4, 8, 16, 32, 64, 128
spr_pos !byte 88,106, 136,106, 88,148, 136,148

dirname_lo !byte <s_n, <s_e, <s_s, <s_w
dirname_hi !byte >s_n, >s_e, >s_s, >s_w
lever_lo   !byte <m_lever1, <m_lever2, <m_lever3
lever_hi   !byte >m_lever1, >m_lever2, >m_lever3

; party: ARDEN paladin, MIRA wizard, TORVIK fighter, SELA bard
p_maxhp !byte 28, 16, 34, 20
p_maxsp !byte 9, 12, 0, 8
p_wpn   !byte 7, 3, 9, 5
p_spkey !byte $48, $42, $00, $53      ; H(eal) B(olt) - S(ing)
p_cost  !byte 3, 3, 0, 2
hp_gain !byte 4, 2, 5, 3              ; per level (+0..2 random)
sp_gain !byte 2, 4, 0, 2
mgt_gain !byte 1, 0, 1, 1
pname_lo  !byte <s_n0, <s_n1, <s_n2, <s_n3
pname_hi  !byte >s_n0, >s_n1, >s_n2, >s_n3
pnamep_lo !byte <pnames, <(pnames+8), <(pnames+16), <(pnames+24)
pnamep_hi !byte >pnames, >(pnames+8), >(pnames+16), >(pnames+24)
pclass_lo !byte <s_c0, <s_c1, <s_c2, <s_c3
pclass_hi !byte >s_c0, >s_c1, >s_c2, >s_c3

!source "render.asm"
!source "quest.asm"

low_end
!if low_end > SPRITES { !error "low code overruns sprite data" }

; =====================================================================
;  High memory: combat, towns, character sheet, generated tables, text
; =====================================================================
*= HICODE
!source "combat.asm"
!source "town.asm"
!source "panel.asm"
!source "text.asm"
!source "sheet.asm"
!source "saveload.asm"
!source "create.asm"
!if MUSIC {
!source "music.asm"
!source "build/music.asm"
} else {
!source "nomusic.asm"
}
!source "build/gen.asm"
!source "build/quests_hi.asm"

code_end
!if code_end > $b400 { !error "high code runs into the saved floors at $B400" }

; ---------------------------------------------------------------- data
*= SPRITES
        !binary "build/sprites.bin"
*= GLYPHS
        !binary "build/glyphs.bin"
*= OWMAP
        !binary "build/owmap.bin"
*= $5000
        !binary "build/town0.bin"
        !binary "build/town1.bin"
!source "build/quests.asm"           ; people and quests: tables at $5C00, text at $2C00
!source "build/floors.asm"           ; the 11 floors as they start, in their save slots

