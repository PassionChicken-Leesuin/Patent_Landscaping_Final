"""Generate per-domain MAS rubrics and sanity-check the generic Snorkel LFs locally.

  python -m scripts.gen_domain_artifacts

Writes rubrics/<domain>_v1.json for the 5 added domains and prints, for each, the pure-python
LF coverage / majority-vote class balance computed on that domain's GOLD set (so we can see
whether the keyword LFs recover SEED before spending Colab time). No snorkel needed (3.14 ok).
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
from src import domains as D
from src import data_pipeline as dp
from src.mas.rubric_gen import write_rubric
from src.snorkel_arm import pipeline as P
from src.snorkel_arm.lfs_generic import _count_hits


def main():
    for key in D.NEW_DOMAINS:
        spec = D.DOMAINS[key]
        path = write_rubric(spec, D.DOMAINS)
        gold = dp.load_gold(spec)
        texts = gold["text"].tolist()
        y = np.array(gold["label"].astype(int).tolist())
        lvl = gold["expansion_level"].values
        L = P.apply_lfs_pure(texts, domain=key)
        rep = P.coverage_report(L, domain=key)

        # keyword discrimination by gold expansion level: does ">=1 domain keyword" separate
        # SEED from the hard (ANTISEED-manual) and easy (ANTISEED-AF) negatives?
        own = [k.lower() for k in spec.keywords]
        hit = np.array([_count_hits(t, own) >= 1 for t in texts])
        def rate(level):
            m = (lvl == level)
            return hit[m].mean() if m.sum() else float("nan")
        tp = int((hit & (y == 1)).sum()); fp = int((hit & (y == 0)).sum())
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / int((y == 1).sum()) if (y == 1).sum() else 0.0

        print(f"\n=== {spec.display} ({key}) ===")
        print(f"rubric -> {Path(path).relative_to(D.ROOT)}")
        print(f"gold n={len(texts)} (SEED={int((y==1).sum())}) | any-label={rep['fraction_with_any_label']:.2f}")
        print(f"keyword>=1 hit-rate:  SEED={rate('SEED'):.2f}  HARDneg={rate('ANTISEED-manual'):.2f}  "
              f"EASYneg={rate('ANTISEED-AF'):.2f}   (proxy P={prec:.2f} R={rec:.2f})")
        for r in rep["lf_table"]:
            print(f"   {r['lf']:18s} cov={r['coverage']:.3f} overlap={r['overlap']:.3f} {r['polarity']}")


if __name__ == "__main__":
    main()
