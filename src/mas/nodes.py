"""Nodes A/B + per-patent orchestration (mirrors the LangGraph design exactly).

process_patent = Node A (relevance_route) -> route -> [Node B (exclusion) if
boundary/hard_negative] -> Node C (score_and_type, deterministic).

Kept langgraph-free so it runs locally; graph.py offers an optional LangGraph
wrapper around the same callables.
"""
from __future__ import annotations

from src.mas.schemas import RelevanceOut, ExclusionOut
from src.mas.prompts import (
    build_relevance_system, EXCLUSION_SYSTEM,
    render_relevance_prompt, render_exclusion_prompt,
)
from src.mas.scoring import route_after_relevance, score_and_type
from src.mas.llm import StructuredLLM, Usage


def relevance_route(llm: StructuredLLM, state: dict, usage: Usage | None = None) -> dict:
    user = render_relevance_prompt(state["rubric"], state["title"], state["abstract"])
    out, pt, ct = llm.parse(build_relevance_system(state["rubric"]), user, RelevanceOut)
    if usage is not None:
        usage.add(pt, ct)
    return out.model_dump()


def exclusion_check(llm: StructuredLLM, state: dict, usage: Usage | None = None) -> dict:
    user = render_exclusion_prompt(
        state["rubric"], state["title"], state["abstract"],
        state.get("functional_evidence"), state.get("technical_evidence"),
    )
    out, pt, ct = llm.parse(EXCLUSION_SYSTEM, user, ExclusionOut)
    if usage is not None:
        usage.add(pt, ct)
    return out.model_dump()


def process_patent(state: dict, llm_fast: StructuredLLM, llm_strong: StructuredLLM,
                   usage: Usage | None = None) -> dict:
    """Run the full per-patent graph. Returns the merged state dict."""
    state = dict(state)
    state.update(relevance_route(llm_fast, state, usage))                 # Node A
    if route_after_relevance(state) == "exclusion_check":                 # conditional edge
        state.update(exclusion_check(llm_strong, state, usage))           # Node B
    state.update(score_and_type(state))                                   # Node C
    return state
