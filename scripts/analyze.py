#!/usr/bin/env python3
"""One command per screenshot: read it, solve it, and write the finished reply pieces.

Usage: python3 analyze.py IMG.png [--outdir out] [--add-dug r3c5 ...] [--remove-dug r3c5 ...]
                                   [--found tall,tall] [--hits r3c4 ...] [--no-found-sprites]
Writes to outdir:
  widget.html       crop (found count + gem list with sizes) AND heatmap in ONE inline widget. Always send this.
  crop_preview.png  the crop decoded from the RLE string; `view` it and compare its colours with the screenshot
  reply.md          gem table + best-squares table + closing question, ready to adapt
  spec.json, result.json, heatmap_compact.html
Overrides are for user corrections ("mark r3c5 as blank" = --add-dug r3c5; "that tall is not found" = --found ...).
The reader is verified on 14 real screenshots, but still compare its report with the image by eye.
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screen, solve, widget

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("image")
    ap.add_argument("--outdir", default="analysis")
    ap.add_argument("--add-dug", nargs="*", default=[])
    ap.add_argument("--remove-dug", nargs="*", default=[])
    ap.add_argument("--hits", nargs="*")
    ap.add_argument("--prev", help="spec.json of the previous screenshot of the SAME level: its dug cells are kept "
                    "(cells never un-dig; the app sometimes redraws a dug cell as unknown) and the difference is reported")
    ap.add_argument("--found", help="comma list of found classes, replaces what the sprites say")
    a = ap.parse_args()
    os.makedirs(a.outdir, exist_ok=True)
    arr = screen.load(a.image)
    res = screen.read(a.image)
    if "error" in res:
        sys.exit("READ FAILED: " + res["error"] + " -> ask the user")
    level = next(l for l in solve.load_levels() if l["level"] == res["level"])
    sprs = res["sprites"]
    if a.found is not None:
        want = [c for c in a.found.split(",") if c]
        for s in sprs:                      # re-label sprite states to follow the override
            s["state"] = "hidden"
        for c in want:
            s = next((s for s in sprs if s["class"] == c and s["state"] == "hidden"), None)
            if s: s["state"] = "found"; s["color_name"] = s["color_name"] if s["color_name"] != "magenta" else "found"
        res["found"] = sorted(want)
    carried = []
    if a.prev and os.path.exists(a.prev):
        pv = json.load(open(a.prev))
        if pv.get("level") == res["level"]:
            carried = sorted(set(pv.get("dug", [])) - set(res["dug"]) - set(solve_cells(a.remove_dug, level)))
            res["dug"] = sorted(set(res["dug"]) | set(carried))
            if carried:
                print(f"NOTE: {', '.join(carried)} were dug in the previous screenshot but read as unknown now; kept as dug "
                      "(cells never un-dig). Tell the user, and drop it with --remove-dug if they say it is wrong.")
    dug = sorted(set(res["dug"]) - set(solve_cells(a.remove_dug, level)) | set(solve_cells(a.add_dug, level)),
                 key=lambda s: (int(s[1:s.index("c")]), int(s[s.index("c") + 1:])))
    spec = {"level": res["level"], "dug": dug, "hits": a.hits if a.hits is not None else res["hits"], "found": res["found"]}
    json.dump(spec, open(os.path.join(a.outdir, "spec.json"), "w"))
    full = solve.apply_level(json.loads(json.dumps(spec)))
    prob, layouts, d, h = solve.solve(full)
    text, cand = solve.report(full, prob, layouts, d, h)
    print(f"READ: {os.path.basename(a.image)} -> level {res['level']} ({level['rows']}x{level['cols']}), {res['checks']} check marks")
    print("Grid (. unknown, # dug/found, H hit):")
    ds = set(dug)
    for r in range(level["rows"]):
        print(f" r{r+1}  " + " ".join("H" if f"r{r+1}c{c+1}" in spec["hits"] else "#" if f"r{r+1}c{c+1}" in ds else "." for c in range(level["cols"])))
    print("Sprites:", ", ".join(f"{s['class']}:{s['state']}:{s['color_name']}" for s in sprs))
    if not res["sprites_match_level"]:
        print("WARNING: sprite classes do not match the level's gem table; check by eye and ask the user")
    print(text)
    rows = widget.gem_rows(level, sprs)
    k, n = widget.found_count(rows)
    cr = screen.crop_rle(arr, sprs)
    cr["preview"].save(os.path.join(a.outdir, "crop_preview.png"))
    screen.decode_rle(cr)                    # raises if the RLE rows are malformed
    tied = [solve.lab(rc) for p, rc in cand if cand[0][0] - p < 0.0005]
    heat = solve.compact(full, prob, d, h, cand)
    html = widget.CSS + widget.crop_block("cv", cr, level, rows, f"level {level['level']} gems") + heat
    open(os.path.join(a.outdir, "widget.html"), "w").write(html)
    open(os.path.join(a.outdir, "heatmap_compact.html"), "w").write(heat)
    best = cand[0][0] * 100
    near = [(solve.lab(rc), 100 * p) for p, rc in cand if 0.0005 <= cand[0][0] - p < 0.005][:3]
    nxt = [(solve.lab(rc), 100 * p) for p, rc in cand if cand[0][0] - p >= 0.0005][:3]
    md = [f"Level {level['level']}, {level['rows']}x{level['cols']} board, {k} of {n} gems found.", "", widget.reply_tables(level, rows), "",
          f"{layouts:,} layouts remain. Best square{'s' if len(tied) > 1 else ''}:", "", "| Squares | Chance |", "|---|---|",
          f"| {', '.join(tied)} | {best:.2f}%{' (tied)' if len(tied) > 1 else ''} |", "",
          ("Next: " + ", ".join(f"{l} {p:.2f}%" for l, p in nxt) + ".") if nxt else "", "(add pickaxe count by eye; at 0 they cannot dig)", "Does this match your screen?"]
    open(os.path.join(a.outdir, "reply.md"), "w").write("\n".join(md))
    json.dump({"level": res["level"], "found": k, "total": n, "layouts": layouts, "best": tied, "best_percent": round(best, 2),
               "prob": {solve.lab(rc): p for rc, p in prob.items()}}, open(os.path.join(a.outdir, "result.json"), "w"), indent=1)
    print(f"\nWROTE {a.outdir}/widget.html ({len(html)} chars): crop + {k} of {n} found + heatmap. `view` crop_preview.png to check colours,")
    print("then paste widget.html into the inline visual tool VERBATIM (copy from this file, never retype or reuse an older string).")

def solve_cells(items, level):
    """'r3c5' or 'r2c1:r2c4' items -> list of 'r<row>c<col>' labels."""
    return [f"r{r+1}c{c+1}" for r, c in solve.expand_cells(items, level["rows"], level["cols"])]

if __name__ == "__main__":
    main()
