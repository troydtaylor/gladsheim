; =====================================================================
;  VAULTS OF KESH -- engine v4
;  Ultima II-style overworld and towns, Bard's Tale-style 3D dungeons,
;  sprite monster portraits, party combat with experience and levels,
;  shops, puzzles, and a world of six dungeons. Keyboard only.
;
;  Build:  ./build.sh   (python3 gen.py; acme main.asm; d64)
;
;  Memory map
;    $0400        screen            $07F8  sprite pointers
;    $0801-$1FFF  BASIC stub, engine core
;    $2000-$29FF  monster portraits (10 x 4 sprites)
;    $2A00-$37FF  engine text, character sheet
;    $3800-$3FFF  charset
;    $4000-$4FFF  64x64 overworld
;    $5000-$57FF  town maps (2 x 32x32)
;    $5800-$58FF  game variables
;    $5A00-$5AFF  working copy of the current dungeon floor
;    $6000-$9FFF  combat, towns, generated tables, floors (pristine)
;    $C000-$C3FF  3D view buffers
;    $C400-$CEFF  saved state of all 11 dungeon floors
; =====================================================================
!cpu 6502
!to "build/proto.prg", cbm
!symbollist "build/proto.sym"

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
inbuf   = VARS+$40      ; 12
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
sigils  = VARS+$a8      ; bit per sigil
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
SCREEN  = $0400
COLRAM  = $d800
SPRITES = $2000
SPR_PTR = SPRITES / 64
CHARSET = $3800
OWMAP   = $4000
DMAP    = $5a00
HICODE  = $6000

FRAMECOL = 6        ; hires colours must be 0-7 in multicolour text mode
TITLECOL = 7
HEADCOL  = 3
TEXTCOL  = 1
DEADCOL  = 2
PC       = 24       ; side panel column

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
        lda #$1e            ; screen $0400, charset $3800
        sta $d018
        lda $d016
        ora #$10            ; multicolour text mode
        sta $d016
        jsr sprites_init
        jsr new_game
        jsr clear_screen
        jsr draw_frame
        jsr draw_panel
        jsr draw_party
        lda #START_X
        sta px
        lda #START_Y
        sta py
        lda #0
        sta mode
        jsr ow_colors
        jsr ow_draw
        jsr ow_status
        +msg m_welcome1
        +msg m_welcome2
        +msg m_welcome3

main
        jsr getkey
        ldx mode
        cpx #1
        beq +
        jsr ow_key
        jmp main
+       jsr dg_key
        jmp main

; wait for a key; stir the raster position into the RNG (real hardware)
getkey
        jsr GETIN
        beq getkey
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
        ldx #15
.ps     sta pstate,x
        dex
        bpl .ps
        lda #60             ; a little starting coin for the shops
        sta gold
        lda #$a5
        sta seed
        lda #$3c
        sta seed+1
        ldx #0              ; every floor starts from its pristine copy
.lv     stx tmp
        lda lvl_src_lo,x
        sta src
        lda lvl_src_hi,x
        sta src+1
        lda lvl_save_hi,x
        sta dst+1
        lda #0
        sta dst
        ldy #0
.cp     lda (src),y
        sta (dst),y
        iny
        bne .cp
        ldx tmp
        inx
        cpx #NUM_LEVELS
        bne .lv
        rts

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
!zone clear_screen
clear_screen
        ldx #0
.l      lda #32
        sta SCREEN,x
        sta SCREEN+$100,x
        sta SCREEN+$200,x
        sta SCREEN+$2e8,x
        lda #TEXTCOL
        sta COLRAM,x
        sta COLRAM+$100,x
        sta COLRAM+$200,x
        sta COLRAM+$2e8,x
        inx
        bne .l
        rts

!zone draw_frame
draw_frame
        ldx #21
.h      lda #CH_HLINE
        sta SCREEN+1,x
        sta SCREEN+19*40+1,x
        lda #FRAMECOL
        sta COLRAM+1,x
        sta COLRAM+19*40+1,x
        dex
        bpl .h
        ldx #1
.v      lda scr_lo,x
        sta dst
        sta cdst
        lda scr_hi,x
        sta dst+1
        clc
        adc #$d4
        sta cdst+1
        lda #CH_VLINE
        ldy #0
        sta (dst),y
        ldy #23
        sta (dst),y
        lda #FRAMECOL
        sta (cdst),y
        ldy #0
        sta (cdst),y
        inx
        cpx #19
        bne .v
        lda #CH_TL
        sta SCREEN
        lda #CH_TR
        sta SCREEN+23
        lda #CH_BL
        sta SCREEN+19*40
        lda #CH_BR
        sta SCREEN+19*40+23
        lda #FRAMECOL
        sta COLRAM
        sta COLRAM+23
        sta COLRAM+19*40
        sta COLRAM+19*40+23
        ldx #15
.u      lda #CH_HLINE
        sta SCREEN+2*40+PC,x
        lda #FRAMECOL
        sta COLRAM+2*40+PC,x
        dex
        bpl .u
        rts

draw_panel
        +print PC+1,1,s_title,TITLECOL
        +print PC,4,s_party,HEADCOL
        +print PC,9,s_gold,HEADCOL
        +print PC,15,s_keys,HEADCOL
        rts

; party rows 5-8: name, HP (3), SP (2), level (2); then gold
!zone draw_party
draw_party
        ldx #0
.l      stx dpc
        lda #TEXTCOL
        ldy hp,x
        bne +
        lda #DEADCOL
+       sta textcol
        lda pnamep_lo,x
        sta str
        lda pnamep_hi,x
        sta str+1
        jsr .row
        ldx #PC
        jsr print_at
        ldx dpc
        lda hp,x
        bne .alive
        lda #<s_dead3
        sta str
        lda #>s_dead3
        sta str+1
        jsr .row
        ldx #PC+7
        jsr print_at
        jmp .sp
.alive  lda #3
        sta ndig
        jsr .row
        lda hp,x
        ldx #PC+7
        jsr pu8
.sp     ldx dpc
        lda maxsp,x
        bne .hassp
        lda #<s_2sp
        sta str
        lda #>s_2sp
        sta str+1
        jsr .row
        ldx #PC+11
        jsr print_at
        jmp .lv
.hassp  jsr .row
        lda sp,x
        ldx #PC+11
        jsr print_num2
.lv     lda #2
        sta ndig
        ldx dpc
        jsr .row
        lda lvl,x
        ldx #PC+14
        jsr pu8
        ldx dpc
        inx
        cpx #4
        beq +
        jmp .l
+       jmp print_gold
.row    lda dpc             ; Y = 5 + member, X = member
        clc
        adc #5
        tay
        ldx dpc
        rts

print_gold
        lda gold
        sta n16
        lda gold+1
        sta n16+1
        lda #5
        sta ndig
        lda #TITLECOL
        sta textcol
        ldx #PC+11
        ldy #9
        jmp print_u

; set dst/cdst to screen position X=col, Y=row
set_cursor
        txa
        clc
        adc scr_lo,y
        sta dst
        sta cdst
        lda scr_hi,y
        adc #0
        sta dst+1
        clc
        adc #$d4
        sta cdst+1
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
.l      lda SCREEN+21*40+1,x
        sta SCREEN+20*40+1,x
        lda SCREEN+22*40+1,x
        sta SCREEN+21*40+1,x
        lda SCREEN+23*40+1,x
        sta SCREEN+22*40+1,x
        lda SCREEN+24*40+1,x
        sta SCREEN+23*40+1,x
        lda #32
        sta SCREEN+24*40+1,x
        lda #TEXTCOL
        sta COLRAM+20*40+1,x
        sta COLRAM+21*40+1,x
        sta COLRAM+22*40+1,x
        sta COLRAM+23*40+1,x
        dex
        bpl .l
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

mb_name                     ; X = party member
        lda pname_lo,x
        pha
        lda pname_hi,x
        tax
        pla
        jmp mb_str

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

; wait until the raster is in the lower border (line >= 256)
wait_vb
-       bit $d011
        bpl -
        rts

; =====================================================================
;  OVERWORLD (and town walking, mode 2)
; =====================================================================
ow_colors
        lda #9              ; brown
        sta $d022
        lda #15             ; light grey
        sta $d023
        rts

!zone ow_status
ow_status
        +print PC,10,s_loc,HEADCOL
        lda mode
        cmp #2
        bne +
        ldx town
        lda town_name_lo,x
        sta str
        lda town_name_hi,x
        sta str+1
        lda #TEXTCOL
        sta textcol
        ldx #PC
        ldy #11
        jsr print_at
        jmp ++
+       +print PC,11,s_wilds,TEXTCOL
++      +print PC,12,s_xy,TEXTCOL
        +printnum PC+2,12,px
        +printnum PC+7,12,py
        +print PC,13,s_blank,TEXTCOL
        lda mode
        cmp #2
        beq .tk
        +print PC,16,s_ow_k1,TEXTCOL
        +print PC,17,s_ow_k2,TEXTCOL
        +print PC,18,s_ow_k3,TEXTCOL
        +print PC,19,s_ow_k4,TEXTCOL
        rts
.tk     +print PC,16,s_ow_k1,TEXTCOL
        +print PC,17,s_tw_k2,TEXTCOL
        +print PC,18,s_ow_k3,TEXTCOL
        +print PC,19,s_tw_k4,TEXTCOL
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

; 11 x 9 tiles, player in the middle
!zone ow_draw
ow_draw
        lda #0
        sta ry
.row    lda #0
        sta rx
.col    lda px
        clc
        adc rx
        sec
        sbc #5
        sta tx
        lda py
        clc
        adc ry
        sec
        sbc #4
        sta ty
        jsr get_tile
        ldx rx
        cpx #5
        bne +
        ldx ry
        cpx #4
        bne +
        lda #T_PLAYER
+       jsr draw_tile
        inc rx
        lda rx
        cmp #11
        bne .col
        inc ry
        lda ry
        cmp #9
        bne .row
        rts

; draw tile A as 2x2 chars at viewport tile (rx,ry)
draw_tile
        tax
        lda tile_char,x
        sta ch
        lda tile_color,x
        sta col
        lda ry
        asl
        tay
        iny                 ; screen row = 1 + 2*ry
        lda rx
        asl
        tax
        inx                 ; screen col = 1 + 2*rx
        jsr set_cursor
        ldy #0
        lda ch
        sta (dst),y
        lda col
        sta (cdst),y
        iny
        lda ch
        clc
        adc #1
        sta (dst),y
        lda col
        sta (cdst),y
        ldy #40
        lda ch
        clc
        adc #2
        sta (dst),y
        lda col
        sta (cdst),y
        iny
        lda ch
        clc
        adc #3
        sta (dst),y
        lda col
        sta (cdst),y
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
        jsr most_wounded
        lda tmp2            ; any damage at all?
        bne +
        +msg m_allwell
        rts
+       lda sp
        sec
        sbc #3
        sta sp
        jsr heal_target
        jmp draw_party
.cant   +msg m_cantheal
        rts

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
        lda dg_need,x       ; sealed by sigils?
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
        sta cdst
        lda scr_hi,x
        sta dst+1
        clc
        adc #$d4
        sta cdst+1
        ldy #22
.c      lda #32
        sta (dst),y
        lda #0
        sta (cdst),y
        dey
        bne .c
        inx
        cpx #19
        bne .r
        rts

dg_status
        +print PC,10,s_loc,HEADCOL
        ldx level
        lda lvl_name_lo,x
        sta str
        lda lvl_name_hi,x
        sta str+1
        lda #TEXTCOL
        sta textcol
        ldx #PC
        ldy #11
        jsr print_at
        +print PC,12,s_xy,TEXTCOL
        +printnum PC+2,12,dpx
        +printnum PC+7,12,dpy
        +print PC,13,s_facing,TEXTCOL
        ldx ddir
        lda dirname_lo,x
        sta str
        lda dirname_hi,x
        sta str+1
        ldx #PC+7
        ldy #13
        jsr print_at
        +print PC,16,s_dg_k1,TEXTCOL
        +print PC,17,s_dg_k2,TEXTCOL
        +print PC,18,s_dg_k3,TEXTCOL
        +print PC,19,s_dg_k4,TEXTCOL
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
        rts

; ---------------------------------------------------------------------
;  3D view: clear buffer to ceiling/floor, then paint wall pieces
;  back-to-front. Secret walls draw as walls; doors use the door pieces.
; ---------------------------------------------------------------------
!zone dg_render
dg_render
        ldx #161
.clr    lda #D_CEIL
        sta BUF,x
        lda #D_FLOOR
        sta BUF+162,x
        lda #8
        sta CBUF,x
        sta CBUF+162,x
        dex
        cpx #$ff
        bne .clr
        ldx #WIN-1          ; floor seams at each depth boundary
.seam   lda #D_FLOORLN
        sta BUF+15*WIN,x
        sta BUF+13*WIN,x
        sta BUF+11*WIN,x
        dex
        bpl .seam

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

        ; copy 18x18 buffer to screen row 1, col 3
        jsr wait_vb
        lda #<BUF
        sta src
        lda #>BUF
        sta src+1
        lda #<CBUF
        sta csrc
        lda #>CBUF
        sta csrc+1
        lda #<(SCREEN+43)
        sta dst
        lda #>(SCREEN+43)
        sta dst+1
        lda #<(COLRAM+43)
        sta cdst
        lda #>(COLRAM+43)
        sta cdst+1
        ldx #WIN
.b      ldy #WIN-1
.bc     lda (src),y
        sta (dst),y
        lda (csrc),y
        sta (cdst),y
        dey
        bpl .bc
        lda src
        clc
        adc #WIN
        sta src
        bcc +
        inc src+1
+       lda csrc
        clc
        adc #WIN
        sta csrc
        bcc +
        inc csrc+1
+       lda dst
        clc
        adc #40
        sta dst
        bcc +
        inc dst+1
+       lda cdst
        clc
        adc #40
        sta cdst
        bcc +
        inc cdst+1
+       dex
        bne .b
        rts

; run list at (dl): lo,hi,len,char,colour ... terminated by hi = 0
!zone drawlist
drawlist
        ldy #0
.n      lda (dl),y
        sta dst
        sta cdst
        iny
        lda (dl),y
        beq .done
        sta dst+1
        clc
        adc #>(CBUF-BUF)
        sta cdst+1
        iny
        lda (dl),y
        sta cnt
        iny
        lda (dl),y
        sta ch
        iny
        lda (dl),y
        sta col
        iny
        sty ysave
        ldy cnt
        dey
.f      lda ch
        sta (dst),y
        lda col
        sta (cdst),y
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
        cmp #$41            ; A
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
        lda #0
        sta inlen
.draw   lda inlen
        clc
        adc #3
        tax
        ldy #24
        jsr set_cursor
        ldy #0
        lda #CH_SOLID
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
        cpx #10
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
        sta $07f8
        adc #1
        sta $07f9
        adc #1
        sta $07fa
        adc #1
        sta $07fb
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
scr_lo  !for r, 0, 24 { !byte <(SCREEN + r*40) }
scr_hi  !for r, 0, 24 { !byte >(SCREEN + r*40) }
pw_lo   !byte <10000, <1000, <100, <10, <1
pw_hi   !byte >10000, >1000, >100, >10, >1
bitmask !byte 1, 2, 4, 8, 16, 32, 64, 128
spr_pos !byte 72,106, 120,106, 72,148, 120,148

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
pnamep_lo !byte <s_np0, <s_np1, <s_np2, <s_np3
pnamep_hi !byte >s_np0, >s_np1, >s_np2, >s_np3
pclass_lo !byte <s_c0, <s_c1, <s_c2, <s_c3
pclass_hi !byte >s_c0, >s_c1, >s_c2, >s_c3

low_end
!if low_end > SPRITES { !error "low code overruns sprite data" }

; =====================================================================
;  High memory: combat, towns, character sheet, generated tables, text
; =====================================================================
*= HICODE
!source "combat.asm"
!source "town.asm"
!source "saveload.asm"
!source "build/gen.asm"

code_end
!if code_end > $a000 { !error "high code must stay below $A000 (BASIC ROM)" }

; ---------------------------------------------------------------- data
*= SPRITES
        !binary "build/sprites.bin"
; the gap between the monster portraits and the charset holds text and the sheet
!source "text.asm"
!source "sheet.asm"
mid_end
!if mid_end > CHARSET { !error "text overruns the charset" }
*= CHARSET
        !binary "build/charset.bin"
*= OWMAP
        !binary "build/owmap.bin"
*= $5000
        !binary "build/town0.bin"
        !binary "build/town1.bin"
