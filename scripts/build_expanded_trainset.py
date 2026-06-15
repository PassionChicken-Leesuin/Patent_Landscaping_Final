"""Merge old pool + expanded candidates, dedup, remove gold leakage -> clean train pool.

  python -m scripts.build_expanded_trainset
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
from src import data_pipeline as dp

EXP_RAW = C.DATA_DIR / "expanded" / "expanded_candidates_raw.csv"
OUT = C.PROCESSED_DIR / "training_expanded_clean.csv"
LEAK_OUT = C.LEAKAGE_DIR / "expanded_gold_leak.csv"


def hr(t): print("\n" + "=" * 64 + f"\n{t}\n" + "=" * 64)


def main():
    old = pd.read_csv(C.TRAINING_CLEAN_CSV, dtype=str).fillna("")     # 6,139 (already eval-clean)
    exp = pd.read_csv(EXP_RAW, dtype=str).fillna("")
    ev = dp.load_eval()

    # unify expanded to pipeline schema
    exp = exp.rename(columns={"Patent_title": "title", "Patent_abstract": "abstract"})
    exp["text"] = (exp["title"].str.strip() + ". " + exp["abstract"].str.strip()).str.strip(". ").str.strip()
    exp["record_id"] = exp["patent_id"]; exp["domain"] = C.DOMAIN
    cols = ["record_id", "patent_id", "domain", "title", "abstract", "text"]

    hr("MERGE old pool + expanded (dedup by patent_id)")
    merged = pd.concat([old[cols], exp[cols]], ignore_index=True)
    merged = merged.drop_duplicates(subset="patent_id").reset_index(drop=True)
    print(f"old pool: {len(old):,}   expanded: {len(exp):,}   union (dedup id): {len(merged):,}")
    print(f"new patents added: {len(merged) - len(old):,}")

    hr("GOLD LEAKAGE (expanded collection overlaps gold US families)")
    leaked = dp.find_leakage(merged, ev)             # abstract Jaccard >= 0.7
    print(f"merged patents near-duplicate of a gold patent: {len(leaked)}")
    if len(leaked):
        print("\nby gold expansion_level:")
        print(leaked["eval_expansion_level"].value_counts().to_string())
        n_seed = (leaked["eval_label"] == 1).sum()
        print(f"\noverlap with gold SEED (positives): {n_seed} / {(ev['label']==1).sum()}")

    drop_ids = set(leaked["train_patent_id"])
    clean = merged[~merged["patent_id"].isin(drop_ids)].reset_index(drop=True)

    hr("FINAL CLEAN EXPANDED TRAIN POOL")
    print(f"{len(merged):,} -> {len(clean):,}  (removed {len(merged)-len(clean)} gold-leaking)")

    C.LEAKAGE_DIR.mkdir(parents=True, exist_ok=True)
    leaked.to_csv(LEAK_OUT, index=False, encoding="utf-8")
    clean.to_csv(OUT, index=False, encoding="utf-8")
    print(f"\nsaved -> {OUT.relative_to(C.ROOT)}")
    print(f"leak list -> {LEAK_OUT.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
