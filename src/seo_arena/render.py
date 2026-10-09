"""Render an agent plan into a crawlable static site."""

from __future__ import annotations

import html
import json
import math
import shutil
from pathlib import Path

_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">\n'
    '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
    '  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;600&family=ZCOOL+XiaoWei&display=swap" rel="stylesheet">'
)


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


def _wheel() -> str:
    spokes = []
    for step in range(12):
        angle = math.radians(step * 30 - 90)
        x2 = 200 + 148 * math.cos(angle)
        y2 = 200 + 148 * math.sin(angle)
        spokes.append(f'<line x1="200" y1="200" x2="{x2:.1f}" y2="{y2:.1f}"/>')
    return (
        '<svg class="wheel-svg" viewBox="0 0 400 400">'
        f'<g fill="none" stroke="currentColor" stroke-width="1.5">{"".join(spokes)}</g>'
        '<circle cx="200" cy="200" r="170" fill="none" stroke="currentColor" stroke-width="9"/>'
        '<circle cx="200" cy="200" r="14" fill="currentColor"/>'
        '<circle class="patch" cx="200" cy="30" r="16"/>'
        "</svg>"
    )


def _nav(from_path: str, brand: str, plans: list[dict], current: str) -> str:
    brand_attrs = ' aria-current="page"' if current == "/" else ""
    parts = [
        f'<a class="brand" href="{html.escape(rel_link(from_path, "/"))}"{brand_attrs}>{html.escape(brand)}</a>'
    ]
    for plan in plans:
        current_attrs = ' aria-current="page"' if plan["path"] == current else ""
        href = html.escape(rel_link(from_path, plan["path"]))
        parts.append(f'<a href="{href}"{current_attrs}>{html.escape(plan["h1"])}</a>')
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
    links = "".join(
        f'<li><a href="{html.escape(rel_link(plan["path"], item["href"]))}"><strong>{html.escape(item["anchor"])}</strong></a></li>'
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
  {_FONTS}
  <link rel="stylesheet" href="{html.escape(css)}">
  <script type="application/ld+json">{_jsonld(plan, brand, home)}</script>
</head>
<body>
  <header class="bar"><div class="wrap bar-inner">{_nav(plan["path"], brand, plans, plan["path"])}</div></header>
  <main>
    <article class="wrap">
      <p class="crumb"><a href="{html.escape(crumb)}">{html.escape(brand)}</a> / {html.escape(plan["h1"])}</p>
      <div class="prose">
        <h1>{html.escape(plan["h1"])}</h1>
        <p class="lede">{html.escape(plan["paragraphs"][0])}</p>
        <figure>
          {figure["svg"].replace('role="img"', f'role="img" aria-label="{html.escape(figure["alt"])}"', 1)}
          <figcaption>{html.escape(figure["caption"])}</figcaption>
        </figure>
        <section>
          {paragraphs}
        </section>
      </div>
      <h2>店里其他问题</h2>
      <ul class="jobs jobs-text">{links}</ul>
    </article>
  </main>
  <footer><div class="wrap"><p>{html.escape(brand)}。修胎压、补内胎、看气嘴。</p></div></footer>
</body>
</html>
"""


def _home(brief: dict, plans: list[dict], css: str, template: dict) -> str:
    items = "".join(
        '<li><a href="{href}"><span class="job-fig" aria-hidden="true">{svg}</span><span class="job-copy"><strong>{title}</strong><span class="job-desc">{desc}</span></span></a></li>'.format(
            href=html.escape(rel_link("/", plan["path"])),
            svg=plan["figure"]["svg"],
            title=html.escape(plan["h1"]),
            desc=html.escape(plan["offer"]),
        )
        for plan in plans
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
  {_FONTS}
  <link rel="stylesheet" href="{html.escape(css)}">
</head>
<body>
  <header class="bar"><div class="wrap bar-inner">{_nav("/", brief["brand"], plans, "/")}</div></header>
  <main>
    <section class="wrap hero">
      <div>
        <h1>{html.escape(brief["brand"])}</h1>
        <p class="lede">{html.escape(brief["description"])}</p>
      </div>
      <div class="wheel" aria-hidden="true">{_wheel()}</div>
    </section>
    <section class="wrap jobs-block">
      <h2>到店前可以先看</h2>
      <ul class="jobs">{items}</ul>
    </section>
  </main>
  <footer><div class="wrap"><p>{html.escape(brief["brand"])}。修胎压、补内胎、看气嘴。</p></div></footer>
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
