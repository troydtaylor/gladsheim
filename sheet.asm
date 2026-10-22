; =====================================================================
;  CHARACTER SHEET (C key) and THE END
; =====================================================================
!zone char_sheet
char_sheet
        lda #1
        sta insheet
        jsr clear_view
        +print VX+2,1,s_cs_title,TITLECOL
        lda #0
        sta member
.m      lda member          ; base row = 2 + 4*member
        asl
        asl
        clc
        adc #2
        sta n3row
        ldx member          ; --- row 1: name, class, level
        lda #TEXTCOL
        ldy hp,x
        bne +
        lda #DEADCOL
+       sta textcol
        lda pnamep_lo,x
        sta str
        lda pnamep_hi,x
        sta str+1
        ldx #VX+2
        ldy n3row
        jsr print_at
        ldx member
        lda pclass_lo,x
        sta str
        lda pclass_hi,x
        sta str+1
        ldx #VX+10
        ldy n3row
        jsr print_at
        lda #<s_lv
        sta str
        lda #>s_lv
        sta str+1
        ldx #VX+18
        ldy n3row
        jsr print_at
        lda #2
        sta ndig
        ldx member
        lda lvl,x
        ldx #VX+20
        ldy n3row
        jsr pu8
        inc n3row           ; --- row 2: hp, sp
        lda #<s_cs_b
        sta str
        lda #>s_cs_b
        sta str+1
        ldx #VX+2
        ldy n3row
        jsr print_at
        lda #3
        sta ndig
        ldx member
        lda hp,x
        ldx #VX+5
        ldy n3row
        jsr pu8
        ldx member
        lda maxhp,x
        ldx #VX+9
        ldy n3row
        jsr pu8
        lda #2
        sta ndig
        ldx member
        lda sp,x
        ldx #VX+17
        ldy n3row
        jsr pu8
        ldx member
        lda maxsp,x
        ldx #VX+20
        ldy n3row
        jsr pu8
        inc n3row           ; --- row 3: attack (weapon + might), armour, xp
        lda #<s_cs_c
        sta str
        lda #>s_cs_c
        sta str+1
        ldx #VX+2
        ldy n3row
        jsr print_at
        lda #3
        sta ndig
        ldx member
        lda wpn,x
        clc
        adc mgt,x
        ldx #VX+5
        ldy n3row
        jsr pu8
        lda #2
        sta ndig
        ldx member
        lda arm,x
        ldx #VX+12
        ldy n3row
        jsr pu8
        lda #5
        sta ndig
        ldx member
        lda xp_l,x
        sta n16
        lda xp_h,x
        sta n16+1
        ldx #VX+18
        ldy n3row
        jsr print_u
        inc member
        lda member
        cmp #4
        beq +
        jmp .m
+       +print VX+2,18,s_sig1,HEADCOL      ; runestones held
        lda sigils
        ldx #0
.pop    lsr
        bcc +
        inx
+       cmp #0
        bne .pop
        txa
        ora #$30
        sta tmp             ; set_cursor uses A
        ldx #VX+14
        ldy #18
        jsr set_cursor
        ldy #0
        lda tmp
        sta (dst),y
        lda #TITLECOL
        sta (cdst),y
        +msg m_presskey
        jsr getkey
        lda #0
        sta insheet
; redraw whatever the sheet covered
redraw_view
        lda mode
        cmp #1
        bne +
        jsr clear_view      ; the sheet is wider than the 3D window
        jsr dg_render
        jmp dg_status
+       jsr ow_draw
        jmp ow_status

; the final chest: the wyrm is slain
!zone the_end
the_end
        lda #1
        sta won
        jsr pause
        jsr clear_view
        ldx #0
.l      stx member
        lda end_lo,x
        sta str
        lda end_hi,x
        sta str+1
        lda end_col,x
        sta textcol
        txa
        clc
        adc #3
        tay
        ldx #VX+3
        jsr print_at
        ldx member
        inx
        cpx #12
        bne .l
        +msg m_presskey
        jsr getkey
        jmp redraw_view

end_lo  !byte <e0,<e1,<e2,<e3,<e4,<e5,<e6,<e7,<e8,<e9,<e10,<e11
end_hi  !byte >e0,>e1,>e2,>e3,>e4,>e5,>e6,>e7,>e8,>e9,>e10,>e11
end_col !byte TITLECOL,TITLECOL,TEXTCOL,TEXTCOL,TEXTCOL,TEXTCOL,TEXTCOL,TEXTCOL,HEADCOL,HEADCOL,TEXTCOL,TITLECOL
e0  !scr "nidhogg the wyrm" : !byte $ff
e1  !scr "is slain!" : !byte $ff
e2  !byte $ff
e3  !scr "the runestones" : !byte $ff
e4  !scr "blaze with light," : !byte $ff
e5  !scr "and the gates of" : !byte $ff
e6  !scr "valhalla open." : !byte $ff
e7  !byte $ff
e8  !scr "thank you for" : !byte $ff
e9  !scr "playing!" : !byte $ff
e10 !byte $ff
e11 !scr "  - the end -" : !byte $ff
