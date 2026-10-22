; =====================================================================
;  COMBAT
;  in: mtype, nmon.  out: cres = 0 won, 1 fled.  A wiped party restarts.
;  Party damage: 1 + rnd(weapon) + might.  Hit chance grows with level.
;  Spells scale with the caster's level and with tomes bought in town.
; =====================================================================
!zone combat
combat
        tsx
        stx csp
        lda #1
        sta incombat
        ldx mtype
        lda mon_hp,x
        ldx #3
-       sta mhp,x
        dex
        bpl -
        ldx nmon            ; clear unused slots
        lda #0
-       cpx #4
        beq +
        sta mhp,x
        inx
        bne -
+       jsr show_monster
        jsr draw_foes
        lda #3
        jsr panel_keys
        jsr mb_start
        lda nmon
        cmp #1
        bne .many
        jsr mb_art
        jsr mb_mon
        +mbs s_attacks
        jmp .ann
.many   lda nmon
        jsr mb_num
        lda #32
        jsr mb_char
        jsr mb_mons
        +mbs s_attack
.ann    jsr cmsg

.round  ldx #0              ; ---- each living member picks an action
.choose stx cur
        lda hp,x
        bne .prompt
        lda #3
        sta action,x
        jmp .nextc
.prompt ldx cur
        +ptrmsg prompt_lo, prompt_hi
.key    jsr getkey
        ldx cur
        cmp #$41            ; A
        bne +
        lda #0
        sta action,x
        jmp .nextc
+       cmp #$50            ; P
        bne +
        lda #1
        sta action,x
        jmp .nextc
+       cmp #$52            ; R
        bne +
        jmp .run
+       cmp p_spkey,x
        bne .key
        lda sp,x
        cmp p_cost,x
        bcs +
        +msg m_nosp
        jmp .prompt
+       lda #2
        sta action,x
.nextc  ldx cur
        inx
        cpx #4
        bne .choose

        ldx #0              ; ---- party acts
.act    stx cur
        lda hp,x
        bne +
        jmp .nexta
+       lda action,x
        beq .attack
        cmp #2
        bne +
        jmp .cast
+       jmp .nexta
.attack jsr first_foe
        stx target
        ldx cur             ; hit chance 175 + 3 per level
        lda lvl,x
        asl
        adc lvl,x
        adc #175
        sta tmp2
        jsr rnd
        cmp tmp2
        bcs .miss
        ldx cur
        lda wpn,x
        jsr rnd_n
        ldx cur
        sec                 ; 1 + rnd(weapon) + might - monster armour (min 1)
        adc mgt,x
        ldx mtype
        sec
        sbc mon_def,x
        beq +
        bcs ++
+       lda #1
++      sta dmg
        jsr mb_start
        ldx cur
        jsr mb_name
        +mbs s_hits
        jsr mb_mon
        +mbs s_for
        lda dmg
        jsr mb_num
        lda #'.'
        jsr mb_char
        jsr cmsg
        jsr hurt_foe
        jmp .nexta
.miss   jsr mb_start
        ldx cur
        jsr mb_name
        +mbs s_misses
        jsr cmsg
.nexta  jsr draw_party
        ldx cur
        inx
        cpx #4
        beq .monturn
        jmp .act

.monturn
        ldx #0              ; ---- monsters act
.mon    stx mcur
        lda mhp,x
        bne +
        jmp .nextm
+       ldx mtype           ; bosses strike more than once a round
        lda mon_hits,x
        sta acnt
.strike
-       lda #4              ; pick a living victim
        jsr rnd_n
        tax
        lda hp,x
        beq -
        stx target
        jsr rnd
        ldx mtype
        cmp mon_hit,x
        bcc +
        jmp .mmiss
+       lda mon_dmg,x       ; damage: half + 1 .. full
        lsr
        sta tmp2
        lda mon_dmg,x
        sec
        sbc tmp2
        jsr rnd_n
        sec
        adc tmp2
        ldx target
        sec                 ; armour soaks damage, minimum 1
        sbc arm,x
        beq .one
        bcs +
.one    lda #1
+       sta dmg
        ldx target
        lda action,x
        cmp #1              ; parrying halves the blow
        bne +
        lda dmg
        lsr
        adc #0
        sta dmg
+       ldx target
        lda hp,x
        sec
        sbc dmg
        bcs +
        lda #0
+       sta hp,x
        jsr mb_start
        +mbs s_the
        jsr mb_mon
        +mbs s_hits2
        ldx target
        jsr mb_name
        +mbs s_for
        lda dmg
        jsr mb_num
        lda #'.'
        jsr mb_char
        jsr draw_party
        jsr cmsg
        ldx target
        lda hp,x
        bne .more
        jsr mb_start
        ldx target
        jsr mb_name
        +mbs s_slain
        jsr cmsg
        lda hp
        ora hp+1
        ora hp+2
        ora hp+3
        bne .more
        jmp defeat
.mmiss  jsr mb_start
        +mbs s_the
        jsr mb_mon
        +mbs s_misses2
        ldx target
        jsr mb_name
        lda #'.'
        jsr mb_char
        jsr cmsg
.more   dec acnt
        beq .nextm
        jmp .strike
.nextm  ldx mcur
        inx
        cpx nmon
        beq +
        jmp .mon
+       jmp .round

.run    jsr rnd
        cmp #128
        bcs .nogo
        +msg m_fled
        jsr pause
        lda #1
        sta cres
        jmp combat_end
.nogo   +msg m_noflee
        jsr pause
        ldx #3              ; nobody parries during a botched escape
        lda #3
-       sta action,x
        dex
        bpl -
        jmp .monturn

.cast   ldx cur
        lda sp,x
        sec
        sbc p_cost,x
        sta sp,x
        cpx #0
        bne +
        jsr most_wounded    ; ARDEN: heal
        jsr heal_target
        jmp .nexta
+       cpx #1
        beq .bolt
        jsr song            ; SELA: song
        jmp .nexta
.bolt   jsr first_foe       ; MIRA: flame bolt  6 + rnd(8) + tome + 2*level
        stx target
        lda #8
        jsr rnd_n
        clc
        adc #6
        adc bonus+1
        sta dmg
        lda lvl+1           ; + 2 per level (magic ignores armour)
        asl
        adc dmg
        bcc +
        lda #255
+       sta dmg
        jsr mb_start
        +mbs s_bolt
        lda dmg
        jsr mb_num
        lda #'!'
        jsr mb_char
        jsr cmsg
        jsr hurt_foe
        jmp .nexta

; heal [target] by 6 + rnd(8) + tome + 2*level, with a message (caster = ARDEN)
heal_target
        lda #8
        jsr rnd_n
        clc
        adc #6
        adc bonus
        adc lvl
        adc lvl
        sta dmg
        ldx target
        clc
        adc hp,x
        bcs +
        cmp maxhp,x
        bcc ++
+       lda maxhp,x
++      sta hp,x
        jsr mb_start
        ldx #0
        jsr mb_name
        +mbs s_heals
        ldx target
        jsr mb_name
        +mbs s_for
        lda dmg
        jsr mb_num
        lda #'.'
        jsr mb_char
        jsr draw_party
        jmp cmsg

; SELA's song: every living member +1..4 + lute + level/2
song
        lda lvl+3
        lsr
        clc
        adc bonus+2
        sta dmg
        ldx #3
-       lda hp,x
        beq +
        stx tmp2
        lda #4
        jsr rnd_n
        ldx tmp2
        sec
        adc dmg
        adc hp,x
        bcs .cap
        cmp maxhp,x
        bcc ++
.cap    lda maxhp,x
++      sta hp,x
+       dex
        bpl -
        jsr draw_party
        +msg m_song
        jmp pause

; damage monster [target] by dmg; may end the fight
!zone hurt_foe
hurt_foe
        ldx target
        lda mhp,x
        sec
        sbc dmg
        bcs +
        lda #0
+       sta mhp,x
        php
        jsr draw_foes
        plp
        bne .alive
        jsr mb_start
        +mbs s_the
        jsr mb_mon
        +mbs s_falls
        jsr cmsg
        lda mhp
        ora mhp+1
        ora mhp+2
        ora mhp+3
        bne .alive
        jmp victory
.alive  rts

first_foe
        ldx #0
-       lda mhp,x
        bne +
        inx
        cpx #3
        bne -
+       rts

; most wounded living member -> target (tmp2 = how wounded)
most_wounded
        ldx cur
        stx target
        lda #0
        sta tmp2
        ldx #3
-       lda hp,x
        beq +
        lda maxhp,x
        sec
        sbc hp,x
        cmp tmp2
        bcc +
        beq +
        sta tmp2
        stx target
+       dex
        bpl -
        rts

; --------------------------------------------------------------------- victory, xp, levels
!zone victory
victory
        jsr hide_monster
        lda #0
        sta ggain
        sta ggain+1
        sta xpgain
        sta xpgain+1
        ldy nmon            ; rewards x number of monsters
.sum    ldx mtype
        lda ggain
        clc
        adc mon_gold_lo,x
        sta ggain
        lda ggain+1
        adc mon_gold_hi,x
        sta ggain+1
        lda xpgain
        clc
        adc mon_xp_lo,x
        sta xpgain
        lda xpgain+1
        adc mon_xp_hi,x
        sta xpgain+1
        dey
        bne .sum
        lda gold
        clc
        adc ggain
        sta gold
        lda gold+1
        adc ggain+1
        sta gold+1
        ldx #3              ; every survivor earns the full experience
.xp     lda hp,x
        beq +
        lda xp_l,x
        clc
        adc xpgain
        sta xp_l,x
        lda xp_h,x
        adc xpgain+1
        sta xp_h,x
+       dex
        bpl .xp
        jsr draw_party
        jsr mb_start
        +mbs s_victory
        lda ggain
        sta n16
        lda ggain+1
        sta n16+1
        jsr mb_u16
        +mbs s_goldf
        lda xpgain
        sta n16
        lda xpgain+1
        sta n16+1
        jsr mb_u16
        +mbs s_xpf
        jsr mb_end
        jsr level_ups
        lda #0
        sta cres
combat_end
        ldx csp
        txs
        jsr hide_monster
        jsr flush_keys      ; no attack key left over to walk or turn with
        lda #0
        sta incombat
        lda mode
        cmp #1
        bne +
        jmp dg_status
+       jmp ow_status

; promote every living member whose experience has reached the next level
!zone level_ups
level_ups
        ldx #0
        jmp .m
.nx     jmp .next           ; trampoline for the short branches below
.m      stx cur
        lda hp,x
        beq .nx
.again  ldx cur
        ldy lvl,x
        cpy #20
        bcs .nx
        iny                 ; Y = next level
        lda xp_h,x
        cmp xp_hi,y
        bcc .nx
        bne .up
        lda xp_l,x
        cmp xp_lo,y
        bcc .nx
.up     tya
        sta lvl,x
        lda #3              ; HP: class gain + 0..2
        jsr rnd_n
        ldx cur
        clc
        adc hp_gain,x
        sta dmg
        clc
        adc maxhp,x
        bcc +
        lda #250
+       cmp #250
        bcc +
        lda #250
+       sta maxhp,x
        lda hp,x
        clc
        adc dmg
        cmp maxhp,x
        bcc +
        lda maxhp,x
+       sta hp,x
        lda maxsp,x         ; SP
        clc
        adc sp_gain,x
        cmp #99
        bcc +
        lda #99
+       sta maxsp,x
        lda sp,x
        clc
        adc sp_gain,x
        cmp maxsp,x
        bcc +
        lda maxsp,x
+       sta sp,x
        lda mgt,x           ; might
        clc
        adc mgt_gain,x
        sta mgt,x
        jsr draw_party
        jsr mb_start
        ldx cur
        jsr mb_name
        +mbs s_reaches
        ldx cur
        lda lvl,x
        jsr mb_num
        lda #'!'
        jsr mb_char
        jsr cmsg
        jmp .again
.next   ldx cur
        inx
        cpx #4
        beq +
        jmp .m
+       rts

; the party falls: wake at the einherjar hall, everyone alive but hurt, half the gold gone.
; Dungeon progress (doors, bosses, runestones) is kept.
defeat
        jsr hide_monster
        +msg m_fallen
        jsr pause
        lda mode
        cmp #1
        bne +
        jsr save_level
+       lsr gold+1
        ror gold
        ldx #3
-       lda maxhp,x
        lsr
        lsr
        ora #1
        sta hp,x
        dex
        bpl -
        ldx #$ff            ; abandon everything in progress
        txs
        lda #0
        sta mode
        sta incombat
        sta inshop
        lda #CASTLE_X
        sta px
        lda #CASTLE_Y+1
        sta py
        jsr ow_colors
        jsr ow_draw
        jsr ow_status
        jsr draw_party
        +msg m_awaken
        +msg m_halfgold
        jmp main


