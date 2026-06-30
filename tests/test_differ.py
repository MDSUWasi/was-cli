"""Differ module tests."""
import unittest
from was.differ import generate_delta, format_delta_summary


class DeltaTests(unittest.TestCase):
    def test_same_files_give_empty_delta(self):
        old = new = ["Line 1", "Line 2"]
        self.assertEqual(generate_delta(old, new), [])

    def test_added_lines_show_plus(self):
        delta = generate_delta(["A"], ["A", "B"])
        self.assertTrue(any(l.startswith('+') for l in delta))

    def test_removed_lines_show_minus(self):
        delta = generate_delta(["A", "B"], ["A"])
        self.assertTrue(any(l.startswith('-') for l in delta))

    def test_changed_both_markers(self):
        delta = generate_delta(["Old"], ["New"])
        has_del = any(l.startswith('-') for l in delta)
        has_add = any(l.startswith('+') for l in delta)
        self.assertTrue(has_del and has_add)


class SummaryTests(unittest.TestCase):
    def test_counts_return_dict(self):
        old = ["1", "2", "3"]
        new = ["1", "changed", "3", "4"]
        s = format_delta_summary(generate_delta(old, new))
        self.assertIsInstance(s, dict)
        self.assertIn("insertions", s)
        self.assertIn("deletions", s)

    def test_zero_for_empty_input(self):
        s = format_delta_summary([])
        self.assertEqual(s["insertions"], 0)
        self.assertEqual(s["deletions"], 0)

    def test_header_lines_not_counted(self):
        s = format_delta_summary(["--- a", "+++ b"])
        self.assertEqual(s["insertions"], 0)
        self.assertEqual(s["deletions"], 0)

if __name__ == "__main__":
    unittest.main()
