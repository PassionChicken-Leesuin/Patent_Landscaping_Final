import unittest

from src.mas.llm import StructuredLLM, Usage
from src.agentic.judge import judge_patent
from src.agentic.schemas import JudgmentOut, SecondPassOut


class ConflictLLM(StructuredLLM):
    """First pass: C-matched yet excluded (the E-veto fault). Second pass arbitrates in."""
    def parse(self, system, user, schema):
        if schema is JudgmentOut:
            return JudgmentOut(matched_criteria=["C1", "C2"], violated_exclusions=["E2"],
                               stance="out_of_domain", relevance_score=0.1,
                               decision_confidence=0.2,
                               rationale="satisfies C1,C2 but E2 cited"), 0, 0
        if schema is SecondPassOut:
            assert "violates the stance+C/E contract" in user
            return SecondPassOut(confirmed_stance="in_domain",
                                 confirmed_matched_criteria=["C1", "C2"],
                                 confirmed_violated_exclusions=[],
                                 confirmed_relevance_score=0.85,
                                 confirmed_decision_confidence=0.95,
                                 decisive_criterion="C1", rationale="inclusion is genuine"), 0, 0
        raise ValueError(schema)


class TestConflictGuard(unittest.TestCase):
    def _state(self):
        return {"record_id": "r1", "patent_id": "p1", "domain": "d",
                "title": "t", "abstract": "a",
                "rubric": {"block": "CRITERIA", "second_pass": True}}

    def test_conflict_triggers_second_pass_arbitration(self):
        llm = ConflictLLM()
        res = judge_patent(self._state(), llm, llm, Usage())
        self.assertEqual(res["stance"], "in_domain")
        self.assertEqual(res["final_score"], 0.85)
        self.assertTrue(res["included"])
        self.assertEqual(res["candidate_type"], "positive")
        self.assertIsNotNone(res["second_pass"])

    def test_conflict_guard_respects_second_pass_off(self):
        llm = ConflictLLM()
        state = self._state()
        state["rubric"]["second_pass"] = False
        res = judge_patent(state, llm, llm, Usage())
        self.assertEqual(res["stance"], "boundary")
        self.assertFalse(res["included"])


if __name__ == "__main__":
    unittest.main()
