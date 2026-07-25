"""[6.5] Tier-B boundary specialist judge.

The mass judge ([6]) reads only the title+abstract with a cheap model and is recall-biased,
so it makes CONFIDENT errors exactly at the industrial/transferable claim-scope line — both
false positives (process-bound arms admitted) and false negatives (transferable core cut).
Those errors share one cluster: the look-alike zone the case-mapping stage already mapped.

This stage re-judges only that contested cluster, and it fixes the two root causes:
  - it reads the representative CLAIM (the decisive test is about claim scope, which the
    abstract cannot show), and
  - it reasons by analogy to the case-mapping IN/OUT exemplars (the system's own verified
    examples), with a strong model.
Verdicts are written back as an audit override so the ranked export reflects them.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import pandas as pd

from src.agentic import config as AC
from src.agentic.schemas import BoundaryJudgeOut, CriteriaDocOut, DesignPlanOut
from src.agentic.workspace import Workspace
from src.mas.llm import Usage
from src.mas.runner import KeyPool

_SYSTEM = (
    "You are the Boundary Specialist judge for the domain '{domain}'. You receive ONE patent "
    "that sits in the domain's look-alike zone, its representative CLAIM (not just the abstract), "
    "the decisive exclusion tests, and verified IN / OUT exemplars from earlier case-mapping. "
    "Decide IN or OUT by the CLAIM SCOPE: a patent is OUT when its independent claim is DIRECTED "
    "TO a specific excluded use/process/fixed equipment; it is IN when the claim covers a general, "
    "transferable robot capability (hand/grasp, manipulation, actuator/joint, control/learning, "
    "teleoperation, human-safety) even if an application is mentioned. Reason by analogy to the "
    "closest exemplar. Judge from the claim, not the assignee. Output JSON only."
)


def _row_text(df: pd.DataFrame) -> pd.Series:
    t = df.get("title", pd.Series("", index=df.index)).fillna("").astype(str)
    a = df.get("abstract", pd.Series("", index=df.index)).fillna("").astype(str)
    return (t + " " + a).str.lower()


def _sig_regex(signals):
    toks = [re.escape(s.strip().lower()) for s in signals if s and s.strip()]
    return "|".join(toks) if toks else None


def select_contested(pool_df: pd.DataFrame, latest: dict, plan: DesignPlanOut) -> pd.DataFrame:
    """The contested cluster, selected robustly from the mass judge's own output rather than
    fragile exclusion keywords:
      - FP risk: every currently-INCLUDED patent — a claim read can demote a process-bound
        look-alike the abstract made look general.
      - FN risk: currently-EXCLUDED patents that carry a core-capability signal (or residual
        relevance) — a claim read can rescue a transferable core the sharp exclusions over-cut.
    The abstract could not settle either; the claim can. Capped, FP side prioritized."""
    rid = pool_df["record_id"].astype(str)
    inc = rid.map(lambda r: bool(latest.get(r, {}).get("included", False))).values
    rel = rid.map(lambda r: float(latest.get(r, {}).get("relevance_score", 0) or 0)).values
    # E-excluded look-alikes: an exclusion criterion fired = exactly where the sharp E-tests
    # over-cut transferable core (the false-negative population).
    e_fired = rid.map(lambda r: bool(latest.get(r, {}).get("violated_exclusions"))).values
    core_sig = _sig_regex([s for t in plan.tiers if t.tier in ("T1", "T2")
                           for s in t.expected_signals])
    txt = _row_text(pool_df)
    core = txt.str.contains(core_sig, regex=True).values if core_sig \
        else pd.Series(False, index=pool_df.index).values
    fp_side = pool_df[inc]
    fn_side = pool_df[(~inc) & (e_fired | core | (rel >= 0.35))]
    ordered = pd.concat([fp_side, fn_side]).drop_duplicates("record_id")
    return ordered.head(AC.BOUNDARY_TIER_MAX)


def build_anchor_bank(cats: list[dict]) -> dict:
    """Per-category IN / OUT exemplars from the case-mapping tables (the system's own labels):
    - IN  = T-tier confirmed + E-tier false_positive (rescues)
    - OUT = E-tier confirmed + T-tier false_positive
    Keyed by category name for signal-based retrieval."""
    bank = {}
    for c in cats:
        cat = c.get("category", "")
        is_e = cat.startswith("E_")
        conf = c.get("confirmed", [])
        fps = c.get("false_positive", [])
        ins = (fps if is_e else conf)
        outs = (conf if is_e else fps)
        bank[cat] = {
            "in": [f"[{r['patent_id']}] {r['gist']} — {r.get('basis','')}" for r in ins[:6]],
            "out": [f"[{r['patent_id']}] {r['gist']} — {r.get('basis','')}" for r in outs[:6]],
        }
    return bank


def _tier_signal_map(plan: DesignPlanOut) -> list[tuple[str, str]]:
    out = []
    for t in plan.tiers:
        rx = _sig_regex(t.expected_signals)
        if rx:
            out.append((f"{t.tier}_{t.name}", rx))
    return out


def _anchors_for(text: str, sig_map, bank: dict) -> tuple[list[str], list[str]]:
    ins, outs = [], []
    low = text.lower()
    for cat, rx in sig_map:
        if re.search(rx, low):
            b = bank.get(cat, {})
            ins += b.get("in", [])
            outs += b.get("out", [])
    k = AC.BOUNDARY_ANCHORS_PER_SIDE
    # dedup, keep order
    def uniq(xs):
        seen, o = set(), []
        for x in xs:
            if x not in seen:
                seen.add(x); o.append(x)
        return o
    return uniq(ins)[:k], uniq(outs)[:k]


def _decisive_block(doc: CriteriaDocOut) -> str:
    lines = ["DECISIVE EXCLUSION TESTS:"]
    for e in doc.exclusion_criteria:
        lines.append(f"- {e.id}: {e.statement}")
    return "\n".join(lines)


def _judge_one(row: dict, strong, usage: Usage) -> dict:
    """One claim-scope verdict. run_pool cannot carry Tier-B's per-patent anchors/claim, so
    this stage runs its own thread pool and writes the audit override itself."""
    user = (row["decisive"] + "\n\n"
            + "IN exemplars (verified in-domain):\n" + ("\n".join(row["anchors_in"]) or "(none)")
            + "\n\nOUT exemplars (verified out-of-domain):\n"
            + ("\n".join(row["anchors_out"]) or "(none)")
            + f"\n\nPATENT UNDER REVIEW\nTitle: {row['title']}\n"
            f"Representative claim:\n{row['claim']}")
    out, pt, ct = strong.parse(_SYSTEM.format(domain=row.get("domain", "the domain")),
                               user, BoundaryJudgeOut)
    usage.add(pt, ct)
    inc = bool(out.in_domain)
    return {
        "record_id": row["record_id"], "patent_id": row.get("patent_id", ""),
        "domain": row.get("domain", ""),
        "stance": "in_domain" if inc else "out_of_domain", "included": inc,
        "matched_criteria": ["C1"] if inc else [],
        "violated_exclusions": [] if inc else ["E1"],
        "relevance_score": 0.80 if inc else 0.20, "final_score": 0.80 if inc else 0.20,
        "decision_confidence": float(out.confidence),
        "candidate_type": "positive" if inc else "hard_negative",
        "decision_reason": f"tier_b_claim: {out.decisive_factor}", "judge_pass": 65,
        "tier_b": out.model_dump(),
    }


def tier_b_judge(ws: Workspace, pool_df: pd.DataFrame, plan: DesignPlanOut,
                 cats: list[dict], doc: CriteriaDocOut, latest: dict,
                 strong_pool: KeyPool, usage: Usage, workers: int = 40) -> int:
    """Re-judge the contested cluster from the claim + anchors; append audit overrides."""
    contested = select_contested(pool_df, latest, plan)
    if contested.empty:
        print("  [tier-b] no contested look-alike patents — skipping")
        return 0
    bank = build_anchor_bank(cats)
    sig_map = _tier_signal_map(plan)
    decisive = _decisive_block(doc)
    claim_col = next((c for c in ("rep_claim", "독립청구항[KR,JP,US,CN,EP,IN]", "abstract")
                      if c in pool_df.columns), "abstract")
    rows = []
    for _, r in contested.iterrows():
        text = f"{r.get('title','')} {r.get('abstract','')}"
        a_in, a_out = _anchors_for(text, sig_map, bank)
        rows.append({
            "record_id": str(r["record_id"]), "patent_id": str(r.get("patent_id", "")),
            "domain": ws.slug, "title": str(r.get("title", "")),
            "claim": str(r.get(claim_col, ""))[:AC.BOUNDARY_CLAIM_CHARS],
            "decisive": decisive, "anchors_in": a_in, "anchors_out": a_out,
        })
    print(f"  [tier-b] re-judging {len(rows)} contested patents from the claim "
          f"(model={AC.MODEL_JUDGE_BOUNDARY}, claim col={claim_col})")

    import threading
    lock = threading.Lock()
    results, done, flipped = [], 0, 0

    def work(i, row):
        strong = strong_pool.clients[i % strong_pool.n][1]
        u = Usage()
        try:
            res = _judge_one(row, strong, u)
        except Exception as e:  # noqa: BLE001
            return {"_error": repr(e), "record_id": row["record_id"]}, u
        return res, u

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(work, i, r): i for i, r in enumerate(rows)}
        for fut in as_completed(futs):
            res, u = fut.result()
            with lock:
                usage.merge(u)
                done += 1
                if res.get("_error"):
                    continue
                ws.append_jsonl(ws.judge_audit_jsonl, res)
                results.append(res)
                if bool(res["included"]) != bool(latest.get(res["record_id"], {}).get("included")):
                    flipped += 1
                if done % 200 == 0 or done == len(rows):
                    print(f"    [tier-b] {done}/{len(rows)} re-judged, {flipped} flipped, "
                          f"~${usage.cost_usd():.2f}", flush=True)
    print(f"  [tier-b] done: {len(results)} re-judged, {flipped} verdicts flipped")
    return len(results)
