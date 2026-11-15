#!/usr/bin/env python3
"""HTML pieces shared by analyze.py and gem_crops.py: crop canvas + gem list with sizes and found count."""
import collections
import screen, solve

CSS = ('<style>.r{display:flex;gap:12px;align-items:center;padding:6px 0 12px;}'
       '.r canvas{width:150px;height:auto;flex:none;border-radius:8px;image-rendering:pixelated;background:#000;}'
       '.r b{font-weight:500;font-size:15px;display:block;margin-bottom:4px;}'
       '.r ul{margin:0;padding:0;list-style:none;font-size:13px;line-height:1.6;color:var(--text-secondary);}'
       '.f{color:var(--text-primary);}</style>')

def gem_rows(level, sprs):
    """[(count, class, size, state, colour_name)] grouped, found first. Sizes always written (user rule)."""
    size = {g["class"]: g["size"] for g in level["gems"]}
    total = {g["class"]: g["count"] for g in level["gems"]}
    seen = collections.Counter((s["class"], s["state"], s["color_name"] if s["state"] == "found" else "") for s in sprs)
    rows = []
    for (cls, st, col), n in seen.items():
        rows.append((n, cls, size[cls], st, col))
    got = collections.Counter(s["class"] for s in sprs)
    for cls, t in total.items():          # sprites the reader did not see are listed as hidden
        if got[cls] < t:
            rows.append((t - got[cls], cls, size[cls], "hidden", ""))
    rows.sort(key=lambda r: (r[3] != "found", list(size).index(r[1])))
    return rows

def found_count(rows):
    return sum(r[0] for r in rows if r[3] == "found"), sum(r[0] for r in rows)

def list_html(level, rows):
    k, n = found_count(rows)
    li = []
    for cnt, cls, sz, st, col in rows:
        each = " each" if cnt > 1 else ""
        txt = f"{cnt} {cls}, {sz[0]}x{sz[1]}{each} ({st}" + (f", {col}" if col else "") + ")"
        li.append(f'<li class="f">{txt}</li>' if st == "found" else f"<li>{txt}</li>")
    return f'<b>Level {level["level"]} ({level["rows"]}x{level["cols"]}): {k} of {n} found</b><ul>{"".join(li)}</ul>'

def crop_block(cid, cr, level, rows, alt):
    return (f'<div class="r"><canvas id="{cid}" width="{cr["w"]}" height="{cr["h"]}" aria-label="{alt}"></canvas>'
            f'<div>{list_html(level, rows)}</div></div><script>{screen.crop_js(cid, cr)}</script>')

def reply_tables(level, rows):
    t = ["| Status | Gem | Size (rows x cols) |", "|---|---|---|"]
    for cnt, cls, sz, st, col in rows:
        t.append(f"| {st.capitalize()} | {cls}{' x' + str(cnt) if cnt > 1 else ''} | {sz[0]}x{sz[1]} |")
    return "\n".join(t)
