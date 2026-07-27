"""KISTA benchmark — criteria-first MAS vs. Choi et al. (2022, TFSC) on their EXACT test folds.

Choi et al. released the exact sampled train/val/test splits used in their paper
(patent-landscaping.s3.amazonaws.com/patent-dataset/<domain>_samples_{train,val,test}.csv).
Each test fold = all test-positives + 10,000 CPC-undersampled negatives; the task is binary
"valid/target patent" selection from a noisy keyword-retrieved pool — i.e. OUR task
(domain relevance), same abstract-only footing as our judge.

We run our ZERO-TRAINING pipeline and report F1 + AP, directly comparable to their Table 8
(same rows, same protocol; no model reproduction needed). To mirror their train->test setup
and avoid transductive leakage, criteria are synthesized ONLY from the TRAIN split's UNLABELED
text (corpus/case-mapping), then applied to the held-out TEST split. We never read test text
while forming criteria, and never read any labels.

Run:
  python -m scripts.eval_kista --domain gocs --mock --limit 40   # plumbing smoke test
  python -m scripts.eval_kista --domain gocs                     # real pilot
  python -m scripts.eval_kista --domain all
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd
from sklearn.metrics import (precision_score, recall_score, f1_score,
                             average_precision_score)

from src import config as C
from src.mas.llm import Usage, load_openai_keys
from src.mas.runner import KeyPool
from src.agentic import config as AC
from src.agentic import judge as J
from src.agentic.axes import AxisSynthesisBlocked
from src.agentic.hitl import HITL, PendingHumanInput
from src.agentic.pipeline import build_criteria, research_llm
from src.agentic.search import make_search_client
from src.agentic.validator import CriteriaValidationBlocked

KISTA_DIR = C.ROOT / "DataSet" / "kista"

# slug -> (KISTA code, NL domain query). Queries corrected to the TRUE domain subject, verified
# against each domain's positive-set vocabulary (Appendix A search formulas and Table 3 keywords
# disagree for GOCS/1MWDFS; the positives resolve it). An optional owner-doc (scope_<slug>.md)
# injects the same scope as a reference document via --owner-doc.
DOMAINS = {
    "gocs":   ("GOCS",   "satellite GNSS and pseudolite based positioning and navigation technology"),
    "mpuart": ("MPUART", "augmented, virtual and mixed reality technology (incl. marine/offshore plant use)"),
    "1mwdfs": ("1MWDFS", "dual- and multi-frequency induction heating for surface hardening of metal parts"),
    "mrrg":   ("MRRG",   "radar and microwave based precipitation and weather measurement"),
}

# Choi et al. 2022, Table 8 (F1; AP where noted) — for side-by-side context, per domain.
THEIRS = {
    "mpuart": {"APL": 0.5323, "PatentBERT": 0.5323, "TRF+DIFF": 0.8361, "TRF+DIFF_AP": 0.7038},
    "1mwdfs": {"APL": 0.6540, "PatentBERT": 0.7476, "TRF+DIFF": 0.7339, "TRF+DIFF_AP": 0.5555},
    "mrrg":   {"APL": 0.5074, "PatentBERT": 0.8641, "TRF+DIFF": 0.8941, "TRF+DIFF_AP": 0.8029},
    "gocs":   {"APL": 0.5742, "PatentBERT": 0.6403, "TRF+DIFF": 0.6203, "TRF+DIFF_AP": 0.4094},
}


def load_split(domain: str, split: str, limit: int | None) -> pd.DataFrame:
    df = pd.read_csv(KISTA_DIR / f"{domain}_samples_{split}.csv", encoding="utf-8", dtype=str)
    df["title"] = df["title_text"].fillna("").astype(str)
    df["abstract"] = df["abstract_text"].fillna("").astype(str)
    df["label"] = df["valid"].map(lambda v: int(str(v).strip().lower() == "true"))
    df["record_id"] = df["publication_number"].astype(str)
    df["patent_id"] = df["record_id"]
    df["domain"] = domain
    if limit:                                   # smoke test: keep some positives + some negatives
        df = pd.concat([df[df.label == 1].head(limit),
                        df[df.label == 0].head(limit)]).reset_index(drop=True)
    return df


def run_domain(domain: str, args) -> dict | None:
    code, query = DOMAINS[domain]
    train = load_split(domain, "train", args.limit)   # criteria come from TRAIN only
    train = train.sample(frac=1, random_state=42).reset_index(drop=True)  # corpus reads first 10k
    df = load_split(domain, "test", args.limit)        # judged / scored (held out)
    if args.sample and len(df) > args.sample:          # cost control: all positives + neg sample
        pos = df[df.label == 1]
        neg = df[df.label == 0].sample(n=max(0, args.sample - len(pos)), random_state=42)
        df = pd.concat([pos, neg]).sample(frac=1, random_state=42).reset_index(drop=True)
        print(f"[sample] judging {len(df)} rows (all {int(pos.label.sum())} pos + "
              f"{len(neg)} sampled neg) — NOT the full test fold (dev only, not vs Table 8)")
    npos, npos_tr = int(df.label.sum()), int(train.label.sum())
    print(f"\n{'=' * 74}\n### {domain} ({code}): '{query}'"
          f"\n    train rows: {len(train)} ({npos_tr} pos) | test rows: {len(df)} "
          f"({npos} pos, {npos/len(df):.2%})\n{'=' * 74}")

    variant = f"kista-{domain}" + ("-owner" if args.owner_doc else "")
    local_docs = None
    if args.owner_doc:
        scope_md = KISTA_DIR / f"scope_{domain}.md"
        if scope_md.exists():
            local_docs = [str(scope_md)]
            print(f"[owner-doc] injecting scope memo: {scope_md.name}")
        else:
            print(f"[owner-doc] WARNING: {scope_md.name} not found — running query-only")
    try:
        ws, scope, doc = build_criteria(
            query, train[["record_id", "patent_id", "title", "abstract"]],
            mock=args.mock, force=args.force, hitl_mode="off",
            variant=variant, no_research=args.no_research, no_corpus=args.no_corpus,
            local_docs=local_docs)
    except PendingHumanInput as e:
        print(f"[HITL] {domain}: {len(e.questions)} pending — skipped")
        return None
    except (CriteriaValidationBlocked, AxisSynthesisBlocked) as e:
        print(f"[BLOCKED] {domain}: {e}")
        return None

    if args.force:                          # --force must re-judge with the rebuilt criteria
        ws.judge_audit_jsonl.unlink(missing_ok=True)
        print("[force] cleared judge audit — re-judging with rebuilt criteria")
    from scripts.run_mas import done_record_ids
    done = done_record_ids(ws.judge_audit_jsonl)
    todo = df[~df["record_id"].isin(done)]
    print(f"[judge] {len(todo)}/{len(df)} rows to judge")
    if args.mock:
        pool = J.mock_pool(3)
    else:
        keys = load_openai_keys(str(C.ROOT / ".env"))
        pool = KeyPool(keys, AC.MODEL_JUDGE_FAST, AC.MODEL_JUDGE_STRONG, AC.LLM_TEMPERATURE)
    if len(todo):
        rows = todo[["record_id", "patent_id", "domain", "title", "abstract"]].to_dict("records")
        out = J.judge_rows(ws, doc, rows, pool, workers=args.workers, append=bool(done),
                           second_pass=not args.no_second_pass)
        print(f"judged {len(out['results'])}, failed {len(out['failures'])} "
              f"| ~${out['usage'].cost_usd():.2f}")

    if args.validate:
        rows_by_id = {r["record_id"]: r for r in
                      df[["record_id", "patent_id", "domain", "title", "abstract"]].to_dict("records")}
        try:
            J.validate_judgments(ws, doc, research_llm(args.mock), make_search_client(args.mock),
                                 HITL(ws, mode="off", stage="judge"), pool, rows_by_id,
                                 scope.canonical_name_en, Usage(), workers=args.workers)
        except PendingHumanInput:
            pass

    # ---- metrics on THEIR exact test fold ----
    latest = J.judgments_from_audit(ws)
    y = df["label"].astype(int).values
    scores = np.array([float(latest.get(rid, {}).get(
        "relevance_score", latest.get(rid, {}).get("final_score", 0.5)))
        for rid in df["record_id"]])
    yhat = np.array([int(bool(latest.get(rid, {}).get(
        "included", latest.get(rid, {}).get("stance") == "in_domain")))
        for rid in df["record_id"]])
    n_missing = int(sum(1 for rid in df["record_id"] if rid not in latest))
    res = {
        "domain": domain, "kista_code": code, "query": query, "slug": ws.slug,
        "n_test": int(len(df)), "n_pos": npos, "n_train": int(len(train)), "n_pos_train": npos_tr,
        "precision": float(precision_score(y, yhat, zero_division=0)),
        "recall": float(recall_score(y, yhat, zero_division=0)),
        "f1": float(f1_score(y, yhat, zero_division=0)),
        "ap": float(average_precision_score(y, scores)) if y.sum() else 0.0,
        "tp": int(((yhat == 1) & (y == 1)).sum()), "fp": int(((yhat == 1) & (y == 0)).sum()),
        "fn": int(((yhat == 0) & (y == 1)).sum()), "n_unjudged": n_missing,
    }
    t = THEIRS[domain]
    print(f"\n  OURS   P={res['precision']:.3f} R={res['recall']:.3f} "
          f"F1={res['f1']:.4f} AP={res['ap']:.4f}  (TP{res['tp']}/FP{res['fp']}/FN{res['fn']})"
          + (f"  [{n_missing} unjudged]" if n_missing else ""))
    print(f"  THEIRS F1: APL={t['APL']:.3f}  PatentBERT={t['PatentBERT']:.3f}  "
          f"TRF+DIFF={t['TRF+DIFF']:.3f}  (TRF+DIFF AP={t['TRF+DIFF_AP']:.3f})")
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", default="gocs", help="'all' or one of: " + ", ".join(DOMAINS))
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--owner-doc", action="store_true",
                    help="inject DataSet/kista/scope_<domain>.md as an owner reference document "
                         "(owner-in-the-loop condition; still zero training labels)")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--sample", type=int, default=None,
                    help="judge only N test rows (all positives + sampled negatives) to save "
                         "cost during development; not comparable to the full-fold Table 8")
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--no-research", action="store_true")
    ap.add_argument("--no-corpus", action="store_true")
    ap.add_argument("--no-second-pass", action="store_true")
    args = ap.parse_args()

    doms = list(DOMAINS) if args.domain == "all" else [args.domain]
    results = []
    for d in doms:
        if d not in DOMAINS:
            print(f"skip {d}: unknown domain")
            continue
        r = run_domain(d, args)
        if r:
            results.append(r)

    AC.OUTPUTS_DIR.mkdir(exist_ok=True)
    tag = "_owner" if args.owner_doc else "_queryonly"
    out_path = AC.OUTPUTS_DIR / f"kista_results{tag}.json"
    payload = {"condition": "owner_doc" if args.owner_doc else "query_only",
               "results": results, "theirs": THEIRS}
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if results:
        tab = pd.DataFrame([{k: r[k] for k in
                             ("domain", "n_test", "n_pos", "precision", "recall", "f1", "ap")}
                            for r in results])
        print("\n" + "=" * 74)
        print(tab.round(4).to_string(index=False))
    print(f"\n-> {out_path}")


if __name__ == "__main__":
    main()
