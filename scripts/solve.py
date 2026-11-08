#!/usr/bin/env python3
"""Exact hit-probability map for a hidden-shapes dig grid (Battleship-like).

Usage: python3 solve.py spec.json [--outdir out]

Prints a VALIDATION REPORT (what was read from the screenshot) and the probability
map, and writes heatmap_compact.html (use this one inline), heatmap_fragment.html, heatmap.html and result.json to --outdir.
Cell labels are 1-indexed: r<row>c<col>, e.g. r5c2 = row 5, column 2.
Rectangles are allowed in cell lists: "r2c2:r3c7" = every cell from r2c2 to r3c7.
Every target needs an explicit "size": [rows, cols]. There are NO standard gem sizes: sizes differ
per level (see levels/levels.json). Instead of typing targets, a spec may say {"level": 3} and list what
was already found with "found": ["octagon", "diamond"] (sprite classes); the solver then fills rows, cols,
targets and found_gems from levels/levels.json. Explicit "targets" always win over the level table.
"""
import argparse, json, os, re, sys
from math import comb

LEVELS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "levels", "levels.json")

def load_levels():
    return json.load(open(LEVELS_PATH))["levels"]

def target_size(t):
    if "size" not in t:
        sys.exit(f"Target {t.get('name')!r} needs \"size\": [rows, cols]. There are no standard gem sizes; "
                 "take them from levels/levels.json or ask the user.")
    return tuple(t["size"])

def apply_level(spec):
    """Fill rows/cols/targets/found_gems from the level table when spec has \"level\" and no explicit targets."""
    if "level" not in spec:
        return spec
    lv = next((l for l in load_levels() if l["level"] == int(spec["level"])), None)
    if lv is None:
        sys.exit(f"Unknown level {spec['level']!r}; levels are 1-{len(load_levels())}")
    spec.setdefault("rows", lv["rows"])
    spec.setdefault("cols", lv["cols"])
    if "targets" not in spec:
        pool = [dict(name=f"{g['class']} {i+1}", **{"class": g["class"], "size": g["size"]})
                for g in lv["gems"] for i in range(g["count"])]
        found = []
        for cls in spec.get("found", []):
            i = next((i for i, g in enumerate(pool) if g["class"] == cls), None)
            if i is None:
                sys.exit(f"'found' lists {cls!r} but level {lv['level']} has no unfound {cls} left")
            found.append(pool.pop(i))
        spec["targets"] = pool
        spec.setdefault("found_gems", found)
    return spec

def expand_cells(items, rows, cols):
    out = set()
    for it in items:
        if ":" in str(it):
            a, b = str(it).split(":", 1)
            (r1, c1), (r2, c2) = parse_cell(a, rows, cols), parse_cell(b, rows, cols)
            out |= {(r, c) for r in range(min(r1, r2), max(r1, r2) + 1) for c in range(min(c1, c2), max(c1, c2) + 1)}
        else:
            out.add(parse_cell(it, rows, cols))
    return out

def parse_cell(s, rows, cols):
    m = re.fullmatch(r"r(\d+)c(\d+)", str(s).strip().lower())
    if not m:
        sys.exit(f"Bad cell label {s!r}: use r<row>c<col>, 1-indexed (e.g. r3c2)")
    r, c = int(m[1]) - 1, int(m[2]) - 1
    if not (0 <= r < rows and 0 <= c < cols):
        sys.exit(f"Cell {s!r} is outside the {rows}x{cols} board")
    return r, c

def placements(h, w, rows, cols, rotate, blocked):
    dims = {(h, w)} | ({(w, h)} if rotate else set())
    out = []
    for hh, ww in sorted(dims):
        for r in range(rows - hh + 1):
            for c in range(cols - ww + 1):
                cells = [(r + i, c + j) for i in range(hh) for j in range(ww)]
                mask = 0
                for rr, cc in cells:
                    mask |= 1 << (rr * cols + cc)
                if not mask & blocked:
                    out.append((mask, cells))
    return out

def solve(spec):
    rows, cols = spec["rows"], spec["cols"]
    rotate = spec.get("allow_rotation", True)
    dug = expand_cells(spec.get("dug", []), rows, cols)
    hits = expand_cells(spec.get("hits", []), rows, cols)
    if dug & hits:
        sys.exit(f"Cells listed as both dug and hit: {sorted(dug & hits)}")
    bit = lambda rc: 1 << (rc[0] * cols + rc[1])
    blocked = sum(bit(c) for c in dug)
    hit_mask = sum(bit(c) for c in hits)
    free_mask = ((1 << (rows * cols)) - 1) & ~blocked

    targets = spec["targets"]
    k = sum(1 for t in targets if target_size(t) == (1, 1))
    groups = {}
    for t in targets:
        if target_size(t) == (1, 1):
            continue
        key = tuple(sorted(target_size(t))) if rotate else target_size(t)
        groups.setdefault(key, []).append(t)
    slots = []
    for key, ts in groups.items():
        pl = placements(key[0], key[1], rows, cols, rotate, blocked)
        for i in range(len(ts)):
            slots.append((pl, i > 0))
    n = len(slots)
    accW = [[0.0] * len(pl) for pl, _ in slots]
    accW1 = [[0.0] * len(pl) for pl, _ in slots]
    chosen = [0] * n
    tot = {"w": 0, "w1": 0.0}

    def rec(s, used, prev):
        if s == n:
            h = (hit_mask & ~used).bit_count()
            if h > k:
                return
            m = (free_mask & ~used).bit_count()
            w = comb(m - h, k - h)
            if not w:
                return
            w1 = w * (k - h) / (m - h) if m > h else 0.0
            tot["w"] += w
            tot["w1"] += w1
            for si in range(n):
                accW[si][chosen[si]] += w
                accW1[si][chosen[si]] += w1
            return
        pl, same = slots[s]
        for i in range(prev + 1 if same else 0, len(pl)):
            mk = pl[i][0]
            if not mk & used:
                chosen[s] = i
                rec(s + 1, used | mk, i)

    rec(0, 0, -1)
    if not tot["w"]:
        sys.exit("No layout is consistent with this input - re-check dug cells, hits and target sizes.")
    prob = {}
    for r in range(rows):
        for c in range(cols):
            if (r, c) in dug:
                continue
            if (r, c) in hits:
                prob[(r, c)] = 1.0
                continue
            cov = cov1 = 0.0
            for si, (pl, _) in enumerate(slots):
                for i, (_, cells) in enumerate(pl):
                    if (r, c) in cells:
                        cov += accW[si][i]
                        cov1 += accW1[si][i]
            prob[(r, c)] = (cov + tot["w1"] - cov1) / tot["w"]
    return prob, tot["w"], dug, hits

def lab(rc):
    return f"r{rc[0]+1}c{rc[1]+1}"

def report(spec, prob, layouts, dug, hits):
    rows, cols = spec["rows"], spec["cols"]
    L = []
    L.append("=== VALIDATION: what I read from the screenshot ===")
    L.append(f"Board: {rows} rows x {cols} columns")
    L.append("Grid (. unknown, # dug/empty, H revealed gem cell):")
    L.append("      " + " ".join(f"c{c+1}" for c in range(cols)))
    for r in range(rows):
        row = ["#" if (r, c) in dug else "H" if (r, c) in hits else "." for c in range(cols)]
        L.append(f" r{r+1}   " + "  ".join(row))
    L.append(f"Dug (empty) cells ({len(dug)}): " + (", ".join(lab(c) for c in sorted(dug)) or "none"))
    if hits:
        L.append(f"Revealed gem cells ({len(hits)}): " + ", ".join(lab(c) for c in sorted(hits)))
    L.append("Targets counted:")
    cells_total = 0
    for i, t in enumerate(spec["targets"], 1):
        a, b = target_size(t)
        cells_total += a * b
        L.append(f"  {i}. {t['name']}: {a}x{b}" + (f"  [{t['source']}]" if t.get("source") else ""))
    L.append(f"  -> {len(spec['targets'])} targets, {cells_total} target cells")
    for e in spec.get("excluded", []):
        L.append(f"Excluded: {e['name']} ({e.get('reason', 'no reason given')})")
    fg = spec.get("found_gems", [])
    if fg:
        fcells = sum(target_size(g)[0] * target_size(g)[1] for g in fg)
        empt = len(dug) - fcells
        L.append(f"Found gems ({len(fg)}): " + ", ".join(g["name"] for g in fg) + f" = {fcells} cells")
        L.append(f"Black cells {len(dug)} - found-gem cells {fcells} = {empt} empty digs"
                 + ("  <-- NEGATIVE: black cells misread or a found gem is mis-sized" if empt < 0 else ""))
    L.append(f"Rules: uniform random placement, rotation {'allowed' if spec.get('allow_rotation', True) else 'NOT allowed'}, touching allowed")
    L.append(f"Layouts counted (weighted): {layouts:,}")
    L.append("")
    L.append("=== PROBABILITY MAP (% chance each cell holds a gem) ===")
    L.append("      " + "".join(f"{'c'+str(c+1):>5}" for c in range(cols)))
    for r in range(rows):
        cells = []
        for c in range(cols):
            if (r, c) in dug:
                cells.append(f"{'##':>5}")
            elif (r, c) in hits:
                cells.append(f"{'HIT':>5}")
            else:
                cells.append(f"{100*prob[(r, c)]:5.0f}")
        L.append(f" r{r+1}   " + "".join(cells))
    cand = sorted(((p, rc) for rc, p in prob.items() if rc not in hits), reverse=True)
    L.append(f"Check: probabilities sum to {sum(prob.values()):.2f} (should equal {cells_total})")
    L.append("Top cells to dig: " + ", ".join(f"{lab(rc)} {100*p:.2f}%" for p, rc in cand[:6]))
    if cand and len(cand) > 1 and cand[0][0] - cand[1][0] < 0.005:
        L.append("Note: top cells are within 0.5 percentage points - effectively a tie.")
    return "\n".join(L), cand

def fragment(spec, prob, dug, hits, cand):
    """Heatmap HTML. Design rules learned from the user (keep them):
    - solid cell colours (no rgba on a transparent page) and text colour chosen by luminance,
      because mid-blue cells with fixed white/dark text were unreadable;
    - colour scale capped at the 90th percentile so one outlier (e.g. a 94% cell) does not wash out the rest;
    - every tied-best cell gets the solid outline, near ties (<0.5 pt) a dashed one;
    - dug/black cells are blank neutral, revealed gem cells amber with 'gem'."""
    rows, cols = spec["rows"], spec["cols"]
    vals = sorted(p for rc, p in prob.items() if rc not in hits)
    lo_v = vals[0] if vals else 0.0
    hi_v = vals[min(len(vals) - 1, int(0.9 * len(vals)))] if vals else 1.0
    if hi_v - lo_v < 1e-9:
        hi_v = lo_v + 1e-9
    span = hi_v - lo_v
    lo, hi = (230, 241, 251), (12, 68, 124)
    best = cand[0][1] if cand else None
    tied = {rc for p, rc in cand if cand[0][0] - p < 0.0005}
    near = {rc for p, rc in cand if 0.0005 <= cand[0][0] - p < 0.005}
    base = "aspect-ratio:1;border-radius:6px;display:flex;align-items:center;justify-content:center;box-sizing:border-box;"
    muted = "font:12px system-ui,sans-serif;color:var(--text-muted,#898781);text-align:center;"
    fs = 15 if cols <= 7 else 13
    h = [f'<h2 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);">Heatmap of hit probability on a {rows} by {cols} board; best square {lab(best) if best else "none"}.</h2>',
         '<div style="padding:.5rem 0;">',
         f'<div style="display:grid;grid-template-columns:18px repeat({cols},minmax(0,1fr));gap:3px;align-items:center;">',
         f'<div style="{muted}"></div>' + "".join(f'<div style="{muted}">c{c+1}</div>' for c in range(cols))]
    for r in range(rows):
        h.append(f'<div style="{muted}">r{r+1}</div>')
        for c in range(cols):
            rc = (r, c)
            if rc in dug:
                h.append(f'<div style="{base}background:var(--surface-1,#e9e8e3);border:0.5px solid var(--border,#b9b8b0);"></div>')
            elif rc in hits:
                h.append(f'<div style="{base}font:500 12px system-ui,sans-serif;background:#EF9F27;color:#412402;">gem</div>')
            else:
                t = min(1.0, max(0.0, (prob[rc] - lo_v) / span))
                rgb = [round(x + (y - x) * t) for x, y in zip(lo, hi)]
                lum = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) / 255
                fg = "#042C53" if lum > 0.62 else "#FFFFFF"
                extra = ""
                if rc in tied:
                    extra = "outline:3px solid #EF9F27;outline-offset:-3px;"
                elif rc in near:
                    extra = "outline:2px dashed #EF9F27;outline-offset:-2px;"
                h.append(f'<div style="{base}font:500 {fs}px system-ui,sans-serif;background:rgb({",".join(map(str, rgb))});color:{fg};{extra}">{100*prob[rc]:.0f}%</div>')
    h.append("</div>")
    h.append(f'<div style="display:flex;align-items:center;gap:8px;margin-top:14px;font:12px system-ui,sans-serif;color:var(--text-secondary,#52514e);"><span>{100*lo_v:.0f}%</span><div style="flex:1;height:10px;border-radius:2px;background:linear-gradient(to right,rgb{lo},rgb{hi});"></div><span>{100*hi_v:.0f}%+</span></div>')
    h.append('<div style="margin-top:8px;font:12px system-ui,sans-serif;color:var(--text-secondary,#52514e);">Solid orange outline: best (all tied cells). Dashed: within 0.5 pt. Blank gray: dug or found. Amber: revealed gem part.</div>')
    h.append("</div>")
    return "\n".join(h)

def compact(spec, prob, dug, hits, cand, title=""):
    """Small JS-driven widget (about 2-3 KB) for the inline visual tool. Prefer it over heatmap_fragment.html:
    the fragment is ~16 KB of repeated inline styles that must be pasted into the tool call in full."""
    rows, cols = spec["rows"], spec["cols"]
    vals = sorted(p for rc, p in prob.items() if rc not in hits)
    lo = vals[0] if vals else 0.0
    hi = vals[min(len(vals) - 1, int(0.9 * len(vals)))] if vals else 1.0
    if hi - lo < 1e-9:
        hi = lo + 1e-9
    tied = {rc for p, rc in cand if cand[0][0] - p < 0.0005}
    near = {rc for p, rc in cand if 0.0005 <= cand[0][0] - p < 0.005}
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            rc = (r, c)
            row.append(-1 if rc in dug else -2 if rc in hits else round(100 * prob[rc]))
        grid.append(row)
    best = [[r, c] for r, c in sorted(tied)]
    nr = [[r, c] for r, c in sorted(near)]
    js = ("const G=%s,B=%s,N=%s,lo=%.1f,hi=%.1f;" % (json.dumps(grid, separators=(",", ":")), json.dumps(best, separators=(",", ":")),
          json.dumps(nr, separators=(",", ":")), 100 * lo, 100 * hi))
    return (
        f'<h2 style="position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);">Heatmap of gem probability on a {rows} by {cols} board; best {", ".join(lab(rc) for rc in sorted(tied))}.</h2>'
        + (f'<div style="font:500 14px system-ui,sans-serif;color:var(--text-primary);margin:6px 0;">{title}</div>' if title else "")
        + '<div id="w"></div><div style="margin-top:10px;font:12px system-ui,sans-serif;color:var(--text-secondary);">Solid orange outline: best squares. Dashed: within 0.5 points. Blank: dug or found. Amber: revealed gem part. Darker blue = more likely.</div>'
        + "<script>" + js +
        "const L=t=>'<div style=\"font:12px system-ui,sans-serif;color:var(--text-muted);text-align:center;\">'+t+'</div>';"
        "const n=G[0].length,fs=n>7?12:n>6?13:15,has=(a,r,c)=>a.some(x=>x[0]==r&&x[1]==c);"
        "let h='<div style=\"display:grid;grid-template-columns:18px repeat('+n+',minmax(0,1fr));gap:3px;align-items:center;\">'+L('');"
        "for(let c=1;c<=n;c++)h+=L('c'+c);"
        "G.forEach((row,r)=>{h+=L('r'+(r+1));row.forEach((v,c)=>{"
        "const b='aspect-ratio:1;border-radius:6px;display:flex;align-items:center;justify-content:center;box-sizing:border-box;';"
        "if(v==-1){h+='<div style=\"'+b+'background:var(--surface-1);border:0.5px solid var(--border);\"></div>';return;}"
        "if(v==-2){h+='<div style=\"'+b+'font:500 12px system-ui,sans-serif;background:#EF9F27;color:#412402;\">gem</div>';return;}"
        "const t=Math.min(1,Math.max(0,(v-lo)/(hi-lo))),R=Math.round(230-218*t),Gc=Math.round(241-173*t),Bc=Math.round(251-127*t);"
        "const lum=(0.299*R+0.587*Gc+0.114*Bc)/255,o=has(B,r,c)?'outline:3px solid #EF9F27;outline-offset:-3px;':has(N,r,c)?'outline:2px dashed #EF9F27;outline-offset:-2px;':'';"
        "h+='<div style=\"'+b+'font:500 '+fs+'px system-ui,sans-serif;background:rgb('+R+','+Gc+','+Bc+');color:'+(lum>0.62?'#042C53':'#FFFFFF')+';'+o+'\">'+v+'%</div>';});});"
        "document.getElementById('w').innerHTML=h+'</div>';"
        "</script>")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--outdir", default="heatmap_out")
    a = ap.parse_args()
    spec = apply_level(json.load(open(a.spec)))
    prob, layouts, dug, hits = solve(spec)
    text, cand = report(spec, prob, layouts, dug, hits)
    print(text)
    frag = fragment(spec, prob, dug, hits, cand)
    os.makedirs(a.outdir, exist_ok=True)
    open(os.path.join(a.outdir, "heatmap_fragment.html"), "w").write(frag)
    open(os.path.join(a.outdir, "heatmap_compact.html"), "w").write(compact(spec, prob, dug, hits, cand))
    page = ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<style>body{margin:0 auto;max-width:480px;padding:16px;font-family:system-ui,sans-serif;background:#fff;color:#0b0b0b}'
            '@media(prefers-color-scheme:dark){body{background:#1a1a19;color:#f0efec}}</style>' + frag)
    open(os.path.join(a.outdir, "heatmap.html"), "w").write(page)
    json.dump({"layouts": layouts, "best": lab(cand[0][1]) if cand else None,
               "prob": {lab(rc): p for rc, p in prob.items()}},
              open(os.path.join(a.outdir, "result.json"), "w"), indent=1)

if __name__ == "__main__":
    main()
