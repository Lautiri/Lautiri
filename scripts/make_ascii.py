"""One-off: turns the portfolio robot into coloured ASCII (assets/robot.json). Needs Pillow; the daily
build (build_card.py) only reads the JSON, so the GitHub Action stays stdlib only.

    python make_ascii.py <robot.png> <out.json> [cols]
"""
import colorsys
import json
import sys

from PIL import Image

RAMP = " .:-=+*#%@"  # light to dense
src, out = sys.argv[1], sys.argv[2]
cols = int(sys.argv[3]) if len(sys.argv) > 3 else 64
img = Image.open(src).convert("RGB")
w, h = img.size
rows = round(h / w * cols * 0.5)  # mono glyphs are about twice as tall as wide
small = img.resize((cols, rows), Image.LANCZOS)


def classify(r, g, b):
    hh, ll, ss = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if ss < 0.15 and ll > 0.5:
        return None  # the grey studio background
    if hh > 0.42 and hh < 0.58 and ss > 0.4 and ll > 0.35:
        return "eye"
    if 0.03 < hh < 0.12 and ss > 0.45:
        return "body"
    if ll > 0.82:
        return "badge"
    return "dark"


grid = []
for y in range(rows):
    line = []
    for x in range(cols):
        r, g, b = small.getpixel((x, y))
        kind = classify(r, g, b)
        if kind is None:
            line.append([" ", ""])
            continue
        lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        if kind == "dark":
            ch = RAMP[2 + int((1 - lum) * 3.99)]  # dark parts: : - = +
        elif kind == "eye":
            ch = "@"
        elif kind == "badge":
            ch = "#"
        else:
            ch = RAMP[4 + int(lum * 5.99)]  # orange shading: + * # % @
        line.append([ch, kind])
    grid.append(line)
# trim empty rows top and bottom
while grid and all(c == " " for c, _ in grid[0]):
    grid.pop(0)
while grid and all(c == " " for c, _ in grid[-1]):
    grid.pop()
json.dump({"cols": cols, "rows": len(grid), "grid": grid}, open(out, "w"), separators=(",", ":"))
print(len(grid), "rows")
for line in grid:
    print("".join(c for c, _ in line))
