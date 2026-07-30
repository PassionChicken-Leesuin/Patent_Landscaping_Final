"""Boundary probing: MEASURE how many pool patents a scope boundary actually flips.

For each candidate ScopeQuestion the criteria author raised, judge a random pool
sample under BOTH its broad_rule and its narrow_rule (one cheap call per patent
covers every boundary at once). A boundary's real impact = the number of sample
patents whose in/out verdict differs between the two rules. Boundaries below
BOUNDARY_MIN_FLIP_RATE are dropped (the author over-worried); the rest are ranked
by measured flip count and their why_it_matters is rewritten with the real number.

Reuses the existing KeyPool / run_pool parallel engine via process_fn injection.
"""
from __future__ import annotations
import json

import pandas as pd

from src.mas.llm import StructuredLLM, Usage
from src.mas.runner import KeyPool, run_pool
from src.agentic import config as AC
from src.agentic.schemas import BoundaryProbeOut, ScopeQuestion
from src.agentic.workspace import Workspace

_PROBE_SYSTEM = (
    "You are a patent-scope probe. For the domain '{domain}', you are given one patent "
    "(title+abstract) and a list of SCOPE BOUNDARIES. Each boundary has a BROAD inclusion "
    "rule and a NARROW inclusion rule. For EACH boundary, decide, from the patent text "
    "alone, whether the patent would be IN the domain under the broad rule and whether it "
    "would be IN under the narrow rule. Most patents are unaffected by a given boundary "
    "(broad==narrow); report the difference only when the two rules genuinely disagree for "
    "THIS patent. Output JSON only."
)


def _probe_patent(state: dict, fast: StructuredLLM, strong: StructuredLLM,
                  usage: Usage) -> dict:
    boundaries = state["rubric"]["boundaries"]
    blocks = [f"[{b['id']}] BROAD: {b['broad_rule']}  |  NARROW: {b['narrow_rule']}"
              for b in boundaries]
    user = ("SCOPE BOUNDARIES:\n" + "\n".join(blocks) +
            f"\n\nPATENT\nTitle: {state['title']}\nAbstract: {state['abstract']}")
    out, pt, ct = fast.parse(_PROBE_SYSTEM.format(domain=state.get("domain", "the domain")),
                             user, BoundaryProbeOut)
    usage.add(pt, ct)
    return {"record_id": state["record_id"],
            "verdicts": [v.model_dump() for v in out.verdicts]}


_PK = ("record_id", "verdicts")


def probe_boundaries(questions: list[ScopeQuestion], pool_df: pd.DataFrame,
                     pool: KeyPool, domain: str, audit_path,
                     workers: int = 40, min_flip_rate: float | None = None,
                     max_questions: int | None = None
                     ) -> list[tuple[ScopeQuestion, int, int]]:
    """Return [(question, flip_count, sample_n), ...] sorted by flip_count desc,
    filtered to boundaries whose flip rate >= BOUNDARY_MIN_FLIP_RATE.

    The thresholds are overridable because they exist to SELECT which candidate
    boundaries deserve the owner's attention. When the boundary is already known to
    need an answer (the validator is blocking on it), pass min_flip_rate=0 to measure
    impact without dropping the question."""
    if not questions:
        return []
    n = min(AC.BOUNDARY_PROBE_SAMPLE, len(pool_df))
    sample = pool_df.sample(n=n, random_state=7) if len(pool_df) > n else pool_df
    boundaries = [{"id": q.id, "broad_rule": q.broad_rule, "narrow_rule": q.narrow_rule}
                  for q in questions]
    rubric = {"boundaries": boundaries}
    rows = [{"record_id": str(r["record_id"]), "patent_id": str(r.get("patent_id", "")),
             "domain": domain, "title": str(r.get("title", "")),
             "abstract": str(r.get("abstract", ""))}
            for _, r in sample.iterrows()]

    out = run_pool(rows, rubric, pool, workers=workers, audit_path=audit_path,
                   process_fn=_probe_patent, audit_keys=_PK, slim_keys=_PK,
                   log_every=10_000)
    flips = {q.id: 0 for q in questions}
    for res in out["results"]:
        for v in res.get("verdicts", []):
            if v.get("boundary_id") in flips and v.get("broad") != v.get("narrow"):
                flips[v["boundary_id"]] += 1

    rate = AC.BOUNDARY_MIN_FLIP_RATE if min_flip_rate is None else min_flip_rate
    cap = AC.BOUNDARY_MAX_QUESTIONS if max_questions is None else max_questions
    ranked = []
    for q in questions:
        f = flips.get(q.id, 0)
        if f >= rate * n:
            ranked.append((q, f, n))
    ranked.sort(key=lambda t: t[1], reverse=True)
    return ranked[:cap]


def measured_questions(ranked: list[tuple[ScopeQuestion, int, int]]) -> list[ScopeQuestion]:
    """Rewrite why_it_matters with the measured flip count (author guess -> fact)."""
    out = []
    for q, flip, n in ranked:
        q2 = q.model_copy()
        pct = round(100 * flip / n)
        q2.why_it_matters = (f"측정: 풀 표본 {n}건 중 {flip}건(~{pct}%)의 판정이 "
                             f"넓게/좁게에 따라 갈립니다. " + q.why_it_matters)
        out.append(q2)
    return out
