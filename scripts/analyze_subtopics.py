"""Do GOLD-SEED subtopics (aviation autopilot, ADAS, cruise, ...) exist in the TRAIN pool?

For each subtopic (keyword set), report the share of docs containing it in:
  - GOLD SEED            (the positives we must recall)
  - TRAIN pool (all AD)  (candidate pool)
  - TRAIN MAS-positives  (what MAS called positive -> downstream label=1)
A subtopic that is large in GOLD-SEED but tiny in TRAIN means the model never
learned to fire on it -> guaranteed misses on those seeds.
"""
from __future__ import annotations
import re, numpy as np, pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "DataSet"
eval_df = pd.read_csv(D / "processed" / "eval_processed.csv")
train   = pd.read_csv(D / "processed" / "training_clean.csv")
mas     = pd.read_csv(D / "mas" / "mas_ranked_scores.csv")

seed = eval_df[eval_df["expansion_level"] == "SEED"]["text"].fillna("").str.lower()
anti = eval_df[eval_df["expansion_level"].str.startswith("ANTISEED")]["text"].fillna("").str.lower()
pool = train["text"].fillna("").str.lower()
mpos = (mas[mas["candidate_type"] == "positive"]["title"].fillna("") + ". " +
        mas[mas["candidate_type"] == "positive"]["abstract"].fillna("")).str.lower()

# subtopic -> regex (word-boundary, any-of)
SUB = {
    "aviation/UAV/drone": r"\b(aircraft|aerial|drone|uav|unmanned aerial|autopilot|flight|aviation|aircrafts)\b",
    "ADAS/driver-assist": r"\b(adas|driver[- ]assist|advanced driver|lane keep|lane departure|collision avoidance|blind spot|parking assist)\b",
    "cruise control":     r"\b(cruise control|adaptive cruise|acc\b)\b",
    "lane/road percep.":  r"\b(lane|lane line|road marking|traffic sign|crosswalk|pedestrian)\b",
    "perception/sensor":  r"\b(lidar|radar|camera|sensor fusion|point cloud|object detection)\b",
    "path/motion plan":   r"\b(path planning|trajectory|motion planning|route planning|navigation)\b",
    "vehicle control":    r"\b(steering|throttle|braking|powertrain|torque|actuator)\b",
    "deep learning":      r"\b(neural network|deep learning|cnn|machine learning|training data|inference)\b",
    "V2X/comm":           r"\b(v2x|v2v|vehicle[- ]to[- ]vehicle|telematics|roadside unit)\b",
    "marine/rail/other":  r"\b(vessel|ship|marine|railway|train\b|locomotive)\b",
}

def share(series: pd.Series, pat: str) -> float:
    rx = re.compile(pat)
    return float(series.map(lambda t: bool(rx.search(t))).mean())

groups = {"GOLD-SEED": seed, "GOLD-ANTISEED": anti, "TRAIN-pool": pool, "TRAIN-MASpos": mpos}
print(f"n: GOLD-SEED={len(seed)}  GOLD-ANTISEED={len(anti)}  TRAIN-pool={len(pool)}  TRAIN-MASpos={len(mpos)}")
print("=" * 88)
hdr = f"{'subtopic':22s}" + "".join(f"{g:>14s}" for g in groups)
print(hdr); print("-" * 88)
rows = []
for name, pat in SUB.items():
    vals = {g: share(s, pat) for g, s in groups.items()}
    rows.append((name, vals))
    print(f"{name:22s}" + "".join(f"{vals[g]*100:13.1f}%" for g in groups))

print("=" * 88)
print("COVERAGE GAP = GOLD-SEED share - TRAIN-MASpos share  (high => seeds the model can't fire on)")
print("-" * 88)
for name, vals in sorted(rows, key=lambda r: r[1]["GOLD-SEED"] - r[1]["TRAIN-MASpos"], reverse=True):
    gap = vals["GOLD-SEED"] - vals["TRAIN-MASpos"]
    flag = "  <== UNDER-COVERED" if gap > 0.05 else ""
    print(f"{name:22s} gap={gap*100:+6.1f} pts   (seed {vals['GOLD-SEED']*100:4.1f}% vs maspos {vals['TRAIN-MASpos']*100:4.1f}%){flag}")
