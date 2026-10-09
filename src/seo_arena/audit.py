"""Public audit checks used by site crawlers: titles, snippets, body, links, canonicals."""

from __future__ import annotations

import re

FIXABLE = {"title_length", "description_length", "thin_body", "query_stuffing"}


def _chars(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def audit_plans(plans: list[dict], site_url: str) -> list[dict]:
    issues: list[dict] = []
    titles = [plan["title"] for plan in plans]
    descriptions = [plan["description"] for plan in plans]
    for plan in plans:
        path = plan["path"]
        if not plan["title"]:
            issues.append({"path": path, "code": "title_missing"})
        elif plan["title"].count(plan["query"]) > 1 or _chars(plan["title"]) > 32 or _chars(plan["title"]) < 8:
            issues.append({"path": path, "code": "title_length"})
        if titles.count(plan["title"]) > 1:
            issues.append({"path": path, "code": "title_duplicate"})
        if not plan["description"]:
            issues.append({"path": path, "code": "description_missing"})
        elif _chars(plan["description"]) > 80 or _chars(plan["description"]) < 20:
            issues.append({"path": path, "code": "description_length"})
        if descriptions.count(plan["description"]) > 1:
            issues.append({"path": path, "code": "description_duplicate"})
        if plan["h1"] != plan["query"]:
            issues.append({"path": path, "code": "h1_mismatch"})
        body = "".join(plan["paragraphs"])
        if _chars(body) < 80:
            issues.append({"path": path, "code": "thin_body"})
        if body.count(plan["query"]) > 2:
            issues.append({"path": path, "code": "query_stuffing"})
        expected = site_url.rstrip("/") + path
        if plan["canonical"] != expected:
            issues.append({"path": path, "code": "canonical_mismatch"})
        anchors = {link["anchor"] for link in plan["links"]}
        expected_anchors = {other["h1"] for other in plans if other["path"] != path}
        if anchors != expected_anchors:
            issues.append({"path": path, "code": "anchor_mismatch"})
    return issues


def _clip(text: str, limit: int) -> str:
    compact = re.sub(r"\s+", "", text)
    if _chars(compact) <= limit:
        return text
    cut = compact[:limit]
    for mark in ("。", "，", "、"):
        pivot = cut.rfind(mark)
        if pivot >= 20:
            return cut[: pivot + 1]
    return cut


def revise_plans(plans: list[dict], issues: list[dict]) -> list[dict]:
    flagged = {issue["path"]: {item["code"] for item in issues if item["path"] == issue["path"]} for issue in issues}
    for plan in plans:
        codes = flagged.get(plan["path"], set())
        if "title_length" in codes:
            plan["title"] = _clip(f"{plan['query']}｜{plan['brand']}", 32)
        if "description_length" in codes:
            plan["description"] = _clip(f"{plan['offer']}。{plan['detail']}", 80)
        if "thin_body" in codes:
            extra = plan["close"]
            if extra not in plan["paragraphs"]:
                plan["paragraphs"].append(extra)
        if "query_stuffing" in codes:
            kept = []
            seen = 0
            for paragraph in plan["paragraphs"]:
                seen += paragraph.count(plan["query"])
                if seen <= 2:
                    kept.append(paragraph)
                else:
                    kept.append(paragraph.replace(plan["query"], plan["brand"]))
            plan["paragraphs"] = kept
    return plans
