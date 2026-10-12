"""Daily briefing agent: papers, models, and skills from public APIs."""

from __future__ import annotations

import html
import json
import os
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Callable, TypedDict
from zoneinfo import ZoneInfo

from langgraph.graph import END, START, StateGraph

from seo_arena.render import _FONTS, _nav, _social
from seo_arena.templates import TEMPLATES

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


class DigestState(TypedDict, total=False):
    papers: list[dict]
    models: list[dict]
    skills: list[dict]
    trace: list[dict]


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


def fetch_papers() -> list[dict]:
    query = "search_query=cat:cs.CL+OR+cat:cs.AI&sortBy=submittedDate&sortOrder=descending&start=0&max_results=6"
    raw = _get(f"https://export.arxiv.org/api/query?{query}")
    root = ET.fromstring(raw)
    items = []
    for entry in root.findall(f"{ATOM}entry"):
        link = entry.find(f"{ATOM}id").text or ""
        for candidate in entry.findall(f"{ATOM}link"):
            if candidate.get("rel") == "alternate" and candidate.get("href"):
                link = candidate.get("href")
                break
        authors = [node.text or "" for node in entry.findall(f"{ATOM}author/{ATOM}name")]
        who = authors[0] if authors else ""
        if len(authors) > 1:
            who = f"{who} 等"
        category = entry.find(f"{ATOM}category")
        term = category.get("term") if category is not None else "cs"
        updated = (entry.find(f"{ATOM}updated").text or "")[:10]
        items.append(
            {
                "title": _clip(entry.find(f"{ATOM}title").text or "", 200),
                "url": link.replace("http://", "https://"),
                "detail": _clip(entry.find(f"{ATOM}summary").text or ""),
                "meta": f"{term} · {updated} · {who}",
            }
        )
    return items


def fetch_models() -> list[dict]:
    raw = _get(
        "https://huggingface.co/api/models?pipeline_tag=text-generation&sort=trendingScore&direction=-1&limit=6"
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
                "meta": f"{likes:,} 次点赞 · {downloads:,} 次下载",
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
    chosen = [name for name in SKILL_ORDER if name in available]
    items = []
    for name in chosen:
        items.append(
            {
                "title": name,
                "url": f"https://github.com/anthropics/skills/tree/main/skills/{name}",
                "detail": _skill_description(name, headers),
                "meta": "anthropics/skills",
            }
        )
    return items


def build_digest_graph(fetchers: dict[str, Callable[[], list[dict]]] | None = None):
    fetchers = fetchers or {
        "papers": fetch_papers,
        "models": fetch_models,
        "skills": fetch_skills,
    }

    def fetch_papers_node(state: DigestState) -> dict:
        items = fetchers["papers"]()
        trace = list(state.get("trace") or [])
        trace.append({"tool": "fetch_papers", "source": "https://export.arxiv.org/api/query", "count": len(items)})
        return {"papers": items, "trace": trace}

    def fetch_models_node(state: DigestState) -> dict:
        items = fetchers["models"]()
        trace = list(state.get("trace") or [])
        trace.append({"tool": "fetch_models", "source": "https://huggingface.co/api/models", "count": len(items)})
        return {"models": items, "trace": trace}

    def fetch_skills_node(state: DigestState) -> dict:
        items = fetchers["skills"]()
        trace = list(state.get("trace") or [])
        trace.append({"tool": "fetch_skills", "source": "https://github.com/anthropics/skills", "count": len(items)})
        return {"skills": items, "trace": trace}

    graph = StateGraph(DigestState)
    graph.add_node("fetch_papers", fetch_papers_node)
    graph.add_node("fetch_models", fetch_models_node)
    graph.add_node("fetch_skills", fetch_skills_node)
    graph.add_edge(START, "fetch_papers")
    graph.add_edge("fetch_papers", "fetch_models")
    graph.add_edge("fetch_models", "fetch_skills")
    graph.add_edge("fetch_skills", END)
    return graph.compile()


def run_digest(fetchers: dict[str, Callable[[], list[dict]]] | None = None) -> tuple[dict, list[dict]]:
    final = build_digest_graph(fetchers).invoke({})
    fetched_at = datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M")
    report = {
        "fetched_at": fetched_at,
        "modules": [
            {
                "id": "papers",
                "title": "论文",
                "note": "arXiv 最新提交，分类 cs.CL 和 cs.AI。",
                "items": final["papers"],
            },
            {
                "id": "models",
                "title": "大模型",
                "note": "Hugging Face 上文本生成模型的趋势列表。",
                "items": final["models"],
            },
            {
                "id": "skills",
                "title": "Skill",
                "note": "anthropics/skills 里写文档、做设计和搭 agent 时会打开的几条。",
                "items": final["skills"],
            },
        ],
    }
    return report, final["trace"]


def render_digest(report: dict, brief: dict, plans: list[dict], template: dict) -> str:
    sections = []
    for module in report["modules"]:
        rows = []
        for item in module["items"]:
            detail = f'<span class="job-desc">{html.escape(item["detail"])}</span>' if item["detail"] else ""
            rows.append(
                f'<li><a href="{html.escape(item["url"])}"><strong>{html.escape(item["title"])}</strong>'
                f'<span class="job-meta">{html.escape(item["meta"])}</span>{detail}</a></li>'
            )
        sections.append(
            f'<section id="{html.escape(module["id"])}">'
            f'<h2>{html.escape(module["title"])}</h2>'
            f'<p>{html.escape(module["note"])}</p>'
            f'<ul class="jobs jobs-text">{"".join(rows)}</ul>'
            "</section>"
        )
    canonical = brief["site_url"].rstrip("/") + "/ai/"
    title = "今日 AI 简报"
    description = "论文、大模型和 Skill 的当日条目，链接指向原文。"
    return f"""<!DOCTYPE html>
<html lang="zh-CN" data-template="{html.escape(template["id"])}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(title)}｜{html.escape(brief["brand"])}</title>
  <meta name="description" content="{html.escape(description)}">
  {_social(title, description, canonical, "website")}
  <meta name="theme-color" content="{html.escape(template["tokens"]["paper"])}">
  <link rel="canonical" href="{html.escape(canonical)}">
  {_FONTS}
  <link rel="stylesheet" href="../assets/site.css">
</head>
<body>
  <header class="bar"><div class="wrap bar-inner">{_nav("/ai/", brief["brand"], plans, "/ai/")}</div></header>
  <main>
    <article class="wrap">
      <h1>{html.escape(title)}</h1>
      <p class="lede">更新于 {html.escape(report["fetched_at"])}。下面每条都能点进原文，标题和数字来自接口，没有另写摘要。</p>
      {"".join(sections)}
    </article>
  </main>
  <footer><div class="wrap"><p>{html.escape(brief["brand"])}。这一页每天重新拉取。</p></div></footer>
</body>
</html>
"""


def _add_sitemap(out: Path, url: str) -> None:
    path = out / "sitemap.xml"
    if not path.exists() or url in path.read_text(encoding="utf-8"):
        return
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("</urlset>", f"  <url><loc>{html.escape(url)}</loc></url>\n</urlset>"), encoding="utf-8")


def publish_digest(brief: dict, plans: list[dict], template: dict, out: Path, root: Path, fetchers=None) -> dict:
    report, trace = run_digest(fetchers)
    folder = out / "ai"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "index.html").write_text(render_digest(report, brief, plans, template), encoding="utf-8")
    _add_sitemap(out, brief["site_url"].rstrip("/") + "/ai/")
    records = root / "records"
    records.mkdir(exist_ok=True)
    (records / "digest.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (records / "digest-trace.json").write_text(
        json.dumps({"fetched_at": report["fetched_at"], "steps": trace}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report
