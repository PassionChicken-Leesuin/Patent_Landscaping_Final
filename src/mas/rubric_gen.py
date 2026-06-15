"""Auto-generate a MAS rubric JSON from a DomainSpec (Bergeaud & Verluise 2023, PLOS ONE).

Grounded in the paper, NOT a generic template:
- The SEED definition is the paper's functional-application level: a patent is SEED iff its
  abstract shows the invention performing one of the domain's in-scope TASKS (S2-1 annotation
  guideline tasks). The positive definition is therefore per-domain (the tasks differ).
- The HARD-NEGATIVE concept is the paper's "augmented anti-seed" (§3.1.3, §4.1.1): patents that
  MATCH the rule-based criteria (the keywords S2.3.1 / CPC classes S2.3.2) but, on reading the
  abstract, human scrutiny deemed them NOT the technology. So a hard negative is a RULE-MATCH-
  BUT-NOT-THE-TASK case — NOT "a patent from another Bergeaud domain". (Earlier versions wrongly
  listed the other domains as confusables, which made truly-unrelated OOD patents get routed to
  hard_negative instead of easy_negative.)
- Truly unrelated patents (no domain signal) are EASY negatives.
Self-driving keeps its bespoke v2 rubric — the ONLY domain for which the paper body states an
explicit negative decision axis (automate-vs-assist, p.8: "the very same technology can be used
to automate driving or to assist human driving ... the former we accept, the latter we reject").
The other five domains have no such per-domain negative axis in the paper, so we do not invent one.
"""
from __future__ import annotations
import json


def build_rubric(spec, registry) -> dict:
    tasks = [{"task_id": f"T{i+1}", "desc": t} for i, t in enumerate(spec.tasks)]
    task_phrases = "; ".join(spec.tasks[:3])
    return {
        "domain": spec.key,
        "version": "v1",
        "source": (
            "Bergeaud & Verluise (2023), PLOS ONE 18(12):e0295587. Definition = functional-"
            f"application TASKS for {spec.display} (S2-1 annotation guidelines); keywords (S2.3.1) "
            "and CPC (S2.3.2) are the rule-based candidate criteria. Hard negatives follow the "
            "paper's 'augmented anti-seed' (rule-matched but human-rejected on the abstract)."
        ),
        "definition": (
            f"{spec.display}: technology whose invention actually performs one of the defining "
            f"{spec.display} tasks (e.g. {task_phrases}). A patent is SEED only if its "
            "title+abstract clearly shows it carrying out one or more of the in-scope tasks below. "
            "Matching a keyword or CPC class is NOT sufficient — it only makes the patent a candidate."
        ),
        "primary_decision_axis": {
            "name": "performs_task_vs_rule_match_only",
            "rule": (
                f"ACCEPT (SEED) only if the invention itself PERFORMS a {spec.display} in-scope task "
                "with a concrete mechanism. REJECT as a HARD negative if the patent matched the "
                "domain's keywords/CPC (so it looks relevant) but the abstract shows it does NOT "
                "perform the task — the domain term is background/prior-art/one-possible-application, "
                "or the real contribution is a different/adjacent mechanism. REJECT as an EASY "
                "negative if there is no domain signal at all (clearly another field)."
            ),
        },
        "in_scope_tasks": tasks,
        "key_technical_signals": spec.keywords,
        "out_of_scope_confusables": [
            f"RULE-MATCH-BUT-NOT-THE-TASK: the abstract contains {spec.display} keywords (or the "
            "patent sits in a listed CPC class) but the invention does not actually perform an "
            "in-scope task — the paper's 'augmented anti-seed' / hard examples.",
            f"The {spec.display} term appears only as background, motivation, prior art, or one "
            "possible application, while the real contribution is a different mechanism.",
            f"A generic or adjacent method that shares {spec.display} vocabulary but pursues a "
            "different functional goal.",
        ],
        "hard_negative_patterns": [
            f"matched a {spec.display} keyword/CPC rule, but the abstract shows no in-scope task is performed -> hard negative",
            f"{spec.display} named only as an example/application; the invention is really about something else -> hard negative",
            "shares terminology with the domain but the functional goal is different -> hard negative",
        ],
        "score_anchors": {
            "0.9_1.0": f"the invention clearly PERFORMS a {spec.display} in-scope task with a concrete mechanism",
            "0.6_0.75": "an in-scope task is plausibly implied but the mechanism/scope is unclear, or signals are mixed -> boundary",
            "0.25_0.4": "matched the rules but the abstract shows it does NOT perform the task (rule-match look-alike) -> hard negative",
            "0.0_0.2": "no domain signal at all — clearly a different field -> easy negative",
        },
    }


def write_rubric(spec, registry) -> str:
    rubric = build_rubric(spec, registry)
    spec.rubric_path.parent.mkdir(parents=True, exist_ok=True)
    with open(spec.rubric_path, "w", encoding="utf-8") as f:
        json.dump(rubric, f, ensure_ascii=False, indent=2)
    return str(spec.rubric_path)
