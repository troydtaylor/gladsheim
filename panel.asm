; =====================================================================
;  SIDE PANEL (cells 28-39, full-size font, 12 characters wide)
;
;   0  title               10  GOLD   12345
;   1  ----------           12  location / foes
;   2  ARDEN   L  1         13  X:30 Y:34  / foe hp
;   3  HP  28   SP  9       14  FACING WEST / foe hp
;   4-9 the other three     16-19 the main keys for the current mode
; =====================================================================
PW      = 12            ; panel width

draw_panel
        +print PC+1,0,s_title,TITLECOL
        rts

; party: two rows each, from row 2
!zone draw_party
draw_party
        ldx #0
.l      stx dpc
        txa                 ; row = 2 + 2 * member
        asl
        clc
        adc #2
        sta n3row
        lda #TEXTCOL        ; name (red if dead)
        ldy hp,x
        bne +
        lda #DEADCOL
+       sta textcol
        lda pnamep_lo,x
        sta str
        lda pnamep_hi,x
        sta str+1
        ldx #PC
        ldy n3row
        jsr print_at
        lda #HEADCOL
        sta textcol
        lda #<s_l1
        sta str
        lda #>s_l1
        sta str+1
        ldx #PC+8
        ldy n3row
        jsr print_at
        lda #TEXTCOL
        sta textcol
        lda #2
        sta ndig
        ldx dpc
        lda lvl,x
        ldx #PC+10
        ldy n3row
        jsr pu8
        inc n3row           ; --- second row: HP and SP
        lda #HEADCOL
        sta textcol
        lda #<s_hp
        sta str
        lda #>s_hp
        sta str+1
        ldx #PC
        ldy n3row
        jsr print_at
        lda #TEXTCOL
        sta textcol
        ldx dpc
        lda hp,x
        bne .alive
        lda #DEADCOL
        sta textcol
        lda #<s_dead3
        sta str
        lda #>s_dead3
        sta str+1
        ldx #PC+2
        ldy n3row
        jsr print_at
        jmp .sp
.alive  lda #3
        sta ndig
        lda hp,x
        ldx #PC+2
        ldy n3row
        jsr pu8
.sp     ldx dpc
        lda maxsp,x
        bne .hassp
        lda #<s_blank5      ; the fighter has no spell points
        sta str
        lda #>s_blank5
        sta str+1
        ldx #PC+7
        ldy n3row
        jsr print_at
        jmp .next
.hassp  lda #HEADCOL
        sta textcol
        lda #<s_sp
        sta str
        lda #>s_sp
        sta str+1
        ldx #PC+7
        ldy n3row
        jsr print_at
        lda #TEXTCOL
        sta textcol
        lda #2
        sta ndig
        ldx dpc
        lda sp,x
        ldx #PC+10
        ldy n3row
        jsr pu8
.next   ldx dpc
        inx
        cpx #4
        beq print_gold
        jmp .l

print_gold
        +print PC,10,s_gold,HEADCOL
        lda gold
        sta n16
        lda gold+1
        sta n16+1
        lda #5
        sta ndig
        lda #TITLECOL
        sta textcol
        ldx #PC+7
        ldy #10
        jmp print_u

; print the place name A/X (lo/hi) on row 12, padded to the panel width
place_name
        pha
        txa
        pha
        +print PC,12,s_blank12,TEXTCOL
        pla
        sta str+1
        pla
        sta str
        ldx #PC
        ldy #12
        jmp print_at

; X:nn Y:nn on row 13 (A = x, X = y)
coords
        pha
        txa
        pha
        +print PC,13,s_xy,TEXTCOL
        pla
        ldx #PC+7
        ldy #13
        jsr print_num2
        pla
        ldx #PC+2
        ldy #13
        jmp print_num2

; the four key lines (rows 16-19) for key set A (0 wilds, 1 town, 2 dungeon, 3 combat, 4 shop)
!zone panel_keys
panel_keys
        asl
        asl                 ; A = set * 4
        sta pk
        lda #16
        sta pkrow
.l      ldx pk
        lda keys_lo,x
        sta str
        lda keys_hi,x
        sta str+1
        lda #TEXTCOL
        sta textcol
        ldx #PC
        ldy pkrow
        jsr print_at
        inc pk
        inc pkrow
        lda pkrow
        cmp #20
        bne .l
        rts

; overworld or town status
!zone ow_status
ow_status
        lda mode
        cmp #2
        bne .wild
        ldx town
        lda town_short_lo,x
        pha
        lda town_short_hi,x
        tax
        pla
        jsr place_name
        jmp .xy
.wild   lda #<s_wilds
        ldx #>s_wilds
        jsr place_name
.xy     lda px
        ldx py
        jsr coords
        +print PC,14,s_blank12,TEXTCOL
        lda mode
        lsr                 ; 0 wilds -> keys 0, 2 town -> keys 1
        jmp panel_keys

dg_status
        ldx level
        lda lvl_short_lo,x
        pha
        lda lvl_short_hi,x
        tax
        pla
        jsr place_name
        lda dpx
        ldx dpy
        jsr coords
        +print PC,14,s_facing,TEXTCOL
        ldx ddir
        lda dirname_lo,x
        sta str
        lda dirname_hi,x
        sta str+1
        ldx #PC+7
        ldy #14
        jsr print_at
        lda #2
        jmp panel_keys

; combat: the foes' name and hit points in rows 12-14
!zone draw_foes
draw_foes
        ldx mtype
        lda mplur_lo,x
        sta str
        lda mplur_hi,x
        sta str+1
        lda nmon
        cmp #1
        bne +
        lda mname_lo,x
        sta str
        lda mname_hi,x
        sta str+1
+       lda str
        ldx str+1
        jsr place_name
        lda #DEADCOL        ; the name is printed in red
        ldx #PW-1
-       sta VTC+12*40+PC,x
        dex
        bpl -
        +print PC,13,s_blank12,TEXTCOL
        +print PC,14,s_blank12,TEXTCOL
        lda #3
        sta ndig
        lda #0
        sta fcur
.l      ldx fcur
        cpx nmon
        bcs .d
        ldy foe_row,x
        lda foe_col,x
        tax
        lda #TEXTCOL
        sta textcol
        stx n3col
        sty n3row
        ldy fcur
        lda mhp,y
        beq .dead
        ldy n3row
        jsr pu8
        jmp .n
.dead   lda #DEADCOL
        sta textcol
        lda #<s_dead3
        sta str
        lda #>s_dead3
        sta str+1
        ldx n3col
        ldy n3row
        jsr print_at
.n      inc fcur
        jmp .l
.d      rts

foe_col !byte PC, PC+4, PC+8, PC
foe_row !byte 13, 13, 13, 14

; key sets: 4 lines each (wilds, town, dungeon, combat, shop)
keys_lo !byte <k00,<k01,<k02,<kmore, <k00,<k11,<k12,<kmore, <k20,<k21,<k22,<kmore
        !byte <k30,<k31,<k32,<k33,   <k40,<k41,<k42,<kbl
keys_hi !byte >k00,>k01,>k02,>kmore, >k00,>k11,>k12,>kmore, >k20,>k21,>k22,>kmore
        !byte >k30,>k31,>k32,>k33,   >k40,>k41,>k42,>kbl
k00 !scr "wasd move   " : !byte $ff
k01 !scr "e enter     " : !byte $ff
k02 !scr "c sheet     " : !byte $ff
k11 !scr "walk into   " : !byte $ff
k12 !scr "folk, shops " : !byte $ff
k20 !scr "w forward   " : !byte $ff
k21 !scr "q/d turn    " : !byte $ff
k22 !scr "s back e use" : !byte $ff
k30 !scr "a attack    " : !byte $ff
k31 !scr "p parry     " : !byte $ff
k32 !scr "h/b/s spell " : !byte $ff
k33 !scr "r run       " : !byte $ff
k40 !scr "a-d buy     " : !byte $ff
k41 !scr "1-4 for who " : !byte $ff
k42 !scr "x leave shop" : !byte $ff
kmore !scr "? more keys " : !byte $ff
kbl !scr "            " : !byte $ff

s_hp      !scr "hp" : !byte $ff
s_l1      !scr "l" : !byte $ff
s_sp      !scr "sp" : !byte $ff
s_blank5  !scr "     " : !byte $ff
s_blank12 !scr "            " : !byte $ff

; ? : every key, in the view
!zone help_screen
help_screen
        jsr clear_view
        ldx #0
.l      stx member
        lda help_lo,x
        sta str
        lda help_hi,x
        sta str+1
        lda help_col,x
        sta textcol
        txa
        clc
        adc #1
        tay
        ldx #VX+1
        jsr print_at
        ldx member
        inx
        cpx #HELP_N
        bne .l
        +msg m_presskey
        jsr getkey
        jmp redraw_view

HELP_N = 18
help_lo  !byte <h0,<h1,<h2,<h3,<h4,<h5,<h17,<h6,<h7,<h8,<h9,<h10,<h11,<h12,<h13,<h14,<h15,<h16
help_hi  !byte >h0,>h1,>h2,>h3,>h4,>h5,>h17,>h6,>h7,>h8,>h9,>h10,>h11,>h12,>h13,>h14,>h15,>h16
help_col !byte TITLECOL,TEXTCOL,TEXTCOL,TEXTCOL,TEXTCOL,TEXTCOL,TEXTCOL,HEADCOL,TEXTCOL,TEXTCOL,TEXTCOL
         !byte HEADCOL,TEXTCOL,TEXTCOL,TEXTCOL,HEADCOL,TEXTCOL,TEXTCOL
h0  !scr "keys" : !byte $ff
h1  !scr "wasd/cursor  move" : !byte $ff
h2  !scr "e   enter, use, climb" : !byte $ff
h3  !scr "c   character sheet" : !byte $ff
h4  !scr "h   paladin heals (1-4)" : !byte $ff
h5  !scr "v/l save/load (wilds)" : !byte $ff
h6  !scr "in dungeons" : !byte $ff
h7  !scr "w   step forward" : !byte $ff
h8  !scr "q/d turn left/right" : !byte $ff
h9  !scr "s   turn around" : !byte $ff
h10 !scr "in combat, each hero" : !byte $ff
h11 !scr "a attack   p parry" : !byte $ff
h12 !scr "h heal  b bolt  s sing" : !byte $ff
h13 !scr "r   try to run" : !byte $ff
h14 !scr "in towns" : !byte $ff
h15 !scr "walk into folk to talk," : !byte $ff
h16 !scr "into counters to shop" : !byte $ff
h17 !scr "j   journal (quests)" : !byte $ff
