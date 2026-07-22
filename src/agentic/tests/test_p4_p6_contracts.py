import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from app.artifacts import selected_slice
from src.agentic.axes import _canonicalize_reference_prefixes
from src.agentic.reproducibility import compare_independent_runs
from src.agentic.schemas import (
    AxisSynthesisOut, CriteriaDocOut, CriterionOut, EvidenceSourceRef,
    OwnerDocumentAssessmentOut, TechnologyAxisOut,
)
from src.agentic.validator import criteria_integrity_issues


def _ref():
    return EvidenceSourceRef(source_type="web", reference="https://example.org/domain",
                             claim="supports the domain axis", strength="high")


def _axes():
    return AxisSynthesisOut(
        owner_document_assessment=OwnerDocumentAssessmentOut(
            present=False, overall_quality="none", scope_clarity="none",
            technical_completeness="none", factual_reliability="none",
            strengths=[], gaps=[], conflicts=[]),
        technology_axes=[TechnologyAxisOut(
            id="A1", name="Core mechanism", description="Does the core task.",
            status="core", confidence="high", owner_documented=False,
            observed_in_corpus=True, source_refs=[_ref()], rationale="supported",
            boundary_examples=[])], unresolved_conflicts=[])


def _doc(with_refs=True):
    refs = [_ref()] if with_refs else []
    return CriteriaDocOut(
        domain_name="D", domain_definition="D does a task.",
        domain_criteria=[CriterionOut(id="C1", statement="Performs the task.",
                                      sources=[], axis_ids=["A1"], source_refs=refs)],
        scope_statement="Task patents.", scope_decisions=[],
        exclusion_criteria=[CriterionOut(id="E1", statement="Mentions D but does another task.",
                                         sources=[], axis_ids=["A1"], source_refs=refs)],
        boundary_guidance=[], open_questions=[], technology_axes=_axes().technology_axes,
        owner_document_assessment=_axes().owner_document_assessment)


class TestP4P6Contracts(unittest.TestCase):
    def test_corpus_prefix_is_repaired_without_fuzzy_matching(self):
        axes = _axes()
        axes.technology_axes[0].source_refs[0].source_type = "corpus"
        axes.technology_axes[0].source_refs[0].reference = "Core mechanism"
        _canonicalize_reference_prefixes(axes, {"corpus: Core mechanism"})
        self.assertEqual(axes.technology_axes[0].source_refs[0].reference,
                         "corpus: Core mechanism")

    def test_typed_provenance_is_enforced(self):
        self.assertEqual(criteria_integrity_issues(_doc(True), _axes()), [])
        issues = criteria_integrity_issues(_doc(False), _axes())
        self.assertEqual({i.field for i in issues}, {"C1.source_refs", "E1.source_refs"})
        self.assertTrue(all(i.severity == "critical" for i in issues))

    def test_exact_catalog_reference_can_support_exclusion(self):
        doc = _doc(True)
        doc.exclusion_criteria[0].source_refs[0].source_type = "corpus"
        doc.exclusion_criteria[0].source_refs[0].reference = "corpus: adjacent cluster"
        issues = criteria_integrity_issues(
            doc, _axes(), allowed_refs={"corpus: adjacent cluster"})
        self.assertEqual(issues, [])

    def test_ui_selection_never_promotes_negative_by_score(self):
        df = pd.DataFrame([
            {"record_id": "negative-high", "included": False, "relevance_score": .99,
             "candidate_type": "hard_negative"},
            {"record_id": "positive-low", "included": True, "relevance_score": .31,
             "candidate_type": "positive"},
        ])
        selected = selected_slice(df, "all_positive", 0.0, 0)
        self.assertEqual(selected["record_id"].tolist(), ["positive-low"])

    def test_independent_run_comparison(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runs = [root / "a", root / "b"]
            for run in runs:
                (run / "judge").mkdir(parents=True)
                audit = [
                    {"record_id": "1", "stance": "in_domain", "included": True,
                     "relevance_score": .9, "decision_confidence": .9},
                    {"record_id": "2", "stance": "out_of_domain", "included": False,
                     "relevance_score": .1, "decision_confidence": .9},
                ]
                (run / "judge" / "audit.jsonl").write_text(
                    "\n".join(json.dumps(x) for x in audit) + "\n", encoding="utf-8")
                (run / "axis_synthesis.json").write_text(
                    json.dumps(_axes().model_dump()), encoding="utf-8")
                (run / "criteria_final.json").write_text(
                    json.dumps(_doc(True).model_dump()), encoding="utf-8")
                (run / "human_qa.jsonl").write_text("", encoding="utf-8")
            report, changed = compare_independent_runs(*runs, top_n=1)
            self.assertTrue(report["passed"])
            self.assertEqual(report["metrics"]["stance_agreement"], 1.0)
            self.assertEqual(changed, [])


if __name__ == "__main__":
    unittest.main()
