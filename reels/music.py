# DPL music layer. Adds a Mixkit music bed to a finished silent reel.
# Video stream is copied untouched, so every video measurement still holds.
#
# Config key (optional):
#   "music": {"mixkit": 614, "start": 70.24, "title": "Silent Descent"}
# Mixkit Stock Music Free License: commercial use and social media allowed, no attribution.
#
# Usage: python3 music.py cfg.json in.mp4 out.mp4
import json, os, subprocess, sys

DUR = 8.0
FADE_OUT = 0.6

def fetch(mid):
    os.makedirs("music", exist_ok=True)
    p = f"music/{mid}.mp3"
    if not os.path.exists(p):
        subprocess.run(["curl", "-sSfL", "-o", p,
                        f"https://assets.mixkit.co/music/{mid}/{mid}.mp3"], check=True)
    return p

def main(cfgpath, src, dst):
    m = json.load(open(cfgpath)).get("music")
    if not m:
        print("no music in config, leaving reel silent")
        if src != dst:
            subprocess.run(["cp", src, dst], check=True)
        return
    mp3 = fetch(m["mixkit"])
    start = float(m.get("start", 0))
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11,aresample=48000,"
          f"afade=t=in:st=0:d=0.05,afade=t=out:st={DUR - FADE_OUT}:d={FADE_OUT}")
    tmp = dst + ".tmp.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y",
                    "-i", src, "-ss", str(start), "-t", str(DUR), "-i", mp3,
                    "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy",
                    "-af", af, "-c:a", "aac", "-b:a", "192k", "-ac", "2",
                    "-t", str(DUR), "-movflags", "+faststart", tmp], check=True)
    os.replace(tmp, dst)
    print(f"music: Mixkit {m['mixkit']} {m.get('title', '')} from {start}s, "
          f"normalised to -14 LUFS, {FADE_OUT}s fade out -> {dst}")

if __name__ == "__main__":
    main(*sys.argv[1:4])
