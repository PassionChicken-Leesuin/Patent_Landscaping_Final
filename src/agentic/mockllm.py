"""Offline deterministic mock LLM covering every agentic schema (smoke tests only).

Stateful where the pipeline needs it: the first criteria critique demands ask_human
(exercising the HITL path), the second approves. Judgment uses crude keyword rules —
NOT for real labeling, only to exercise the machinery without API keys.
"""
from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
from typing import Type

from pydantic import BaseModel

from src.mas.llm import StructuredLLM
from src.agentic.schemas import (
    AxisSynthesisOut, BoundaryProbeOut, BoundaryVerdict, CorpusBatchDigestOut, CorpusDigestOut,
    CriteriaCritiqueOut, CriteriaDocOut, CriterionOut, EvidenceNote, EvidenceNotesOut,
    EvidenceSourceRef, GapAnalysisOut, HITLQuestion, INTENT_TYPES, JudgeAuditOut, JudgmentOut,
    OwnerDocumentAssessmentOut, QueryScopeOut, ScopeDecisionOut, ScopeQuestion,
    SearchIntent, SecondPassOut, TechnologyAxisOut,
)


@dataclass
class MockAgentLLM(StructuredLLM):
    model: str = "mock-agentic"
    calls: Counter = field(default_factory=Counter)

    def parse(self, system: str, user: str, schema: Type[BaseModel]):
        self.calls[schema.__name__] += 1
        fn = getattr(self, f"_{schema.__name__}", None)
        if fn is None:
            raise ValueError(f"MockAgentLLM: unsupported schema {schema}")
        return fn(system, user), 0, 0

    # ------------------------------------------------------------- [1] scoping
    def _QueryScopeOut(self, system, user):
        q = user.split("User query:", 1)[-1].strip()
        low = q.lower()
        name = "Hydrogen Storage" if ("hydrogen" in low or "수소" in q) else (q.title() or "Example Technology")
        plan = [SearchIntent(intent_type=t, query_en=f"{name} {t.replace('_', ' ')}",
                             rationale=f"cover {t}") for t in INTENT_TYPES]
        return QueryScopeOut(
            canonical_name_en=name, language_detected="ko" if "수소" in q else "en",
            disambiguation_notes=f"interpreted '{q}' as {name}",
            initial_task_hypotheses=[
                f"An invention belongs to {name} if it stores the target substance or state for later use.",
                f"An invention belongs to {name} if it improves capacity, kinetics, or safety of storage.",
                f"Merely using {name} outputs (e.g. consuming stored material) is not the domain task.",
            ],
            search_plan=plan)

    # ------------------------------------------------------------- [2] research
    def _EvidenceNotesOut(self, system, user):
        quote = user[-160:].replace("\n", " ")
        return EvidenceNotesOut(page_is_relevant=True, page_is_benchmark_leak=False, notes=[
            EvidenceNote(claim="The domain concerns storing hydrogen by physical or material-based means.",
                         evidence_type="definition", quote=quote[:180], confidence="high"),
            EvidenceNote(claim="Fuel cells convert stored hydrogen to power and are adjacent, not in-domain.",
                         evidence_type="confusable", quote=quote[:180], confidence="medium"),
        ])

    def _GapAnalysisOut(self, system, user):
        return GapAnalysisOut(covered=list(INTENT_TYPES), missing=[],
                              followup_queries=[], research_complete=True)

    # ------------------------------------------------------------- [3] corpus
    def _CorpusBatchDigestOut(self, system, user):
        return CorpusBatchDigestOut(
            clusters=["high-pressure tanks", "metal hydrides", "adsorption materials"],
            recurring_terms=["hydrogen", "storage", "hydride", "tank", "adsorption"],
            boundary_examples=["Fuel cell stack — mentions hydrogen but converts it rather than stores it"])

    def _CorpusDigestOut(self, system, user):
        return CorpusDigestOut(
            main_clusters=["compressed-gas tanks", "metal hydrides", "sorbent materials"],
            vocabulary_profile=["hydrogen storage", "hydride", "tank", "adsorbent", "desorption"],
            representative_cases=["Metal hydride hydrogen storage vessel"],
            suspected_boundary_cases=[
                "Fuel-cell patents mention hydrogen supply but perform conversion, not storage (e.g. 'Fuel cell stack')."],
            mismatch_with_web_evidence=[
                "The pool contains many vessel-engineering patents while web evidence emphasizes materials research."])

    # ------------------------------------------------------------- [4a] axes
    def _AxisSynthesisOut(self, system, user):
        web = EvidenceSourceRef(
            source_type="web", reference="https://www.energy.gov/eere/fuelcells/hydrogen-storage",
            claim="Hydrogen can be stored physically or in materials.", strength="high")
        corpus = EvidenceSourceRef(
            source_type="corpus", reference="corpus: compressed-gas tanks",
            claim="The patent pool repeatedly contains vessel and material storage inventions.",
            strength="high")
        query = EvidenceSourceRef(
            source_type="user_query", reference="query.json",
            claim="The requested domain is hydrogen storage technology.", strength="high")
        return AxisSynthesisOut(
            owner_document_assessment=OwnerDocumentAssessmentOut(
                present=False, overall_quality="none", scope_clarity="none",
                technical_completeness="none", factual_reliability="none",
                strengths=[], gaps=["No owner document supplied."], conflicts=[]),
            technology_axes=[
                TechnologyAxisOut(
                    id="A1", name="Physical storage", description="Compressed or liquefied storage.",
                    status="core", confidence="high", owner_documented=False,
                    observed_in_corpus=True, source_refs=[query, web, corpus],
                    rationale="Query, research, and pool evidence converge.", boundary_examples=[]),
                TechnologyAxisOut(
                    id="A2", name="Material storage", description="Hydrides and sorbents.",
                    status="core", confidence="high", owner_documented=False,
                    observed_in_corpus=True, source_refs=[web, corpus],
                    rationale="Research and pool evidence converge.", boundary_examples=[]),
                TechnologyAxisOut(
                    id="A3", name="Charging and release", description="Mechanisms for uptake and release.",
                    status="supplemental", confidence="medium", owner_documented=False,
                    observed_in_corpus=True, source_refs=[corpus],
                    rationale="A repeated enabling mechanism in the pool.", boundary_examples=[]),
            ], unresolved_conflicts=[])

    # ------------------------------------------------------------- [4b] criteria
    def _CriteriaDocOut(self, system, user):
        web_ref = EvidenceSourceRef(
            source_type="web", reference="https://www.energy.gov/eere/fuelcells/hydrogen-storage",
            claim="Hydrogen storage includes physical and material-based approaches.", strength="high")
        corpus_ref = EvidenceSourceRef(
            source_type="corpus", reference="corpus: compressed-gas tanks",
            claim="The pool contains storage vessels and material charge/release mechanisms.",
            strength="high")
        C = [CriterionOut(id="C1", statement="The invention stores hydrogen physically (compressed or liquefied) or in a material, as its primary function.",
                          sources=[web_ref.reference], axis_ids=["A1", "A2"], source_refs=[web_ref]),
             CriterionOut(id="C2", statement="The invention improves capacity, kinetics, cycling, or safety of a hydrogen storage system or material.",
                          sources=[web_ref.reference], axis_ids=["A1", "A2"], source_refs=[web_ref]),
             CriterionOut(id="C3", statement="The invention concerns charging or releasing hydrogen from a storage medium as a described mechanism.",
                          sources=[corpus_ref.reference], axis_ids=["A3"], source_refs=[corpus_ref])]
        E = [CriterionOut(id="E1", statement="Patents that consume or convert hydrogen (fuel cells, combustion) without storing it are excluded even if they mention storage.",
                          sources=["corpus: Fuel cell stack"], axis_ids=["A1"], source_refs=[corpus_ref]),
             CriterionOut(id="E2", statement="Patents with no hydrogen-related signal at all are excluded as out of domain.",
                          sources=[web_ref.reference], axis_ids=["A1", "A2"], source_refs=[web_ref])]
        return CriteriaDocOut(
            domain_name="Hydrogen Storage",
            domain_definition="Hydrogen storage covers inventions whose primary function is to hold hydrogen for later use by physical or material-based means.",
            domain_criteria=C,
            scope_statement="Analysis covers patents whose title and abstract describe storing hydrogen or storage materials, vessels, and their charge/discharge mechanisms.",
            scope_decisions=[
                ScopeDecisionOut(topic="compressed-gas tanks", verdict="in",
                                 rationale="Physical storage is a core defining task per the evidence."),
                ScopeDecisionOut(topic="fuel cells", verdict="out",
                                 rationale="Conversion of stored hydrogen, not storage itself.")],
            # first draft raises a scope question; the post-answer revision returns none
            open_questions=([ScopeQuestion(
                id="Q1",
                question="수소 생산·연료전지 공급계 특허를 저장 도메인에 포함할까요?",
                why_it_matters="풀의 상당수 특허가 생산·공급계라 판정이 크게 갈립니다.",
                options=["포함", "제외"],
                tentative_default="제외",
                broad_rule="Include any patent whose invention handles, produces, supplies, or converts hydrogen.",
                narrow_rule="Include only patents whose primary function is storing hydrogen.")]
                if self.calls["CriteriaDocOut"] == 1 else []),
            exclusion_criteria=E,
            boundary_guidance=["If a patent mentions hydrogen supply to a fuel cell, judge whether storage itself is the claimed contribution (C1) or mere context (E1)."])

    def _CriteriaPatchOut(self, system, user):
        """Replace each criterion named in the ledger issues; leave the rest frozen."""
        import json as _json
        import re as _re
        from src.agentic.schemas import CriteriaFieldPatch, CriteriaPatchOut
        doc_part = user.split("=== Current criteria document (patch targets) ===", 1)[-1]
        doc_json = doc_part.split("\n=== UNRESOLVED", 1)[0].strip()
        issues_part = user.split("=== UNRESOLVED LEDGER ISSUES", 1)[-1].split("\n===", 1)[0]
        try:
            doc = CriteriaDocOut(**_json.loads(doc_json))
        except Exception:
            return CriteriaPatchOut(patches=[], unresolvable_issue_codes=["MOCK:PARSE"],
                                    notes="mock could not parse the document")
        by_id = {c.id: (c, "domain_criteria") for c in doc.domain_criteria}
        by_id.update({e.id: (e, "exclusion_criteria") for e in doc.exclusion_criteria})
        patches = []
        for cid in dict.fromkeys(_re.findall(r"\b([CE]\d+)\b", issues_part)):
            if cid not in by_id:
                continue
            crit, target = by_id[cid]
            fixed = crit.model_copy(deep=True)
            if not fixed.observable_signals:
                fixed.observable_signals = ["hydrogen storage", "hydride", "tank"]
            fixed.statement = fixed.statement.rstrip(".") + ", as evidenced in the text."
            patches.append(CriteriaFieldPatch(
                issue_codes=[f"MOCK:{cid}"], target=target, op="replace",
                target_id=cid, new_criterion=fixed, rationale="mock targeted fix"))
        if not patches:
            return CriteriaPatchOut(patches=[], unresolvable_issue_codes=["MOCK:NONE"],
                                    notes="no criterion ids named in the issues")
        return CriteriaPatchOut(patches=patches)

    def _IssueResolutionOut(self, system, user):
        from src.agentic.schemas import IssueResolutionOut
        return IssueResolutionOut(resolved=True, evidence="mock verification")

    def _CriteriaCritiqueOut(self, system, user):
        first = self.calls["CriteriaCritiqueOut"] == 1
        if first:
            return CriteriaCritiqueOut(
                approved=False, issues=[], action="ask_human",
                followup_queries=[],
                human_questions=[HITLQuestion(
                    id="HQ1",
                    question="수소 '운송'(파이프라인·튜브트레일러) 특허를 저장 도메인에 포함할까요?",
                    why_needed="웹 근거와 특허 풀에서 저장과 운송의 경계가 갈립니다.",
                    options=["포함", "제외"])])
        return CriteriaCritiqueOut(approved=True, issues=[], action="approve",
                                   followup_queries=[], human_questions=[])

    # ------------------------------------------------------------- boundary probe
    def _BoundaryProbeOut(self, system, user):
        # keyword-detect only the PATENT text (the boundary rules mention both readings)
        bounds_part, _, patent_part = user.partition("PATENT")
        t = patent_part.lower()
        supply = any(k in t for k in ("production", "generat", "fuel cell", "supply", "recover"))
        store = any(k in t for k in ("storage", "hydride", "tank", "adsorb", "vessel"))
        verdicts = []
        for line in bounds_part.splitlines():
            line = line.strip()
            if line.startswith("[") and "]" in line:
                bid = line[1:line.index("]")]
                if supply and not store:
                    verdicts.append(BoundaryVerdict(boundary_id=bid, broad="in", narrow="out"))
                else:
                    v = "in" if store else "out"
                    verdicts.append(BoundaryVerdict(boundary_id=bid, broad=v, narrow=v))
        return BoundaryProbeOut(verdicts=verdicts)

    # ------------------------------------------------------------- [3] closed loop
    def _BoundaryFeedbackOut(self, system, user):
        from src.agentic.schemas import BoundaryFeedbackOut
        return BoundaryFeedbackOut(questions=[ScopeQuestion(
            id="F1",
            question="경계 특허(연료전지 수소 공급계)를 저장 도메인에 포함할까요?",
            why_it_matters="판정 불확실 특허 다수가 공급계입니다.",
            options=["포함", "제외"], tentative_default="제외",
            broad_rule="Include any patent handling or supplying hydrogen.",
            narrow_rule="Include only patents storing hydrogen.")])

    # ------------------------------------------------------------- [6] judgment
    def _JudgmentOut(self, system, user):
        _, _, patent = user.partition("PATENT")
        t = patent.lower()
        store = any(k in t for k in ("storage", "storing", "hydride", "tank", "adsorb", "vessel"))
        hydro = "hydrogen" in t
        if hydro and store:
            return JudgmentOut(matched_criteria=["C1"], violated_exclusions=[],
                               stance="in_domain", relevance_score=0.9,
                               decision_confidence=0.92,
                               rationale="Stores hydrogen as primary function, satisfying C1.")
        if hydro:
            return JudgmentOut(matched_criteria=[], violated_exclusions=["E1"],
                               stance="boundary", relevance_score=0.5,
                               decision_confidence=0.45,
                               rationale="Mentions hydrogen but storage is not clearly the contribution (E1 risk).")
        return JudgmentOut(matched_criteria=[], violated_exclusions=["E2"],
                           stance="out_of_domain", relevance_score=0.1,
                           decision_confidence=0.95,
                           rationale="No hydrogen storage signal; E2 applies.")

    def _SecondPassOut(self, system, user):
        _, _, patent = user.partition("PATENT")
        t = patent.split("FIRST-PASS JUDGMENT", 1)[0].lower()
        if "storage" in t or "hydride" in t:
            return SecondPassOut(confirmed_stance="in_domain",
                                 confirmed_matched_criteria=["C1"],
                                 confirmed_violated_exclusions=[],
                                 confirmed_relevance_score=0.85,
                                 confirmed_decision_confidence=0.9,
                                 decisive_criterion="C1", rationale="Storage mechanism is the claimed contribution.")
        return SecondPassOut(confirmed_stance="out_of_domain",
                             confirmed_matched_criteria=[],
                             confirmed_violated_exclusions=["E1"],
                             confirmed_relevance_score=0.2,
                             confirmed_decision_confidence=0.88,
                             decisive_criterion="E1", rationale="Conversion, not storage, is the contribution.")

    # ------------------------------------------------------------- [7] judge audit
    def _JudgeAuditOut(self, system, user):
        return JudgeAuditOut(verdict_ok=True, problem="", action="confirm",
                             followup_queries=[], human_questions=[],
                             criteria_amendments=[])
