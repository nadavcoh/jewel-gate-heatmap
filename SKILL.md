---
name: jewel-gate-heatmap
description: Turn Jewel Gate screenshots (Battleship-style dig grid with hidden gems, pickaxe counter and a check-mark progress bar) into exact probability heatmaps that mark the best square to dig next, or answer "map for level N" from the stored blank-board data without a screenshot. Five levels are stored (4x4 to 8x8) with their gem definitions and sizes. Use whenever the user shares Jewel Gate screenshots, types "jewel gate heatmap", asks where to dig, which square is best, for a level's gem list or blank heatmap, or sends a new screenshot after digging, even if they never say "heatmap".
---

# Jewel Gate heatmap

Compute the exact chance that each unrevealed square hides part of a gem and show it as a heatmap with the best square(s) marked. Reading the screenshot is the error-prone step (wrong grid size, gem size or hidden/found state silently gives a wrong map), so state what you read, in tables with sizes, and let the user correct it. Paths below are relative to this skill's folder. Read `references/lessons.md` once: it lists what the user already corrected so you do not repeat it.

## Levels (stored in `levels/levels.json`)

The game has five rounds. **Level = check marks in the progress bar + 1**, and the board grows with the level. Gem sizes are `rows x cols`, rotation always allowed. There are **no standard gem sizes**: the same crystal name has different sizes on different levels, so always write the size next to every gem and never reuse a size from another level.

| Level | Board | Gems (count, class, size) | Cells | Blank-board best square(s) |
|---|---|---|---|---|
| 1 | 4x4 | 1 octagon 2x2, 2 tall 2x1, 2 diamond 1x1 | 10 | r2c2 r2c3 r3c2 r3c3, 72.87% |
| 2 | 5x5 | 1 octagon 2x2, 2 tall 3x1, 1 flat 2x1, 1 diamond 1x1 | 13 | r3c3, 60.84% |
| 3 | 6x6 | 1 octagon 2x2, 2 tall 2x1, 1 flat 1x3, 2 diamond 1x1 | 13 | r2c2 r2c5 r5c2 r5c5, 41.83% (12 cells within 0.5 pt, nearly flat) |
| 4 | 7x7 | 1 octagon 3x3, 2 tall 3x1, 1 flat 2x1, 3 diamond 1x1 | 20 | r3c3 r3c5 r5c3 r5c5, 54.83% |
| 5 | 8x8 | 1 octagon 3x3, 2 hex 2x3, 2 flat 2x1, 4 diamond 1x1 | 29 | r3c3 r3c6 r6c3 r6c6, 59.21% |

`levels.json` also holds the full blank-board percentage matrix per level. For a board/gem set that is not in the table (a new level), ask the user for the sizes and add it to `levels.json`.

## Workflow A: "map for level N" (no screenshot)

Run `python3 scripts/level.py N --widget out.html`. Reply with the gem definition as a table (count, gem, size) and the heatmap: paste `out.html` into the inline visual tool (call its `read_me` first, `data_viz` module, mobile platform), or present it as a file. Say the best squares with percentages. `python3 scripts/level.py --list` gives one line per level.

## Workflow B: screenshot(s)

1. **Read every screenshot automatically**: `python3 scripts/read_board.py IMG.png` (one call per file, list file names explicitly, no brace expansion). It counts grid lines (board size), maps the board to a level, prints the grid of dug/hit cells, classifies the artwork sprites (purple = hidden, other colour = found), compares them with the level's gem table and prints a draft spec. **Check its grid and sprite lines by eye against the image**: dug/hit/found detection is verified only on blank boards.
2. **Analyze all boards** the user sent unless they limit it (several screenshots = several levels; give one result per level, sorted by level, not just the newest). A new screenshot means a new full read: never reuse old numbers.
3. **Write a spec** (below) and run `python3 scripts/solve.py spec.json --outdir out`. It prints a validation report with every target's size, the map, and writes `heatmap_compact.html`, `heatmap_fragment.html`, `heatmap.html`, `result.json`. `examples/*.json` are real boards with their expected best squares.
4. **Check the report**: `Black cells N - found-gem cells M = K empty digs` should be a small non-negative number; probabilities must sum to the hidden gem cells. Negative K or "no consistent layout" = misread; fix the spec instead of answering.
5. **Show it**: use `heatmap_compact.html` (about 2 KB, JS-driven) in the inline visual tool. `heatmap_fragment.html` is ~16 KB of repeated styles and is too long to paste; use it only if a full static fragment is needed. Several boards: one widget per board or one stacked widget with a title per board.
6. **Verify widget on request** ("crop the gems so I can verify"): `python3 scripts/gem_crops.py IMG1 IMG2 ... --outdir out` builds `gem_crops_widget.html` (each crop inline beside its gem list with sizes) and `gems_all_boards.png`. Embed the widget inline; present the PNG only if a file is wanted. The user prefers inline, one crop next to one list.
7. **Reply short** (phone): tables for gems with sizes and for best squares, the percentage unrounded, ties called ties, then one line asking the user to confirm. If pickaxes are 0 say they must earn some before digging. Do not repeat the heatmap in text.

## Spec format

Level mode (preferred; the solver fills rows, cols, targets and found_gems from the level table):

```json
{"level": 5, "dug": ["r2c2:r3c7", "r5c2"], "hits": ["r3c6", "r4c6"], "found": ["octagon", "hex", "hex", "flat", "diamond"]}
```

`found` lists the **found gems' classes** (octagon, hex, tall, flat, diamond; one entry per gem). Everything else in the level table becomes a hidden target.

Explicit mode (new gem set): `"rows"`, `"cols"`, `"targets": [{"name": "...", "size": [rows, cols]}]`, optional `"found_gems"` (same shape), `"excluded"`, `"allow_rotation": true`. Every target needs a `size`; the old `kind` shortcut was removed because its sizes were only right for one level.

- Cells are 1-indexed `r<row>c<col>`, row 1 on top; `"r2c2:r3c7"` is a rectangle.
- `dug`: every solid-black cell, empty dig or part of a found gem.
- `hits`: revealed cells of a gem that is still hidden (purple sprite on black); the solver infers the rest of that gem.

## Rules confirmed by the user

- Gems can always be rotated and always touch. Do not ask again.
- Purple = hidden, any other colour = found (found gems are not targets but occupy cells).
- Every layout consistent with the screen is equally likely.
- Sizes come from `levels.json` or the user, never from the sprite's pixels.

## Heatmap design (user asked for readability fixes)

Solid light-to-dark blue cells with text colour chosen by luminance; scale capped near the 90th percentile; 15 px numbers up to 7 columns, 13 px at 8; `c1..`/`r1..` labels; every tied best cell has a solid orange (#EF9F27) inset outline, near ties (under 0.5 pt) dashed; dug cells blank, revealed gem parts amber "gem"; one-line legend; `sr-only` heading. `solve.py` implements all of this.

## Flag rather than guess

- Unknown level/gem set, black cells that do not add up, targets that cannot fit the board (solver exits): treat as a misreading, ask.
- Top squares a fraction of a point apart: say near tie. A top cell that completes a partly revealed gem (about 94%) is "completes that gem"; after that dig the next-best unknown squares.

## Packaging

The user normally wants code files as tar.gz; for this skill they explicitly asked for a zip plus a push to `nadavcoh/jewl-gate-heatmap` (branch main). The current request wins.
