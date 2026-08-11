#!/usr/bin/env python3
"""Convert Notion page(s) into static Notes HTML for the site.
Usage:  NOTION_TOKEN=... python3 tools/notion_to_note.py <page_id> [<page_id> ...]
Images are downloaded locally; equations render via MathJax; tables/callouts
(incl. nested children) are supported. Prints one JSON line per page.
"""
import os, sys, json, re, html, urllib.request, urllib.parse
from pathlib import Path

TOKEN = os.environ["NOTION_TOKEN"]
SITE = Path(os.path.expanduser("~/gaeunby1102.github.io"))
NOTES_DIR = SITE / "notes"
IMG_ROOT = SITE / "assets" / "img" / "notes"
API = "https://api.notion.com/v1"
HDRS = {"Authorization": f"Bearer {TOKEN}", "Notion-Version": "2022-06-28"}

def api_get(path):
    with urllib.request.urlopen(urllib.request.Request(API + path, headers=HDRS)) as r:
        return json.load(r)

def get_children(block_id):
    out, cursor = [], None
    while True:
        q = "?page_size=100" + (f"&start_cursor={cursor}" if cursor else "")
        d = api_get(f"/blocks/{block_id}/children{q}")
        out.extend(d.get("results", []))
        if not d.get("has_more"):
            break
        cursor = d.get("next_cursor")
        if not cursor:
            break
    return out

def esc(s): return html.escape(s or "", quote=True)

def rich(rt):
    out = []
    for x in rt or []:
        if x.get("type") == "equation":
            out.append("\\(" + esc(x.get("equation", {}).get("expression", "")) + "\\)")
            continue
        s = esc(x.get("plain_text", "")).replace("\n", "<br>")
        a = x.get("annotations", {})
        if a.get("code"): s = f"<code>{s}</code>"
        if a.get("bold"): s = f"<strong>{s}</strong>"
        if a.get("italic"): s = f"<em>{s}</em>"
        if a.get("strikethrough"): s = f"<s>{s}</s>"
        if a.get("underline"): s = f"<u>{s}</u>"
        if x.get("href"): s = f'<a href="{esc(x["href"])}">{s}</a>'
        out.append(s)
    return "".join(out)

IMG_IDX = {"n": 0}
def dl_image(url, imgdir, relprefix):
    IMG_IDX["n"] += 1
    n = IMG_IDX["n"]
    ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower().lstrip(".") or "png"
    if len(ext) > 5 or "/" in ext:
        ext = "png"
    fn = f"img-{n}.{ext}"
    imgdir.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r, open(imgdir / fn, "wb") as f:
            f.write(r.read())
    except Exception as e:
        print(f"    ! image dl failed: {e}", file=sys.stderr)
        return None
    return f"{relprefix}/{fn}"

def render_table(block):
    has_col = block.get("table", {}).get("has_column_header")
    rows = [b for b in get_children(block["id"]) if b["type"] == "table_row"]
    out = ["<table>"]
    for i, r in enumerate(rows):
        cells = r.get("table_row", {}).get("cells", [])
        tag = "th" if (i == 0 and has_col) else "td"
        out.append("<tr>" + "".join(f"<{tag}>{rich(c)}</{tag}>" for c in cells) + "</tr>")
    out.append("</table>")
    return "\n".join(out)

def render_blocks(blocks, imgdir, relprefix, indent=8):
    html_out, i, n = [], 0, len(blocks)
    pad = " " * indent
    while i < n:
        b = blocks[i]; t = b["type"]; o = b.get(t, {})
        if t in ("bulleted_list_item", "numbered_list_item"):
            tag = "ul" if t == "bulleted_list_item" else "ol"
            items = []
            while i < n and blocks[i]["type"] == t:
                bi = blocks[i]
                inner = rich(bi.get(bi["type"], {}).get("rich_text", []))
                sub = ""
                if bi.get("has_children"):
                    sub = "\n" + render_blocks(get_children(bi["id"]), imgdir, relprefix, indent + 2) + pad
                items.append(f"{pad}  <li>{inner}{sub}</li>")
                i += 1
            html_out.append(f"{pad}<{tag}>\n" + "\n".join(items) + f"\n{pad}</{tag}>")
            continue
        if t == "to_do":
            chk = "checked" if o.get("checked") else ""
            html_out.append(f'{pad}<p><input type="checkbox" disabled {chk}> {rich(o.get("rich_text", []))}</p>')
        elif t == "paragraph":
            txt = rich(o.get("rich_text", []))
            if txt.strip():
                html_out.append(f"{pad}<p>{txt}</p>")
        elif t in ("heading_1", "heading_2", "heading_3"):
            lvl = {"heading_1": "h2", "heading_2": "h2", "heading_3": "h3"}[t]
            html_out.append(f"{pad}<{lvl}>{rich(o.get('rich_text', []))}</{lvl}>")
        elif t == "quote":
            html_out.append(f'{pad}<blockquote class="lead-quote">{rich(o.get("rich_text", []))}</blockquote>')
        elif t == "callout":
            emoji = (o.get("icon") or {}).get("emoji", "")
            body = (f"{emoji} " + rich(o.get("rich_text", []))).strip()
            if b.get("has_children"):
                sub = render_blocks(get_children(b["id"]), imgdir, relprefix, indent + 2)
                html_out.append(f'{pad}<blockquote class="lead-quote">{body}\n{sub}\n{pad}</blockquote>')
            else:
                html_out.append(f'{pad}<blockquote class="lead-quote">{body}</blockquote>')
        elif t == "divider":
            html_out.append(f"{pad}<hr>")
        elif t == "code":
            code = "".join(x.get("plain_text", "") for x in o.get("rich_text", []))
            html_out.append(f"{pad}<pre><code>{esc(code)}</code></pre>")
        elif t == "equation":
            html_out.append(f'{pad}<p class="mathblock">\\[ {esc(o.get("expression", ""))} \\]</p>')
        elif t == "image":
            st = o.get("type"); url = o.get(st, {}).get("url", "")
            cap = rich(o.get("caption", []))
            src = (dl_image(url, imgdir, relprefix) if url else None) or url
            fig = f'{pad}<figure><img src="{esc(src)}" alt="{esc(cap) or "image"}" loading="lazy">'
            if cap:
                fig += f"<figcaption>{cap}</figcaption>"
            html_out.append(fig + "</figure>")
        elif t == "table":
            html_out.append(pad + render_table(b).replace("\n", "\n" + pad))
        elif t == "toggle":
            summ = rich(o.get("rich_text", []))
            ch = get_children(b["id"]) if b.get("has_children") else []
            html_out.append(f"{pad}<details><summary>{summ}</summary>\n{render_blocks(ch, imgdir, relprefix, indent + 2)}\n{pad}</details>")
        elif t in ("column_list", "column"):
            ch = get_children(b["id"]) if b.get("has_children") else []
            html_out.append(render_blocks(ch, imgdir, relprefix, indent))
        elif t == "child_page":
            ctitle = o.get("title", "") or "Untitled"
            ch = get_children(b["id"])
            inner = render_blocks(ch, imgdir, relprefix, indent + 2)
            html_out.append(f'{pad}<section class="subpage">\n{pad}  <h2>{esc(ctitle)}</h2>\n{inner}\n{pad}</section>')
        else:
            rt = o.get("rich_text")
            if rt:
                html_out.append(f"{pad}<p>{rich(rt)}</p>")
        i += 1
    return "\n".join(html_out)

NAV = '''      <nav>
        <a href="../index.html">Home</a>
        <a href="../publications.html">Publications</a>
        <a href="../projects.html">Projects</a>
        <a href="../seminars.html">Seminars</a>
        <a href="../posters.html">Posters</a>
        <a href="../papers.html">Papers</a>
        <a href="../notes.html" class="active">Notes</a>
        <a href="../skills.html">Skills</a>
      </nav>'''

SIDEBAR = '''    <aside class="author">
      <img class="avatar" src="../assets/img/profile.jpg" alt="Gaeun Byeon">
      <div class="name">Gaeun Byeon</div>
      <p class="bio">ML &amp; Computational Biology</p>
      <p class="affil">M.S. Student,<br>Human Genomics Lab, Korea University</p>
      <ul class="links">
        <li><a href="mailto:gaeunbyeon1102@gmail.com">Email</a></li>
        <li><a href="https://github.com/gaeunby1102">GitHub</a></li>
        <li><a href="https://www.linkedin.com/in/%EA%B0%80%EC%9D%80-%EB%B3%80-621113361/">LinkedIn</a></li>
      </ul>
    </aside>'''

FOOTER = '''  <footer class="site-footer">
    <div class="follow">
      <a href="https://github.com/gaeunby1102" aria-label="GitHub">GitHub</a>
      <a href="mailto:gaeunbyeon1102@gmail.com" aria-label="Email">Email</a>
      <a href="https://www.linkedin.com/in/%EA%B0%80%EC%9D%80-%EB%B3%80-621113361/" aria-label="LinkedIn">LinkedIn</a>
    </div>
    <p>© 2026 Gaeun Byeon</p>
  </footer>'''

def build_page(title, date_iso, date_disp, body):
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)} · Gaeun Byeon</title>
  <link rel="icon" href="../assets/img/favicon.svg" type="image/svg+xml">
  <link rel="stylesheet" href="../assets/css/style.css">
</head>
<body>
  <header class="masthead">
    <div class="masthead-inner">
      <a class="brand" href="../index.html">Gaeun Byeon</a>
{NAV}
    </div>
  </header>

  <div class="page-wrap">
{SIDEBAR}

    <main class="content">
      <article class="note">
        <header class="note-header">
          <h1>{esc(title)}</h1>
          <p class="note-meta"><time datetime="{date_iso}">{date_disp}</time></p>
        </header>
{body}
        <p class="back"><a href="../notes.html">← 모든 노트</a></p>
      </article>
    </main>
  </div>

{FOOTER}

  <script>
  window.MathJax = {{
    tex: {{ inlineMath: [['\\\\(', '\\\\)']], displayMath: [['\\\\[', '\\\\]']] }},
    options: {{ skipHtmlTags: ['script','noscript','style','textarea','pre','code'] }}
  }};
  </script>
  <script async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
</body>
</html>
'''

def slugify(t):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (t or "").strip().lower()).strip("-")
    return s or "note"

def page_title(meta):
    for v in meta.get("properties", {}).values():
        if v.get("type") == "title":
            return "".join(x.get("plain_text", "") for x in v.get("title", [])) or "Untitled"
    return "Untitled"

def process(page_id):
    meta = api_get(f"/pages/{page_id}")
    title = page_title(meta)
    created = (meta.get("created_time") or "")[:10]
    disp = created.replace("-", ".")
    slug = slugify(title)
    imgdir = IMG_ROOT / slug
    body = render_blocks(get_children(page_id), imgdir, f"../assets/img/notes/{slug}", 8)
    (NOTES_DIR / f"{slug}.html").write_text(build_page(title, created, disp, body), encoding="utf-8")
    print(json.dumps({"title": title, "slug": slug, "date": created, "disp": disp,
                      "file": f"notes/{slug}.html", "images": IMG_IDX["n"]}, ensure_ascii=False))

if __name__ == "__main__":
    for pid in sys.argv[1:]:
        IMG_IDX["n"] = 0
        try:
            process(pid)
        except Exception as e:
            print(f"ERROR {pid}: {e}", file=sys.stderr)
