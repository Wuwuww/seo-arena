import json
from pathlib import Path

from seo_arena.agent import load_brief, run_agent
from seo_arena.flow import build_graph
from seo_arena.render import render_site

ROOT = Path(__file__).resolve().parents[1]


def test_flow_routes_gaps_before_sitemap():
    graph = build_graph()
    nodes = set(graph.get_graph().nodes)
    assert {"inspect", "lookup", "choose", "apply", "next_page", "cross_link", "audit", "revise", "present", "sitemap"} <= nodes


def test_audit_flags_stuffing_and_revision_removes_the_extra_repeats():
    from seo_arena.audit import audit_plans, revise_plans

    plans = [
        {
            "path": "/a/",
            "query": "胎压",
            "title": "胎压｜南门",
            "description": "按侧壁区间充气，公路车和山地车分开看，雨天取中段。",
            "h1": "胎压",
            "paragraphs": ["胎压？可以打。", "胎压胎压胎压胎压，这段只是在重复查询。"],
            "canonical": "https://example.com/a/",
            "links": [],
            "offer": "按侧壁区间充气",
            "detail": "雨天取中段，避免打满后碾坑爆胎。",
            "close": "充完在门口压一压胎侧。",
            "brand": "南门",
        }
    ]
    issues = audit_plans(plans, "https://example.com")
    assert "query_stuffing" in {issue["code"] for issue in issues}
    revised = revise_plans(plans, issues)
    assert revised[0]["paragraphs"][1].count("胎压") == 0


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
        assert "<figure>" in text
        assert plan["figure"]["alt"] in text
        assert "<figcaption>" in text
        assert 'role="img"' in text
        payload = json.loads(text.split('application/ld+json">', 1)[1].split("</script>", 1)[0])
        crumbs = payload["@graph"][0]
        assert crumbs["itemListElement"][-1]["name"] == plan["h1"]
        assert crumbs["itemListElement"][-1]["item"] == plan["canonical"]
