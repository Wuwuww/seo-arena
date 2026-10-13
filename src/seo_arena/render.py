"""Render one briefing issue into a crawlable page."""

from __future__ import annotations

import html
import shutil
from pathlib import Path

SITE_NAME = "AI 简报"
SITE_URL = "https://wuwuww.github.io/seo-arena"
SITE_DESCRIPTION = "每天列出新论文、正在热的文本模型，以及会用到的 Skill。点标题打开原文。"
_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;600&family=Noto+Serif+SC:wght@600&display=swap" rel="stylesheet">'
)


def _items(items: list[dict]) -> str:
    if not items:
        return "<p>这次没有拉到。明天早上会再拉一次。</p>"
    rows = []
    for item in items:
        bits = "".join(f"<span>{html.escape(bit)}</span>" for bit in item.get("bits") or [])
        detail = f'<span class="detail">{html.escape(item["detail"])}</span>' if item.get("detail") else ""
        rows.append(
            f'<li><a href="{html.escape(item["url"])}"><strong>{html.escape(item["title"])}</strong>'
            f'<span class="bits">{bits}</span>{detail}</a></li>'
        )
    return f'<ul class="items">{"".join(rows)}</ul>'


def render_issue(issue: dict) -> str:
    sections = []
    for section in issue["sections"]:
        sections.append(
            f'<section id="{html.escape(section["id"])}">'
            f'<h2>{html.escape(section["title"])}</h2>'
            f'<p class="note">{html.escape(section["note"])}</p>'
            f'{_items(section["items"])}'
            "</section>"
        )
    canonical = SITE_URL.rstrip("/") + "/"
    title = f"{issue['h1']} {SITE_NAME}"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(SITE_DESCRIPTION)}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(SITE_DESCRIPTION)}">
  <meta property="og:type" content="website">
  <meta property="og:url" content="{html.escape(canonical)}">
  <meta name="theme-color" content="#e4ebf0">
  <link rel="canonical" href="{html.escape(canonical)}">
  {_FONTS}
  <link rel="stylesheet" href="assets/site.css">
</head>
<body>
  <header class="bar">
    <div class="wrap bar-inner">
      <a class="brand" href="./">{SITE_NAME}</a>
      <nav class="site-nav" aria-label="这一期">
        <a href="#papers">论文</a>
        <a href="#models">大模型</a>
        <a href="#skills">Skill</a>
      </nav>
    </div>
  </header>
  <main>
    <article class="wrap">
      <h1>{html.escape(issue["h1"])}</h1>
      <p class="standfirst">{SITE_DESCRIPTION}</p>
      <p class="when">更新于 {html.escape(issue["fetched_at"])}</p>
      {"".join(sections)}
    </article>
  </main>
  <footer><div class="wrap"><p>标题链到原文。数字和摘要片段来自接口。</p></div></footer>
</body>
</html>
"""


def render_missing() -> str:
    home = SITE_URL.rstrip("/") + "/"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>没有这个页面｜{SITE_NAME}</title>
  <meta name="robots" content="noindex">
  <link rel="canonical" href="{html.escape(home)}">
  {_FONTS}
  <link rel="stylesheet" href="{html.escape(home)}assets/site.css">
</head>
<body>
  <header class="bar">
    <div class="wrap bar-inner">
      <a class="brand" href="{html.escape(home)}">{SITE_NAME}</a>
    </div>
  </header>
  <main>
    <article class="wrap">
      <h1>没有这个页面</h1>
      <p class="standfirst">原来的演示页已经撤掉。现在只保留每天的 AI 简报。</p>
      <p><a href="{html.escape(home)}">回到今天的简报</a></p>
    </article>
  </main>
</body>
</html>
"""


def write_site(issue: dict, root: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "assets").mkdir()
    shutil.copyfile(root / "content" / "site.css", out / "assets" / "site.css")
    (out / "index.html").write_text(render_issue(issue), encoding="utf-8")
    (out / "404.html").write_text(render_missing(), encoding="utf-8")
    home = SITE_URL.rstrip("/") + "/"
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"  <url><loc>{home}</loc></url>\n"
        "</urlset>\n"
    )
    (out / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {home}sitemap.xml\n", encoding="utf-8")
