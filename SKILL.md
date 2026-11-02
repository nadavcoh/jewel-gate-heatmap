---
name: jewel-gate-heatmap
description: Turn a screenshot of a Battleship-style dig/mining grid game (hidden gems under a grid, e.g. the "Jewel Gate" event with a pickaxe counter and a gem gate at the top) into an exact probability heatmap that marks the best square to dig next. Prints the board and the targets it read, so the user can validate them first. Use this whenever the user shares a screenshot of such a grid (or types "jewel gate heatmap") and asks where to dig, which square is best, for a probability map or heatmap, or to update the map after more squares were revealed or a new round started, even if they never say "heatmap".
---

# Jewel Gate heatmap

Compute the exact chance that each unrevealed square hides part of a gem, then show it as a heatmap with the best square marked. Reading the screenshot is the error-prone step (a wrong grid size, gem size or hidden/found state silently gives a wrong map), so always state what you read and let the user correct it. Read `references/screenshot-reading.md` first; it holds the confirmed gem sizes, colour meanings and pixel geometry, which saves most of the guesswork.

## Workflow

1. **Read the screenshot** (`references/screenshot-reading.md`): board size, black cells, revealed gem parts, and the gems in the artwork with their state (purple = hidden, any other colour = found).
2. **Write a spec** (below) and **run** `python3 scripts/solve.py spec.json --outdir out`. Paths are relative to this skill's folder. It prints a validation report and the map, and writes `out/heatmap_fragment.html`, `out/heatmap.html`, `out/result.json`. `examples/*.json` are real boards from earlier sessions with their expected best squares; copy the closest one.
3. **Check the report before replying**: the line `Black cells N - found-gem cells M = K empty digs` should be a small non-negative number, and the probabilities must sum to the number of hidden gem cells. A negative K or a "no consistent layout" error means a misread, so fix the spec instead of answering.
4. **Show the heatmap**: pass `heatmap_fragment.html` to the inline visual tool if there is one (it needs `read_me` first on the visualize tool); otherwise present `heatmap.html`. The fragment already has the readability fixes below. If you hand-build a widget instead, follow the same design rules.
5. **Reply short** (phone screen): what you read (board, found gems, still-hidden gems, rules), then the best square(s) with the unrounded percentage and ties, then one line asking the user to correct anything. Lead with the answer; the heatmap itself is not repeated in text. If the pickaxe count is 0, say the user needs pickaxes before digging.

A new screenshot means a new full read: rebuild the spec from scratch and rerun, never reuse old numbers. Rounds change the board and gem set (see the reference).

## Spec format

```json
{
  "rows": 8, "cols": 8,
  "dug": ["r1c2:r1c4", "r2c2:r3c7", "r5c2"],
  "hits": ["r3c6", "r4c6"],
  "targets": [
    {"name": "diamond NE", "kind": "diamond", "source": "purple"},
    {"name": "flat bottom", "kind": "flat"},
    {"name": "odd gem", "size": [2, 4]}
  ],
  "found_gems": [{"name": "octagon", "kind": "octagon"}],
  "excluded": [],
  "allow_rotation": true
}
```

- Cells are 1-indexed `r<row>c<col>`, row 1 on top. `"r2c2:r3c7"` is a rectangle.
- `dug`: **every solid-black cell**, whether it was an empty dig or belongs to a found gem. Both are unavailable for hidden gems.
- `hits`: revealed gem cells of a gem that is **still hidden** (purple sprite visible on black). Probability 1; the solver infers where the rest of that gem is.
- `targets`: only the **hidden (purple)** gems. `kind` is one of `diamond` 1x1, `tall` 3x1, `flat` 1x2, `hex` 3x2, `octagon` 3x3, or give `size` as `[rows, cols]`.
- `found_gems`: the found gems (any non-purple colour). Used only for the consistency check on black cells; they are not solved for.
- `excluded`: anything left out on purpose, with a reason, so the report shows it.

## Rules confirmed by the user

- Gems can always be rotated and can always touch each other. Do not ask again.
- Gem sizes (corrected by the user after my wrong first guesses of tall 1x2 and flat 1x3): small diamond 1x1, tall crystal 3x1, flat crystal 2x1, hexagon 2x3, octagon 3x3. The artwork's pixel proportions do **not** match these, so never size a gem from its sprite; use this list and ask when a new shape appears.
- Purple = still hidden. Any other colour (red octagon, blue hexagon, cyan flat, green diamond) = already found. The first session wrongly treated the red octagon as "not a target"; found gems are not targets but they do occupy cells.
- Every layout consistent with the screen is equally likely.

## Heatmap design (user asked for readability fixes)

- Solid cell colours, light-to-dark blue, and the number's colour chosen by luminance (dark text on light cells, white on dark). Fixed thresholds on translucent colours gave unreadable mid-tones.
- 15px numbers on 7-column boards, 13px on 8 columns, column labels `c1..` on top, row labels `r1..` at the left.
- Colour scale capped near the 90th percentile so a 94% cell does not wash out the 10-25% cells.
- All tied best cells get the solid orange (#EF9F27) inset outline, near ties (under 0.5 point) a dashed one. Do not mark only the first cell of a tie.
- Black cells are blank neutral squares (the label would only add noise), revealed gem parts amber with "gem". Include a one-line legend.
- Use an `sr-only` heading as the text alternative.

## Flag rather than guess

- A gem shape or size not in the list above: ask, or run each candidate size and, if the best squares agree, say so (this worked for the hexagons: 2x2 and 2x3 gave the same best four squares).
- Black cells that do not add up to the found gems plus plausible isolated misses.
- Targets that cannot fit the board (the solver exits with an error). Treat it as a misreading.

## Output notes

- Top squares are often a fraction of a point apart; call it a near tie instead of a winner. With an empty board the best squares are just the geometric favourites; with a partly revealed gem the next end cell is about 94%.
- When the top cell is a known extension of a partly revealed gem (for example r5c6 at 94%), say it completes that gem. After that, the next-best unknown squares are the ones to dig.
- Packaging: the user normally wants code as tar.gz, but for this skill they explicitly asked for a zip plus a push to GitHub (`nadavcoh/jewl-gate-heatmap`, branch main). The current request wins.
