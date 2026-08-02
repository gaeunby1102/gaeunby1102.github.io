# gaeunby1102.github.io

Personal homepage of **Gaeun Byeon** — M.S. student, Human Genomics Lab, Korea University.
Static site (plain HTML/CSS/JS, no build step), deployed on GitHub Pages:
**https://gaeunby1102.github.io**

## Sections
Home · Publications · Projects · Seminars · Posters · Papers · Notes · Skills

The Home page shows a profile, starred papers, and an interactive knowledge graph.
Notes are categorized and rendered with MathJax.

## Local preview
```bash
python3 -m http.server 8000   # open http://localhost:8000
```

## Regenerating content (`tools/`)
- `build_home.py` — knowledge-graph data (`assets/js/notes-data.js`) + starred papers
- `build_papers.py` — Papers reading list
- `update_nav.py` — sync the top navigation across all pages
