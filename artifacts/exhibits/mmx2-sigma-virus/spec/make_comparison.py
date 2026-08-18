"""Reference beside render, both at the same head height, for the eyeball half of acceptance.

The gates score numbers; this is the "show, don't tell" half. Both panels are scaled so the
head measures the same height, because a comparison at native resolution compares two different
sizes and reads every proportion wrong.

Usage: python3 make_comparison.py <render.png> <sheet.png> <out.png> [--height 900]
"""
import argparse

from PIL import Image

FRONT = (63, 1811, 47, 69)          # geometry authority
GREEN = (496, 2573, 48, 69)         # colour authority
BG, TOL = (0, 0, 41), 24


def near(p, q, t):
    return all(abs(a - b) <= t for a, b in zip(p[:3], q[:3]))


def trim(im):
    px = im.load()
    bg = px[0, 0]
    xs, ys = [], []
    for yy in range(im.height):
        for xx in range(im.width):
            if not near(px[xx, yy], bg, TOL):
                xs.append(xx)
                ys.append(yy)
    return im.crop((min(xs), min(ys), max(xs) + 1, max(ys) + 1))


def scaled(im, height):
    w = max(1, round(im.width * height / im.height))
    return im.resize((w, height), Image.Resampling.NEAREST)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("render")
    ap.add_argument("sheet")
    ap.add_argument("out")
    ap.add_argument("--height", type=int, default=900)
    a = ap.parse_args()

    sheet = Image.open(a.sheet).convert("RGB")
    panels = [
        scaled(sheet.crop((GREEN[0], GREEN[1], GREEN[0] + GREEN[2], GREEN[1] + GREEN[3])), a.height),
        scaled(sheet.crop((FRONT[0], FRONT[1], FRONT[0] + FRONT[2], FRONT[1] + FRONT[3])), a.height),
        scaled(trim(Image.open(a.render).convert("RGB")), a.height),
    ]
    gap = 24
    out = Image.new(
        "RGB",
        (sum(p.width for p in panels) + gap * (len(panels) + 1), a.height + gap * 2),
        BG,
    )
    x = gap
    for p in panels:
        out.paste(p, (x, gap))
        x += p.width + gap
    out.save(a.out)
    print(a.out, out.size, "panels: green colour authority | red geometry authority | render")


main()
