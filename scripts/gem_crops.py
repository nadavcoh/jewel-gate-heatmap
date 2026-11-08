#!/usr/bin/env python3
"""Crop the gem artwork from one or more screenshots and build a verify widget: each crop beside its gem list.

Usage: python3 gem_crops.py IMG1.png [IMG2.png ...] [--outdir out]
Writes out/gem_crops_widget.html (inline widget fragment: tiny 1-bit PNG crops as data URIs, each next to the
level's gem list with sizes) and out/gems_all_boards.png (one composite image, for a file download).
The user asked for this ("crop the gems and show them next to the detected list so I can verify"). Rows are
sorted by level. The list comes from levels/levels.json, so sizes are always written out.
Paste the widget fragment into the inline visual tool (it is ~7 KB for five boards).
"""
import argparse, base64, io, os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve, read_board

BOX = (415, 470, 710, 725)          # artwork crop, fits all five levels
WIDE = (380, 450, 745, 740)

def level_of(a):
    blk = a[read_board.Y0:read_board.Y1].astype(int).sum(axis=2) < 120
    n = len(read_board.peaks(blk.sum(axis=0), 300)) - 1
    return next((l for l in solve.load_levels() if l["cols"] == n), None)

def crop_b64(im):
    c = im.convert("RGB").crop(BOX)
    m = c.convert("L").point(lambda p: 1 if p > 60 else 0)
    p = Image.new("P", c.size)
    p.putpalette([0, 0, 0, 214, 0, 255] + [0] * 762)
    p.putdata(list(m.getdata()))
    b = io.BytesIO(); p.save(b, "PNG", optimize=True, bits=1)
    return base64.b64encode(b.getvalue()).decode()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--outdir", default="gem_crops_out")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    rows = []
    for path in a.images:
        im = Image.open(path)
        lv = level_of(np.array(im.convert("RGB")))
        if not lv:
            print("skip (no matching level):", path); continue
        rows.append((lv, im))
    rows.sort(key=lambda t: t[0]["level"])
    css = ('<style>.r{display:flex;gap:12px;align-items:center;padding:10px 0;border-bottom:0.5px solid var(--border);}.r:last-child{border-bottom:none;}'
           '.r img{width:150px;height:auto;flex:none;border-radius:8px;image-rendering:pixelated;background:#000;}'
           '.r b{font-weight:500;font-size:15px;display:block;margin-bottom:4px;}'
           '.r ul{margin:0;padding:0;list-style:none;font-size:13px;line-height:1.6;color:var(--text-secondary);}</style>')
    h = ['<h2 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);">Gem artwork cropped from each screenshot, each next to its gem list with sizes.</h2>', css, "<div>"]
    for lv, im in rows:
        li = "".join(f"<li>{g['count']} {g['class']}{'s' if g['count']>1 else ''}, {g['size'][0]}x{g['size'][1]}</li>" for g in lv["gems"])
        h.append(f'<div class="r"><img alt="level {lv["level"]} gems" src="data:image/png;base64,{crop_b64(im)}"><div><b>Level {lv["level"]} ({lv["rows"]}x{lv["cols"]})</b><ul>{li}</ul></div></div>')
    h.append("</div>")
    open(os.path.join(a.outdir, "gem_crops_widget.html"), "w").write("\n".join(h))
    W, H = WIDE[2] - WIDE[0], WIDE[3] - WIDE[1]; sc, pad = 2, 60
    cols = 2; nr = (len(rows) + 1) // 2
    comp = Image.new("RGB", (W * sc * cols, (H * sc + pad) * nr), (0, 0, 0)); d = ImageDraw.Draw(comp)
    for i, (lv, im) in enumerate(rows):
        x, y = (i % cols) * W * sc, (i // cols) * (H * sc + pad)
        d.text((x + 20, y + 10), f"Level {lv['level']} ({lv['rows']}x{lv['cols']})", fill=(255, 245, 0))
        comp.paste(im.convert("RGB").crop(WIDE).resize((W * sc, H * sc), Image.NEAREST), (x, y + pad))
    comp.save(os.path.join(a.outdir, "gems_all_boards.png"))
    print("wrote", os.path.join(a.outdir, "gem_crops_widget.html"), "and gems_all_boards.png for levels", [l["level"] for l, _ in rows])

if __name__ == "__main__":
    main()
