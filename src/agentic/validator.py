"""[5] Criteria validator + feedback-loop controller.

The validator criticizes the sentence-form criteria document; its action drives
the loop: revise (redraft with the critique), collect_more (re-enter the research
agent with targeted searches), ask_human (HITL), approve (finalize). Budgeted by
CRITERIA_MAX_ITERS; on budget exhaustion the latest draft is finalized with a
warning recorded in the critique file.
"""
from __future__ import annotations
import json

import pandas as pd

from src.mas.llm import StructuredLLM, Usage
from src.mas.runner import KeyPool
from src.agentic import config as AC
from src.agentic import research as R
from src.agentic.boundary_probe import measured_questions, probe_boundaries
from src.agentic.criteria import draft_criteria, resolve_open_questions, save_final
from src.agentic.hitl import HITL
from src.agentic.schemas import (CriteriaCritiqueOut, CriteriaDocOut, CorpusDigestOut,
                                 QueryScopeOut)
from src.agentic.search import SearchClient
from src.agentic.workspace import Workspace

_CRITIQUE_SYSTEM = (
    "You are the Criteria Validator — an adversarial patent-domain expert reviewing the "
    "criteria document that will govern patent judgments for the domain: {domain}.\n"
    "Check rigorously:\n"
    "1. Is every C-criterion a testable full sentence an expert could apply to a "
    "title+abstract alone (no external data needed)?\n"
    "2. Do the C-criteria cover ALL defining functional tasks found in the evidence, and do "
    "they demand that the invention PERFORMS a task (not merely mentions vocabulary)?\n"
    "3. Are the E-criteria genuinely 'rule-match-but-not-the-task' shaped (adjacent/look-"
    "alike technologies), not just restatements of 'irrelevant'?\n"
    "4. Does boundary_guidance actually resolve the borderline patterns reported in the "
    "pool digest?\n"
    "4b. Do scope_decisions cover EVERY main cluster of the pool digest, and is each "
    "verdict's rationale actually supported by evidence (not an unexamined narrow default)? "
    "A major pool cluster ruled out with a weak rationale is a critical fault — if the "
    "call genuinely cannot be settled from evidence, that is what ask_human is for.\n"
    "4c. CONSISTENCY: a scope verdict that contradicts an exclusion criterion is a critical "
    "fault (e.g. an assist-technology cluster ruled 'in' while an E-criterion excludes "
    "assist technologies). 'Important/essential to the domain' used as an in-rationale is a "
    "critical fault. A dual-form cluster with a blanket in/out instead of 'conditional' + "
    "decisive test is a critical fault.\n"
    "5. Is the definition faithful to the user's query scope (no silent narrowing or "
    "broadening)? Are cited sources plausible?\n"
    "Rate every issue's severity: 'critical' = it would MATERIALLY change judgment outcomes "
    "on the pool (wrong scope ruling, untestable criterion, missing whole task family); "
    "'minor' = polish (an extra example, finer wording, a sub-technique not named but "
    "already generically covered by an existing criterion).\n"
    "Decide ONE action:\n"
    "- approve: no CRITICAL issues remain — approve even when minor issues exist (list them; "
    "do not hold the document hostage to perfection).\n"
    "- revise: at least one critical issue is fixable by rewriting.\n"
    "- collect_more: evidence is insufficient on some aspect — propose targeted follow-up "
    "searches (followup_queries).\n"
    "- ask_human: a genuine scope decision only the human owner can make (e.g. whether an "
    "ambiguous sub-area is in scope) — write clear natural-language human_questions with "
    "options where possible.\n"
    "ESCALATION RULE: if you challenge a scope_decision verdict (a cluster's in/out ruling) "
    "and the available evidence cannot settle it, the action MUST be ask_human — rewriting "
    "cannot resolve a question of the owner's intent. Never spend a revise round on a scope "
    "dispute.\n"
    "Output JSON only."
)


def critique_criteria(llm: StructuredLLM, doc: CriteriaDocOut, scope: QueryScopeOut,
                      digest: CorpusDigestOut, evidence_summary: str,
                      usage: Usage) -> CriteriaCritiqueOut:
    user = (f"=== Criteria document ===\n{json.dumps(doc.model_dump(), ensure_ascii=False)}\n\n"
            f"=== Pool digest ===\n{json.dumps(digest.model_dump(), ensure_ascii=False)}\n\n"
            f"=== Evidence notes ===\n{evidence_summary}")
    out, pt, ct = llm.parse(_CRITIQUE_SYSTEM.format(domain=scope.canonical_name_en),
                            user, CriteriaCritiqueOut)
    usage.add(pt, ct)
    return out


def criteria_loop(ws: Workspace, llm: StructuredLLM, client: SearchClient,
                  scope: QueryScopeOut, digest: CorpusDigestOut, usage: Usage,
                  hitl: HITL, pool_df: pd.DataFrame | None = None,
                  probe_pool: KeyPool | None = None) -> CriteriaDocOut:
    """Draft -> (probe + ask author's own scope questions) -> critique -> {approve |
    revise | collect_more | ask_human} loop."""
    evidence_summary = R.notes_summary_by_type(ws)
    # P3: the owner's persisted rulings for this domain enter EVERY draft as
    # authoritative answers — even when this run never re-asks the question
    # (prevents rulings evaporating between runs/UIs, as in the A/B incident)
    human_qa_all: list[dict] = hitl.profile_qa()
    if human_qa_all:
        print(f"  [criteria] domain profile: {len(human_qa_all)}건의 기존 소유자 판결 주입")
    ver = 1                                              # next unused criteria version

    # Batch-HITL resume: if a pending draft was persisted and answers are now available,
    # reuse that EXACT draft (same question ids) instead of redrafting non-deterministically.
    resuming = ws.criteria_pending_json.exists() and ws.answers_json.exists()
    if resuming:
        doc = CriteriaDocOut(**ws.read_json(ws.criteria_pending_json))
        print(f"  [criteria] resuming pending draft with {len(doc.open_questions)} "
              f"answered question(s)")
    else:
        doc = draft_criteria(ws, llm, scope, digest, evidence_summary, usage, version=1,
                             human_qa=human_qa_all or None)

    # PROACTIVE scope questions: the author flags candidate boundaries; we MEASURE each by
    # judging a pool sample under its broad vs narrow rule and keep only those that flip a
    # real number of patents (ranked by measured impact). Then ask the human BEFORE spending
    # the critique budget (answers are authoritative and baked into a revised draft).
    if doc.open_questions:
        if not resuming and pool_df is not None and probe_pool is not None and len(pool_df):
            ranked = probe_boundaries(doc.open_questions, pool_df, probe_pool,
                                      scope.canonical_name_en, ws.boundary_probe_jsonl)
            kept = measured_questions(ranked)
            ws.append_jsonl(ws.boundary_probe_jsonl,
                            {"summary": [{"id": q.id, "flip": f, "n": n} for q, f, n in ranked]})
            print(f"  [criteria] probed {len(doc.open_questions)} candidate boundaries "
                  f"-> {len(kept)} move real patents")
            doc.open_questions = kept
        if doc.open_questions:
            # persist BEFORE asking so a batch-mode stop resumes on the same questions
            ws.write_json(ws.criteria_pending_json, doc.model_dump())
            print(f"  [criteria] asking human {len(doc.open_questions)} scope question(s)")
            doc, qa = resolve_open_questions(ws, llm, scope, digest, evidence_summary,
                                             doc, hitl, usage, version=ver)
            human_qa_all += qa
            ver = 2
            ws.criteria_pending_json.unlink(missing_ok=True)   # answered -> clear

    versions: dict[int, tuple[CriteriaDocOut, int]] = {}   # v -> (doc, n_critical)

    for rnd in range(1, AC.CRITERIA_MAX_ITERS + 1):
        critique = critique_criteria(llm, doc, scope, digest, evidence_summary, usage)
        ws.write_json(ws.critique_json(ver), critique.model_dump())
        n_crit = sum(1 for i in critique.issues if i.severity == "critical")
        versions[ver] = (doc, n_crit)
        print(f"  [criteria] v{ver} validator: action={critique.action} "
              f"issues={len(critique.issues)} (critical={n_crit})")

        no_critical = not any(i.severity == "critical" for i in critique.issues)
        if critique.action == "approve" or critique.approved or (
                critique.action == "revise" and no_critical):
            if critique.action == "revise":
                print("  [criteria] only minor issues — treating as approve")
            save_final(ws, doc)
            return doc

        if rnd == AC.CRITERIA_MAX_ITERS:
            break

        if critique.action == "collect_more" and critique.followup_queries:
            R.collect_more(ws, llm, client, critique.followup_queries,
                           scope.canonical_name_en, usage)
            evidence_summary = R.notes_summary_by_type(ws)
        elif critique.action == "ask_human" and critique.human_questions:
            human_qa_all += hitl.ask(critique.human_questions,
                                     context=f"기준서 v{ver} 검증 중")
        # revise (and every non-approve path) -> redraft with full feedback
        doc = draft_criteria(ws, llm, scope, digest, evidence_summary, usage,
                             version=ver + 1, prior=doc, critique=critique,
                             human_qa=human_qa_all or None)
        ver += 1

    # budget exhausted: finalize the version the validator rated LEAST critical
    # (the last draft is not necessarily the best — revisions can regress)
    best_v = min(versions, key=lambda v: (versions[v][1], -v))
    doc = versions[best_v][0]
    ws.write_json(ws.critique_json(ver + 1),
                  {"warning": "criteria loop budget exhausted",
                   "finalized_version": best_v,
                   "critical_counts": {v: versions[v][1] for v in versions}})
    print(f"  [criteria] WARNING: budget exhausted — finalizing v{best_v} "
          f"(fewest critical issues: {versions[best_v][1]})")
    save_final(ws, doc)
    return doc
