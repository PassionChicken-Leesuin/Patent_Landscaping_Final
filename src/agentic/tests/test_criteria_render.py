import unittest

from src.agentic.criteria import _renumber, render_md
from src.agentic.judge import _candidate_type, criteria_prompt_block
from src.agentic.schemas import CriteriaDocOut, CriterionOut, ScopeQuestion
from src.agentic.workspace import slugify


def _doc() -> CriteriaDocOut:
    return CriteriaDocOut(
        domain_name="Hydrogen Storage",
        domain_definition="Stores hydrogen for later use.",
        domain_criteria=[
            CriterionOut(id="Cx", statement="Stores hydrogen physically.", sources=["u1"]),
            CriterionOut(id="C9", statement="Improves storage materials.", sources=[]),
        ],
        scope_statement="Patents about storing hydrogen.", scope_decisions=[],
        exclusion_criteria=[
            CriterionOut(id="E7", statement="Consumes hydrogen without storing.", sources=[])
        ],
        boundary_guidance=["Fuel-cell supply context is not storage."], open_questions=[])


class TestCriteria(unittest.TestCase):
    def test_renumber_forces_canonical_ids(self):
        d = _renumber(_doc())
        self.assertEqual([c.id for c in d.domain_criteria], ["C1", "C2"])
        self.assertEqual([e.id for e in d.exclusion_criteria], ["E1"])

    def test_render_md_contains_sections_and_ids(self):
        md = render_md(_renumber(_doc()))
        for token in ("포함 판단 기준", "분석 대상 특허의 범위", "제외 판단 기준",
                      "C1.", "E1.", "경계 판정 지침"):
            self.assertIn(token, md)

    def test_prompt_block_amendments(self):
        block = criteria_prompt_block(_renumber(_doc()),
                                      amendments=["Human decision: transport is out."])
        self.assertIn("BINDING AMENDMENTS", block)
        self.assertIn("C1.", block)
        self.assertIn("E1.", block)

    def test_candidate_type_mapping(self):
        self.assertEqual(_candidate_type("in_domain", 0.9), "positive")
        self.assertEqual(_candidate_type("out_of_domain", 0.1), "easy_negative")
        self.assertEqual(_candidate_type("out_of_domain", 0.4, ["E1"]), "hard_negative")
        self.assertEqual(_candidate_type("boundary", 0.5), "boundary")

    def test_slugify(self):
        self.assertEqual(slugify("Hydrogen Storage"), "hydrogen-storage")
        self.assertEqual(slugify("3D Printing (Additive Mfg.)"),
                         "3d-printing-additive-mfg")

    def test_render_md_shows_open_questions(self):
        d = _renumber(_doc())
        d.open_questions = [ScopeQuestion(
            id="Q1", question="Include production?", why_it_matters="flips many",
            options=["in", "out"], tentative_default="out",
            broad_rule="include production", narrow_rule="storage only")]
        md = render_md(d)
        self.assertIn("HITL이 필요한 범위 질문", md)
        self.assertIn("Q1.", md)
        self.assertIn("미응답 기본값", md)


if __name__ == "__main__":
    unittest.main()
