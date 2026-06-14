"""Deterministic-core tests (no API, no langgraph). Run:
   .venv/Scripts/python.exe -m src.mas.tests.test_scoring
"""
from __future__ import annotations

from src.mas.scoring import score_and_type, route_after_relevance
from src.mas import config as MC


def _check(name, cond):
    assert cond, f"FAILED: {name}"
    print(f"ok  {name}")


def run():
    # routing
    _check("boundary -> exclusion", route_after_relevance({"route": "boundary"}) == "exclusion_check")
    _check("hard_neg -> exclusion", route_after_relevance({"route": "hard_negative"}) == "exclusion_check")
    _check("easy_pos -> score", route_after_relevance({"route": "easy_positive"}) == "score_and_type")

    # clear positive
    r = score_and_type({"core_score": 0.92, "route": "easy_positive", "core_stance": "related"})
    _check("positive type", r["candidate_type"] == "positive")
    _check("positive score kept", r["final_score"] == 0.92)

    # easy negative
    r = score_and_type({"core_score": 0.10, "route": "easy_negative", "core_stance": "unrelated"})
    _check("easy_negative type", r["candidate_type"] == "easy_negative")

    # hard negative via route flag: high core but flagged hard_negative
    r = score_and_type({"core_score": 0.80, "route": "hard_negative", "core_stance": "unrelated"})
    _check("hard_negative flag overrides band", r["candidate_type"] == "hard_negative")

    # exclusion override: caps score AND flags hard_negative even if route=boundary
    r = score_and_type({"core_score": 0.88, "route": "boundary", "core_stance": "related",
                        "exclusion_risk": 0.9})
    _check("exclusion caps score", r["final_score"] == MC.EX_CAP)
    _check("exclusion -> hard_negative", r["candidate_type"] == "hard_negative")

    # boundary (mid score, no exclusion)
    r = score_and_type({"core_score": 0.5, "route": "boundary", "core_stance": "related",
                        "exclusion_risk": 0.0})
    _check("boundary type", r["candidate_type"] == "boundary")

    # abstain
    r = score_and_type({"core_score": 0.5, "route": "abstain_candidate", "core_stance": "abstain"})
    _check("abstain type", r["candidate_type"] == "abstain")

    print("\nALL SCORING TESTS PASSED")


if __name__ == "__main__":
    run()
