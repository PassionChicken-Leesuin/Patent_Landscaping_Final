"""[4b-map] Category case-mapping with self-correction.

The system form of the step the human owner and assistant did by hand for the humanoid
gold set: for every tier of the design plan, sample candidate patents (cross-matched
boundary cases first), read title+abstract(+richer columns), and sort them into
confirmed / boundary / false-positive tables. A critic then re-examines the draft and
reclassifies mistakes; each correction is streamed to a revisions log so the UI can show
the mapping fixing itself. Finally the per-category results are aggregated into
representative cases, cross-cutting insights, and a merged false-positive cue list that
feed the criteria draft — none of which alter the downstream CriteriaDocOut contract.
"""
from __future__ import annotations

import re

import pandas as pd

from src.agentic import config as AC
from src.agentic.diagnose import _ai_summary_cols
from src.agentic.schemas import (CaseMapCategoryOut, CaseMapReviseOut, CaseMapSummaryOut,
                                 CaseRow, DesignPlanOut, DesignTier)
from src.agentic.workspace import Workspace
from src.mas.llm import StructuredLLM, Usage

_MAP_BATCH = 25


# ---------------- column resolution + candidate extraction ----------------
def _idcol(df):
    for n in ("patent_id", "record_id", "grant_no", "id"):
        if n in df.columns:
            return n
    return None


def _assigneecol(df):
    for n in ("assignee", "출원인", "applicant"):
        if n in df.columns:
            return n
    return None


def _row_text(df: pd.DataFrame) -> pd.Series:
    parts = [df.get("title", pd.Series("", index=df.index)).fillna("").astype(str),
             df.get("abstract", pd.Series("", index=df.index)).fillna("").astype(str)]
    for c in _ai_summary_cols(df):
        parts.append(df[c].fillna("").astype(str))
    txt = parts[0]
    for p in parts[1:]:
        txt = txt + " " + p
    return txt


def _signal_regex(signals: list[str]) -> str | None:
    toks = [re.escape(s.strip().lower()) for s in signals if s and s.strip()]
    return "|".join(toks) if toks else None


def candidates_for_tier(df: pd.DataFrame, tier: DesignTier,
                        other_tiers: list[DesignTier]) -> pd.DataFrame:
    """Rows matching this tier's signals, cross-matched (also matching an opposite-class
    tier's signals) prioritized — those are the boundary cases worth the human's insight."""
    txt = _row_text(df).str.lower()
    pat = _signal_regex(tier.expected_signals)
    if not pat:
        return df.head(0)
    hit = txt.str.contains(pat, regex=True)
    cand = df[hit]
    if cand.empty:
        return cand

    opp = [t for t in other_tiers if t.tier != tier.tier]      # E vs T split
    opp_pat = _signal_regex([s for t in opp for s in t.expected_signals])
    ctxt = _row_text(cand).str.lower()
    cross = ctxt.str.contains(opp_pat, regex=True) if opp_pat else pd.Series(False, index=cand.index)

    cross_rows = cand[cross].head(AC.CASEMAP_CROSS_PRIORITY)
    rest = cand[~cross].head(AC.CASEMAP_SAMPLE_PER_CATEGORY - len(cross_rows))
    return pd.concat([cross_rows, rest]).head(AC.CASEMAP_SAMPLE_PER_CATEGORY)


# ---------------- mapping (mini, batched) ----------------
_MAP_SYSTEM = """
You are the Case-Mapping agent of a patent-landscaping system. You are given ONE tier of the
selection design (its definition and signals) and a batch of REAL candidate patents from the
pool. For EACH patent decide, from its title/abstract/summary text and the DECISIVE TEST of
"what the claim is actually about" (never the assignee or a listed application):
- confirmed      — clearly belongs to this tier;
- boundary       — genuinely ambiguous; state what is ambiguous and the recommended tier;
- false_positive — matched the tier's keywords but does not belong (state why).
Also emit false_positive_cues: short reusable rules that caught a false match here (e.g.
"'recycling' is not rehabilitation", "'load balancing' is not robot balance").
Judge only the patents given. Copy each patent_id exactly. Output JSON only.
"""


def _batch_block(batch: pd.DataFrame, idcol, acol) -> str:
    txt = _row_text(batch)
    lines = []
    for i, (_, r) in enumerate(batch.iterrows()):
        pid = str(r[idcol]) if idcol else str(i)
        who = str(r[acol]) if acol else ""
        lines.append(f"[{pid}] ({who}) {txt.loc[r.name][:AC.CASEMAP_TEXT_CHARS]}")
    return "\n".join(lines)


def _map_category(llm_map: StructuredLLM, tier: DesignTier, cand: pd.DataFrame,
                  usage: Usage) -> CaseMapCategoryOut:
    idcol, acol = _idcol(cand), _assigneecol(cand)
    agg = CaseMapCategoryOut(category=f"{tier.tier}_{tier.name}", confirmed=[],
                             boundary=[], false_positive=[], false_positive_cues=[])
    head = (f"TIER {tier.tier} — {tier.name}\nDEFINITION: {tier.definition}\n"
            f"SIGNALS: {', '.join(tier.expected_signals)}\n\nCANDIDATE PATENTS:\n")
    for s in range(0, len(cand), _MAP_BATCH):
        batch = cand.iloc[s:s + _MAP_BATCH]
        out, pt, ct = llm_map.parse(_MAP_SYSTEM, head + _batch_block(batch, idcol, acol),
                                    CaseMapCategoryOut)
        usage.add(pt, ct)
        agg.confirmed += out.confirmed
        agg.boundary += out.boundary
        agg.false_positive += out.false_positive
        agg.false_positive_cues += out.false_positive_cues
    # dedup cues
    seen, cues = set(), []
    for c in agg.false_positive_cues:
        k = c.strip().lower()
        if k and k not in seen:
            seen.add(k); cues.append(c)
    agg.false_positive_cues = cues
    return agg


# ---------------- self-correction loop ----------------
_REVISE_SYSTEM = """
You are the Case-Mapping Critic. You are given a tier definition and its current draft mapping
(confirmed and false_positive rows). Re-examine them and return ONLY the rows whose verdict or
tier is wrong — the classic mistakes: a 'confirmed' that is actually a false_positive or belongs
to a different tier, or a 'false_positive' that is really a rescue (belongs after all). For each
changed row restate patent_id, the corrected verdict/tier, and the basis. If nothing is wrong,
return changed=[] and settled=true. Do not restate rows that are already correct. Output JSON only.
"""


def _revise_category(llm: StructuredLLM, ws: Workspace, tier: DesignTier,
                     cat: CaseMapCategoryOut, usage: Usage) -> CaseMapCategoryOut:
    for _ in range(AC.CASEMAP_REVISE_ROUNDS):
        rows = cat.confirmed + cat.false_positive
        listing = "\n".join(f"[{r.patent_id}] {r.verdict}/{r.tier or '?'} — {r.gist} :: {r.basis}"
                            for r in rows[:120])
        user = (f"TIER {tier.tier} — {tier.name}\nDEFINITION: {tier.definition}\n\n"
                f"CURRENT DRAFT (confirmed + false_positive):\n{listing}\n")
        out, pt, ct = llm.parse(_REVISE_SYSTEM, user, CaseMapReviseOut)
        usage.add(pt, ct)
        if out.changed:
            ws.append_jsonl(ws.casemap_revisions_jsonl(cat.category),
                            {"rationale": out.rationale,
                             "changed": [c.model_dump() for c in out.changed]})
            _apply_changes(cat, out.changed)
        if out.settled or not out.changed:
            break
    return cat


def _apply_changes(cat: CaseMapCategoryOut, changed: list[CaseRow]) -> None:
    idx = {c.patent_id: c for c in changed}
    for bucket in ("confirmed", "boundary", "false_positive"):
        setattr(cat, bucket, [r for r in getattr(cat, bucket) if r.patent_id not in idx])
    for c in changed:
        {"confirmed": cat.confirmed, "boundary": cat.boundary,
         "false_positive": cat.false_positive}[c.verdict].append(c)


# ---------------- orchestration ----------------
def run_casemap(ws: Workspace, llm: StructuredLLM, llm_map: StructuredLLM,
                plan: DesignPlanOut, pool_df: pd.DataFrame, usage: Usage,
                *, force: bool = False) -> list[CaseMapCategoryOut]:
    ws.casemap_dir.mkdir(parents=True, exist_ok=True)
    results: list[CaseMapCategoryOut] = []
    for tier in plan.tiers:
        cat_name = f"{tier.tier}_{tier.name}"
        path = ws.casemap_json(cat_name)
        if path.exists() and not force:
            results.append(CaseMapCategoryOut(**Workspace.read_json(path)))
            continue
        cand = candidates_for_tier(pool_df, tier, plan.tiers)
        if cand.empty:
            cat = CaseMapCategoryOut(category=cat_name, confirmed=[], boundary=[],
                                     false_positive=[], false_positive_cues=[])
        else:
            cat = _map_category(llm_map, tier, cand, usage)
            cat = _revise_category(llm, ws, tier, cat, usage)
        ws.write_json(path, cat.model_dump())
        print(f"  [casemap] {cat_name}: {len(cat.confirmed)}C / "
              f"{len(cat.boundary)}B / {len(cat.false_positive)}FP")
        results.append(cat)
    return results


_SUMMARY_SYSTEM = """
You are the Case-Mapping Synthesizer. Given the per-category mapping results, produce:
- representative_confirmed — a few of the strongest confirmed patents across categories;
- insights — the cross-cutting lessons a domain expert would draw (e.g. "a category cannot be
  excluded wholesale because X of it is rescues", "assignee A must be split by product line",
  "the industrial-lookalike cluster splits by claim, not by company"), each with the patent_ids
  that evidence it;
- false_positive_cues — the merged, deduped reusable exclusion cues.
Output JSON only.
"""


def summarize_casemap(ws: Workspace, llm: StructuredLLM, cats: list[CaseMapCategoryOut],
                      usage: Usage, *, force: bool = False) -> CaseMapSummaryOut:
    if ws.casemap_summary_json.exists() and not force:
        return CaseMapSummaryOut(**Workspace.read_json(ws.casemap_summary_json))
    blocks = []
    for c in cats:
        ex = "; ".join(f"[{r.patent_id}] {r.gist}" for r in c.boundary[:4])
        cf = "; ".join(f"[{r.patent_id}] {r.gist}" for r in c.confirmed[:3])
        blocks.append(f"### {c.category}: {len(c.confirmed)}C/{len(c.boundary)}B/"
                      f"{len(c.false_positive)}FP\n confirmed: {cf}\n boundary: {ex}\n"
                      f" cues: {', '.join(c.false_positive_cues[:6])}")
    out, pt, ct = llm.parse(_SUMMARY_SYSTEM, "\n\n".join(blocks), CaseMapSummaryOut)
    usage.add(pt, ct)
    ws.write_json(ws.casemap_summary_json, out.model_dump())
    ws.write_json(ws.false_positive_cues_json, {"cues": out.false_positive_cues})
    return out
