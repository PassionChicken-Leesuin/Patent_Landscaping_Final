"""Orchestration of stages [1]-[5]: query -> research -> corpus -> criteria (validated).

Every stage caches its artifact under DataSet/agentic/<run-slug>/ and is skipped
when the SAME run resumes (including after a PendingHumanInput stop in batch
HITL mode). HITL memory is strictly workspace-local; no prior run's user answers
are imported.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from src import config as C
from src.mas.llm import OpenAIStructuredLLM, StructuredLLM, Usage, load_openai_keys
from src.agentic import config as AC
from src.agentic import research as R
from src.agentic.axes import synthesize_axes
from src.agentic.casemap import run_casemap, summarize_casemap
from src.agentic.corpus import read_corpus
from src.agentic.criteria import load_final
from src.agentic.decisions import run_decisions
from src.agentic.designplan import build_design_plan
from src.agentic.diagnose import diagnose_alignment, sufficiency_precheck
from src.agentic.hitl import HITL, HITLMode
from src.agentic.mockllm import MockAgentLLM
from src.agentic.schemas import CriteriaDocOut, QueryScopeOut
from src.agentic.scoping import scope_query
from src.agentic.search import make_search_client
from src.agentic.validator import criteria_loop
from src.agentic.workspace import Workspace, slugify

# gpt-4o pricing (USD / 1M tokens) for the research-stage cost print
_RESEARCH_IN_RATE, _RESEARCH_OUT_RATE = 2.50, 10.00


class RetryingLLM(StructuredLLM):
    """Backoff-retry wrapper for the sequential research-stage calls (the mass judge
    already retries inside run_pool; these single-threaded calls need their own)."""

    def __init__(self, inner: StructuredLLM, max_attempts: int = 5):
        self.inner = inner
        self.max_attempts = max_attempts

    def parse(self, system, user, schema):
        import time
        from src.mas.runner import _backoff, _is_retryable
        last = None
        for attempt in range(self.max_attempts):
            try:
                return self.inner.parse(system, user, schema)
            except Exception as e:  # noqa: BLE001
                last = e
                # output hit the completion-length cap: retry once asking for concision
                if type(e).__name__ == "LengthFinishReasonError" and attempt < self.max_attempts - 1:
                    system = (system + "\n\nIMPORTANT: keep the output COMPACT — merge minor "
                              "items, cap every list at its most decision-relevant entries. "
                              "An over-long answer will be rejected.")
                    continue
                if _is_retryable(e) and attempt < self.max_attempts - 1:
                    time.sleep(_backoff(attempt))
                    continue
                raise
        raise last


def _judge_pool(mock: bool = False):
    """A KeyPool on the cheap judge model — reused for boundary probing (mass calls)."""
    from src.mas.runner import KeyPool
    if mock:
        from src.agentic.judge import mock_pool
        return mock_pool(3)
    keys = load_openai_keys(str(C.ROOT / ".env"))
    return KeyPool(keys, AC.MODEL_JUDGE_FAST, AC.MODEL_JUDGE_STRONG, AC.LLM_TEMPERATURE)


def _corpus_map_llm(mock: bool, llm: StructuredLLM) -> StructuredLLM:
    """The cheap mini model used for mass mapping (corpus reading, case-mapping)."""
    if mock:
        return llm
    keys = load_openai_keys(str(C.ROOT / ".env"))
    return RetryingLLM(OpenAIStructuredLLM(
        api_key=keys[min(1, len(keys) - 1)], model=AC.MODEL_CORPUS_MAP,
        temperature=AC.LLM_TEMPERATURE))


def _front_matter(ws: Workspace, plan, cm_summary, cats, answered: list[dict]) -> str:
    """Assemble the case-mapping product as authoritative context for the criteria draft."""
    lines = ["=== TIERED DESIGN PLAN ==="]
    for t in plan.tiers:
        lines.append(f"- [{t.tier}] {t.name} (axes {', '.join(t.axis_ids)}): {t.definition}")
    # Enforced exclusion contract: each E-tier MUST become an exclusion criterion.
    e_tiers = [t for t in plan.tiers if t.tier == "E"]
    if e_tiers:
        lines.append("\n=== REQUIRED EXCLUSION FAMILIES (create ONE exclusion criterion per "
                     "family; state the DECISIVE CLAIM-SCOPE test — exclude when the claim is "
                     "bound to this use/process/equipment, keep the transferable capability in "
                     "scope) ===")
        fp_by_cat = {c.category: c.false_positive for c in (cats or [])}
        for t in e_tiers:
            lines.append(f"- {t.name}: {t.definition}")
            fps = fp_by_cat.get(f"{t.tier}_{t.name}", [])
            if fps:
                lines.append("    예 (제외): " + "; ".join(
                    f"[{r.patent_id}] {r.gist}" for r in fps[:4]))
    lines.append("\n=== CROSS-CUTTING INSIGHTS ===")
    for i in cm_summary.insights:
        lines.append(f"- {i.title}: {i.detail}")
    lines.append("\n=== REUSABLE FALSE-POSITIVE CUES (encode as observable-signal cautions "
                 "on the matching exclusion criteria) ===")
    lines.append("; ".join(cm_summary.false_positive_cues) or "(none)")
    human = [a for a in answered
             if a.get("answered_by") in ("human", "human_batch", "human_prior")]
    if human:
        lines.append("\n=== OWNER-ANSWERED SCOPE DECISIONS (record verbatim) ===")
        for a in human:
            lines.append(f"Q: {a['question']}\nA: {a['answer']}")
    return "\n".join(lines)


def research_llm(mock: bool = False) -> StructuredLLM:
    if mock:
        return MockAgentLLM()
    keys = load_openai_keys(str(C.ROOT / ".env"))
    if not keys:
        raise ValueError("no OpenAI keys in .env (OPENAI_API_KEY_1..N)")
    return RetryingLLM(OpenAIStructuredLLM(api_key=keys[0], model=AC.MODEL_RESEARCH,
                                           temperature=AC.LLM_TEMPERATURE))


def find_workspace_for_query(query: str, mock: bool = False,
                             variant: str = "") -> Workspace | None:
    """Reuse an existing workspace whose query.json matches this exact query.
    Mock/live and experiment variants never mix (distinct slugs)."""
    if not AC.AGENTIC_DIR.exists():
        return None
    for qj in AC.AGENTIC_DIR.glob("*/query.json"):
        try:
            data = Workspace.read_json(qj)
        except Exception:
            continue
        if (data.get("query_original") == query and bool(data.get("mock")) == mock
                and str(data.get("variant", "")) == variant):
            return Workspace(qj.parent.name)
    return None


def build_criteria(query: str, pool_df: pd.DataFrame, *, mock: bool = False,
                   force: bool = False, hitl_mode: HITLMode = "interactive",
                   no_research: bool = False, no_corpus: bool = False,
                   variant: str = "", local_docs: list[str] | None = None,
                   local_docs_allow_flagged: bool = False,
                   ) -> tuple[Workspace, QueryScopeOut, CriteriaDocOut]:
    """Stages [1]-[5]. pool_df must have title/abstract columns (the judge pool —
    its real text is read during the corpus stage, per the system design).
    no_research / no_corpus are ABLATION switches (experiments only).
    local_docs: user-supplied reference files ingested into the research notes."""
    llm = research_llm(mock)
    usage = Usage()

    # [1] scoping (workspace is keyed by the canonical name -> resume by query match)
    ws = find_workspace_for_query(query, mock, variant)
    if ws is not None and not force:
        scope = QueryScopeOut(**Workspace.read_json(ws.query_json)["scope"])
        print(f"[1] scoping: reusing workspace '{ws.slug}'")
    else:
        # Anchor scoping on the owner scope document so the canonical name/scope is NOT
        # broadened or drifted by query-only stochasticity (root cause of the GOCS regression:
        # "satellite GNSS…" silently became "satellite…"). Owner doc is authoritative for scope.
        owner_context = ""
        if local_docs:
            parts = []
            for p in local_docs:
                try:
                    parts.append(Path(p).read_text(encoding="utf-8", errors="replace"))
                except Exception:
                    pass
            owner_context = "\n\n".join(parts)
        scope = scope_query(llm, query, usage, owner_context=owner_context)
        slug = ("mock-" if mock else "") + slugify(scope.canonical_name_en) \
               + (f"-{variant}" if variant else "")
        ws = Workspace(slug).ensure()
        ws.write_json(ws.query_json, {"query_original": query, "mock": mock,
                                      "variant": variant, "scope": scope.model_dump()})
        print(f"[1] scoping: '{query}' -> {scope.canonical_name_en} (slug={ws.slug})")
    ws.ensure()

    if force:
        # A forced rebuild must not leave a stale approved document visible if
        # the new axis/validator contract later blocks the run.
        ws.criteria_final_json.unlink(missing_ok=True)
        ws.criteria_final_md.unlink(missing_ok=True)
        ws.criteria_blocked_json.unlink(missing_ok=True)

    # criteria already approved? -> everything below is done
    if (ws.criteria_final_json.exists() and not ws.criteria_blocked_json.exists()
            and not force):
        cached_doc = load_final(ws)
        provenance_ok = (bool(cached_doc.technology_axes)
                         and all(a.source_refs for a in cached_doc.technology_axes)
                         and all(c.source_refs for c in [*cached_doc.domain_criteria,
                                                        *cached_doc.exclusion_criteria]))
        if provenance_ok:
            print("[2-5] compliant criteria_final.json exists — skipping")
            return ws, scope, cached_doc
        print("[2-5] legacy criteria_final lacks axis/provenance contract — rebuilding")
        ws.criteria_final_json.unlink(missing_ok=True)
        ws.criteria_final_md.unlink(missing_ok=True)

    client = make_search_client(mock)

    # [2b] owner-supplied local reference documents FIRST (idempotent per chunk;
    # fail-loud on leak-scan hits — an owner document is never silently dropped).
    # Ingesting before research lets the sufficiency gate read the owner material.
    if local_docs:
        from src.agentic.localdocs import ingest_local_docs
        print(f"[2b] local docs: ingesting {len(local_docs)} file(s)")
        ingest_local_docs(ws, llm, local_docs, scope.canonical_name_en, usage,
                          allow_flagged=local_docs_allow_flagged)

    # [2-gate] sufficiency: is the supplied material enough, or is web research needed?
    web_done = ws.searches_jsonl.exists()
    if no_research:
        print("[2] research: SKIPPED (ablation — criteria from LLM internal knowledge)")
    elif web_done and not force:
        print(f"[2] research: reusing cached web notes")
    else:
        suff = sufficiency_precheck(llm, scope, ws, usage)
        need_web = suff.sufficiency != "sufficient" or not local_docs
        if need_web:
            reason = "; ".join(suff.gaps[:4]) or "owner material thin/absent"
            print(f"[2] research: material insufficient -> web collection ({reason})")
            R.research(ws, llm, client, scope, usage)
        else:
            print("[2] research: SKIPPED — owner material judged sufficient")

    # [3] corpus reading (the actual pool text)
    if no_corpus:
        print("[3] corpus: SKIPPED (ablation)")
        from src.agentic.schemas import CorpusDigestOut
        digest = CorpusDigestOut(main_clusters=[], vocabulary_profile=[],
                                 representative_cases=[], suspected_boundary_cases=[],
                                 mismatch_with_web_evidence=[])
    else:
        print(f"[3] corpus: reading the judge pool ({len(pool_df)} patents)")
        if mock:
            llm_map = llm
        else:
            keys = load_openai_keys(str(C.ROOT / ".env"))
            llm_map = RetryingLLM(OpenAIStructuredLLM(
                api_key=keys[min(1, len(keys) - 1)], model=AC.MODEL_CORPUS_MAP,
                temperature=AC.LLM_TEMPERATURE))
        digest = read_corpus(ws, llm, pool_df, scope.canonical_name_en,
                             R.notes_summary_by_type(ws), usage, force=force,
                             llm_map=llm_map)

    # [3.5] alignment diagnosis: quantitative pool profile + LLM reading of problem /
    # reference / alignment, with the direct-domain terms & key players code counts back.
    print("[3.5] alignment diagnosis (pool profile + sufficiency)")
    diagnosis = diagnose_alignment(ws, llm, scope, digest, pool_df, usage, force=force)
    prof = Workspace.read_json(ws.pool_profile_json)
    print(f"  [diagnose] direct-domain {prof['direct_domain_mention']} "
          f"({prof['direct_domain_pct']:.1%}) · sufficiency={diagnosis.sufficiency}")

    # [4a] quality-aware axis anchoring from query/owner doc + research + pool
    print("[4a] technology-axis synthesis + provenance anchoring")
    axes = synthesize_axes(ws, llm, scope, digest, usage, force=force)
    print(f"  [axes] {len(axes.technology_axes)} axes -> {ws.axis_synthesis_md}")

    hitl = HITL(ws, mode=hitl_mode, stage="criteria")
    probe_pool = _judge_pool(mock)   # cheap model, reused by the boundary probe + casemap

    # [4a+] tiered design plan (axes -> T1/T2/E categories, domain-general)
    print("[4a+] design plan (axes -> tiers)")
    from src.agentic.schemas import PoolProfile
    plan = build_design_plan(ws, llm, axes, PoolProfile(**prof), diagnosis, usage, force=force)
    print(f"  [design] {len(plan.tiers)} tiers")

    # [4b-map] category case-mapping with self-correction, then aggregate
    print("[4b-map] category case-mapping (confirmed/boundary/false-positive + self-correction)")
    llm_map = _corpus_map_llm(mock, llm)
    cats = run_casemap(ws, llm, llm_map, plan, pool_df, usage, force=force)
    cm_summary = summarize_casemap(ws, llm, cats, usage, force=force)
    print(f"  [casemap] {sum(len(c.confirmed) for c in cats)} confirmed, "
          f"{sum(len(c.boundary) for c in cats)} boundary, {len(cm_summary.insights)} insights")

    # [4c] decision cards: frame the hard scope calls for the owner (measured impact)
    print("[4c] scope decisions (measured impact -> HITL)")
    answered = run_decisions(ws, llm, cats, cm_summary, pool_df, probe_pool,
                             scope.canonical_name_en, hitl, usage)

    # [4b-5] criteria + validator feedback loop — now seeded by the front-half product.
    # The design plan's E-tiers become an ENFORCED exclusion-coverage contract so the
    # look-alikes case-mapping found are actually encoded as exclusion criteria (else
    # they leak into positives — the precision failure mode, general to every domain).
    print("[4b-5] criteria drafting + validator loop")
    front_matter = _front_matter(ws, plan, cm_summary, cats, answered)
    excl_fams = [{"name": t.name, "definition": t.definition}
                 for t in plan.tiers if t.tier == "E"]
    doc = criteria_loop(ws, llm, client, scope, digest, axes, usage, hitl,
                        pool_df=pool_df, probe_pool=probe_pool, front_matter=front_matter,
                        exclusion_families=excl_fams)

    print(f"[criteria approved] {len(doc.domain_criteria)} C / "
          f"{len(doc.exclusion_criteria)} E -> {ws.criteria_final_md}")
    if local_docs:
        from src.agentic.localdocs import unreflected_owner_docs
        missing = unreflected_owner_docs(ws)
        if missing:
            warn = ("> ⚠ **소유자 문서 미반영 경고**: 다음 참고자료에서 근거 노트가 0개 추출되었고 "
                    "원문 주입 한도도 초과하여 이 기준서에 반영되지 못했습니다: "
                    + ", ".join(missing) + " — `research/blocked.jsonl` 을 확인하세요.\n\n")
            ws.criteria_final_md.write_text(
                warn + ws.criteria_final_md.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  !!!! 소유자 문서 미반영: {', '.join(missing)} — 기준서 상단에 경고 기록")
    if not mock:
        print(f"research usage: {usage.calls} calls "
              f"~${usage.cost_usd(_RESEARCH_IN_RATE, _RESEARCH_OUT_RATE):.2f}")
    return ws, scope, doc
