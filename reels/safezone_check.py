# Fails the build if any glyph, on any frame of the reel, falls outside the
# safe box for DPL_PLATFORM. Frame count comes from the config's optional
# "frames" key, default 240. See PLATFORM_SAFE_ZONES.md.
import os, sys, importlib.util, numpy as np

SAFE = {                      # x0, x1, y0, y1
    "instagram": (0,  996, 210, 1610),
    "x":         (0,  996, 210, 1610),
    "tiktok":    (60, 940, 130, 1436),
}

spec = importlib.util.spec_from_file_location("ov", "overlay_ask.py")
ov = importlib.util.module_from_spec(spec); spec.loader.exec_module(ov)

cfgpath = sys.argv[1]
BEATS, cfg = ov.load_beats(cfgpath)
NF = ov.frames_for(cfg)
x0, x1, y0, y1 = SAFE[ov.PLATFORM]

rows, cols = [], []
for n in range(NF):
    a = np.array(ov.ink_layer(n, BEATS, NF).split()[3])
    ys, xs = np.nonzero(a > 8)
    rows += [ys.min(), ys.max()]; cols += [xs.min(), xs.max()]

r0, r1, c0, c1 = min(rows), max(rows), min(cols), max(cols)
print(f"{ov.PLATFORM}: {NF} frames | ink rows {r0}-{r1} cols {c0}-{c1} | safe x{x0}-{x1} y{y0}-{y1}")

bad = []
if c0 < x0: bad.append(f"copy reaches x{c0}, left limit {x0}")
if c1 > x1: bad.append(f"copy reaches x{c1}, right limit {x1}")
if r0 < y0: bad.append(f"copy reaches y{r0}, top limit {y0}")
if r1 > y1: bad.append(f"copy reaches y{r1}, bottom limit {y1}")
if bad:
    print("SAFE ZONE FAILED: " + "; ".join(bad)); sys.exit(1)
print("safe zone clear")
