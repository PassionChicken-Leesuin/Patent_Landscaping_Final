"""Local LF coverage analysis on the candidate pool (no snorkel needed).

Run:  python -m scripts.analyze_lfs
Use this to iterate on labeling functions before the Colab LabelModel run.
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd
from src import config as C
from src.snorkel_arm.pipeline import apply_lfs_pure, coverage_report


def main():
    df = pd.read_csv(C.TRAINING_CLEAN_CSV, encoding="utf-8", dtype=str).fillna("")
    L = apply_lfs_pure(df["text"].tolist())
    rep = coverage_report(L)

    print(f"candidates: {rep['n']}")
    print("\nper-LF coverage / overlap / polarity:")
    print(f"  {'LF':28s} {'cov':>7s} {'overlap':>8s}  polarity")
    for r in rep["lf_table"]:
        print(f"  {r['lf']:28s} {r['coverage']:7.3f} {r['overlap']:8.3f}  {r['polarity']}")

    print(f"\nfraction with >=1 label : {rep['fraction_with_any_label']:.3f}")
    print(f"fraction all-abstain    : {rep['fraction_all_abstain']:.3f}")
    print("\nmajority-vote preview (NOT the LabelModel; just class-balance sanity):")
    for k, v in rep["majority_vote_preview"].items():
        print(f"  {k:18s} {v}")


if __name__ == "__main__":
    main()
