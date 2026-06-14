"""Stage C (deterministic scoring & candidate_type) + routing predicate.

Pure functions — no LLM, no langgraph. Unit-testable locally.

candidate_type is a FLAG, not a score band: a hard negative has many domain
signals (high core_score) but gets capped to EX_CAP, so it would otherwise be
trapped in 'boundary'. Flagging it lets the downstream build augmented anti-seed
(negatives = easy_negative sample + ALL hard_negative) and run the ablation.
"""
from __future__ import annotations

from src.mas import config as MC


def route_after_relevance(state: dict) -> str:
    """Conditional edge: only boundary / hard_negative escalate to exclusion."""
    if state.get("route") in ("boundary", "hard_negative"):
        return "exclusion_check"
    return "score_and_type"


def score_and_type(state: dict) -> dict:
    core = float(state["core_score"])
    ex = float(state.get("exclusion_risk") or 0.0)
    route = state.get("route")
    stance = state.get("core_stance")

    score = core
    if ex >= MC.EX_TRIGGER:
        score = min(score, MC.EX_CAP)        # look-alikes are capped

    if route == "hard_negative" or ex >= MC.EX_TRIGGER:
        ctype = "hard_negative"
    elif route == "abstain_candidate" or stance == "abstain":
        ctype = "abstain"
    elif score >= MC.TAU_POS:
        ctype = "positive"
    elif score <= MC.TAU_NEG:
        ctype = "easy_negative"
    else:
        ctype = "boundary"

    return {"final_score": round(score, 6), "candidate_type": ctype}
