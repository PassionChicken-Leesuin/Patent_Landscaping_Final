"""Structured-output schemas for every agentic stage (Pydantic, OpenAI parse-safe).

All fields are fixed (no free-form dicts) because `chat.completions.parse` strict
JSON schema rejects additionalProperties. Imports only pydantic + stdlib.
"""
from __future__ import annotations
from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

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
# Unified evidence vocabulary shared by research notes (EvidenceType) and the web<->pool
# alignment, so the two are formally comparable rather than ad-hoc text.
EvidenceDimension = Literal[
    "definition", "task", "technique", "signal_term",
    "confusable", "boundary", "cpc_code", "synonym",
]
AlignmentRelation = Literal["confirmed", "web_only", "pool_only", "conflict"]
CriterionImplication = Literal["inclusion", "exclusion", "scope_boundary", "none"]


class EvidenceAlignment(BaseModel):
    """One auditable web<->pool comparison. Ties specific web-evidence note ids to specific
    corpus-finding ids under a typed relation, so every inclusion/exclusion criterion can be
    traced to a concrete comparison (see validator EXCL_FROM_ALIGN / ALIGN_RESOLVE)."""
    id: str                              # "align:1", "align:2" — citable like corpus:/web:
    dimension: EvidenceDimension
    relation: AlignmentRelation
    web_refs: list[str]                  # ["web:3", ...] research-note ids
    pool_refs: list[str]                 # ["corpus:cluster:2", ...] corpus-finding ids
    statement: str                       # one sentence describing the comparison
    implies: CriterionImplication        # what criterion kind this comparison motivates


class CorpusBatchDigestOut(BaseModel):
    clusters: list[str]
    vocabulary: list[str]                # renamed from recurring_terms (unified naming)
    boundary_examples: list[str]         # "title — why it is borderline"


class CorpusReduceOut(BaseModel):
    """Parse target for the corpus REDUCE call 1 (core digest, no alignment)."""
    clusters: list[str]
    vocabulary: list[str]
    representative_examples: list[str]
    boundary_examples: list[str]


class AlignmentOut(BaseModel):
    """Parse target for the corpus REDUCE call 2 (web<->pool alignment rows)."""
    alignment: list[EvidenceAlignment]


class CorpusDigestOut(BaseModel):
    """Final corpus digest. New unified field names; old cached JSON still loads via aliases,
    and legacy readers keep working via the compat @property shims below."""
    model_config = ConfigDict(populate_by_name=True)
    clusters: list[str] = Field(default_factory=list,
                                validation_alias=AliasChoices("clusters", "main_clusters"))
    vocabulary: list[str] = Field(default_factory=list,
                                  validation_alias=AliasChoices("vocabulary", "vocabulary_profile"))
    representative_examples: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("representative_examples", "representative_cases"))
    boundary_examples: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("boundary_examples", "suspected_boundary_cases"))
    alignment: list[EvidenceAlignment] = Field(default_factory=list)
    # deprecated free-text contrast, superseded by `alignment`; kept so old JSON round-trips
    mismatch_with_web_evidence: list[str] = Field(default_factory=list)

    # backward-compat attribute access for un-migrated readers
    @property
    def main_clusters(self) -> list[str]: return self.clusters
    @property
    def vocabulary_profile(self) -> list[str]: return self.vocabulary
    @property
    def representative_cases(self) -> list[str]: return self.representative_examples
    @property
    def suspected_boundary_cases(self) -> list[str]: return self.boundary_examples


# ---------------- [4] technology-axis synthesis + criteria ----------------
SourceType = Literal["user_query", "owner_doc", "web", "corpus", "alignment", "hitl"]


class EvidenceSourceRef(BaseModel):
    """One auditable source supporting an axis or a C/E criterion."""
    source_type: SourceType
    reference: str                  # URL, local://..., corpus case, query, or HITL id
    claim: str                      # the exact proposition this source supports
    strength: Literal["high", "medium", "low"]


class OwnerDocumentAssessmentOut(BaseModel):
    """Quality is assessed independently from the owner's scope authority."""
    present: bool
    overall_quality: Literal["high", "medium", "low", "none"]
    scope_clarity: Literal["high", "medium", "low", "none"]
    technical_completeness: Literal["high", "medium", "low", "none"]
    factual_reliability: Literal["high", "medium", "low", "none"]
    strengths: list[str]
    gaps: list[str]
    conflicts: list[str]


class TechnologyAxisOut(BaseModel):
    id: str                          # A1, A2, ...
    name: str
    description: str
    status: Literal["core", "supplemental", "disputed", "excluded"]
    confidence: Literal["high", "medium", "low"]
    owner_documented: bool
    observed_in_corpus: bool
    source_refs: list[EvidenceSourceRef]
    rationale: str
    boundary_examples: list[str]


class AxisSynthesisOut(BaseModel):
    owner_document_assessment: OwnerDocumentAssessmentOut
    technology_axes: list[TechnologyAxisOut]
    unresolved_conflicts: list[str]


class CriterionOut(BaseModel):
    id: str                          # C1.., E1..
    statement: str                   # full-sentence criterion
    sources: list[str]               # evidence URLs / "corpus: <case>"
    axis_ids: list[str] = Field(default_factory=list)
    source_refs: list[EvidenceSourceRef] = Field(default_factory=list)
    # Non-exclusive title/abstract cues that indicate the criterion MAY apply.
    # They make testability concrete; absence of a signal alone never excludes.
    observable_signals: list[str] = Field(default_factory=list)


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


class ScopeQuestionsOut(BaseModel):
    """Scope issues the validator raised, restated as testable broad/narrow boundaries
    so they can be measured on the pool and shown as decision cards — the same shape
    the criteria author's own open questions take."""
    questions: list[ScopeQuestion]


class BoundaryFeedbackOut(BaseModel):
    """New scope questions inferred from the patents the judge was UNSURE about
    (boundary/abstain/low decision confidence). Closes the loop: the pool's hard cases surface
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
    technology_axes: list[TechnologyAxisOut] = Field(default_factory=list)
    owner_document_assessment: Optional[OwnerDocumentAssessmentOut] = None


# ---------------- [5]/[7] validators + HITL ----------------
class HITLQuestion(BaseModel):
    id: str
    question: str                    # natural-language question to the human
    why_needed: str
    options: list[str]               # suggested answers ([] = free-form)


class CardedHITLQuestion(HITLQuestion):
    """A question OUR OWN code raises, carrying the self-contained decision card
    (stake / include·exclude argument + example patents / recommendation / measured
    impact) so the UI always renders the unified card without depending on a fragile
    decisions.json id-join.

    The card lives here and NOT on HITLQuestion because HITLQuestion is embedded in
    LLM response schemas (CriteriaCritiqueOut, JudgeAuditOut), and strict JSON-schema
    parsing rejects free-form dicts — see this module's docstring. The LLM never
    produces a card; only decisions.as_hitl_questions and criteria.resolve_open_questions
    attach one."""
    card: Optional[dict] = None


IssueCategory = Literal["testability", "coverage", "provenance", "consistency",
                        "scope_decision", "definition", "other"]


class CritiqueIssue(BaseModel):
    field: str
    problem: str
    suggestion: str
    severity: Literal["critical", "minor"]   # critical = would change judgments materially
    # Structural identity for the cross-round ledger (prose wording drifts each round).
    category: IssueCategory = "other"
    target_ids: list[str] = Field(default_factory=list)  # C/E/A ids or scope topics
    issue_code: str = ""             # "CATEGORY:TARGET", stable across rounds


class CriteriaCritiqueOut(BaseModel):
    approved: bool
    issues: list[CritiqueIssue]
    action: Literal["approve", "revise", "collect_more", "ask_human"]
    followup_queries: list[SearchIntent]       # when action == collect_more
    human_questions: list[HITLQuestion]        # when action == ask_human


# ---------------- [5b] issue-specific criteria patching ----------------
class CriteriaFieldPatch(BaseModel):
    """One targeted edit addressing specific ledger issues; everything not named
    here stays byte-identical (whole-document redrafts churn unrelated fields)."""
    issue_codes: list[str]           # ledger codes this patch resolves
    target: Literal["domain_criteria", "exclusion_criteria", "scope_decisions",
                    "boundary_guidance", "domain_definition", "scope_statement"]
    op: Literal["replace", "add", "remove"]
    target_id: str                   # criterion id / scope topic / 1-based guidance index; "" for prose fields
    new_criterion: Optional[CriterionOut] = None       # criteria targets
    new_scope_decision: Optional[ScopeDecisionOut] = None
    new_text: str = ""               # prose targets / boundary_guidance
    rationale: str = ""


class CriteriaPatchOut(BaseModel):
    patches: list[CriteriaFieldPatch]
    unresolvable_issue_codes: list[str] = Field(default_factory=list)  # need human/evidence
    notes: str = ""


class IssueResolutionOut(BaseModel):
    """Blind per-issue verification by a fresh judge (no ledger in context) —
    breaks the anchoring loop where a critic re-reports an already-fixed issue."""
    resolved: bool
    evidence: str                    # the exact criterion/section that resolves it


class PriorRulingMatch(BaseModel):
    question_id: str
    settled_by_prior_index: int      # index into the prior-rulings list; -1 = new boundary
    rationale: str


class PriorRulingMatchOut(BaseModel):
    """Semantic dedup of newly proposed scope questions against the run's existing
    human rulings (exact-text reuse cannot catch reworded re-asks of a settled
    boundary — observed in the A2 boundary loop, 2026-07-22)."""
    matches: list[PriorRulingMatch]


# ---------------- [6] judgment ----------------
class JudgmentOut(BaseModel):
    matched_criteria: list[str]      # cited C-ids supporting inclusion
    violated_exclusions: list[str]   # cited E-ids supporting exclusion
    stance: Literal["in_domain", "out_of_domain", "boundary", "abstain"]
    relevance_score: float = Field(ge=0, le=1)  # ranking/AUC, never the inclusion rule
    decision_confidence: float = Field(ge=0, le=1)  # confidence in the stated stance
    rationale: str                   # sentence-form, must reference cited ids


class SecondPassOut(BaseModel):
    confirmed_stance: Literal["in_domain", "out_of_domain", "boundary", "abstain"]
    confirmed_matched_criteria: list[str]
    confirmed_violated_exclusions: list[str]
    confirmed_relevance_score: float = Field(ge=0, le=1)
    confirmed_decision_confidence: float = Field(ge=0, le=1)
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


# ================= case-mapping-based criteria authoring (front-half) =================
# The stages below replace the single-shot criteria draft with the procedure a human
# domain owner and the assistant used to build the humanoid A2 gold set:
#   [3.5] alignment diagnosis -> [4a] design plan -> [4b-map] category case-mapping
#   (with self-correction) -> [4c] decision cards (HITL) -> [4d] initial criteria.
# The back-half ([5] validator loop, [6] judge, [7] judge validator) is unchanged;
# its contract is CriteriaDocOut, which these stages feed but never alter.

# ---------------- [3.5] alignment diagnosis ----------------
class NameCount(BaseModel):
    name: str
    count: int


class PlayerCoverage(BaseModel):
    name: str            # a key player named by the reference material / research
    in_pool: int         # how many pool patents that normalized name authored


class PoolProfile(BaseModel):
    """Code-computed quantitative profile of the judge pool (never an LLM output).
    Domain-general: every metric degrades gracefully when a column is absent."""
    n_total: int
    n_family_dedup: int
    family_dup_rows: int
    ai_summary_fill_rate: float                       # richer-text columns available?
    direct_domain_terms: list[str] = Field(default_factory=list)   # from diagnosis LLM
    direct_domain_mention: int = 0                    # rows whose text hits a direct term
    direct_domain_pct: float = 0.0
    top_assignees: list[NameCount] = Field(default_factory=list)
    top10_assignee_share: float = 0.0                # assignee concentration (general)
    nationality_dist: list[NameCount] = Field(default_factory=list)
    cpc_main_dist: list[NameCount] = Field(default_factory=list)
    reference_player_coverage: list[PlayerCoverage] = Field(default_factory=list)


class AlignmentDiagnosisOut(BaseModel):
    """LLM interpretation of the pool profile vs the owner/reference material.
    Emits the direct-domain terms and key players the code then counts (auditable),
    and judges whether the supplied material is enough or web research is needed."""
    problem_understanding: str                       # (1) the task / problem
    reference_understanding: str                     # (2) the core reference material
    direct_domain_terms: list[str]                   # literal terms = direct domain hit
    reference_key_players: list[str]                 # companies/orgs named by the material
    alignment_notes: list[str]                       # (3) alignment diagnosis, boundary flags
    sufficiency: Literal["sufficient", "need_web"]
    gaps: list[str]                                  # if need_web: what to search for


# ---------------- [4a] design plan (tiers anchored to axes) ----------------
class DesignTier(BaseModel):
    tier: Literal["T1", "T2", "E"]
    name: str
    axis_ids: list[str]                              # anchoring technology axes (A1..)
    definition: str
    expected_signals: list[str]                      # title/abstract cues
    est_count_lo: int
    est_count_hi: int


class DesignPlanOut(BaseModel):
    tiers: list[DesignTier]
    judging_unit: str                                # e.g. "family representative"
    notes: list[str]


# ---------------- [4b-map] category case-mapping ----------------
class CaseRow(BaseModel):
    patent_id: str
    assignee: str
    gist: str                                        # short title gist
    verdict: Literal["confirmed", "boundary", "false_positive"]
    tier: str                                        # T1/T2/E (recommended assignment; "" if none)
    basis: str                                       # basis / what is ambiguous / why false-positive
    recommendation: str                              # boundary rows: recommended tier + reason


class CaseMapCategoryOut(BaseModel):
    category: str                                    # e.g. "T1_direct" / "E_surgical"
    confirmed: list[CaseRow]
    boundary: list[CaseRow]
    false_positive: list[CaseRow]
    false_positive_cues: list[str]                   # 'recycling != rehab' style exclusion cues


class CaseMapReviseOut(BaseModel):
    """One self-correction step over an already-drafted category (shown live in the UI)."""
    changed: list[CaseRow]                           # rows whose verdict/tier changed
    rationale: str                                   # why the reclassification
    settled: bool                                    # True = no further change needed


class CaseInsight(BaseModel):
    title: str                                       # e.g. "OEM must be split 3 ways"
    detail: str
    evidence_ids: list[str]                          # patent_ids supporting it


class CaseMapSummaryOut(BaseModel):
    representative_confirmed: list[CaseRow]          # a few strong confirmations per category
    insights: list[CaseInsight]
    false_positive_cues: list[str]                   # merged, deduped across categories


# ---------------- [4c] decision cards (rich HITL) ----------------
class DecisionQuestion(BaseModel):
    """A boundary decision framed for the human owner the way the assistant framed the
    4족 / 물류학습 / 산업용 회색지대 calls: stake, both arguments with example patents,
    measured impact, and a recommendation. broad_rule/narrow_rule stay machine-testable
    so boundary_probe can MEASURE impact_flips (reused, not re-implemented)."""
    id: str
    stake: str                                       # 쟁점: what the decision is about
    include_argument: str
    include_examples: list[str]                      # patent_ids for the include side
    exclude_argument: str
    exclude_examples: list[str]                      # patent_ids for the exclude side
    impact_flips: int                                # measured by boundary_probe
    impact_sample_n: int
    recommendation: str                              # 권고안
    options: list[str]
    tentative_default: str
    broad_rule: str
    narrow_rule: str


class DecisionQuestionsOut(BaseModel):
    questions: list[DecisionQuestion]


class DecisionEnrichOut(BaseModel):
    """Enriches a criteria-loop scope question into the same decision-card shape as [4c]
    (Korean), so every human scope decision shares one UI and one logic."""
    stake: str
    include_argument: str
    include_examples: list[str]
    exclude_argument: str
    exclude_examples: list[str]
    recommendation: str


# ---------------- [6.5] Tier-B boundary specialist ----------------
class BoundaryJudgeOut(BaseModel):
    """Claim-scope verdict for one contested look-alike patent, reasoned from the
    representative CLAIM against the case-mapping IN/OUT exemplars and the decisive test."""
    in_domain: bool
    claim_is_process_bound: bool     # is the claim tied to a specific excluded use/process?
    decisive_factor: str             # the one claim feature that settled it
    closest_anchor: str              # the exemplar patent_id it most resembles
    confidence: float                # 0..1, genuinely calibrated for this hard case
    rationale: str
