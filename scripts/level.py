#!/usr/bin/env python3
"""Show one level (or all): gem definition with sizes + the stored blank-board heat map.

Usage: python3 level.py 3            gem table, heat map, best squares (text)
       python3 level.py 3 --widget out.html    also write the compact inline widget for the visual tool
       python3 level.py --list       one line per level
Levels 1-5 grow with board size (4x4 ... 8x8). Sizes are [rows, cols]; rotation is always allowed.
For a partly dug board do NOT use this; write a spec with "level" + dug/hits/found and run solve.py.
"""
import argparse, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solve

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("level", nargs="?", type=int)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--widget")
    a = ap.parse_args()
    levels = solve.load_levels()
    if a.list or a.level is None:
        for l in levels:
            n = sum(g["count"] for g in l["gems"])
            print(f"level {l['level']}: {l['rows']}x{l['cols']}, {n} gems, {l['blank_heatmap']['cells']} cells, best {', '.join(l['blank_heatmap']['best'])} at {l['blank_heatmap']['best_percent']}%")
        return
    lv = next((l for l in levels if l["level"] == a.level), None)
    if not lv:
        sys.exit(f"levels are 1-{len(levels)}")
    print(f"Level {lv['level']}: {lv['rows']}x{lv['cols']} board")
    print("Gems (rows x cols, rotation allowed):")
    for g in lv["gems"]:
        print(f"  {g['count']} x {g['class']}  {g['size'][0]}x{g['size'][1]}")
    h = lv["blank_heatmap"]
    print(f"Total {h['cells']} gem cells, {h['layouts']:,} layouts. Blank-board heat map (% chance a cell holds a gem):")
    print("      " + "".join(f"{'c'+str(c+1):>7}" for c in range(lv["cols"])))
    for r, row in enumerate(h["percent"]):
        print(f" r{r+1}   " + "".join(f"{v:7.2f}" for v in row))
    print("Best: " + ", ".join(h["best"]) + f" at {h['best_percent']}%" + (f"; within 0.5 pt: {', '.join(h['near_best'])}" if h["near_best"] else ""))
    if a.widget:
        spec = solve.apply_level({"level": lv["level"]})
        prob, layouts, dug, hits = solve.solve(spec)
        cand = sorted(((p, rc) for rc, p in prob.items()), reverse=True)
        open(a.widget, "w").write(solve.compact(spec, prob, dug, hits, cand, title=f"Level {lv['level']} ({lv['rows']}x{lv['cols']}), blank board"))
        print("widget written:", a.widget)

if __name__ == "__main__":
    main()
