"""End-to-end downstream for ONE arm: assemble trainset -> fine-tune SciBERT -> eval.

Requires torch + transformers + datasets + scikit-learn (Colab/GPU).

Examples
--------
python -m scripts.run_downstream --arm snorkel
python -m scripts.run_downstream --arm mas --no-hard-neg     # ablation: drop MAS hard negs
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
from src import config as C
from src import domains as D
from src.downstream import build_trainset as B
from src.downstream.train import train, TrainCfg
from src.downstream.evaluate import evaluate, print_report

LABELED = {
    "snorkel": C.PROCESSED_DIR / "snorkel_labeled_pool.csv",
    "mas": C.ROOT / "DataSet" / "mas" / "mas_ranked_scores.csv",
}
# unified labeling: the labeler labeled the FULL candidate_all (expanded pool + OOD)
LABELED_UNIFIED = {
    "snorkel": C.PROCESSED_DIR / "snorkel_labeled_all.csv",
    "mas": C.ROOT / "DataSet" / "mas" / "mas_ranked_scores.csv",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default=D.AUTONOMOUS, help="domain key (default: self-driving)")
    ap.add_argument("--arm", choices=["snorkel", "mas"], required=True)
    ap.add_argument("--no-inpool-neg", action="store_true", help="use only out-of-domain negatives")
    ap.add_argument("--no-hard-neg", action="store_true", help="(mas) drop hard_negative from training")
    ap.add_argument("--ood-n", type=int, default=None,
                    help="number of OOD negatives to include (None=all, 0=none). Recall ablation.")
    ap.add_argument("--neg-pos-ratio", type=float, default=None,
                    help="cap total negatives to ratio*positives, in-domain first (e.g. 1.0). Overrides --ood-n.")
    ap.add_argument("--tag", default="", help="suffix for output dir / metrics (e.g. 'equalN')")
    ap.add_argument("--unified", action="store_true",
                    help="use the unified labeled set (expanded pool + OOD labeled together)")
    ap.add_argument("--hard-neg-only", action="store_true",
                    help="(unified, MAS) negatives = in-domain HARD negatives only (positive vs hard-neg)")
    ap.add_argument("--easy-neg-n", type=int, default=None,
                    help="(unified, MAS) all pos + all hard negatives + this many easy negatives (anchor)")
    ap.add_argument("--epochs", type=int, default=4)
    ap.add_argument("--max-len", type=int, default=256)
    args = ap.parse_args()

    spec = D.get(args.domain)
    labeled_unified = {"snorkel": spec.snorkel_labeled, "mas": spec.mas_ranked}

    if args.unified and args.easy_neg_n is not None and args.arm == "mas":
        # hard-centric: all pos + all hard neg + easy downsampled to --easy-neg-n
        labeled = pd.read_csv(labeled_unified["mas"], dtype=str).fillna("")
        train_df = B.assemble_mas_he(labeled, easy_n=args.easy_neg_n)
        train_df["label"] = train_df["label"].astype(int)
        print(B.summary(train_df))
        part = negatives = None  # already assembled
    elif args.unified:
        labeled = pd.read_csv(labeled_unified[args.arm], dtype=str).fillna("")
        part, negatives = B.from_labeled_all(labeled, args.arm, include_hard_neg=not args.no_hard_neg,
                                             hard_neg_only=args.hard_neg_only)
    else:
        negatives = pd.read_csv(C.NEG_CLEAN_CSV if spec.legacy else spec.negatives_pool, dtype=str).fillna("")
        labeled = pd.read_csv(LABELED[args.arm], dtype=str).fillna("")
        part = B.from_snorkel(labeled) if args.arm == "snorkel" else \
            B.from_mas(labeled, include_hard_neg=not args.no_hard_neg)

    if part is not None:                 # not pre-assembled (assemble_mas_he sets part=None)
        train_df = B.assemble(part, negatives, use_inpool_neg=not args.no_inpool_neg,
                              ood_n=args.ood_n, neg_pos_ratio=args.neg_pos_ratio)
        train_df["label"] = train_df["label"].astype(int)
        print(B.summary(train_df))

    name = spec.model_name(args.arm, args.tag)

    # A binary classifier needs both classes. Some positive-dominated pools (CPC∩keyword)
    # yield ZERO in-pool negatives for the Snorkel arm -> the noood config is degenerate
    # (100% positive). Skip it cleanly (no crash, no model) so the notebook continues; the
    # MAS arm and both *_ood configs still train. This is itself a finding worth reporting.
    n_pos = int((train_df["label"] == 1).sum())
    n_neg = int((train_df["label"] == 0).sum())
    if n_pos == 0 or n_neg == 0:
        print(f"\n[SKIP] {name}: single-class train set (pos={n_pos}, neg={n_neg}); "
              f"cannot fine-tune a binary classifier. Skipping (degenerate config).")
        return

    out_dir = str(C.ROOT / "outputs" / f"scibert_{name}")
    cfg = TrainCfg(epochs=args.epochs, max_len=args.max_len)
    train(train_df, out_dir, cfg)

    eval_df = pd.read_csv(C.EVAL_PROCESSED_CSV if spec.legacy else spec.eval_processed,
                          dtype=str).fillna("")
    eval_df["label"] = eval_df["label"].astype(int)
    res = evaluate(out_dir, eval_df, max_len=args.max_len)
    print_report(res, arm=name)

    metrics_path = C.ROOT / "outputs" / f"metrics_{name}.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2)
    print(f"\nmetrics -> {metrics_path.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
