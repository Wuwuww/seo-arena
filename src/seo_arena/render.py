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


def _tokens(template: dict) -> str:
    lines = [":root {"]
    for key, value in template["tokens"].items():
        lines.append(f"  --{key}: {value};")
    lines.append("}")
    return "\n".join(lines) + "\n\n"


def _nav(from_path: str, brand: str, plans: list[dict], current: str) -> str:
    brand_attrs = ' aria-current="page"' if current == "/" else ""
    parts = [
        f'<a class="brand" href="{html.escape(rel_link(from_path, "/"))}"{brand_attrs}>{html.escape(brand)}</a>'
    ]
    for index, plan in enumerate(plans, start=1):
        current_attrs = ' aria-current="page"' if plan["path"] == current else ""
        href = html.escape(rel_link(from_path, plan["path"]))
        parts.append(
            f'<a href="{href}"{current_attrs}><span class="index">{index:02d}</span> {html.escape(plan["h1"])}</a>'
        )
    return f'<nav class="site-nav" aria-label="全站">{"".join(parts)}</nav>'


def _social(title: str, description: str, url: str, kind: str) -> str:
    return (
        f'<meta property="og:title" content="{html.escape(title)}">\n'
        f'  <meta property="og:description" content="{html.escape(description)}">\n'
        f'  <meta property="og:type" content="{kind}">\n'
        f'  <meta property="og:url" content="{html.escape(url)}">'
    )


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


def _page(plan: dict, plans: list[dict], brand: str, home: str, css: str, template: dict) -> str:
    paragraphs = "".join(f"<p>{html.escape(text)}</p>" for text in plan["paragraphs"][1:])
    order = {item["path"]: index for index, item in enumerate(plans, start=1)}
    links = "".join(
        f'<li><a class="card" href="{html.escape(rel_link(plan["path"], item["href"]))}"><span class="index">{order[item["href"]]:02d}</span><strong>{html.escape(item["anchor"])}</strong></a></li>'
        for item in plan["links"]
    )
    crumb = rel_link(plan["path"], "/")
    figure = plan["figure"]
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-template="{html.escape(template["id"])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(plan["title"])}</title>
  <meta name="description" content="{html.escape(plan["description"])}">
  {_social(plan["title"], plan["description"], plan["canonical"], "article")}
  <meta name="theme-color" content="{html.escape(template["tokens"]["paper"])}">
  <link rel="canonical" href="{html.escape(plan["canonical"])}">
  <link rel="stylesheet" href="{html.escape(css)}">
  <script type="application/ld+json">{_jsonld(plan, brand, home)}</script>
</head>
<body>
  <header class="bar"><div class="wrap bar-inner">{_nav(plan["path"], brand, plans, plan["path"])}</div></header>
  <main>
    <article class="wrap">
      <p class="crumb"><a href="{html.escape(crumb)}">{html.escape(brand)}</a> / {html.escape(plan["h1"])}</p>
      <div class="stage">
        <div class="prose">
          <h1>{html.escape(plan["h1"])}</h1>
          <p class="lede">{html.escape(plan["paragraphs"][0])}</p>
          <section>
            {paragraphs}
          </section>
        </div>
        <figure>
          {figure["svg"].replace('role="img"', f'role="img" aria-label="{html.escape(figure["alt"])}"', 1)}
          <figcaption>{html.escape(figure["caption"])}</figcaption>
        </figure>
      </div>
      <h2>店里其他问题</h2>
      <ul class="cards">{links}</ul>
    </article>
  </main>
  <footer><div class="wrap"><p>{html.escape(brand)}。图、导航和正文都在页面里，不靠脚本才出现。</p></div></footer>
</body>
</html>
"""


def _home(brief: dict, plans: list[dict], css: str, template: dict) -> str:
    items = "".join(
        "<li><a class=\"card\" href=\"{href}\"><span class=\"index\">{index:02d}</span>{svg}<strong>{title}</strong><span>{desc}</span></a></li>".format(
            href=html.escape(rel_link("/", plan["path"])),
            index=index,
            svg=plan["figure"]["svg"],
            title=html.escape(plan["h1"]),
            desc=html.escape(plan["description"]),
        )
        for index, plan in enumerate(plans, start=1)
    )
    canonical = brief["site_url"].rstrip("/") + "/"
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-template="{html.escape(template["id"])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(brief["brand"])}</title>
  <meta name="description" content="{html.escape(brief["description"])}">
  {_social(brief["brand"], brief["description"], canonical, "website")}
  <meta name="theme-color" content="{html.escape(template["tokens"]["paper"])}">
  <link rel="canonical" href="{html.escape(canonical)}">
  <link rel="stylesheet" href="{html.escape(css)}">
</head>
<body>
  <header class="bar"><div class="wrap bar-inner">{_nav("/", brief["brand"], plans, "/")}</div></header>
  <main>
    <section class="wrap hero">
      <p class="kicker">{html.escape(template["label"])}</p>
      <h1>{html.escape(brief["brand"])}</h1>
      <p class="lede">{html.escape(brief["description"])}</p>
    </section>
    <ul class="wrap poster-grid">{items}</ul>
  </main>
  <footer><div class="wrap"><p>{html.escape(brief["brand"])}。同一套版式套在每一页上。</p></div></footer>
</body>
</html>
"""


def render_site(brief: dict, plans: list[dict], root: Path, out: Path, template: dict) -> None:
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "assets").mkdir()
    sheet = _tokens(template) + (root / "content" / "site.css").read_text(encoding="utf-8")
    (out / "assets" / "site.css").write_text(sheet, encoding="utf-8")
    home = brief["site_url"].rstrip("/") + "/"
    (out / "index.html").write_text(_home(brief, plans, "assets/site.css", template), encoding="utf-8")
    for plan in plans:
        folder = out / plan["path"].strip("/")
        folder.mkdir(parents=True)
        css = rel_link(plan["path"], "/assets/site.css", directory=False)
        (folder / "index.html").write_text(
            _page(plan, plans, brief["brand"], home, css, template),
            encoding="utf-8",
        )
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
