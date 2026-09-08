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

NAV = """
<header class="site-header">
  <div class="inner">
    <p class="kicker">William &amp; Mary · GIAS Futures Group · Team 2</p>
    <h1>Who is waiting for Mexico’s grid</h1>
    <p class="sub">U.S. vs PRC vs Mexico, in megawatts and days. Diagnostic only — no policy advice.</p>
    <nav>
      <a href="index.html">Dashboard</a>
      <a href="methods.html">Methods</a>
      <a href="bibliography.html" aria-current="page">Bibliography</a>
    </nav>
  </div>
</header>
"""

FOOT = ""


def page(body: str, title: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <link rel="stylesheet" href="css/site.css">
</head>
<body>
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
        sup_html = f'<p class="bib-supports">Supports: {sup}</p>'
    else:
        sup_html = '<p class="bib-supports">No codebook row. Context only.</p>'
    return f"""
<article class="bib-entry" id="{html.escape(e["id"])}">
  <p class="bib-type">{html.escape(e.get("type", ""))} · <code>{html.escape(e["id"])}</code></p>
  <p class="bib-chicago">{html.escape(e.get("chicago", ""))}</p>
  {link}
  <p class="bib-ann">{html.escape(e.get("annotation", ""))}</p>
  {sup_html}
</article>
"""


def main() -> None:
    entries = yaml.safe_load(SRC.read_text(encoding="utf-8"))
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUT.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    blocks = [
        "<h2>Annotated bibliography</h2>",
        "<p>Official sources, named academic publishers for context, and established outlets for named factory matches. Built from <code>sources/bibliography.yml</code> so this page cannot drift.</p>",
        "<p>Excluded: World Population Review, anonymous blogs, SOUTHCOM advocacy as finding, AMP-style clips.</p>",
    ]
    order = ["official", "journalism", "academic"]
    labels = {
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
        blocks.append(f"<h3>{labels[kind]}</h3>")
        for e in by[kind]:
            blocks.append(render_entry(e))
    OUT.write_text(page("\n".join(blocks), "Bibliography · Who is waiting for Mexico’s grid"), encoding="utf-8")
    print("WROTE", OUT, "n=", len(entries))


if __name__ == "__main__":
    main()
