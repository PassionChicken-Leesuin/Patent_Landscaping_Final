"""[5] Criteria validator + feedback-loop controller.

The validator criticizes the sentence-form criteria document; its action drives
the loop: revise (redraft with the critique), collect_more (re-enter the research
agent with targeted searches), ask_human (HITL), approve (finalize). Budgeted by
CRITERIA_MAX_ITERS; budget exhaustion with a critical issue or unresolved external
action writes criteria_blocked.json and stops without a final document.
"""
from __future__ import annotations
import json

import pandas as pd

from src.mas.llm import StructuredLLM, Usage
from src.mas.runner import KeyPool
from src.agentic import config as AC
from src.agentic import research as R
from src.agentic.axes import allowed_source_references
from src.agentic.boundary_probe import measured_questions, probe_boundaries
from src.agentic.criteria import draft_criteria, resolve_open_questions, save_final
from src.agentic.hitl import HITL
from src.agentic.schemas import (AxisSynthesisOut, CriteriaCritiqueOut, CriteriaDocOut,
                                 CorpusDigestOut, CritiqueIssue, QueryScopeOut)
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


_PROVENANCE_CRITIQUE = (
    "\n6. AXIS COVERAGE: every core/supplemental technology axis must map to at least one "
    "C-criterion through axis_ids; disputed axes must remain explicit boundaries.\n"
    "7. PROVENANCE: every axis and every C/E criterion must carry typed source_refs whose "
    "references exist in the supplied evidence/axis synthesis. Legacy sources alone are "
    "insufficient. Missing whole-axis coverage or provenance is critical.\n"
    "8. OWNER-DOCUMENT QUALITY: respect owner scope intent, but verify that documented gaps "
    "were supplemented where research/corpus evidence supports doing so.\n"
)


class CriteriaValidationBlocked(RuntimeError):
    """Raised when the criteria budget ends with material faults unresolved."""

    def __init__(self, path, critical_count: int):
        self.path = path
        self.critical_count = critical_count
        super().__init__(
            f"criteria validation blocked with {critical_count} critical issue(s); see {path}"
        )


def criteria_integrity_issues(doc: CriteriaDocOut,
                              axes: AxisSynthesisOut,
                              allowed_refs: set[str] | None = None) -> list[CritiqueIssue]:
    """Deterministic checks that cannot be waived by a prose validator."""
    issues: list[CritiqueIssue] = []
    axis_ids = {a.id for a in axes.technology_axes}
    anchored_refs = {ref.reference for a in axes.technology_axes for ref in a.source_refs}
    valid_refs = anchored_refs | (allowed_refs or set())
    active_ids = {a.id for a in axes.technology_axes
                  if a.status in ("core", "supplemental")}
    mapped = {aid for c in doc.domain_criteria for aid in c.axis_ids}
    missing = sorted(active_ids - mapped)
    if missing:
        issues.append(CritiqueIssue(
            field="domain_criteria.axis_ids",
            problem=f"Active technology axes lack a C-criterion mapping: {missing}",
            suggestion="Map every active axis to a testable inclusion criterion.",
            severity="critical"))
    if not axes.technology_axes:
        issues.append(CritiqueIssue(
            field="technology_axes", problem="No technology axes were synthesized.",
            suggestion="Synthesize an auditable axis inventory before drafting criteria.",
            severity="critical"))
    for axis in axes.technology_axes:
        if not axis.source_refs:
            issues.append(CritiqueIssue(
                field=f"technology_axes.{axis.id}.source_refs",
                problem=f"Axis {axis.id} has no typed provenance.",
                suggestion="Attach a real query/owner/web/corpus source reference.",
                severity="critical"))
        for ref in axis.source_refs:
            malformed = ((ref.source_type == "web" and not ref.reference.startswith(("http://", "https://")))
                         or (ref.source_type == "owner_doc" and not ref.reference.startswith("local://"))
                         or (ref.source_type == "corpus" and not ref.reference.startswith("corpus:")))
            if malformed:
                issues.append(CritiqueIssue(
                    field=f"technology_axes.{axis.id}.source_refs",
                    problem=f"Axis {axis.id} has a malformed {ref.source_type} reference: {ref.reference}",
                    suggestion="Use the exact typed reference format from the input catalog.",
                    severity="critical"))
    for item in [*doc.domain_criteria, *doc.exclusion_criteria]:
        unknown = sorted(set(item.axis_ids) - axis_ids)
        if unknown:
            issues.append(CritiqueIssue(
                field=f"{item.id}.axis_ids",
                problem=f"Criterion {item.id} cites unknown axes: {unknown}",
                suggestion="Use only ids from the approved axis synthesis.",
                severity="critical"))
        if not item.source_refs:
            issues.append(CritiqueIssue(
                field=f"{item.id}.source_refs",
                problem=f"Criterion {item.id} has no typed provenance.",
                suggestion="Copy supporting typed references from mapped axes/evidence.",
                severity="critical"))
        unknown_refs = sorted({ref.reference for ref in item.source_refs
                               if ref.source_type != "hitl"
                               and ref.reference not in valid_refs})
        if unknown_refs:
            issues.append(CritiqueIssue(
                field=f"{item.id}.source_refs",
                problem=f"Criterion {item.id} cites references absent from the allowed evidence catalog: {unknown_refs}",
                suggestion="Copy an exact reference from the axis synthesis or allowed evidence catalog.",
                severity="critical"))
    return issues


def critique_criteria(llm: StructuredLLM, doc: CriteriaDocOut, scope: QueryScopeOut,
                      digest: CorpusDigestOut, axes: AxisSynthesisOut,
                      evidence_summary: str,
                      usage: Usage,
                      allowed_refs: set[str] | None = None) -> CriteriaCritiqueOut:
    user = (f"=== Criteria document ===\n{json.dumps(doc.model_dump(), ensure_ascii=False)}\n\n"
            f"=== Approved axis synthesis ===\n{json.dumps(axes.model_dump(), ensure_ascii=False)}\n\n"
            f"=== Pool digest ===\n{json.dumps(digest.model_dump(), ensure_ascii=False)}\n\n"
            f"=== Evidence notes ===\n{evidence_summary}")
    out, pt, ct = llm.parse(_CRITIQUE_SYSTEM.format(domain=scope.canonical_name_en)
                            + _PROVENANCE_CRITIQUE,
                            user, CriteriaCritiqueOut)
    usage.add(pt, ct)
    deterministic = criteria_integrity_issues(doc, axes, allowed_refs)
    if deterministic:
        known = {(i.field, i.problem) for i in out.issues}
        out.issues.extend(i for i in deterministic if (i.field, i.problem) not in known)
        out.approved = False
        if out.action == "approve":
            out.action = "revise"
    return out


def criteria_loop(ws: Workspace, llm: StructuredLLM, client: SearchClient,
                  scope: QueryScopeOut, digest: CorpusDigestOut,
                  axes: AxisSynthesisOut, usage: Usage,
                  hitl: HITL, pool_df: pd.DataFrame | None = None,
                  probe_pool: KeyPool | None = None) -> CriteriaDocOut:
    """Draft -> (probe + ask author's own scope questions) -> critique -> {approve |
    revise | collect_more | ask_human} loop."""
    evidence_summary = R.notes_summary_by_type(ws)
    allowed_refs = allowed_source_references(ws, digest)
    # Research-run isolation: only answers collected during THIS criteria loop
    # enter later drafts. No user ruling from another run is seeded here.
    human_qa_all: list[dict] = []
    ver = 1                                              # next unused criteria version

    # Batch-HITL resume: if a pending draft was persisted and answers are now available,
    # reuse that EXACT draft (same question ids) instead of redrafting non-deterministically.
    resuming = ws.criteria_pending_json.exists() and ws.answers_json.exists()
    if resuming:
        doc = CriteriaDocOut(**ws.read_json(ws.criteria_pending_json))
        print(f"  [criteria] resuming pending draft with {len(doc.open_questions)} "
              f"answered question(s)")
    else:
        doc = draft_criteria(ws, llm, scope, digest, axes, evidence_summary, usage, version=1,
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
            doc, qa = resolve_open_questions(ws, llm, scope, digest, axes, evidence_summary,
                                             doc, hitl, usage, version=ver)
            human_qa_all += qa
            ver = 2
            ws.criteria_pending_json.unlink(missing_ok=True)   # answered -> clear

    versions: dict[int, tuple[CriteriaDocOut, int, CriteriaCritiqueOut]] = {}

    for rnd in range(1, AC.CRITERIA_MAX_ITERS + 1):
        critique = critique_criteria(llm, doc, scope, digest, axes, evidence_summary, usage,
                                     allowed_refs=allowed_refs)
        ws.write_json(ws.critique_json(ver), critique.model_dump())
        n_crit = sum(1 for i in critique.issues if i.severity == "critical")
        versions[ver] = (doc, n_crit, critique)
        print(f"  [criteria] v{ver} validator: action={critique.action} "
              f"issues={len(critique.issues)} (critical={n_crit})")

        no_critical = not any(i.severity == "critical" for i in critique.issues)
        if no_critical and critique.action in ("approve", "revise"):
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
            allowed_refs = allowed_source_references(ws, digest)
        elif critique.action == "ask_human" and critique.human_questions:
            human_qa_all += hitl.ask(critique.human_questions,
                                     context=f"기준서 v{ver} 검증 중")
        # revise (and every non-approve path) -> redraft with full feedback
        doc = draft_criteria(ws, llm, scope, digest, axes, evidence_summary, usage,
                             version=ver + 1, prior=doc, critique=critique,
                             human_qa=human_qa_all or None)
        ver += 1

    # Budget exhausted: a criteria document with material faults is not a valid
    # output. Persist an actionable report and stop instead of silently blessing it.
    best_v_checked = min(versions, key=lambda v: (versions[v][1], -v))
    checked_doc, checked_n, checked_critique = versions[best_v_checked]
    unresolved_action = checked_critique.action in ("ask_human", "collect_more")
    blocked_report = {
        "status": "blocked" if (checked_n or unresolved_action)
                  else "approved_without_more_revisions",
        "reason": "criteria loop budget exhausted",
        "best_version": best_v_checked,
        "critical_counts": {str(v): versions[v][1] for v in versions},
        "critical_issues": [i.model_dump() for i in checked_critique.issues
                            if i.severity == "critical"],
        "unresolved_action": checked_critique.action if unresolved_action else None,
    }
    if checked_n or unresolved_action:
        ws.write_json(ws.criteria_blocked_json, blocked_report)
        reported_n = max(1, checked_n)
        print(f"  [criteria] BLOCKED: v{best_v_checked} has {checked_n} critical "
              f"issue(s), unresolved action={checked_critique.action}; final criteria "
              "were not written.")
        raise CriteriaValidationBlocked(ws.criteria_blocked_json, reported_n)
    save_final(ws, checked_doc)
    return checked_doc
