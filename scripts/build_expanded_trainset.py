"""Merge old pool + expanded candidates, dedup, remove gold leakage -> clean train pool.

  python -m scripts.build_expanded_trainset
"""
from __future__ import annotations
import argparse
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
from src import domains as D


def hr(t): print("\n" + "=" * 64 + f"\n{t}\n" + "=" * 64)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default=D.AUTONOMOUS, help="domain key (default: self-driving)")
    args = ap.parse_args()
    spec = D.get(args.domain)
    exp_raw, out = spec.pool_raw, spec.pool_clean
    leak_out = spec.leaked_ids.parent / ("expanded_gold_leak.csv" if spec.legacy
                                         else f"{args.domain}_expanded_gold_leak.csv")
    out.parent.mkdir(parents=True, exist_ok=True)
    leak_out.parent.mkdir(parents=True, exist_ok=True)

    exp = pd.read_csv(exp_raw, dtype=str).fillna("")
    ev = dp.load_eval() if spec.legacy else dp.load_gold(spec)

    # unify expanded to pipeline schema
    exp = exp.rename(columns={"Patent_title": "title", "Patent_abstract": "abstract"})
    exp["text"] = (exp["title"].str.strip() + ". " + exp["abstract"].str.strip()).str.strip(". ").str.strip()
    exp["record_id"] = exp["patent_id"]; exp["domain"] = args.domain
    cols = ["record_id", "patent_id", "domain", "title", "abstract", "text"]

    if spec.legacy:
        old = pd.read_csv(C.TRAINING_CLEAN_CSV, dtype=str).fillna("")
        hr("MERGE old pool + expanded (dedup by patent_id)")
        merged = pd.concat([old[cols], exp[cols]], ignore_index=True)
        merged = merged.drop_duplicates(subset="patent_id").reset_index(drop=True)
        print(f"old pool: {len(old):,}   expanded: {len(exp):,}   union (dedup id): {len(merged):,}")
        print(f"new patents added: {len(merged) - len(old):,}")
    else:
        hr("COLLECTED EXPANDED POOL (dedup by patent_id)")
        merged = exp[cols].drop_duplicates(subset="patent_id").reset_index(drop=True)
        print(f"collected: {len(exp):,}   dedup id: {len(merged):,}")

    hr("GOLD LEAKAGE (collected pool overlaps gold families)")
    leaked = dp.find_leakage(merged, ev)
    print(f"pool patents near-duplicate of a gold patent: {len(leaked)}")
    if len(leaked):
        print("\nby gold expansion_level:")
        print(leaked["eval_expansion_level"].value_counts().to_string())
        n_seed = (leaked["eval_label"] == 1).sum()
        print(f"\noverlap with gold SEED (positives): {n_seed} / {(ev['label']==1).sum()}")

    drop_ids = set(leaked["train_patent_id"]) if len(leaked) else set()
    clean = merged[~merged["patent_id"].isin(drop_ids)].reset_index(drop=True)

    hr("FINAL CLEAN EXPANDED TRAIN POOL")
    print(f"{len(merged):,} -> {len(clean):,}  (removed {len(merged)-len(clean)} gold-leaking)")

    leaked.to_csv(leak_out, index=False, encoding="utf-8")
    clean.to_csv(out, index=False, encoding="utf-8")
    print(f"\nsaved -> {out.relative_to(C.ROOT)}")
    print(f"leak list -> {leak_out.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
