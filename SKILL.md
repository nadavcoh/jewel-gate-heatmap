---
name: jewel-gate-heatmap
description: Turn a screenshot of a Battleship-style dig/mining grid game (hidden gems or treasures under a grid, e.g. the "Jewel Gate" event with a pickaxe counter and a gem gate at the top) into an exact probability heatmap that marks the best square to dig next. Prints the board and the targets it read, so the user can validate them first. Use this whenever the user shares a screenshot of such a grid and asks where to dig, which square is best, for a probability map or heatmap, or to update the map after more squares were revealed, even if they never say "heatmap".
---

# Jewel Gate heatmap

Compute the exact chance that each unrevealed square hides part of a gem, then show it as a heatmap with the best square marked. Reading the screenshot is the error-prone step (a wrong grid size or gem size silently gives a wrong map), so the output always starts with a validation report the user can check against their screen.

## Workflow

1. **Read the screenshot** using `references/screenshot-reading.md`. Extract:
   - board size (count grid lines, cells = lines - 1 in each direction)
   - dug (empty) squares and any revealed gem squares
   - the target gems from the artwork at the top, each with its size
2. **Write a spec file** (JSON, below). Cell labels are 1-indexed `r<row>c<col>`, row 1 at the top, column 1 at the left.
3. **Run** `python3 scripts/solve.py spec.json --outdir out` (the path is relative to this skill's folder). It prints the validation report and the map, and writes `out/heatmap_fragment.html`, `out/heatmap.html` and `out/result.json`.
4. **Reply** in this order: the validation block (board, dug cells, targets counted, anything excluded, rules assumed), then the heatmap, then the best square with its unrounded percentage and any near ties. End by asking the user to correct anything misread. Keep it short; on mobile the validation block can be condensed to the grid, the target list and the exclusions.
5. **Show the heatmap.** If an inline visual tool is available, pass the contents of `heatmap_fragment.html` to it (it is plain HTML with inline styles, no script). Otherwise present `heatmap.html` as a file.

If the user later reports a new dig result, add it to `dug` (empty) or `hits` (gem found) and rerun. Do not reuse old numbers.

## Spec format

```json
{
  "rows": 6, "cols": 6,
  "dug": ["r3c4", "r3c5", "r4c3", "r4c4", "r4c5"],
  "hits": [],
  "targets": [
    {"name": "tall crystal (left)", "size": [1, 2], "source": "purple"},
    {"name": "small diamond (top-left)", "size": [1, 1], "source": "purple"}
  ],
  "excluded": [{"name": "red octagon (center)", "reason": "user said only purple gems are targets"}],
  "allow_rotation": true
}
```

- `dug`: revealed squares with nothing in them (shown as solid black in the game).
- `hits`: revealed squares that belong to a gem. Their probability is 1 and the solver requires every hit to be covered by some gem.
- `size` is `[rows, cols]`; with rotation allowed the orientation does not matter.
- Always list gems you chose to leave out in `excluded` with the reason, so the validation report shows it.

## Rules confirmed by the user

- Gems may be rotated and may touch each other. The solver assumes this and every layout is equally likely. If the user says a rule is different (for example gems cannot touch), say the solver does not model that and the map is an approximation.
- Gem sizes seen so far: small diamond 1x1, tall narrow crystal 1x2, flat wide crystal 1x3.

## Things to flag rather than guess

- A gem you cannot size from the artwork (the red octagon in the Jewel Gate art was not a target when the user said "the purple gems are the targets"). Ask, or run both versions and label them.
- Dug versus unrevealed cells that are hard to tell apart in the screenshot.
- Targets that do not fit the board (the solver exits with an error if no layout is consistent). Treat that as a misreading, not a result.

## Notes on the output

The best square is the one with the highest probability among unrevealed squares. Differences between top squares are often a fraction of a percentage point; say so when it is a near tie rather than implying a clear winner. Probabilities across the board sum to the total number of target cells, which the report checks.
