"""Attacker picks a tactic on the train queries. Defender picks penalties on that web."""

from __future__ import annotations

import json
from pathlib import Path

from seo_arena.attack import attack
from seo_arena.corpus import Query, base_web
from seo_arena.metrics import legit_mrr, spam_at_k

TACTICS = ("stuff", "farm", "doorway", "combined")
DEFENSE_GRID = (0.0, 0.8, 1.6, 3.2)


def _split(queries: list[Query], name: str) -> list[Query]:
    return [query for query in queries if query.split == name]


def choose_tactic(pages, queries: list[Query]) -> str:
    """Offense: the tactic that puts the most spam into train top-5."""
    best = "stuff"
    best_spam = -1.0
    for tactic in TACTICS:
        edited = attack(pages, queries, tactic)
        leaked = spam_at_k(edited, queries)
        if leaked > best_spam:
            best = tactic
            best_spam = leaked
    return best


def choose_defense(pages, queries: list[Query], *, reference_mrr: float | None = None) -> dict[str, float]:
    """Defense: cut train spam without dropping legitimate MRR below the clean web."""
    floor = legit_mrr(pages, queries) if reference_mrr is None else reference_mrr
    best = {"repetition": 0.0, "farm": 0.0, "near_dup": 0.0}
    best_key = (-1.0, -1.0)
    for repetition in DEFENSE_GRID:
        for farm in DEFENSE_GRID:
            for near_dup in DEFENSE_GRID:
                weights = {"repetition": repetition, "farm": farm, "near_dup": near_dup}
                leaked = spam_at_k(pages, queries, weights)
                kept = legit_mrr(pages, queries, weights)
                if kept + 1e-9 < 0.85 * floor:
                    continue
                key = (1.0 - leaked, kept)
                if key > best_key:
                    best_key = key
                    best = weights
    return best


def run() -> dict:
    pages, queries = base_web()
    train = _split(queries, "train")
    test = _split(queries, "test")
    tactic = choose_tactic(pages, train)
    attacked = attack(pages, queries, tactic)
    weights = choose_defense(attacked, train, reference_mrr=legit_mrr(pages, train))
    rows = []
    for name, split in (("train", train), ("test", test)):
        rows.append(
            {
                "split": name,
                "clean_spam_at_5": spam_at_k(pages, split),
                "clean_legit_mrr": legit_mrr(pages, split),
                "attack_spam_at_5": spam_at_k(attacked, split),
                "attack_legit_mrr": legit_mrr(attacked, split),
                "defense_spam_at_5": spam_at_k(attacked, split, weights),
                "defense_legit_mrr": legit_mrr(attacked, split, weights),
            }
        )
    by_tactic = []
    for name in ("none",) + TACTICS:
        edited = attack(pages, queries, name)
        by_tactic.append(
            {
                "tactic": name,
                "test_spam_at_5": spam_at_k(edited, test),
                "test_legit_mrr": legit_mrr(edited, test),
            }
        )
    return {
        "tactic": tactic,
        "defense": weights,
        "splits": rows,
        "tactics_on_test": by_tactic,
    }


def main() -> None:
    report = run()
    text = json.dumps(report, ensure_ascii=False, indent=2)
    print(text)
    output = Path("runs")
    output.mkdir(exist_ok=True)
    (output / "arena.json").write_text(text + "\n", encoding="utf-8")
