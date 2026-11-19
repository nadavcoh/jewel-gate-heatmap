# Lessons (read once). Everything below was a correction from the user or a failure I hit while running the code.

## Standing rules that came from the user's prompts
1. **Analyze every screenshot** and give one result per board, sorted by level, not only the newest. (First session: "The 8x8 is correct. Analyze all boards from the screenshots in this chat.")
2. **"There are no standard gem sizes, always write sizes."** Octagon is 2x2 on levels 1-3 and 3x3 on 4-5; tall is 2x1 or 3x1; flat is 2x1 or 1x3. List every gem as `count, class, size (rows x cols)`; never carry a size from another level. Before saying sizes are unknown, check `levels/levels.json` and `examples/`.
3. **"Always show the crop with the found count."** Every board reply has the gem crop from that screenshot beside the gem list, with "k of N found" and sizes, inline (not a separate PNG, not one composite). (Earlier: "Crop the gems ... so I can verify", "Embed the crops inline, one crop next to one list".)
4. **Always generate the heatmap.** After a board where all remaining squares were tied (25%) I answered in text; the user had to say "Make the heatmap". Tied, flat, zero pickaxes, only diamonds left: still draw it (flat boards get a uniform mid-blue; `solve.compact` handles it).
5. **The crop must match the screenshot's colours.** "That crop doesn't match the latest screenshot": I had squeezed the crop to 8 colours and the green found diamond came out as a dull purple-grey, so it looked hidden. Colours are now the exact measured ones (below).
6. **The crop data must not be garbled.** "The crop is broken" / "there are black squares instead of the crops": a base64 PNG I retyped into the widget had a changed character, so the whole image was black, twice. Once I even pasted the previous screenshot's string, so the octagon was not red. Fix: the crop is a run-length pixel map drawn on a canvas (errors stay local), `analyze.py` decodes it before writing `widget.html`, and you copy from `cat widget.html`, never from memory or an earlier message.
7. **"Mark r3c5 as blank."** A cell that was dug (empty) in one screenshot was shown undug in the next, and I trusted the newer screenshot. The user knew it was an empty dig. Cells never un-dig: keep earlier dug cells (`analyze.py --prev`), tell the user about the discrepancy, and apply `--add-dug`/`--remove-dug` when they correct you. User corrections beat the reader.
8. Short answers from the user are answers to my last question ("Yes" = confirm / deliver the rest). Level requests arrive as `/jewel gate level 1`, `Level 2`, `Level 3` = Workflow A. A bare screenshot = Workflow B.
9. Code goes out as a **zip**, never tar.gz (saved preference), and is pushed to `nadavcoh/jewel-gate-heatmap` main when asked. (The old SKILL.md misspelled the repo as `jewl-gate-heatmap`.)
10. Every repo edited in a session must have an up-to-date `README.md` and `CLAUDE.md` (add them if missing) and updated docs; this repo now has both.
11. Repeated by the user across sessions: sizes written out; crop next to list; one board at a time in the dig loop; short phone-friendly replies.

## The auto reader: what was wrong and how it was fixed
- Symptoms on real boards: IMG_3205 read as 3x4 with no dug cells, IMG_3206 as 2x2, IMG_3217 as 7x6. I fell back to reading by eye every time.
- Cause: the old reader counted grid lines by projecting black pixels. A dug block is black, so it adds hundreds of black pixels to every column/row it spans; peaks merged or shifted. It only worked on blank boards.
- Fix (`scripts/screen.py`): level = green check marks in the progress bar + 1 (green pixels in 90x75 boxes at x 242/404/566/728, y 825-900, threshold 300; a check has ~1290 pixels, none = 0). Grid lines are then fixed per level (`GEOM`), cells sampled in the inner half; dark fraction above 0.8 = dug. Verified on 14 screenshots (levels 1-3), all matching my by-eye reads.
- Sprite detection: label non-black pixels in x 425-705, y 440-740 (the decoration blobs at x 383-404 and 721-742 are outside), area >= 600, classify by bounding box. State comes from the dominant colour: hidden = (214,0,255); anything else is found. The violet tall (173,84,255) of level 2 was missed before because the old mask called it "magenta".
- Tall area can reach 3875 px (3-cell), so the tall/flat area limit is 4100, not 4000.
- Consistency check printed by the reader and solver: black cells - found-gem cells = empty digs, must be >= 0 and matched my reading every time.
- Levels 4-5: geometry comes from blank boards only; verify the first real board of those levels.

## Colours and crops (measured)
- Hidden sprites (214,0,255). Found: red octagon (255,0,111), teal tall (0,255,210) on levels 1 and 3, violet tall (173,84,255) on level 2, green diamond (0,255,4). A found sprite is simply not magenta; do not classify found gems by colour.
- Crop box (415,470)-(711,726), widened to cover all sprites; 4x4 blocks, a block is coloured when >= 6 of its 16 pixels are non-black, nearest exact palette colour. 74x64 blocks, about 1.3 KB of RLE, 4 KB for the whole widget. A base64 PNG was 1.1-1.7 KB of random characters and failed twice.
- `view crop_preview.png` after every run; it is decoded from the RLE string itself.

## Solver and widget findings
- `solve.py` (exact enumeration, rotation and touching allowed) needed no change; all blank maps sum to the gem-cell total.
- The `kind` shortcut for gem sizes was removed earlier (it gave wrong sizes for levels 1-3). Every target needs `size`, or use `{"level": N}`.
- `heatmap_fragment.html` (~16 KB) is too long to paste; the compact JS widget (~2 KB) is used. A flat board (all squares tied) used to render almost white; now uniform mid-blue.
- Digging a gem cell reveals the whole gem (all cells turn black, sprite changes colour). Observed on every found gem. So `hits` (partially revealed hidden gem) never occurred.
- Pickaxes per dig: 1. The counter is not read by the script (pixel digits); read it by eye and say "0 = they must earn some" (button then says PLAY instead of RANDOM).
- Time remaining shrinks across screenshots, which orders them.

## Session log (what the boards looked like, for regression)
Level 1: tall found at r2c1:r2c2 -> best r3c3 75.00%; octagon + tall found -> 25% everywhere (two diamonds left, 8 squares tied). Level 2: two empty digs -> best r2c4/r4c2 70.57%; diamond found -> r2c2/r4c2 76.95%; octagon found -> r3c5/r5c3 80%; tall found -> r3c5 70.37%; after r3c5 empty and both talls found -> r3c1/r4c1/r5c1 50.00%. Level 3: r2c2,r2c5 empty -> r5c2/r5c5 49.76%; tall found r5c5:r5c6 -> r5c2 51.36%; octagon found r4c2:r5c3 -> r3c4 39.22%. The same boards are in `examples/` and `tests/`.

## Reply style that worked
Short: widget (crop with found count + heatmap), gem table with sizes, best-squares table with unrounded percentages and ties called ties, pickaxe count, one question ("Does this match your screen?"). Say plainly when the reader and the image disagree.
