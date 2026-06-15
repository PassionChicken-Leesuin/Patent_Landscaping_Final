"""Unify the full candidate dataset the labelers process: expanded autonomous pool
+ out-of-domain negatives. Both Snorkel and MAS label ALL of it (OOD -> NOT_SEED).

  python -m scripts.build_candidate_all

Output: DataSet/processed/candidate_all.csv
  columns: record_id, patent_id, domain, title, abstract, text, source
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

EXPANDED = C.PROCESSED_DIR / "training_expanded_clean.csv"
OUT = C.PROCESSED_DIR / "candidate_all.csv"


def main():
    exp = pd.read_csv(EXPANDED, dtype=str).fillna("")
    neg = pd.read_csv(C.NEG_CLEAN_CSV, dtype=str).fillna("")

    # expanded autonomous-driving pool (already has title/abstract/text/patent_id)
    a = pd.DataFrame({
        "record_id": exp["patent_id"], "patent_id": exp["patent_id"],
        "domain": C.DOMAIN, "title": exp["title"], "abstract": exp["abstract"],
        "text": exp["text"], "source": "autonomous_pool",
    })
    # OOD negatives — only combined 'text' is available; feed it as the abstract so MAS/LFs see it
    b = pd.DataFrame({
        "record_id": neg["family_id"], "patent_id": "",
        "domain": C.DOMAIN, "title": "", "abstract": neg["text"],
        "text": neg["text"], "source": "ood_" + neg["source_domain"],
    })

    allc = pd.concat([a, b], ignore_index=True)
    allc.to_csv(OUT, index=False, encoding="utf-8")

    print(f"autonomous_pool: {len(a):,}   OOD: {len(b):,}   total: {len(allc):,}")
    print("by source:")
    print(allc["source"].value_counts().to_string())
    print(f"\nsaved -> {OUT.relative_to(C.ROOT)}")


if __name__ == "__main__":
    main()
