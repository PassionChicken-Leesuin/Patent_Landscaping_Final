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
    BoundaryProbeOut, BoundaryVerdict, CorpusBatchDigestOut, CorpusDigestOut,
    CriteriaCritiqueOut, CriteriaDocOut, CriterionOut, EvidenceNote, EvidenceNotesOut,
    GapAnalysisOut, HITLQuestion, INTENT_TYPES, JudgeAuditOut, JudgmentOut,
    QueryScopeOut, ScopeDecisionOut, ScopeQuestion, SearchIntent, SecondPassOut,
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

    # ------------------------------------------------------------- [4] criteria
    def _CriteriaDocOut(self, system, user):
        C = [CriterionOut(id="C1", statement="The invention stores hydrogen physically (compressed or liquefied) or in a material, as its primary function.",
                          sources=["https://en.wikipedia.org/wiki/Hydrogen_storage"]),
             CriterionOut(id="C2", statement="The invention improves capacity, kinetics, cycling, or safety of a hydrogen storage system or material.",
                          sources=["https://www.energy.gov/eere/fuelcells/hydrogen-storage"]),
             CriterionOut(id="C3", statement="The invention concerns charging or releasing hydrogen from a storage medium as a described mechanism.",
                          sources=["corpus: Metal hydride hydrogen storage vessel"])]
        E = [CriterionOut(id="E1", statement="Patents that consume or convert hydrogen (fuel cells, combustion) without storing it are excluded even if they mention storage.",
                          sources=["corpus: Fuel cell stack"]),
             CriterionOut(id="E2", statement="Patents with no hydrogen-related signal at all are excluded as out of domain.",
                          sources=[])]
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
        t = user.lower()
        store = any(k in t for k in ("storage", "storing", "hydride", "tank", "adsorb", "vessel"))
        hydro = "hydrogen" in t
        if hydro and store:
            return JudgmentOut(matched_criteria=["C1"], violated_exclusions=[],
                               stance="in_domain", score=0.9,
                               rationale="Stores hydrogen as primary function, satisfying C1.")
        if hydro:
            return JudgmentOut(matched_criteria=[], violated_exclusions=["E1"],
                               stance="boundary", score=0.5,
                               rationale="Mentions hydrogen but storage is not clearly the contribution (E1 risk).")
        return JudgmentOut(matched_criteria=[], violated_exclusions=["E2"],
                           stance="out_of_domain", score=0.1,
                           rationale="No hydrogen storage signal; E2 applies.")

    def _SecondPassOut(self, system, user):
        t = user.lower()
        if "storage" in t or "hydride" in t:
            return SecondPassOut(confirmed_stance="in_domain", confirmed_score=0.85,
                                 decisive_criterion="C1", rationale="Storage mechanism is the claimed contribution.")
        return SecondPassOut(confirmed_stance="out_of_domain", confirmed_score=0.2,
                             decisive_criterion="E1", rationale="Conversion, not storage, is the contribution.")

    # ------------------------------------------------------------- [7] judge audit
    def _JudgeAuditOut(self, system, user):
        return JudgeAuditOut(verdict_ok=True, problem="", action="confirm",
                             followup_queries=[], human_questions=[],
                             criteria_amendments=[])
