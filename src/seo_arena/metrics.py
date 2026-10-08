"""Top-k quality on labeled relevant pages, plus how much spam leaked in."""

from __future__ import annotations

from seo_arena.corpus import Page, Query
from seo_arena.rank import score_pages


def ranking(pages: list[Page], query: Query, weights: dict[str, float] | None = None, k: int = 5) -> list[str]:
    return [page_id for page_id, _ in score_pages(pages, query.text, weights=weights)[:k]]


def spam_at_k(pages: list[Page], queries: list[Query], weights: dict[str, float] | None = None, k: int = 5) -> float:
    if not queries:
        return 0.0
    kinds = {page.id: page.kind for page in pages}
    total = 0
    for query in queries:
        total += sum(1 for page_id in ranking(pages, query, weights, k) if kinds.get(page_id) == "spam")
    return total / (len(queries) * k)


def legit_mrr(pages: list[Page], queries: list[Query], weights: dict[str, float] | None = None) -> float:
    if not queries:
        return 0.0
    score = 0.0
    for query in queries:
        order = [page_id for page_id, _ in score_pages(pages, query.text, weights=weights)]
        relevant = set(query.relevant)
        for rank, page_id in enumerate(order, start=1):
            if page_id in relevant:
                score += 1.0 / rank
                break
    return score / len(queries)
