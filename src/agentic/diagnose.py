"""[3.5] Alignment diagnosis + sufficiency gate.

Mirrors the human step that opened the humanoid A2 gold build: profile the judge
pool quantitatively, interpret it against the owner/reference material, and decide
whether the supplied material is enough or web research is still needed.

Split of responsibility (same philosophy as the rest of the system — code counts,
the LLM reasons):
  - profile_pool():        pure pandas, no LLM, degrades gracefully per missing column
  - diagnose_alignment():  one LLM call for the (1) problem / (2) reference / (3)
                           alignment reading + the direct-domain terms & key players,
                           which code then COUNTS back into the profile (auditable).
"""
from __future__ import annotations

import re

import pandas as pd

from src.agentic import config as AC
from src.agentic.localdocs import owner_docs_block
from src.agentic.research import notes_summary_by_type
from src.agentic.schemas import (AlignmentDiagnosisOut, CorpusDigestOut, NameCount,
                                 PlayerCoverage, PoolProfile, QueryScopeOut)
from src.agentic.workspace import Workspace
from src.mas.llm import StructuredLLM, Usage

from pydantic import BaseModel


class SufficiencyOut(BaseModel):
    sufficiency: str            # "sufficient" | "need_web"
    gaps: list[str]

_LEGAL = (r"\b(?:KABUSHIKI KAISHA|CO\.?,? ?LTD|CORPORATION|CORP|INCORPORATED|INC|LLC|LTD"
          r"|GMBH|AKTIENGESELLSCHAFT|AG|AB|SA|SE|BV|NV|KK|COMPANY|LIMITED|HOLDINGS?)\b")


def _col(df: pd.DataFrame, *names: str) -> str | None:
    for n in names:
        if n in df.columns:
            return n
    return None


def _ai_summary_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns
            if ("요약[" in str(c)) or str(c).lower().startswith("ai 요약")
            or str(c).lower().startswith("ai_summary")]


def norm_assignee(raw: str) -> str:
    s = str(raw).upper().strip()
    s = re.split(r"\s*\|\s*", s)[0]                       # first of multi-assignee
    m = re.match(rf"^({_LEGAL}),\s*(.+)$", s)             # de-invert "CORPORATION, FANUC"
    if m:
        s = f"{m.group(2)} {m.group(1)}"
    s = re.sub(r"[.,]", "", s)
    s = re.sub(_LEGAL, "", s)
    return re.sub(r"\s+", " ", s).strip()


def _pool_text(df: pd.DataFrame) -> pd.Series:
    """Domain-general text field: title + abstract (+ any AI-summary columns present)."""
    parts = [df.get("title", pd.Series("", index=df.index)).fillna(""),
             df.get("abstract", pd.Series("", index=df.index)).fillna("")]
    for c in _ai_summary_cols(df):
        parts.append(df[c].fillna(""))
    txt = parts[0].astype(str)
    for p in parts[1:]:
        txt = txt + " " + p.astype(str)
    return txt.str.lower()


def profile_pool(df: pd.DataFrame) -> PoolProfile:
    """Structural metrics only (no domain terms yet — those need the diagnosis LLM)."""
    n = len(df)
    fam = _col(df, "family_id", "WIPS패밀리 ID", "wips_family_id")
    if fam:
        n_ded = int(df[fam].nunique())
        dup = n - n_ded
    else:
        n_ded, dup = n, 0

    acol = _col(df, "assignee", "출원인", "applicant")
    top: list[NameCount] = []
    top10_share = 0.0
    if acol:
        norm = df[acol].map(norm_assignee)
        vc = norm.value_counts()
        top = [NameCount(name=str(k), count=int(v))
               for k, v in vc.head(AC.DIAGNOSE_TOP_ASSIGNEES).items()]
        top10_share = float(vc.head(10).sum() / n) if n else 0.0

    ncol = _col(df, "assignee_country", "출원인_국적1", "출원인 국적")
    nat: list[NameCount] = []
    if ncol:
        c = df[ncol].astype(str).str.split(r"\s*\|\s*").str[0].str.strip().replace("", "N/A")
        nat = [NameCount(name=str(k), count=int(v)) for k, v in c.value_counts().head(12).items()]

    ccol = _col(df, "cpc_main", "Current CPC Main", "cpc_main_orig")
    cpc: list[NameCount] = []
    if ccol:
        sub = df[ccol].astype(str).str.replace(" ", "").str.extract(r"([A-H]\d{2}[A-Z])")[0]
        cpc = [NameCount(name=str(k), count=int(v)) for k, v in sub.value_counts().head(10).items()]

    ai_cols = _ai_summary_cols(df)
    if ai_cols:
        filled = df[ai_cols].notna().any(axis=1) & \
                 df[ai_cols].astype(str).apply(lambda r: any(x.strip() for x in r), axis=1)
        ai_fill = float(filled.mean())
    else:
        ai_fill = 0.0

    return PoolProfile(n_total=n, n_family_dedup=n_ded, family_dup_rows=dup,
                       ai_summary_fill_rate=round(ai_fill, 3), top_assignees=top,
                       top10_assignee_share=round(top10_share, 3),
                       nationality_dist=nat, cpc_main_dist=cpc)


def _fill_domain_counts(prof: PoolProfile, df: pd.DataFrame,
                        terms: list[str], players: list[str]) -> None:
    """After the LLM names direct-domain terms & key players, COUNT them (auditable)."""
    txt = _pool_text(df)
    prof.direct_domain_terms = terms
    if terms:
        pat = "|".join(re.escape(t.lower()) for t in terms if t.strip())
        hit = txt.str.contains(pat, regex=True) if pat else pd.Series(False, index=df.index)
        prof.direct_domain_mention = int(hit.sum())
        prof.direct_domain_pct = round(float(hit.mean()), 4)

    acol = _col(df, "assignee", "출원인", "applicant")
    if acol and players:
        norm = df[acol].map(norm_assignee)
        cov = []
        for p in players:
            key = norm_assignee(p)
            if not key:
                continue
            n_in = int(norm.str.contains(re.escape(key), regex=True).sum())
            cov.append(PlayerCoverage(name=p, in_pool=n_in))
        prof.reference_player_coverage = cov


_SUFFICIENCY_SYSTEM = """
You are the Material-Sufficiency gate of a patent-landscaping system. BEFORE any web research,
decide whether the supplied material — the domain query and the owner's own reference documents
— already pins the domain well enough to define its technology axes and scope boundaries.
Answer "sufficient" only when the owner material is substantive and clearly scopes the domain;
answer "need_web" when there is no/'(none)' owner material or it is thin, vague, or narrow, in
which case list the specific gaps to search the web for. Output JSON only.
"""


def sufficiency_precheck(llm: StructuredLLM, scope: QueryScopeOut, ws: Workspace,
                         usage: Usage) -> SufficiencyOut:
    """Owner-doc-only gate (no corpus): decides whether web research is needed."""
    owner = owner_docs_block(ws)
    user = (f"DOMAIN: {scope.canonical_name_en}\n"
            f"TASK HYPOTHESES:\n" + "\n".join(f"- {h}" for h in scope.initial_task_hypotheses) +
            f"\n\nOWNER REFERENCE MATERIAL:\n{owner}\n")
    out, pt, ct = llm.parse(_SUFFICIENCY_SYSTEM, user, SufficiencyOut)
    usage.add(pt, ct)
    return out


_SYSTEM = """
You are the Alignment-Diagnosis agent of a patent-landscaping system. Before any criteria
are written, you review whether the supplied material (the domain query, the owner's domain
description, the owner's core reference material, and the actual patent pool) is coherent and
sufficient, exactly as a human domain expert would first read the inputs.

Produce:
1. problem_understanding — what selection task the owner actually wants (full sentences).
2. reference_understanding — what the core reference material establishes about the domain's
   value chain / key technologies / players.
3. direct_domain_terms — the literal words whose presence in a patent's title/abstract means
   it is DIRECTLY the domain (e.g. the domain's proper name and near-synonyms). Code will count
   these across the pool, so give discriminating terms, not generic robotics words.
4. reference_key_players — companies/organizations the reference material names as important
   (verbatim names). Code will count how many pool patents each authored.
5. alignment_notes — the alignment diagnosis: where the pool and the reference agree or diverge,
   and which clusters will be the hard boundary calls (e.g. a large industrial-lookalike
   assignee cluster that must be judged per-patent, not by company).
6. sufficiency — "sufficient" if the query + owner material already pin the domain's axes and
   boundaries; "need_web" if the domain definition is thin/ambiguous and external references
   are required.
7. gaps — if need_web, the specific things to search for (empty if sufficient).

Output JSON only.
"""


def diagnose_alignment(ws: Workspace, llm: StructuredLLM, scope: QueryScopeOut,
                       digest: CorpusDigestOut, pool_df: pd.DataFrame, usage: Usage,
                       *, force: bool = False) -> AlignmentDiagnosisOut:
    if ws.diagnosis_json.exists() and not force:
        return AlignmentDiagnosisOut(**Workspace.read_json(ws.diagnosis_json))

    prof = profile_pool(pool_df)

    titles = pool_df.get("title", pd.Series([], dtype=str)).dropna().astype(str)
    sample = "\n".join(f"- {t[:140]}" for t in titles.head(AC.DIAGNOSE_TITLE_SAMPLE))
    prof_lines = [
        f"total={prof.n_total}, family_dedup={prof.n_family_dedup}, family_dup_rows={prof.family_dup_rows}",
        f"ai_summary_fill_rate={prof.ai_summary_fill_rate}",
        f"top10_assignee_share={prof.top10_assignee_share}",
        "top_assignees: " + ", ".join(f"{a.name}({a.count})" for a in prof.top_assignees[:15]),
        "nationality: " + ", ".join(f"{a.name}({a.count})" for a in prof.nationality_dist),
        "cpc_main: " + ", ".join(f"{a.name}({a.count})" for a in prof.cpc_main_dist),
    ]
    user = (
        f"DOMAIN (canonical): {scope.canonical_name_en}\n"
        f"TASK HYPOTHESES:\n" + "\n".join(f"- {h}" for h in scope.initial_task_hypotheses) + "\n\n"
        f"OWNER / REFERENCE MATERIAL:\n{owner_docs_block(ws)}\n\n"
        f"WEB RESEARCH NOTES (may be empty this early):\n{notes_summary_by_type(ws)}\n\n"
        f"CORPUS DIGEST (what the pool actually contains):\n"
        f"- clusters: {', '.join(digest.main_clusters[:12])}\n"
        f"- vocabulary: {', '.join(digest.vocabulary_profile[:15])}\n"
        f"- boundary cases: {', '.join(digest.suspected_boundary_cases[:8])}\n\n"
        f"POOL PROFILE (code-computed):\n" + "\n".join(prof_lines) + "\n\n"
        f"POOL TITLE SAMPLE:\n{sample}\n"
    )
    out, pt, ct = llm.parse(_SYSTEM, user, AlignmentDiagnosisOut)
    usage.add(pt, ct)

    _fill_domain_counts(prof, pool_df, out.direct_domain_terms, out.reference_key_players)
    ws.write_json(ws.pool_profile_json, prof.model_dump())
    ws.write_json(ws.diagnosis_json, out.model_dump())
    return out
