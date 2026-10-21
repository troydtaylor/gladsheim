; =====================================================================
;  BITMAP COMPOSITOR
;  The game draws into two in-memory layers; `present` turns whatever
;  changed into hires bitmap pixels (320x200, two colours per 8x8 cell).
;
;  Graphics layer  VSCR  40x25 glyph codes (tiles, walls, frame).
;                        EMPTY ($FF) = show the text layer there.
;  Text layer      VTX   80x25 screen codes in a 3x7 font, two per cell
;                  VTC   80x25 colours (a cell takes its left letter's colour)
;
;  Graphics cells are redrawn when their code differs from the last one
;  presented (PG). Text rows are redrawn when marked in `tdirty`, which
;  the text cursor (set_cursor) does automatically.
;
;  present is called from getkey and pause, i.e. whenever the game waits.
; =====================================================================
; --------------------------------------------------------------------- setup
!zone video_init
video_init
        lda $dd02           ; VIC bank 3 ($C000-$FFFF)
        ora #3
        sta $dd02
        lda $dd00
        and #$fc
        sta $dd00
        lda #$08            ; colour matrix $C000, bitmap $E000
        sta $d018
        lda #$3b            ; bitmap mode, screen on, 25 rows
        sta $d011
        lda #$08            ; hires, 40 columns
        sta $d016
        ldx #0              ; monster portraits into bank 3
.sp     lda SPRITES,x
        sta SPRDST,x
        lda SPRITES+$100,x
        sta SPRDST+$100,x
        lda SPRITES+$200,x
        sta SPRDST+$200,x
        lda SPRITES+$300,x
        sta SPRDST+$300,x
        lda SPRITES+$400,x
        sta SPRDST+$400,x
        lda SPRITES+$500,x
        sta SPRDST+$500,x
        lda SPRITES+$600,x
        sta SPRDST+$600,x
        lda SPRITES+$700,x
        sta SPRDST+$700,x
        lda SPRITES+$800,x
        sta SPRDST+$800,x
        lda SPRITES+$900,x
        sta SPRDST+$900,x
        inx
        bne .sp
        lda #T_GRASS
        sta under
; fall through: blank both layers and force a full redraw
!zone clear_screen
clear_screen
        ldx #0
.g      lda #EMPTY
        sta VSCR,x
        sta VSCR+$100,x
        sta VSCR+$200,x
        sta VSCR+$2e8,x
        lda #$fe            ; never a real code: every cell gets drawn
        sta PG,x
        sta PG+$100,x
        sta PG+$200,x
        sta PG+$2e8,x
        inx
        bne .g
        ldx #0
.t      lda #32
        sta VTX,x
        sta VTX+$100,x
        sta VTX+$200,x
        sta VTX+$300,x
        sta VTX+$400,x
        sta VTX+$500,x
        sta VTX+$600,x
        sta VTX+$700,x
        lda #TEXTCOL
        sta VTC,x
        sta VTC+$100,x
        sta VTC+$200,x
        sta VTC+$300,x
        sta VTC+$400,x
        sta VTC+$500,x
        sta VTC+$600,x
        sta VTC+$700,x
        inx
        bne .t
mark_all
        ldx #24
        lda #1
-       sta tdirty,x
        dex
        bpl -
        rts

; --------------------------------------------------------------------- present
!zone present
present
        lda #0
        sta prow
.row    ldx prow
        lda scr_lo,x        ; VSCR row; PG and MATRIX share its low byte
        sta rg
        sta rp
        sta rm
        lda scr_hi,x
        sta rg+1
        clc
        adc #>(PG-VSCR)
        sta rp+1
        lda scr_hi,x
        clc
        adc #>(MATRIX-VSCR)
        sta rm+1
        lda tx_lo,x
        sta rt
        sta rc
        lda tx_hi,x
        sta rt+1
        clc
        adc #>(VTC-VTX)
        sta rc+1
        lda bm_lo,x
        sta brow
        lda bm_hi,x
        sta brow+1
        lda tdirty,x
        sta pdirty
        lda #0
        sta tdirty,x
        ldy #0
.col    lda (rg),y
        cmp (rp),y
        bne .draw
        cmp #EMPTY
        bne .next
        ldx pdirty
        beq .next
.draw   sta (rp),y
        sty pcol
        tax                 ; bm = bitmap row + column * 8
        lda brow
        clc
        adc col8_lo,y
        sta bm
        lda brow+1
        adc col8_hi,y
        sta bm+1
        txa
        jsr draw_cell
        ldy pcol
.next   iny
        cpy #40
        bne .col
        inc prow
        lda prow
        cmp #25
        bne .row
        rts

; A = graphics code of cell pcol in the current row
!zone draw_cell
draw_cell
        cmp #EMPTY
        beq .text
        tax
        lda gcol,x          ; colour pair
        cpx #T_PLAYER+TILE_BASE
        bne +
        and #$f0            ; the party: its own colour on the terrain's ground
        sta tmp2
        ldy under
        lda tile_char,y
        tay
        lda gcol,y
        and #$0f
        ora tmp2
+       ldy pcol
        sta (rm),y
        lda glyph_lo,x
        sta gp
        lda glyph_hi,x
        sta gp+1
        ldy #0
        !for i, 0, 7 {
        lda (gp),y
        sta (bm),y
        iny
        }
        rts
.text   lda pcol            ; two small letters side by side
        asl
        tay
        lda (rt),y
        and #63
        sta lcode
        iny
        lda (rt),y
        and #63
        sta rcode
        cmp #32
        bne .ink
        lda lcode
        cmp #32
        bne .ink
        ldy #0              ; two spaces: a blank cell
        tya
        !for i, 0, 7 {
        sta (bm),y
        iny
        }
        ldy pcol
        sta (rm),y
        rts
.ink    dey                 ; colour: the left letter's, unless it is a space
        lda (rc),y
        ldx lcode
        cpx #32
        bne +
        iny
        lda (rc),y
+       asl
        asl
        asl
        asl
        ldy pcol
        sta (rm),y
        ldx lcode
        lda font_lo,x
        sta gp
        lda fonth_hi,x
        sta gp+1
        ldx rcode
        lda font_lo,x
        sta gq
        lda fontl_hi,x
        sta gq+1
        ldy #0
        !for i, 0, 7 {
        lda (gp),y
        ora (gq),y
        sta (bm),y
        iny
        }
        rts

col8_lo  !for i, 0, 39 { !byte <(i*8) }
col8_hi  !for i, 0, 39 { !byte >(i*8) }
glyph_lo !for i, 0, 255 { !byte <(GLYPHS + i*8) }
glyph_hi !for i, 0, 255 { !byte >(GLYPHS + i*8) }
font_lo  !for i, 0, 63 { !byte <(i*8) }
fonth_hi !for i, 0, 63 { !byte >(FONT4H + i*8) }
fontl_hi !for i, 0, 63 { !byte >(FONT4L + i*8) }

; rows of the text layer and of the bitmap
tx_lo   !for r, 0, 24 { !byte <(VTX + r*80) }
tx_hi   !for r, 0, 24 { !byte >(VTX + r*80) }
bm_lo   !for r, 0, 24 { !byte <(BITMAP + r*320) }
bm_hi   !for r, 0, 24 { !byte >(BITMAP + r*320) }
