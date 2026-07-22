"""Query-driven agentic domain-valid patent identification (full pipeline).

Examples
--------
# offline smoke test (no API keys, no network):
python -m scripts.run_agentic --query "hydrogen storage technology" --mock --limit 20 --hitl off

# criteria only (research + corpus + validated criteria document):
python -m scripts.run_agentic --query "수소 저장 기술" --input DataSet/processed/hydrogenstorage/eval_processed.csv --criteria-only

# full run with resume:
python -m scripts.run_agentic --query "수소 저장 기술" --input <pool.csv> --resume --workers 40
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
from src.mas.llm import Usage, load_openai_keys
from src.mas.runner import KeyPool, write_ranked_csv
from src.agentic import config as AC
from src.agentic import judge as J
from src.agentic.hitl import HITL, PendingHumanInput, profile_path
from src.agentic.pipeline import build_criteria, research_llm
from src.agentic.search import make_search_client


def load_pool(path: str, limit: int | None) -> pd.DataFrame:
    df = pd.read_csv(path, encoding="utf-8", dtype=str).fillna("")
    if "record_id" not in df.columns:
        idc = "family_id" if "family_id" in df.columns else ("patent_id" if "patent_id" in df.columns else None)
        df["record_id"] = df[idc].astype(str) if idc else [f"row{i}" for i in range(len(df))]
    if "patent_id" not in df.columns:
        df["patent_id"] = df["record_id"]
    for col in ("title", "abstract"):
        if col not in df.columns:
            raise SystemExit(f"input CSV must have a '{col}' column")
    if limit:
        df = df.head(limit)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="natural-language domain query (any language)")
    ap.add_argument("--input", default=None, help="patent pool CSV (title/abstract [+record_id])")
    ap.add_argument("--mock", action="store_true", help="offline: mock search + mock LLM")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--resume", action="store_true", help="skip record_ids already judged")
    ap.add_argument("--hitl", choices=["interactive", "batch", "off"], default="interactive")
    ap.add_argument("--criteria-only", action="store_true")
    ap.add_argument("--force", action="store_true", help="rebuild cached stages")
    ap.add_argument("--no-validate", action="store_true", help="skip the judgment validator loop")
    ap.add_argument("--variant", default="", help="experiment tag -> separate workspace slug")
    ap.add_argument("--no-research", action="store_true", help="ablation: skip web research")
    ap.add_argument("--local-doc", action="append", default=None, metavar="PATH",
                    help="local reference document (pdf/txt/md) fed to the research "
                         "agent alongside web evidence; repeatable")
    ap.add_argument("--local-doc-allow-flagged", action="store_true",
                    help="ingest a --local-doc even when the benchmark-leak scan "
                         "flags it (default: stop and ask the user to review)")
    ap.add_argument("--no-corpus", action="store_true", help="ablation: skip corpus reading")
    ap.add_argument("--no-second-pass", action="store_true", help="ablation: skip judge confirmation pass")
    ap.add_argument("--boundary-loop", action="store_true",
                    help="closed loop: discover scope questions from uncertain judgments, re-judge")
    args = ap.parse_args()

    if not args.input and not args.criteria_only:
        raise SystemExit("--input is required unless --criteria-only")
    pool_df = load_pool(args.input, args.limit) if args.input else pd.DataFrame(
        columns=["record_id", "patent_id", "title", "abstract"])

    # ---- stages [1]-[5]: research -> corpus -> validated criteria ----
    try:
        ws, scope, doc = build_criteria(args.query, pool_df, mock=args.mock,
                                        force=args.force, hitl_mode=args.hitl,
                                        no_research=args.no_research,
                                        no_corpus=args.no_corpus, variant=args.variant,
                                        local_docs=args.local_doc,
                                        local_docs_allow_flagged=args.local_doc_allow_flagged)
    except PendingHumanInput as e:
        print(f"\n[HITL] {len(e.questions)}건의 질문이 대기 중입니다.")
        print(f"  질문: {Path.cwd()}")
        print("  -> questions_pending.json 을 확인하고 answers.json 을 작성한 뒤 같은 명령을 재실행하세요.")
        sys.exit(2)

    if args.criteria_only or pool_df.empty:
        print("criteria-only run complete.")
        return

    # ---- stage [6]: judgment ----
    from scripts.run_mas import done_record_ids
    done = done_record_ids(ws.judge_audit_jsonl) if args.resume else set()
    todo = pool_df[~pool_df["record_id"].isin(done)] if done else pool_df
    print(f"\n[6] judge: pool={len(pool_df)} | already judged={len(done)} | to judge={len(todo)}")

    if args.mock:
        pool = J.mock_pool(3)
        print("MODE: MOCK")
    else:
        keys = load_openai_keys(str(C.ROOT / ".env"))
        pool = KeyPool(keys, AC.MODEL_JUDGE_FAST, AC.MODEL_JUDGE_STRONG, AC.LLM_TEMPERATURE)
        print(f"MODE: OpenAI | keys: {pool.n} | workers: {args.workers}")

    if len(todo):
        rows = todo[["record_id", "patent_id", "title", "abstract"]].to_dict("records")
        for r in rows:
            r["domain"] = ws.slug
        out = J.judge_rows(ws, doc, rows, pool, workers=args.workers, append=args.resume,
                           second_pass=not args.no_second_pass)
        u = out["usage"]
        print(f"judged {len(out['results'])}, failed {len(out['failures'])} in "
              f"{out['elapsed_s']:.0f}s | calls={u.calls} ~${u.cost_usd():.2f}")

    # ---- stage [7]: judgment validator loop ----
    if not args.no_validate:
        print("\n[7] judgment validator")
        rows_by_id = {str(r["record_id"]): {"record_id": str(r["record_id"]),
                                            "patent_id": str(r["patent_id"]),
                                            "domain": ws.slug,
                                            "title": r["title"], "abstract": r["abstract"]}
                      for _, r in pool_df.iterrows()}
        vusage = Usage()
        try:
            J.validate_judgments(ws, doc, research_llm(args.mock),
                                 make_search_client(args.mock),
                                 HITL(ws, mode=args.hitl, stage="judge",
                                      profile=profile_path(scope.canonical_name_en, args.mock)),
                                 pool, rows_by_id, scope.canonical_name_en,
                                 vusage, workers=args.workers)
        except PendingHumanInput as e:
            print(f"\n[HITL] 판정 감사 중 질문 {len(e.questions)}건 대기 — answers.json 작성 후 재실행하세요.")
            sys.exit(2)

    # ---- stage [3-loop]: closed-loop boundary discovery (opt-in) ----
    if args.boundary_loop:
        print("\n[3-loop] boundary discovery from uncertain judgments")
        rows_by_id = {str(r["record_id"]): {"record_id": str(r["record_id"]),
                                            "patent_id": str(r["patent_id"]), "domain": ws.slug,
                                            "title": r["title"], "abstract": r["abstract"]}
                      for _, r in pool_df.iterrows()}
        try:
            J.boundary_feedback_round(ws, doc, research_llm(args.mock),
                                      HITL(ws, mode=args.hitl, stage="boundary-loop",
                                           profile=profile_path(scope.canonical_name_en, args.mock)),
                                      pool, pool, pool_df, rows_by_id,
                                      scope.canonical_name_en, Usage(), workers=args.workers)
        except PendingHumanInput:
            print("\n[HITL] 경계 발견 질문 대기 — answers.json 작성 후 재실행하세요.")
            sys.exit(2)

    # ---- ranked CSV from the final audit state ----
    latest = J.judgments_from_audit(ws)
    meta = pool_df.set_index("record_id")
    results = []
    for rid, e in latest.items():
        if rid not in meta.index:
            continue
        results.append({"record_id": rid, "patent_id": e.get("patent_id", ""),
                        "domain": ws.slug,
                        "title": meta.loc[rid, "title"], "abstract": meta.loc[rid, "abstract"],
                        "final_score": e.get("final_score"),
                        "candidate_type": e.get("candidate_type"),
                        "source": e.get("stance", "")})
    path = write_ranked_csv(results, path=ws.ranked_csv)
    print(f"\nranked CSV ({len(results)} rows) -> {path}")
    print("candidate_type:", dict(Counter(r["candidate_type"] for r in results)))
    print(f"기준서: {ws.criteria_final_md}")


if __name__ == "__main__":
    main()
