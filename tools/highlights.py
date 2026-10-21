#!/usr/bin/env python3
"""
Highlight reel of a complete automated playthrough (tools/playtest.py) as MP4.
Puzzles, bosses, level-ups and the ending run at normal speed; travel and ordinary
fights are fast-forwarded; grinding and routine shopping are skipped with a card.
Every frame is the emulated C64 screen.

    python3 tools/highlights.py [out.mp4] [--seed 0x2222]
"""
import os, sys, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import playtest as P
import content as C

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = [a for a in sys.argv[1:] if not a.startswith("--") and not a.startswith("0x")]
OUT = args[0] if args else os.path.join(ROOT, "build", "highlights.mp4")
SEED = int(sys.argv[sys.argv.index("--seed") + 1], 16) if "--seed" in sys.argv else None
FPS, SCALE, BAR = 10, 3, 60
W, H = 384 * SCALE, 264 * SCALE
TMP = "/tmp/_hl_frame.png"

def font(size):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", size)
    except OSError:
        return ImageFont.load_default()
FONT, BIG, MID = font(30), font(60), font(32)

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                       "-s", f"{W}x{H + BAR}", "-r", str(FPS), "-i", "-", "-c:v", "libx264",
                       "-pix_fmt", "yuv420p", "-crf", "20", "-movflags", "+faststart", OUT],
                      stdin=subprocess.PIPE)
st = {"bot": None, "caption": "", "speed": "fast", "frames": 0, "fastskip": 0, "seen_mon": set()}
BOSSES = {i for i, m in enumerate(C.MONSTERS) if m[12] in ("the ", "")}

def screen():
    st["bot"].c.render(TMP, scale=SCALE)
    img = Image.new("RGB", (W, H + BAR), (0, 0, 0))
    img.paste(Image.open(TMP), (0, 0))
    return img

def emit(img, n):
    raw = img.tobytes()
    for _ in range(n):
        ff.stdin.write(raw)
    st["frames"] += n

def card(title, sub, sub2="", n=28):
    img = ImageEnhance.Brightness(screen()).enhance(0.22)
    d = ImageDraw.Draw(img)
    for text, f, y, col in ((title, BIG, H // 2 - 90, (191, 206, 114)), (sub, MID, H // 2, (210, 210, 235)),
                            (sub2, MID, H // 2 + 50, (150, 200, 210))):
        if text:
            d.text(((W - d.textlength(text, font=f)) / 2, y), text, font=f, fill=col)
    emit(img, n)

def on_frame(caption, tenths):
    b = st["bot"]
    if b is None or st["speed"] == "skip":
        return
    if caption:
        st["caption"] = caption
    speed = st["speed"]
    if b.v("incombat"):
        mt = b.v("mtype")
        if mt in BOSSES:
            speed = "boss"                       # bosses play out (briskly)
        elif mt not in st["seen_mon"]:
            st["seen_mon"].add(mt)
            speed = "meet"                       # a good look at each new monster
    bl = b.bottom()
    if not b.v("incombat") and any(w in bl for w in (
            "REACHES LEVEL", "SIGIL", "DOOR OPENS", "GRINDS OPEN", "ILLUSION", "RUNE FLARES", "IRON KEY",
            "CLUNK", "CLANG", "WRONG", "PASS.'", "HEART", "REALM")):
        speed = "normal"
    if speed == "fast":
        st["fastskip"] += 1
        if st["fastskip"] % 7:
            return
        n = 1
    elif speed == "boss":
        n = 2
    elif speed == "meet":
        n = 18
    else:
        n = max(2, min(tenths, 8))
    img = screen()
    d = ImageDraw.Draw(img)
    d.rectangle([0, H, W, H + BAR], fill=(24, 24, 40))
    tag = "  >>" if speed == "fast" else ""
    d.text((24, H + 12), st["caption"] + tag, font=FONT, fill=(200, 200, 230))
    emit(img, n)

class Hooked(P.Bot):
    def grind(self, d, target):
        st["speed"] = "skip"
        super().grind(d, target)
        st["speed"] = "fast"
        card("TRAINING", f"the party grinds to level {min(self.lvls())}", n=22)

    def resupply(self, t, shopping=True):
        first_raven = (t == 1 and not st.get("raven"))
        st["speed"] = "normal" if first_raven else "skip"
        if first_raven:
            st["raven"] = True
            card("RAVENMOOR", "the frontier town: finer steel, higher magic", n=24)
        super().resupply(t, shopping)
        st["speed"] = "fast"

    def run_dungeon(self, d):
        name = C.DUNGEONS[d][0].upper()
        sig = bin(self.v("sigils")).count("1")
        card(f"DUNGEON {d + 1}: {name}", f"danger {d + 1}   party level {min(self.lvls())}", f"sigils held: {sig} of 5")
        super().run_dungeon(d)

bot = Hooked(on_frame=on_frame, seed=SEED, log=lambda *a: None)
st["bot"] = bot
card("VAULTS OF KESH", "a Commodore 64 RPG - full game highlights", "levels, six dungeons, two towns", n=35)
st["speed"] = "normal"
bot.c.key('C')
on_frame("C  the character sheet", 30)
bot.c.key('X')
on_frame("", 4)
st["speed"] = "fast"
P.run(bot)
st["speed"] = "normal"
card("THE END", f"{bot.battles} battles, party level {min(bot.lvls())}", "every frame from the emulated C64", n=40)
ff.stdin.close()
ff.wait()
print("wrote", OUT, "frames", st["frames"], f"({st['frames'] / FPS / 60:.1f} min)", "battles", bot.battles)
