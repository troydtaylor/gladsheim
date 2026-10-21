; =====================================================================
;  Engine text (lowercase in source = upper-case screen codes; $ff ends)
;  Panel strings are 16 wide so they overwrite what was there.
;  Game content text (places, floors, towns, monsters) is in build/gen.asm.
; =====================================================================
s_title  !scr " gladsheim" : !byte $ff
s_gold   !scr "gold" : !byte $ff
s_wilds  !scr "gladsheim" : !byte $ff
s_xy     !scr "x:   y:     " : !byte $ff
s_facing !scr "facing      " : !byte $ff
s_dead3  !scr "---" : !byte $ff
s_n      !scr "north" : !byte $ff
s_e      !scr "east " : !byte $ff
s_s      !scr "south" : !byte $ff
s_w      !scr "west " : !byte $ff

s_n0     !scr "arden" : !byte $ff
s_n1     !scr "mira" : !byte $ff
s_n2     !scr "torvik" : !byte $ff
s_n3     !scr "sela" : !byte $ff
s_np0    !scr "arden " : !byte $ff
s_np1    !scr "mira  " : !byte $ff
s_np2    !scr "torvik" : !byte $ff
s_np3    !scr "sela  " : !byte $ff
s_c0     !scr "paladin" : !byte $ff
s_c1     !scr "wizard" : !byte $ff
s_c2     !scr "fighter" : !byte $ff
s_c3     !scr "bard" : !byte $ff

prompt_lo !byte <s_pr0, <s_pr1, <s_pr2, <s_pr3
prompt_hi !byte >s_pr0, >s_pr1, >s_pr2, >s_pr3
s_pr0    !scr "arden: (a)ttack (p)arry (h)eal (r)un" : !byte $ff
s_pr1    !scr "mira: (a)ttack (p)arry (b)olt (r)un" : !byte $ff
s_pr2    !scr "torvik: (a)ttack (p)arry (r)un" : !byte $ff
s_pr3    !scr "sela: (a)ttack (p)arry (s)ing (r)un" : !byte $ff

s_attacks !scr " attacks!" : !byte $ff
s_attack !scr " attack!" : !byte $ff
s_the    !scr "the " : !byte $ff
s_hits   !scr " hits the " : !byte $ff
s_hits2  !scr " hits " : !byte $ff
s_for    !scr " for " : !byte $ff
s_misses !scr " misses." : !byte $ff
s_misses2 !scr " misses " : !byte $ff
s_slain  !scr " is slain!" : !byte $ff
s_falls  !scr " falls!" : !byte $ff
s_heals  !scr " heals " : !byte $ff
s_bolt   !scr "mira's flame bolt hits for " : !byte $ff
s_victory !scr "victory! " : !byte $ff
s_goldf  !scr " gold, " : !byte $ff
s_xpf    !scr " xp each." : !byte $ff
s_reaches !scr " reaches level " : !byte $ff

s_sh_head  !scr "  goods       st cost" : !byte $ff
s_sh_party !scr "  party  lv at ar  hp" : !byte $ff
s_sh_foot  !scr "a-d buy    x leave" : !byte $ff
s_takes    !scr " takes the " : !byte $ff
s_hasbetter !scr " already has better." : !byte $ff
s_isdead   !scr " is dead." : !byte $ff
s_lives    !scr " lives again!" : !byte $ff
s_notdead  !scr " is not dead." : !byte $ff
s_isyours  !scr " is yours." : !byte $ff
s_blessed  !scr " feels hardier! (+max hp)" : !byte $ff

s_cs_title !scr "the party" : !byte $ff
s_cs_b     !scr "hp    /     sp   /" : !byte $ff
s_cs_c     !scr "at     ar    xp" : !byte $ff
s_lv       !scr "lv" : !byte $ff
s_sig1     !scr "runestones:   of 5" : !byte $ff

m_welcome1 !scr "welcome to gladsheim, heroes!" : !byte $ff
m_welcome2 !scr "a crypt lies near. thornbury, east." : !byte $ff
m_welcome3 !scr "c sheet  v save  l load saved game" : !byte $ff
m_north    !scr "north" : !byte $ff
m_south    !scr "south" : !byte $ff
m_east     !scr "east" : !byte $ff
m_west     !scr "west" : !byte $ff
m_blocked  !scr "blocked!" : !byte $ff
m_nothing  !scr "there is nothing to enter here." : !byte $ff
m_castle   !scr "the einherjar hall." : !byte $ff
m_healed   !scr "its healers tend the living." : !byte $ff
m_allwell  !scr "nobody needs healing." : !byte $ff
m_cantheal !scr "arden can't cast a heal now." : !byte $ff
m_sealed1  !scr "a vast gate, sealed by five runes." : !byte $ff
m_sealed2  !scr "you do not hold every runestone." : !byte $ff
m_descend  !scr "you descend into the darkness..." : !byte $ff
m_deeper   !scr "you descend deeper..." : !byte $ff
m_climb    !scr "you climb the stairs." : !byte $ff
m_ascend   !scr "you climb back into the daylight." : !byte $ff
m_wall     !scr "ouch! a wall." : !byte $ff
m_illusion !scr "the wall was an illusion!" : !byte $ff
m_stairs   !scr "stairs lead up to daylight. (e)xit?" : !byte $ff
m_stairsup !scr "stairs lead up. (e) to climb." : !byte $ff
m_stairsdn !scr "stairs lead down. (e) to descend." : !byte $ff
m_litrune  !scr "a rune glows here." : !byte $ff
m_lever1   !scr "an iron lever. (e) to pull it." : !byte $ff
m_lever2   !scr "a bone lever. (e) to pull it." : !byte $ff
m_lever3   !scr "a gold lever. (e) to pull it." : !byte $ff
m_ambush   !scr "something moves in the dark!" : !byte $ff
m_noexit   !scr "nothing to use here." : !byte $ff
m_guard    !scr "guardians bar the way!" : !byte $ff
m_key      !scr "you find an old iron key!" : !byte $ff
m_rune     !scr "a rune flares with light!" : !byte $ff
m_rumble   !scr "a distant door grinds open!" : !byte $ff
m_keyturns !scr "the key turns. the door opens!" : !byte $ff
m_mouth_ok !scr "the voice is silent. the door opens!" : !byte $ff
m_mouth_bad !scr "'wrong!' the door stays shut." : !byte $ff
m_lever_stuck !scr "the lever won't move." : !byte $ff
m_clunk    !scr "clunk! the lever locks in place." : !byte $ff
m_clang    !scr "clang! the levers all snap back." : !byte $ff
m_prompt   !scr "> " : !byte $ff
m_nosp     !scr "not enough spell points!" : !byte $ff
m_fled     !scr "the party flees!" : !byte $ff
m_noflee   !scr "no escape!" : !byte $ff
m_song     !scr "sela sings. the party is soothed." : !byte $ff
m_fallen   !scr "the party has fallen..." : !byte $ff
m_awaken   !scr "you awaken in the einherjar hall..." : !byte $ff
m_halfgold !scr "the healers took half your gold." : !byte $ff
m_presskey !scr "(press any key)" : !byte $ff
m_merch    !scr "'use the counter, friend.'" : !byte $ff
m_fount    !scr "the fountain's water sparkles." : !byte $ff
m_bed      !scr "rooms are rented at the bar." : !byte $ff
m_who      !scr "who? (1-4)" : !byte $ff
m_nevermind !scr "never mind." : !byte $ff
m_nogold   !scr "not enough gold!" : !byte $ff
m_comeagain !scr "'come again!'" : !byte $ff
m_rested   !scr "the party rests. hp and sp restored." : !byte $ff
m_cured    !scr "a warm light heals the living." : !byte $ff
m_mana     !scr "spell points restored!" : !byte $ff
m_owned    !scr "you already know that magic." : !byte $ff
m_stronger !scr "a spell grows stronger!" : !byte $ff
