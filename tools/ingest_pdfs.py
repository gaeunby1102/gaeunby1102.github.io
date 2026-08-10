#!/usr/bin/env python3
"""Scan ~/Dropbox/9aeun/pdfs for new PDFs, extract a clean title, and append
them to the ingest log (pdf-ingest-pending.jsonl) so they show in Starred Papers.
Idempotent: PDFs already recorded (by basename) are skipped.
Prints the number of newly-ingested papers to stdout.

Title strategy: (1) use the filename if it already reads like a title;
(2) if the filename is an arXiv id, fetch the title from the arXiv API;
(3) otherwise parse the first PDF page, skipping author/byline lines and
fixing letter-spaced ALLCAPS titles.
"""
import os, re, json, subprocess, sys, datetime, urllib.request, urllib.parse

PDFS = os.path.expanduser("~/Dropbox/9aeun/pdfs")
JSONL = os.path.expanduser("~/Dropbox/9aeun/.claude-shared/pdf-ingest-pending.jsonl")

ARXIV_RE = re.compile(r'^(\d{4}\.\d{4,5})(v\d+)?$')
SKIP = re.compile(r'^(arXiv[:\s]|Published as|Preprint|Under review|Accepted|doi:|https?://|©|www\.)', re.I)
BYLINE = re.compile(r'(∗|†|‡|\bet al\b|,\s*\d|\d\s*,|\b(and|&)\b\s+[A-Z][a-z]+|\s&\s)')

def processed():
    s = set()
    if os.path.exists(JSONL):
        for line in open(JSONL, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            try:
                s.add(json.loads(line).get("basename"))
            except Exception:
                pass
    return s

def despace_caps(s):
    prev = None
    while s != prev:                       # "U NCERTAINTY" -> "UNCERTAINTY"
        prev = s
        s = re.sub(r'\b([A-Z]) ([A-Z])', r'\1\2', s)
    return re.sub(r'\s*-\s*', '-', s) if s.isupper() else s

def titlecase_if_shouty(s):
    letters = re.sub(r'[^A-Za-z]', '', s)
    if letters and sum(c.isupper() for c in letters) / len(letters) > 0.7:
        return s.title()
    return s

def looks_like_title(s):
    words = s.split()
    return (len(s) >= 25 and len(words) >= 4 and re.search(r'[a-z]{3}', s)
            and not re.search(r'\d{3,}', s))

def arxiv_title(arxiv_id):
    try:
        with urllib.request.urlopen("http://export.arxiv.org/api/query?id_list=" + arxiv_id, timeout=20) as r:
            xml = r.read().decode()
        m = re.search(r'<entry>.*?<title>(.*?)</title>', xml, re.S)
        if m:
            return re.sub(r'\s+', ' ', m.group(1)).strip()
    except Exception:
        pass
    return ""

def from_pdf(pdf):
    try:
        txt = subprocess.run(["pdftotext", "-f", "1", "-l", "1", pdf, "-"],
                             capture_output=True, text=True, timeout=40).stdout
    except Exception:
        txt = ""
    for raw in txt.splitlines():
        l = re.sub(r'\s+', ' ', raw).strip()
        if not l or SKIP.match(l):
            continue
        l = re.sub(r'^(Review article|Article|Letter|Perspective|Resource|Report)\s+', '', l, flags=re.I)
        if BYLINE.search(l):
            continue
        cand = titlecase_if_shouty(despace_caps(l))
        if len(cand) >= 15 and len(cand.split()) >= 3 and re.search(r'[A-Za-z]{3}', cand):
            return cand
    return ""

def extract_title(pdf, basename):
    base = re.sub(r'\.pdf$', '', basename, flags=re.I).strip()
    fname = re.sub(r'\s+', ' ', base.replace('_', ' ')).strip()
    if looks_like_title(fname):
        return fname
    m = ARXIV_RE.match(base)
    if m:
        t = arxiv_title(m.group(1))
        if t:
            return t
    t = from_pdf(pdf)
    if t:
        return t
    try:
        info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, timeout=15).stdout
        mm = re.search(r'^Title:\s*(.+)$', info, re.M)
        if mm and len(mm.group(1).strip()) >= 12:
            return re.sub(r'\s+', ' ', mm.group(1)).strip()
    except Exception:
        pass
    return fname

def classify(title):
    t = title.lower()
    for kw, tag in [("perturb", "Perturbation"), ("single-cell", "Single-cell"),
                    ("single cell", "Single-cell"), ("scrna", "Single-cell"),
                    ("spatial", "Spatial"), ("organoid", "Organoid"),
                    ("regulat", "GRN"), ("gene regulation", "GRN"), (" grn", "GRN"),
                    ("brain", "Neuro"), ("neuro", "Neuro"),
                    ("flow matching", "ML"), ("foundation model", "ML"),
                    ("diffusion", "ML"), ("transformer", "ML"), ("schr", "ML")]:
        if kw in t:
            return tag
    return "Paper"

def main():
    done = processed()
    new = []
    if os.path.isdir(PDFS):
        for fn in sorted(os.listdir(PDFS)):
            if not fn.lower().endswith(".pdf") or fn in done:
                continue
            path = os.path.join(PDFS, fn)
            title = extract_title(path, fn)
            tag = classify(title)
            am = ARXIV_RE.match(re.sub(r'\.pdf$', '', fn, flags=re.I).strip())
            url = ("https://arxiv.org/abs/" + am.group(1)) if am else \
                  ("https://scholar.google.com/scholar?q=" + urllib.parse.quote(title))
            ts = datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
            new.append({"ts": ts, "wiki": "", "tag": tag, "basename": fn, "path": path,
                        "title": title, "url": url})
    if new:
        with open(JSONL, "a", encoding="utf-8") as f:
            for e in new:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(len(new))
    for e in new:
        print("  + [{}] {}".format(e["tag"], e["title"][:74]), file=sys.stderr)

if __name__ == "__main__":
    main()
