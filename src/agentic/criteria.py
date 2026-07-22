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
from src.agentic.schemas import (CriteriaCritiqueOut, CriteriaDocOut, CorpusDigestOut,
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
    "Output JSON only."
)

_OWNER_CLAUSE = (
    "\nOWNER DOMAIN DEFINITION — the user message contains a document written by the DOMAIN "
    "OWNER (the person whose scope intent this criteria document must encode). It is the TOP "
    "AUTHORITY: wherever it conflicts with web evidence, corpus impressions, or your own "
    "knowledge, the owner definition WINS. Anchor the domain_definition and the C-criteria "
    "skeleton to it; every technology axis it names MUST be covered by at least one "
    "C-criterion, and every scope_decision must be consistent with its stated "
    "inclusion/boundary intent. Where the owner document explicitly defers a boundary to the "
    "owner's decision, that boundary is a prime open_questions candidate. Cite it in sources "
    "as 'owner_doc: <document name>'.\n"
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
                   digest: CorpusDigestOut, evidence_summary: str, usage: Usage,
                   version: int = 1,
                   prior: CriteriaDocOut | None = None,
                   critique: CriteriaCritiqueOut | None = None,
                   human_qa: list[dict] | None = None) -> CriteriaDocOut:
    system = _SYSTEM.format(domain=scope.canonical_name_en) + _scope_clause()
    parts = [f"User query: {scope.canonical_name_en} ({scope.disambiguation_notes})",
             f"Initial task hypotheses:\n" + "\n".join(f"- {t}" for t in scope.initial_task_hypotheses),
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
    if prior is not None:
        system += _REVISE_SUFFIX
        parts.append(f"\n=== Previous document ===\n{json.dumps(prior.model_dump(), ensure_ascii=False)}")
    if critique is not None:
        parts.append(f"\n=== Validator critique ===\n{json.dumps(critique.model_dump(), ensure_ascii=False)}")
    if human_qa:
        parts.append("\n=== Human expert answers (authoritative) ===\n"
                     + "\n".join(f"Q: {qa['question']}\nA: {qa['answer']}" for qa in human_qa))

    out, pt, ct = llm.parse(system, "\n".join(parts), CriteriaDocOut)
    usage.add(pt, ct)
    out = _renumber(out)
    save_criteria(ws, out, version)
    return out


def resolve_open_questions(ws: Workspace, llm: StructuredLLM, scope: QueryScopeOut,
                           digest: CorpusDigestOut, evidence_summary: str,
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
    qa = hitl.ask(questions, context=f"{scope.canonical_name_en} 기준 작성 중 범위 결정")
    # if the human just accepted every default (or off-mode auto-answers), no revision needed
    doc2 = draft_criteria(ws, llm, scope, digest, evidence_summary, usage,
                          version=version + 1, prior=doc, human_qa=qa)
    return doc2, qa


# ----------------------------------------------------------------- rendering / io
def render_md(doc: CriteriaDocOut) -> str:
    lines = [f"# 도메인 판단 기준서 — {doc.domain_name}", "",
             "## 도메인 정의", doc.domain_definition, "",
             "## 도메인 판단 기준 (C)", ""]
    for c in doc.domain_criteria:
        lines.append(f"- **{c.id}.** {c.statement}")
        if c.sources:
            lines.append(f"  - 근거: {', '.join(c.sources)}")
    lines += ["", "## 분석 대상 특허의 범위", doc.scope_statement, "",
              "## 범위 결정 (클러스터별 in/out)", ""]
    for s in doc.scope_decisions:
        lines.append(f"- [{s.verdict.upper()}] **{s.topic}** — {s.rationale}")
    lines += ["", "## 제외 기준 (E)", ""]
    for e in doc.exclusion_criteria:
        lines.append(f"- **{e.id}.** {e.statement}")
        if e.sources:
            lines.append(f"  - 근거: {', '.join(e.sources)}")
    lines += ["", "## 경계 판정 지침", ""]
    lines += [f"- {g}" for g in doc.boundary_guidance]
    if doc.open_questions:
        lines += ["", "## 사용자 결정이 필요한 범위 질문", ""]
        for q in doc.open_questions:
            lines.append(f"- **{q.id}. {q.question}**")
            lines.append(f"  - 영향: {q.why_it_matters}")
            lines.append(f"  - 선택지: {', '.join(q.options)}")
            lines.append(f"  - 현재 가정(미답변 시): {q.tentative_default}")
    return "\n".join(lines) + "\n"


def save_criteria(ws: Workspace, doc: CriteriaDocOut, version: int) -> None:
    ws.write_json(ws.criteria_json(version), doc.model_dump())
    ws.criteria_md(version).write_text(render_md(doc), encoding="utf-8")


def save_final(ws: Workspace, doc: CriteriaDocOut) -> None:
    ws.write_json(ws.criteria_final_json, doc.model_dump())
    ws.criteria_final_md.write_text(render_md(doc), encoding="utf-8")


def load_final(ws: Workspace) -> CriteriaDocOut:
    return CriteriaDocOut(**ws.read_json(ws.criteria_final_json))
