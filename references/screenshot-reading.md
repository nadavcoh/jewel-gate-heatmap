# Reading the screenshot

Screenshots are iPhone portrait, 1125 x 2436 px. From the top: title, gem artwork (y ~450-740), progress bar with check marks (y ~830-990), time remaining, yellow play area (y 1110-2090), pickaxe counter and RANDOM/PLAY button.

`scripts/screen.py` (used by `read_board.py` and `analyze.py`) does this automatically; this file is what it is based on and what to verify.

## Level and board size
- Level = green check marks + 1 (0 checks = level 1, 4x4; 4 checks = level 5, 8x8). Check marks sit above x 242/404/566/728 at y 825-900 (~1290 green pixels each).
- **Do not detect grid lines by projecting black pixels on a dug board**: black blocks add hundreds of black pixels to the columns/rows they span, so peaks merge (boards were read as 3x4, 2x2, 7x6). That method only works on blank boards. Use the fixed lines below (`screen.GEOM`). Measured lines (px):

| Level | Board | x lines | y lines | cell |
|---|---|---|---|---|
| 1 | 4x4 | 140, 351, 562, 773, 984 | 1180, 1391, 1602, 1813, 2024 | 211 |
| 2 | 5x5 | 140, 309, 477, 646, 815, 984 | 1180, 1349, 1518, 1686, 1855, 2024 | 169 |
| 3 | 6x6 | 140, 280, 421, 562, 702, 843, 984 | 1180, 1321, 1461, 1602, 1743, 1883, 2024 | 141 |
| 4 | 7x7 | 119, 246, 372, 499, 625, 752, 878, 1005 | 1159, 1286, 1412, 1539, 1665, 1792, 1918, 2045 | 127 |
| 5 | 8x8 | 112, 224, 337, 449, 562, 674, 787, 899, 1012 | 1152, 1265, 1377, 1489, 1602, 1714, 1827, 1939, 2052 | 112.5 |

Cell column = floor((x - first x line) / cell), row likewise. Never eyeball-count crossings; use the script.

## Black cells (`dug`)
- Solid black blocks are revealed cells, empty dig or part of a found gem, and blocks can be irregular. Map each block to cells row by row.
- A found gem leaves a plain black block (a found octagon = black square). Check: black cells - found-gem cells = empty digs (put found gems in `found`; the solver reports it).

## Revealed parts of hidden gems (`hits`)
- A purple sprite drawn on black cells is a hit on a still-hidden gem; its other cells are still yellow. Its top edge shows where it starts. An empty dig next to a hit rules out that end.

## Gems in the artwork
- Magenta (214,0,255) = hidden. Any other colour = found. Seen on real boards: red octagon (255,0,111), teal tall (0,255,210) on levels 1 and 3, violet tall (173,84,255) on level 2, green diamond (0,255,4). Hexagon/flat found colours of levels 4-5 not seen yet.
- Digging one cell of a gem reveals the whole gem: all its cells go black and the sprite changes colour.
- Sprite bounding boxes on blank boards (px): octagon ~101x101 (area ~8.6k, same for 2x2 and 3x3, so sprite size says nothing about cells), diamond ~39x39 (area ~790), hexagon ~54-64 x 104 (area ~4.2k), tall w30 x h100-136, flat h30 x w101-133. Tall/flat length was ~101 px for 2-cell and ~134 px for 3-cell gems on levels 1-4, a useful sanity check but not a source of sizes.
- A 17x82 magenta blob and many tiny dither blobs are decoration; `read_board.py` filters by area and shape.
- Artwork layouts: L1 diamonds above/below octagon, talls left/right; L2 octagon on top, talls left/right, flat below, diamond at the bottom; L3 diamonds NW/NE, talls left/right, flat below; L4 three diamonds above, talls left/right, flat below; L5 diamonds on the four diagonals, flats top/bottom, hexagons left/right.

## Ignore
Progress bar, time remaining and the Play/Random button do not affect the map. Pickaxe count only matters for saying the user cannot dig at 0. Time remaining decreases across screenshots, which orders them in time.
