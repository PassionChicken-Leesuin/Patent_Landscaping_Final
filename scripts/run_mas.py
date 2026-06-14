"""Run MAS pseudo-labeling over the candidate pool (10-key parallel).

Examples
--------
# offline smoke test (no API, 50 patents):
python -m scripts.run_mas --mock --limit 50

# real run, all keys, full candidate pool:
python -m scripts.run_mas --workers 40

# real run, small pilot:
python -m scripts.run_mas --limit 80
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

import pandas as pd
from src import config as C
from src.mas import config as MC
from src.mas.rubric import load_rubric
from src.mas.runner import KeyPool, run_pool, write_ranked_csv
from src.mas.llm import load_openai_keys


def load_candidate_rows(limit: int | None) -> list[dict]:
    df = pd.read_csv(C.TRAINING_CLEAN_CSV, encoding="utf-8", dtype=str).fillna("")
    if limit:
        df = df.head(limit)
    return df[["record_id", "patent_id", "domain", "title", "abstract"]].to_dict("records")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true", help="offline deterministic stub (no API)")
    ap.add_argument("--limit", type=int, default=None, help="only first N candidates")
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--max-attempts", type=int, default=6)
    args = ap.parse_args()

    rows = load_candidate_rows(args.limit)
    rubric = load_rubric()
    print(f"candidates: {len(rows)} | domain: {MC.DOMAIN} | rubric: {MC.RUBRIC_PATH.name}")

    if args.mock:
        pool = KeyPool.mock(n=3)
        print("MODE: MOCK (no API calls)")
    else:
        keys = load_openai_keys(str(C.ROOT / ".env"))
        pool = KeyPool(keys, MC.LLM_FAST, MC.LLM_STRONG, MC.LLM_TEMPERATURE)
        print(f"MODE: OpenAI | keys: {pool.n} | model_fast: {MC.LLM_FAST} | workers: {args.workers}")

    out = run_pool(rows, rubric, pool, workers=args.workers, max_attempts=args.max_attempts)
    results, failures, usage = out["results"], out["failures"], out["usage"]

    csv_path = write_ranked_csv(results)

    print("\n" + "=" * 64)
    print(f"done: {len(results)} labeled, {len(failures)} failed in {out['elapsed_s']:.0f}s")
    print("candidate_type:", dict(Counter(r["candidate_type"] for r in results)))
    print(f"LLM calls: {usage.calls}  (~{usage.calls/max(len(results),1):.2f}/patent)  "
          f"tokens in/out: {usage.prompt_tokens}/{usage.completion_tokens}  ~${usage.cost_usd():.3f}")
    if not args.mock:
        print("per-key calls:", [u.calls for u in pool.per_key_usage])
    print(f"ranked CSV -> {csv_path}")
    print(f"audit JSONL -> {MC.AUDIT_JSONL}")
    if failures:
        print(f"\n⚠ {len(failures)} failures (see returned list / rerun). first:", failures[0])


if __name__ == "__main__":
    main()
