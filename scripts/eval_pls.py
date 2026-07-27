"""PLS benchmark pilot — criteria-first MAS vs. Pujari et al. (EMNLP 2022) on Ritonavir.

The Bosch/WIPO PLS datasets label an *already-relevant* patent landscape into K
application categories (a multi-label task; their TMM uses one binary head per label,
and macro/micro-F1 aggregate those per-label binary decisions). We reformulate each
category as a natural-language DOMAIN QUERY and run our zero-training criteria-first
pipeline as K independent binary relevance selections, then aggregate the SAME way —
producing numbers comparable to their Table 5 on the SAME test split.

Protocol (mirrors their train/test):
- criteria are built reading ONLY the train split's unlabeled text (corpus stage);
- the held-out TEST split is judged;
- per-category P/R/F1 on the test split -> macro-F1 (mean over categories) + micro-F1
  (pooled over all (patent, category) decisions).

Our method uses ZERO training labels; theirs is supervised on ~85%. That asymmetry —
not a raw win — is the point.

Run:
  python -m scripts.eval_pls --mock --limit 20            # plumbing smoke test
  python -m scripts.eval_pls --categories Combinations    # one real category
  python -m scripts.eval_pls                              # all 7, background-friendly
"""
from __future__ import annotations
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import pandas as pd
from sklearn.metrics import precision_score, recall_score, f1_score

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

PLS_DIR = C.ROOT / "DataSet" / "pls"

# Category -> natural-language domain query. Written the way a domain owner would ask,
# NOT copied from the benchmark's label glossary (the pipeline canonicalizes them).
RITO_QUERIES = {
    "Combinations":
        "combination formulations that pair ritonavir with other antiretroviral drugs",
    "Prodrug":
        "prodrug forms of ritonavir (compounds that convert to ritonavir in the body)",
    "Pharmaceutical Compositions":
        "pharmaceutical compositions and formulations of ritonavir",
    "Derivatives":
        "chemical derivatives and analogues of ritonavir",
    "Methods of Treating HIV":
        "methods of treating HIV/AIDS with ritonavir-based therapy",
    "Synthesis and Crystalline Forms":
        "synthesis processes and crystalline or polymorphic forms of ritonavir",
    "Stabilized Forms":
        "stabilized formulations of ritonavir that improve shelf-life or stability",
}


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def _compose_fulltext(row) -> str:
    """All inputs the benchmark model used, packed into one judge-visible text block
    (title stays separate). Mirrors Pujari et al.: title+abstract, claims, description,
    plus CPC/IPC labels — the recall signal ('co-administered with ritonavir') lives in
    claims/description, not the abstract."""
    parts = [str(row.get("abstract", "")).strip()]
    if str(row.get("claims", "")).strip():
        parts.append("[CLAIMS] " + str(row["claims"]).strip())
    if str(row.get("description", "")).strip():
        parts.append("[DESCRIPTION] " + str(row["description"]).strip())
    tags = " ".join(x for x in [str(row.get("cpc", "")).strip(),
                                str(row.get("ipc", "")).strip()] if x)
    if tags:
        parts.append("[CPC/IPC] " + tags)
    return "\n\n".join(p for p in parts if p)


def load_data(limit: int | None, fulltext: bool):
    fname = "ritonavir_full.csv" if fulltext else "ritonavir_slim.csv"
    df = pd.read_csv(PLS_DIR / fname, encoding="utf-8", dtype=str).fillna("")
    df["title"] = df["title"].fillna("")
    df["abstract"] = df["abstract"].fillna("")
    df["abstract_full"] = (df.apply(_compose_fulltext, axis=1) if fulltext
                           else df["abstract"])
    df["catset"] = df["cats"].fillna("").apply(lambda s: set(x for x in s.split("|") if x))
    test_ids = {l.strip() for l in (PLS_DIR / "test-split.txt").read_text().splitlines() if l.strip()}
    train_ids = set()
    for i in range(1, 6):
        train_ids |= {l.strip() for l in (PLS_DIR / f"split-{i}.txt").read_text().splitlines() if l.strip()}
    df["split"] = df["family_id"].map(lambda x: "test" if x in test_ids
                                      else ("train" if x in train_ids else "?"))
    if limit:                                    # smoke test: shrink both splits
        keep = pd.concat([df[df.split == "train"].head(limit),
                          df[df.split == "test"].head(limit)])
        df = keep
    return df


def pool_frame(df: pd.DataFrame, category: str) -> pd.DataFrame:
    out = df.copy()
    out["record_id"] = out["family_id"].astype(str)
    out["patent_id"] = out["record_id"]
    out["domain"] = "rito-" + _slug(category)
    out["label"] = out["catset"].map(lambda s: int(category in s))
    return out


def judge_text_col(df: pd.DataFrame, fulltext: bool) -> pd.DataFrame:
    """Rows for the judge: when fulltext, the 'abstract' field the judge renders IS the
    composed full-text block (criteria are still built from the plain abstract upstream)."""
    d = df.copy()
    if fulltext:
        d["abstract"] = d["abstract_full"]
    return d


def run_category(category: str, df: pd.DataFrame, args) -> dict | None:
    query = RITO_QUERIES[category]
    pf = pool_frame(df, category)
    # BOTH criteria-building (corpus/casemap on train) and judging (test) see full text
    train = judge_text_col(pf[pf.split == "train"], args.fulltext)
    test = judge_text_col(pf[pf.split == "test"], args.fulltext)
    npos_tr, npos_te = int(train.label.sum()), int(test.label.sum())
    print(f"\n{'=' * 72}\n### {category}: '{query}'"
          f"\n    train {len(train)} ({npos_tr} pos) | test {len(test)} ({npos_te} pos)\n{'=' * 72}")

    variant = f"plsrito-{_slug(category)}"
    try:
        # criteria formed from TRAIN text only (unlabeled) — mirrors their train/test protocol
        ws, scope, doc = build_criteria(
            query, train[["record_id", "patent_id", "title", "abstract"]],
            mock=args.mock, force=args.force, hitl_mode="off",
            variant=variant, no_research=args.no_research, no_corpus=args.no_corpus)
    except PendingHumanInput as e:
        print(f"[HITL] {category}: {len(e.questions)} pending — skipped (run with --hitl)")
        return None
    except (CriteriaValidationBlocked, AxisSynthesisBlocked) as e:
        print(f"[BLOCKED] {category}: {e}")
        return None

    # judge the TEST split (resume-aware)
    from scripts.run_mas import done_record_ids
    done = done_record_ids(ws.judge_audit_jsonl)
    todo = test[~test["record_id"].isin(done)]
    print(f"[judge] {len(todo)}/{len(test)} test rows to judge")
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
                      test[["record_id", "patent_id", "domain", "title", "abstract"]]
                      .to_dict("records")}
        try:
            J.validate_judgments(ws, doc, research_llm(args.mock), make_search_client(args.mock),
                                 HITL(ws, mode="off", stage="judge"), pool, rows_by_id,
                                 scope.canonical_name_en, Usage(), workers=args.workers)
        except PendingHumanInput:
            pass

    # metrics on the test split
    latest = J.judgments_from_audit(ws)
    y = test["label"].astype(int).values
    scores = np.array([float(latest.get(rid, {}).get(
        "relevance_score", latest.get(rid, {}).get("final_score", 0.5)))
        for rid in test["record_id"]])
    yhat = np.array([int(bool(latest.get(rid, {}).get(
        "included", latest.get(rid, {}).get("stance") == "in_domain")))
        for rid in test["record_id"]])
    n_missing = int(sum(1 for rid in test["record_id"] if rid not in latest))
    res = {
        "category": category, "query": query, "slug": ws.slug,
        "n_test": int(len(test)), "n_pos_test": npos_te,
        "n_train": int(len(train)), "n_pos_train": npos_tr,
        "precision": float(precision_score(y, yhat, zero_division=0)),
        "recall": float(recall_score(y, yhat, zero_division=0)),
        "f1": float(f1_score(y, yhat, zero_division=0)),
        "n_unjudged": n_missing,
        "y": y.tolist(), "yhat": yhat.tolist(),      # kept for pooled micro aggregation
    }
    print(f"  P={res['precision']:.3f} R={res['recall']:.3f} F1={res['f1']:.3f}"
          + (f"  ({n_missing} unjudged)" if n_missing else ""))
    return res


def aggregate(results: list[dict]) -> dict:
    if not results:
        return {}
    macro = {m: float(np.mean([r[m] for r in results]))
             for m in ("precision", "recall", "f1")}
    y_all = np.concatenate([np.array(r["y"]) for r in results])
    yhat_all = np.concatenate([np.array(r["yhat"]) for r in results])
    micro = {
        "precision": float(precision_score(y_all, yhat_all, zero_division=0)),
        "recall": float(recall_score(y_all, yhat_all, zero_division=0)),
        "f1": float(f1_score(y_all, yhat_all, zero_division=0)),
    }
    return {"macro": macro, "micro": micro, "n_decisions": int(len(y_all))}


# Pujari et al. (2022) Table 5, Ritonavir (macro-avg / micro-avg F1) — for side-by-side context.
THEIRS_RITO = {
    "SVM (Benites 2018)":            {"macro_f1": 0.511, "micro_f1": 0.582},
    "TMM + e(t+a) (Pujari 2021)":    {"macro_f1": 0.443, "micro_f1": 0.660},
    "TMM best (all text; cpc_graph)": {"macro_f1": 0.539, "micro_f1": 0.677},
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--categories", default="all",
                    help="'all' or comma-separated category names")
    ap.add_argument("--mock", action="store_true")
    ap.add_argument("--fulltext", action="store_true",
                    help="feed all benchmark inputs (abstract+claims+description+CPC/IPC) to "
                         "BOTH criteria-building and judging")
    ap.add_argument("--read-chars", type=int, default=6000,
                    help="corpus/casemap per-patent read cap when --fulltext")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--workers", type=int, default=40)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--validate", action="store_true",
                    help="also run the judgment validator (slower; part of full method)")
    ap.add_argument("--no-research", action="store_true")
    ap.add_argument("--no-corpus", action="store_true")
    ap.add_argument("--no-second-pass", action="store_true")
    args = ap.parse_args()

    if args.fulltext:
        # let the criteria-building corpus/casemap actually READ the full text
        # (defaults truncate to ~600/520 chars, which strands the signal in the abstract)
        AC.CORPUS_ABSTRACT_CHARS = max(AC.CORPUS_ABSTRACT_CHARS, args.read_chars)
        AC.CASEMAP_TEXT_CHARS = max(AC.CASEMAP_TEXT_CHARS, args.read_chars)
        print(f"[fulltext] corpus/casemap read cap -> {args.read_chars} chars")

    df = load_data(args.limit, args.fulltext)
    cats = (list(RITO_QUERIES) if args.categories == "all"
            else [c.strip() for c in args.categories.split(",")])

    results = []
    for c in cats:
        if c not in RITO_QUERIES:
            print(f"skip {c}: unknown category")
            continue
        r = run_category(c, df, args)
        if r:
            results.append(r)

    agg = aggregate(results)
    AC.OUTPUTS_DIR.mkdir(exist_ok=True)
    payload = {"dataset": "ritonavir", "results": results, "aggregate": agg,
               "theirs": THEIRS_RITO}
    out_path = AC.OUTPUTS_DIR / "pls_ritonavir_pilot.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    # readable table
    tab = pd.DataFrame([{k: r[k] for k in
                         ("category", "n_test", "n_pos_test", "precision", "recall", "f1")}
                        for r in results])
    print("\n" + "=" * 72)
    print(tab.round(3).to_string(index=False))
    if agg:
        print(f"\nMACRO  P={agg['macro']['precision']:.3f} R={agg['macro']['recall']:.3f} "
              f"F1={agg['macro']['f1']:.3f}")
        print(f"MICRO  P={agg['micro']['precision']:.3f} R={agg['micro']['recall']:.3f} "
              f"F1={agg['micro']['f1']:.3f}  (over {agg['n_decisions']} decisions)")
        print("\n-- Pujari et al. 2022, Ritonavir test (for context) --")
        for k, v in THEIRS_RITO.items():
            print(f"   {k:34s} macro_f1={v['macro_f1']:.3f}  micro_f1={v['micro_f1']:.3f}")
    print(f"\n-> {out_path}")


if __name__ == "__main__":
    main()
