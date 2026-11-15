#!/usr/bin/env python3
"""Verify widget for several screenshots: each crop (colour-true, drawn from a run-length pixel map) next to its
gem list with sizes and the found count.  analyze.py already includes this crop in its widget, so use this
script only when the user sends many boards and wants the crops of all of them together.

Usage: python3 gem_crops.py IMG1.png [IMG2.png ...] [--outdir out]
Writes out/gem_crops_widget.html (paste verbatim into the inline visual tool) and out/crop_<name>.png previews.
"""
import argparse, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screen, solve, widget

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("images", nargs="+")
    ap.add_argument("--outdir", default="gem_crops_out")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    items = []
    for p in a.images:
        res = screen.read(p)
        if "error" in res:
            print("skip:", p, res["error"]); continue
        items.append((res, p))
    items.sort(key=lambda t: t[0]["level"])
    parts = ['<h2 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);">Gem artwork cropped from each screenshot next to its gem list with sizes and found count.</h2>', widget.CSS]
    for i, (res, p) in enumerate(items):
        level = next(l for l in solve.load_levels() if l["level"] == res["level"])
        arr = screen.load(p)
        cr = screen.crop_rle(arr, res["sprites"]); screen.decode_rle(cr)
        cr["preview"].save(os.path.join(a.outdir, f"crop_{os.path.splitext(os.path.basename(p))[0]}.png"))
        parts.append(widget.crop_block(f"cv{i}", cr, level, widget.gem_rows(level, res["sprites"]), f"level {level['level']} gems"))
    html = "\n".join(parts)
    open(os.path.join(a.outdir, "gem_crops_widget.html"), "w").write(html)
    print(f"wrote {a.outdir}/gem_crops_widget.html ({len(html)} chars) for levels {[r['level'] for r, _ in items]}")

if __name__ == "__main__":
    main()
