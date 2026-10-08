"""BM25 plus PageRank. Defense features are computed only from the page graph."""

from __future__ import annotations

import math
from collections import Counter, defaultdict

from seo_arena.corpus import Page
from seo_arena.tokenize import tokenize


def bm25(pages: list[Page], query: str, *, k1: float = 1.2, b: float = 0.75) -> dict[str, float]:
    docs = [(page.id, tokenize(page.text())) for page in pages]
    count = len(docs) or 1
    df: Counter[str] = Counter()
    for _, doc in docs:
        df.update(set(doc))
    avgdl = sum(len(doc) for _, doc in docs) / count
    query_terms = Counter(tokenize(query))
    scores: dict[str, float] = {}
    for page_id, doc in docs:
        tf = Counter(doc)
        length = len(doc) or 1
        score = 0.0
        for term, qtf in query_terms.items():
            freq = tf.get(term, 0)
            if freq == 0:
                continue
            idf = math.log(1.0 + (count - df[term] + 0.5) / (df[term] + 0.5))
            denom = freq + k1 * (1.0 - b + b * length / avgdl)
            score += idf * freq * (k1 + 1.0) / denom * qtf
        scores[page_id] = score
    return scores


def pagerank(pages: list[Page], *, damping: float = 0.85, iterations: int = 40) -> dict[str, float]:
    ids = [page.id for page in pages]
    index = {page_id: pos for pos, page_id in enumerate(ids)}
    count = len(ids)
    if count == 0:
        return {}
    outlinks: list[list[int]] = []
    for page in pages:
        linked = []
        seen: set[int] = set()
        for target in page.outlinks:
            pos = index.get(target)
            if pos is None or pos in seen or target == page.id:
                continue
            seen.add(pos)
            linked.append(pos)
        outlinks.append(linked)
    rank = [1.0 / count] * count
    for _ in range(iterations):
        nxt = [(1.0 - damping) / count] * count
        dangling = 0.0
        for pos, links in enumerate(outlinks):
            if not links:
                dangling += rank[pos]
                continue
            share = damping * rank[pos] / len(links)
            for dest in links:
                nxt[dest] += share
        if dangling:
            share = damping * dangling / count
            for pos in range(count):
                nxt[pos] += share
        rank = nxt
    return {page_id: rank[pos] for pos, page_id in enumerate(ids)}


def _peak(scores: dict[str, float]) -> dict[str, float]:
    peak = max(scores.values(), default=0.0) or 1.0
    return {key: value / peak for key, value in scores.items()}


def content_features(pages: list[Page]) -> dict[str, dict[str, float]]:
    """Repetition, short-page link support, and near-duplicate overlap."""
    tokens = {page.id: tokenize(page.text()) for page in pages}
    sets = {page_id: set(doc) for page_id, doc in tokens.items()}
    inbound: dict[str, list[str]] = defaultdict(list)
    for page in pages:
        for target in page.outlinks:
            if target in tokens and target != page.id:
                inbound[target].append(page.id)
    features: dict[str, dict[str, float]] = {}
    for page in pages:
        doc = tokens[page.id]
        repetition = 0.0
        if doc:
            repetition = 1.0 - len(set(doc)) / len(doc)
        sources = inbound.get(page.id, [])
        short_in = sum(1 for source in sources if len(tokens[source]) <= 12)
        farm = 0.0
        if len(sources) >= 4 and short_in / len(sources) >= 0.7:
            farm = short_in / len(sources)
        short_out = [target for target in page.outlinks if target in tokens and len(tokens[target]) <= 12]
        if len(page.outlinks) >= 2 and len(short_out) == len(set(page.outlinks)):
            farm = 1.0
        overlap = 0.0
        own = sets[page.id]
        own_len = len(doc)
        for other_id, other in sets.items():
            other_len = len(tokens[other_id])
            if other_id == page.id or not own or not other or own_len == 0 or other_len == 0:
                continue
            ratio = own_len / other_len
            if ratio < 0.5 or ratio > 2.0:
                continue
            overlap = max(overlap, len(own & other) / len(own | other))
        features[page.id] = {
            "repetition": repetition,
            "farm": farm,
            "near_dup": max(0.0, (overlap - 0.55) / 0.45),
        }
    return features


def score_pages(
    pages: list[Page],
    query: str,
    *,
    pagerank_weight: float = 0.25,
    weights: dict[str, float] | None = None,
) -> list[tuple[str, float]]:
    textual = _peak(bm25(pages, query))
    authority = _peak(pagerank(pages))
    penalty_weights = weights or {"repetition": 0.0, "farm": 0.0, "near_dup": 0.0}
    features = content_features(pages) if any(penalty_weights.values()) else {}
    scored: list[tuple[str, float]] = []
    for page in pages:
        base = (1.0 - pagerank_weight) * textual[page.id] + pagerank_weight * authority[page.id]
        feat = features.get(page.id, {})
        excess_rep = max(0.0, feat.get("repetition", 0.0) - 0.45)
        penalty = (
            penalty_weights.get("repetition", 0.0) * excess_rep
            + penalty_weights.get("farm", 0.0) * feat.get("farm", 0.0)
            + penalty_weights.get("near_dup", 0.0) * feat.get("near_dup", 0.0)
        )
        scored.append((page.id, base * (1.0 - min(0.98, penalty))))
    scored.sort(key=lambda item: (-item[1], item[0]))
    return scored
