---
name: jewel-gate-heatmap
description: Turn Jewel Gate screenshots (Battleship-style dig grid with hidden gems, pickaxe counter and a check-mark progress bar) into exact probability heatmaps that mark the best square to dig next, or answer "level N" / "map for level N" from the stored blank-board data without a screenshot. Five levels are stored (4x4 to 8x8) with their gem definitions and sizes. Every reply shows ONE inline widget with the colour-true gem crop, the found count, the gem list with sizes and the heatmap. Use whenever the user shares Jewel Gate screenshots, types "jewel gate heatmap" or "/jewel gate level N", asks where to dig, which square is best, for a level's gem list or blank heatmap, or sends a new screenshot after digging, even if they never say "heatmap".
---

# Jewel Gate heatmap

Compute the exact chance that each unrevealed square hides part of a gem and show it as a heatmap with the best square(s) marked. The user digs one or two squares at a time and sends a screenshot after each dig, so the loop must be fast: **one command per screenshot**. Paths are relative to this skill's folder. Read `references/lessons.md` once; it lists what the user already corrected so you do not repeat it.

## Non-negotiable output (user standing rules)

Every screenshot reply contains, in this order:
1. **One inline widget** = gem crop from THIS screenshot beside the gem list with **sizes (rows x cols)** and the **found count** ("3 of 5 found"), then the **heatmap**. Always generate the heatmap, even when every square is tied (flat boards get a uniform mid-blue), when pickaxes are 0, or when only diamonds are left. Never answer a board in text only; the user had to ask "Make the heatmap" once.
2. Gem table with sizes and a best-squares table, unrounded percentages, ties called ties.
3. Anything odd you saw or changed (a dug cell that disappeared, a sprite colour you did not expect) and one closing question: "Does this match your screen?"

The crop must be **colour-true** (hidden = magenta; found gems keep their own colour: red octagon, teal or violet tall, green diamond) and its data must be **intact**. `scripts/analyze.py` guarantees both (exact colours from the screenshot, run-length pixel map drawn on a canvas, decoded and checked before it writes `widget.html`). Never build the crop by hand, never reduce it to few colours, never reuse a crop string from an earlier screenshot.

## Workflow B: screenshot(s) (the common case)

For each screenshot, in upload order (several screenshots = several boards, one result per board; the newest is not the only one):

```
python3 scripts/analyze.py /mnt/user-data/uploads/IMG.png --outdir out_N [--prev out_prev/spec.json] [--add-dug r3c5] [--remove-dug ...] [--found tall,tall]
```

It reads the level (green check marks + 1), the dug cells, hits and sprite states, runs the exact solver, prints the validation report and writes `out_N/widget.html`, `crop_preview.png`, `reply.md`, `spec.json`, `result.json`.

1. **Check the printed grid, sprite list and `Black cells - found-gem cells = K empty digs`** against the image by eye (K must be >= 0). The reader is verified on 14 real screenshots (levels 1-3); levels 4-5 only on blank boards. A wrong read silently gives a wrong map.
2. **`view out_N/crop_preview.png`** and compare its colours with the screenshot's gem artwork (found gems coloured, hidden ones magenta).
3. **Paste `out_N/widget.html` into the inline visual tool verbatim** (call its `read_me` first, `data_viz` module, mobile). `cat` the file right before pasting and copy it from that output. Do not retype, shorten, reflow or reuse an older string: one wrong character in the crop string garbles the picture (this happened twice, see lessons). If the widget renders black or broken, regenerate and paste again; if it still fails, send `crop_preview.png` with `present_files`.
4. **Reply from `reply.md`** (short, phone): gem table with sizes, best-squares table, pickaxe count read by eye (0 = they must earn some before digging), the question.
5. Pass `--prev` (the previous `spec.json` of the same level): the dug cells of the earlier screenshot are kept, because cells never un-dig; the script reports any cell that was dug before but reads as unknown now. Tell the user about it. If the user says "mark rXcY as blank", use `--add-dug rXcY`. User corrections always win over the reader.
6. The user can also correct found/hidden state: `--found tall,tall`.

Lower-level tools: `scripts/read_board.py IMG1.png IMG2.png` (reader only; list file names explicitly, no brace expansion), `scripts/solve.py spec.json --outdir out` (solver), `scripts/gem_crops.py IMG...` (crops of many boards in one widget).

## Workflow A: "level N" / "map for level N" (no screenshot)

`python3 scripts/level.py N --widget out.html` prints the gem definition with sizes and the stored blank heatmap; paste `out.html` inline and give the gem table (count, gem, size) and the best squares with percentages. `level.py --list` gives one line per level. A request such as `/jewel gate level 2` is this workflow.

## Levels (`levels/levels.json`)

**Level = check marks in the progress bar + 1**; the board grows with the level. Sizes are `rows x cols`, rotation always allowed. There are **no standard gem sizes**: the same crystal has different sizes on different levels, so write the size next to every gem and never carry a size from another level.

| Level | Board | Gems (count, class, size) | Cells | Blank-board best square(s) |
|---|---|---|---|---|
| 1 | 4x4 | 1 octagon 2x2, 2 tall 2x1, 2 diamond 1x1 | 10 | r2c2 r2c3 r3c2 r3c3, 72.87% |
| 2 | 5x5 | 1 octagon 2x2, 2 tall 3x1, 1 flat 2x1, 1 diamond 1x1 | 13 | r3c3, 60.84% |
| 3 | 6x6 | 1 octagon 2x2, 2 tall 2x1, 1 flat 1x3, 2 diamond 1x1 | 13 | r2c2 r2c5 r5c2 r5c5, 41.83% (12 cells within 0.5 pt) |
| 4 | 7x7 | 1 octagon 3x3, 2 tall 3x1, 1 flat 2x1, 3 diamond 1x1 | 20 | r3c3 r3c5 r5c3 r5c5, 54.83% |
| 5 | 8x8 | 1 octagon 3x3, 2 hex 2x3, 2 flat 2x1, 4 diamond 1x1 | 29 | r3c3 r3c6 r6c3 r6c6, 59.21% |

For a gem set not in the table, ask the user for the sizes (one board at a time, list what you assume) and add it to `levels.json` and `screen.GEOM`.

## How a dig works (what the screenshot shows)

- Digging any cell of a gem reveals the **whole gem**: all its cells turn black at once and its sprite in the artwork changes from magenta to the gem's own colour. So a black block the shape of a gem plus a recoloured sprite = that gem found. Black cells that belong to no found gem are empty digs.
- `Black cells - found-gem cells = empty digs` is the consistency check printed by the solver and the reader.
- Hidden sprite colour is always (214,0,255). Found colours seen: red octagon, green diamond, teal tall (levels 1 and 3), violet tall (level 2). Any non-magenta sprite is found.

## Spec format (for `solve.py`; analyze.py writes it for you)

```json
{"level": 3, "dug": ["r2c2", "r4c2:r5c3"], "hits": [], "found": ["octagon", "tall"]}
```
`found` lists the found gems' classes, one entry per gem. Cells are 1-indexed `r<row>c<col>`; `"r2c2:r3c7"` is a rectangle. `dug` = every solid-black cell; `hits` = revealed cells of a still-hidden gem (never seen in practice, since a dig reveals the whole gem). Explicit mode for a new gem set: `"rows"`, `"cols"`, `"targets": [{"name":..,"size":[r,c]}]`, optional `"found_gems"`. Every target needs a `size`.

## Rules confirmed by the user

- Gems can always be rotated and always touch. Every layout consistent with the screen is equally likely. Do not ask again.
- Sizes come from `levels.json` or the user, never from the sprite's pixels.
- Standing preferences: always write each gem's size; always show the inline crop beside the gem list with the found count; always generate the heatmap; crop colours must match the screenshot; crop data must not be garbled; code is delivered as a zip, never tar.gz.

## Heatmap design

Solid light-to-dark blue cells, text colour by luminance, scale capped near the 90th percentile, `c1..`/`r1..` labels, tied best cells outlined solid orange (#EF9F27), near ties (under 0.5 pt) dashed, dug cells blank, a flat board uniform mid-blue, one-line legend, `sr-only` heading. Implemented in `solve.compact`.

## Flag rather than guess

Unknown level or gem set, `K < 0`, sprites that do not match the level table, a dug cell that vanished between screenshots, top squares a fraction of a point apart ("near tie"): say so and ask. A top cell that completes a partly revealed gem is "completes that gem".

## Testing and packaging

Run `python3 scripts/selftest.py` after any change (reader on `tests/fixtures`, solver on `examples/`, crop colours and widget contents). Deliver code as a **zip** (never tar.gz) and push to `nadavcoh/jewel-gate-heatmap` branch `main` when asked; the current request wins.

Keep `README.md`, `CLAUDE.md`, this file and `references/` in sync with the code in the same commit (CLAUDE.md lists the rules for changing the repo).
