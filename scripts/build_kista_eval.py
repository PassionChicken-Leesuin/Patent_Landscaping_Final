"""Reconstruct Choi et al. (2022, TFSC) evaluation sets from the full KISTA 'filed' pools.

The released CSVs are the FULL keyword-retrieved pools (~0.3-2.1M rows) with a boolean
`valid` (KISTA expert 'target/valid patent' label). Choi et al. report F1/AP on a
CPC-undersampled, 6:2:2-split test fold (their §3.4). We replicate that protocol so our
zero-training MAS can be scored on a COMPARABLE (same data, same protocol, not identical
rows) test set.

Their undersampling (§3.4): keep every positive; among negatives, keep only those that
contain an "important CPC" — a CPC that (a) appears in >=0.5% of the target(valid) patents
AND (b) whose emergence ratio in the target set is >50x its ratio in the background patent
DB. We use the full pool as the background-rate proxy (it is the broad keyword-retrieved
universe). Then a seeded stratified 6:2:2 split; we emit the test fold.

Out: DataSet/kista/<slug>_test.csv  (family_id, publication_number, title, abstract,
cpc, ipc, label) + a sidecar _meta.json with the important-CPC list and counts.

Run: python -m scripts.build_kista_eval --domain geostationary
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
csv.field_size_limit(10 ** 8)

ROOT = Path(__file__).resolve().parent.parent
WRITING = ROOT / "Writing"
OUT = ROOT / "DataSet" / "kista"

DOMAINS = {                                   # slug -> (csv stem, KISTA code, NL query)
    "geostationary": ("geostationary_filed", "GOCS",
                      "geostationary orbit complex satellite technology"),
    "1mw":           ("1MW_filed", "1MWDFS",
                      "1 MW dual-frequency antenna and feed system technology"),
    "marine":        ("marine_filed", "MPUART",
                      "augmented reality technology for marine plants and offshore facilities"),
    "micro":         ("micro_filed", "MRRG",
                      "micro radar rain gauge technology"),
}

IMP_MIN_TARGET_RATE = 0.005    # (a) CPC in >=0.5% of valid patents
IMP_MIN_LIFT = 50.0            # (b) target-rate / pool-rate > 50x


def _cpcs(s: str) -> list[str]:
    # keep full CPC symbol (subgroup); Choi selected at the code level present in the field
    return [c.strip() for c in str(s or "").split(",") if c.strip()]


def build(domain: str, seed: int = 42, neg_cap: int | None = None):
    stem, code, query = DOMAINS[domain]
    src = WRITING / f"{stem}.csv"
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- pass 1: pool CPC freq (background) + collect positives fully ----
    pool_cpc = Counter()
    n_total = 0
    positives: list[dict] = []
    tgt_cpc = Counter()
    with open(src, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            n_total += 1
            cset = set(_cpcs(row.get("cpc_code")))
            for c in cset:
                pool_cpc[c] += 1
            if str(row.get("valid", "")).strip().lower() == "true":
                positives.append(row)
                for c in cset:
                    tgt_cpc[c] += 1
            if n_total % 500000 == 0:
                print(f"  pass1 {n_total:,} rows...", flush=True)
    n_pos = len(positives)
    print(f"pass1 done: {n_total:,} rows, {n_pos} positives")

    # ---- important CPCs ----
    important = set()
    for c, tc in tgt_cpc.items():
        tr = tc / n_pos                                  # target rate
        pr = pool_cpc[c] / n_total                       # background rate (pool proxy)
        if tr >= IMP_MIN_TARGET_RATE and pr > 0 and (tr / pr) > IMP_MIN_LIFT:
            important.add(c)
    print(f"important CPCs: {len(important)}")

    # ---- pass 2: negatives that contain an important CPC ----
    negatives: list[dict] = []
    n2 = 0
    with open(src, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            n2 += 1
            if str(row.get("valid", "")).strip().lower() == "true":
                continue
            if important.intersection(_cpcs(row.get("cpc_code"))):
                negatives.append(row)
            if n2 % 500000 == 0:
                print(f"  pass2 {n2:,} rows... (neg kept {len(negatives):,})", flush=True)
    print(f"undersampled negatives: {len(negatives):,} (from {n_total - n_pos:,})")

    rng = random.Random(seed)
    if neg_cap and len(negatives) > neg_cap:
        negatives = rng.sample(negatives, neg_cap)
        print(f"  neg capped to {neg_cap:,}")

    # ---- stratified 6:2:2 split; emit TEST fold ----
    def split_test(rows):
        rows = rows[:]
        rng.shuffle(rows)
        n_test = round(len(rows) * 0.2)
        return rows[:n_test]
    test = split_test(positives) + split_test(negatives)
    rng.shuffle(test)
    n_test_pos = sum(1 for r in test if str(r.get("valid")).strip().lower() == "true")

    out_csv = OUT / f"{domain}_test.csv"
    with open(out_csv, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["family_id", "publication_number", "title", "abstract", "cpc", "ipc", "label"])
        for r in test:
            lab = 1 if str(r.get("valid")).strip().lower() == "true" else 0
            w.writerow([r.get("family_id", ""), r.get("publication_number", ""),
                        r.get("title_text", ""), r.get("abstract_text", ""),
                        r.get("cpc_code", ""), r.get("ipc_code", ""), lab])
    meta = {"domain": domain, "kista_code": code, "query": query, "seed": seed,
            "pool_total": n_total, "positives_total": n_pos,
            "important_cpc_count": len(important), "important_cpc": sorted(important),
            "undersampled_negatives": len(negatives),
            "test_rows": len(test), "test_positives": n_test_pos}
    (OUT / f"{domain}_meta.json").write_text(json.dumps(meta, indent=2, ensure_ascii=False),
                                             encoding="utf-8")
    print(f"\nTEST fold: {len(test):,} rows, {n_test_pos} positives -> {out_csv}")
    print(f"meta -> {OUT / f'{domain}_meta.json'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", required=True, choices=list(DOMAINS))
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--neg-cap", type=int, default=None,
                    help="cap undersampled negatives before split (cost control for pilots)")
    args = ap.parse_args()
    build(args.domain, args.seed, args.neg_cap)


if __name__ == "__main__":
    main()
