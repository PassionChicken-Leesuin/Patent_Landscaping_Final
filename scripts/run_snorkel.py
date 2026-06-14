"""Snorkel arm: label the autonomous-driving candidate pool with LabelModel.

Requires snorkel (Python 3.10/3.11 — run on Colab, NOT the local 3.14 .venv).
Output: DataSet/processed/snorkel_labeled_pool.csv  (snorkel_label, snorkel_prob_seed)

Downstream (scripts.build_trainset) then combines:
  positives      = pool rows snorkel_label == 1
  in-pool negs   = pool rows snorkel_label == 0   (keyword-detected look-alikes)
  out-of-domain  = negatives_pool.csv (6,296, fixed)   -> NOT_SEED
"""
from __future__ import annotations
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

OUT = C.PROCESSED_DIR / "snorkel_labeled_pool.csv"


def main():
    df = pd.read_csv(C.TRAINING_CLEAN_CSV, encoding="utf-8", dtype=str).fillna("")
    print(f"candidate pool: {len(df)}")

    labeled, summary, L = run_snorkel(df, text_col="text", drop_abstain=False)

    print("\nLF summary (coverage / overlaps / conflicts):")
    print(summary.to_string())
    print("\nsnorkel_label distribution:")
    print(Counter(labeled["snorkel_label"].tolist()))   # 1=SEED, 0=NOT_SEED, -1=ABSTAIN

    labeled.to_csv(OUT, index=False, encoding="utf-8")
    print(f"\nsaved -> {OUT.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
