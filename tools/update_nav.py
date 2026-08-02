#!/usr/bin/env python3
"""Normalize the top navigation across every page.
Edit NAV below, then run:  python3 tools/update_nav.py
"""
import os, re, glob

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAV = [
    ("Home", "index.html"),
    ("Publications", "publications.html"),
    ("Projects", "projects.html"),
    ("Seminars", "seminars.html"),
    ("Posters", "posters.html"),
    ("Papers", "papers.html"),
    ("Notes", "notes.html"),
    ("Skills", "skills.html"),
]

files = sorted(glob.glob(os.path.join(SITE, "*.html")) +
               glob.glob(os.path.join(SITE, "notes", "*.html")))

for f in files:
    in_notes = (os.sep + "notes" + os.sep) in f
    prefix = "../" if in_notes else ""
    base = os.path.basename(f)
    active = "notes.html" if in_notes else base   # note detail pages -> Notes tab

    items = []
    for label, target in NAV:
        cls = ' class="active"' if target == active else ''
        items.append(f'        <a href="{prefix}{target}"{cls}>{label}</a>')
    nav_html = "<nav>\n" + "\n".join(items) + "\n      </nav>"

    s = open(f, encoding="utf-8").read()
    s2, n = re.subn(r'<nav>.*?</nav>', nav_html, s, count=1, flags=re.S)
    if n:
        open(f, "w", encoding="utf-8").write(s2)
    print(f"{os.path.relpath(f, SITE):58s} nav={'updated' if n else 'NOT FOUND'} active={active}")
