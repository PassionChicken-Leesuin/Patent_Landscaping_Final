"""Threshold calibration + ROC/PR diagnostics for the trained UNIFIED models.

NO retraining — loads outputs/scibert_{snorkel_uni,mas_uni}. The 0.5 threshold is
conservative (recall suppressed); we pick the macro-F1-optimal threshold on the
VALIDATION split (never the gold set) and re-report on gold.

  python -m scripts.calibrate_eval

Run in a session where the models exist (restore from Drive first if needed). Needs the
data prep (build_dataset, build_candidate_all, run_snorkel) so the val split can be rebuilt.
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

# (model-dir suffix, arm, unified-labeled file)
ARMS = [
    ("snorkel_uni", "snorkel", C.PROCESSED_DIR / "snorkel_labeled_all.csv"),
    ("mas_uni", "mas", C.ROOT / "DataSet" / "mas" / "mas_ranked_scores.csv"),
]


def rebuild_val_split(arm: str, labeled_path, cfg: TrainCfg) -> pd.DataFrame:
    """Recreate the exact validation split the unified run used (from_labeled_all + default assemble)."""
    labeled = pd.read_csv(labeled_path, dtype=str).fillna("")
    part, ood = B.from_labeled_all(labeled, arm)
    train_df = B.assemble(part, ood)                              # default (all-OOD), seed=42 — matches --unified --tag uni
    train_df["label"] = train_df["label"].astype(int)
    df = train_df.sample(frac=1.0, random_state=cfg.seed).reset_index(drop=True)
    n_val = int(len(df) * cfg.val_frac)
    return df.iloc[:n_val]


def main():
    cfg = TrainCfg()
    eval_df = pd.read_csv(C.EVAL_PROCESSED_CSV, dtype=str).fillna("")
    eval_df["label"] = eval_df["label"].astype(int)
    y = eval_df["label"].values

    curves, summary = {}, {}
    for name, arm, labeled_path in ARMS:
        model_dir = str(C.ROOT / "outputs" / f"scibert_{name}")
        if not Path(model_dir, "config.json").exists():
            print(f"[{name}] model not found at {model_dir} — skip"); continue
        val = rebuild_val_split(arm, labeled_path, cfg)
        pv = predict_proba(model_dir, val["text"].tolist(), max_len=cfg.max_len)
        thr, vf1 = tune_threshold(val["label"].values, pv)
        pe = predict_proba(model_dir, eval_df["text"].tolist(), max_len=cfg.max_len)
        r_default = report_from_probs(y, pe, eval_df, threshold=0.5)
        r_tuned = report_from_probs(y, pe, eval_df, threshold=thr)
        print_report(r_default, arm=f"{name} @0.5")
        print_report(r_tuned, arm=f"{name} @tuned={thr:.2f} (val F1={vf1:.3f})")
        curves[name] = (y, pe)
        summary[name] = {"tuned_threshold": thr, "default": r_default, "tuned": r_tuned}
        plots.score_hist(name, y, pe)

    if curves:
        plots.roc_pr(curves)
    print("\n" + "=" * 78)
    print(f"{'model':12s} {'AUC':>6s} {'AUC_hard':>9s} | {'F1@0.5':>7s} {'R@0.5':>6s} | "
          f"{'thr':>5s} {'F1@tuned':>9s} {'R@tuned':>8s}")
    for name, s in summary.items():
        d, t = s["default"], s["tuned"]
        print(f"{name:12s} {d['auc']:.3f} {d.get('auc_seed_vs_hard', float('nan')):.3f}     | "
              f"{d['macro_f1']:.3f} {d['recall']:.3f} | {s['tuned_threshold']:.2f}  "
              f"{t['macro_f1']:.3f}    {t['recall']:.3f}")
    with open(C.ROOT / "outputs" / "metrics_calibrated.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print("\nsaved -> outputs/metrics_calibrated.json, roc_pr.png, scorehist_*.png")


if __name__ == "__main__":
    main()
