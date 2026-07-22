"""Structured-output schemas for every agentic stage (Pydantic, OpenAI parse-safe).

All fields are fixed (no free-form dicts) because `chat.completions.parse` strict
JSON schema rejects additionalProperties. Imports only pydantic + stdlib.
"""
from __future__ import annotations
from typing import Literal, Optional

from pydantic import BaseModel, Field

IntentType = Literal[
    "definition", "taxonomy_subfields", "core_techniques", "applications",
    "adjacent_out_of_scope", "classification_codes", "terminology_synonyms",
]

INTENT_TYPES: tuple[str, ...] = (
    "definition", "taxonomy_subfields", "core_techniques", "applications",
    "adjacent_out_of_scope", "classification_codes", "terminology_synonyms",
)


# ---------------- [1] scoping ----------------
class SearchIntent(BaseModel):
    intent_type: IntentType
    query_en: str
    rationale: str


class QueryScopeOut(BaseModel):
    canonical_name_en: str
    language_detected: str
    disambiguation_notes: str
    initial_task_hypotheses: list[str]
    search_plan: list[SearchIntent]


# ---------------- [2] research ----------------
EvidenceType = Literal[
    "definition", "task", "technique", "signal_term",
    "confusable", "boundary_case", "cpc_code", "synonym",
]


class EvidenceNote(BaseModel):
    claim: str
    evidence_type: EvidenceType
    quote: str
    confidence: Literal["high", "medium", "low"]
    # source_url is attached in code (never trusted from the LLM)


class EvidenceNotesOut(BaseModel):
    page_is_relevant: bool
    page_is_benchmark_leak: bool
    notes: list[EvidenceNote]


class GapAnalysisOut(BaseModel):
    covered: list[IntentType]
    missing: list[IntentType]
    followup_queries: list[SearchIntent]
    research_complete: bool


# ---------------- [3] corpus reading ----------------
class CorpusBatchDigestOut(BaseModel):
    clusters: list[str]
    recurring_terms: list[str]
    boundary_examples: list[str]     # "title — why it is borderline"


class CorpusDigestOut(BaseModel):
    main_clusters: list[str]
    vocabulary_profile: list[str]
    representative_cases: list[str]
    suspected_boundary_cases: list[str]
    mismatch_with_web_evidence: list[str]


# ---------------- [4] criteria (sentence-form) ----------------
class CriterionOut(BaseModel):
    id: str                          # C1.., E1..
    statement: str                   # full-sentence criterion
    sources: list[str]               # evidence URLs / "corpus: <case>"


class ScopeDecisionOut(BaseModel):
    """Explicit ruling for one technical cluster observed in the judge pool.
    Forces the criteria agent to treat scope breadth as a decision, not a default.
    'conditional' = the cluster exists in both an in-scope and a look-alike form;
    rationale must then state the DECISIVE TEST the judge applies per patent."""
    topic: str                       # cluster / sub-technology name
    verdict: Literal["in", "out", "conditional"]
    rationale: str                   # full sentence, grounded in evidence or corpus


class ScopeQuestion(BaseModel):
    """A scope boundary the criteria author is genuinely unsure about and that would
    change judgments. The author states its own tentative default so the pipeline can
    proceed unattended, but flags it for the human owner. broad_rule/narrow_rule make the
    boundary machine-testable: the pipeline judges a pool sample under each to MEASURE how
    many patents actually flip (replacing the author's guess in why_it_matters)."""
    id: str                          # Q1, Q2, ...
    question: str                    # natural-language question to the human owner
    why_it_matters: str              # measured after probing (author's guess pre-probe)
    options: list[str]               # concrete choices (e.g. ["include", "exclude"])
    tentative_default: str           # the author's current assumption if unanswered
    broad_rule: str                  # one-sentence inclusion rule under the BROAD reading
    narrow_rule: str                 # one-sentence inclusion rule under the NARROW reading


class BoundaryVerdict(BaseModel):
    boundary_id: str
    broad: Literal["in", "out"]      # would this patent be in-domain under broad_rule?
    narrow: Literal["in", "out"]     # ...and under narrow_rule?


class BoundaryProbeOut(BaseModel):
    verdicts: list[BoundaryVerdict]


class BoundaryFeedbackOut(BaseModel):
    """New scope questions inferred from the patents the judge was UNSURE about
    (boundary/abstain/near-0.5). Closes the loop: the pool's own hard cases surface
    the boundaries the criteria author missed."""
    questions: list[ScopeQuestion]


class CriteriaDocOut(BaseModel):
    domain_name: str
    domain_definition: str
    domain_criteria: list[CriterionOut]        # C-ids: inclusion judgment criteria
    scope_statement: str                       # sentence-form scope of analyzed patents
    scope_decisions: list[ScopeDecisionOut]    # per-cluster in/out rulings
    exclusion_criteria: list[CriterionOut]     # E-ids: exclusion criteria
    boundary_guidance: list[str]               # corpus-grounded borderline guidance
    open_questions: list[ScopeQuestion]        # scope calls that need the human owner


# ---------------- [5]/[7] validators + HITL ----------------
class HITLQuestion(BaseModel):
    id: str
    question: str                    # natural-language question to the human
    why_needed: str
    options: list[str]               # suggested answers ([] = free-form)


class CritiqueIssue(BaseModel):
    field: str
    problem: str
    suggestion: str
    severity: Literal["critical", "minor"]   # critical = would change judgments materially


class CriteriaCritiqueOut(BaseModel):
    approved: bool
    issues: list[CritiqueIssue]
    action: Literal["approve", "revise", "collect_more", "ask_human"]
    followup_queries: list[SearchIntent]       # when action == collect_more
    human_questions: list[HITLQuestion]        # when action == ask_human


# ---------------- [6] judgment ----------------
class JudgmentOut(BaseModel):
    matched_criteria: list[str]      # cited C-ids supporting inclusion
    violated_exclusions: list[str]   # cited E-ids supporting exclusion
    stance: Literal["in_domain", "out_of_domain", "boundary", "abstain"]
    score: float = Field(ge=0, le=1)
    rationale: str                   # sentence-form, must reference cited ids


class SecondPassOut(BaseModel):
    confirmed_stance: Literal["in_domain", "out_of_domain", "boundary", "abstain"]
    confirmed_score: float = Field(ge=0, le=1)
    decisive_criterion: str          # the single C/E id that decided the case
    rationale: str


# ---------------- [7] judgment validator ----------------
class JudgeAuditOut(BaseModel):
    verdict_ok: bool
    problem: str
    action: Literal["confirm", "re_judge", "collect_more", "ask_human"]
    followup_queries: list[SearchIntent]
    human_questions: list[HITLQuestion]
    criteria_amendments: list[str]   # sentence-form clarifications to append for re-judging
