# DPL reel text layer. overlay.py plus two additions:
#  1. a beat may carry an optional "ask" string, drawn as a smaller white
#     EB Garamond line (size 44) under the main copy block
#  2. DPL_PLATFORM shifts the whole text layer to that platform's safe zone
import os, sys, json, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS, NF = 1080, 1920, 30, 240
MARGIN, MAXW = 86, 908
WHITE = (242, 239, 233)
GOLD  = (224, 180, 107)          # Endurance Gold #E0B46B
F = "fonts/%s.ttf"

WORDMARK = "DISASTER-PROOF LIFE"
TAGLINE  = "BUILD. STAND. ENDURE."
HANDLE   = "@disasterprooflife"

XFADE_START, XFADE_LEN = 174, 12

ASK_Y, ASK_SIZE = 1046, 44

# --- platform safe zones, added October 18 2026 ---------------------------
# TikTok covers the bottom 484px (username, caption, sound, progress bar) and
# the right 140px (button rail), so its safe box is x 60-940, y 130-1436.
# The Instagram geometry puts the lockup at y1470 and 1538, which sits behind
# TikTok's caption block, and lets copy reach x978, which clips the rail.
# Instagram Reels is safe to y1610 and x996. X publishes no safe zone and its
# immersive viewer overlay is lighter than both, so it shares the IG geometry.
# See PLATFORM_SAFE_ZONES.md.
PLATFORMS = {
    "instagram": dict(dy=0,    maxw=908),
    "x":         dict(dy=0,    maxw=908),
    "tiktok":    dict(dy=-150, maxw=800),
}
PLATFORM = os.environ.get("DPL_PLATFORM", "instagram")
if PLATFORM not in PLATFORMS:
    raise SystemExit(f"unknown DPL_PLATFORM {PLATFORM!r}, expected one of {sorted(PLATFORMS)}")
DY   = PLATFORMS[PLATFORM]["dy"]
MAXW = PLATFORMS[PLATFORM]["maxw"]
COPY_Y    = 830  + DY
ASK_Y     = ASK_Y + DY
LOCKUP_Y  = 1470 + DY
TAGLINE_Y = 1538 + DY
POOL_Y    = 830  + DY
BAND_Y    = 1330 + DY
# ---------------------------------------------------------------------------

SCRIMS = {
    "legacy": dict(base=12.0, pool=50.0, band=92.0, wide=(24, 1.05), tight=(6, 1.6)),
    "light":  dict(base=10.0, pool=20.0, band=58.0, wide=(28, 1.30), tight=(7, 2.05)),
}
SCRIM_MODE = os.environ.get("DPL_SCRIM", "light")
S = SCRIMS[SCRIM_MODE]

def font(name, size): return ImageFont.truetype(F % name, size)

def wrap_fit(text, name, size, maxw, max_lines=2):
    while size > 20:
        f = font(name, size)
        words, lines, cur = text.split(), [], ""
        for w in words:
            t = (cur + " " + w).strip()
            if f.getlength(t) <= maxw or not cur:
                cur = t
            else:
                lines.append(cur); cur = w
        if cur: lines.append(cur)
        if len(lines) <= max_lines and all(f.getlength(l) <= maxw for l in lines):
            return f, lines
        size -= 2
    return font(name, size), [text]

def tracked(draw, cx, cy, text, f, fill, track):
    total = sum(f.getlength(c) for c in text) + track * (len(text) - 1)
    x = cx - total / 2
    asc, desc = f.getmetrics()
    y = cy - (asc - desc) / 2 - desc
    for c in text:
        draw.text((x, y), c, font=f, fill=fill)
        x += f.getlength(c) + track

def scrim():
    y = np.arange(H, dtype=np.float32)
    a = S["base"] + S["pool"] * np.exp(-((y - POOL_Y) ** 2) / (2 * 400.0 ** 2))
    a = a + S["band"] / (1 + np.exp(-(y - BAND_Y) / 70.0))
    a = np.clip(a, 0, 150).astype(np.uint8)
    arr = np.zeros((H, W, 4), dtype=np.uint8)
    arr[..., 3] = a[:, None]
    return Image.fromarray(arr, "RGBA")

SCRIM = scrim()

def fade(n):
    o = min(1.0, max(0.0, (n - XFADE_START) / XFADE_LEN))
    i = min(1.0, max(0.0, (n - (XFADE_START + XFADE_LEN)) / XFADE_LEN))
    return round(o, 3), round(i, 3)

def load_beats(cfgpath):
    cfg = json.load(open(cfgpath))
    out = []
    for b in cfg["beats"]:
        out.append(dict(a=b["a"], b=b["b"], text=b["text"],
                        color=GOLD if b.get("gold") else WHITE,
                        size=b["size"], weight=b.get("weight", 600),
                        ask=b.get("ask")))
    return out, cfg

def beat_for(n, BEATS):
    for i, b in enumerate(BEATS):
        if b["a"] <= n <= b["b"]: return i, b
    raise ValueError(n)

def ink_layer(n, BEATS):
    i, b = beat_for(n, BEATS)
    ink = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ink)

    f, lines = wrap_fit(b["text"], f"EBG-{b['weight']}", b["size"], MAXW)
    lead = int(f.size * 1.24)
    top = COPY_Y - (len(lines) * lead) / 2
    for k, ln in enumerate(lines):
        d.text((W / 2, top + k * lead + lead / 2), ln, font=f, fill=b["color"], anchor="mm")

    if b.get("ask"):
        af, alines = wrap_fit(b["ask"], "EBG-600", ASK_SIZE, MAXW, max_lines=1)
        d.text((W / 2, ASK_Y), alines[0], font=af, fill=WHITE, anchor="mm")

    tracked(d, W / 2, LOCKUP_Y, WORDMARK, font("Mont-700", 33), WHITE, 7)
    out_t, in_t = fade(n)
    if out_t < 1.0:
        tracked(d, W / 2, TAGLINE_Y, TAGLINE, font("Mont-500", 26), GOLD + (int(255 * (1 - out_t)),), 6)
    if in_t > 0.0:
        tracked(d, W / 2, TAGLINE_Y, HANDLE, font("Mont-700", 30), GOLD + (int(255 * in_t),), 3)
    return ink

def build(n, BEATS):
    ink = ink_layer(n, BEATS)
    a = ink.split()[3]
    wb, wm = S["wide"]; tb, tm = S["tight"]
    wide = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    wide.putalpha(a.filter(ImageFilter.GaussianBlur(wb)).point(lambda v: int(min(255, v * wm))))
    tight = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    tight.putalpha(a.filter(ImageFilter.GaussianBlur(tb)).point(lambda v: int(min(255, v * tm))))
    out = Image.alpha_composite(SCRIM, wide)
    out = Image.alpha_composite(out, tight)
    return Image.alpha_composite(out, ink)

if __name__ == "__main__":
    import subprocess
    cfgpath = sys.argv[1]
    BEATS, cfg = load_beats(cfgpath)
    cache = {}

    def frame(n):
        i, _ = beat_for(n, BEATS)
        key = (i, fade(n))
        if key not in cache: cache[key] = build(n, BEATS)
        base = Image.open(f"base/b_{n:04d}.png").convert("RGBA")
        return Image.alpha_composite(base, cache[key]).convert("RGB")

    if len(sys.argv) > 3 and sys.argv[2] == "frame":
        n = int(sys.argv[3]); frame(n).save(sys.argv[4]); print("wrote", sys.argv[4]); raise SystemExit

    out = cfg["out"]
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    p = subprocess.Popen([
        "ffmpeg", "-v", "error", "-y",
        "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
        "-an", "-c:v", "libx264", "-preset", "slow", "-crf", "17",
        "-pix_fmt", "yuv420p", "-profile:v", "high", "-level", "4.1",
        "-movflags", "+faststart", "-g", "30", out], stdin=subprocess.PIPE)
    for n in range(NF):
        p.stdin.write(frame(n).tobytes())
    p.stdin.close(); p.wait()
    print(f"wrote {out} rc {p.returncode} | scrim={SCRIM_MODE} | platform={PLATFORM} | overlays {len(cache)}")
