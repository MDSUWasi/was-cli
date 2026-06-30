"""Core tests for WAS history - the brain of this thing."""
import os, json, shutil, tempfile
import unittest
from was.history import (
    init_repository, save_commit, checkout_file, get_status,
    tag_version, rollback_file, search_history, export_file,
    purge_history, load_db, _validate_path as validate_path
)


class InitTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_creates_was_folder(self):
        success, msg = init_repository()
        self.assertTrue(success)
        self.assertTrue(os.path.exists(".was"))
        self.assertTrue(os.path.exists(".was/versions"))

    def test_double_init_fails_gracefully(self):
        init_repository()
        ok, msg = init_repository()
        self.assertFalse(ok)

    def test_schema_looks_right(self):
        init_repository()
        db = load_db()
        self.assertIn("commits", db)
        self.assertIn("tracked_files", db)
        self.assertEqual(db["repository_info"]["version"], "2.0.0")


class CommitTests(unittest.TestCase):
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

    def test_baseline_on_first_save(self):
        success, _ = save_commit(self.test_file, "Initial")
        self.assertTrue(success)
        db = load_db()
        self.assertTrue(db["commits"][0]["is_baseline"])

    def test_new_line_gets_saved(self):
        save_commit(self.test_file, "Start")
        with open(self.test_file, 'a') as f:
            f.write("Line 4\n")
        ok, msg = save_commit(self.test_file, "Added line 4")
        self.assertTrue(ok)
        self.assertEqual(len(load_db()["commits"]), 2)

    def test_same_content_skips(self):
        save_commit(self.test_file, "First")
        ok, msg = save_commit(self.test_file, "Again")
        self.assertFalse(ok)

    def test_missing_file_is_no_problem(self):
        ok, msg = save_commit("ghost.txt", "Whoops")
        self.assertFalse(ok)


# Checkout + rollback together makes sense
class RestoreTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("Original content\n")
        _, _ = save_commit(self.test_file, "Baseline", "Test")
        db = load_db()
        self.version_id = db["commits"][0]["id"]

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_checkout_restores_old_version(self):
        with open(self.test_file, 'w') as f:
            f.write("New stuff\n")
        save_commit(self.test_file, "Changed")
        
        checkout_file(self.test_file, self.version_id)
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Original content\n")

    def test_rollback_clears_local_edits(self):
        with open(self.test_file, 'w') as f:
            f.write("Junk edits\n")
        rollback_file(self.test_file)
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Original content\n")

    def test_bad_version_raises(self):
        with self.assertRaises(ValueError):
            checkout_file(self.test_file, "vFAKE_ID_NOTHING_HERE")


class TagTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("Content\n")
        save_commit(self.test_file, "Baseline")
        self.version_id = load_db()["commits"][0]["id"]

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_simple_tag(self):
        ok, msg = tag_version(self.test_file, self.version_id, "milestone")
        self.assertTrue(ok)
        self.assertIn("milestone", load_db()["tags"])

    def test_tag_used_in_checkout(self):
        tag_version(self.test_file, self.version_id, "old")
        with open(self.test_file, 'w') as f:
            f.write("Change\n")
        checkout_file(self.test_file, "old")
        with open(self.test_file, 'r') as f:
            self.assertEqual(f.read(), "Content\n")

    def test_shared_tag_between_files_rejected(self):
        tag_version(self.test_file, self.version_id, "dup-tag")
        
        with open("other.txt", 'w') as f:
            f.write("Other\n")
        save_commit("other.txt", "Second file")
        db = load_db()
        other_ver = db["commits"][-1]["id"]

        ok, msg = tag_version("other.txt", other_ver, "dup-tag")
        self.assertFalse(ok)


class SearchTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("Light behaves both as a wave and particle\n")
        save_commit(self.test_file, "Bio")

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_can_find_word(self):
        results = search_history("wave-particle duality")
        self.assertEqual(len(results), 1)

    def test_lowercase_doesnt_matter(self):
        results = search_history("LIGHT")
        self.assertEqual(len(results), 1)

    def test_garbage_search_returns_none(self):
        self.assertEqual(len(search_history("xyz123abc")), 0)


class StatusChecks(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        self.test_file = "notes.txt"
        with open(self.test_file, 'w') as f:
            f.write("Original\n")
        save_commit(self.test_file, "Base")

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_clean_is_green(self):
        st, ins, dels = get_status(self.test_file)
        self.assertEqual(st, "unmodified")

    def test_modified_shows_ins_and_dels(self):
        with open(self.test_file, 'a') as f:
            f.write("More\n")
        st, i, d = get_status(self.test_file)
        self.assertEqual(st, "modified")
        self.assertGreater(i, 0)

    def test_missing_file_detected(self):
        os.remove(self.test_file)
        st, _, _ = get_status(self.test_file)
        self.assertEqual(st, "missing")


# Path validation tests
class SecurityValidation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_traversal_blocked(self):
        with self.assertRaises(ValueError):
            validate_path("../../etc/passwd")

    def test_absolute_outside_workspace_blocks(self):
        with self.assertRaises(ValueError):
            validate_path("/etc/passwd")

    def test_normal_path_passes(self):
        p = validate_path("notes.txt")
        self.assertTrue(p.startswith(self.test_dir))


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.makedirs("subfolder", exist_ok=True)
        os.chdir(self.test_dir)
        init_repository()
        with open("notes.txt", 'w') as f:
            f.write("Exportable\n")
        save_commit("notes.txt", "Base")
        self.ver = load_db()["commits"][0]["id"]

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_export_to_subfolder(self):
        dest = "subfolder/copy.txt"
        export_file("notes.txt", self.ver, dest)
        self.assertTrue(os.path.exists(dest))
        with open(dest) as f:
            self.assertEqual(f.read(), "Exportable\n")

    # Testing outside workspace should work
    def test_export_anywhere(self):
        dest = "/tmp/was_test_export.txt"
        export_file("notes.txt", self.ver, dest)
        self.assertTrue(os.path.exists(dest))
        os.remove(dest)  # cleanup

    def cant_write_inside_was_dir(self):
        with self.assertRaises(ValueError):
            export_file("notes.txt", self.ver, ".was/stolen.txt")


class PurgeTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.chdir(self.test_dir)
        init_repository()
        with open("notes.txt", 'w') as f:
            f.write("V1\n")
        save_commit("notes.txt", "Manual")

    def tearDown(self):
        os.chdir("/tmp")
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_auto_saves_get_deleted(self):
        with open("notes.txt", 'a') as f:
            f.write("V2\n")
        save_commit("notes.txt", "Auto-save snapshot", "Modified at 2026-01-01", is_auto=True)
        
        with open("notes.txt", 'a') as f:
            f.write("V3\n")
        save_commit("notes.txt", "Manual")

        cnt = purge_history("notes.txt")
        self.assertEqual(cnt, 1)

        db = load_db()
        for c in db["commits"]:
            if c["filepath"] == "notes.txt":
                self.assertNotIn("Auto-save", c.get('message', ''))


if __name__ == "__main__":
    unittest.main()
