"""Threshold calibration + ROC/PR/score diagnostics for the trained models.

NO retraining — loads the saved models in outputs/scibert_{arm}. The 0.5 threshold
is badly placed (easy OOD negatives crush recall); we pick the macro-F1-optimal
threshold on the VALIDATION split (never the gold set) and re-report on gold.

  python -m scripts.calibrate_eval

Run it in the SAME Colab session that trained the models (so outputs/ still exists).
"""
from __future__ import annotations
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
from src.downstream import build_trainset as B
from src.downstream.train import TrainCfg
from src.downstream.evaluate import predict_proba, tune_threshold, report_from_probs, print_report
from src.downstream import plots

LABELED = {"snorkel": C.PROCESSED_DIR / "snorkel_labeled_pool.csv",
           "mas": C.ROOT / "DataSet" / "mas" / "mas_ranked_scores.csv"}


def rebuild_val_split(arm: str, cfg: TrainCfg) -> pd.DataFrame:
    """Recreate the exact validation split train.py used (same shuffles/seed)."""
    negatives = pd.read_csv(C.NEG_CLEAN_CSV, dtype=str).fillna("")
    labeled = pd.read_csv(LABELED[arm], dtype=str).fillna("")
    part = B.from_snorkel(labeled) if arm == "snorkel" else B.from_mas(labeled, include_hard_neg=True)
    train_df = B.assemble(part, negatives)                       # default seed=42
    train_df["label"] = train_df["label"].astype(int)
    df = train_df.sample(frac=1.0, random_state=cfg.seed).reset_index(drop=True)
    n_val = int(len(df) * cfg.val_frac)
    return df.iloc[:n_val]


def main():
    cfg = TrainCfg()
    eval_df = pd.read_csv(C.EVAL_PROCESSED_CSV, dtype=str).fillna("")
    eval_df["label"] = eval_df["label"].astype(int)
    yv_eval = eval_df["label"].values

    curves, summary = {}, {}
    for arm in ["snorkel", "mas"]:
        model_dir = str(C.ROOT / "outputs" / f"scibert_{arm}")
        # 1) tune threshold on validation
        val = rebuild_val_split(arm, cfg)
        pv = predict_proba(model_dir, val["text"].tolist(), max_len=cfg.max_len)
        thr, vf1 = tune_threshold(val["label"].values, pv)
        # 2) gold probs + reports at 0.5 and tuned threshold
        pe = predict_proba(model_dir, eval_df["text"].tolist(), max_len=cfg.max_len)
        r_default = report_from_probs(yv_eval, pe, eval_df, threshold=0.5)
        r_tuned = report_from_probs(yv_eval, pe, eval_df, threshold=thr)
        print_report(r_default, arm=f"{arm} @0.5")
        print_report(r_tuned, arm=f"{arm} @tuned={thr:.2f} (val F1={vf1:.3f})")
        curves[arm] = (yv_eval, pe)
        summary[arm] = {"tuned_threshold": thr, "default": r_default, "tuned": r_tuned}
        plots.score_hist(arm, yv_eval, pe)

    plots.roc_pr(curves)

    print("\n" + "=" * 64)
    print(f"{'arm':8s} {'AUC':>6s} {'AP':>6s} | {'F1@0.5':>7s} {'R@0.5':>6s} | {'F1@tuned':>9s} {'R@tuned':>8s}")
    for arm, s in summary.items():
        d, t = s["default"], s["tuned"]
        print(f"{arm:8s} {d['auc']:.3f} {d['average_precision']:.3f} | "
              f"{d['macro_f1']:.3f} {d['recall']:.3f} | {t['macro_f1']:.3f} {t['recall']:.3f}")
    with open(C.ROOT / "outputs" / "metrics_calibrated.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("\nsaved -> outputs/metrics_calibrated.json, roc_pr.png, scorehist_*.png")


if __name__ == "__main__":
    main()
