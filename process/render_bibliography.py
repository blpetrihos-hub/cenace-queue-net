"""Render docs/bibliography.html from sources/bibliography.yml."""
from __future__ import annotations

import html
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SRC = ROOT / "sources" / "bibliography.yml"
OUT = ROOT / "docs" / "bibliography.html"
JSON_OUT = ROOT / "docs" / "data" / "bibliography.json"

TYPE_ES = {
    "official": "oficial",
    "journalism": "prensa",
    "academic": "académico",
}

NAV = """
<header class="site-header">
  <div class="inner">
    <div class="header-row">
      <p class="kicker" data-i18n="kicker">William &amp; Mary · GIAS Futures Group · Team 2</p>
      <div class="lang-toggle" role="group" aria-label="Language">
        <button type="button" data-lang-btn="en">EN</button>
        <span class="lang-sep">|</span>
        <button type="button" data-lang-btn="es">ES</button>
      </div>
    </div>
    <h1 data-i18n="title">Who is waiting for Mexico’s grid</h1>
    <p class="sub" data-i18n="sub">U.S. vs PRC vs Mexico, in megawatts and days. Diagnostic only — no policy advice.</p>
    <nav>
      <a href="index.html" data-i18n="navDash">Dashboard</a>
      <a href="methods.html" data-i18n="navMethods">Methods</a>
      <a href="bibliography.html" aria-current="page" data-i18n="navBib">Bibliography</a>
    </nav>
  </div>
</header>
"""

FOOT = """
<footer class="site-footer">
  <p data-i18n="footer">No policy recommendations. Unnamed megawatts stay unnamed. Map: Carto / OpenStreetMap.</p>
</footer>
<script src="js/i18n.js"></script>
<script>initLang();</script>
"""


def page(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="css/site.css">
</head>
<body data-page-title="pageTitleBib">
{NAV}
<main class="page">
{body}
</main>
{FOOT}
</body>
</html>
"""


def render_entry(e: dict) -> str:
    url = e.get("url") or ""
    link = (
        f'<p class="bib-url"><a href="{html.escape(url)}" rel="noopener">{html.escape(url)}</a></p>'
        if url
        else ""
    )
    supports = e.get("supports") or []
    if supports:
        sup = ", ".join(html.escape(str(s)) for s in supports)
        sup_html = (
            f'<p class="bib-supports"><span data-i18n="bibSupports">Supports</span>: {sup}</p>'
        )
    else:
        sup_html = '<p class="bib-supports" data-i18n="bibContext">No codebook row. Context only.</p>'
    typ = e.get("type", "")
    typ_es = TYPE_ES.get(typ, typ)
    ann_es = e.get("annotation_es") or e.get("annotation") or ""
    return f"""
<article class="bib-entry" id="{html.escape(e["id"])}">
  <p class="bib-type"><span class="lang-en">{html.escape(typ)}</span><span class="lang-es" hidden>{html.escape(typ_es)}</span> · <code>{html.escape(e["id"])}</code></p>
  <p class="bib-chicago">{html.escape(e.get("chicago", ""))}</p>
  {link}
  <p class="bib-ann lang-en">{html.escape(e.get("annotation", ""))}</p>
  <p class="bib-ann lang-es" hidden>{html.escape(ann_es)}</p>
  {sup_html}
</article>
"""


def main() -> None:
    entries = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    blocks = [
        '<h2 data-i18n="bibH2">Annotated bibliography</h2>',
        '<p data-i18n="bibLead">Official sources, named academic publishers for context, and established outlets for named factory matches. Built from sources/bibliography.yml so this page cannot drift.</p>',
        '<p data-i18n="bibExclude">Excluded: World Population Review, anonymous blogs, SOUTHCOM advocacy as finding, AMP-style clips.</p>',
    ]
    order = ["official", "journalism", "academic"]
    labels = {
        "official": "bibOfficial",
        "journalism": "bibJournalism",
        "academic": "bibAcademic",
    }
    fallback = {
        "official": "Official",
        "journalism": "Journalism (named factory matches)",
        "academic": "Academic / practitioner (context, not the queue)",
    }
    by = {}
    for e in entries:
        by.setdefault(e.get("type", "other"), []).append(e)
    for kind in order:
        if kind not in by:
            continue
        blocks.append(f'<h3 data-i18n="{labels[kind]}">{fallback[kind]}</h3>')
        for e in by[kind]:
            blocks.append(render_entry(e))
    OUT.write_text(page("\n".join(blocks), "Bibliography · Who is waiting for Mexico’s grid"), encoding="utf-8")
    print("WROTE", OUT, "n=", len(entries))


if __name__ == "__main__":
    main()
