from datetime import datetime
from zoneinfo import ZoneInfo

from seo_arena.digest import build_graph, run_briefing, trim_items
from seo_arena.render import render_issue, render_missing


def _item(title: str, url: str | None = None) -> dict:
    return {
        "title": title,
        "url": url or f"https://example.com/{title}",
        "detail": "接口原文",
        "bits": ["来源"],
    }


def test_trim_keeps_unique_https_titles():
    kept = trim_items(
        [
            _item("ok"),
            _item("  "),
            _item("dup"),
            _item("dup"),
            {"title": "bad", "url": "http://example.com/x", "detail": "", "bits": []},
            _item("later"),
        ]
    )
    assert [item["title"] for item in kept] == ["ok", "dup", "later"]


def test_loop_trims_then_composes_an_issue():
    nodes = set(build_graph().get_graph().nodes)
    assert {"fetch_papers", "fetch_models", "fetch_skills", "trim", "compose", "audit"} <= nodes
    moment = datetime(2026, 10, 13, 8, 30, tzinfo=ZoneInfo("Asia/Shanghai"))
    issue, trace = run_briefing(
        {
            "papers": lambda: [_item("paper"), _item("paper")],
            "models": lambda: [],
            "skills": lambda: [_item("skill")],
        },
        now=lambda: moment,
    )
    assert [step["tool"] for step in trace] == [
        "fetch_papers",
        "fetch_models",
        "fetch_skills",
        "trim",
        "compose",
        "audit",
    ]
    assert issue["h1"] == "10月13日"
    assert len(issue["sections"][0]["items"]) == 1
    assert trace[-1]["issues"] == ["empty_section"]
    page = render_issue(issue)
    assert page.count("<h1>") == 1
    assert "10月13日" in page
    assert "南门" not in page
    assert "https://example.com/paper" in page
    assert "这次没有拉到" in page
    assert "display:none" not in page.replace(" ", "")
    missing = render_missing()
    assert "南门" not in missing
    assert "回到今天的简报" in missing
