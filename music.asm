; =====================================================================
;  MUSIC: a small three-voice SID player on the KERNAL's 60 Hz interrupt
;
;  Tunes, patterns and instruments come from music.py (build/music.asm).
;  Pattern bytes: $00 rest, $01-$5F note, $60-$9F length (1-64 ticks),
;                 $A0+ instrument, $FF end of pattern.
;  A tick is a 16th note, mus_speed frames long.  Each note's gate is
;  released two frames before the next tick so notes are articulated.
;  The main loop calls music_sync: the wilds tune above ground, the
;  dungeon tune below.  M turns the music off and on.
; =====================================================================
SID     = $d400

; once at start: hook the interrupt, silence the SID
music_init
        sei
        lda #<music_irq
        sta $0314
        lda #>music_irq
        sta $0315
        cli
        lda #1
        sta mus_enabled
        lda #$ff
        sta mus_tune
        ; fall through
music_stop
        lda #0
        sta mus_on
        ldx #$17
-       sta SID,x
        dex
        bpl -
        rts

; before disk work: silence; the main loop starts the music again afterwards
music_pause
        jsr music_stop
        lda #$ff
        sta mus_tune
        rts

music_irq
        lda mus_on
        beq +
        jsr music_play
+       jmp $ea31           ; the KERNAL's own work: keyboard, clock

; play the tune that belongs here (0 wilds and towns, 1 dungeons)
music_sync
        lda mus_enabled
        beq .r
        ldx #0
        lda mode
        cmp #1
        bne +
        inx
+       cpx mus_tune
        beq .r
        txa
        jmp music_start
.r      rts

; M: music off / on
music_toggle
        lda mus_enabled
        eor #1
        sta mus_enabled
        beq .off
        lda #$ff            ; music_sync starts the right tune
        sta mus_tune
        jsr music_sync
        +msg m_musicon
        rts
.off    jsr music_stop
        lda #$ff
        sta mus_tune
        +msg m_musicoff
        rts

; A = tune: start it from the top
!zone music_start
music_start
        pha
        jsr music_stop
        pla
        sta mus_tune
        tax
        lda mus_speed,x
        sta mspeed
        sec
        sbc #2
        sta mgoff
        txa                 ; order lists of voices tune*3 .. tune*3+2
        asl
        adc mus_tune
        tay
        ldx #0
.v      lda mus_ord_lo,y
        sta vord_lo,x
        lda mus_ord_hi,y
        sta vord_hi,x
        lda #0
        sta vordi,x
        sta vins,x
        sta vfx,x
        lda #1
        sta vtick,x
        sta vdur,x
        txa
        pha
        tya
        pha
        jsr next_pattern
        pla
        tay
        pla
        tax
        iny
        inx
        cpx #3
        bne .v
        lda #0
        sta mfcnt
        lda #$0f            ; full volume, no filter
        sta SID+$18
        lda #1
        sta mus_on
        rts

; X = voice: the next pattern of its order list (looping at $FF)
!zone next_pattern
next_pattern
        lda vord_lo,x
        sta .o+1
        lda vord_hi,x
        sta .o+2
        ldy vordi,x
.o      lda $ffff,y
        cmp #$ff
        bne +
        lda #0              ; loop
        sta vordi,x
        tay
        jmp .o
+       tay
        lda mus_pat_lo,y
        sta vpat_lo,x
        lda mus_pat_hi,y
        sta vpat_hi,x
        inc vordi,x
        rts

; one frame
!zone music_play
music_play
        ldx #2
.fx     jsr voice_fx
        dex
        bpl .fx
        lda mfcnt
        bne .gate
        ldx #2              ; a tick: voices whose note is over read on
.t      dec vtick,x
        bne +
        jsr fetch
+       dex
        bpl .t
.gate   lda mfcnt           ; release the gate just before a note ends
        cmp mgoff
        bne .next
        ldx #2
.g      lda vtick,x
        cmp #1
        bne +
        ldy sidofs,x
        lda vwave,x
        and #$fe
        sta SID+4,y
+       dex
        bpl .g
.next   inc mfcnt
        lda mfcnt
        cmp mspeed
        bcc +
        lda #0
        sta mfcnt
+       rts

; X = voice: read its pattern up to the next note or rest
!zone fetch
fetch
.rd     lda vpat_lo,x
        sta .b+1
        lda vpat_hi,x
        sta .b+2
.b      lda $ffff
        inc vpat_lo,x
        bne +
        inc vpat_hi,x
+       cmp #$ff
        bne +
        jsr next_pattern
        jmp .rd
+       cmp #$a0
        bcc +
        sbc #$a0            ; instrument
        sta vins,x
        jmp .rd
+       cmp #$60
        bcc .note
        sbc #$5f            ; length
        sta vdur,x
        jmp .rd
.note   sta mnote
        lda vdur,x
        sta vtick,x
        ldy sidofs,x
        lda mnote
        bne .play
        lda vwave,x         ; a rest
        and #$fe
        sta SID+4,y
        rts
.play   stx mvoice
        ldx mnote
        lda mus_flo,x
        sta SID+0,y
        pha
        lda mus_fhi,x
        sta SID+1,y
        ldx mvoice
        sta vfhi,x
        pla
        sta vflo,x
        lda vins,x          ; the instrument's sound
        tax
        lda ins_ad,x
        sta SID+5,y
        lda ins_sr,x
        sta SID+6,y
        lda ins_fx,x
        sta mfxv
        lda ins_pw,x
        sta mpw
        lda ins_wave,x
        ldx mvoice
        sta vwave,x
        pha
        lda mfxv
        sta vfx,x
        lda mpw
        sta vpwhi,x
        sta SID+3,y
        lda #0
        sta vpwlo,x
        sta SID+2,y
        sta vvib,x
        sta vpwd,x
        pla
        sta SID+4,y         ; gate on
        rts

; X = voice: pulse sweep and vibrato
!zone voice_fx
voice_fx
        ldy sidofs,x
        lda vfx,x
        lsr
        bcc .vib
        pha
        lda vpwd,x          ; pulse width sweeps $400..$C00 and back
        bne .down
        lda vpwlo,x
        clc
        adc #$20
        sta vpwlo,x
        bcc .wr
        inc vpwhi,x
        lda vpwhi,x
        cmp #$0c
        bcc .wr
        inc vpwd,x
        bne .wr
.down   lda vpwlo,x
        sec
        sbc #$20
        sta vpwlo,x
        bcs .wr
        dec vpwhi,x
        lda vpwhi,x
        cmp #$04
        bcs .wr
        dec vpwd,x
.wr     lda vpwlo,x
        sta SID+2,y
        lda vpwhi,x
        sta SID+3,y
        pla
.vib    lsr
        bcc .r
        inc vvib,x          ; after a moment, +-1/128 of the pitch
        lda vvib,x
        cmp #14
        bcc .r
        and #4
        bne .minus
        lda vfhi,x          ; delta = high byte * 2
        asl
        sta mvlo
        lda #0
        rol
        sta mvhi
        lda vflo,x
        clc
        adc mvlo
        sta SID+0,y
        lda vfhi,x
        adc mvhi
        sta SID+1,y
        rts
.minus  lda vfhi,x
        asl
        sta mvlo
        lda #0
        rol
        sta mvhi
        lda vflo,x
        sec
        sbc mvlo
        sta SID+0,y
        lda vfhi,x
        sbc mvhi
        sta SID+1,y
.r      rts

sidofs  !byte 0, 7, 14
mus_on      !byte 0
mus_enabled !byte 1
mus_tune    !byte $ff
mspeed  !byte 7
mgoff   !byte 5
mfcnt   !byte 0
mnote   !byte 0
mvoice  !byte 0
mfxv    !byte 0
mpw     !byte 0
mvlo     !byte 0
mvhi     !byte 0
vord_lo !fill 3
vord_hi !fill 3
vordi   !fill 3
vpat_lo !fill 3
vpat_hi !fill 3
vtick   !fill 3
vdur    !fill 3
vins    !fill 3
vwave   !fill 3
vflo    !fill 3
vfhi    !fill 3
vpwlo   !fill 3
vpwhi   !fill 3
vpwd    !fill 3
vvib    !fill 3
vfx     !fill 3
m_musicon  !scr "music on." : !byte $ff
m_musicoff !scr "music off. (m to turn it back on)" : !byte $ff
