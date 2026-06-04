#!/usr/bin/env python3
"""
AI Engineering Digest — HTML newsletter generator.

Called by OpenClaw cron. Reads research JSON from stdin, produces the daily HTML issue.
Usage: echo '<research_json>' | python3 newsletter_generate.py [--date YYYY-MM-DD]
"""

import json
import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
ISSUES_DIR = REPO_DIR / "issues"

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Engineering Digest — {date_display}</title>
<link rel="stylesheet" href="{css_path}">
</head>
<body>
<div class="container">
  <header>
    <h1>AI Engineering <span>Digest</span></h1>
    <p class="tagline">Validated trends for engineers who ship</p>
    <p class="date">{date_display}</p>
  </header>

  <section class="summary">
    <h2>Today's Highlights</h2>
    <ul>
{summary_items}
    </ul>
  </section>

{sections_html}

  <footer>
    <p>AI Engineering Digest &middot; Curated by Pepe &middot; <a href="{archive_link}" style="color:var(--accent)">Archive</a></p>
  </footer>
</div>
<script>
document.querySelectorAll('.toggle-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const details = btn.closest('.article').querySelector('.details');
    details.classList.toggle('open');
    btn.textContent = details.classList.contains('open') ? 'Less ▲' : 'More ▼';
  }});
}});
</script>
</body>
</html>
"""

ARTICLE_TEMPLATE = """\
    <div class="article" id="{article_id}">
      <div class="article-header">
        <h3><a href="{url}">{title}</a></h3>
        <span class="traction-badge traction-{traction_level}">{traction_label}</span>
      </div>
      <p class="tldr">{tldr}</p>
      <div class="article-meta">
{tags_html}
        <button class="toggle-btn">More ▼</button>
      </div>
      <div class="details">
{details_html}
      </div>
    </div>
"""


def build_tags(tags):
    return "\n".join(f'        <span class="tag">{t}</span>' for t in tags)


def build_details(article):
    parts = []
    if article.get("why_it_matters"):
        parts.append(f"        <h4>Why it matters</h4>\n        <p>{article['why_it_matters']}</p>")
    if article.get("use_cases"):
        items = "\n".join(f"          <li>{uc}</li>" for uc in article["use_cases"])
        parts.append(f"        <h4>Use cases</h4>\n        <ul>\n{items}\n        </ul>")
    if article.get("traction_evidence"):
        items = "\n".join(f"          <li>{ev}</li>" for ev in article["traction_evidence"])
        parts.append(f"        <h4>Traction</h4>\n        <ul>\n{items}\n        </ul>")
    if article.get("links"):
        items = "\n".join(f'          <li><a href="{l["url"]}">{l["label"]}</a></li>' for l in article["links"])
        parts.append(f"        <h4>Sources</h4>\n        <ul>\n{items}\n        </ul>")
    return "\n".join(parts)


def traction_info(level):
    mapping = {
        "high": ("high", "High Traction"),
        "medium": ("medium", "Growing"),
        "emerging": ("emerging", "Emerging"),
    }
    return mapping.get(level, ("emerging", "Emerging"))


def build_section(section_name, articles):
    cards = []
    for i, art in enumerate(articles):
        t_level, t_label = traction_info(art.get("traction", "emerging"))
        aid = f"{section_name.lower().replace(' ', '-')}-{i}"
        cards.append(ARTICLE_TEMPLATE.format(
            article_id=aid,
            url=art.get("url", "#"),
            title=art.get("title", "Untitled"),
            traction_level=t_level,
            traction_label=t_label,
            tldr=art.get("tldr", ""),
            tags_html=build_tags(art.get("tags", [])),
            details_html=build_details(art),
        ))
    return f'  <section>\n    <h2 class="section-title">{section_name}</h2>\n{"".join(cards)}  </section>\n'


def build_index(date_str):
    issues = sorted(ISSUES_DIR.glob("*.html"), reverse=True)
    items = []
    for p in issues[:30]:
        d = p.stem
        try:
            label = datetime.strptime(d, "%Y-%m-%d").strftime("%B %d, %Y")
        except ValueError:
            label = d
        items.append(f'    <li><a href="issues/{p.name}"><span class="date-label">{label}</span></a></li>')

    return f"""\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Engineering Digest</title>
<link rel="stylesheet" href="style.css">
<meta http-equiv="refresh" content="0;url=issues/{date_str}.html">
</head>
<body>
<div class="container">
  <header>
    <h1>AI Engineering <span>Digest</span></h1>
    <p class="tagline">Validated trends for engineers who ship</p>
  </header>
  <section>
    <h2 class="section-title">Archive</h2>
    <ul class="archive-list">
{chr(10).join(items)}
    </ul>
  </section>
  <footer>
    <p>AI Engineering Digest &middot; Curated by Pepe</p>
  </footer>
</div>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("input", nargs="?", default="-")
    args = parser.parse_args()

    if args.input == "-":
        data = json.load(sys.stdin)
    else:
        with open(args.input) as f:
            data = json.load(f)

    date_display = datetime.strptime(args.date, "%Y-%m-%d").strftime("%B %d, %Y")

    anchor_to_url = {}
    for sec in data.get("sections", []):
        sec_slug = sec["name"].lower().replace(" ", "-").replace("&", "and")
        for i, art in enumerate(sec["articles"]):
            anchor_to_url[f"{sec_slug}-{i}"] = art.get("url", "#")

    summary_items = "\n".join(
        f'      <li><a href="{anchor_to_url.get(s.get("anchor", ""), "#")}">{s["text"]}</a></li>'
        for s in data.get("highlights", [])
    )

    sections_html = ""
    for sec in data.get("sections", []):
        sections_html += build_section(sec["name"], sec["articles"])

    is_issue = True
    css_path = "../style.css" if is_issue else "style.css"
    archive_link = "../index.html" if is_issue else "index.html"

    html = HTML_TEMPLATE.format(
        date_display=date_display,
        css_path=css_path,
        summary_items=summary_items,
        sections_html=sections_html,
        archive_link=archive_link,
    )

    ISSUES_DIR.mkdir(parents=True, exist_ok=True)
    issue_path = ISSUES_DIR / f"{args.date}.html"
    issue_path.write_text(html)

    index_html = build_index(args.date)
    (REPO_DIR / "index.html").write_text(index_html)

    print(f"Generated: {issue_path}")
    print(f"Updated: {REPO_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
