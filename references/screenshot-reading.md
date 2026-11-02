# Reading the screenshot

Screenshots are iPhone portrait, 1125 x 2436 px. Layout from top: title, gem artwork (about y 480-710), progress bar with check marks (y ~870-980), time remaining, the yellow play area (y ~1110-2090), pickaxe counter and a RANDOM/PLAY button at the bottom.

## Board size and cell geometry
Count the vertical and horizontal grid lines; cells = lines - 1 each way. The dashed lines break up, so use the crossings (small plus marks). Observed boards:

| Board | x lines (px) | y lines (px) | cell |
|---|---|---|---|
| 7x7 (8 lines) | 119, 246, 372, 499, 626, 752, 879, 1006 | 1158, 1285, 1412, 1539, 1665, 1792, 1919, 2045 | ~127 |
| 8x8 (9 lines) | 112, 225, 337, 450, 562, 675, 787, 900, 1012 | 1152, 1265, 1377, 1490, 1603, 1715, 1827, 1940, 2052 | ~112.5 |

Cell column = floor((x - x_first_line) / cell), row likewise from the first y line. A first guess of 6x6 in the original skill was wrong; always count.

## Black cells (`dug`)
- Solid black blocks are revealed cells. They look the same whether they were an empty dig or part of a found gem, and blocks are irregular (L shapes, steps), so map each block to cells by the lines it spans, row by row, and confirm the count.
- A found gem leaves a plain black block with no sprite (the 3x3 black square in the middle is the found octagon).
- Isolated single black cells that are not part of any gem shape are empty digs. Check: black cells - found-gem cells = number of empty digs (put the found gems in `found_gems` and the script checks this).

## Revealed parts of hidden gems (`hits`)
- A purple sprite drawn on black cells is a hit on a still-hidden gem (seen: a tall crystal in column 6 showing in rows 3-4). Put the visible cells in `hits`. Its remaining cells are still yellow and unrevealed; the solver infers them. The sprite's top edge shows where the gem starts, which helps (a tall crystal starting in row 3 runs rows 3-5).
- An empty dig next to a hit (r2c6 above) rules out that end, so the gem must extend the other way.

## Gems in the artwork (hidden vs found)
- Purple = hidden, target. Any other colour = found, not a target, but its cells are black in the grid.
- Found colours seen: red octagon, blue hexagons, cyan flat crystals, green diamonds.
- Sizes (user-confirmed): diamond 1x1, tall 3x1, flat 2x1, hexagon 2x3, octagon 3x3. Sprite pixel sizes are not proportional to cells, so do not size from the art.
- Artwork layouts seen:
  - 7x7 round (3 checks): 3 diamonds (top, left, right of the octagon), 2 tall crystals (left, right), 1 flat (bottom), octagon in the middle. Total 20 cells.
  - 8x8 round (4 checks): 4 diamonds (diagonals), 2 flats (top, bottom), 2 hexagons (left, right), octagon. Total 29 cells.
- Count the sprites every time; the set changes with the round.

## Ignore
Progress bar, time remaining and the Play/Random button do not affect the map. The pickaxe counter matters only to tell the user they cannot dig at 0. A round's board and gem set change as the check marks advance, so a new screenshot with a different grid is a new round, not a correction.
