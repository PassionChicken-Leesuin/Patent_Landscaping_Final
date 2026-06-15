"""Snorkel arm: label a candidate set with LabelModel (LFs over the FULL set).

Requires snorkel (Python 3.10/3.11 — run on Colab, NOT the local 3.14 .venv).

  # unified full set (autonomous pool + OOD):
  python -m scripts.run_snorkel --input DataSet/processed/candidate_all.csv

Output: DataSet/processed/snorkel_labeled_all.csv  (snorkel_label, snorkel_prob_seed, source)
"""
from __future__ import annotations
import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd
from src import config as C
from src.snorkel_arm.pipeline import run_snorkel


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", default=str(C.PROCESSED_DIR / "candidate_all.csv"))
    ap.add_argument("--out", default=str(C.PROCESSED_DIR / "snorkel_labeled_all.csv"))
    args = ap.parse_args()

    df = pd.read_csv(args.input, encoding="utf-8", dtype=str).fillna("")
    print(f"candidates: {len(df)}  (from {Path(args.input).name})")

    labeled, summary, L = run_snorkel(df, text_col="text", drop_abstain=False)

    print("\nLF summary (coverage / overlaps / conflicts):")
    print(summary.to_string())
    print("\nsnorkel_label distribution:")
    print(Counter(labeled["snorkel_label"].tolist()))     # 1=SEED, 0=NOT_SEED, -1=ABSTAIN
    if "source" in labeled.columns:
        print("\nby source (label distribution):")
        print(labeled.groupby("source")["snorkel_label"].value_counts().to_string())

    labeled.to_csv(args.out, index=False, encoding="utf-8")
    print(f"\nsaved -> {args.out}")


if __name__ == "__main__":
    main()
