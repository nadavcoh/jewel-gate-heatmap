#!/usr/bin/env python3
"""Shared screenshot reader for Jewel Gate (iPhone portrait, 1125x2436).

Everything here was verified on 14 real screenshots (levels 1-3, blank and partly dug boards).
What changed versus the first reader (see references/lessons.md, "Auto reader"):
 - Level comes from the GREEN CHECK MARKS in the progress bar (level = checks + 1), not from counting grid
   lines. The old projection of black pixels breaks as soon as a cell is dug: a black block adds hundreds of
   black pixels to every column it spans, so lines merged and boards were read as 3x4, 2x2 or 7x6.
 - Grid lines are then FIXED per level (GEOM). Cells are sampled in an inner window.
 - Sprite colours: hidden = (214,0,255). ANY other colour is a found gem. Found colours seen: teal (0,255,210),
   red (255,0,111), green (0,255,4), violet (173,84,255). The violet tall of level 2 used to be missed because
   it looked "magenta" to the old mask.
 - The artwork crop is encoded as a run-length pixel map (see crop_rle) that is drawn on a canvas; far safer to
   paste than a base64 PNG (one wrong character in base64 turns the whole image black).
"""
import os, sys, json, collections
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve

# level: (x0, x1, y0, y1, n) outer grid lines in px and cells per side. Measured on real screenshots.
GEOM = {1: (140, 984, 1180, 2024, 4), 2: (140, 984, 1180, 2024, 5), 3: (140, 984, 1180, 2024, 6),
        4: (119, 1005, 1159, 2045, 7), 5: (112, 1012, 1152, 2052, 8)}
CHECK_X = (242, 404, 566, 728)           # progress-bar slots, check mark = green pixels
HIDDEN = (214, 0, 255)
ART = (425, 440, 705, 740)               # x0, y0, x1, y1 of the gem artwork (decoration blobs sit outside it)
CROP = (415, 470, 711, 726)              # default crop, 296x256 = 74x64 blocks of 4 px
NAMES = {(0, 255, 210): "teal", (255, 0, 111): "red", (0, 255, 4): "green", (173, 84, 255): "violet", (19, 147, 255): "blue", HIDDEN: "magenta"}
LETTERS = {HIDDEN: "M", (173, 84, 255): "V", (0, 255, 210): "T", (255, 0, 111): "R", (0, 255, 4): "G", (19, 147, 255): "B"}
SPARE = list("ABCDEFHIJLNOPQSUWXYZ")

def load(path):
    return np.array(Image.open(path).convert("RGB"))

def count_checks(a):
    n = 0
    for cx in CHECK_X:
        b = a[825:900, cx - 45:cx + 45].astype(int)
        n += int(((b[:, :, 1] > 180) & (b[:, :, 0] < 140) & (b[:, :, 2] < 90)).sum() > 300)
    return n

def level_of(a):
    return count_checks(a) + 1

def lines(level):
    x0, x1, y0, y1, n = GEOM[level]
    return [round(x0 + (x1 - x0) * i / n) for i in range(n + 1)], [round(y0 + (y1 - y0) * i / n) for i in range(n + 1)], n

def read_cells(a, level):
    """Return (dug, hits) as lists of 'r<row>c<col>'. dug = solid black cell (empty dig or part of a found gem)."""
    xs, ys, n = lines(level)
    dug, hits = [], []
    for r in range(n):
        for c in range(n):
            mx, my = (xs[c + 1] - xs[c]) // 4, (ys[r + 1] - ys[r]) // 4
            cell = a[ys[r] + my:ys[r + 1] - my, xs[c] + mx:xs[c + 1] - mx].astype(int)
            dark = (cell.sum(axis=2) < 120).mean()
            pur = ((cell[:, :, 0] > 140) & (cell[:, :, 2] > 200) & (cell[:, :, 1] < 140)).mean()   # magenta (214,0,255) and the violet (173,84,255) a partly revealed tall shows on black
            lab = f"r{r+1}c{c+1}"
            if pur > 0.08 and dark + pur > 0.8:
                hits.append(lab)             # purple/violet sprite on black = revealed part of a still-hidden gem (seen on level 4: tall crystal, 2 of 3 cells dug)
            elif dark > 0.8:
                dug.append(lab)
    return dug, hits

def classify(w, h, area):
    if area > 7000: return "octagon"
    if 3800 < area < 5200 and 45 < min(w, h) < 70: return "hex"
    if area < 1100 and 0.8 < w / h < 1.25: return "diamond"
    if 2200 < area < 4100 and w < 45 and h > 2 * w: return "tall"
    if 2200 < area < 4100 and h < 45 and w > 2 * h: return "flat"
    return None

def near(c, ref, tol=30):
    return all(abs(int(c[i]) - ref[i]) <= tol for i in range(3))

def sprites(a):
    x0, y0, x1, y1 = ART
    reg = a[y0:y1, x0:x1].astype(int)
    lab, _ = ndi.label(ndi.binary_closing(reg.max(axis=2) > 100, iterations=3))
    out = []
    for i, sl in enumerate(ndi.find_objects(lab), 1):
        m = lab[sl] == i
        area = int(m.sum())
        h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        cls = classify(w, h, area) if area >= 600 else None
        if not cls:
            continue
        px = reg[sl][m]
        px = px[px.max(axis=1) > 150]
        col = collections.Counter(map(tuple, px)).most_common(1)[0][0] if len(px) else (0, 0, 0)
        col = tuple(int(v) for v in col)
        out.append({"class": cls, "state": "hidden" if near(col, HIDDEN, 25) else "found", "color": col,
                    "color_name": NAMES.get(col, "other"), "w": w, "h": h, "area": area,
                    "box": [sl[1].start + x0, sl[0].start + y0, sl[1].stop + x0, sl[0].stop + y0]})
    return sorted(out, key=lambda s: (s["box"][1], s["box"][0]))

def read(path):
    a = load(path)
    lv = level_of(a)
    res = {"file": os.path.basename(path), "checks": lv - 1, "level": lv}
    if lv not in GEOM:
        res["error"] = f"{lv - 1} check marks gives level {lv}, which has no geometry"
        return res
    res["dug"], res["hits"] = read_cells(a, lv)
    res["sprites"] = sprites(a)
    level = next(l for l in solve.load_levels() if l["level"] == lv)
    res["rows"] = res["cols"] = level["rows"]
    pool = {g["class"]: g["size"] for g in level["gems"]}
    res["found"] = sorted(s["class"] for s in res["sprites"] if s["state"] == "found")
    res["hidden"] = sorted(s["class"] for s in res["sprites"] if s["state"] == "hidden")
    want = sorted(g["class"] for g in level["gems"] for _ in range(g["count"]))
    res["sprites_match_level"] = sorted(res["found"] + res["hidden"]) == want
    fc = sum(pool[c][0] * pool[c][1] for c in res["found"] if c in pool)
    res["found_cells"] = fc
    res["empty_digs"] = len(res["dug"]) - fc
    return res

def crop_rle(a, sprs=None):
    """Colour-true 4x downscaled artwork as run-length rows. Returns dict(w, h, rle, palette, preview).
    Letters: K black, M hidden magenta, V violet, T teal, R red, G green (others from a spare pool).
    Palette colours are the exact colours measured in the full-resolution crop, so they match the original."""
    x0, y0, x1, y1 = CROP
    if sprs:
        bx = [s["box"] for s in sprs]
        x0, y0 = min(x0, min(b[0] for b in bx) - 8), min(y0, min(b[1] for b in bx) - 8)
        x1, y1 = max(x1, max(b[2] for b in bx) + 8), max(y1, max(b[3] for b in bx) + 8)
    x1, y1 = x0 + 4 * ((x1 - x0 + 3) // 4), y0 + 4 * ((y1 - y0 + 3) // 4)
    c = a[y0:y1, x0:x1].astype(int)
    bright = c.max(axis=2) >= 120
    cnt = collections.Counter(map(tuple, c[bright]))
    pal = [(k, v) for k, v in cnt.most_common() if v >= 150]
    if not pal:
        pal = [(HIDDEN, 1)]
    cols = [np.array(k) for k, _ in pal]
    idx = np.zeros(c.shape[:2], dtype=int)             # 0 = black, i+1 = palette colour i
    ys, xs = np.where(bright)
    d = np.stack([((c[ys, xs] - col) ** 2).sum(axis=1) for col in cols], axis=1)
    idx[ys, xs] = d.argmin(axis=1) + 1
    H, W = (y1 - y0) // 4, (x1 - x0) // 4
    letter, spare = {}, list(SPARE)
    for i, (k, _) in enumerate(pal, 1):
        near_k = next((kk for kk in LETTERS if near(k, kk, 6)), None)
        letter[i] = LETTERS[near_k] if near_k else spare.pop(0)
    letter[0] = "K"
    rows, prev = [], np.zeros((H, W, 3), dtype=np.uint8)
    for by in range(H):
        s = ""
        for bx in range(W):
            blk = idx[by * 4:by * 4 + 4, bx * 4:bx * 4 + 4].ravel()
            nz = blk[blk > 0]
            v = 0
            if len(nz) >= 6:
                v = int(np.bincount(nz).argmax())
            s += letter[v]
            if v:
                prev[by, bx] = pal[v - 1][0]
        out, i = "", 0
        while i < len(s):
            j = i
            while j < len(s) and s[j] == s[i]: j += 1
            out += s[i] + (str(j - i) if j - i > 1 else ""); i = j
        rows.append(out)
    palette = {letter[i]: "#%02x%02x%02x" % tuple(int(v) for v in pal[i - 1][0]) for i in range(1, len(pal) + 1)}
    return {"w": W, "h": H, "rle": "|".join(rows), "palette": palette,
            "preview": Image.fromarray(prev).resize((W * 4, H * 4), Image.NEAREST)}

def crop_js(cid, cr):
    """JS that draws the RLE crop on <canvas id=cid>. Copy the string verbatim from the script output."""
    pal = json.dumps(cr["palette"], separators=(",", ":")).replace('"', "'")
    return ("const S%s=\"%s\",P%s=%s;const x%s=document.getElementById('%s').getContext('2d');"
            "S%s.split('|').forEach((row,y)=>{let x=0;(row.match(/[A-Z]\\d*/g)||[]).forEach(t=>{const n=t.length>1?+t.slice(1):1;"
            "if(P%s[t[0]]){x%s.fillStyle=P%s[t[0]];x%s.fillRect(x,y,n,1);}x+=n;});});"
            % (cid, cr["rle"], cid, pal, cid, cid, cid, cid, cid, cid, cid))

def decode_rle(cr):
    """Inverse of crop_rle, used by the self test to prove the string decodes to the preview."""
    import re
    W, H = cr["w"], cr["h"]
    img = np.zeros((H, W, 3), dtype=np.uint8)
    for y, row in enumerate(cr["rle"].split("|")):
        x = 0
        for ch, n in re.findall(r"([A-Z])(\d*)", row):
            n = int(n) if n else 1
            hexc = cr["palette"].get(ch)
            if hexc:
                img[y, x:x + n] = [int(hexc[i:i + 2], 16) for i in (1, 3, 5)]
            x += n
        assert x == W, f"row {y} decodes to {x} px, expected {W}"
    assert len(cr["rle"].split("|")) == H
    return img
