; =====================================================================
;  PEOPLE, SIDE QUESTS AND THE STORY
;
;  Every person (and the hermit in the wilds) has a list of pages,
;  generated from content.py into build/quests.asm.  Talking speaks the
;  first page whose conditions (up to two) all hold and runs its actions.
;
;  conditions: 0 always, 1 quest a is at stage b, 2 at least a runestones,
;              3 runestone bit-mask a taken
;  actions:    1 quest a := stage b, 2 gold += a + 256b, 3 xp += a + 256b,
;              4 member a's weapon >= b, 5 spell upgrade a >= b
;  quest stage: 0 unknown, 1 asked, 2 item found, 3 done
; =====================================================================
qs      = VARS+$d0      ; 16: quest stages (part of the saved game)
qpg     = VARS+$e0
qcnt    = VARS+$e1
qln     = VARS+$e2
qn      = VARS+$e3
qb      = VARS+$e4

; X = person
!zone talk_script
talk_script
        lda npc_pg,x
        sta qpg
        lda npc_np,x
        sta qcnt
.pg     ldx qpg
        lda pg_cb0,x
        sta qb
        ldy pg_ca0,x
        lda pg_ct0,x
        jsr qcond
        bcc .skip
        ldx qpg
        lda pg_cb1,x
        sta qb
        ldy pg_ca1,x
        lda pg_ct1,x
        jsr qcond
        bcs .speak
.skip   inc qpg
        dec qcnt
        bne .pg
        rts
.speak  ldx qpg
        lda pg_l0,x
        sta qln
        lda pg_nl,x
        sta qn
.line   ldx qln
        +ptrmsg ln_lo, ln_hi
        inc qln
        dec qn
        bne .line
        ldx qpg
        lda pg_na,x
        beq .done
        sta qn
        lda pg_a0,x
        sta qln
.act    ldx qln
        jsr qaction
        inc qln
        dec qn
        bne .act
        jmp draw_party
.done   rts

; A = condition type, Y = a, qb = b -> carry set if it holds
!zone qcond
qcond
        cmp #0
        beq .yes
        cmp #1
        bne .runes
        lda qs,y
        cmp qb
        beq .yes
.no     clc
        rts
.runes  cmp #2
        bne .sigil
        sty qb
        jsr count_runes
        cmp qb              ; carry set if count >= a
        rts
.sigil  tya
        and sigils
        beq .no
.yes    sec
        rts

; A = number of runestones taken (X is used)
count_runes
        ldx #0
        lda sigils
-       beq +
        lsr
        bcc -
        inx
        bcs -
+       txa
        rts

; X = action
!zone qaction
qaction
        lda ac_b,x
        sta qb
        ldy ac_a,x
        lda ac_op,x
        cmp #1
        bne .gold
        lda qb              ; quest stage
        sta qs,y
        rts
.gold   cmp #2
        bne .xp
        tya
        clc
        adc gold
        sta gold
        lda qb
        adc gold+1
        sta gold+1
        rts
.xp     cmp #3
        bne .weapon
        sty xpgain
        lda qb
        sta xpgain+1
        ldx #3              ; every living member learns from it
-       lda hp,x
        beq +
        lda xp_l,x
        clc
        adc xpgain
        sta xp_l,x
        lda xp_h,x
        adc xpgain+1
        sta xp_h,x
+       dex
        bpl -
        jmp level_ups
.weapon cmp #4
        bne .bonus
        lda qb
        cmp wpn,y
        bcc .r
        sta wpn,y
.r      rts
.bonus  lda qb              ; spell upgrade
        cmp bonus,y
        bcc .r
        sta bonus,y
        rts

; stepping onto a quest item in a dungeon
pick_quest
        jsr clear_here
        ldx level
        ldy lvl_qid,x
        lda qs,y
        cmp #2
        bcs +
        lda #2
        sta qs,y
+       ldx level
        +ptrmsg lvl_qt1_lo, lvl_qt1_hi
        ldx level
        +ptrmsg lvl_qt2_lo, lvl_qt2_hi
        rts

; the story so far, before the first step
!zone intro
intro
        jsr clear_view
        +print VX+8,1,s_title,TITLECOL
        ldx #0
.l      stx qn
        lda intro_lo,x
        sta str
        lda intro_hi,x
        sta str+1
        lda #TEXTCOL
        sta textcol
        txa
        clc
        adc #3
        tay
        ldx #VX+1
        jsr print_at
        ldx qn
        inx
        cpx #INTRO_N
        bne .l
        +msg m_presskey
        jmp getkey

; Q: every quest heard of, and where it stands
!zone quest_log
quest_log
        jsr clear_view
        +print VX+1,1,s_qlog,TITLECOL
        lda #3
        sta qln             ; row
        ldx #0
.l      stx qcnt
        lda qs,x
        beq .next
        lda qname_lo,x
        sta str
        lda qname_hi,x
        sta str+1
        lda #TITLECOL
        sta textcol
        ldx #VX+1
        ldy qln
        jsr print_at
        inc qln
        ldx qcnt
        lda qhint_lo,x      ; stage 1: where to go
        sta str
        lda qhint_hi,x
        sta str+1
        lda #TEXTCOL
        sta textcol
        lda qs,x
        cmp #2
        bcc .say
        bne .done
        lda #<s_qfound
        sta str
        lda #>s_qfound
        sta str+1
        jmp .say
.done   lda #<s_qdone
        sta str
        lda #>s_qdone
        sta str+1
        lda #HEADCOL
        sta textcol
.say    ldx #VX+2
        ldy qln
        jsr print_at
        inc qln
.next   ldx qcnt
        inx
        cpx #NUM_QUESTS
        bne .l
        lda qln
        cmp #3
        bne +
        +print VX+1,3,s_qempty,TEXTCOL
+       +msg m_presskey
        jsr getkey
        jmp redraw_view

s_qlog   !scr "quests" : !byte $ff
s_qfound !scr "found! take it back." : !byte $ff
s_qdone  !scr "done." : !byte $ff
s_qempty !scr "none yet. ask townsfolk." : !byte $ff
