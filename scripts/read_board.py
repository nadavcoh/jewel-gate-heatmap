#!/usr/bin/env python3
"""Read Jewel Gate screenshots automatically: level, dug cells, sprite states, draft spec.

Usage: python3 read_board.py IMG1.png [IMG2.png ...] [--json]      (list files explicitly, no brace expansion)
Prefer analyze.py, which calls the same reader (screen.py) and also solves and builds the widget.
Level = green check marks in the progress bar + 1; grid lines are fixed per level; hidden sprites are
(214,0,255), any other sprite colour is a found gem. Verified on 14 real screenshots of levels 1-3
(blank and partly dug, found tall/octagon/diamond). Levels 4-5 geometry is from blank boards only.
Still compare the printed grid with the image by eye: a wrong read silently gives a wrong map.
"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import screen, solve

def show(path):
    res = screen.read(path)
    if "error" in res:
        print(f"{res['file']}: READ FAILED: {res['error']}"); return res
    lv = next(l for l in solve.load_levels() if l["level"] == res["level"])
    n = lv["rows"]
    print(f"{res['file']}: level {res['level']} ({n}x{n}), {res['checks']} check marks")
    print("Grid (. unknown, # dug/found, H hit on hidden gem):")
    for r in range(n):
        print(f" r{r+1}  " + " ".join("H" if f"r{r+1}c{c+1}" in res["hits"] else "#" if f"r{r+1}c{c+1}" in res["dug"] else "." for c in range(n)))
    print("Sprites:", ", ".join(f"{s['class']}:{s['state']}:{s['color_name']}" for s in res["sprites"]))
    print("Level gem table: " + ", ".join(f"{g['count']} {g['class']} {g['size'][0]}x{g['size'][1]}" for g in lv["gems"]))
    print("Sprite count matches level table." if res["sprites_match_level"] else "MISMATCH between sprites and level table: check by eye and ask the user.")
    print(f"Black cells {len(res['dug'])} - found-gem cells {res['found_cells']} = {res['empty_digs']} empty digs" + ("   <-- negative: misread" if res["empty_digs"] < 0 else ""))
    print(f'Draft spec: {json.dumps({"level": res["level"], "dug": res["dug"], "hits": res["hits"], "found": res["found"]})}')
    return res

def main():
    files = [x for x in sys.argv[1:] if not x.startswith("--")]
    if not files:
        sys.exit(__doc__)
    if "--json" in sys.argv:
        print(json.dumps([screen.read(f) for f in files], indent=1, default=str)); return
    for f in files:
        show(f); print()

if __name__ == "__main__":
    main()
