"""Tool loop that fills a site plan, then checks it against public SEO audit items."""

from __future__ import annotations

import json
from pathlib import Path

def load_brief(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _empty_plan(page: dict, brand: str) -> dict:
    return {
        "slug": page["slug"],
        "path": f"/{page['slug']}/",
        "query": page["query"],
        "offer": page["offer"],
        "detail": page["detail"],
        "close": page["close"],
        "brand": brand,
        "title": "",
        "description": "",
        "h1": "",
        "paragraphs": [],
        "canonical": "",
        "links": [],
        "jsonld": False,
    }


def _missing(plan: dict) -> str | None:
    if not plan["title"]:
        return "title"
    if not plan["description"]:
        return "description"
    if not plan["h1"]:
        return "h1"
    if not plan["paragraphs"]:
        return "body"
    if not plan["canonical"]:
        return "canonical"
    if not plan["links"]:
        return "links"
    if not plan["jsonld"]:
        return "jsonld"
    return None


def apply_method(method: dict, plan: dict, site_url: str) -> dict:
    gap = method["gap"]
    if gap == "title":
        plan["title"] = f"{plan['query']}｜{plan['brand']}"
    elif gap == "description":
        plan["description"] = f"{plan['offer']}。{plan['detail']}"
    elif gap == "h1":
        plan["h1"] = plan["query"]
    elif gap == "body":
        plan["paragraphs"] = [
            f"{plan['query']}？{plan['offer']}。",
            plan["detail"],
            plan["close"],
        ]
    elif gap == "canonical":
        plan["canonical"] = site_url.rstrip("/") + plan["path"]
    elif gap == "links":
        plan["links"] = [{"href": "/", "anchor": plan["brand"]}]
    elif gap == "jsonld":
        plan["jsonld"] = True
    else:
        raise ValueError(f"未知步骤: {method['id']}")
    return plan


def _link_pages(plans: list[dict]) -> None:
    for plan in plans:
        plan["links"] = [
            {"href": other["path"], "anchor": other["h1"]}
            for other in plans
            if other["slug"] != plan["slug"]
        ]


class ScriptedAgent:
    """Picks the catalog action that fills the next empty slot."""

    def choose(self, gap: str, methods: list[dict]) -> dict:
        if not methods:
            raise RuntimeError(f"没有能补上 {gap} 的步骤")
        return methods[0]


def run_agent(brief: dict, agent=None) -> tuple[list[dict], list[dict]]:
    from seo_arena.flow import run_flow

    return run_flow(brief, agent or ScriptedAgent())


def write_records(brief: dict, plans: list[dict], trace: list[dict], root: Path) -> None:
    records = root / "records"
    records.mkdir(exist_ok=True)
    serp = {
        "judge": "谷歌自然结果在 Chrome 中的展现顺序。广告、地图和「人们也问」不计入名次。",
        "rows": [
            {
                "query": plan["query"],
                "path": plan["path"],
                "google_position": None,
                "checked_at": None,
            }
            for plan in plans
        ],
    }
    (records / "serp.json").write_text(json.dumps(serp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (records / "agent-trace.json").write_text(
        json.dumps({"brand": brief["brand"], "steps": trace}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
