#!/usr/bin/env python3
"""Overlay and difference images for the FF7 menu UI recreation.

    python3 tools/ff7_overlay.py \
      --reference artifacts/ff7-ui-reference.png \
      --current   artifacts/ff7-ui-current.png \
      --overlay   artifacts/ff7-ui-overlay.png \
      --diff      artifacts/ff7-ui-diff.png

The overlay is the recreation drawn at 50% over the reference crop, which is what
makes a box sitting a few pixels off readable at a glance. The diff is the per
pixel absolute difference, amplified, so a wrong colour shows up even where the
geometry lines up. Both are written at the reference resolution; a capture that
comes back at a different size is reported and rescaled with NEAREST rather than
silently resampled, because a smooth resample would blur away exactly the pixel
level error the comparison exists to find.
"""

import argparse
import json
import sys

from PIL import Image, ImageChops


def load(path, size=None):
    image = Image.open(path).convert("RGB")
    if size and image.size != size:
        print(f"  {path} is {image.size}, rescaling to {size} (NEAREST)", file=sys.stderr)
        image = image.resize(size, Image.Resampling.NEAREST)
    return image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", required=True)
    parser.add_argument("--current", required=True)
    parser.add_argument("--overlay", required=True)
    parser.add_argument("--diff", required=True)
    parser.add_argument("--amplify", type=float, default=3.0)
    args = parser.parse_args()

    reference = load(args.reference)
    current = load(args.current, reference.size)

    Image.blend(reference, current, 0.5).save(args.overlay)

    # Per pixel delta collapsed to the worst channel, then amplified into a grey
    # image: the eye picks a bright patch out of black far faster than it picks a
    # subtle hue shift out of two side by side screenshots.
    delta = ImageChops.difference(reference, current)
    worst_channel = delta.convert("RGB").split()
    grey = ImageChops.lighter(ImageChops.lighter(*worst_channel[:2]), worst_channel[2])
    grey.point(lambda v: min(255, int(v * args.amplify))).save(args.diff)

    values = grey.tobytes()
    width, height = reference.size
    print(
        json.dumps(
            {
                "size": [width, height],
                "meanChannelDelta": round(sum(values) / len(values), 2),
                "maxChannelDelta": max(values),
                "overlay": args.overlay,
                "diff": args.diff,
            }
        )
    )


if __name__ == "__main__":
    main()
