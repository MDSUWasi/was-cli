"""Tests for patcher module (unused but good to have)."""
import unittest
from was.patcher import apply_delta
from was.differ import generate_delta


class TestPatcherLogic(unittest.TestCase):
    def test_empty_delta_returns_copy(self):
        base = ["Line 1", "Line 2"]
        result = apply_delta(base, [])
        self.assertEqual(result, base)
        self.assertIsNot(result, base)

    def test_roundtrip_generate_then_apply(self):
        """Actually important - can we rebuild from diff?"""
        base = ["Line 1", "Line 2", "Line 3"]
        modified = ["Line 1", "Line 2 modified", "Line 3", "Line 4"]
        delta = generate_delta(base, modified)
        reconstructed = apply_delta(base, delta)
        self.assertEqual(reconstructed, modified)

    def test_additions_work(self):
        base = ["A", "B"]
        delta = [
            "@@ -1,2 +1,3 @@",
            " A",
            " B",
            "+C",
        ]
        result = apply_delta(base, delta)
        self.assertEqual(result, ["A", "B", "C"])

    def test_deletions_work(self):
        base = ["A", "B", "C"]
        delta = [
            "@@ -1,3 +1,2 @@",
            " A",
            "-B",
            " C",
        ]
        self.assertEqual(apply_delta(base, delta), ["A", "C"])

    def test_skip_headers(self):
        base = ["A"]
        delta = ["--- original", "+++ modified", "@@ -1,1 +1,1 @@", " A"]
        self.assertEqual(apply_delta(base, delta), ["A"])

    def test_no_hunks_copy_only(self):
        base = ["A", "B"]
        result = apply_delta(base, ["--- x", "+++ y"])
        self.assertEqual(result, base)


if __name__ == "__main__":
    unittest.main()
