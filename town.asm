; =====================================================================
;  TOWNS (mode 2): Thornbury, Ravenmoor
;  Walk into a counter/altar to shop, into people to talk, into signs.
;  Shops are numbered globally: town*5 + (forge, armory, temple, tavern, magic).
; =====================================================================

; A = town index
town_enter
        sta town
        lda px
        sta owx
        lda py
        sta owy
        lda #2
        sta mode
        ldx town
        lda town_sx,x
        sta px
        lda town_sy,x
        sta py
        jsr ow_draw
        jsr ow_status
        ldx town
        +ptrmsg town_wel_lo, town_wel_hi
        rts

town_leave
        lda #0
        sta mode
        lda owx
        sta px
        lda owy
        sta py
        jsr ow_draw
        jsr ow_status
        ldx town
        +ptrmsg town_bye_lo, town_bye_hi
        rts

; A = tile walked into at (tx,ty)
!zone town_bump
town_bump
        cmp #T_COUNTER
        beq .shop
        cmp #T_ALTAR
        beq .shop
        cmp #T_MERCHANT
        beq .merch
        cmp #T_FOUNTAIN
        beq .fount
        cmp #T_BED
        beq .bed
        cmp #T_SIGN_W
        bcc .wall
        cmp #T_SIGN_M+1
        bcc .sign
        cmp #T_GUARD
        bcc .wall
        cmp #T_FOLK2+1
        bcc .npc
.wall   +msg m_blocked
        rts
.shop   jsr find_shop
        bmi .wall
        jmp shop_open
.sign   jsr find_shop
        bmi .wall
        +ptrmsg sign_lo, sign_hi
        rts
.npc    jmp talk_npc
.merch  +msg m_merch
        rts
.fount  +msg m_fount
        rts
.bed    +msg m_bed
        rts

; which of this town's shops contains (tx,ty)? -> X = global shop, N clear; N set if none
!zone find_shop
find_shop
        lda town
        asl
        asl
        adc town            ; town*5
        sta tmp
        clc
        adc #4
        tax
.l      lda tx
        cmp shop_x0,x
        bcc .no
        lda shop_x1,x
        cmp tx
        bcc .no
        lda ty
        cmp shop_y0,x
        bcc .no
        lda shop_y1,x
        cmp ty
        bcc .no
        txa
        rts
.no     cpx tmp
        beq .none
        dex
        jmp .l
.none   ldx #$ff
        rts

!zone talk_npc
talk_npc
        ldx town
        lda town_npc_first,x
        sta tmp
        clc
        adc town_npc_count,x
        sta tmp2
        ldx tmp
.l      lda npc_x,x
        cmp tx
        bne .no
        lda npc_y,x
        cmp ty
        beq .found
.no     inx
        cpx tmp2
        bne .l
        +msg m_blocked
        rts
.found  stx member
        +ptrmsg npc1_lo, npc1_hi
        ldx member
        +ptrmsg npc2_lo, npc2_hi
        rts

; ---------------------------------------------------------------------
;  Shop screen (drawn inside the viewport)
; ---------------------------------------------------------------------
!zone shop_open
shop_open
        stx shop
        lda #1
        sta inshop
        jsr shop_draw
        +print PC,16,s_sh_k1,TEXTCOL
        +print PC,17,s_sh_k2,TEXTCOL
        +print PC,18,s_sh_k3,TEXTCOL
        +print PC,19,s_blank,TEXTCOL
        ldx shop
        +ptrmsg greet_lo, greet_hi
.loop   jsr getkey
        cmp #$58            ; X
        beq .leave
        cmp #$41            ; A-D
        bcc .loop
        cmp #$45
        bcs .loop
        sec
        sbc #$41
        jsr shop_buy
        jmp .loop
.leave  lda #0
        sta inshop
        jsr ow_draw
        jsr ow_status
        +msg m_comeagain
        rts

!zone shop_draw
shop_draw
        jsr clear_view
        ldx shop
        lda sname_lo,x
        sta str
        lda sname_hi,x
        sta str+1
        lda #TITLECOL
        sta textcol
        ldx #2
        ldy #2
        jsr print_at
        ldx shop
        lda squote_lo,x
        sta str
        lda squote_hi,x
        sta str+1
        lda #TEXTCOL
        sta textcol
        ldx #2
        ldy #3
        jsr print_at
        +print 2,5,s_sh_head,HEADCOL
        lda #0
        sta member          ; reused as the item row counter
.item   lda shop
        asl
        asl
        clc
        adc member
        tax
        lda it_eff,x
        bne +
        jmp .next
+       stx itidx
        lda member          ; letter A-D
        clc
        adc #6
        sta n3row
        tay
        ldx #2
        jsr set_cursor
        lda member
        clc
        adc #1
        ldy #0
        sta (dst),y
        lda #HEADCOL
        sta (cdst),y
        ldx itidx
        lda it_name_lo,x
        sta str
        lda it_name_hi,x
        sta str+1
        lda #TEXTCOL
        sta textcol
        ldx #4
        ldy n3row
        jsr print_at
        ldx itidx
        lda it_stat,x
        beq .nostat
        ldy #2
        sty ndig
        ldy n3row
        ldx #16
        jsr pu8
.nostat ldx itidx
        lda it_price_lo,x
        sta n16
        lda it_price_hi,x
        sta n16+1
        lda #5
        sta ndig
        ldx #18
        ldy n3row
        jsr print_u
.next   inc member
        lda member
        cmp #4
        beq +
        jmp .item
+       +print 2,11,s_sh_party,HEADCOL
        jsr shop_party
        +print 2,17,s_sh_foot,HEADCOL
        rts

; party rows 12-15: number, name, level, weapon, armour, hp
!zone shop_party
shop_party
        ldx #0
.l      stx member
        lda #TEXTCOL
        ldy hp,x
        bne +
        lda #DEADCOL
+       sta textcol
        txa
        clc
        adc #12
        sta n3row
        tay
        ldx #2
        jsr set_cursor
        ldy #0
        lda member
        clc
        adc #$31            ; '1'..'4'
        sta (dst),y
        lda textcol
        sta (cdst),y
        ldx member
        lda pnamep_lo,x
        sta str
        lda pnamep_hi,x
        sta str+1
        ldx #4
        ldy n3row
        jsr print_at
        lda #2
        sta ndig
        ldx member
        lda lvl,x
        ldx #11
        ldy n3row
        jsr pu8
        ldx member
        lda wpn,x
        ldx #14
        ldy n3row
        jsr pu8
        ldx member
        lda arm,x
        ldx #17
        ldy n3row
        jsr pu8
        lda #3
        sta ndig
        ldx member
        lda hp,x
        ldx #20
        ldy n3row
        jsr pu8
        ldx member
        inx
        cpx #4
        beq +
        jmp .l
+       rts

; A = item letter 0-3
!zone shop_buy
shop_buy
        sta tmp
        lda shop
        asl
        asl
        clc
        adc tmp
        sta itidx
        tax
        lda it_eff,x
        bne +
        rts
+       lda gold+1          ; can we afford it?  (16-bit gold >= price)
        cmp it_price_hi,x
        bcc .poor
        bne .afford
        lda gold
        cmp it_price_lo,x
        bcs .afford
.poor   +msg m_nogold
        rts
.afford lda it_eff,x
        cmp #E_WEAPON
        beq .who
        cmp #E_ARMOR
        beq .who
        cmp #E_RAISE
        beq .who
        cmp #E_BLESS
        beq .who
        jmp .nomember
.who    +msg m_who
        jsr getkey
        cmp #$31
        bcc .cancel
        cmp #$35
        bcs .cancel
        sec
        sbc #$31
        sta member
        ldx itidx
        lda it_eff,x
        cmp #E_WEAPON
        beq .weapon
        cmp #E_ARMOR
        beq .armor
        cmp #E_BLESS
        bne +
        jmp .bless
+       jmp .raise
.cancel +msg m_nevermind
        rts

.weapon ldy member
        lda hp,y
        beq .isdead
        lda it_stat,x
        cmp wpn,y
        beq .better
        bcc .better
        sta wpn,y
        jmp .takes
.armor  ldy member
        lda hp,y
        beq .isdead
        lda it_stat,x
        cmp arm,y
        beq .better
        bcc .better
        sta arm,y
.takes  jsr pay
        jsr mb_start
        ldx member
        jsr mb_name
        +mbs s_takes
        jsr mb_item
        lda #'.'
        jsr mb_char
        jsr mb_end
        jmp .done
.better jsr mb_start
        ldx member
        jsr mb_name
        +mbs s_hasbetter
        jmp mb_end
.isdead jsr mb_start
        ldx member
        jsr mb_name
        +mbs s_isdead
        jmp mb_end
.bless  ldy member
        lda hp,y
        beq .isdead
        lda maxhp,y
        clc
        adc it_stat,x
        cmp #250
        bcc +
        lda #250
+       sta maxhp,y
        lda hp,y
        clc
        adc it_stat,x
        cmp maxhp,y
        bcc +
        lda maxhp,y
+       sta hp,y
        jsr pay
        jsr mb_start
        ldx member
        jsr mb_name
        +mbs s_blessed
        jsr mb_end
        jmp .done
.raise  ldy member
        lda hp,y
        bne .notdead
        lda maxhp,y
        sta hp,y
        jsr pay
        jsr mb_start
        ldx member
        jsr mb_name
        +mbs s_lives
        jsr mb_end
        jmp .done
.notdead jsr mb_start
        ldx member
        jsr mb_name
        +mbs s_notdead
        jmp mb_end

.nomember
        cmp #E_ALE
        bne +
        jsr pay
        lda #8
        jsr rnd_n
        sta tmp
        lda town
        asl
        asl
        asl
        clc
        adc tmp
        tax
        +ptrmsg rumor_lo, rumor_hi
        jmp .done
+       cmp #E_ROOM
        bne +
        jsr pay
        jsr restore_hp
        jsr restore_sp
        +msg m_rested
        jmp .done
+       cmp #E_CURE
        bne +
        jsr pay
        jsr restore_hp
        +msg m_cured
        jmp .done
+       cmp #E_TOME
        bne +
        ldy it_par,x
        lda bonus,y
        cmp it_stat,x
        bcc .learn
        +msg m_owned
        rts
.learn  lda it_stat,x
        sta bonus,y
        jsr pay
        jsr mb_start
        +mbs s_the
        jsr mb_item
        +mbs s_isyours
        jsr mb_end
        +msg m_stronger
        jmp .done
+       jsr pay             ; E_MANA
        jsr restore_sp
        +msg m_mana
.done   jsr shop_party
        jmp draw_party

pay
        ldx itidx
        lda gold
        sec
        sbc it_price_lo,x
        sta gold
        lda gold+1
        sbc it_price_hi,x
        sta gold+1
        rts

mb_item
        ldx itidx
        lda it_name_lo,x
        pha
        lda it_name_hi,x
        tax
        pla
        jmp mb_str
