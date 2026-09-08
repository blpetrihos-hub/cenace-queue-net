"""Render docs/bibliography.html from sources/bibliography.yml."""
from __future__ import annotations

import html
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
    <h1>Place in line for electricity</h1>
    <p class="sub">CENACE interconnection and connection queues, Mexico. Diagnostic only.</p>
    <nav>
      <a href="index.html">Dashboard</a>
      <a href="methods.html">Methods</a>
      <a href="bibliography.html" aria-current="page">Bibliography</a>
    </nav>
  </div>
</header>
"""

FOOT = """
<footer class="site-footer">
  <p>No policy recommendations. Unmatched megawatts stay unmatched.</p>
</footer>
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
    import json

    JSON_OUT.write_text(json.dumps(entries, indent=2, ensure_ascii=False), encoding="utf-8")
    blocks = [
        "<h2>Annotated bibliography</h2>",
        "<p>Reputable sources only: official gazettes and operators, named academic/think-tank publishers for context, and established outlets for named-plant matches. Generated from <code>sources/bibliography.yml</code> so this page cannot drift from the codebook.</p>",
        "<p>Excluded: World Population Review, anonymous blogs, SOUTHCOM advocacy treated as finding, AMP-style clips.</p>",
    ]
    order = ["official", "journalism", "academic"]
    labels = {
        "official": "Official",
        "journalism": "Journalism (named-plant matches)",
        "academic": "Academic / practitioner (context, not the queue)",
    }
    by = {}
    for e in entries:
        by.setdefault(e.get("type", "other"), []).append(e)
    for t in order:
        if t not in by:
            continue
        blocks.append(f"<h3>{labels[t]}</h3>")
        for e in by[t]:
            blocks.append(render_entry(e))
    OUT.write_text(page("\n".join(blocks), "Bibliography · CENACE queue net"), encoding="utf-8")
    print("WROTE", OUT, "n=", len(entries))


if __name__ == "__main__":
    main()
