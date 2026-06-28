"""
Unit tests for the WAS patcher module (currently unused but tested for future activation).
Run with: python -m pytest tests/ -v
"""
import unittest
from was.patcher import apply_delta
from was.differ import generate_delta


class TestApplyDelta(unittest.TestCase):
    def test_empty_delta_returns_copy(self):
        base = ["Line 1", "Line 2"]
        result = apply_delta(base, [])
        self.assertEqual(result, base)
        self.assertIsNot(result, base)  # Must be a copy

    def test_roundtrip_generate_then_apply(self):
        base = ["Line 1", "Line 2", "Line 3"]
        modified = ["Line 1", "Line 2 modified", "Line 3", "Line 4"]
        delta = generate_delta(base, modified)
        reconstructed = apply_delta(base, delta)
        self.assertEqual(reconstructed, modified)

    def test_pure_addition(self):
        base = ["A", "B"]
        delta = [
            "@@ -1,2 +1,3 @@",
            " A",
            " B",
            "+C",
        ]
        result = apply_delta(base, delta)
        self.assertEqual(result, ["A", "B", "C"])

    def test_pure_deletion(self):
        base = ["A", "B", "C"]
        delta = [
            "@@ -1,3 +1,2 @@",
            " A",
            "-B",
            " C",
        ]
        result = apply_delta(base, delta)
        self.assertEqual(result, ["A", "C"])

    def test_skips_file_headers(self):
        base = ["A"]
        delta = [
            "--- original",
            "+++ modified",
            "@@ -1,1 +1,1 @@",
            " A",
        ]
        result = apply_delta(base, delta)
        self.assertEqual(result, ["A"])

    def test_no_hunks_returns_base_copy(self):
        base = ["A", "B"]
        delta = ["--- original", "+++ modified"]
        result = apply_delta(base, delta)
        self.assertEqual(result, ["A", "B"])


if __name__ == "__main__":
    unittest.main()