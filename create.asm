; =====================================================================
;  PARTY CREATION, NAMES, HEAL TARGETS
;  Four heroes, one per class (the classes' spells belong to their
;  slots): the player names each one and rolls hit points, spell points
;  and might until happy.  Names live in the game state, so saves keep them.
; =====================================================================
pnames  = VARS+$e0      ; 4 x 8: name padded to 7 with spaces, then $ff

; X = member: the default name back into the buffer
!zone default_name
default_name
        lda dname_lo,x
        sta src
        lda dname_hi,x
        sta src+1
        txa
        asl
        asl
        asl
        tax
        ldy #0
-       lda (src),y
        sta pnames,x
        inx
        iny
        cpy #8
        bne -
        rts

; after loading an older save: any name that isn't letters gets its default
!zone check_names
check_names
        ldx #0
.m      stx crm
        txa
        asl
        asl
        asl
        tay
        lda pnames,y        ; must start with a letter
        beq .bad
        cmp #27
        bcs .bad
        ldx #7
.c      lda pnames,y
        cmp #32
        beq .ok
        cmp #27
        bcs .bad
        cmp #1
        bcc .bad
.ok     iny
        dex
        bne .c
        lda pnames,y
        cmp #$ff
        beq .next
.bad    ldx crm
        jsr default_name
.next   ldx crm
        inx
        cpx #4
        bne .m
        rts

; the four heroes, one screen each
!zone create_party
create_party
        ldx #0
.m      stx crm
        jsr clear_view
        +print VX+1,1,s_cr_title,TITLECOL
        +print VX+1,3,s_cr_hero,HEADCOL
        lda #1
        sta ndig
        lda crm
        clc
        adc #1
        ldx #VX+6
        ldy #3
        jsr pu8
        ldx crm
        lda pclass_lo,x
        sta str
        lda pclass_hi,x
        sta str+1
        lda #TITLECOL
        sta textcol
        ldx #VX+14
        ldy #3
        jsr print_at
        ldx crm
        lda cdesc1_lo,x
        sta str
        lda cdesc1_hi,x
        sta str+1
        lda #TEXTCOL
        sta textcol
        ldx #VX+1
        ldy #5
        jsr print_at
        ldx crm
        lda cdesc2_lo,x
        sta str
        lda cdesc2_hi,x
        sta str+1
        ldx #VX+1
        ldy #6
        jsr print_at
        +print VX+1,9,s_cr_name,HEADCOL
        +print VX+1,11,s_cr_keep,TEXTCOL
        lda #VX+7           ; type the name
        sta incol
        lda #9
        sta inrow
        lda #7
        sta inmax
        jsr input_at
        lda inlen
        beq .roll           ; RETURN alone: keep the name
        lda crm
        asl
        asl
        asl
        tax
        ldy #0
-       lda #32             ; letters, then spaces to 7
        cpy inlen
        bcs +
        lda inbuf,y
+       sta pnames,x
        inx
        iny
        cpy #7
        bne -
.roll   ldx crm             ; hit points, spell points, might
        lda #5
        jsr rnd_n
        ldx crm
        clc
        adc p_maxhp,x
        sta maxhp,x
        sta hp,x
        lda p_maxsp,x
        beq .nosp
        lda #4
        jsr rnd_n
        ldx crm
        clc
        adc p_maxsp,x
.nosp   sta maxsp,x
        sta sp,x
        lda #2
        jsr rnd_n
        ldx crm
        sta mgt,x
        jsr draw_party
        +print VX+1,13,s_cr_stats,HEADCOL
        lda #TEXTCOL
        sta textcol
        lda #3
        sta ndig
        ldx crm
        lda maxhp,x
        ldx #VX+4
        ldy #13
        jsr pu8
        lda #2
        sta ndig
        ldx crm
        lda maxsp,x
        ldx #VX+11
        ldy #13
        jsr pu8
        lda #1
        sta ndig
        ldx crm
        lda mgt,x
        ldx #VX+20
        ldy #13
        jsr pu8
        +print VX+1,15,s_cr_roll,TITLECOL
.k      jsr getkey
        cmp #$52            ; R
        bne +
        jmp .roll
+       cmp #$0d
        bne .k
        ldx crm
        inx
        cpx #4
        beq +
        jmp .m
+       rts

; Arden's heal: whom?  htarget = member 0-3, or $ff for the most wounded (RETURN)
!zone pick_heal
pick_heal
        +msg m_healwho
.k      jsr getkey
        cmp #$0d
        beq .auto
        sec
        sbc #$31
        cmp #4
        bcs .k
        tax
        lda hp,x            ; the fallen need the temple
        beq .k
        stx htarget
        rts
.auto   lda #$ff
        sta htarget
        rts

dname_lo !byte <s_np0, <s_np1, <s_np2, <s_np3
dname_hi !byte >s_np0, >s_np1, >s_np2, >s_np3
cdesc1_lo !byte <s_cd10, <s_cd11, <s_cd12, <s_cd13
cdesc1_hi !byte >s_cd10, >s_cd11, >s_cd12, >s_cd13
cdesc2_lo !byte <s_cd20, <s_cd21, <s_cd22, <s_cd23
cdesc2_hi !byte >s_cd20, >s_cd21, >s_cd22, >s_cd23
s_cr_title !scr "create your party" : !byte $ff
s_cr_hero  !scr "hero   of 4:" : !byte $ff
s_cr_name  !scr "name:" : !byte $ff
s_cr_keep  !scr "(return alone keeps it)" : !byte $ff
s_cr_stats !scr "hp     sp    might" : !byte $ff
s_cr_roll  !scr "(r)eroll  (return) keep" : !byte $ff
s_cd10 !scr "heals one friend at a" : !byte $ff
s_cd20 !scr "time with holy light." : !byte $ff
s_cd11 !scr "hurls flame bolts that" : !byte $ff
s_cd21 !scr "no armour can stop." : !byte $ff
s_cd12 !scr "the strongest arm in the" : !byte $ff
s_cd22 !scr "party. no spells." : !byte $ff
s_cd13 !scr "sings to heal the whole" : !byte $ff
s_cd23 !scr "party at once." : !byte $ff
m_healwho !scr "heal who? 1-4 (return: most hurt)" : !byte $ff
