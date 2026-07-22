import unittest

import pandas as pd

from src.agentic import config as AC
from src.agentic.boundary_probe import measured_questions, probe_boundaries
from src.agentic.judge import mock_pool
from src.agentic.schemas import ScopeQuestion


def _q(qid, default="exclude"):
    return ScopeQuestion(id=qid, question=f"{qid}?", why_it_matters="author guess",
                         options=["include", "exclude"], tentative_default=default,
                         broad_rule="include supply/production hydrogen patents",
                         narrow_rule="storage only")


class TestBoundaryProbe(unittest.TestCase):
    def setUp(self):
        # 20 supply/production patents (should FLIP) + 20 pure-storage (should NOT)
        rows = []
        for i in range(20):
            rows.append({"record_id": f"s{i}", "patent_id": f"s{i}",
                         "title": "Hydrogen production and fuel cell supply", "abstract": "generates hydrogen"})
        for i in range(20):
            rows.append({"record_id": f"t{i}", "patent_id": f"t{i}",
                         "title": "Metal hydride storage tank", "abstract": "stores hydrogen in a hydride vessel"})
        self.pool = pd.DataFrame(rows)

    def test_flip_measurement_and_filter(self):
        import tempfile, os
        tmp = os.path.join(tempfile.gettempdir(), "probe_test.jsonl")
        ranked = probe_boundaries([_q("Q1")], self.pool, mock_pool(3),
                                  "Hydrogen Storage", tmp, workers=8)
        self.assertEqual(len(ranked), 1)          # boundary flips 20/40 -> kept
        q, flip, n = ranked[0]
        self.assertGreaterEqual(flip, 15)          # ~20 supply patents flip
        self.assertLessEqual(flip, 25)

    def test_measured_text_rewrites_why(self):
        import tempfile, os
        tmp = os.path.join(tempfile.gettempdir(), "probe_test2.jsonl")
        ranked = probe_boundaries([_q("Q1")], self.pool, mock_pool(3),
                                  "Hydrogen Storage", tmp, workers=8)
        mq = measured_questions(ranked)
        self.assertIn("측정", mq[0].why_it_matters)

    def test_below_threshold_dropped(self):
        # a pool where nothing flips (all pure storage) -> boundary dropped
        pure = self.pool[self.pool["record_id"].str.startswith("t")].reset_index(drop=True)
        import tempfile, os
        tmp = os.path.join(tempfile.gettempdir(), "probe_test3.jsonl")
        ranked = probe_boundaries([_q("Q1")], pure, mock_pool(3),
                                  "Hydrogen Storage", tmp, workers=8)
        self.assertEqual(len(ranked), 0)


if __name__ == "__main__":
    unittest.main()
