import json
from pathlib import Path

from seo_arena.agent import load_brief, run_agent
from seo_arena.flow import build_graph
from seo_arena.render import render_site

ROOT = Path(__file__).resolve().parents[1]


def test_flow_routes_gaps_before_sitemap():
    graph = build_graph()
    nodes = set(graph.get_graph().nodes)
    assert {"inspect", "lookup", "choose", "apply", "next_page", "cross_link", "sitemap"} <= nodes


def test_agent_fills_every_page_from_catalog_tools():
    brief = load_brief(ROOT / "briefs" / "nanmen.json")
    plans, trace = run_agent(brief)
    assert len(plans) == 4
    titles = [plan["title"] for plan in plans]
    assert len(titles) == len(set(titles))
    applies = [step for step in trace if step["tool"] == "apply"]
    assert {step["method"] for step in applies} >= {
        "unique_title",
        "meta_description",
        "single_h1",
        "answer_first",
        "self_canonical",
        "breadcrumb_jsonld",
        "sitemap_and_robots",
    }
    assert all(step["source"].startswith("https://developers.google.com/") for step in applies)
    for plan in plans:
        assert plan["query"] in plan["title"]
        assert plan["query"] in plan["paragraphs"][0]
        assert plan["canonical"] == brief["site_url"] + plan["path"]
        assert len(plan["links"]) == 3


def test_rendered_site_matches_the_plan(tmp_path):
    brief = load_brief(ROOT / "briefs" / "nanmen.json")
    plans, _trace = run_agent(brief)
    render_site(brief, plans, ROOT, tmp_path)
    css = (tmp_path / "assets" / "site.css").read_text(encoding="utf-8")
    assert "display:none" not in css.replace(" ", "")
    sitemap = (tmp_path / "sitemap.xml").read_text(encoding="utf-8")
    robots = (tmp_path / "robots.txt").read_text(encoding="utf-8")
    assert robots.strip().endswith(brief["site_url"] + "/sitemap.xml")
    for plan in plans:
        text = (tmp_path / plan["path"].strip("/") / "index.html").read_text(encoding="utf-8")
        assert text.count("<h1>") == 1
        assert plan["canonical"] in text
        assert plan["canonical"] in sitemap
        assert plan["query"] in text
        payload = json.loads(text.split('application/ld+json">', 1)[1].split("</script>", 1)[0])
        crumbs = payload["@graph"][0]
        assert crumbs["itemListElement"][-1]["name"] == plan["h1"]
        assert crumbs["itemListElement"][-1]["item"] == plan["canonical"]
