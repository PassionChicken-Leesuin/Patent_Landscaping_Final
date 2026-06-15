"""Subtopic-stratified recall on the GOLD SEED set, per arm.

Tests the coverage hypothesis: do the arms miss seeds *specifically* in the
subtopics that the training pool under-covers (cruise / aviation / ADAS / lane)?

Loads the trained models in outputs/scibert_{arm} (run in the SAME Colab session
that trained them, exactly like calibrate_eval.py).

  python -m scripts.stratified_recall                 # threshold 0.5
  python -m scripts.stratified_recall --tuned         # also tune thr on val split
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd
from src import config as C
from src.downstream import build_trainset as B
from src.downstream.train import TrainCfg
from src.downstream.evaluate import predict_proba, tune_threshold

LABELED = {"snorkel": C.PROCESSED_DIR / "snorkel_labeled_pool.csv",
           "mas": C.ROOT / "DataSet" / "mas" / "mas_ranked_scores.csv"}

# subtopic -> regex. UNDER = under-covered in training (see analyze_subtopics.py).
SUB = {
    "cruise control":      (r"\b(cruise control|adaptive cruise|acc)\b", "UNDER"),
    "aviation/UAV":        (r"\b(aircraft|aerial|drone|uav|unmanned aerial|autopilot|flight|aviation)\b", "UNDER"),
    "ADAS/driver-assist":  (r"\b(adas|driver[- ]assist|advanced driver|lane keep|lane departure|collision avoidance|blind spot|parking assist)\b", "UNDER"),
    "lane/road percep.":   (r"\b(lane|lane line|road marking|traffic sign|crosswalk|pedestrian)\b", "UNDER"),
    "V2X/comm":            (r"\b(v2x|v2v|vehicle[- ]to[- ]vehicle|telematics|roadside unit)\b", "UNDER"),
    "perception/sensor":   (r"\b(lidar|radar|camera|sensor fusion|point cloud|object detection)\b", "OK"),
    "vehicle control":     (r"\b(steering|throttle|braking|powertrain|torque|actuator)\b", "OK"),
    "path/motion plan":    (r"\b(path planning|trajectory|motion planning|route planning|navigation)\b", "OVER"),
}


def rebuild_val_split(arm: str, cfg: TrainCfg) -> pd.DataFrame:
    negatives = pd.read_csv(C.NEG_CLEAN_CSV, dtype=str).fillna("")
    labeled = pd.read_csv(LABELED[arm], dtype=str).fillna("")
    part = B.from_snorkel(labeled) if arm == "snorkel" else B.from_mas(labeled, include_hard_neg=True)
    train_df = B.assemble(part, negatives)
    train_df["label"] = train_df["label"].astype(int)
    df = train_df.sample(frac=1.0, random_state=cfg.seed).reset_index(drop=True)
    return df.iloc[:int(len(df) * cfg.val_frac)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tuned", action="store_true", help="also report at val-tuned threshold")
    cfg_args = ap.parse_args()
    cfg = TrainCfg()

    eval_df = pd.read_csv(C.EVAL_PROCESSED_CSV, dtype=str).fillna("")
    eval_df["label"] = eval_df["label"].astype(int)
    seed_mask = (eval_df["expansion_level"] == "SEED").values
    txt = eval_df["text"].str.lower()

    # precompute subtopic membership (seeds only)
    memb = {name: txt.map(lambda t, rx=re.compile(p): bool(rx.search(t))).values & seed_mask
            for name, (p, _) in SUB.items()}
    any_under = np.zeros(len(eval_df), bool)
    for name, (p, tag) in SUB.items():
        if tag == "UNDER":
            any_under |= memb[name]
    none_mask = seed_mask.copy()
    for m in memb.values():
        none_mask &= ~m

    for arm in ["snorkel", "mas"]:
        model_dir = str(C.ROOT / "outputs" / f"scibert_{arm}")
        pe = predict_proba(model_dir, eval_df["text"].tolist(), max_len=cfg.max_len)
        thr = 0.5
        if cfg_args.tuned:
            val = rebuild_val_split(arm, cfg)
            pv = predict_proba(model_dir, val["text"].tolist(), max_len=cfg.max_len)
            thr, _ = tune_threshold(val["label"].values, pv)
        yhat = (pe >= thr).astype(int)

        print("=" * 78)
        print(f"ARM = {arm}   (threshold = {thr:.3f})")
        overall = yhat[seed_mask].mean()
        print(f"  OVERALL seed recall : {overall:.3f}  (n={seed_mask.sum()})")
        print(f"  {'subtopic':22s} {'tag':6s} {'n':>4s} {'recall':>8s} {'mean_prob':>10s}")
        print("  " + "-" * 56)
        for name, (p, tag) in sorted(SUB.items(), key=lambda kv: kv[1][1]):
            m = memb[name]
            if m.sum() == 0:
                continue
            print(f"  {name:22s} {tag:6s} {m.sum():4d} {yhat[m].mean():8.3f} {pe[m].mean():10.3f}")
        print("  " + "-" * 56)
        print(f"  {'[ANY under-covered]':22s} {'UNDER':6s} {any_under.sum():4d} "
              f"{yhat[any_under].mean():8.3f} {pe[any_under].mean():10.3f}")
        cov = seed_mask & ~any_under
        print(f"  {'[rest of seeds]':22s} {'':6s} {cov.sum():4d} "
              f"{yhat[cov].mean():8.3f} {pe[cov].mean():10.3f}")
        if none_mask.sum():
            print(f"  {'[no subtopic matched]':22s} {'':6s} {none_mask.sum():4d} "
                  f"{yhat[none_mask].mean():8.3f} {pe[none_mask].mean():10.3f}")


if __name__ == "__main__":
    main()
