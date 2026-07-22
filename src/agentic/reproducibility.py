"""Independent-run reproducibility regression metrics for the July system."""
from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path

import pandas as pd


DEFAULT_THRESHOLDS = {
    "stance_agreement": 0.90,
    "cohen_kappa": 0.80,
    "positive_jaccard": 0.85,
    "top_n_overlap": 0.80,
    "relevance_spearman": 0.90,
    "axis_jaccard": 0.80,
    "shared_axis_status_agreement": 0.90,
    "criterion_source_coverage": 0.95,
    "axis_source_coverage": 0.95,
    "hitl_question_jaccard": 0.70,
}


def _json(path: Path) -> dict:
    import json
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl(path: Path) -> list[dict]:
    import json
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _latest(run: Path) -> dict[str, dict]:
    latest = {}
    for row in _jsonl(run / "judge" / "audit.jsonl"):
        rid = str(row.get("record_id", ""))
        if rid:
            latest[rid] = row
    return latest


def _included(row: dict) -> bool:
    value = row.get("included")
    if isinstance(value, str):
        return value.lower() in ("true", "1", "yes")
    if value is not None:
        return bool(value)
    return row.get("stance") == "in_domain"


def _score(row: dict) -> float:
    value = row.get("relevance_score", row.get("final_score", row.get("score", 0.5)))
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.5


def _jaccard(a: set, b: set) -> float:
    return len(a & b) / len(a | b) if (a or b) else 1.0


def _categorical_kappa(a: list[str], b: list[str]) -> float:
    if not a:
        return math.nan
    observed = sum(x == y for x, y in zip(a, b)) / len(a)
    ca, cb = Counter(a), Counter(b)
    expected = sum((ca[k] / len(a)) * (cb[k] / len(b)) for k in set(ca) | set(cb))
    return 1.0 if expected == 1.0 and observed == 1.0 else (observed - expected) / (1 - expected)


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9가-힣]+", " ", str(text).lower()).strip()


def _axis_map(run: Path) -> dict[str, dict]:
    data = _json(run / "axis_synthesis.json")
    axes = data.get("technology_axes", [])
    if not axes:
        axes = _json(run / "criteria_final.json").get("technology_axes", [])
    return {_norm(a.get("name", a.get("id", ""))): a for a in axes
            if _norm(a.get("name", a.get("id", "")))}


def _source_profile(run: Path) -> dict:
    doc = _json(run / "criteria_final.json")
    items = [*doc.get("domain_criteria", []), *doc.get("exclusion_criteria", [])]
    typed = [item for item in items if item.get("source_refs")]
    source_types = Counter(
        ref.get("source_type", "unknown")
        for item in items for ref in (item.get("source_refs") or [])
    )
    axes = doc.get("technology_axes", []) or _json(run / "axis_synthesis.json").get(
        "technology_axes", [])
    axis_typed = [axis for axis in axes if axis.get("source_refs")]
    return {
        "criteria_count": len(items),
        "criterion_source_coverage": len(typed) / len(items) if items else 0.0,
        "axis_count": len(axes),
        "axis_source_coverage": len(axis_typed) / len(axes) if axes else 0.0,
        "source_type_counts": dict(source_types),
    }


def _question_set(run: Path) -> set[str]:
    return {_norm(row.get("question", "")) for row in _jsonl(run / "human_qa.jsonl")
            if _norm(row.get("question", ""))}


def _answer_map(run: Path) -> dict[str, str]:
    return {_norm(row.get("question", "")): _norm(row.get("answer", ""))
            for row in _jsonl(run / "human_qa.jsonl")
            if _norm(row.get("question", ""))}


def _owner_signature(run: Path) -> list[tuple]:
    docs = _json(run / "owner_docs.json").get("docs", [])
    return sorted((str(d.get("name", "")), int(d.get("chars", 0)), int(d.get("chunks", 0)))
                  for d in docs)


def compare_independent_runs(run_a: Path, run_b: Path, top_n: int = 100,
                             thresholds: dict[str, float] | None = None
                             ) -> tuple[dict, list[dict]]:
    """Compare artifacts only; never imports Q&A or state from one run into another."""
    run_a, run_b = Path(run_a), Path(run_b)
    if run_a.resolve() == run_b.resolve():
        raise ValueError("reproducibility requires two distinct isolated run workspaces")
    a, b = _latest(run_a), _latest(run_b)
    ids_a, ids_b = set(a), set(b)
    common = sorted(ids_a & ids_b)
    if not common:
        raise ValueError("the two runs have no common judged record_id")

    st_a = [str(a[r].get("stance", "missing")) for r in common]
    st_b = [str(b[r].get("stance", "missing")) for r in common]
    scores_a = pd.Series({_id: _score(a[_id]) for _id in common}, dtype=float)
    scores_b = pd.Series({_id: _score(b[_id]) for _id in common}, dtype=float)
    pos_a = {r for r, row in a.items() if _included(row)}
    pos_b = {r for r, row in b.items() if _included(row)}
    ranked_a = sorted(pos_a, key=lambda r: _score(a[r]), reverse=True)[:top_n]
    ranked_b = sorted(pos_b, key=lambda r: _score(b[r]), reverse=True)[:top_n]
    top_a, top_b = set(ranked_a), set(ranked_b)
    denom = min(len(top_a), len(top_b))

    axes_a, axes_b = _axis_map(run_a), _axis_map(run_b)
    axis_common = set(axes_a) & set(axes_b)
    source_a, source_b = _source_profile(run_a), _source_profile(run_b)
    q_a, q_b = _question_set(run_a), _question_set(run_b)
    answers_a, answers_b = _answer_map(run_a), _answer_map(run_b)
    answer_common = set(answers_a) & set(answers_b)

    spearman = float(scores_a.rank().corr(scores_b.rank()))
    if math.isnan(spearman):
        spearman = 1.0 if scores_a.equals(scores_b) else 0.0
    metrics = {
        "stance_agreement": sum(x == y for x, y in zip(st_a, st_b)) / len(common),
        "cohen_kappa": _categorical_kappa(st_a, st_b),
        "positive_jaccard": _jaccard(pos_a, pos_b),
        "top_n_overlap": len(top_a & top_b) / denom if denom else 1.0,
        "top_n_jaccard": _jaccard(top_a, top_b),
        "relevance_spearman": spearman,
        "relevance_mae": float((scores_a - scores_b).abs().mean()),
        "axis_jaccard": _jaccard(set(axes_a), set(axes_b)),
        "shared_axis_status_agreement": (
            sum(axes_a[k].get("status") == axes_b[k].get("status") for k in axis_common)
            / len(axis_common) if axis_common else 1.0),
        "hitl_question_jaccard": _jaccard(q_a, q_b),
        "shared_hitl_answer_agreement": (
            sum(answers_a[q] == answers_b[q] for q in answer_common) / len(answer_common)
            if answer_common else 1.0),
        "criterion_source_coverage": min(
            source_a["criterion_source_coverage"], source_b["criterion_source_coverage"]),
        "axis_source_coverage": min(
            source_a["axis_source_coverage"], source_b["axis_source_coverage"]),
    }
    limits = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    checks = {name: {"value": metrics[name], "minimum": limit,
                     "passed": bool(metrics[name] >= limit)}
              for name, limit in limits.items()}
    input_checks = {
        "pool_identity": ids_a == ids_b,
        "query_identity": (_json(run_a / "query.json").get("query_original")
                           == _json(run_b / "query.json").get("query_original")),
        "owner_document_identity": _owner_signature(run_a) == _owner_signature(run_b),
    }
    checks.update({name: {"value": value, "expected": True, "passed": value}
                   for name, value in input_checks.items()})

    changed = []
    for rid in common:
        if (a[rid].get("stance") != b[rid].get("stance")
                or _included(a[rid]) != _included(b[rid])):
            changed.append({
                "record_id": rid,
                "stance_a": a[rid].get("stance"), "stance_b": b[rid].get("stance"),
                "included_a": _included(a[rid]), "included_b": _included(b[rid]),
                "relevance_a": _score(a[rid]), "relevance_b": _score(b[rid]),
                "confidence_a": a[rid].get("decision_confidence"),
                "confidence_b": b[rid].get("decision_confidence"),
            })

    report = {
        "run_a": str(run_a.resolve()), "run_b": str(run_b.resolve()),
        "independence_contract": "artifact comparison only; no state or HITL answer sharing",
        "pool": {"n_a": len(a), "n_b": len(b), "n_common": len(common),
                 "only_a": len(ids_a - ids_b), "only_b": len(ids_b - ids_a)},
        "positive_counts": {"a": len(pos_a), "b": len(pos_b)},
        "metrics": metrics,
        "source_profiles": {"a": source_a, "b": source_b},
        "checks": checks,
        "passed": all(check["passed"] for check in checks.values()),
        "n_changed_decisions": len(changed),
    }
    return report, changed
