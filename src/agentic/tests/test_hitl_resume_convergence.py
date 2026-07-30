"""Contract: a batch-HITL relaunch CONTINUES the criteria loop, it does not restart it.

Batch HITL exits the process on every question and the UI relaunches after each answer,
so anything the loop keeps only in local variables silently resets. Two things did:

  - the run's own human answers, so each resume redrafted as if the owner had never
    answered and the drafter re-raised the boundary it had just been told about;
  - the critique-round budget, so the loop could never exhaust it and block with a
    report — it just kept asking.

Together they made the criteria stage loop forever in the UI (observed: 13 relaunches
re-asking one boundary, answered identically every time).
"""
from __future__ import annotations
import tempfile
import unittest
from pathlib import Path

from src.agentic import config as AC
from src.agentic.judge import _prior_rulings
from src.agentic.schemas import CriteriaCritiqueOut, CritiqueIssue
from src.agentic.validator import IssueLedger
from src.agentic.workspace import Workspace


def _ws() -> Workspace:
    return Workspace(Path(tempfile.mkdtemp()) / "ws")


def _critique(*codes: str) -> CriteriaCritiqueOut:
    return CriteriaCritiqueOut(
        approved=False, action="revise", followup_queries=[], human_questions=[],
        issues=[CritiqueIssue(field="f", problem=f"p{c}", suggestion="s",
                              severity="critical", category="consistency",
                              issue_code=c, target_ids=[]) for c in codes])


class ResumeKeepsRunState(unittest.TestCase):

    def test_answers_survive_a_relaunch(self):
        """What the drafter is given on resume — the seeding the loop now does."""
        ws = _ws()
        ws.append_jsonl(ws.human_qa_jsonl, {
            "stage": "criteria", "id": "Q1", "answered_by": "human_batch",
            "question": "로봇 일정 관리를 포함할까요?", "answer": "제외"})
        ws.append_jsonl(ws.human_qa_jsonl, {
            "stage": "criteria", "id": "Q2", "answered_by": "auto",
            "question": "자동 가정", "answer": "포함"})

        seeded = _prior_rulings(ws)
        self.assertEqual([q["question"] for q in seeded], ["로봇 일정 관리를 포함할까요?"],
                         "owner rulings must survive the relaunch; auto assumptions must not")

    def test_round_budget_survives_a_relaunch(self):
        ws = _ws()
        self.assertEqual(IssueLedger(ws).rounds_spent(), 0)

        # three rounds spent on the same unresolved fault, across separate processes
        for rnd in (1, 2, 3):
            IssueLedger(ws).update(rnd, version=2, critique=_critique("CONSISTENCY:X"))

        spent = IssueLedger(ws).rounds_spent()
        self.assertEqual(spent, 3)
        self.assertEqual(max(1, AC.CRITERIA_MAX_ITERS - spent),
                         AC.CRITERIA_MAX_ITERS - 3,
                         "a resumed loop must continue the budget, not restart it")

    def test_budget_cannot_go_below_one_round(self):
        """Exhausted budget still runs one round, so the loop can BLOCK with a report
        instead of silently returning an unvalidated document."""
        ws = _ws()
        for rnd in range(1, AC.CRITERIA_MAX_ITERS + 3):
            IssueLedger(ws).update(rnd, version=2, critique=_critique("CONSISTENCY:X"))
        spent = IssueLedger(ws).rounds_spent()
        self.assertGreater(spent, AC.CRITERIA_MAX_ITERS)
        self.assertEqual(max(1, AC.CRITERIA_MAX_ITERS - spent), 1)

    def test_resolved_faults_do_not_consume_budget_forever(self):
        """rounds_open stops growing once the fault is resolved, so a document that
        keeps making progress is not starved of rounds."""
        ws = _ws()
        IssueLedger(ws).update(1, version=2, critique=_critique("CONSISTENCY:X"))
        IssueLedger(ws).update(2, version=3, critique=_critique("CONSISTENCY:X"))
        IssueLedger(ws).update(3, version=4, critique=_critique())   # X resolved
        led = IssueLedger(ws)
        self.assertEqual(led.open_codes(), set())
        self.assertEqual(led.rounds_spent(), 2)


if __name__ == "__main__":
    unittest.main()
