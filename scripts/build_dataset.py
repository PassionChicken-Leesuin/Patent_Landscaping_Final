"""Build processed datasets + print an EDA report.

Usage:  python -m scripts.build_dataset
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # Windows consoles often default to cp949; force UTF-8 for non-ASCII output
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd
from src import config as C
from src import data_pipeline as dp


def hr(title: str):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def main():
    out = dp.run(write=True)
    train, ev, leaked, clean = out["train_raw"], out["eval"], out["leaked"], out["train_clean"]

    hr("RAW SIZES")
    print(f"Training (candidate pool): {len(train):,}")
    print(f"Evaluation (gold)        : {len(ev):,}")

    hr("EVALUATION SET — label / expansion distribution")
    print(ev["label"].value_counts().rename({1: "SEED(1)", 0: "NOT_SEED(0)"}).to_string())
    pos = (ev["label"] == 1).mean()
    print(f"\npositive rate: {pos:.1%}  (imbalanced -> report Macro-F1 / P / R / AUC, not just accuracy)")
    print("\nexpansion_level:")
    print(ev["expansion_level"].value_counts().to_string())

    hr("LEAKAGE (eval gold appearing inside training candidate pool)")
    print(f"near-duplicate training patents found: {len(leaked)}")
    if len(leaked):
        print("\nby eval expansion_level:")
        print(leaked["eval_expansion_level"].value_counts().to_string())
        n_seed_leak = (leaked["eval_label"] == 1).sum()
        n_seed_total = (ev["label"] == 1).sum()
        print(f"\nSEED(positive) leakage: {n_seed_leak}/{n_seed_total} = {n_seed_leak/n_seed_total:.1%} of all positives")
        print(f"\nsaved list -> {C.LEAKED_IDS_CSV.relative_to(C.ROOT)}")

    hr("CLEAN TRAINING (leakage removed)")
    print(f"{len(train):,} -> {len(clean):,}  (dropped {len(train)-len(clean)})")

    hr("TEXT LENGTH (clean training, char count of title+abstract)")
    lens = clean["text"].str.len()
    print(lens.describe().to_string())
    empty = (clean["text"].str.strip() == "").sum()
    print(f"empty text rows: {empty}")

    hr("OUTPUTS WRITTEN")
    for p in [C.TRAINING_CLEAN_CSV, C.EVAL_PROCESSED_CSV, C.LEAKED_IDS_CSV]:
        print(f"  {p.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
