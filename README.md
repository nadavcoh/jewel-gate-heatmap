# jewel-gate-heatmap

Claude skill: turns Jewel Gate screenshots into exact probability heatmaps (best square to dig next).

```
python3 scripts/analyze.py IMG.png --outdir out [--prev out_prev/spec.json] [--add-dug r3c5] [--found tall,tall]
python3 scripts/level.py 3 --widget out.html     # blank-board map for a level, no screenshot
python3 scripts/selftest.py                      # regression test (fixtures + examples)
```
`analyze.py` reads the level (check marks), dug cells and gem sprites, solves exactly and writes one inline widget with the
colour-true gem crop, the found count, the gem list with sizes and the heatmap. See `SKILL.md` and `references/lessons.md`.
Needs python3 with numpy, pillow, scipy.
