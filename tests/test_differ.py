"""
Unit tests for the WAS differ module.
Run with: python -m pytest tests/ -v
"""
import unittest
from was.differ import generate_delta, format_delta_summary


class TestGenerateDelta(unittest.TestCase):
    def test_identical_files_produce_empty_delta(self):
        old = ["Line 1", "Line 2"]
        new = ["Line 1", "Line 2"]
        delta = generate_delta(old, new)
        self.assertEqual(delta, [])

    def test_addition_detected(self):
        old = ["Line 1"]
        new = ["Line 1", "Line 2"]
        delta = generate_delta(old, new)
        self.assertTrue(any(line.startswith('+') and 'Line 2' in line for line in delta))

    def test_deletion_detected(self):
        old = ["Line 1", "Line 2"]
        new = ["Line 1"]
        delta = generate_delta(old, new)
        self.assertTrue(any(line.startswith('-') and 'Line 2' in line for line in delta))

    def test_modification_detected(self):
        old = ["Old text"]
        new = ["New text"]
        delta = generate_delta(old, new)
        self.assertTrue(any(line.startswith('-') for line in delta))
        self.assertTrue(any(line.startswith('+') for line in delta))


class TestFormatDeltaSummary(unittest.TestCase):
    def test_counts_match(self):
        old = ["Line 1", "Line 2", "Line 3"]
        new = ["Line 1", "Modified 2", "Line 3", "Line 4"]
        delta = generate_delta(old, new)
        summary = format_delta_summary(delta)
        self.assertIsInstance(summary, dict)
        self.assertIn("insertions", summary)
        self.assertIn("deletions", summary)
        self.assertGreater(summary["insertions"], 0)

    def test_empty_delta_zero_counts(self):
        summary = format_delta_summary([])
        self.assertEqual(summary["insertions"], 0)
        self.assertEqual(summary["deletions"], 0)

    def test_headers_not_counted_as_changes(self):
        # Unified diff headers (--- and +++) should not be counted
        delta = ["--- original", "+++ modified"]
        summary = format_delta_summary(delta)
        self.assertEqual(summary["insertions"], 0)
        self.assertEqual(summary["deletions"], 0)


if __name__ == "__main__":
    unittest.main()