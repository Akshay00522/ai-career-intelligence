"""Evaluation harness: metrics, baselines, ablations and cross-validated weight tuning.

Pairs are (resume, job description, human fit label 0-3). A good scorer ranks
pairs the way the human labels do, so we report rank-based metrics:

  spearman  - rank correlation between score and label (ties handled)
  auc_good  - P(score of a good-fit pair > score of a not-good pair); good = label >= 2
  top1      - for each resume, does the top-scored JD match the best-labelled JD?
"""
from __future__ import annotations

import csv
import itertools
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .pipeline import DEFAULT_WEIGHTS, analyze, blend
from .similarity import tfidf_similarity
from .skills import extract_skills

DEFAULT_EVAL_DIR = Path(__file__).resolve().parents[2] / "data" / "eval"


@dataclass
class Pair:
    resume_id: str
    jd_id: str
    label: int
    resume: str
    jd: str


def load_eval(directory: str | Path | None = None) -> list[Pair]:
    d = Path(directory or DEFAULT_EVAL_DIR)
    pairs = []
    with open(d / "labels.csv", newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            pairs.append(Pair(
                row["resume"], row["jd"], int(row["label"]),
                (d / "resumes" / f"{row['resume']}.txt").read_text(encoding="utf-8"),
                (d / "jobs" / f"{row['jd']}.txt").read_text(encoding="utf-8"),
            ))
    return pairs


# ----------------------------------------------------------------- metrics
def _ranks(x) -> np.ndarray:
    """Average ranks (ties share the mean rank)."""
    x = np.asarray(x, dtype=float)
    order = np.argsort(x, kind="mergesort")
    ranks = np.empty(len(x))
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x[order[j + 1]] == x[order[i]]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2 + 1
        i = j + 1
    return ranks


def pearson(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    if a.std() == 0 or b.std() == 0:
        return 0.0
    return float(np.corrcoef(a, b)[0, 1])


def spearman(a, b) -> float:
    return pearson(_ranks(a), _ranks(b))


def auc(scores, positives) -> float:
    pos = [s for s, p in zip(scores, positives) if p]
    neg = [s for s, p in zip(scores, positives) if not p]
    if not pos or not neg:
        return float("nan")
    wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
    return wins / (len(pos) * len(neg))


def top1_accuracy(pairs: list[Pair], scores) -> float:
    """Tie-aware: credit = share of top-scored JDs that are among the best-labelled."""
    by_resume: dict[str, list[tuple[float, int]]] = {}
    for p, s in zip(pairs, scores):
        by_resume.setdefault(p.resume_id, []).append((s, p.label))
    credits = []
    for items in by_resume.values():
        top = max(s for s, _ in items)
        best = max(label for _, label in items)
        winners = [label for s, label in items if s == top]
        credits.append(sum(label == best for label in winners) / len(winners))
    return float(np.mean(credits))


def summarize(pairs: list[Pair], scores) -> dict:
    labels = [p.label for p in pairs]
    return {
        "spearman": spearman(scores, labels),
        "pearson": pearson(scores, labels),
        "auc_good": auc(scores, [lab >= 2 for lab in labels]),
        "top1": top1_accuracy(pairs, scores),
    }


# ---------------------------------------------------------------- scorers
def score_jaccard(pairs: list[Pair]) -> list[float]:
    out = []
    for p in pairs:
        a, b = extract_skills(p.resume), extract_skills(p.jd)
        out.append(100 * len(a & b) / len(a | b) if a | b else 0.0)
    return out


def score_tfidf(pairs: list[Pair]) -> list[float]:
    return [100 * tfidf_similarity(p.resume, p.jd) for p in pairs]


def run_configs(pairs: list[Pair]) -> dict[str, list]:
    """Run every system variant once. Hybrid variants return full AnalysisResults."""
    return {
        "Baseline A: skill overlap (Jaccard)": score_jaccard(pairs),
        "Baseline B: TF-IDF cosine only": score_tfidf(pairs),
        "Hybrid v0.1 (no implications, no OR groups)": [
            analyze(p.resume, p.jd, use_implications=False, use_or_groups=False) for p in pairs],
        "Hybrid + skill implications": [
            analyze(p.resume, p.jd, use_implications=True, use_or_groups=False) for p in pairs],
        "Hybrid v1.0 (+ implications + OR groups)": [
            analyze(p.resume, p.jd) for p in pairs],
    }


def _as_scores(values) -> list[float]:
    return [v.score if hasattr(v, "score") else v for v in values]


# ----------------------------------------------------------------- tuning
def weight_grid(step: float = 0.05):
    n = int(round(1 / step))
    for r, p in itertools.product(range(n + 1), repeat=2):
        s = n - r - p
        w = {"required": r * step, "preferred": p * step, "semantic": s * step}
        if s >= 0 and w["required"] >= 0.3 and w["semantic"] <= 0.5 and w["preferred"] <= 0.3:
            yield w


def _dist(w: dict) -> float:
    return sum(abs(w[k] - DEFAULT_WEIGHTS[k]) for k in w)


def tune_weights(pairs: list[Pair], components: list[dict]) -> dict:
    """Grid-search weights maximising Spearman; ties go to the weights nearest the default."""
    labels = [p.label for p in pairs]
    best, best_key = None, None
    for w in weight_grid():
        score = spearman([blend(c, w) for c in components], labels)
        key = (round(score, 6), -_dist(w))
        if best_key is None or key > best_key:
            best, best_key = w, key
    return best


def leave_one_resume_out(pairs: list[Pair], components: list[dict]) -> tuple[list[float], dict]:
    """Tune on all-but-one resume, score the held-out resume. Returns pooled scores."""
    resumes = sorted({p.resume_id for p in pairs})
    pooled = [0.0] * len(pairs)
    chosen = {}
    for held in resumes:
        train = [i for i, p in enumerate(pairs) if p.resume_id != held]
        test = [i for i, p in enumerate(pairs) if p.resume_id == held]
        w = tune_weights([pairs[i] for i in train], [components[i] for i in train])
        chosen[held] = w
        for i in test:
            pooled[i] = 100 * blend(components[i], w)
    return pooled, chosen


# ----------------------------------------------------------------- driver
def evaluate(directory: str | Path | None = None) -> dict:
    pairs = load_eval(directory)
    configs = run_configs(pairs)
    table = {name: summarize(pairs, _as_scores(vals)) for name, vals in configs.items()}

    full = configs["Hybrid v1.0 (+ implications + OR groups)"]
    components = [r.components for r in full]
    cv_scores, chosen = leave_one_resume_out(pairs, components)
    tuned_all = tune_weights(pairs, components)

    return {
        "n_pairs": len(pairs),
        "n_resumes": len({p.resume_id for p in pairs}),
        "n_jds": len({p.jd_id for p in pairs}),
        "table": table,
        "cv_tuned": summarize(pairs, cv_scores),
        "tuned_all_data_weights": tuned_all,
        "cv_weights": chosen,
        "pairs": pairs,
        "full_results": full,
    }


def per_resume_top1(pairs: list[Pair], results) -> list[dict]:
    rows = []
    for rid in sorted({p.resume_id for p in pairs}):
        items = [(r.score, p) for p, r in zip(pairs, results) if p.resume_id == rid]
        top = max(items, key=lambda t: t[0])
        best_label = max(p.label for _, p in items)
        best_jds = [p.jd_id for _, p in items if p.label == best_label]
        rows.append({"resume": rid, "predicted": top[1].jd_id, "predicted_score": top[0],
                     "labelled_best": best_jds, "correct": top[1].label == best_label})
    return rows


def findings(res: dict) -> list[str]:
    """Plain-language conclusions computed from the numbers (so they cannot go stale)."""
    t = res["table"]
    hybrid = t["Hybrid v1.0 (+ implications + OR groups)"]
    tfidf = t["Baseline B: TF-IDF cosine only"]
    v01 = t["Hybrid v0.1 (no implications, no OR groups)"]
    out = []
    if hybrid["spearman"] >= tfidf["spearman"]:
        out.append(f"The full hybrid ranks pairs at least as well as TF-IDF alone (Spearman {hybrid['spearman']:.3f} vs {tfidf['spearman']:.3f}).")
    else:
        out.append(
            f"On rank correlation the full hybrid does NOT beat the TF-IDF-only baseline "
            f"(Spearman {hybrid['spearman']:.3f} vs {tfidf['spearman']:.3f}). Its advantage is explainability: "
            "it reports which required and preferred skills are matched or missing, which a similarity score cannot.")
    if hybrid["spearman"] > v01["spearman"]:
        out.append(f"Implications and OR groups together improved the hybrid (Spearman {v01['spearman']:.3f} -> {hybrid['spearman']:.3f}).")
    cv = res["cv_tuned"]
    out.append(
        f"Cross-validated weight tuning gave Spearman {cv['spearman']:.3f} versus {hybrid['spearman']:.3f} with the default weights, "
        "but the chosen weights differ across folds and the data is small, so the default weights were kept.")
    if all(abs(m["top1"] - 1.0) < 1e-9 for m in t.values()):
        out.append("Top-1 role accuracy is 1.00 for every system, so with this dataset it cannot separate them.")
    return out


def to_markdown(res: dict) -> str:
    lines = [
        "# Evaluation report", "",
        f"Dataset: {res['n_pairs']} labelled pairs ({res['n_resumes']} resumes x {res['n_jds']} job descriptions), "
        "labels 0-3 (poor / weak / good / strong fit). Regenerate with `python cli.py evaluate --write-report docs/EVALUATION.md`.", "",
        "## Ablation: baselines vs. each added feature", "",
        "| System | Spearman | AUC (good fit) | Top-1 role | Pearson |",
        "|---|---|---|---|---|",
    ]
    for name, m in res["table"].items():
        lines.append(f"| {name} | {m['spearman']:.3f} | {m['auc_good']:.3f} | {m['top1']:.2f} | {m['pearson']:.3f} |")
    cv = res["cv_tuned"]
    lines += [
        f"| Hybrid v1.0 with weights tuned by leave-one-resume-out CV | {cv['spearman']:.3f} | {cv['auc_good']:.3f} | {cv['top1']:.2f} | {cv['pearson']:.3f} |",
        "", "Default weights: " + ", ".join(f"{k}={v:.2f}" for k, v in DEFAULT_WEIGHTS.items()) + ".",
        "Weights tuned on all data (for reference only, optimistic): "
        + ", ".join(f"{k}={v:.2f}" for k, v in res["tuned_all_data_weights"].items()) + ".", "",
        "## Does the top-ranked role match the best-labelled role?", "",
        "| Resume | Top predicted JD (score) | Best-labelled JD(s) | Correct |", "|---|---|---|---|",
    ]
    for row in per_resume_top1(res["pairs"], res["full_results"]):
        lines.append(f"| {row['resume']} | {row['predicted']} ({row['predicted_score']}) | "
                     f"{', '.join(row['labelled_best'])} | {'yes' if row['correct'] else 'no'} |")
    lines += [
        "", "## Limitations (read before quoting these numbers)", "",
        "- The resumes and JDs are hand-written personas, not real documents, and the labels come from a single annotator. "
        "Treat this as a regression benchmark and smoke test, not as evidence of real-world accuracy.",
        "- The taxonomy and the test documents were written by the same person, so skill-extraction recall is optimistic.",
        "- 56 pairs from 8 resumes is small; differences of a few hundredths between systems are noise.",
        "- Embedding similarity (`--embedding`) is not part of this table; add it on a machine with `sentence-transformers` installed.",
        "- To strengthen the study: add real anonymised resumes and JDs with several annotators and report inter-annotator agreement.",
        "",
    ]
    return "\n".join(lines)
