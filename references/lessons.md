# Lessons from the sessions (read once; these are the user's corrections and my own findings)

## The user's prompts and what they taught
1. First request: `/jewl gate heatmap` with five screenshots (levels 1-5 in upload order, blank boards). I analyzed only the newest (8x8). **Correction: "The 8x8 is correct. Analyze all boards from the screenshots in this chat."** When several screenshots arrive, produce a result for every board, sorted by level, not just the latest. Uploaded file order was also time order (time remaining shrinks).
2. **"There are no standard gem sizes, always write sizes."** I had assumed one size table (tall 3x1, octagon 3x3, ...) for all boards. Sizes differ per level (octagon is 2x2 on levels 1-3, 3x3 on 4-5; tall is 2x1 or 3x1; flat is 2x1 or 1x3). Always list gems with their sizes; never carry sizes between levels. Stored as a standing preference.
3. Level 1 (4x4) gems given by the user: 1 x 2x2, 2 x 2x1, 2 x 1x1. With the old sizes the board was impossible (17 cells on 16), which was the first sign that sizes vary. A set of gems that cannot fit is a signal that sizes are wrong, not that the screenshot is.
4. **"Don't you have boards from past runs in the skill?"** Yes: the skill's examples held the confirmed level 4 and 5 gem sets, and I had wrongly called them "assumed". Before saying sizes are unknown, check `levels/levels.json` and `examples/`.
5. "The octagon in the 5x5 board is 2x2", then level 3: octagon 2x2, tall 2x1, flat 1x3, diamonds 1x1, and "5x5 tall/flat/diamond are the sizes you listed" (tall 3x1, flat 2x1, diamond 1x1). Answers to my size questions were short and specific; ask for the missing sizes of one board at a time, listing what I assume.
6. **"Crop the gems from each screenshot and present them together with the detected gems so I can verify them again easily."** then **"Embed the crops inline, one crop next to one list."** Verification should be inline, one crop beside one gem list (not a separate PNG, not one big composite). `scripts/gem_crops.py` does this.
7. "Yes" twice: the first confirmed the crops matched the lists; the second answered my offer of heatmaps for the other four boards. Treat a bare "Yes" as answering my last question, and when I offer the remaining boards' heatmaps and they say yes, deliver all of them in one widget.
8. Final request: store the five boards as levels 1-5 (increasing size) with gem definitions and the blank heatmap, and on request for a level's map supply the gem definition with sizes and the heat map; update the skill with the lessons; push to GitHub main; also present a zip. Done as `levels/levels.json` + `scripts/level.py`.

## Findings from running code
- `solve.py` logic (exact enumeration with rotation, touching allowed) needed no change; all blank maps sum to the gem-cell total. Blank-board numbers per level are in `levels/levels.json`.
- The `kind` shortcut (diamond 1x1, tall 3x1, flat 1x2, hex 3x2, octagon 3x3) silently produced wrong sizes for levels 1-3. Removed; every target needs `size`, or use `{"level": N}`.
- The old heatmap fragment is ~16 KB of repeated inline styles, too long to paste into the inline visual tool reliably. `heatmap_compact.html` (~2 KB, JS-driven, checked under node) replaces it for inline use.
- Grid detection by black-pixel projection (y 1110-2090, threshold 300 px, merge lines closer than 6 px) gave exactly lines = cells + 1 on all five levels. It replaces counting crossings by eye (an earlier session guessed 6x6 for a 7x7 board).
- Sprite detection needs a minimum area (600 px) and shape rules: without it, dither noise produced ~60 fake diamonds per image. A 17x82 blob is decoration.
- Level 3 (6x6) blank map is almost flat (12 squares within 0.5 pt), so a "best square" there is a near tie; say so.
- Level 1 sizes sum to 10 cells; ties r2c2 r2c3 r3c2 r3c3 at 72.87%. Level 2 has a single clear best square r3c3 (60.84%).
- Shell brace expansion in the tool did not expand (`IMG_30{34,42}.png`); list file names explicitly.
- Pickaxe counters seen on the blank boards: L1 0, L2 3, L3 1, L4 2, L5 4. At 0 the user cannot dig (L1 button says PLAY).

## Reply style that worked
Short, mobile-friendly: a table of gems with sizes (count, gem, size), a table of best squares per board with unrounded percentages, ties called ties, and one closing question asking the user to confirm or give the missing sizes.
