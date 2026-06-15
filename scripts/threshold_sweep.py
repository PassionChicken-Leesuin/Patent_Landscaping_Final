"""Threshold sweep on gold — show the precision/recall/F1 tradeoff as the decision
threshold is lowered (no gold tuning, just the operating-point curve).

  python -m scripts.threshold_sweep

Loads outputs/scibert_{snorkel_uni,mas_uni}; needs cells 3-4 only if you also want the
score histograms (it just predicts on the gold set, which is in the repo).
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score
from src import config as C
from src.downstream.evaluate import predict_proba

MODELS = ["snorkel_noood", "mas_noood"]
THRESHOLDS = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50]


def main():
    ev = pd.read_csv(C.EVAL_PROCESSED_CSV, dtype=str).fillna("")
    y = ev["label"].astype(int).values
    lvl = ev["expansion_level"].values

    for name in MODELS:
        mdir = C.ROOT / "outputs" / f"scibert_{name}"
        if not (mdir / "config.json").exists():
            print(f"[{name}] not found — skip"); continue
        p = predict_proba(str(mdir), ev["text"].tolist())
        print(f"\n=== {name} — threshold sweep (gold n={len(y)}) ===")
        print(f"{'thr':>5s} {'precision':>10s} {'recall':>8s} {'macroF1':>8s} "
              f"{'SEEDrec':>8s} {'spec_hard':>10s} {'spec_easy':>10s} {'#pred_pos':>10s}")
        for t in THRESHOLDS:
            yhat = (p >= t).astype(int)
            prec = precision_score(y, yhat, zero_division=0)
            rec = recall_score(y, yhat, zero_division=0)
            f1 = f1_score(y, yhat, average="macro", zero_division=0)
            seed_rec = recall_score(y[lvl == "SEED"], yhat[lvl == "SEED"], zero_division=0)
            sh = float((yhat[lvl == "ANTISEED-manual"] == 0).mean())
            se = float((yhat[lvl == "ANTISEED-AF"] == 0).mean())
            print(f"{t:5.2f} {prec:10.3f} {rec:8.3f} {f1:8.3f} {seed_rec:8.3f} "
                  f"{sh:10.3f} {se:10.3f} {int(yhat.sum()):10d}")


if __name__ == "__main__":
    main()
