"""Score an agentic judge audit against a labeled CSV (pilot/eval analysis).

python -m scripts.score_agentic --slug hydrogen-storage --labels DataSet/agentic/_pilot_hydro80.csv
"""
from __future__ import annotations
import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd

from src.downstream.evaluate import report_from_probs
from src.agentic import config as AC
from src.agentic.judge import judgments_from_audit
from src.agentic.workspace import Workspace


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slug", required=True)
    ap.add_argument("--labels", required=True, help="CSV with family_id/record_id + label (+expansion_level)")
    ap.add_argument("--threshold", type=float, default=AC.EVAL_THRESHOLD)
    args = ap.parse_args()

    ws = Workspace(args.slug)
    latest = judgments_from_audit(ws)
    df = pd.read_csv(args.labels, encoding="utf-8")
    if "record_id" not in df.columns:
        df["record_id"] = df["family_id"].astype(str)
    df["record_id"] = df["record_id"].astype(str)

    df = df[df["record_id"].isin(latest)].copy()
    if df.empty:
        raise SystemExit("no overlap between audit and labels")
    df["p"] = [float(latest[r]["final_score"]) for r in df["record_id"]]
    df["stance"] = [latest[r].get("stance") for r in df["record_id"]]
    y = df["label"].astype(int).values
    res = report_from_probs(y, df["p"].values, df, threshold=args.threshold)

    print(f"n={res['n']}  acc={res['accuracy']:.3f}  precision={res['precision']:.3f}  "
          f"recall={res['recall']:.3f}  macroF1={res['macro_f1']:.3f}  auc={res['auc']:.3f}")
    for k, v in res.get("by_expansion_level", {}).items():
        print(f"  {k}: {v}")
    for k in ("auc_seed_vs_hard", "auc_seed_vs_easy"):
        if k in res:
            print(f"  {k}: {res[k]:.3f}")
    print("stance:", dict(Counter(df["stance"])))

    # error listing: worst false positives / false negatives by score distance
    yhat = (df["p"] >= args.threshold).astype(int)
    fp = df[(yhat == 1) & (y == 0)].sort_values("p", ascending=False)
    fn = df[(yhat == 0) & (y == 1)].sort_values("p")
    print(f"\nFalse positives ({len(fp)}):")
    for _, r in fp.head(10).iterrows():
        print(f"  p={r['p']:.2f} [{r.get('expansion_level', '?')}] {str(r['title'])[:90]}")
    print(f"False negatives ({len(fn)}):")
    for _, r in fn.head(10).iterrows():
        print(f"  p={r['p']:.2f} [{r.get('expansion_level', '?')}] {str(r['title'])[:90]}")


if __name__ == "__main__":
    main()
