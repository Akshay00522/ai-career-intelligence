"""Skill-Gap Analyzer command line.

  python cli.py analyze resume.pdf jd.txt [--hours 8] [--market-dir DIR] [--report out.md] [--json] [--embedding]
  python cli.py evaluate [--dir DIR] [--write-report docs/EVALUATION.md] [--min-spearman X --min-auc Y]
  python cli.py market DIR [--top 15]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from analyzer.evaluation import evaluate, to_markdown as eval_markdown  # noqa: E402
from analyzer.market import demand_by_category, load_jds, skill_demand, top_skills  # noqa: E402
from analyzer.parsers import read_document  # noqa: E402
from analyzer.report import to_markdown  # noqa: E402
from analyzer.service import run_analysis  # noqa: E402


def cmd_analyze(a: argparse.Namespace) -> int:
    out = run_analysis(read_document(a.resume), read_document(a.jd),
                       "embedding" if a.embedding else "tfidf", a.hours, a.market_dir)
    if a.json:
        print(json.dumps(out, indent=2))
    else:
        print(to_markdown(out["analysis"], out["plan"]))
    if a.report:
        Path(a.report).write_text(to_markdown(out["analysis"], out["plan"]), encoding="utf-8")
        print(f"\nReport written to {a.report}", file=sys.stderr)
    return 0


def cmd_evaluate(a: argparse.Namespace) -> int:
    res = evaluate(a.dir)
    md = eval_markdown(res)
    print(md)
    if a.write_report:
        Path(a.write_report).parent.mkdir(parents=True, exist_ok=True)
        Path(a.write_report).write_text(md, encoding="utf-8")
    hybrid = res["table"]["Hybrid v1.0 (+ implications + OR groups)"]
    failed = []
    if a.min_spearman is not None and hybrid["spearman"] < a.min_spearman:
        failed.append(f"Spearman {hybrid['spearman']:.3f} < {a.min_spearman}")
    if a.min_auc is not None and hybrid["auc_good"] < a.min_auc:
        failed.append(f"AUC {hybrid['auc_good']:.3f} < {a.min_auc}")
    if failed:
        print("EVALUATION GATE FAILED: " + "; ".join(failed), file=sys.stderr)
        return 1
    return 0


def cmd_market(a: argparse.Namespace) -> int:
    jds = load_jds(a.dir)
    if not jds:
        print(f"No .txt job descriptions found in {a.dir}", file=sys.stderr)
        return 1
    demand = skill_demand(list(jds.values()))
    print(f"Skill demand across {len(jds)} job descriptions\n")
    for row in top_skills(demand, a.top):
        print(f"{row['skill']:<22}{row['share']:>6.0%}   {row['category']}")
    print("\nMean demand by category:")
    for cat, v in demand_by_category(demand).items():
        print(f"  {cat:<18}{v:.0%}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="AI Career Intelligence & Skill-Gap Analyzer")
    sub = p.add_subparsers(dest="command", required=True)

    an = sub.add_parser("analyze", help="analyze a resume against a job description")
    an.add_argument("resume", help=".txt, .md, .pdf or .docx")
    an.add_argument("jd", help=".txt, .md, .pdf or .docx")
    an.add_argument("--hours", type=float, default=10, help="study hours per week (default 10)")
    an.add_argument("--market-dir", help="folder of job-description .txt files used to rank skills by demand")
    an.add_argument("--report", help="also write a Markdown report to this path")
    an.add_argument("--json", action="store_true", help="print raw JSON instead of Markdown")
    an.add_argument("--embedding", action="store_true", help="use sentence-transformers similarity")
    an.set_defaults(func=cmd_analyze)

    ev = sub.add_parser("evaluate", help="run the evaluation benchmark")
    ev.add_argument("--dir", help="evaluation folder (default data/eval)")
    ev.add_argument("--write-report", help="write the Markdown report here")
    ev.add_argument("--min-spearman", type=float, help="exit 1 if hybrid Spearman falls below this")
    ev.add_argument("--min-auc", type=float, help="exit 1 if hybrid AUC falls below this")
    ev.set_defaults(func=cmd_evaluate)

    mk = sub.add_parser("market", help="skill demand across a folder of job descriptions")
    mk.add_argument("dir")
    mk.add_argument("--top", type=int, default=15)
    mk.set_defaults(func=cmd_market)

    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
