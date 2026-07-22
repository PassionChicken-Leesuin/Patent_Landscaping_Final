"""Issue ledger / routing / patch contracts (2026-07-22 reviser design).

Covers the four conservative-design refinements:
  - unique-prefix provenance repair fires only under strict conditions, audited
  - a criterion's SOLE unknown ref is never dropped (provenance would silently weaken)
  - structural issue codes survive reworded prose; ledger tracks open/resolved
  - new criticals on untouched fields need invariant-level evidence, else demoted
"""
import tempfile
import unittest
from pathlib import Path

from src.agentic.axes import canonicalize_source_refs, drop_unknown_refs
from src.agentic.criteria import PatchApplyError, apply_patches
from src.agentic.schemas import (
    CriteriaCritiqueOut, CriteriaDocOut, CriteriaFieldPatch, CriterionOut,
    CritiqueIssue, EvidenceSourceRef, ScopeDecisionOut,
)
from src.agentic.validator import IssueLedger, constrain_new_criticals, issue_code_for
from src.agentic.workspace import Workspace


_E5_FULL = ("corpus: Liquid hydrogen handling technologies, like 'Liquid hydrogen stand "
            "and liquid hydrogen automobile', relate to handling rather than the storage "
            "technology itself.")


def _ref(reference, source_type="corpus"):
    return EvidenceSourceRef(source_type=source_type, reference=reference,
                             claim="supports", strength="high")


def _doc():
    web = _ref("https://example.org/a", "web")
    return CriteriaDocOut(
        domain_name="D", domain_definition="D does a task.",
        domain_criteria=[
            CriterionOut(id="C1", statement="Performs the task.", sources=[],
                         axis_ids=["A1"], source_refs=[web]),
            CriterionOut(id="C2", statement="Improves the task.", sources=[],
                         axis_ids=["A1"], source_refs=[web])],
        scope_statement="Task patents.",
        scope_decisions=[ScopeDecisionOut(topic="fuel cells", verdict="out",
                                          rationale="conversion, not storage")],
        exclusion_criteria=[CriterionOut(id="E1", statement="Different task.", sources=[],
                                         axis_ids=["A1"], source_refs=[web])],
        boundary_guidance=["Guidance one."], open_questions=[])


class TestProvenanceRepair(unittest.TestCase):
    def test_unique_token_boundary_prefix_is_repaired_and_audited(self):
        # the live-a E5 case: model cites the short cluster name, catalog holds the
        # full boundary-case sentence — same type, unique candidate, token boundary
        refs = [_ref("corpus: Liquid hydrogen handling technologies")]
        repairs = canonicalize_source_refs(refs, {_E5_FULL}, context="criterion:E5")
        self.assertEqual(refs[0].reference, _E5_FULL)
        self.assertEqual(repairs[0]["op"], "unique_prefix_match")
        self.assertEqual(repairs[0]["context"], "criterion:E5")

    def test_non_token_boundary_prefix_is_not_repaired(self):
        refs = [_ref("corpus: Liquid hydrogen handling tech")]  # 'tech...' mid-token
        self.assertEqual(canonicalize_source_refs(refs, {_E5_FULL}), [])
        self.assertEqual(refs[0].reference, "corpus: Liquid hydrogen handling tech")

    def test_ambiguous_prefix_is_not_repaired(self):
        allowed = {"corpus: Liquid hydrogen handling, first variant",
                   "corpus: Liquid hydrogen handling, second variant"}
        refs = [_ref("corpus: Liquid hydrogen handling")]
        self.assertEqual(canonicalize_source_refs(refs, allowed), [])

    def test_cross_source_type_is_never_repaired(self):
        refs = [_ref("Liquid hydrogen handling technologies", "web")]
        self.assertEqual(canonicalize_source_refs(refs, {_E5_FULL}), [])

    def test_unknown_ref_dropped_only_beside_a_valid_ref(self):
        allowed = {"https://example.org/a"}
        c = CriterionOut(id="E5", statement="s", sources=[],
                         source_refs=[_ref("https://example.org/a", "web"),
                                      _ref("corpus: invented cluster")])
        repairs = drop_unknown_refs(c, allowed, context="criterion:E5")
        self.assertEqual([r.reference for r in c.source_refs], ["https://example.org/a"])
        self.assertEqual(repairs[0]["op"], "dropped_unknown_ref")

    def test_sole_unknown_ref_is_kept_as_critical_evidence_gap(self):
        c = CriterionOut(id="E5", statement="s", sources=[],
                         source_refs=[_ref("corpus: invented cluster")])
        self.assertEqual(drop_unknown_refs(c, {"https://example.org/a"}), [])
        self.assertEqual(len(c.source_refs), 1)


class TestIssueLedger(unittest.TestCase):
    def _issue(self, code="", category="testability", targets=("C1",),
               severity="critical", problem="C1 is vague."):
        return CritiqueIssue(field="C-criteria", problem=problem, suggestion="fix",
                             severity=severity, category=category,
                             target_ids=list(targets), issue_code=code)

    def test_code_is_stable_across_reworded_prose(self):
        a = self._issue(problem="C1 is not testable from title+abstract.")
        b = self._issue(problem="C1 relies on indicative terms and stays vague.")
        self.assertEqual(issue_code_for(a), issue_code_for(b))

    def test_ledger_open_then_resolved(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Workspace(slug="x")
            ws.__dict__["slug"] = "x"
            # point the workspace at the temp dir
            import src.agentic.config as AC
            old = AC.AGENTIC_DIR
            AC.AGENTIC_DIR = Path(td)
            try:
                ledger = IssueLedger(ws)
                crit = CriteriaCritiqueOut(approved=False, issues=[self._issue()],
                                           action="revise", followup_queries=[],
                                           human_questions=[])
                ledger.update(1, 1, crit)
                self.assertEqual(ledger.open_codes(), {"TESTABILITY:C1"})
                empty = CriteriaCritiqueOut(approved=True, issues=[], action="approve",
                                            followup_queries=[], human_questions=[])
                ledger.update(2, 2, empty)
                self.assertEqual(ledger.open_codes(), set())
                data = Workspace.read_json(ws.criteria_issue_ledger_json)
                self.assertEqual(data["issues"]["TESTABILITY:C1"]["status"], "resolved")
            finally:
                AC.AGENTIC_DIR = old

    def test_new_critical_on_untouched_field_is_demoted_without_evidence(self):
        crit = CriteriaCritiqueOut(
            approved=False, action="revise", followup_queries=[], human_questions=[],
            issues=[
                self._issue(category="testability", targets=("C2",),
                            problem="C2 suddenly looks vague."),          # new, untouched
                self._issue(category="consistency", targets=("C1", "E1"),
                            problem="C1 and E1 now contradict."),         # evidenced
                self._issue(code="PROVENANCE_REF:E5", category="provenance",
                            targets=("E5",), problem="unknown ref"),      # deterministic
                self._issue(code="TESTABILITY:C1", problem="still open"), # prior open
            ])
        demoted = constrain_new_criticals(crit, prev_open={"TESTABILITY:C1"},
                                          touched={"C1"})
        self.assertEqual(demoted, ["TESTABILITY:C2"])
        by_code = {issue_code_for(i): i.severity for i in crit.issues}
        self.assertEqual(by_code["TESTABILITY:C2"], "minor")
        self.assertEqual(by_code["CONSISTENCY:C1-E1"], "critical")
        self.assertEqual(by_code["PROVENANCE_REF:E5"], "critical")
        self.assertEqual(by_code["TESTABILITY:C1"], "critical")


class TestApplyPatches(unittest.TestCase):
    def test_replace_keeps_other_fields_frozen_and_ids_stable(self):
        doc = _doc()
        fixed = doc.domain_criteria[0].model_copy(deep=True)
        fixed.statement = "Performs the task, with observable evidence."
        fixed.observable_signals = ["task term"]
        out, touched = apply_patches(doc, [CriteriaFieldPatch(
            issue_codes=["TESTABILITY:C1"], target="domain_criteria", op="replace",
            target_id="C1", new_criterion=fixed)])
        self.assertEqual(touched, {"C1"})
        self.assertEqual(out.domain_criteria[0].statement,
                         "Performs the task, with observable evidence.")
        self.assertEqual(out.domain_criteria[1].statement, "Improves the task.")
        self.assertEqual(out.exclusion_criteria[0].statement, "Different task.")
        # the input document is untouched (patches operate on a copy)
        self.assertEqual(doc.domain_criteria[0].statement, "Performs the task.")

    def test_add_assigns_next_free_id(self):
        doc = _doc()
        new_c = CriterionOut(id="ignored", statement="New criterion.", sources=[])
        out, touched = apply_patches(doc, [CriteriaFieldPatch(
            issue_codes=["AXIS_COVERAGE:A2"], target="domain_criteria", op="add",
            target_id="", new_criterion=new_c)])
        self.assertEqual(out.domain_criteria[-1].id, "C3")
        self.assertIn("C3", touched)

    def test_scope_boundary_and_prose_targets(self):
        doc = _doc()
        out, touched = apply_patches(doc, [
            CriteriaFieldPatch(issue_codes=["SCOPE_CONFLICT:FUEL_CELLS"],
                               target="scope_decisions", op="replace",
                               target_id="fuel cells",
                               new_scope_decision=ScopeDecisionOut(
                                   topic="fuel cells", verdict="conditional",
                                   rationale="in only when storage is the contribution")),
            CriteriaFieldPatch(issue_codes=["OTHER:BG"], target="boundary_guidance",
                               op="replace", target_id="1", new_text="Guidance revised."),
            CriteriaFieldPatch(issue_codes=["DEFINITION:D"], target="domain_definition",
                               op="replace", target_id="", new_text="D does a wider task."),
        ])
        self.assertEqual(out.scope_decisions[0].verdict, "conditional")
        self.assertEqual(out.boundary_guidance, ["Guidance revised."])
        self.assertEqual(out.domain_definition, "D does a wider task.")
        self.assertEqual(touched, {"scope:fuel cells", "boundary_guidance",
                                   "domain_definition"})

    def test_unknown_target_raises(self):
        with self.assertRaises(PatchApplyError):
            apply_patches(_doc(), [CriteriaFieldPatch(
                issue_codes=["X"], target="domain_criteria", op="replace",
                target_id="C9", new_criterion=_doc().domain_criteria[0])])


if __name__ == "__main__":
    unittest.main()
