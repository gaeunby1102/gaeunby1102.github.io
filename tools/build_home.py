#!/usr/bin/env python3
"""
Regenerate home-page dynamic bits:
  1) assets/js/notes-data.js   -> window.NOTES_DATA (categories + notes) for the graph
  2) Starred Papers list       -> injected into index.html between markers

Run after adding notes or ingesting papers:
    python3 tools/build_home.py
"""
import os, re, json, html

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTES_HTML = os.path.join(SITE, "notes.html")
INDEX_HTML = os.path.join(SITE, "index.html")
NOTES_DATA_JS = os.path.join(SITE, "assets", "js", "notes-data.js")
JSONL = os.path.expanduser("~/Dropbox/9aeun/.claude-shared/pdf-ingest-pending.jsonl")

# ---------- 1) notes-data.js from notes.html ----------
def build_notes_data():
    src = open(NOTES_HTML, encoding="utf-8").read()
    # split by category headers, keep the following <ul>
    cats = []
    parts = re.split(r'<h2 class="note-cat">(.*?)</h2>', src)
    # parts: [before, cat1, html1, cat2, html2, ...]
    for i in range(1, len(parts), 2):
        name = html.unescape(re.sub(r'<[^>]+>', '', parts[i]).strip())
        chunk = parts[i + 1]
        ul = re.search(r'<ul class="note-list">(.*?)</ul>', chunk, re.S)
        notes = []
        if ul:
            for m in re.finditer(r'<a href="(.*?)">(.*?)</a>', ul.group(1), re.S):
                notes.append({"label": html.unescape(re.sub(r'\s+', ' ', m.group(2)).strip()),
                              "url": m.group(1).strip()})
        cats.append({"category": name, "url": "notes.html", "notes": notes})
    js = "window.NOTES_DATA = " + json.dumps(cats, ensure_ascii=False, indent=2) + ";\n"
    open(NOTES_DATA_JS, "w", encoding="utf-8").write(js)
    print(f"notes-data.js: {len(cats)} categories, {sum(len(c['notes']) for c in cats)} notes")

# ---------- 2) Starred papers from ingest jsonl ----------
WIKI_TAG = {
    "SingleCell-Wiki": "Single-cell",
    "Neuroimmunology-ASD-Wiki": "Neuroimmunology",
    "Neurodevelopment-Wiki": "Neurodevelopment",
    "Genetics-Wiki": "Genetics",
    "Functional-Genomics-Wiki": "Functional Genomics",
    "DL-Conditioning-Wiki": "Deep Learning",
}

def clean_title(basename):
    t = re.sub(r'\.pdf$', '', basename, flags=re.I)
    t = t.strip()
    return t

def is_readable(title):
    # keep entries that look like real paper titles (words + spaces), skip DOI/code filenames
    return (' ' in title) and (len(title) >= 25) and re.search(r'[A-Za-z]{4,}', title)

def build_starred(n=6):
    if not os.path.exists(JSONL):
        print("jsonl not found, skipping starred"); return
    rows = []
    for line in open(JSONL, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            pass
    rows.sort(key=lambda r: r.get("ts", ""), reverse=True)
    seen, picked = set(), []
    for r in rows:
        title = (r.get("title") or clean_title(r.get("basename", ""))).strip()
        if not is_readable(title):
            continue
        key = title.lower()
        if key in seen:
            continue
        seen.add(key)
        tag = r.get("tag") or WIKI_TAG.get(r.get("wiki", ""), r.get("wiki", "").replace("-Wiki", ""))
        picked.append((title, tag))
        if len(picked) >= n:
            break
    lis = []
    for title, tag in picked:
        lis.append('        <li><span class="ptitle">{}</span>'
                   '<span class="ptag">{}</span></li>'.format(html.escape(title), html.escape(tag)))
    block = "<!--STARRED_START-->\n" + "\n".join(lis) + "\n        <!--STARRED_END-->"
    src = open(INDEX_HTML, encoding="utf-8").read()
    src = re.sub(r'<!--STARRED_START-->.*?<!--STARRED_END-->', block, src, flags=re.S)
    open(INDEX_HTML, "w", encoding="utf-8").write(src)
    print(f"starred papers: {len(picked)} items")

if __name__ == "__main__":
    build_notes_data()
    build_starred()
