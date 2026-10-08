import json
from pathlib import Path

from seo_arena.build import build, load_site


ROOT = Path(__file__).resolve().parents[1]


def test_pages_declare_distinct_queries_and_blank_rank_slots():
    _site, pages = load_site(ROOT)
    queries = [page["query"] for page in pages]
    assert len(queries) == len(set(queries)) == 5
    record = json.loads((ROOT / "records" / "serp.json").read_text(encoding="utf-8"))
    assert [row["query"] for row in record["rows"]] == queries
    assert all(row["google_position"] is None and row["company_position"] is None for row in record["rows"])


def test_built_site_is_internally_consistent(tmp_path):
    out = build(ROOT, tmp_path)
    site, pages = load_site(ROOT)
    css = (out / "assets" / "site.css").read_text(encoding="utf-8")
    assert "display: none" not in css
    assert "display:none" not in css
    robots = (out / "robots.txt").read_text(encoding="utf-8")
    sitemap = (out / "sitemap.xml").read_text(encoding="utf-8")
    assert robots.strip().endswith(site["site_url"] + "/sitemap.xml")
    home = (out / "index.html").read_text(encoding="utf-8")
    assert home.count("<h1>") == 1
    assert f'<link rel="canonical" href="{site["site_url"]}/">' in home
    for page in pages:
        file = out / page["path"].strip("/") / "index.html"
        text = file.read_text(encoding="utf-8")
        assert text.count("<h1>") == 1
        assert f"<h1>{page['h1']}</h1>" in text
        assert page["query"] in text
        assert text.count(page["query"]) <= 4
        canonical = site["site_url"] + page["path"]
        assert f'<link rel="canonical" href="{canonical}">' in text
        assert canonical in sitemap
        assert "<article>" in text
        payload = text.split('application/ld+json">', 1)[1].split("</script>", 1)[0]
        data = json.loads(payload)
        crumbs = next(item for item in data["@graph"] if item["@type"] == "BreadcrumbList")
        assert [entry["position"] for entry in crumbs["itemListElement"]] == [1, 2]
        assert crumbs["itemListElement"][-1]["item"] == canonical
        assert crumbs["itemListElement"][-1]["name"] == page["h1"]
        for other in pages:
            if other["slug"] == page["slug"]:
                continue
            assert f">{other['h1']}</a>" in text
