#!/usr/bin/env python3
"""Generate papers.html (reading list) from the GEB Notion database export.
Reads geb_papers.json (list of {title, 저널, 구분, 요약}) and writes papers.html.
Re-run after updating the export.
"""
import os, json, html, re
from collections import Counter

SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("GEB_JSON",
    "/private/tmp/claude-501/-Users-byeongaeun-Dropbox-9aeun/f23b02e8-df36-422a-b46c-c11fc813886b/scratchpad/geb_papers.json")
OUT = os.path.join(SITE, "papers.html")

papers = json.load(open(DATA, encoding="utf-8"))
# order: papers with tags first, keep DB order otherwise
tag_counts = Counter(t for p in papers for t in p.get("구분", []))
TAGS = [t for t, _ in tag_counts.most_common()]

def esc(s): return html.escape(s or "", quote=True)

chips = ['<button class="chip active" data-tag="__all">All ({})</button>'.format(len(papers))]
for t in TAGS:
    chips.append('<button class="chip" data-tag="{0}">{0} ({1})</button>'.format(esc(t), tag_counts[t]))

items = []
for p in papers:
    title = esc(p.get("title", "").strip())
    journal = esc(p.get("저널", "").strip())
    tags = p.get("구분", [])
    summary = esc(p.get("요약", "").strip())
    data = esc("|".join(tags))
    tag_html = "".join('<span class="ptag">{}</span>'.format(esc(t)) for t in tags)
    parts = ['      <li class="paper-item" data-tags="{}">'.format(data)]
    parts.append('        <p class="paper-title">{}</p>'.format(title or "(untitled)"))
    meta = []
    if journal:
        meta.append('<span class="paper-journal">{}</span>'.format(journal))
    if tag_html:
        meta.append('<span class="paper-tags">{}</span>'.format(tag_html))
    if meta:
        parts.append('        <p class="paper-meta">' + " ".join(meta) + "</p>")
    if summary:
        parts.append('        <p class="paper-summary">{}</p>'.format(summary))
    parts.append('      </li>')
    items.append("\n".join(parts))

NAV = '''      <nav>
        <a href="index.html">Home</a>
        <a href="publications.html">Publications</a>
        <a href="projects.html">Projects</a>
        <a href="seminars.html">Seminars</a>
        <a href="posters.html">Posters</a>
        <a href="papers.html" class="active">Papers</a>
        <a href="notes.html">Notes</a>
        <a href="skills.html">Skills</a>
      </nav>'''

FOOTER = '''  <footer class="site-footer">
    <div class="follow">
      <a href="https://github.com/gaeunby1102" aria-label="GitHub"><svg viewBox="0 0 24 24"><path d="M12 .5C5.7.5.5 5.7.5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.2.8-.5v-2c-3.2.7-3.9-1.4-3.9-1.4-.5-1.3-1.3-1.7-1.3-1.7-1.1-.7 0-.7 0-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.7 1.3 3.4 1 .1-.8.4-1.3.8-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C17 4.6 18 4.9 18 4.9c.6 1.6.2 2.8.1 3.1.8.8 1.2 1.8 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.6.8.5 4.6-1.5 7.9-5.8 7.9-10.9C23.5 5.7 18.3.5 12 .5z"/></svg></a>
      <a href="mailto:gaeunbyeon1102@gmail.com" aria-label="Email"><svg viewBox="0 0 24 24"><path d="M2 4a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h20a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2H2zm0 2 10 6 10-6v.01L12 12 2 6.01V6z"/></svg></a>
      <a href="https://www.linkedin.com/in/%EA%B0%80%EC%9D%80-%EB%B3%80-621113361/" aria-label="LinkedIn"><svg viewBox="0 0 24 24"><path d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.34V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.55V9h3.57v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.72v20.56C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.72V1.72C24 .77 23.2 0 22.22 0z"/></svg></a>
    </div>
    <p>© 2026 Gaeun Byeon</p>
  </footer>'''

page = '''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Papers · Gaeun Byeon</title>
  <link rel="icon" href="assets/img/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>
  <header class="masthead">
    <div class="masthead-inner">
      <a class="brand" href="index.html">Gaeun Byeon</a>
{nav}
    </div>
  </header>

  <div class="page-wrap">
    <main class="content">
      <h1>Papers</h1>
      <div class="paper-filters">
{chips}
      </div>
      <ul class="paper-list">
{items}
      </ul>
    </main>
  </div>

{footer}

  <script>
  (function () {{
    var chips = document.querySelectorAll('.paper-filters .chip');
    var items = document.querySelectorAll('.paper-list .paper-item');
    chips.forEach(function (c) {{
      c.addEventListener('click', function () {{
        chips.forEach(function (x) {{ x.classList.remove('active'); }});
        c.classList.add('active');
        var tag = c.getAttribute('data-tag');
        items.forEach(function (li) {{
          var tags = (li.getAttribute('data-tags') || '').split('|');
          li.style.display = (tag === '__all' || tags.indexOf(tag) !== -1) ? '' : 'none';
        }});
      }});
    }});
  }})();
  </script>
</body>
</html>
'''.format(nav=NAV, chips="\n".join("        " + c for c in chips),
           items="\n".join(items), footer=FOOTER)

open(OUT, "w", encoding="utf-8").write(page)
print("papers.html:", len(papers), "papers,", len(TAGS), "tags")
