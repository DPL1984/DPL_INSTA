# Platform safe zones

Every reel is 1080x1920. What differs is how much of that frame each app covers
with its own interface. Copy placed under the interface is copy nobody reads.

Checked October 18 2026 against published 2026 specs.

| | Top | Bottom | Left | Right | Safe box |
|---|---|---|---|---|---|
| Instagram Reels | 210 | 310 | 0 | 84 | x 0-996, y 210-1610 |
| TikTok | 130 | 484 | 44 | 140 | x 60-940, y 130-1436 |
| X | not published | not published | | | lighter than both |

## What this changed

The build used one geometry for all three platforms: copy centred at y830, the
send-ask at y1046, the DPL lockup at y1470 and the tagline at y1538, with copy
reaching x978 on the widest line.

That is correct on Instagram and wrong on TikTok. **The lockup and tagline sat
behind TikTok's caption block, and the widest copy clipped the button rail.**
Every reel the account has cross-posted to TikTok has shipped with its branding
hidden.

`overlay_ask.py` now reads `DPL_PLATFORM` and shifts accordingly:

| | dy | max copy width | Lockup | Tagline | Copy centre | Ask |
|---|---|---|---|---|---|---|
| instagram | 0 | 908 | 1470 | 1538 | 830 | 1046 |
| x | 0 | 908 | 1470 | 1538 | 830 | 1046 |
| tiktok | -150 | 800 | 1320 | 1388 | 680 | 896 |

The scrim's gradient pool and lockup band shift with it, so the grade stays
matched to where the copy actually sits.

## Why X shares the Instagram geometry

X publishes no safe zone for vertical video. Its immersive viewer overlays less
of the frame than either Instagram or TikTok, so the Instagram geometry clears
it with room to spare. Making X artificially different would be invention, not
engineering. If X ever publishes a spec, this file is where it goes and
`PLATFORMS` is the one place to change.

## Verification

The build measures the ink layer across all 240 frames and fails if any glyph
falls outside that platform's safe box. Checked on Wasted years:

| | Ink rows | Ink cols | Safe box | Result |
|---|---|---|---|---|
| instagram | 736-1555 | 143-937 | y 210-1610, x 0-996 | inside |
| tiktok | 586-1405 | 143-937 | y 130-1436, x 60-940 | inside |

Sources: Cadenus TikTok safe zone 2026; Postplanify social media safe zones
2026; Moda X video sizes 2026.
