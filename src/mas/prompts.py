"""Prompt rendering for MAS nodes. stdlib-only (json) — importable locally.

Domain-aware: the Relevance system prompt + few-shot are derived from the rubric so the
same MAS works for any of the 6 Bergeaud domains. Self-driving keeps its bespoke few-shot
(the hard automate-vs-assist boundary); the other domains get a generic
performs-the-task vs merely-mentions-it few-shot instantiated from the rubric.
"""
from __future__ import annotations
import json

EXCLUSION_SYSTEM = (
    "You are the Exclusion agent. The patent is borderline or looks like a domain look-alike.\n"
    "Decide whether it should be EXCLUDED as out-of-scope. Output JSON only. Do NOT use labels."
)

# self-driving (autonomous_driving): the decisive boundary is automate (SEED) vs assist
# (NOT_SEED). Contrasting PAIR on the SAME lane technology — taught explicitly per Bergeaud.
SDV_FEWSHOT = (
    "EXAMPLE A (hard_negative — driver assistance, human in control):\n"
    'Title: "Lane departure warning system for a vehicle"\n'
    'Abstract: "A system warns the human driver with an alert when the vehicle drifts out of '
    'its lane; the driver remains in full control of steering and braking."\n'
    '-> functional_evidence: []   technical_evidence: [{"source":"abstract",'
    '"exact_text":"warns the human driver","mapped_task":"confusable:driver-assistance",'
    '"status":"present","strength":2}]\n'
    '-> core_stance: "unrelated", core_score: 0.15, route: "hard_negative"\n'
    "(reason: ADAS — human keeps control, no autonomous driving decision)\n\n"
    "EXAMPLE B (easy_positive — same lane tech, but the VEHICLE drives itself):\n"
    'Title: "Lane-keeping control for an autonomous vehicle"\n'
    'Abstract: "An autonomous vehicle detects lane boundaries and autonomously steers to keep '
    'the ego vehicle centered, controlling the dynamic driving task without driver input."\n'
    '-> functional_evidence: [{"source":"abstract","exact_text":"autonomously steers ... without '
    'driver input","mapped_task":"T1","status":"present","strength":3}]\n'
    '-> core_stance: "related", core_score: 0.92, route: "easy_positive"\n'
    "(reason: the vehicle itself performs the driving task — automate, not assist)"
)


def build_relevance_system(rubric: dict) -> str:
    domain = rubric.get("domain", "the target")
    definition = rubric.get("definition", "")
    axis = rubric.get("primary_decision_axis", {}).get("rule", "")
    return (
        f"You are the Relevance & Route agent for {domain} patent landscaping on title+abstract only.\n"
        f"Domain definition: {definition}\n"
        f"Decisive axis: {axis}\n"
        "Extract evidence, judge core relevance, assign a route. Output JSON only.\n"
        "Do NOT assume or guess any ground-truth label. Score using the rubric's score_anchors.\n"
        'If relevance is uncertain (a task is implied but the mechanism/scope is unclear), set '
        'route="boundary", not "easy_positive".'
    )


def _generic_fewshot(rubric: dict) -> str:
    """A performs-the-task (SEED) vs mentions-only (hard_negative) pair, from the rubric."""
    tasks = rubric.get("in_scope_tasks", [])
    t1 = tasks[0]["desc"] if tasks else "a domain task"
    t1_id = tasks[0]["task_id"] if tasks else "T1"
    domain = rubric.get("domain", "the domain")
    return (
        "EXAMPLE A (hard_negative — names the domain but does NOT perform a task):\n"
        f'Abstract: "... the method could be applied in {domain} systems among other fields, '
        'but the invention itself concerns an unrelated mechanism ..."\n'
        '-> functional_evidence: []   core_stance: "unrelated", core_score: 0.18, route: "hard_negative"\n'
        "(reason: the domain is only mentioned as a possible application; no in-scope task is performed)\n\n"
        "EXAMPLE B (easy_positive — the invention performs an in-scope task):\n"
        f'Abstract: "... the invention {t1.lower()} ..., with a concrete described mechanism."\n'
        f'-> functional_evidence: [{{"source":"abstract","exact_text":"...","mapped_task":"{t1_id}",'
        '"status":"present","strength":3}]\n'
        '-> core_stance: "related", core_score: 0.9, route: "easy_positive"\n'
        "(reason: the invention itself carries out a defining in-scope task)"
    )


def relevance_fewshot(rubric: dict) -> str:
    return SDV_FEWSHOT if rubric.get("domain") == "autonomous_driving" else _generic_fewshot(rubric)


def render_relevance_prompt(rubric: dict, title: str, abstract: str) -> str:
    return (
        f"{build_relevance_system(rubric)}\n\n"
        f"Rubric:\n{json.dumps(rubric, ensure_ascii=False)}\n\n"
        f"{relevance_fewshot(rubric)}\n\n"
        f"Title: {title}\n"
        f"Abstract: {abstract}\n\n"
        "Steps:\n"
        "1. functional_evidence: units where the invention DOES an in_scope_task.\n"
        "2. technical_evidence: concrete mechanism/method/device supporting that task.\n"
        "3. core_stance (related/unrelated/abstain) and core_score (0-1) per score_anchors.\n"
        "4. route: easy_positive | easy_negative | boundary | hard_negative | abstain_candidate\n"
        "   - easy_positive: clear in-scope task + mechanism, no confusable signal\n"
        "   - easy_negative: no domain signal\n"
        "   - hard_negative: domain words present but looks like an out_of_scope_confusable\n"
        "   - boundary: task implied but mechanism unclear, or mixed signals\n"
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
