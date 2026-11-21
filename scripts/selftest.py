#!/usr/bin/env python3
"""Regression test: python3 scripts/selftest.py   (run after ANY change to screen.py, read_board.py, analyze.py, solve.py)
Checks the reader on tests/fixtures against tests/expected.json, the solver on examples/, and that every widget
crop decodes and keeps the original colours (found gems must not come out magenta, hidden must not come out coloured)."""
import json, os, sys, glob, subprocess, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import screen, solve

bad = 0
def check(name, ok, detail=""):
    global bad
    print(("ok   " if ok else "FAIL ") + name + (("  " + detail) if detail and not ok else ""))
    bad += (not ok)

exp = json.load(open(os.path.join(ROOT, "tests", "expected.json")))
for f, e in exp.items():
    if f.startswith("_"): continue
    p = os.path.join(ROOT, "tests", "fixtures", f)
    r = screen.read(p)
    check(f"{f} level", r["level"] == e["level"], str(r["level"]))
    check(f"{f} dug", sorted(r["dug"]) == sorted(e["dug"]), str(r["dug"]))
    check(f"{f} hits", sorted(r.get("hits", [])) == sorted(e.get("hits", [])), str(r.get("hits")))
    check(f"{f} found sprites", r["found"] == sorted(e["found"]), str(r["found"]))
    check(f"{f} sprites match level table", r["sprites_match_level"])
    check(f"{f} empty digs", r["empty_digs"] == e["empty_digs"], str(r["empty_digs"]))
    arr = screen.load(p); cr = screen.crop_rle(arr, r["sprites"]); img = screen.decode_rle(cr)
    pal = {k: tuple(int(v[i:i+2], 16) for i in (1, 3, 5)) for k, v in cr["palette"].items()}
    for s in r["sprites"]:       # every sprite colour must appear in the decoded crop
        check(f"{f} crop has {s['class']} colour {s['color_name']}", any(screen.near(c, s["color"], 6) for c in pal.values()))
    FOUND = [c for c in screen.NAMES if c != screen.HIDDEN]
    has_found = any(screen.near(c, fc, 6) for c in pal.values() for fc in FOUND)
    check(f"{f} crop {'has' if r['found'] else 'has no'} found colour", has_found == bool(r["found"]))
    if "best" in e:
        with tempfile.TemporaryDirectory() as d:
            out = subprocess.run([sys.executable, os.path.join(HERE, "analyze.py"), p, "--outdir", d], capture_output=True, text=True)
            res = json.load(open(os.path.join(d, "result.json")))
            check(f"{f} best squares", res["best"] == e["best"] or sorted(res["best"]) == sorted(e["best"]), str(res["best"]))
            check(f"{f} best percent", abs(res["best_percent"] - e["best_percent"]) < 0.01, str(res["best_percent"]))
            html = open(os.path.join(d, "widget.html")).read()
            check(f"{f} widget has crop, found count and heatmap", "<canvas" in html and f"{res['found']} of {res['total']} found" in html and "const G=" in html)
for ex in glob.glob(os.path.join(ROOT, "examples", "*.json")):
    spec = json.load(open(ex)); expect = spec.pop("expect", None)
    spec = solve.apply_level(spec) if "level" in spec else spec
    prob, layouts, d, h = solve.solve(spec)
    check(f"example {os.path.basename(ex)} solves", layouts > 0)
    if expect:
        top = max(prob.values()); tied = sorted(solve.lab(rc) for rc, p in prob.items() if top - p < 0.0005)
        check(f"example {os.path.basename(ex)} best", tied == sorted(expect["best"]) and abs(100 * top - expect["percent"]) < 0.01, f"{tied} {100*top:.2f}")
print("ALL PASSED" if not bad else f"{bad} FAILED"); sys.exit(1 if bad else 0)
