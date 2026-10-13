"""Briefing agent: collect papers, models, and skills, then trim and check the issue."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Callable, TypedDict
from zoneinfo import ZoneInfo

from langgraph.graph import END, START, StateGraph

UA = "seo-arena-digest/0.1 (https://github.com/Wuwuww/seo-arena)"
ATOM = "{http://www.w3.org/2005/Atom}"
SKILL_ORDER = (
    "frontend-design",
    "skill-creator",
    "mcp-builder",
    "docx",
    "pdf",
    "webapp-testing",
)
class BriefingState(TypedDict, total=False):
    papers: list[dict]
    models: list[dict]
    skills: list[dict]
    issue: dict
    issues: list[dict]
    trace: list[dict]


SECTION_NOTES = {
    "papers": "arXiv 最新提交，分类 cs.CL 和 cs.AI。",
    "models": "Hugging Face 上文本生成模型的趋势列表。",
    "skills": "anthropics/skills 里写文档、做设计和搭 agent 时会打开的几条。",
}


def _clip(text: str, limit: int = 160) -> str:
    flat = " ".join(text.split())
    if len(flat) <= limit:
        return flat
    return flat[:limit].rstrip() + "…"


def _get(url: str, headers: dict | None = None) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": UA, **(headers or {})})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def _github_headers() -> dict:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or ""
    if not token:
        try:
            token = subprocess.check_output(["gh", "auth", "token"], text=True, stderr=subprocess.DEVNULL).strip()
        except (OSError, subprocess.CalledProcessError):
            token = ""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _text(entry: ET.Element, tag: str) -> str:
    node = entry.find(f"{ATOM}{tag}")
    return node.text if node is not None and node.text else ""


def fetch_papers() -> list[dict]:
    query = "search_query=cat:cs.CL+OR+cat:cs.AI&sortBy=submittedDate&sortOrder=descending&start=0&max_results=8"
    root = ET.fromstring(_get(f"https://export.arxiv.org/api/query?{query}"))
    items = []
    for entry in root.findall(f"{ATOM}entry"):
        link = _text(entry, "id")
        for candidate in entry.findall(f"{ATOM}link"):
            if candidate.get("rel") == "alternate" and candidate.get("href"):
                link = candidate.get("href") or link
                break
        authors = [node.text or "" for node in entry.findall(f"{ATOM}author/{ATOM}name")]
        who = authors[0] if authors else ""
        if len(authors) > 1:
            who = f"{who} 等"
        category = entry.find(f"{ATOM}category")
        term = category.get("term") if category is not None else "cs"
        updated = _text(entry, "updated")[:10]
        items.append(
            {
                "title": _clip(_text(entry, "title"), 200),
                "url": link.replace("http://", "https://"),
                "detail": _clip(_text(entry, "summary")),
                "bits": [bit for bit in (term, updated, who) if bit],
            }
        )
    return items


def fetch_models() -> list[dict]:
    raw = _get(
        "https://huggingface.co/api/models?pipeline_tag=text-generation&sort=trendingScore&direction=-1&limit=8"
    )
    items = []
    for model in json.loads(raw):
        name = model.get("id") or model.get("modelId") or ""
        likes = int(model.get("likes") or 0)
        downloads = int(model.get("downloads") or 0)
        items.append(
            {
                "title": name,
                "url": f"https://huggingface.co/{name}",
                "detail": "",
                "bits": [f"{likes:,} 次点赞", f"{downloads:,} 次下载"],
            }
        )
    return items


def _skill_description(name: str, headers: dict) -> str:
    url = f"https://raw.githubusercontent.com/anthropics/skills/main/skills/{name}/SKILL.md"
    text = _get(url, headers).decode("utf-8", errors="replace")
    if not text.startswith("---"):
        return ""
    front = text.split("---", 2)[1]
    for line in front.splitlines():
        if line.startswith("description:"):
            return _clip(line.split(":", 1)[1].strip().strip('"').strip("'"))
    return ""


def fetch_skills() -> list[dict]:
    headers = _github_headers()
    listing = json.loads(_get("https://api.github.com/repos/anthropics/skills/contents/skills", headers))
    available = {item["name"] for item in listing if item.get("type") == "dir"}
    items = []
    for name in SKILL_ORDER:
        if name not in available:
            continue
        items.append(
            {
                "title": name,
                "url": f"https://github.com/anthropics/skills/tree/main/skills/{name}",
                "detail": _skill_description(name, headers),
                "bits": ["anthropics/skills"],
            }
        )
    return items


def trim_items(items: list[dict]) -> list[dict]:
    seen: set[str] = set()
    kept = []
    for item in items:
        title = " ".join((item.get("title") or "").split())
        url = (item.get("url") or "").strip()
        if not title or not url.startswith("https://") or url in seen:
            continue
        seen.add(url)
        kept.append({**item, "title": title, "url": url})
        if len(kept) == 6:
            break
    return kept


def build_graph(fetchers: dict[str, Callable[[], list[dict]]] | None = None, now: Callable[[], datetime] | None = None):
    fetchers = fetchers or {"papers": fetch_papers, "models": fetch_models, "skills": fetch_skills}
    clock = now or (lambda: datetime.now(ZoneInfo("Asia/Shanghai")))

    def collect(key: str, source: str):
        def node(state: BriefingState) -> dict:
            items = fetchers[key]()
            trace = list(state.get("trace") or [])
            trace.append({"tool": f"fetch_{key}", "source": source, "count": len(items)})
            return {key: items, "trace": trace}

        return node

    def trim(state: BriefingState) -> dict:
        papers = trim_items(state.get("papers") or [])
        models = trim_items(state.get("models") or [])
        skills = trim_items(state.get("skills") or [])
        trace = list(state.get("trace") or [])
        trace.append({"tool": "trim", "kept": {"papers": len(papers), "models": len(models), "skills": len(skills)}})
        return {"papers": papers, "models": models, "skills": skills, "trace": trace}

    def compose(state: BriefingState) -> dict:
        moment = clock()
        issue = {
            "h1": f"{moment.month}月{moment.day}日",
            "year": str(moment.year),
            "fetched_at": moment.strftime("%Y-%m-%d %H:%M"),
            "sections": [
                {"id": "papers", "title": "论文", "note": SECTION_NOTES["papers"], "items": state.get("papers") or []},
                {"id": "models", "title": "大模型", "note": SECTION_NOTES["models"], "items": state.get("models") or []},
                {"id": "skills", "title": "Skill", "note": SECTION_NOTES["skills"], "items": state.get("skills") or []},
            ],
        }
        trace = list(state.get("trace") or [])
        trace.append({"tool": "compose", "h1": issue["h1"]})
        return {"issue": issue, "trace": trace}

    def audit(state: BriefingState) -> dict:
        issues = [
            {"code": "empty_section", "section": section["id"]}
            for section in state["issue"]["sections"]
            if not section["items"]
        ]
        trace = list(state.get("trace") or [])
        trace.append({"tool": "audit", "issues": [issue["code"] for issue in issues]})
        return {"issues": issues, "trace": trace}

    graph = StateGraph(BriefingState)
    graph.add_node("fetch_papers", collect("papers", "https://export.arxiv.org/api/query"))
    graph.add_node("fetch_models", collect("models", "https://huggingface.co/api/models"))
    graph.add_node("fetch_skills", collect("skills", "https://github.com/anthropics/skills"))
    graph.add_node("trim", trim)
    graph.add_node("compose", compose)
    graph.add_node("audit", audit)
    graph.add_edge(START, "fetch_papers")
    graph.add_edge("fetch_papers", "fetch_models")
    graph.add_edge("fetch_models", "fetch_skills")
    graph.add_edge("fetch_skills", "trim")
    graph.add_edge("trim", "compose")
    graph.add_edge("compose", "audit")
    graph.add_edge("audit", END)
    return graph.compile()


def run_briefing(fetchers=None, now=None) -> tuple[dict, list[dict]]:
    final = build_graph(fetchers, now).invoke({})
    return final["issue"], final["trace"]
