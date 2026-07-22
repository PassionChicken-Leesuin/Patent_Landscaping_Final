import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.agentic import config as AC
from src.agentic.hitl import HITL
from src.agentic.schemas import HITLQuestion
from src.agentic.workspace import Workspace


def _question() -> HITLQuestion:
    return HITLQuestion(id="Q1", question="Include generic robot control?",
                        why_needed="scope boundary", options=["include", "exclude"])


class TestHITLRunIsolation(unittest.TestCase):
    def test_same_run_can_reuse_human_answer_for_resume(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(AC, "AGENTIC_DIR", Path(tmp)):
            ws = Workspace("run-a").ensure()
            first = HITL(ws, mode="off", stage="criteria")
            first._log(_question(), "include", "human")

            resumed = HITL(ws, mode="off", stage="boundary-loop")
            out = resumed.ask([_question()])

            self.assertEqual(out[0]["answer"], "include")
            self.assertEqual(Workspace.read_jsonl(ws.human_qa_jsonl)[-1]["answered_by"],
                             "human_prior")

    def test_different_run_does_not_inherit_human_answer(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(AC, "AGENTIC_DIR", Path(tmp)):
            ws_a = Workspace("run-a").ensure()
            HITL(ws_a, mode="off", stage="criteria")._log(
                _question(), "include", "human")

            ws_b = Workspace("run-b").ensure()
            out = HITL(ws_b, mode="off", stage="criteria").ask([_question()])

            self.assertNotEqual(out[0]["answer"], "include")
            self.assertEqual(Workspace.read_jsonl(ws_b.human_qa_jsonl)[-1]["answered_by"],
                             "auto")
            self.assertFalse((Path(tmp) / "_profiles").exists())


if __name__ == "__main__":
    unittest.main()
