"""Build a static site. Rank positions are not computed here."""

from __future__ import annotations

import html
import json
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def load_site(root: Path) -> tuple[dict, list[dict]]:
    site = json.loads((root / "content" / "site.json").read_text(encoding="utf-8"))
    pages = [json.loads(path.read_text(encoding="utf-8")) for path in (root / "content" / "pages").glob("*.json")]
    pages.sort(key=lambda page: page["order"])
    return site, pages


def validate(site: dict, pages: list[dict]) -> None:
    if not site.get("site_url", "").startswith("https://"):
        raise ValueError("site_url 需要是 https 绝对地址")
    queries = [page["query"] for page in pages]
    if len(queries) != len(set(queries)):
        raise ValueError("每篇笔记的查询必须不同")
    paths = [page["path"] for page in pages]
    if len(paths) != len(set(paths)):
        raise ValueError("每篇笔记的路径必须不同")
    for page in pages:
        if not page["path"].startswith("/") or not page["path"].endswith("/"):
            raise ValueError(f"路径需要以斜杠开头和结尾: {page['path']}")
        if page["query"] not in page["title"] and page["query"] not in page["h1"] and page["query"] not in _plain_text(page):
            raise ValueError(f"查询没有出现在页面里: {page['query']}")
        if not 8 <= len(page["title"]) <= 40:
            raise ValueError(f"title 长度不合适: {page['title']}")
        if not 40 <= len(page["description"]) <= 140:
            raise ValueError(f"description 长度不合适: {page['slug']}")
        if page["h1"] != page["title"]:
            raise ValueError(f"这篇笔记的 title 和 h1 应表达同一句结论: {page['slug']}")


def _plain_text(page: dict) -> str:
    parts = []
    for section in page["sections"]:
        parts.append(section["h2"])
        parts.extend(section["paragraphs"])
    return "\n".join(parts)


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
    if directory:
        return href + "/"
    return href


def absolute(site: dict, path: str) -> str:
    return site["site_url"].rstrip("/") + path


def breadcrumb_json(site: dict, page: dict | None) -> str:
    items = [
        {
            "@type": "ListItem",
            "position": 1,
            "name": site["name"],
            "item": absolute(site, "/"),
        }
    ]
    if page is not None:
        items.append(
            {
                "@type": "ListItem",
                "position": 2,
                "name": page["h1"],
                "item": absolute(site, page["path"]),
            }
        )
    graph: list[dict] = [{"@type": "BreadcrumbList", "itemListElement": items}]
    if page is not None:
        graph.append(
            {
                "@type": "Article",
                "headline": page["h1"],
                "description": page["description"],
                "dateModified": page["updated"],
                "inLanguage": site["lang"],
                "mainEntityOfPage": absolute(site, page["path"]),
            }
        )
    payload = {"@context": "https://schema.org", "@graph": graph}
    return json.dumps(payload, ensure_ascii=False)


def _layout(site: dict, *, title: str, description: str, canonical: str, css: str, jsonld: str, from_path: str, body: str) -> str:
    home = rel_link(from_path, "/")
    return f"""<!DOCTYPE html>
<html lang="{html.escape(site["lang"])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}</title>
  <meta name="description" content="{html.escape(description)}">
  <link rel="canonical" href="{html.escape(canonical)}">
  <meta property="og:title" content="{html.escape(title)}">
  <meta property="og:description" content="{html.escape(description)}">
  <meta property="og:type" content="article">
  <meta property="og:url" content="{html.escape(canonical)}">
  <link rel="stylesheet" href="{html.escape(css)}">
  <script type="application/ld+json">{jsonld}</script>
</head>
<body>
  <header>
    <a href="{html.escape(home)}">{html.escape(site["name"])}</a>
    <nav><a href="{html.escape(home)}">全部笔记</a></nav>
  </header>
  {body}
  <footer>
    <p>这个网站只发布页面。谷歌名次以 Chrome 搜索结果里的自然排名为准，公司排序模型的名次在模型那边看。</p>
  </footer>
</body>
</html>
"""


def render_home(site: dict, pages: list[dict]) -> str:
    items = []
    for page in pages:
        href = rel_link("/", page["path"])
        items.append(f'<li><a href="{html.escape(href)}">{html.escape(page["h1"])}</a><p>{html.escape(page["description"])}</p></li>')
    body = f"""
  <main class="home">
    <h1>{html.escape(site["name"])}</h1>
    <p>{html.escape(site["description"])}</p>
    <ul class="links">
      {"".join(items)}
    </ul>
  </main>
"""
    return _layout(
        site,
        title=site["name"],
        description=site["description"],
        canonical=absolute(site, "/"),
        css=rel_link("/", "/assets/site.css", directory=False),
        jsonld=breadcrumb_json(site, None),
        from_path="/",
        body=body,
    )


def render_page(site: dict, page: dict, pages: list[dict]) -> str:
    sections = []
    for section in page["sections"]:
        paragraphs = "".join(f"<p>{html.escape(paragraph)}</p>" for paragraph in section["paragraphs"])
        sections.append(f"<h2>{html.escape(section['h2'])}</h2>{paragraphs}")
    related = []
    for other in pages:
        if other["slug"] == page["slug"]:
            continue
        href = rel_link(page["path"], other["path"])
        related.append(f'<li><a href="{html.escape(href)}">{html.escape(other["h1"])}</a></li>')
    crumb_home = rel_link(page["path"], "/")
    body = f"""
  <main>
    <p class="crumb"><a href="{html.escape(crumb_home)}">{html.escape(site["name"])}</a> / {html.escape(page["h1"])}</p>
    <article>
      <h1>{html.escape(page["h1"])}</h1>
      <p class="meta">更新于 {html.escape(page["updated"])}</p>
      {"".join(sections)}
      <h2>相关笔记</h2>
      <ul class="links">{"".join(related)}</ul>
    </article>
  </main>
"""
    return _layout(
        site,
        title=f'{page["title"]}｜{site["name"]}',
        description=page["description"],
        canonical=absolute(site, page["path"]),
        css=rel_link(page["path"], "/assets/site.css", directory=False),
        jsonld=breadcrumb_json(site, page),
        from_path=page["path"],
        body=body,
    )


def render_sitemap(site: dict, pages: list[dict]) -> str:
    urls = [absolute(site, "/")] + [absolute(site, page["path"]) for page in pages]
    body = "\n".join(f"  <url><loc>{html.escape(url)}</loc></url>" for url in urls)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{body}\n"
        "</urlset>\n"
    )


def render_robots(site: dict) -> str:
    return "User-agent: *\nAllow: /\n\nSitemap: " + absolute(site, "/sitemap.xml") + "\n"


def build(root: Path | None = None, out: Path | None = None) -> Path:
    root = root or ROOT
    out = out or root / "docs"
    site, pages = load_site(root)
    validate(site, pages)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    (out / "assets").mkdir()
    shutil.copyfile(root / "content" / "site.css", out / "assets" / "site.css")
    (out / "index.html").write_text(render_home(site, pages), encoding="utf-8")
    for page in pages:
        folder = out / page["path"].strip("/")
        folder.mkdir(parents=True)
        (folder / "index.html").write_text(render_page(site, page, pages), encoding="utf-8")
    (out / "sitemap.xml").write_text(render_sitemap(site, pages), encoding="utf-8")
    (out / "robots.txt").write_text(render_robots(site), encoding="utf-8")
    return out


def main() -> None:
    out = build()
    print(f"wrote {out}")
