#!/usr/bin/env python3
"""Scan ~/Dropbox/9aeun/pdfs for new PDFs, extract a title, and append them to
the ingest log (pdf-ingest-pending.jsonl) so they appear in Starred Papers.
Idempotent: PDFs already recorded (by basename) are skipped.
Prints the number of newly-ingested papers to stdout.
"""
import os, re, json, subprocess, sys, datetime

PDFS = os.path.expanduser("~/Dropbox/9aeun/pdfs")
JSONL = os.path.expanduser("~/Dropbox/9aeun/.claude-shared/pdf-ingest-pending.jsonl")

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

SKIP = re.compile(r'^(arXiv:|Published as|Preprint|Under review|doi:|https?://|©|\d{4}\s|[A-Z]{2,}\s+[A-Z]{2,}\s)', re.I)

def extract_title(pdf):
    try:
        txt = subprocess.run(["pdftotext", "-f", "1", "-l", "1", pdf, "-"],
                             capture_output=True, text=True, timeout=40).stdout
    except Exception:
        txt = ""
    lines = [re.sub(r'\s+', ' ', l).strip() for l in txt.splitlines() if l.strip()]
    cand = [l for l in lines if not SKIP.match(l) and len(l) > 3]
    title = cand[0] if cand else ""
    # append wrapped 2nd line if the first looks like a title fragment
    if len(cand) > 1 and title and not re.search(r'[.?:]$', title) and len(title) < 72:
        nxt = cand[1]
        if not re.search(r'\d|@|·|,\s*[A-Z]\.| and | et al', nxt) and 3 < len(nxt) < 90:
            title = title + " " + nxt
    if len(title) < 12:  # fallback to metadata Title
        try:
            info = subprocess.run(["pdfinfo", pdf], capture_output=True, text=True, timeout=15).stdout
            m = re.search(r'^Title:\s*(.+)$', info, re.M)
            if m and len(m.group(1).strip()) >= 12:
                title = m.group(1).strip()
        except Exception:
            pass
    return re.sub(r'\s+', ' ', title).strip()

def classify(title):
    t = title.lower()
    for kw, tag in [("perturb", "Perturbation"), ("single-cell", "Single-cell"),
                    ("single cell", "Single-cell"), ("scrna", "Single-cell"),
                    ("spatial", "Spatial"), ("regulat", "GRN"), ("grn", "GRN"),
                    ("organoid", "Organoid"), ("brain", "Neuro"), ("neuro", "Neuro"),
                    ("foundation model", "ML"), ("flow matching", "ML"),
                    ("diffusion", "ML"), ("transformer", "ML")]:
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
            title = extract_title(path) or re.sub(r'\.pdf$', '', fn, flags=re.I)
            tag = classify(title)
            ts = datetime.datetime.fromtimestamp(os.path.getmtime(path)).astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")
            new.append({"ts": ts, "wiki": "", "tag": tag, "basename": fn, "path": path, "title": title})
    if new:
        with open(JSONL, "a", encoding="utf-8") as f:
            for e in new:
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(len(new))
    for e in new:
        print("  + [{}] {}".format(e["tag"], e["title"][:74]), file=sys.stderr)

if __name__ == "__main__":
    main()
