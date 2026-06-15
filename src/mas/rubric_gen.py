"""Auto-generate a MAS rubric JSON from a DomainSpec (Bergeaud & Verluise S2 Appendix).

The rubric schema matches the hand-seeded autonomous_driving_v2.json. For the 5 added
domains the decisive axis is the GENERIC one: does the invention actually PERFORM one of
the domain's in-scope tasks (SEED), or does it merely mention the domain / use an adjacent
technology for a different purpose / belong to another field (NOT_SEED)? Self-driving's
special automate-vs-assist axis is NOT generated here (it keeps its bespoke v2 rubric).
"""
from __future__ import annotations
import json


def build_rubric(spec, registry) -> dict:
    others = [registry[k].display for k in spec.ood_domains(registry)]
    tasks = [{"task_id": f"T{i+1}", "desc": t} for i, t in enumerate(spec.tasks)]
    task_phrases = "; ".join(spec.tasks[:3])
    return {
        "domain": spec.key,
        "version": "v1",
        "source": (
            "Bergeaud & Verluise (2023), PLOS ONE — S2 Appendix annotation guidelines, "
            f"keywords (S2.3.1) and CPC classes (S2.3.2) for {spec.display}. The domain is "
            "defined at the FUNCTIONAL-APPLICATION level (a set of tasks), not by keyword presence."
        ),
        "definition": (
            f"{spec.display}: technology whose invention actually performs one of the defining "
            f"{spec.display} tasks (e.g. {task_phrases}). A patent is SEED only if its "
            "title+abstract clearly discusses doing one or more of the in-scope tasks below."
        ),
        "primary_decision_axis": {
            "name": "performs_task_vs_mentions_or_adjacent",
            "rule": (
                f"ACCEPT (SEED) only if the invention itself PERFORMS a {spec.display} in-scope "
                "task with a concrete mechanism. REJECT (NOT_SEED) if it merely MENTIONS the "
                "domain, uses a related/adjacent technology for a DIFFERENT purpose, applies the "
                "domain's tools to another field, or belongs to a different technology entirely. "
                "Keyword presence alone is NOT sufficient — the functional task must be present."
            ),
        },
        "in_scope_tasks": tasks,
        "key_technical_signals": spec.keywords,
        "out_of_scope_confusables": [
            f"Patents from an ADJACENT/other Bergeaud domain ({', '.join(others)}) that share "
            "vocabulary but do not perform a " + spec.display + " task.",
            f"Generic patents that merely MENTION {spec.display} terms without doing the task "
            "(e.g. listing it as background, prior art, or one possible application).",
            f"Using {spec.display}-adjacent components/methods for a different end (no in-scope task).",
        ],
        "hard_negative_patterns": [
            f"domain keyword present but the invention does NOT perform a {spec.display} task -> reject",
            f"the domain is named only as an example/application, the real contribution is elsewhere -> reject",
            "an adjacent-domain invention that overlaps in terminology -> reject",
        ],
        "score_anchors": {
            "0.9_1.0": f"the invention clearly PERFORMS a {spec.display} in-scope task with a concrete mechanism",
            "0.6_0.75": "domain task plausibly implied but the mechanism/scope is unclear, or mixed signals -> boundary",
            "0.0_0.25": "merely mentions the domain, an adjacent-field/different-purpose use, or no domain signal at all",
        },
    }


def write_rubric(spec, registry) -> str:
    rubric = build_rubric(spec, registry)
    spec.rubric_path.parent.mkdir(parents=True, exist_ok=True)
    with open(spec.rubric_path, "w", encoding="utf-8") as f:
        json.dump(rubric, f, ensure_ascii=False, indent=2)
    return str(spec.rubric_path)
