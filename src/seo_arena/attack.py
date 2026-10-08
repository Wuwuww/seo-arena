"""Synthetic SEO edits. They only rewrite this sandbox web."""

from __future__ import annotations

from seo_arena.corpus import Page, Query, clone_pages


def _spam_id(query: Query) -> str:
    return f"spam-{query.id}"


def _natural_spam_body(query: Query) -> str:
    return f"关于{query.text.replace(' ', '')}，本文汇总一份公开说明，供检索对照。"


def _stuffed_body(query: Query, repeats: int) -> str:
    phrase = query.text.replace(" ", "")
    return " ".join([phrase] * repeats)


def _apply(pages: list[Page], query: Query, *, body: str, farms: int, doors: int) -> None:
    target = _spam_id(query)
    farm_ids = [f"farm-{query.id}-{index}" for index in range(farms)]
    door_ids = [f"door-{query.id}-{index}" for index in range(doors)]
    pages.append(Page(target, query.text, body, list(farm_ids), "spam"))
    for farm_id in farm_ids:
        pages.append(Page(farm_id, "相关入口", "点击进入", [target], "spam"))
    for index, door_id in enumerate(door_ids):
        # A doorway does not point at the farm. Overlap and repetition have to catch it.
        pages.append(Page(door_id, query.text, body + f" 版本{index}", [], "spam"))


def attack(pages: list[Page], queries: list[Query], tactic: str) -> list[Page]:
    """Return a new web with one spam campaign per query."""
    if tactic not in {"none", "stuff", "farm", "doorway", "combined"}:
        raise ValueError(f"未知打法: {tactic}")
    edited = clone_pages(pages)
    if tactic == "none":
        return edited
    for query in queries:
        if tactic == "stuff":
            _apply(edited, query, body=_stuffed_body(query, 16), farms=0, doors=0)
        elif tactic == "farm":
            _apply(edited, query, body=_natural_spam_body(query), farms=8, doors=0)
        elif tactic == "doorway":
            _apply(edited, query, body=_natural_spam_body(query), farms=0, doors=4)
        else:
            _apply(edited, query, body=_stuffed_body(query, 16), farms=8, doors=3)
    return edited
