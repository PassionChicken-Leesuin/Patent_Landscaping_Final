"""Contract: every HITL scope question reaches the owner as a decision card.

Four code paths raise scope questions — upfront decisions [4c], the criteria author's
own open questions, the validator's blocking scope issues, and the boundary-feedback
loop. Two of them used to hand the owner a bare sentence with no example patents and no
measured impact, which is exactly what the card exists to prevent. These tests pin the
card onto the question payload for each path.
"""
from __future__ import annotations
import json
import tempfile
import unittest
from pathlib import Path

from src.agentic.decisions import (as_hitl_questions, asked_text, carded_questions,
                                   cards_for_raw_questions)
from src.agentic.hitl import _uniquify, question_id
from src.agentic.schemas import (DecisionEnrichOut, DecisionQuestion, ScopeQuestion,
                                 ScopeQuestionsOut)
from src.agentic.workspace import Workspace


class _FakeUsage:
    def add(self, *_a, **_k):
        pass


class _FakeLLM:
    """Returns the schema the caller asked for; records the calls."""
    def __init__(self, fail: bool = False):
        self.calls, self.fail = [], fail

    def parse(self, system, user, model):
        self.calls.append(model.__name__)
        if self.fail:
            raise RuntimeError("llm down")
        if model is ScopeQuestionsOut:
            return ScopeQuestionsOut(questions=[ScopeQuestion(
                id="Q1", question="웨어러블 로봇을 포함할 것인가",
                why_it_matters="경계", options=["포함", "제외"],
                tentative_default="제외",
                broad_rule="Include wearable assistive robots.",
                narrow_rule="Include only free-standing humanoids.")]), 1, 1
        if model is DecisionEnrichOut:
            return DecisionEnrichOut(
                stake="웨어러블 로봇 포함 여부",
                include_argument="이전가능 코어", include_examples=["US1", "US2"],
                exclude_argument="휴머노이드 본체가 아님", exclude_examples=["US3"],
                recommendation="제외 권고"), 1, 1
        raise AssertionError(f"unexpected model {model}")


def _ws() -> Workspace:
    return Workspace(Path(tempfile.mkdtemp()) / "ws")


def _sq(qid="Q1") -> ScopeQuestion:
    return ScopeQuestion(id=qid, question="웨어러블 로봇을 포함할 것인가",
                         why_it_matters="경계", options=["포함", "제외"],
                         tentative_default="제외",
                         broad_rule="broad", narrow_rule="narrow")


class DecisionCardPayload(unittest.TestCase):

    def test_upfront_decisions_carry_their_card(self):
        d = DecisionQuestion(
            id="D1", stake="s", include_argument="i", include_examples=["US1"],
            exclude_argument="e", exclude_examples=["US2"], impact_flips=9,
            impact_sample_n=60, recommendation="r", options=["포함", "제외"],
            tentative_default="제외", broad_rule="b", narrow_rule="n")
        payload = [q.model_dump() for q in _uniquify(as_hitl_questions([d]))]
        self.assertIsNotNone(payload[0]["card"])
        self.assertEqual(payload[0]["card"]["include_examples"], ["US1"])

    def test_measured_questions_become_carded(self):
        ws, llm = _ws(), _FakeLLM()
        qs = carded_questions(ws, llm, [(_sq(), 9, 60)], _FakeUsage())
        self.assertEqual(len(qs), 1)
        self.assertIsNotNone(qs[0].card)
        self.assertEqual(qs[0].card["impact_flips"], 9)
        self.assertEqual(qs[0].card["exclude_examples"], ["US3"])
        # archived for audit — in the card log, NOT in [4c]'s ask-list
        saved = [json.loads(l) for l in
                 ws.decision_cards_jsonl.read_text(encoding="utf-8").splitlines() if l]
        self.assertEqual(len(saved), 1)
        self.assertFalse(ws.decisions_json.exists())

    def test_card_id_matches_the_asked_text(self):
        """A drifting id is what broke the UI join before the card was embedded."""
        ws, q = _ws(), _sq()
        cards = carded_questions(ws, _FakeLLM(), [(q, 3, 60)], _FakeUsage())
        self.assertEqual(cards[0].card["id"], question_id(asked_text(q)))
        self.assertEqual(cards[0].question, asked_text(q))

    def test_boundary_loop_ids_stay_namespaced(self):
        qs = carded_questions(_ws(), _FakeLLM(), [(_sq("Q2"), 5, 60)], _FakeUsage(),
                              id_prefix="BL-")
        self.assertTrue(qs[0].id.startswith("BL-"))
        self.assertIsNotNone(qs[0].card)

    def test_validator_issues_become_carded_questions(self):
        """The path from the screenshot: a blocking scope issue, previously uncarded."""
        ws, llm = _ws(), _FakeLLM()
        qs = cards_for_raw_questions(
            ws, llm, [("The rationale for excluding wearable robots is not supported.",
                       "Clarify the exclusion.")],
            doc=None, pool_df=None, probe_pool=None, domain="Humanoid", usage=_FakeUsage())
        self.assertEqual(len(qs), 1)
        self.assertIsNotNone(qs[0].card)
        self.assertEqual(qs[0].card["stake"], "웨어러블 로봇 포함 여부")
        self.assertIn("ScopeQuestionsOut", llm.calls)     # restated as a testable boundary
        # unmeasured (no pool given) is reported as such, never as "0건이 갈림"
        self.assertEqual(qs[0].card["impact_sample_n"], 0)

    def test_criteria_cards_do_not_become_upfront_decisions(self):
        """decisions.json is [4c]'s ask-list, reloaded verbatim on every resume. A card
        from a later stage archived there came back as an upfront decision — and under a
        different id (hashed from `stake`, not the asked text), so the answer already
        given no longer matched and the owner was asked the same boundary twice."""
        ws = _ws()
        carded_questions(ws, _FakeLLM(), [(_sq(), 9, 60)], _FakeUsage())
        self.assertFalse(ws.decisions_json.exists(),
                         "criteria-stage card leaked into [4c]'s ask-list")
        self.assertTrue(ws.decision_cards_jsonl.exists())

    def test_card_failure_never_blocks_the_question(self):
        """Unanswered is worse than uncarded: the loop must still ask."""
        qs = carded_questions(_ws(), _FakeLLM(fail=True), [(_sq(), 4, 60)], _FakeUsage())
        self.assertEqual(len(qs), 1)
        self.assertIsNone(qs[0].card)
        self.assertEqual(
            cards_for_raw_questions(_ws(), _FakeLLM(fail=True), [("q", "w")], None,
                                    None, None, "D", _FakeUsage()), [])


if __name__ == "__main__":
    unittest.main()
