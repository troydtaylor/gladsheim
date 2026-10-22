; =====================================================================
;  The edition without music: the same entry points, all silent.
;  (build.sh assembles main.asm a second time with MUSIC=0)
; =====================================================================
music_init
music_start
music_sync
music_pause
music_stop
        rts
music_toggle
        +msg m_nomusic
        rts
m_nomusic !scr "this edition has no music." : !byte $ff
