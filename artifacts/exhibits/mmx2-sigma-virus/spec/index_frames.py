"""Index every animation frame on the sprite sheet.

The sheet is a wireframe turntable of two different heads in four palettes. Eyeballing
which frame is a side view does not scale to ~340 frames, so segment them all and let
the numbers pick: connected-component labelling on the non-background pixels, then a
bbox + dominant hue + aspect ratio per frame.

Usage: python3 index_frames.py <sheet.png> <out.json>
"""
import json
import sys
from collections import Counter, deque

from PIL import Image

BG = (0, 0, 41)
BG_TOL = 24
MIN_PX = 60          # drops the tail-end frames that shrink to a few pixels


def is_bg(p):
    return all(abs(a - b) <= BG_TOL for a, b in zip(p, BG))


def hue_family(p):
    r, g, b = p
    if g > r + 40 and g > b + 40:
        return "green"
    if r > g + 40 and b > g + 40:
        return "purple"
    if r > g + 40 and r > b + 40:
        return "orange" if g > 60 else "red"
    if b > r + 40 and b > g + 20:
        return "blue"
    return "other"


def main():
    sheet, out = sys.argv[1], sys.argv[2]
    im = Image.open(sheet).convert("RGB")
    px = im.load()
    W, H = im.size

    # 8-connectivity with a 2px bridge: the wireframe strokes are 1px and the dashed
    # hidden-line segments break contact, so pure 4-connectivity shatters one head into
    # a dozen fragments. The bridge is the smallest radius that keeps a head whole.
    seen = [[False] * W for _ in range(H)]
    nbr = [(dx, dy) for dx in range(-2, 3) for dy in range(-2, 3) if (dx, dy) != (0, 0)]
    frames = []
    for sy in range(H):
        for sx in range(W):
            if seen[sy][sx] or is_bg(px[sx, sy]):
                continue
            q = deque([(sx, sy)])
            seen[sy][sx] = True
            pts, cols = [], Counter()
            while q:
                x, y = q.popleft()
                pts.append((x, y))
                cols[hue_family(px[x, y])] += 1
                for dx, dy in nbr:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < W and 0 <= ny < H and not seen[ny][nx] and not is_bg(px[nx, ny]):
                        seen[ny][nx] = True
                        q.append((nx, ny))
            if len(pts) < MIN_PX:
                continue
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            w, h = max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
            structural = Counter({k: v for k, v in cols.items()
                                  if k in ("blue", "red", "orange", "green")})
            frames.append({
                "x0": min(xs), "y0": min(ys), "w": w, "h": h,
                "strokePx": len(pts),
                "aspect": round(w / h, 4),
                "hue": structural.most_common(1)[0][0] if structural else "other",
                "accents": [k for k, _ in cols.most_common() if k not in ("other",)][1:3],
            })

    frames.sort(key=lambda f: (f["y0"], f["x0"]))
    rec = {"sheet": sheet, "sheetSize": [W, H], "frameCount": len(frames), "frames": frames}
    with open(out, "w") as f:
        json.dump(rec, f, indent=1)

    by_hue = Counter(f["hue"] for f in frames)
    print(f"{len(frames)} frames  hues={dict(by_hue)}")
    for hue in ("red", "orange"):
        sub = [f for f in frames if f["hue"] == hue and f["strokePx"] > 400]
        if not sub:
            continue
        sub.sort(key=lambda f: f["aspect"])
        print(f"\n{hue}: narrowest (front-ish) ->", [(f["x0"], f["y0"], f["aspect"]) for f in sub[:3]])
        print(f"{hue}: widest (side/top-ish)  ->", [(f["x0"], f["y0"], f["aspect"]) for f in sub[-3:]])


main()
