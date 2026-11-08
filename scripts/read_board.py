#!/usr/bin/env python3
"""Read a Jewel Gate screenshot automatically: board size, level, dug cells, revealed gem cells, gem sprites.

Usage: python3 read_board.py IMG.png [--json]
Needs numpy, pillow, scipy. Screenshots are iPhone portrait 1125x2436.
What it does (all verified on blank boards of levels 1-5; dug/hit detection is NOT yet verified on a dug
board, so always print and check the grid it shows):
 - counts vertical/horizontal dashed grid lines by projecting black pixels in the yellow play area
   (y 1110-2090); cells = lines - 1. This replaces counting crossings by eye.
 - maps the board size to a level (4x4=1 ... 8x8=5) and prints that level's gem table with sizes.
 - samples the centre of every cell: mostly black = dug/found, black with purple sprite = hit on a hidden gem.
 - finds sprites in the artwork (x 380-745, y 440-740): purple = hidden, any other colour = found.
Sprite classes come from bounding boxes: octagon ~101x101, diamond ~39x39, hex ~55-64 x 104, tall = narrow and
long, flat = wide and short. Sprite pixel sizes do not give the gem size in cells; sizes come from levels.json.
"""
import json, os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve

Y0, Y1 = 1110, 2090

def peaks(p, th):
    out = []
    for i in np.where(p > th)[0]:
        if out and i - out[-1][-1] <= 6:
            out[-1].append(i)
        else:
            out.append([i])
    return [int(np.mean(g)) for g in out]

def classify(w, h, area):
    if area > 7000: return "octagon"
    if 3800 < area < 5200 and 45 < min(w, h) < 70: return "hex"
    if area < 1100 and 0.8 < w / h < 1.25: return "diamond"
    if 2200 < area < 4000 and w < 45 and h > 2 * w: return "tall"
    if 2200 < area < 4000 and h < 45 and w > 2 * h: return "flat"
    return None

def sprites(a):
    reg = a[440:740, 380:745].astype(int)
    r, g, b = reg[:, :, 0], reg[:, :, 1], reg[:, :, 2]
    purple = (r > 150) & (b > 200) & (g < 80)
    magenta = (r > 100) & (b > 100) & (g < 110)           # purple/magenta family incl. anti-aliased edges
    other = ((reg.max(axis=2) - reg.min(axis=2)) > 90) & ~magenta & (reg.max(axis=2) > 120)
    out = []
    for name, m in (("purple", purple), ("found", other)):
        m = ndi.binary_closing(m, iterations=3)
        lab, n = ndi.label(m)
        for i, sl in enumerate(ndi.find_objects(lab), 1):
            h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            area = int((lab[sl] == i).sum())
            cls = classify(w, h, area) if area >= 600 else None   # dither noise forms hundreds of tiny blobs
            if cls:
                out.append({"state": "hidden" if name == "purple" else "found", "class": cls, "w": w, "h": h, "area": area})
    return out

def main():
    path = sys.argv[1]
    a = np.array(Image.open(path).convert("RGB"))
    reg = a[Y0:Y1].astype(int)
    blk = reg.sum(axis=2) < 120
    xs = peaks(blk.sum(axis=0), 300)
    ys = [y + Y0 for y in peaks(blk.sum(axis=1), 300)]
    cols, rows = len(xs) - 1, len(ys) - 1
    res = {"file": os.path.basename(path), "rows": rows, "cols": cols, "x_lines": xs, "y_lines": ys}
    lv = next((l for l in solve.load_levels() if l["rows"] == rows and l["cols"] == cols), None)
    res["level"] = lv["level"] if lv else None
    dug, hits = [], []
    for r in range(rows):
        for c in range(cols):
            cx0, cx1 = xs[c], xs[c + 1]; cy0, cy1 = ys[r], ys[r + 1]
            mx, my = (cx1 - cx0) // 4, (cy1 - cy0) // 4
            cell = a[cy0 + my:cy1 - my, cx0 + mx:cx1 - mx].astype(int)
            dark = (cell.sum(axis=2) < 120).mean()
            pur = ((cell[:, :, 0] > 150) & (cell[:, :, 2] > 200) & (cell[:, :, 1] < 80)).mean()
            lab = f"r{r+1}c{c+1}"
            if pur > 0.08 and dark + pur > 0.8:
                hits.append(lab)
            elif dark > 0.85:
                dug.append(lab)
    res["dug"], res["hits"] = dug, hits
    res["sprites"] = sprites(a)
    if "--json" in sys.argv:
        print(json.dumps(res, indent=1)); return
    print(f"{res['file']}: {rows}x{cols} board" + (f" = level {lv['level']}" if lv else " (no matching level - ask the user for gem sizes)"))
    print("Grid (. unknown, # dug/found, H hit on hidden gem):")
    for r in range(rows):
        print(f" r{r+1}  " + " ".join("H" if f"r{r+1}c{c+1}" in hits else "#" if f"r{r+1}c{c+1}" in dug else "." for c in range(cols)))
    hid = [s["class"] for s in res["sprites"] if s["state"] == "hidden"]
    fnd = [s["class"] for s in res["sprites"] if s["state"] == "found"]
    print("Hidden (purple) sprites:", ", ".join(sorted(hid)) or "none")
    print("Found (other colour) sprites:", ", ".join(sorted(fnd)) or "none")
    if lv:
        want = sorted(g["class"] for g in lv["gems"] for _ in range(g["count"]))
        have = sorted(hid + fnd)
        print("Level gem table: " + ", ".join(f"{g['count']} {g['class']} {g['size'][0]}x{g['size'][1]}" for g in lv["gems"]))
        print("Sprite count matches level table." if have == want else f"MISMATCH: level table {want} vs sprites {have}; check by eye and ask the user.")
        print(f'Draft spec: {{"level": {lv["level"]}, "dug": {json.dumps(dug)}, "hits": {json.dumps(hits)}, "found": {json.dumps(fnd)}}}')

if __name__ == "__main__":
    main()
