# DPL footage layer, parameterised. Grades Mixkit clips into a loop-matched 240-frame base/.
import os, shutil, subprocess, sys, json

FPS, NF = 30, 240
GRADE = ("scale=-2:1920:flags=lanczos,crop=1080:1920,"
         "eq=saturation=0.54:contrast=1.30:gamma=1.04:brightness=0.045,"
         "colorbalance=rs=0.04:rm=0.07:rh=0.05:gm=0.01:bm=-0.05:bh=-0.07,"
         "unsharp=5:5:0.8:5:5:0.0,vignette=PI/4.5,fps=30")

def zoom(rate):
    return (f"zoompan=z='min(1+{rate}*on,1.12)':d=1:"
            "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps=30")

def make_plan(cuts):
    a, b, c, d = cuts
    tail = NF - (a + b + c + d)
    assert tail > 1, cuts
    return ([("A", i) for i in range(1, a + 1)]
            + [("B", i) for i in range(1, b + 1)]
            + [("C", i) for i in range(1, c + 1)]
            + [("D", i) for i in range(1, d + 1)]
            + [("A", i) for i in range(tail, 0, -1)])

def fetch(mid):
    p = f"src/{mid}.mp4"
    if not os.path.exists(p):
        os.makedirs("src", exist_ok=True)
        subprocess.run(["curl", "-sS", "-o", p,
                        f"https://assets.mixkit.co/videos/{mid}/{mid}-720.mp4"], check=True)
    return p

def main(cfgpath):
    cfg = json.load(open(cfgpath))
    SHOTS = cfg["shots"]
    PLAN = make_plan(cfg.get("cuts", [18, 44, 67, 69]))
    for name in ("A", "B", "C", "D"):
        mid, ss, n, rate = SHOTS[name]
        src = fetch(mid)
        d = f"work/sh/{name}"
        shutil.rmtree(d, ignore_errors=True); os.makedirs(d, exist_ok=True)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(ss), "-i", src,
                        "-vf", f"{GRADE},{zoom(rate)}", "-frames:v", str(n),
                        f"{d}/f_%04d.png"], check=True)
        got = len(os.listdir(d))
        assert got == n, f"{name}: wanted {n} frames, got {got}"
    assert len(PLAN) == NF, len(PLAN)
    assert PLAN[0] == PLAN[-1], "loop broken: closing frame must be the opening frame"
    shutil.rmtree("base", ignore_errors=True); os.makedirs("base")
    for n, (s, i) in enumerate(PLAN):
        shutil.copy(f"work/sh/{s}/f_{i:04d}.png", f"base/b_{n:04d}.png")
    print(f"base/ {len(PLAN)} frames, loop anchored on {PLAN[0]}")

if __name__ == "__main__":
    main(sys.argv[1])
