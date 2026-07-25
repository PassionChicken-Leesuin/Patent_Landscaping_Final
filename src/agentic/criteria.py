"""[4] Criteria agent: web evidence x corpus reality -> sentence-form criteria document.

Outputs (per user spec, both in full sentences):
  - domain_criteria  [C1..Cn]: how to judge that a patent IS domain-valid
  - scope_statement + exclusion_criteria [E1..Em]: what is analyzed / what is excluded
Each criterion carries its sources (evidence URLs or 'corpus: <case>').
Saved as criteria_v<i>.json + a human-readable criteria_v<i>.md.
"""
from __future__ import annotations
import json

from src.mas.llm import StructuredLLM, Usage
from src.agentic import config as AC
from src.agentic.hitl import HITL
from src.agentic.schemas import (AxisSynthesisOut, CriteriaCritiqueOut, CriteriaDocOut,
                                 CorpusDigestOut, CriteriaPatchOut, CritiqueIssue,
                                 HITLQuestion, QueryScopeOut)
from src.agentic.workspace import Workspace

_LANDSCAPING_CLAUSE = (
    "\nSCOPE PHILOSOPHY — this is a PATENT LANDSCAPING task, which prizes RECALL. A patent "
    "belongs to the domain if it IMPLEMENTS the domain technology, IMPROVES it, provides an "
    "ENABLING component/method/material that is SPECIFIC to it, or is a SPECIFIC APPLICATION "
    "of it — not only if it performs the single canonical end-task. Write the definition and "
    "C-criteria at this landscaping breadth: include component-level, method-level, and "
    "application-level inventions that are specific to the domain. Reserve exclusion criteria "
    "for true look-alikes (the domain's vocabulary/components used FOR A DIFFERENT FIELD) and "
    "for generic inventions with no domain-specific contribution — NOT for domain-specific "
    "inventions that merely address a sub-part or an application of the technology.\n"
)


def _scope_clause() -> str:
    return _LANDSCAPING_CLAUSE if AC.LANDSCAPING_INCLUSIVE else ""

_SYSTEM = (
    "You are the Criteria-Extraction agent of a patent-landscaping system: a patent-domain "
    "expert writing the OFFICIAL criteria document that will govern whether each patent "
    "belongs to the domain: {domain}.\n"
    "You must COMPARE AND CONTRAST two inputs: (a) evidence notes collected from the web, and "
    "(b) a digest of the ACTUAL patent pool that will be judged. The criteria must fit both — "
    "grounded in authoritative evidence, and operational for the real pool.\n"
    "Write, ALL IN FULL SENTENCES:\n"
    "- domain_definition: a precise one-paragraph definition at the functional-task level "
    "(what an invention must DO to belong, not just what words it uses).\n"
    "- domain_criteria (ids C1, C2, ...): positive judgment criteria. Each statement must be "
    "a self-contained, testable sentence an expert could apply to a title+abstract. Cover "
    "every defining task and the technical signals that evidence it — write in English.\n"
    "- scope_statement: one paragraph delimiting which patents are within the scope of "
    "analysis for this domain.\n"
    "- scope_decisions: an EXPLICIT ruling for EVERY main cluster and suspected boundary "
    "cluster reported in the pool digest. Scope breadth is a decision, never a silent "
    "default: a cluster that shares the domain's core purpose (even a different technique "
    "or an enabling/handling step of that purpose) is ruled in; a cluster that merely uses "
    "the domain's outputs or vocabulary for another purpose is ruled out.\n"
    "  Cover at most the 15 highest-impact clusters (merge minor ones); do not enumerate "
    "every tiny cluster — an over-long list dilutes the document and can be truncated.\n"
    "  RULES for verdicts: (1) 'X is important/essential to the domain' is NOT a valid "
    "in-rationale — the cluster's patents must PERFORM a defining task or exist specifically "
    "for it. (2) A verdict must never contradict an exclusion criterion. (3) If a cluster "
    "exists in BOTH an in-scope form and a look-alike form (e.g. the same component serving "
    "either the domain system or its excluded counterpart), rule it 'conditional' and state "
    "the DECISIVE TEST in the rationale — hedges like 'in when integrated' are forbidden.\n"
    "- exclusion_criteria (ids E1, E2, ...): each a sentence identifying a class of patents "
    "that MATCH the domain's vocabulary or rules but do NOT perform its defining tasks "
    "(look-alikes / adjacent technologies), or that clearly lack any domain signal.\n"
    "- boundary_guidance: sentences telling the judge how to decide the borderline patterns "
    "actually observed in the pool digest (cite the pattern).\n"
    "- open_questions: the SCOPE BOUNDARIES you are genuinely unsure about — cases where the "
    "evidence and the pool are consistent with either a broader or a narrower domain. These "
    "are exactly the calls only the domain owner can make (e.g. 'does this domain include an "
    "adjacent capability X, or only the strict core?'). Draw candidates from the pool "
    "digest's suspected_boundary_cases and from any 'conditional' scope_decisions. For each: "
    "a plain-language question; 2-3 concrete options; your tentative_default (the assumption "
    "your current criteria encode, so work proceeds unattended); and CRUCIALLY a broad_rule "
    "and a narrow_rule — each a single, self-contained sentence a judge could apply to a "
    "title+abstract to decide in/out, differing ONLY on this boundary. The pipeline will "
    "MEASURE how many pool patents actually flip between the two rules, so make the two rules "
    "genuinely separable. Raise up to 6 candidates; the pipeline keeps only those that move "
    "real patents. If the scope is unambiguous, return an empty list.\n"
    "- For every criterion, sources = the supporting evidence URLs and/or 'corpus: <case>' "
    "references. Do not invent sources.\n"
    "- For every C/E criterion, also fill observable_signals: 3-8 NON-EXCLUSIVE title/"
    "abstract cues (terms, phrasings, component names) indicating the criterion may apply. "
    "TESTABILITY CONTRACT: a criterion is testable when it states a functional task AND "
    "lists observable_signals; the signals are indicative cues, never required keywords — "
    "the absence of a signal alone must never exclude a patent.\n"
    "Output JSON only."
)

# Owner intent is binding; completeness and facts are independently assessed
# and may be supplemented from research + corpus.
_OWNER_CLAUSE = (
    "\nOWNER DOCUMENT POLICY: the document is the top authority for the owner's intended "
    "SCOPE, but it is not assumed to be technically complete or factually perfect. Use the "
    "supplied quality assessment. Anchor every explicit owner axis, autonomously fill "
    "material gaps with supported research and corpus evidence, and never promote a "
    "corpus-only cluster to core without other support. Surface material conflicts as "
    "disputed axes/open questions instead of silently resolving them.\n"
)

_AXIS_CLAUSE = (
    "\nAXIS/PROVENANCE CONTRACT: reproduce the supplied technology_axes and owner-document "
    "assessment faithfully. Map every C/E criterion to axis_ids. Every core or supplemental "
    "axis must be covered by at least one C-criterion. Every C/E criterion must include "
    "typed source_refs copied from the axis synthesis or supplied evidence; also populate "
    "legacy sources for readable export. Do not invent references.\n"
)

_CASEMAP_CLAUSE = (
    "\nCASE-MAPPING POLICY: a case-mapping pass over the pool already produced the tiered "
    "design, confirmed/boundary/false-positive examples, cross-cutting insights, reusable "
    "false-positive cues, and the owner's answered scope decisions (below). Treat them as "
    "authoritative for THIS domain: turn the tiers into C/E criteria and scope_decisions, "
    "encode the false-positive cues as observable-signal cautions, and record each answered "
    "decision VERBATIM as a scope_decision (never summarize an answer into its opposite).\n"
)

_REVISE_SUFFIX = (
    "\n\nA validator reviewed the previous version of this document and demanded changes. "
    "Produce a MINIMALLY-EDITED revision: fix EXACTLY the flagged issues and keep every "
    "other criterion, scope decision, and sentence VERBATIM from the previous document. "
    "Do not add new criteria, do not reword unflagged text — unnecessary rewrites introduce "
    "new faults. Incorporate any human answers verbatim as authoritative decisions."
)


def _renumber(doc: CriteriaDocOut) -> CriteriaDocOut:
    """Force canonical unique ids C1..Cn / E1..Em (LLM id drift is common)."""
    for i, c in enumerate(doc.domain_criteria, 1):
        c.id = f"C{i}"
    for i, e in enumerate(doc.exclusion_criteria, 1):
        e.id = f"E{i}"
    return doc


def draft_criteria(ws: Workspace, llm: StructuredLLM, scope: QueryScopeOut,
                   digest: CorpusDigestOut, axis_synthesis: AxisSynthesisOut,
                   evidence_summary: str, usage: Usage,
                   version: int = 1,
                   prior: CriteriaDocOut | None = None,
                   critique: CriteriaCritiqueOut | None = None,
                   human_qa: list[dict] | None = None,
                   front_matter: str = "") -> CriteriaDocOut:
    from src.agentic.axes import allowed_source_references, render_allowed_refs
    allowed_refs = allowed_source_references(ws, digest)
    system = _SYSTEM.format(domain=scope.canonical_name_en) + _scope_clause() + _AXIS_CLAUSE
    parts = [f"User query: {scope.canonical_name_en} ({scope.disambiguation_notes})",
             f"Initial task hypotheses:\n" + "\n".join(f"- {t}" for t in scope.initial_task_hypotheses),
             f"\n=== (0) Approved technology-axis synthesis ===\n"
             f"{json.dumps(axis_synthesis.model_dump(), ensure_ascii=False)}",
             "\n=== ALLOWED SOURCE REFERENCES (cite the id exactly) ===\n"
             + render_allowed_refs(ws, digest),
             f"\n=== (a) Web evidence notes ===\n{evidence_summary}",
             f"\n=== (b) Patent-pool digest ===\n{json.dumps(digest.model_dump(), ensure_ascii=False)}"]
    # P1: a short owner document is the top scope authority — inject it verbatim
    # (its notes also flow in via (a), but summarization loses the owner's axes)
    from src.agentic.localdocs import owner_docs_block
    owner_block = owner_docs_block(ws)
    if owner_block:
        system += _OWNER_CLAUSE
        parts.insert(1, owner_block)
    # 2번: surface the corpus-derived boundary candidates explicitly so open_questions has
    # high coverage (the probe stage then filters to the ones that move real patents).
    cand = list(digest.suspected_boundary_cases) + list(digest.mismatch_with_web_evidence)
    if cand and prior is None:
        parts.append("\n=== CANDIDATE SCOPE BOUNDARIES (evaluate EACH as a possible "
                     "open_question with a broad_rule and narrow_rule) ===\n"
                     + "\n".join(f"- {c}" for c in cand))
    # Front-half (case-mapping) product: the tiered design, the confirmed/boundary
    # case tables, the cross-cutting insights, the merged false-positive cues, and the
    # human's answered scope decisions. Authoritative for the FIRST draft only; the
    # revise loop then works from the critique like before.
    if front_matter and prior is None:
        system += _CASEMAP_CLAUSE
        parts.append(front_matter)
    if prior is not None:
        system += _REVISE_SUFFIX
        parts.append(f"\n=== Previous document ===\n{json.dumps(prior.model_dump(), ensure_ascii=False)}")
    if critique is not None:
        parts.append(f"\n=== Validator critique ===\n{json.dumps(critique.model_dump(), ensure_ascii=False)}")
    # auto answers are unattended assumptions, NOT owner decisions — presenting
    # them as authoritative human answers was the '권위 오인' fault (2026-07-22)
    human = [qa for qa in (human_qa or [])
             if qa.get("answered_by", "human") in ("human", "human_batch", "human_prior")]
    assumed = [qa for qa in (human_qa or []) if qa not in human]
    if human:
        parts.append("\n=== Human expert answers (authoritative owner decisions) ===\n"
                     + "\n".join(f"Q: {qa['question']}\nA: {qa['answer']}" for qa in human))
    if assumed:
        parts.append(
            "\n=== SYSTEM ASSUMPTIONS (unattended run — NOT owner decisions) ===\n"
            "No human was available for these scope questions. Encode each as an "
            "explicit provisional assumption: keep the evidence-supported ruling, state "
            "the assumption in boundary_guidance, and keep the boundary listed in "
            "open_questions for a future owner decision. NEVER present these as "
            "owner-confirmed scope.\n"
            + "\n".join(f"Q: {qa['question']}\nA(auto): {qa['answer']}" for qa in assumed))

    out, pt, ct = llm.parse(system, "\n".join(parts), CriteriaDocOut)
    usage.add(pt, ct)
    out.technology_axes = [a.model_copy(deep=True) for a in axis_synthesis.technology_axes]
    out.owner_document_assessment = axis_synthesis.owner_document_assessment.model_copy(deep=True)
    repair_criterion_refs(ws, out, allowed_refs)
    out = _renumber(out)
    save_criteria(ws, out, version)
    return out


def repair_criterion_refs(ws: Workspace, doc: CriteriaDocOut,
                          allowed_refs: set[str]) -> list[dict]:
    """Audited deterministic provenance repair for every C/E criterion."""
    from src.agentic.axes import canonicalize_source_refs, drop_unknown_refs
    repairs: list[dict] = []
    for criterion in [*doc.domain_criteria, *doc.exclusion_criteria]:
        repairs += canonicalize_source_refs(criterion.source_refs, allowed_refs,
                                            context=f"criterion:{criterion.id}")
        repairs += drop_unknown_refs(criterion, allowed_refs,
                                     context=f"criterion:{criterion.id}")
    for repair in repairs:
        ws.append_jsonl(ws.provenance_repairs_jsonl, {"stage": "criteria", **repair})
    return repairs


def resolve_open_questions(ws: Workspace, llm: StructuredLLM, scope: QueryScopeOut,
                           digest: CorpusDigestOut, axis_synthesis: AxisSynthesisOut,
                           evidence_summary: str,
                           doc: CriteriaDocOut, hitl: HITL, usage: Usage,
                           version: int) -> tuple[CriteriaDocOut, list[dict]]:
    """Ask the human the criteria author's own scope questions, then fold the answers
    into a revised document as authoritative decisions. Returns (doc, human_qa)."""
    if not doc.open_questions:
        return doc, []
    questions = [HITLQuestion(
        id=q.id,
        question=f"{q.question} (현재 가정: {q.tentative_default})",
        why_needed=q.why_it_matters,
        options=q.options,
    ) for q in doc.open_questions]
    # Stable-identity guard: the drafter re-raises the same boundary in new words each
    # round, so the text-hash id drifts and HITL cannot match it to the answer already
    # given. Semantically settle new questions against THIS run's human rulings first
    # (the same mechanism the judge stage uses) — a boundary already decided is not
    # re-asked; its prior ruling is reapplied verbatim.
    from src.agentic.judge import _prior_rulings, settle_against_prior
    prior = _prior_rulings(ws)
    fresh, settled = settle_against_prior(llm, questions, prior, usage)
    qa: list[dict] = []
    for q, ruling in settled:
        entry = {"stage": hitl.stage, "id": q.id, "question": q.question,
                 "answer": ruling.get("answer", ""), "answered_by": "human_prior",
                 "settled_from": ruling.get("question", "")}
        ws.append_jsonl(ws.human_qa_jsonl, entry)
        qa.append({"id": q.id, "question": q.question,
                   "answer": ruling.get("answer", ""), "answered_by": "human_prior"})
    if settled:
        print(f"  [criteria] {len(settled)} boundary(s) already decided this run "
              f"-> reapplied prior ruling (no re-ask)")
    qa += hitl.ask(fresh, context=f"{scope.canonical_name_en} 기준 작성 중 범위 결정")
    # if the human just accepted every default (or off-mode auto-answers), no revision needed
    doc2 = draft_criteria(ws, llm, scope, digest, axis_synthesis, evidence_summary, usage,
                          version=version + 1, prior=doc, human_qa=qa)
    return doc2, qa


# ----------------------------------------------------------------- issue-specific patching
_PATCH_SYSTEM = (
    "You are the Criteria Patch Reviser of a patent-landscaping system for the domain: "
    "{domain}.\n"
    "A validator ledger lists specific unresolved issues in the criteria document. Produce "
    "the SMALLEST set of field-level patches that resolves EXACTLY those issues. You may "
    "only touch the fields named by each issue (its target ids); everything else stays "
    "byte-identical — whole-document rewrites are forbidden because they churn unrelated "
    "fields and create new faults.\n"
    "- Each patch lists the issue_codes it resolves.\n"
    "- replace/remove target an existing criterion id, scope-decision topic, or 1-based "
    "boundary_guidance index; add appends a new element (id is assigned by the system).\n"
    "- For criteria patches keep the axis_ids mapping valid, copy source_refs references "
    "EXACTLY from the allowed catalog, and keep observable_signals non-exclusive cues.\n"
    "- An issue you genuinely cannot resolve without new evidence or an owner decision "
    "goes into unresolvable_issue_codes with a note — do not fake a fix.\n"
    "Output JSON only."
)


class PatchApplyError(RuntimeError):
    """A patch referenced a non-existent target or omitted its payload."""


def apply_patches(doc: CriteriaDocOut, patches) -> tuple[CriteriaDocOut, set[str]]:
    """Apply field-level patches; ids of untouched criteria never shift (no renumber)."""
    new = doc.model_copy(deep=True)
    touched: set[str] = set()
    for p in patches:
        if p.target in ("domain_criteria", "exclusion_criteria"):
            lst = getattr(new, p.target)
            if p.op == "add":
                if p.new_criterion is None:
                    raise PatchApplyError(f"add {p.target} without new_criterion")
                norm = " ".join(p.new_criterion.statement.lower().split())
                dup = next((x for x in lst
                            if " ".join(x.statement.lower().split()) == norm), None)
                if dup is not None:      # re-adding an existing criterion is a no-op
                    touched.add(dup.id)
                    continue
                c = p.new_criterion.model_copy(deep=True)
                prefix = "C" if p.target == "domain_criteria" else "E"
                used = {x.id for x in lst}
                n = len(lst) + 1
                while f"{prefix}{n}" in used:
                    n += 1
                c.id = f"{prefix}{n}"
                lst.append(c)
                touched.add(c.id)
                continue
            idx = next((i for i, c in enumerate(lst) if c.id == p.target_id), None)
            if idx is None:
                raise PatchApplyError(f"unknown criterion {p.target_id!r} in {p.target}")
            if p.op == "remove":
                lst.pop(idx)
            else:
                if p.new_criterion is None:
                    raise PatchApplyError(f"replace {p.target_id} without new_criterion")
                c = p.new_criterion.model_copy(deep=True)
                c.id = p.target_id
                lst[idx] = c
            touched.add(p.target_id)
        elif p.target == "scope_decisions":
            if p.op == "add":
                if p.new_scope_decision is None:
                    raise PatchApplyError("add scope_decision without payload")
                new.scope_decisions.append(p.new_scope_decision.model_copy(deep=True))
                touched.add(f"scope:{p.new_scope_decision.topic}")
                continue
            norm = (p.target_id or "").strip().lower()
            idx = next((i for i, s in enumerate(new.scope_decisions)
                        if s.topic.strip().lower() == norm), None)
            if idx is None:
                raise PatchApplyError(f"unknown scope_decision topic {p.target_id!r}")
            if p.op == "remove":
                new.scope_decisions.pop(idx)
            else:
                if p.new_scope_decision is None:
                    raise PatchApplyError(f"replace scope {p.target_id} without payload")
                new.scope_decisions[idx] = p.new_scope_decision.model_copy(deep=True)
            touched.add(f"scope:{p.target_id}")
        elif p.target == "boundary_guidance":
            if p.op == "add":
                if not p.new_text.strip():
                    raise PatchApplyError("add boundary_guidance without new_text")
                new.boundary_guidance.append(p.new_text.strip())
            else:
                try:
                    idx = int(p.target_id) - 1
                    assert 0 <= idx < len(new.boundary_guidance)
                except (ValueError, AssertionError):
                    raise PatchApplyError(f"bad boundary_guidance index {p.target_id!r}")
                if p.op == "remove":
                    new.boundary_guidance.pop(idx)
                else:
                    if not p.new_text.strip():
                        raise PatchApplyError("replace boundary_guidance without new_text")
                    new.boundary_guidance[idx] = p.new_text.strip()
            touched.add("boundary_guidance")
        elif p.target in ("domain_definition", "scope_statement"):
            if not p.new_text.strip():
                raise PatchApplyError(f"{p.target} patch without new_text")
            setattr(new, p.target, p.new_text.strip())
            touched.add(p.target)
        else:
            raise PatchApplyError(f"unknown patch target {p.target!r}")
    return new, touched


def patch_criteria(ws: Workspace, llm: StructuredLLM, scope: QueryScopeOut,
                   digest: CorpusDigestOut, axis_synthesis: AxisSynthesisOut,
                   doc: CriteriaDocOut, issues: list[CritiqueIssue], usage: Usage,
                   version: int,
                   human_qa: list[dict] | None = None
                   ) -> tuple[CriteriaDocOut, set[str], list[str]]:
    """Issue-specific revision: patch ONLY the flagged fields, freeze the rest.
    Returns (doc, touched_field_ids, unresolvable_issue_codes).
    Raises PatchApplyError when the model's patches cannot be applied."""
    from src.agentic.axes import allowed_source_references, render_allowed_refs
    allowed_refs = allowed_source_references(ws, digest)
    human = [qa for qa in (human_qa or [])
             if qa.get("answered_by", "human") in ("human", "human_batch", "human_prior")]
    assumed = [qa for qa in (human_qa or []) if qa not in human]
    parts = [
        f"=== Current criteria document (patch targets) ===\n"
        f"{json.dumps(doc.model_dump(), ensure_ascii=False)}",
        "\n=== UNRESOLVED LEDGER ISSUES (resolve exactly these) ===\n"
        + "\n".join(f"- [{i.issue_code or i.category}] ({i.severity}) {i.field}: "
                    f"{i.problem}\n  suggestion: {i.suggestion}" for i in issues),
        f"\n=== Approved technology-axis synthesis ===\n"
        f"{json.dumps(axis_synthesis.model_dump(), ensure_ascii=False)}",
        "\n=== ALLOWED SOURCE REFERENCES (cite the id exactly) ===\n"
        + render_allowed_refs(ws, digest),
    ]
    if human:
        parts.append("\n=== Human expert answers (authoritative owner decisions) ===\n"
                     + "\n".join(f"Q: {qa['question']}\nA: {qa['answer']}" for qa in human))
    if assumed:
        parts.append("\n=== SYSTEM ASSUMPTIONS (unattended run — NOT owner decisions) ===\n"
                     + "\n".join(f"Q: {qa['question']}\nA(auto): {qa['answer']}"
                                 for qa in assumed))
    out, pt, ct = llm.parse(_PATCH_SYSTEM.format(domain=scope.canonical_name_en),
                            "\n".join(parts), CriteriaPatchOut)
    usage.add(pt, ct)
    if not out.patches and not out.unresolvable_issue_codes:
        raise PatchApplyError("patch reviser returned no patches")
    new_doc, touched = apply_patches(doc, out.patches)
    new_doc.technology_axes = [a.model_copy(deep=True)
                               for a in axis_synthesis.technology_axes]
    repair_criterion_refs(ws, new_doc, allowed_refs)
    save_criteria(ws, new_doc, version)
    ws.append_jsonl(ws.provenance_repairs_jsonl, {
        "stage": "patch", "version": version,
        "patched": sorted(touched),
        "unresolvable": out.unresolvable_issue_codes, "notes": out.notes})
    return new_doc, touched, out.unresolvable_issue_codes


# ----------------------------------------------------------------- rendering / io
def render_md(doc: CriteriaDocOut) -> str:
    """Render the final axis/provenance contract without losing legacy sources."""
    lines = [f"# 특허 도메인 판단 기준서 — {doc.domain_name}", "",
             "## 도메인 정의", "", doc.domain_definition, "",
             "## 기술축", ""]
    for axis in doc.technology_axes:
        lines.append(
            f"### {axis.id}. {axis.name} [{axis.status}/{axis.confidence}]"
        )
        lines += ["", axis.description, "",
                  f"- 사용자 문서 명시: {axis.owner_documented}",
                  f"특허 풀 관찰: {axis.observed_in_corpus}",
                  f"판단 근거: {axis.rationale}", "- 출처:"]
        for ref in axis.source_refs:
            lines.append(
                f"  - [{ref.source_type}/{ref.strength}] {ref.reference}: {ref.claim}"
            )
        lines.append("")

    def add_criteria(title: str, items) -> None:
        lines.extend([f"## {title}", ""])
        for item in items:
            lines.append(f"- **{item.id}.** {item.statement}")
            if item.observable_signals:
                lines.append(f"  - 관찰 신호(비배타적 단서): {', '.join(item.observable_signals)}")
            if item.axis_ids:
                lines.append(f"  - 기술축: {', '.join(item.axis_ids)}")
            for ref in item.source_refs:
                lines.append(
                    f"  - [{ref.source_type}/{ref.strength}] {ref.reference}: {ref.claim}"
                )
            if item.sources:
                lines.append(f"  - 레거시 출처: {', '.join(item.sources)}")

    add_criteria("포함 판단 기준 (C)", doc.domain_criteria)
    lines += ["", "## 분석 대상 특허의 범위", "", doc.scope_statement, "",
              "## 범위 결정", ""]
    for decision in doc.scope_decisions:
        lines.append(
            f"- [{decision.verdict.upper()}] **{decision.topic}** — {decision.rationale}"
        )
    lines.append("")
    add_criteria("제외 판단 기준 (E)", doc.exclusion_criteria)
    lines += ["", "## 경계 판정 지침", ""]
    lines += [f"- {g}" for g in doc.boundary_guidance]
    if doc.open_questions:
        lines += ["", "## HITL이 필요한 범위 질문", ""]
        for q in doc.open_questions:
            lines += [f"- **{q.id}. {q.question}**",
                      f"  - 영향: {q.why_it_matters}",
                      f"  - 선택지: {', '.join(q.options)}",
                      f"  - 미응답 기본값: {q.tentative_default}"]
    return "\n".join(lines).rstrip() + "\n"


def save_criteria(ws: Workspace, doc: CriteriaDocOut, version: int) -> None:
    ws.write_json(ws.criteria_json(version), doc.model_dump())
    ws.criteria_md(version).write_text(render_md(doc), encoding="utf-8")


def save_final(ws: Workspace, doc: CriteriaDocOut) -> None:
    ws.write_json(ws.criteria_final_json, doc.model_dump())
    ws.criteria_final_md.write_text(render_md(doc), encoding="utf-8")
    ws.criteria_blocked_json.unlink(missing_ok=True)


def load_final(ws: Workspace) -> CriteriaDocOut:
    return CriteriaDocOut(**ws.read_json(ws.criteria_final_json))
