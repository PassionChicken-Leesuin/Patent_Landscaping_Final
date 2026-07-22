"""Settled-boundary filter: a reworded re-ask of an owner-ruled boundary is not
re-asked; the prior ruling is reapplied (observed in the A2 boundary loop)."""
import unittest

from src.agentic.judge import settle_against_prior
from src.agentic.schemas import (HITLQuestion, PriorRulingMatch, PriorRulingMatchOut)


class _StubLLM:
    """Returns a fixed verdict; records the prompt for assertions."""
    def __init__(self, matches):
        self.matches = matches
        self.last_user = ""

    def parse(self, system, user, schema):
        self.last_user = user
        return PriorRulingMatchOut(matches=self.matches), 0, 0


class _Usage:
    def add(self, *a):
        pass


def _q(qid, text):
    return HITLQuestion(id=qid, question=text, why_needed="", options=[])


PRIOR = [{"question": "Should soft robotic actuators be included if not humanoid-specific?",
          "answer": "Include human-like manipulation actuators; exclude unrelated fields.",
          "answered_by": "human_batch"}]


class TestSettledBoundaries(unittest.TestCase):
    def test_settled_question_reuses_prior_ruling(self):
        qs = [_q("BL-Q1", "Should control systems without commercialization mention be included?"),
              _q("BL-Q2", "Should soft robotic actuators and components be included?")]
        stub = _StubLLM([PriorRulingMatch(question_id="q0", settled_by_prior_index=-1,
                                          rationale="new"),
                         PriorRulingMatch(question_id="q1", settled_by_prior_index=0,
                                          rationale="same boundary, reworded")])
        new, settled = settle_against_prior(stub, qs, PRIOR, _Usage())
        self.assertEqual([q.id for q in new], ["BL-Q1"])
        self.assertEqual(settled, [(qs[1], PRIOR[0])])
        self.assertIn("(q1)", stub.last_user)      # positional temp ids, not LLM ids

    def test_out_of_range_index_stays_new(self):
        qs = [_q("BL-Q1", "anything")]
        stub = _StubLLM([PriorRulingMatch(question_id="q0", settled_by_prior_index=7,
                                          rationale="bad index")])
        new, settled = settle_against_prior(stub, qs, PRIOR, _Usage())
        self.assertEqual(len(new), 1)
        self.assertEqual(settled, [])

    def test_no_prior_rulings_short_circuits(self):
        qs = [_q("BL-Q1", "anything")]
        stub = _StubLLM([])
        new, settled = settle_against_prior(stub, qs, [], _Usage())
        self.assertEqual(new, qs)
        self.assertEqual(settled, [])
        self.assertEqual(stub.last_user, "")       # no LLM call without priors


if __name__ == "__main__":
    unittest.main()
