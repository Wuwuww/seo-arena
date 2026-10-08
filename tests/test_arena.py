from seo_arena.arena import choose_defense, choose_tactic, run
from seo_arena.attack import attack
from seo_arena.corpus import base_web
from seo_arena.metrics import legit_mrr, spam_at_k
from seo_arena.rank import content_features


def test_clean_web_has_no_spam_and_ranks_the_labeled_page_first():
    pages, queries = base_web()
    assert spam_at_k(pages, queries) == 0.0
    assert legit_mrr(pages, queries) == 1.0


def test_stuffing_is_visible_to_the_repetition_feature():
    pages, queries = base_web()
    query = queries[0]
    edited = attack(pages, [query], "stuff")
    features = content_features(edited)
    assert features[f"spam-{query.id}"]["repetition"] > features["p-huangshan-season"]["repetition"]


def test_link_farm_is_visible_without_using_the_spam_label():
    pages, queries = base_web()
    query = queries[0]
    edited = attack(pages, [query], "farm")
    features = content_features(edited)
    assert features[f"spam-{query.id}"]["farm"] >= 0.7
    assert features["p-huangshan-season"]["farm"] == 0.0


def test_combined_attack_raises_test_spam_and_defense_cuts_it():
    report = run()
    test = next(row for row in report["splits"] if row["split"] == "test")
    assert report["tactic"] == "combined"
    assert test["attack_spam_at_5"] > test["clean_spam_at_5"]
    assert test["defense_spam_at_5"] < test["attack_spam_at_5"]
    assert test["defense_legit_mrr"] >= 0.85 * test["clean_legit_mrr"]
    assert any(value > 0.0 for value in report["defense"].values())


def test_defender_refuses_a_weight_that_only_exists_to_hurt_legit_pages():
    pages, queries = base_web()
    train = [query for query in queries if query.split == "train"]
    attacked = attack(pages, queries, "combined")
    weights = choose_defense(attacked, train, reference_mrr=legit_mrr(pages, train))
    assert legit_mrr(attacked, train, weights) >= 0.85 * legit_mrr(attacked, train)


def test_attacker_picks_the_same_tactic_every_time():
    pages, queries = base_web()
    train = [query for query in queries if query.split == "train"]
    assert choose_tactic(pages, train) == choose_tactic(pages, train)
