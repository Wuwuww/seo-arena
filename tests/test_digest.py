from seo_arena.digest import build_digest_graph, render_digest, run_digest
from seo_arena.templates import TEMPLATES


def _item(title: str) -> dict:
    return {"title": title, "url": f"https://example.com/{title}", "detail": "接口原文", "meta": "来源"}


def test_digest_graph_fetches_three_modules():
    nodes = set(build_digest_graph().get_graph().nodes)
    assert {"fetch_papers", "fetch_models", "fetch_skills"} <= nodes
    report, trace = run_digest(
        {
            "papers": lambda: [_item("paper")],
            "models": lambda: [_item("model")],
            "skills": lambda: [_item("skill")],
        }
    )
    assert [step["tool"] for step in trace] == ["fetch_papers", "fetch_models", "fetch_skills"]
    html = render_digest(
        report,
        {"brand": "南门单车", "site_url": "https://example.com"},
        [{"path": "/tire-pressure/", "h1": "自行车胎压打到多少"}],
        TEMPLATES[0],
    )
    assert html.count("<h1>") == 1
    assert "论文" in html and "大模型" in html and "Skill" in html
    assert "https://example.com/paper" in html
    assert "display:none" not in html.replace(" ", "")
