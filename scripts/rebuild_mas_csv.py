"""Regenerate mas_ranked_scores.csv from the audit JSONL with the CURRENT scoring rule.

No API calls — reuses the stored Node A/B raw outputs and re-applies the (corrected)
deterministic Stage C. Use after fixing src/mas/scoring.py.

  python -m scripts.rebuild_mas_csv
"""
from __future__ import annotations
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import pandas as pd
from src import config as C
from src.mas import config as MC
from src.mas.scoring import score_and_type
from src.mas.runner import write_ranked_csv


def main():
    pool = pd.read_csv(C.TRAINING_CLEAN_CSV, dtype=str).fillna("").set_index("patent_id")
    rows = [json.loads(l) for l in open(MC.AUDIT_JSONL, encoding="utf-8")]

    results = []
    for r in rows:
        sc = score_and_type(r)                       # recompute with current rule
        pid = r.get("patent_id", "")
        title = pool.loc[pid, "title"] if pid in pool.index else ""
        abstract = pool.loc[pid, "abstract"] if pid in pool.index else ""
        results.append({
            "record_id": r["record_id"], "patent_id": pid,
            "domain": r.get("domain", MC.DOMAIN), "title": title, "abstract": abstract,
            "final_score": sc["final_score"], "candidate_type": sc["candidate_type"],
        })

    path = write_ranked_csv(results)
    print(f"rebuilt {len(results)} rows -> {path}")
    print("candidate_type:", dict(Counter(r["candidate_type"] for r in results)))


if __name__ == "__main__":
    main()
