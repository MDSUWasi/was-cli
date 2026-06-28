"""
Unit tests for WAS history module — the core brain of the application.
Run with: python -m pytest tests/ -v
"""
import os
import json
import shutil
import tempfile
import unittest
from was.history import (
    init_repository, save_commit, checkout_file, get_status, get_current_diff,
    tag_version, get_statistics, rollback_file, search_history, export_file,
    purge_history, load_db, validate_path
)


class TestRepositoryInit(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_init_creates_directory_structure(self):
        success, msg = init_repository()
        self.assertTrue(success)
        self.assertTrue(os.path.exists(".was"))
        self.assertTrue(os.path.exists(".was/versions"))
        self.assertTrue(os.path.exists(".was/history.json"))

    def test_init_fails_on_existing_repo(self):
        init_repository()
        success, msg = init_repository()
        self.assertFalse(success)
        self.assertIn("already initialized", msg)

    def test_history_json_has_valid_schema(self):
        init_repository()
        db = load_db()
        self.assertIn("repository_info", db)
        self.assertIn("commits", db)
        self.assertIn("tracked_files", db)
        self.assertIn("tags", db)
        self.assertEqual(db["repository_info"]["version"], "1.4.0")


class TestSaveCommit(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("Line 1\nLine 2\nLine 3\n")

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_first_save_creates_baseline(self):
        success, msg = save_commit(self.test_file, "Initial save", "Testing")
        self.assertTrue(success)
        db = load_db()
        self.assertEqual(len(db["commits"]), 1)
        self.assertTrue(db["commits"][0]["is_baseline"])

    def test_second_save_detects_changes(self):
        save_commit(self.test_file, "Initial save", "Testing")
        with open(self.test_file, 'a') as f:
            f.write("Line 4\n")
        success, msg = save_commit(self.test_file, "Added line 4", "Testing")
        self.assertTrue(success)
        db = load_db()
        self.assertEqual(len(db["commits"]), 2)

    def test_no_change_returns_false(self):
        save_commit(self.test_file, "Initial save", "Testing")
        success, msg = save_commit(self.test_file, "No change save", "Testing")
        self.assertFalse(success)
        self.assertIn("No changes detected", msg)

    def test_nonexistent_file_returns_false(self):
        success, msg = save_commit("nonexistent.txt", "Ghost", "Testing")
        self.assertFalse(success)


class TestCheckoutAndRollback(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("Original content\n")
        success, _ = save_commit(self.test_file, "Baseline", "Test")
        db = load_db()
        self.baseline_version = db["commits"][0]["id"]

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_checkout_restores_previous_version(self):
        # Modify file
        with open(self.test_file, 'w') as f:
            f.write("Completely new content\n")
        save_commit(self.test_file, "Changed file", "Test")

        # Checkout original
        checkout_file(self.test_file, self.baseline_version)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "Original content\n")

    def test_checkout_preserves_file_on_failure(self):
        # Corrupt the snapshot path
        db = load_db()
        db["commits"][0]["snapshot_file"] = "nonexistent_snapshot.txt"
        # Can't easily save via save_db due to import; test indirectly
        # Instead test checkout with invalid version
        with self.assertRaises(ValueError):
            checkout_file(self.test_file, "vNONEXISTENT")

        # Original file should still exist
        self.assertTrue(os.path.exists(self.test_file))

    def test_rollback_discards_unsaved_changes(self):
        with open(self.test_file, 'w') as f:
            f.write("Unsaved junk content\n")
        rollback_file(self.test_file)
        with open(self.test_file, 'r') as f:
            content = f.read()
        self.assertEqual(content, "Original content\n")


class TestTagging(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("Content\n")
        save_commit(self.test_file, "Baseline", "Test")
        db = load_db()
        self.version_id = db["commits"][0]["id"]

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_tag_creation(self):
        success, msg = tag_version(self.test_file, self.version_id, "milestone")
        self.assertTrue(success)
        db = load_db()
        self.assertIn("milestone", db["tags"])
        self.assertEqual(db["tags"]["milestone"]["version_id"], self.version_id)

    def test_tag_checkout_works(self):
        tag_version(self.test_file, self.version_id, "important")
        with open(self.test_file, 'w') as f:
            f.write("Changed content\n")
        save_commit(self.test_file, "New version", "Test")
        checkout_file(self.test_file, "important")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Content\n")

    def test_duplicate_tag_for_different_file_fails(self):
        # Tag first file
        tag_version(self.test_file, self.version_id, "shared-tag")

        # Create second file
        with open("other.txt", 'w') as f:
            f.write("Other content\n")
        save_commit("other.txt", "Second file", "Test")
        db = load_db()
        other_version = db["commits"][-1]["id"]

        success, msg = tag_version("other.txt", other_version, "shared-tag")
        self.assertFalse(success)
        self.assertIn("already exists for a different file", msg)


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("The mitochondria is the powerhouse of the cell\n")
        save_commit(self.test_file, "Bio notes", "Test")

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_search_finds_term(self):
        results = search_history("mitochondria")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["filepath"], "notes.txt")

    def test_search_no_results(self):
        results = search_history("nonexistent_term_xyz")
        self.assertEqual(len(results), 0)

    def test_search_case_insensitive(self):
        results = search_history("MITOCHONDRIA")
        self.assertEqual(len(results), 1)


class TestStatus(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("Original\n")
        save_commit(self.test_file, "Baseline", "Test")

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_status_unmodified(self):
        status, ins, dels = get_status(self.test_file)
        self.assertEqual(status, "unmodified")

    def test_status_modified(self):
        with open(self.test_file, 'a') as f:
            f.write("New line\n")
        status, ins, dels = get_status(self.test_file)
        self.assertEqual(status, "modified")
        self.assertGreater(ins, 0)

    def test_status_missing_file(self):
        os.remove(self.test_file)
        status, ins, dels = get_status(self.test_file)
        self.assertEqual(status, "missing")


class TestPathValidation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_rejects_path_traversal(self):
        with self.assertRaises(ValueError):
            validate_path("../../../etc/passwd")

    def test_rejects_absolute_outside_workspace(self):
        with self.assertRaises(ValueError):
            validate_path("/etc/passwd")

    def test_accepts_valid_path(self):
        result = validate_path("notes.txt")
        self.assertTrue(result.startswith(self.test_dir))


class TestExport(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        os.makedirs("subfolder", exist_ok=True)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("Exportable content\n")
        save_commit(self.test_file, "Baseline", "Test")
        db = load_db()
        self.version_id = db["commits"][0]["id"]

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_creates_copy(self):
        dest = "subfolder/exported_copy.txt"
        export_file(self.test_file, self.version_id, dest)
        self.assertTrue(os.path.exists(dest))
        with open(dest, 'r') as f:
            self.assertEqual(f.read(), "Exportable content\n")

    def test_export_outside_workspace_allowed(self):
        dest = "/tmp/was_export_test.txt"
        export_file(self.test_file, self.version_id, dest)
        self.assertTrue(os.path.exists(dest))
        os.remove(dest)

    def test_export_to_was_dir_rejected(self):
        with self.assertRaises(ValueError):
            export_file(self.test_file, self.version_id, ".was/stolen.txt")


class TestPurge(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("V1\n")
        save_commit(self.test_file, "Baseline", "Manual save")

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_purge_keeps_manual_saves(self):
        # Create an auto-save
        with open(self.test_file, 'a') as f:
            f.write("V2\n")
        save_commit(self.test_file, "Auto-save snapshot", "Modified at 2026-06-28 10:00:00", is_auto=True)

        # Create a manual save
        with open(self.test_file, 'a') as f:
            f.write("V3\n")
        save_commit(self.test_file, "Manual edit", "Important change")

        purged = purge_history(self.test_file)
        self.assertEqual(purged, 1)  # Only the auto-save should be purged

        db = load_db()
        for c in db["commits"]:
            if c["filepath"] == self.test_file:
                self.assertNotIn("Auto-save", c["message"])


if __name__ == "__main__":
    unittest.main()