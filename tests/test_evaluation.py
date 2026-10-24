from analyzer.evaluation import (Pair, auc, evaluate, load_eval, pearson, spearman, top1_accuracy,
                                 tune_weights, weight_grid)


def test_spearman_perfect_and_reversed():
    assert abs(spearman([1, 2, 3, 4], [10, 20, 30, 40]) - 1) < 1e-9
    assert abs(spearman([1, 2, 3, 4], [4, 3, 2, 1]) + 1) < 1e-9


def test_spearman_handles_ties():
    assert abs(spearman([1, 1, 2], [1, 2, 3]) - 0.8660254) < 1e-6


def test_pearson_constant_input_is_zero():
    assert pearson([1, 1, 1], [1, 2, 3]) == 0.0


def test_auc():
    assert auc([0.9, 0.8, 0.3, 0.2], [True, True, False, False]) == 1.0
    assert auc([0.5, 0.5], [True, False]) == 0.5
    assert auc([0.1, 0.9], [True, False]) == 0.0


def _pair(rid, jd, label):
    return Pair(rid, jd, label, "", "")


def test_top1_accuracy_with_ties():
    pairs = [_pair("r1", "a", 3), _pair("r1", "b", 1), _pair("r2", "a", 0), _pair("r2", "b", 2)]
    assert top1_accuracy(pairs, [0.9, 0.2, 0.1, 0.8]) == 1.0
    assert top1_accuracy(pairs, [0.2, 0.9, 0.1, 0.8]) == 0.5
    assert top1_accuracy(pairs, [0.5, 0.5, 0.1, 0.8]) == 0.75  # r1 tie -> half credit


def test_weight_grid_valid():
    grid = list(weight_grid())
    assert grid and all(abs(sum(w.values()) - 1) < 1e-9 for w in grid)
    assert all(w["required"] >= 0.3 and w["semantic"] <= 0.5 for w in grid)


def test_tune_weights_picks_the_informative_component():
    pairs = [_pair("r", str(i), label) for i, label in enumerate([0, 1, 2, 3])]
    comps = [{"required": v, "preferred": 0.5, "semantic": 1 - v} for v in (0.0, 0.3, 0.6, 1.0)]
    assert tune_weights(pairs, comps)["required"] >= 0.5


def test_bundled_dataset_is_well_formed():
    pairs = load_eval()
    assert len(pairs) == 56
    assert {p.label for p in pairs} <= {0, 1, 2, 3}
    assert len({p.resume_id for p in pairs}) == 8 and len({p.jd_id for p in pairs}) == 7


def test_regression_gate_on_bundled_benchmark():
    """If a change makes the scorer much worse at ranking fits, this fails."""
    hybrid = evaluate()["table"]["Hybrid v1.0 (+ implications + OR groups)"]
    assert hybrid["spearman"] >= 0.60
    assert hybrid["auc_good"] >= 0.85
    assert hybrid["top1"] >= 0.85


def test_ablation_features_do_not_hurt():
    t = evaluate()["table"]
    assert t["Hybrid v1.0 (+ implications + OR groups)"]["spearman"] >= t["Hybrid v0.1 (no implications, no OR groups)"]["spearman"]
