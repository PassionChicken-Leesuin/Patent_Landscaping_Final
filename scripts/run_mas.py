"""Run MAS pseudo-labeling over a candidate set (10-key parallel).

Examples
--------
# offline smoke test (no API):
python -m scripts.run_mas --mock --limit 50

# unified full set, resume (skip already-labeled patents in the audit):
python -m scripts.run_mas --input DataSet/processed/candidate_all.csv --resume --workers 40

# original pool, fresh:
python -m scripts.run_mas --workers 40
"""
from __future__ import annotations
import argparse
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
from src import domains as D
from src.mas import config as MC
from src.mas.rubric import load_rubric
from src.mas.runner import KeyPool, run_pool, write_ranked_csv
from src.mas.scoring import score_and_type
from src.mas.llm import load_openai_keys


def done_record_ids(audit_path) -> set:
    if not audit_path.exists():
        return set()
    ids = set()
    for line in open(audit_path, encoding="utf-8"):
        try:
            ids.add(json.loads(line)["record_id"])
        except Exception:
            pass
    return ids


def rebuild_ranked_from_audit(input_df: pd.DataFrame, audit_path, default_domain: str):
    """Ranked CSV over the FULL audit, joining title/abstract from the input set."""
    meta = input_df.set_index("record_id")
    results = []
    for line in open(audit_path, encoding="utf-8"):
        r = json.loads(line)
        rid = r["record_id"]
        if rid not in meta.index:        # audit entry no longer in the candidate set (e.g. removed as leak)
            continue
        sc = score_and_type(r)
        title = meta.loc[rid, "title"] if rid in meta.index else ""
        abstract = meta.loc[rid, "abstract"] if rid in meta.index else ""
        source = meta.loc[rid, "source"] if (rid in meta.index and "source" in meta.columns) else ""
        results.append({"record_id": rid, "patent_id": r.get("patent_id", ""),
                        "domain": r.get("domain", default_domain), "title": title, "abstract": abstract,
                        "final_score": sc["final_score"], "candidate_type": sc["candidate_type"],
                        "source": source})
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default=D.AUTONOMOUS, help="domain key (default: self-driving)")
    ap.add_argument("--input", default=None, help="candidate CSV (default: domain candidate_all.csv)")
    ap.add_argument("--resume", action="store_true", help="skip record_ids already in the audit; append")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--max-attempts", type=int, default=6)
    args = ap.parse_args()

    spec = D.get(args.domain)
    input_path = args.input or str(spec.candidate_all)
    audit_path, ranked_path = spec.mas_audit, spec.mas_ranked
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path, encoding="utf-8", dtype=str).fillna("")
    if args.limit:
        df = df.head(args.limit)
    rubric = load_rubric(spec.rubric_path)

    done = done_record_ids(audit_path) if args.resume else set()
    todo = df[~df["record_id"].isin(done)] if done else df
    print(f"domain: {args.domain} | input: {len(df)} | already labeled: {len(done)} | "
          f"to label: {len(todo)} | rubric: {spec.rubric_path.name}")

    if len(todo):
        rows = todo[["record_id", "patent_id", "domain", "title", "abstract"]].to_dict("records")
        if args.mock:
            pool = KeyPool.mock(n=3); print("MODE: MOCK")
        else:
            keys = load_openai_keys(str(C.ROOT / ".env"))
            pool = KeyPool(keys, MC.LLM_FAST, MC.LLM_STRONG, MC.LLM_TEMPERATURE)
            print(f"MODE: OpenAI | keys: {pool.n} | workers: {args.workers}")
        out = run_pool(rows, rubric, pool, workers=args.workers,
                       max_attempts=args.max_attempts, append=args.resume, audit_path=audit_path)
        usage, failures = out["usage"], out["failures"]
        print(f"\nlabeled {len(out['results'])}, failed {len(failures)} in {out['elapsed_s']:.0f}s | "
              f"calls={usage.calls} ~${usage.cost_usd():.2f}")
        if not args.mock:
            print("per-key calls:", [u.calls for u in pool.per_key_usage])
    else:
        print("nothing to label (all in audit).")

    # rebuild ranked CSV over the full audit
    results = rebuild_ranked_from_audit(df, audit_path, args.domain)
    path = write_ranked_csv(results, path=ranked_path)
    print(f"\nranked CSV ({len(results)} rows) -> {path}")
    print("candidate_type:", dict(Counter(r["candidate_type"] for r in results)))


if __name__ == "__main__":
    main()
