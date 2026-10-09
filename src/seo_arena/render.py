"""Render an agent plan into a crawlable static site."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path


def rel_link(from_path: str, to_path: str, *, directory: bool = True) -> str:
    source = [part for part in from_path.strip("/").split("/") if part]
    target = [part for part in to_path.strip("/").split("/") if part]
    shared = 0
    while shared < len(source) and shared < len(target) and source[shared] == target[shared]:
        shared += 1
    pieces = [".."] * (len(source) - shared) + target[shared:]
    if not pieces:
        return "./"
    href = "/".join(pieces)
    return href + "/" if directory else href


def _jsonld(plan: dict, brand: str, home: str) -> str:
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": brand, "item": home},
                    {"@type": "ListItem", "position": 2, "name": plan["h1"], "item": plan["canonical"]},
                ],
            }
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _page(plan: dict, brand: str, home: str, css: str) -> str:
    paragraphs = "".join(f"<p>{html.escape(text)}</p>" for text in plan["paragraphs"][1:])
    links = "".join(
        f'<li><a class="card" href="{html.escape(rel_link(plan["path"], item["href"]))}"><strong>{html.escape(item["anchor"])}</strong></a></li>'
        for item in plan["links"]
    )
    crumb = rel_link(plan["path"], "/")
    figure = plan["figure"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(plan["title"])}</title>
  <meta name="description" content="{html.escape(plan["description"])}">
  <link rel="canonical" href="{html.escape(plan["canonical"])}">
  <link rel="stylesheet" href="{html.escape(css)}">
  <script type="application/ld+json">{_jsonld(plan, brand, home)}</script>
</head>
<body>
  <header class="site-header"><div class="wrap"><a href="{html.escape(crumb)}">{html.escape(brand)}</a></div></header>
  <main>
    <article class="wrap sheet">
      <p class="crumb"><a href="{html.escape(crumb)}">{html.escape(brand)}</a> / {html.escape(plan["h1"])}</p>
      <h1>{html.escape(plan["h1"])}</h1>
      <p class="lede">{html.escape(plan["paragraphs"][0])}</p>
      <figure>
        {figure["svg"].replace('role="img"', f'role="img" aria-label="{html.escape(figure["alt"])}"', 1)}
        <figcaption>{html.escape(figure["caption"])}</figcaption>
      </figure>
      <section>
        {paragraphs}
      </section>
      <h2>店里其他问题</h2>
      <ul class="cards">{links}</ul>
    </article>
  </main>
  <footer><div class="wrap"><p>{html.escape(brand)}。图和文字说的是同一件事，正文不依赖脚本才出现。</p></div></footer>
</body>
</html>
"""


def _home(brief: dict, plans: list[dict], css: str) -> str:
    items = "".join(
        "<li><a class=\"card\" href=\"{href}\">{svg}<strong>{title}</strong><span>{desc}</span></a></li>".format(
            href=html.escape(rel_link("/", plan["path"])),
            svg=plan["figure"]["svg"],
            title=html.escape(plan["h1"]),
            desc=html.escape(plan["description"]),
        )
        for plan in plans
    )
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(brief["brand"])}</title>
  <meta name="description" content="{html.escape(brief["description"])}">
  <link rel="canonical" href="{html.escape(brief["site_url"].rstrip("/") + "/")}">
  <link rel="stylesheet" href="{html.escape(css)}">
</head>
<body>
  <header class="site-header"><div class="wrap"><a href="./">{html.escape(brief["brand"])}</a></div></header>
  <main>
    <div class="wrap">
      <h1>{html.escape(brief["brand"])}</h1>
      <p class="lede">{html.escape(brief["description"])}</p>
      <ul class="cards">{items}</ul>
    </div>
  </main>
</body>
</html>
"""


def render_site(brief: dict, plans: list[dict], root: Path, out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "assets").mkdir()
    shutil.copyfile(root / "content" / "site.css", out / "assets" / "site.css")
    home = brief["site_url"].rstrip("/") + "/"
    (out / "index.html").write_text(_home(brief, plans, "assets/site.css"), encoding="utf-8")
    for plan in plans:
        folder = out / plan["path"].strip("/")
        folder.mkdir(parents=True)
        css = rel_link(plan["path"], "/assets/site.css", directory=False)
        (folder / "index.html").write_text(_page(plan, brief["brand"], home, css), encoding="utf-8")
    urls = [home] + [plan["canonical"] for plan in plans]
    body = "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls)
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n</urlset>\n"
    )
    (out / "sitemap.xml").write_text(sitemap, encoding="utf-8")
    (out / "robots.txt").write_text(
        "User-agent: *\nAllow: /\n\nSitemap: " + home + "sitemap.xml\n",
        encoding="utf-8",
    )
