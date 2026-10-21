; =====================================================================
;  SAVE / LOAD (overworld only)
;  One file, "GLADSHEIM SAVE": $B400-$BFFF = every dungeon floor's state
;  ($B400-$BEFF) followed by a copy of the game variables ($BF00).
;  The old save is scratched first; the drive's error channel is read
;  afterwards, so write-protect / disk-full errors are reported.
; =====================================================================
SETLFS  = $ffba
SETNAM  = $ffbd
OPEN    = $ffc0
CLOSE   = $ffc3
CHKIN   = $ffc6
CLRCHN  = $ffcc
CHRIN   = $ffcf
LOAD    = $ffd5
SAVE    = $ffd8
SAVES   = $b400
SAVEBUF = $bf00
SAVEEND = $c000
DEVICE  = 8

!zone save_game
save_game
        lda mode
        beq +
        +msg m_saveow
        rts
+       lda px
        sta savepx
        lda py
        sta savepy
        lda #'g'
        sta savemagic
        lda #'4'
        sta savemagic+1
        ldx #0
.cp     lda VARS,x
        sta SAVEBUF,x
        inx
        bne .cp
        +msg m_saving
        lda #scratch_len        ; OPEN 15,8,15,"S0:GLADSHEIM SAVE" : CLOSE 15
        ldx #<scratch_name
        ldy #>scratch_name
        jsr SETNAM
        lda #15
        ldx #DEVICE
        ldy #15
        jsr SETLFS
        jsr OPEN
        lda #15
        jsr CLOSE
        lda #save_len           ; SAVE "GLADSHEIM SAVE",8  $B400-$BFFF
        ldx #<save_name
        ldy #>save_name
        jsr SETNAM
        lda #1
        ldx #DEVICE
        ldy #0
        jsr SETLFS
        lda #<SAVES
        sta $fb
        lda #>SAVES
        sta $fc
        lda #$fb
        ldx #<SAVEEND
        ldy #>SAVEEND
        jsr SAVE
        bcs .err
        jsr drive_ok
        bcs .err
        +msg m_saved
        rts
.err    +msg m_saveerr
        rts

!zone load_game
load_game
        lda mode
        beq +
        +msg m_saveow
        rts
+       +msg m_loading
        lda #save_len
        ldx #<save_name
        ldy #>save_name
        jsr SETNAM
        lda #1
        ldx #DEVICE
        ldy #1                  ; load to the file's own address ($B400)
        jsr SETLFS
        lda #0
        jsr LOAD
        bcs .err
        lda SAVEBUF+(savemagic-VARS)
        cmp #'g'
        bne .bad
        lda SAVEBUF+(savemagic-VARS)+1
        cmp #'4'
        bne .bad
        ldx #0
.cp     lda SAVEBUF,x
        sta VARS,x
        inx
        bne .cp
        lda savepx
        sta px
        lda savepy
        sta py
        lda #0
        sta mode
        sta incombat
        sta inshop
        sta insheet
        jsr hide_monster
        jsr ow_colors
        jsr ow_draw
        jsr ow_status
        jsr draw_party
        +msg m_loaded
        rts
.bad    +msg m_badsave
        rts
.err    jsr drive_ok            ; clear the drive's error state
        +msg m_noload
        rts

; read the drive's error channel: carry clear if it says "00" (or "01" files scratched)
!zone drive_ok
drive_ok
        lda #0
        jsr SETNAM
        lda #15
        ldx #DEVICE
        ldy #15
        jsr SETLFS
        jsr OPEN
        bcs .fail
        ldx #15
        jsr CHKIN
        bcs .fail
        jsr CHRIN               ; tens digit
        sta tmp
        jsr CHRIN               ; units digit
        sta tmp2
.drain  jsr CHRIN               ; rest of the line
        cmp #13
        bne .drain
        jsr CLRCHN
        lda #15
        jsr CLOSE
        lda tmp
        cmp #'0'
        bne .bad
        lda tmp2
        cmp #'2'                ; 00 ok, 01 files scratched
        bcs .bad
        clc
        rts
.bad    sec
        rts
.fail   jsr CLRCHN
        lda #15
        jsr CLOSE
        sec
        rts

scratch_name !pet "s0:gladsheim save"
scratch_len = * - scratch_name
save_name    !pet "gladsheim save"
save_len = * - save_name

m_saveow   !scr "save and load out in the wilds." : !byte $ff
m_saving   !scr "saving to disk..." : !byte $ff
m_saved    !scr "game saved." : !byte $ff
m_saveerr  !scr "save failed! check the disk." : !byte $ff
m_loading  !scr "loading saved game..." : !byte $ff
m_loaded   !scr "welcome back, adventurers!" : !byte $ff
m_badsave  !scr "that save is not from this game." : !byte $ff
m_noload   !scr "no saved game found." : !byte $ff
