"""Build a side-by-side comparison of agentic eval variants + the paper baselines.

python -m scripts.compare_runs --variants full1 full2 full4
-> outputs/agentic_3way.csv (+ printed table)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd

from src.agentic import config as AC

DOMAINS = ["autonomous_driving", "additivemanufacturing", "blockchain",
           "computervision", "genomeediting", "hydrogenstorage"]
METRICS = ["macro_f1", "auc", "recall", "precision", "accuracy"]

# paper baselines (SciBERT downstream) — averages, from generate_paper_draft.py
BASELINES = {
    "Snorkel+SciBERT": {"macro_f1": 0.730, "auc": 0.881, "recall": 0.551, "precision": 0.718, "accuracy": 0.821},
    "MAS+SciBERT": {"macro_f1": 0.833, "auc": 0.945, "recall": 0.781, "precision": 0.783, "accuracy": 0.883},
}


def load_variant(variant: str) -> dict:
    rows = {}
    for dom in DOMAINS:
        p = AC.OUTPUTS_DIR / f"agentic_metrics_{dom}_{variant}.json"
        if p.exists():
            rows[dom] = json.loads(p.read_text(encoding="utf-8"))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variants", nargs="+", default=["full1", "full2", "full4"])
    args = ap.parse_args()

    # per-variant averages
    summary = []
    for v in args.variants:
        rows = load_variant(v)
        if not rows:
            continue
        avg = {m: sum(rows[d][m] for d in rows) / len(rows) for m in METRICS}
        summary.append({"run": f"agentic:{v}", **{m: round(avg[m], 3) for m in METRICS}})
    for name, vals in BASELINES.items():
        summary.append({"run": name, **vals})
    tbl = pd.DataFrame(summary)
    AC.OUTPUTS_DIR.mkdir(exist_ok=True)
    tbl.to_csv(AC.OUTPUTS_DIR / "agentic_3way.csv", index=False, encoding="utf-8")
    print("=== Average across 6 domains ===")
    print(tbl.to_string(index=False))

    # per-domain macro-F1 for the last variant
    last = args.variants[-1]
    rows = load_variant(last)
    print(f"\n=== Per-domain (agentic:{last}) ===")
    perdom = pd.DataFrame([{"domain": d, **{m: round(rows[d][m], 3) for m in METRICS}}
                           for d in rows])
    print(perdom.to_string(index=False))


if __name__ == "__main__":
    main()
