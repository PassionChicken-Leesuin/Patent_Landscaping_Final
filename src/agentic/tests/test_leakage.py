import unittest

from src.agentic import leakage as LK


class TestLeakage(unittest.TestCase):
    def test_blocked_url_patcit(self):
        self.assertIsNotNone(LK.is_blocked_url("https://patcit.github.io/benchmark"))

    def test_blocked_url_doi(self):
        self.assertIsNotNone(
            LK.is_blocked_url("https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0295587"))

    def test_blocked_title_antiseed(self):
        self.assertIsNotNone(
            LK.is_blocked_result("https://example.com/x", "Building the anti-seed for patent search"))

    def test_clean_result_passes(self):
        self.assertIsNone(
            LK.is_blocked_result("https://en.wikipedia.org/wiki/Hydrogen_storage",
                                 "Hydrogen storage - Wikipedia"))

    def test_content_scan_two_hits_blocked(self):
        text = ("This fake PatCit README describes the anti-seed construction "
                "and the expansion-level assignment of each patent.")
        blocked, hits = LK.content_leak_scan(text)
        self.assertTrue(blocked)
        self.assertGreaterEqual(len(hits), 2)

    def test_content_scan_single_generic_hit_allowed(self):
        text = "A survey of seed patents in energy storage research over two decades."
        blocked, _ = LK.content_leak_scan(text)
        self.assertFalse(blocked)


if __name__ == "__main__":
    unittest.main()
