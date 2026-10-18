import subprocess, sys, numpy as np
W,H,FPS = 1080,1920,30
path = sys.argv[1]
p = subprocess.Popen(["ffmpeg","-v","error","-i",path,"-f","rawvideo","-pix_fmt","gray","-"],
                     stdout=subprocess.PIPE)
sz=W*H; prev=None; first=None; last=None; n=0
d_first=[]; d_all=[]
while True:
    buf=p.stdout.read(sz)
    if len(buf)<sz: break
    f=np.frombuffer(buf,dtype=np.uint8).reshape(H,W).astype(np.float32)
    if first is None: first=f.copy()
    if prev is not None:
        d=np.abs(f-prev).mean()
        d_all.append(d)
        if n<=FPS: d_first.append(d)
    prev=f; last=f.copy(); n+=1
p.stdout.close(); p.wait()
print(f"frames            {n}   duration {n/FPS:.3f}s")
print(f"opening brightness {first.mean():.0f}")
print(f"opening contrast   {first.std():.0f}")
print(f"motion, first sec  {np.mean(d_first):.2f}")
print(f"motion, whole reel {np.mean(d_all):.2f}")
print(f"loop delta         {np.abs(last-first).mean():.2f}")
