"""Evaluate the agentic system on the 6 gold domains (direct judgment, no training).

Per domain: fresh NL query (scripts/eval_queries.json) -> full agentic pipeline
(research -> corpus -> validated criteria -> criteria-strict judgment -> judgment
validator) over that domain's eval_processed.csv -> report_from_probs metrics.
Gold labels are NEVER shown to any agent; the eval pool text is read (corpus
stage) but only as unlabeled text.

Examples
--------
python -m scripts.eval_agentic --domains all --mock --limit 20 --hitl off
python -m scripts.eval_agentic --domains hydrogenstorage --hitl interactive
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

import numpy as np
import pandas as pd

from src import config as C
from src import domains as D
from src.downstream.evaluate import report_from_probs
from src.mas.llm import Usage, load_openai_keys
from src.mas.runner import KeyPool
from src.agentic import config as AC
from src.agentic import judge as J
from src.agentic.hitl import HITL, PendingHumanInput
from src.agentic.pipeline import build_criteria, research_llm
from src.agentic.search import make_search_client

QUERIES_PATH = Path(__file__).parent / "eval_queries.json"


def eval_rows(eval_df: pd.DataFrame, slug: str) -> pd.DataFrame:
    df = eval_df.copy()
    df["record_id"] = df["family_id"].astype(str)
    df["patent_id"] = df["record_id"]
    df["domain"] = slug
    df["title"] = df["title"].fillna("")
    df["abstract"] = df["abstract"].fillna("")
    return df


def run_domain(domain: str, query: str, args) -> dict | None:
    spec = D.get(domain)
    eval_df = pd.read_csv(spec.eval_processed, encoding="utf-8")
    eval_df["title"] = eval_df["title"].fillna("").astype(str)
    eval_df["abstract"] = eval_df["abstract"].fillna("").astype(str)
    if args.limit:
        eval_df = eval_df.head(args.limit)
    print(f"\n{'=' * 70}\n### {domain}: '{query}' | eval rows: {len(eval_df)}\n{'=' * 70}")

    pool_df = eval_rows(eval_df, domain)

    try:
        ws, scope, doc = build_criteria(query, pool_df[["record_id", "patent_id",
                                                        "title", "abstract"]],
                                        mock=args.mock, force=args.force,
                                        hitl_mode=args.hitl, variant=args.variant,
                                        no_research=args.no_research,
                                        no_corpus=args.no_corpus)
    except PendingHumanInput as e:
        print(f"[HITL] {domain}: {len(e.questions)} question(s) pending — fill answers.json, re-run")
        return None

    # ---- judge (resume-aware) ----
    from scripts.run_mas import done_record_ids
    done = done_record_ids(ws.judge_audit_jsonl)
    todo = pool_df[~pool_df["record_id"].isin(done)]
    print(f"[6] judge: {len(todo)}/{len(pool_df)} to judge")
    if args.mock:
        pool = J.mock_pool(3)
    else:
        keys = load_openai_keys(str(C.ROOT / ".env"))
        pool = KeyPool(keys, AC.MODEL_JUDGE_FAST, AC.MODEL_JUDGE_STRONG, AC.LLM_TEMPERATURE)
    if len(todo):
        rows = todo[["record_id", "patent_id", "domain", "title", "abstract"]].to_dict("records")
        out = J.judge_rows(ws, doc, rows, pool, workers=args.workers, append=bool(done),
                           second_pass=not args.no_second_pass)
        u = out["usage"]
        print(f"judged {len(out['results'])}, failed {len(out['failures'])} "
              f"| ~${u.cost_usd():.2f}")

    # ---- judgment validator ----
    if not args.no_validate:
        rows_by_id = {r["record_id"]: r for r in
                      pool_df[["record_id", "patent_id", "domain", "title", "abstract"]]
                      .to_dict("records")}
        try:
            J.validate_judgments(ws, doc, research_llm(args.mock), make_search_client(args.mock),
                                 HITL(ws, mode=args.hitl, stage="judge"),
                                 pool, rows_by_id, scope.canonical_name_en,
                                 Usage(), workers=args.workers)
        except PendingHumanInput as e:
            print(f"[HITL] {domain}: {len(e.questions)} question(s) pending during audit")
            return None

    # ---- closed-loop boundary discovery (opt-in) ----
    if args.boundary_loop:
        rows_by_id = {r["record_id"]: r for r in
                      pool_df[["record_id", "patent_id", "domain", "title", "abstract"]]
                      .to_dict("records")}
        try:
            J.boundary_feedback_round(ws, doc, research_llm(args.mock),
                                      HITL(ws, mode=args.hitl, stage="boundary-loop"),
                                      pool, pool, pool_df, rows_by_id,
                                      scope.canonical_name_en, Usage(), workers=args.workers)
        except PendingHumanInput as e:
            print(f"[HITL] {domain}: {len(e.questions)} boundary question(s) pending")
            return None

    # ---- metrics ----
    latest = J.judgments_from_audit(ws)
    missing = [rid for rid in pool_df["record_id"] if rid not in latest]
    if missing:
        print(f"WARNING: {len(missing)} rows unjudged (API failures?) — treated as score 0.5")
    p = np.array([float(latest.get(rid, {}).get("final_score", 0.5))
                  for rid in pool_df["record_id"]])
    y = eval_df["label"].astype(int).values
    res = report_from_probs(y, p, eval_df, threshold=AC.EVAL_THRESHOLD)

    stances = Counter(latest.get(rid, {}).get("stance", "missing")
                      for rid in pool_df["record_id"])
    cited: Counter = Counter()
    for rid in pool_df["record_id"]:
        e = latest.get(rid, {})
        cited.update(e.get("matched_criteria") or [])
        cited.update(e.get("violated_exclusions") or [])
    res.update({
        "domain": domain, "query": query, "slug": ws.slug,
        "stance_distribution": dict(stances),
        "abstain_rate": stances.get("abstain", 0) / max(1, len(pool_df)),
        "criteria_citation_counts": dict(cited.most_common()),
        "n_unjudged": len(missing),
    })

    AC.OUTPUTS_DIR.mkdir(exist_ok=True)
    tag = f"_{args.variant}" if args.variant else ""
    out_path = AC.OUTPUTS_DIR / f"agentic_metrics_{domain}{tag}.json"
    out_path.write_text(json.dumps(res, indent=2, ensure_ascii=False, default=float),
                        encoding="utf-8")
    ws.write_json(ws.metrics_json, json.loads(out_path.read_text(encoding="utf-8")))
    print(f"macro_f1={res['macro_f1']:.3f} auc={res['auc']:.3f} "
          f"recall={res['recall']:.3f} precision={res['precision']:.3f} "
          f"acc={res['accuracy']:.3f} -> {out_path}")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", default="all",
                    help="'all' or comma-separated keys (e.g. hydrogenstorage,blockchain)")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--hitl", choices=["interactive", "batch", "off"], default="interactive")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--no-validate", action="store_true")
    ap.add_argument("--variant", default="", help="experiment tag -> separate workspaces/outputs")
    ap.add_argument("--no-research", action="store_true")
    ap.add_argument("--no-corpus", action="store_true")
    ap.add_argument("--no-second-pass", action="store_true")
    ap.add_argument("--boundary-loop", action="store_true",
                    help="closed loop: discover scope questions from uncertain judgments")
    args = ap.parse_args()

    queries = json.loads(QUERIES_PATH.read_text(encoding="utf-8"))
    queries.pop("_comment", None)
    keys = list(queries) if args.domains == "all" else [d.strip() for d in args.domains.split(",")]

    all_res = []
    for k in keys:
        if k not in queries:
            print(f"skip {k}: no query in eval_queries.json")
            continue
        r = run_domain(k, queries[k], args)
        if r:
            all_res.append(r)

    if all_res:
        cols = ["domain", "accuracy", "precision", "recall", "macro_f1", "auc",
                "auc_seed_vs_hard", "auc_seed_vs_easy", "abstain_rate"]
        table = pd.DataFrame([{c: r.get(c) for c in cols} for r in all_res])
        avg = {c: table[c].mean() for c in cols if c != "domain"}
        table = pd.concat([table, pd.DataFrame([{"domain": "AVERAGE", **avg}])],
                          ignore_index=True)
        AC.OUTPUTS_DIR.mkdir(exist_ok=True)
        tag = f"_{args.variant}" if args.variant else ""
        cmp_path = AC.OUTPUTS_DIR / f"agentic_comparison{tag}.csv"
        table.to_csv(cmp_path, index=False, encoding="utf-8")
        print(f"\n{table.round(3).to_string(index=False)}\ncomparison -> {cmp_path}")


if __name__ == "__main__":
    main()
