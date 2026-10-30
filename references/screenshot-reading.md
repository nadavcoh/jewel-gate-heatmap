# Reading the screenshot

## Board
- The play area is the large flat-colored panel below the progress bar. The grid is drawn with dashed lines.
- Count the vertical and horizontal lines, then cells = lines - 1 in each direction. The Jewel Gate screenshot had 7 lines each way, so a 6x6 board.
- Dashed lines can break up; measure from the line crossings (the small plus marks), not from the dashes.

## Dug (empty) squares
- Solid black rectangles that fill whole cells are dug squares. Map each black block to cells by checking which grid columns and rows it spans; blocks are often irregular (an L shape is several cells).
- List cells row by row, top row first, and confirm the total count of dug cells matches the black area.

## Revealed gem squares
- A revealed gem piece should look colored or patterned instead of plain black or the flat background. If the screenshot shows any, put them in `hits`. If you are unsure whether a cell is a hit or a dig, ask the user.

## Targets
- The gem artwork above the progress bar shows the items hidden in the grid. In Jewel Gate: two small diamonds (1x1), two tall narrow crystals (1x2), one flat wide crystal (1x3), and a large red octagon in the middle.
- The user said the purple gems are the targets, so the red octagon was excluded. Do not assume this for a new screenshot; check what the user says.
- Estimate each gem's cell footprint from its proportions relative to one another, using the known sizes above as anchors. If the artwork is different in another event, state your size reading in the validation block.

## Ignore
- Progress bar and milestone checks, the time remaining, the pickaxe counter and the Play button do not affect the map. The pickaxe count only matters if the user asks about how many digs remain.
