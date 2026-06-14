"""Optional LangGraph wrapper around the same node callables (spec §4).

The parallel runner (runner.py) uses the langgraph-free `process_patent` for
clean per-key parallelism. This compiled graph is the spec-faithful single-stream
artifact — useful for visualization, Colab demos, or a langgraph-native driver.
"""
from __future__ import annotations

from langgraph.graph import StateGraph, START, END

from src.mas.schemas import PatentState
from src.mas.scoring import route_after_relevance, score_and_type
from src.mas.nodes import relevance_route, exclusion_check


def build_graph(llm_fast, llm_strong, usage=None):
    g = StateGraph(PatentState)
    g.add_node("relevance_route", lambda s: relevance_route(llm_fast, s, usage))
    g.add_node("exclusion_check", lambda s: exclusion_check(llm_strong, s, usage))
    g.add_node("score_and_type", score_and_type)

    g.add_edge(START, "relevance_route")
    g.add_conditional_edges(
        "relevance_route", route_after_relevance,
        {"exclusion_check": "exclusion_check", "score_and_type": "score_and_type"},
    )
    g.add_edge("exclusion_check", "score_and_type")
    g.add_edge("score_and_type", END)
    return g.compile()
