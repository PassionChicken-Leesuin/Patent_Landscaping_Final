"""Prompt rendering for MAS nodes. stdlib-only (json) — importable locally.

few-shot uses the autonomous-driving HARD boundary: self-driving vs driver-assist
(ADAS). This is exactly the ANTISEED-manual hard-negative case in the eval set.
"""
from __future__ import annotations
import json

RELEVANCE_SYSTEM = (
    "You are the Relevance & Route agent for patent landscaping on title+abstract only.\n"
    "Extract evidence, judge core relevance, assign a route. Output JSON only.\n"
    "Do NOT assume or guess any ground-truth label. Score using the rubric's score_anchors.\n"
    'If relevance is uncertain (task implied but mechanism unclear), set route="boundary", '
    'not "easy_positive".'
)

EXCLUSION_SYSTEM = (
    "You are the Exclusion agent. The patent is borderline or looks like a domain look-alike.\n"
    "Decide whether it should be EXCLUDED as out-of-scope. Output JSON only. Do NOT use labels."
)

# one hard boundary example (self-driving vs driver-assist)
RELEVANCE_FEWSHOT = (
    "EXAMPLE (hard_negative):\n"
    'Title: "Lane departure warning system for a vehicle"\n'
    'Abstract: "A system warns the human driver with an alert when the vehicle drifts out of '
    'its lane; the driver remains in full control of steering and braking."\n'
    "-> functional_evidence: [] (no autonomous-driving task performed)\n"
    '-> technical_evidence: [{"source":"abstract","exact_text":"warns the human driver",'
    '"mapped_task":"confusable:driver-assistance","status":"present","strength":2}]\n'
    '-> core_stance: "unrelated", core_score: 0.18, route: "hard_negative"\n'
    "(reason: ADAS that keeps the human in control; no self-driving decision making)"
)


def render_relevance_prompt(rubric: dict, title: str, abstract: str) -> str:
    return (
        f"{RELEVANCE_SYSTEM}\n\n"
        f"Rubric:\n{json.dumps(rubric, ensure_ascii=False)}\n\n"
        f"{RELEVANCE_FEWSHOT}\n\n"
        f"Title: {title}\n"
        f"Abstract: {abstract}\n\n"
        "Steps:\n"
        "1. functional_evidence: units where the invention DOES an in_scope_task.\n"
        "2. technical_evidence: concrete mechanism/method/device supporting that task.\n"
        "3. core_stance (related/unrelated/abstain) and core_score (0-1) per score_anchors.\n"
        "4. route: easy_positive | easy_negative | boundary | hard_negative | abstain_candidate\n"
        "   - easy_positive: clear autonomous-driving task + mechanism, no confusable signal\n"
        "   - easy_negative: no domain signal\n"
        "   - hard_negative: domain words present but looks like an out_of_scope_confusable\n"
        "   - boundary: task implied but mechanism unclear, or mixed assist/autonomy signals\n"
        "   - abstain_candidate: title+abstract too thin to judge\n\n"
        "Output JSON with keys: functional_evidence, technical_evidence, core_stance, core_score, route."
    )


def render_exclusion_prompt(rubric: dict, title: str, abstract: str,
                            functional_evidence, technical_evidence) -> str:
    return (
        f"{EXCLUSION_SYSTEM}\n\n"
        f"Rubric out_of_scope_confusables: {json.dumps(rubric.get('out_of_scope_confusables', []), ensure_ascii=False)}\n"
        f"Rubric hard_negative_patterns: {json.dumps(rubric.get('hard_negative_patterns', []), ensure_ascii=False)}\n"
        f"Title: {title}\n"
        f"Abstract: {abstract}\n"
        f"Evidence so far: {json.dumps(functional_evidence or [], ensure_ascii=False)} "
        f"{json.dumps(technical_evidence or [], ensure_ascii=False)}\n\n"
        "Output JSON with keys: exclusion_stance (not_excluded|possible_exclusion|hard_negative), "
        "exclusion_risk (0=clearly in-scope .. 1=clearly look-alike), confusable_category, exclusion_reason."
    )
