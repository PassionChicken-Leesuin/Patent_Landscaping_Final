"""Structured-output schemas (Pydantic) + per-patent graph State (TypedDict).

These import ONLY pydantic + stdlib, so they load locally without langgraph/
langchain for unit testing the deterministic core.
"""
from __future__ import annotations
from typing import Literal, Optional, TypedDict
from typing_extensions import NotRequired

from pydantic import BaseModel, Field

Route = Literal["easy_positive", "easy_negative", "boundary", "hard_negative", "abstain_candidate"]
CandidateType = Literal["positive", "easy_negative", "hard_negative", "boundary", "abstain"]


# ---------------- LLM structured outputs ----------------
class Evidence(BaseModel):
    source: Literal["title", "abstract"]
    exact_text: str
    mapped_task: str
    status: Literal["present", "implied", "absent", "contradicted"]
    strength: int = Field(ge=0, le=3)


class RelevanceOut(BaseModel):
    functional_evidence: list[Evidence] = Field(default_factory=list)
    technical_evidence: list[Evidence] = Field(default_factory=list)
    core_stance: Literal["related", "unrelated", "abstain"]
    core_score: float = Field(ge=0, le=1)
    route: Route


class ExclusionOut(BaseModel):
    exclusion_stance: Literal["not_excluded", "possible_exclusion", "hard_negative"]
    exclusion_risk: float = Field(ge=0, le=1)
    confusable_category: Optional[str] = None
    exclusion_reason: Optional[str] = None


# ---------------- per-patent graph state ----------------
class PatentState(TypedDict):
    # input (one candidate-pool row)
    record_id: str
    patent_id: str
    domain: str
    title: str
    abstract: str
    rubric: dict

    # Stage A
    functional_evidence: NotRequired[list]
    technical_evidence: NotRequired[list]
    core_stance: NotRequired[Literal["related", "unrelated", "abstain"]]
    core_score: NotRequired[float]
    route: NotRequired[Route]

    # Stage B (conditional)
    exclusion_stance: NotRequired[Optional[str]]
    exclusion_risk: NotRequired[Optional[float]]
    confusable_category: NotRequired[Optional[str]]
    exclusion_reason: NotRequired[Optional[str]]

    # Stage C
    final_score: NotRequired[float]
    candidate_type: NotRequired[CandidateType]
