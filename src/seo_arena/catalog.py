"""Executable on-page actions. Sources are public documents, not copied guides."""

METHODS = [
    {
        "id": "unique_title",
        "gap": "title",
        "source": "https://developers.google.com/search/docs/appearance/title-link",
        "does": "每页一个不同的 title，写明这一页要回答的问题，并带上品牌。",
    },
    {
        "id": "meta_description",
        "gap": "description",
        "source": "https://developers.google.com/search/docs/appearance/snippet",
        "does": "每页写一段独立的 meta description，概括这一页的结论。",
    },
    {
        "id": "single_h1",
        "gap": "h1",
        "source": "https://developers.google.com/search/docs/appearance/title-link",
        "does": "页面上只放一个 h1，作为视觉上的主标题。",
    },
    {
        "id": "answer_first",
        "gap": "body",
        "source": "https://developers.google.com/search/docs/fundamentals/seo-starter-guide",
        "does": "第一段用看得见的文字回答查询，不把正文只放进脚本。",
    },
    {
        "id": "self_canonical",
        "gap": "canonical",
        "source": "https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls",
        "does": "canonical 指向这一页自己的网址，并与 sitemap 使用同一条。",
    },
    {
        "id": "descriptive_anchor",
        "gap": "links",
        "source": "https://developers.google.com/search/docs/crawling-indexing/links-crawlable",
        "does": "站内链接用目标页的标题做锚文本，保证目标页能从其他页点到。",
    },
    {
        "id": "breadcrumb_jsonld",
        "gap": "jsonld",
        "source": "https://developers.google.com/search/docs/appearance/structured-data/breadcrumb",
        "does": "JSON-LD 面包屑与页面上看得见的路径一致。",
    },
    {
        "id": "sitemap_and_robots",
        "gap": "sitemap",
        "source": "https://developers.google.com/search/docs/crawling-indexing/sitemaps/overview",
        "does": "把要索引的网址写入 sitemap，并在 robots.txt 里指出这份 sitemap。",
    },
]


def lookup_methods(gap: str | None = None) -> list[dict]:
    if gap is None:
        return list(METHODS)
    return [method for method in METHODS if method["gap"] == gap]
