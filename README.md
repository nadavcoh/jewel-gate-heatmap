# jewel-gate-heatmap

A Claude skill that turns [Jewel Gate](#about-the-game) dig-game screenshots into **exact** probability heatmaps and marks the best square to dig next.
It can also print the stored blank-board map for any of the five levels without a screenshot.

For each screenshot it produces one inline widget with:

- the gem artwork **cropped from that screenshot**, colour-true (hidden gems magenta, found gems in their own colour),
- the **found count** ("3 of 5 found") and the gem list with every gem's **size (rows x cols)**,
- the **heatmap** (chance that each unrevealed square holds part of a gem), best squares outlined, dug squares blank.

The heatmap is always generated, even when all remaining squares are tied.

## Install

Copy this folder into Claude's skills location (it is the skill: `SKILL.md` is the entry point), or upload the zip.
The scripts need Python 3 with `numpy`, `pillow` and `scipy`.

## Quick start

```bash
# one command per screenshot: read it, solve it, write the widget and the reply pieces
python3 scripts/analyze.py IMG.png --outdir out

# same level, next screenshot: keep earlier dug cells (cells never un-dig)
python3 scripts/analyze.py IMG2.png --outdir out2 --prev out/spec.json

# user corrections
python3 scripts/analyze.py IMG.png --outdir out --add-dug r3c5          # "mark r3c5 as blank"
python3 scripts/analyze.py IMG.png --outdir out --found tall,tall       # override found gems

# blank-board map of a level (no screenshot)
python3 scripts/level.py 3 --widget out.html

# regression test (fixtures + examples)
python3 scripts/selftest.py
```

`analyze.py` writes `widget.html` (paste it verbatim into the inline visual tool), `crop_preview.png` (decoded from the crop string; check its colours),
`reply.md` (gem table, best-squares table, closing question), `spec.json` and `result.json`.

## How it works

1. **Read** (`scripts/screen.py`): level = green check marks in the progress bar + 1; grid lines are fixed per level; a cell is dug when it is solid black;
   a sprite in the artwork is hidden when it is magenta (214,0,255) and found otherwise. Verified on 14 real screenshots of levels 1-3.
2. **Solve** (`scripts/solve.py`): exact enumeration of every layout consistent with the screen (gems may rotate and touch; every layout equally likely).
3. **Show** (`scripts/widget.py`, `solve.compact`): the crop is a run-length pixel map drawn on a canvas (a base64 image corrupted when retyped), the gem list uses `levels/levels.json`, the heatmap is a small JS grid.

## Levels

Level = check marks + 1. Sizes are rows x cols and always rotatable. There are no standard gem sizes: the same crystal differs between levels.

| Level | Board | Gems |
|---|---|---|
| 1 | 4x4 | 1 octagon 2x2, 2 tall 2x1, 2 diamond 1x1 |
| 2 | 5x5 | 1 octagon 2x2, 2 tall 3x1, 1 flat 2x1, 1 diamond 1x1 |
| 3 | 6x6 | 1 octagon 2x2, 2 tall 2x1, 1 flat 1x3, 2 diamond 1x1 |
| 4 | 7x7 | 1 octagon 3x3, 2 tall 3x1, 1 flat 2x1, 3 diamond 1x1 |
| 5 | 8x8 | 1 octagon 3x3, 2 hex 2x3, 2 flat 2x1, 4 diamond 1x1 |

## Layout

| Path | What |
|---|---|
| `SKILL.md` | Skill entry point: workflow, standing output rules, levels |
| `CLAUDE.md` | Notes for Claude when changing this repo |
| `references/lessons.md` | What the user corrected and what failed, with fixes |
| `references/screenshot-reading.md` | Geometry, colours and how a screenshot is read |
| `scripts/` | `analyze.py` (pipeline), `screen.py` (reader, crop), `solve.py` (solver, heatmap), `widget.py`, `read_board.py`, `gem_crops.py`, `level.py`, `selftest.py` |
| `levels/levels.json` | Gem sets, sizes and blank-board heatmaps for levels 1-5 |
| `examples/` | Example specs (including boards from real sessions) |
| `tests/` | Screenshot fixtures and the expected reader output |

## Limits

- Reader verified on levels 1-3; levels 4-5 geometry comes from blank boards only.
- The pickaxe counter is not read by the script (read it by eye).
- A screenshot taken with a different phone or layout needs new geometry in `screen.GEOM`.

## About the game

Jewel Gate is a Battleship-style dig grid: hidden gems lie under the squares, each dig reveals a square (a gem is revealed whole), and a progress bar with check marks unlocks the next level.
