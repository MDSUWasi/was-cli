import os
import sys
import json
import time
import shutil
import subprocess
import uuid
import logging
from collections import Counter
from .extractor import extract_document_text
from .differ import generate_delta, format_delta_summary

# Platform-safe file locking
if sys.platform != "win32":
    import fcntl
else:
    fcntl = None

logger = logging.getLogger("was.history")

WAS_DIR = ".was"
HISTORY_FILE = os.path.join(WAS_DIR, "history.json")
VERSIONS_DIR = os.path.join(WAS_DIR, "versions")
DB_VERSION = "1.4.0"


# --- SECURITY HELPERS ---
def validate_path(filepath):
    """
    Validates that the path does not attempt to escape the current working directory.
    Raises ValueError if path traversal or symlink attacks are detected.
    """
    abs_path = os.path.abspath(filepath)
    cwd = os.getcwd()
    
    real_path = os.path.realpath(abs_path)
    real_cwd = os.path.realpath(cwd)
    
    normalized_cwd = os.path.normpath(real_cwd)
    normalized_abs = os.path.normpath(real_path)
    
    if not normalized_abs.startswith(normalized_cwd + os.sep) and normalized_abs != normalized_cwd:
        raise ValueError(f"Security violation: Path '{filepath}' attempts to access outside the workspace.")
    return normalized_abs


def sanitize_string(value, max_length=500):
    """Sanitizes user-provided strings to prevent injection issues."""
    if value is None:
        return ""
    sanitized = str(value).strip()
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t\r')
    return sanitized


def send_notification(title, message):
    """Triggers a native Linux system notification. Falls back gracefully."""
    try:
        subprocess.run(["notify-send", title, message], check=False, timeout=5)
    except FileNotFoundError:
        pass
    except subprocess.TimeoutExpired:
        pass


class LockedFile:
    """Context manager for safe file locking with automatic cleanup."""
    
    def __init__(self, filepath, exclusive=True):
        self.filepath = filepath
        self.exclusive = exclusive
        self.lock_fd = None
    
    def __enter__(self):
        lock_file = self.filepath + '.lock'
        try:
            self.lock_fd = os.open(lock_file, os.O_CREAT | os.O_RDWR, 0o644)
        except OSError:
            if not os.path.exists(lock_file):
                open(lock_file, 'a').close()
            self.lock_fd = os.open(lock_file, os.O_RDWR)
        
        if fcntl is not None:
            lock_type = fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH
            try:
                fcntl.flock(self.lock_fd, lock_type)
            except BlockingIOError:
                time.sleep(0.1)
                fcntl.flock(self.lock_fd, lock_type)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_fd is not None:
            if fcntl is not None:
                try:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                except Exception:
                    pass
            try:
                os.close(self.lock_fd)
            except Exception:
                pass
        
        lock_file = self.filepath + '.lock'
        if os.path.exists(lock_file) and os.path.getsize(lock_file) == 0:
            try:
                os.remove(lock_file)
            except Exception:
                pass
        
        return False


class DBTransaction:
    """
    Context manager that holds an exclusive lock across both read and write,
    eliminating the TOCTOU race window between separate load_db() and save_db() calls.
    """
    def __init__(self):
        self.data = None
        self._lock = None
        self._dirty = False
    
    def __enter__(self):
        self._lock = LockedFile(HISTORY_FILE, exclusive=True)
        self._lock.__enter__()
        
        if not os.path.exists(HISTORY_FILE):
            raise RuntimeError("No 'Was' repository found. Initialize one with 'was init' first.")
        
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                self.data = json.loads(content)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Database corrupted (Invalid JSON): {e}")
        except Exception as e:
            raise RuntimeError(f"Error reading database: {e}")
        
        # Auto-migrate if schema version differs
        self.data = _migrate_db(self.data)
        return self
    
    def mark_dirty(self):
        """Call after modifying self.data to trigger write on exit."""
        self._dirty = True
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None and self._dirty:
            temp_file = HISTORY_FILE + '.tmp'
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self.data, f, indent=4)
                shutil.move(temp_file, HISTORY_FILE)
            except Exception:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                raise
        
        self._lock.__exit__(exc_type, exc_val, exc_tb)
        return False


def _migrate_db(db):
    """
    Migrates database schema to current version if needed.
    Currently a no-op scaffold for future schema changes.
    """
    repo_version = db.get("repository_info", {}).get("version", "unknown")
    
    if repo_version == "unknown":
        logger.warning("Repository has no version marker. Treating as legacy schema.")
        db.setdefault("repository_info", {})["version"] = DB_VERSION
        return db
    
    if repo_version != DB_VERSION:
        logger.info(f"Migrating database from v{repo_version} to v{DB_VERSION}")
        # Future migrations go here:
        # if repo_version < "1.5.0":
        #     db = _migrate_1_4_to_1_5(db)
        db["repository_info"]["version"] = DB_VERSION
    
    return db


def init_repository():
    """Initializes a new Was workspace directory."""
    if os.path.exists(WAS_DIR):
        return False, "A 'Was' repository is already initialized here!"
    
    os.makedirs(WAS_DIR)
    os.makedirs(VERSIONS_DIR)
    
    initial_db = {
        "repository_info": {
            "created_at": time.time(),
            "version": DB_VERSION
        },
        "commits": [],
        "tracked_files": {},
        "tags": {}
    }
    
    temp_file = HISTORY_FILE + '.tmp'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(initial_db, f, indent=4)
        shutil.move(temp_file, HISTORY_FILE)
    except Exception:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise
        
    logger.info("Initialized new Was repository")
    return True, "Initialized empty 'Was' repository successfully."


def load_db():
    """
    Read-only database access. For read-modify-write, use DBTransaction.
    """
    if not os.path.exists(HISTORY_FILE):
        raise RuntimeError("No 'Was' repository found. Initialize one with 'was init' first.")
    
    with LockedFile(HISTORY_FILE, exclusive=False):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
                return _migrate_db(data)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Database corrupted (Invalid JSON): {e}")
        except Exception as e:
            raise RuntimeError(f"Error reading database: {e}")


def save_db(db):
    """
    Saves updates to the database with exclusive locking.
    NOTE: For new code, prefer DBTransaction to avoid TOCTOU races.
    """
    with LockedFile(HISTORY_FILE, exclusive=True):
        temp_file = HISTORY_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)
        shutil.move(temp_file, HISTORY_FILE)


def resolve_version(db, filepath, version_or_tag):
    """Resolves a tag name to version ID, or returns the input directly."""
    normalized_path = os.path.relpath(filepath)
    
    if "tags" in db and version_or_tag in db["tags"]:
        tag_data = db["tags"][version_or_tag]
        if tag_data["filepath"] == normalized_path:
            return tag_data["version_id"]
    
    return version_or_tag


def save_commit(filepath, message, reason="", is_auto=False):
    """Saves a new snapshot. Baseline on first save, diff-check on subsequent."""
    abs_filepath = validate_path(filepath)
    
    if not os.path.exists(abs_filepath):
        return False, f"File {abs_filepath} does not exist."
    
    with DBTransaction() as txn:
        db = txn.data
        filename = os.path.basename(abs_filepath)
        normalized_path = os.path.relpath(abs_filepath)
        
        try:
            current_lines = extract_document_text(abs_filepath)
        except Exception as e:
            logger.error(f"Failed to extract text from {abs_filepath}: {e}")
            return False, f"Error reading document text: {str(e)}"
        
        commit_id = f"v{str(uuid.uuid4())[:8]}"
        snapshot_filename = f"{commit_id}_{filename}"
        snapshot_dest = os.path.join(VERSIONS_DIR, snapshot_filename)
        
        # 1. Handle Initial Baseline
        if normalized_path not in db['tracked_files']:
            try:
                shutil.copy2(abs_filepath, snapshot_dest)
            except IOError as e:
                return False, f"Failed to create snapshot: {e}"
                
            db['tracked_files'][normalized_path] = {"current_version": commit_id}
            
            commit_entry = {
                "id": commit_id,
                "timestamp": time.time(),
                "filepath": normalized_path,
                "message": sanitize_string(message),
                "reason": sanitize_string(reason),
                "snapshot_file": snapshot_filename,
                "is_baseline": True,
                "delta": []
            }
            db['commits'].append(commit_entry)
            txn.mark_dirty()
            
            if is_auto:
                send_notification("💾 Was Time Machine", f"Tracking started: {filename} ({commit_id})")
            logger.info(f"Baseline saved: {filename} ({commit_id})")
            return True, f"Saved base state of '{filename}' as {commit_id}."
        
        # 2. Check for modifications against latest version
        last_version_id = db['tracked_files'][normalized_path]["current_version"]
        matching_commits = [c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == last_version_id]
        if not matching_commits:
            last_commit = next((c for c in reversed(db['commits']) if c['filepath'] == normalized_path), None)
            if not last_commit:
                 return False, "Could not find previous version record."
        else:
            last_commit = matching_commits[-1]
            
        last_file_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
        
        if not os.path.exists(last_file_path):
            return False, f"Historical snapshot {last_commit['snapshot_file']} is missing."
        
        try:
            last_lines = extract_document_text(last_file_path)
        except Exception as e:
            logger.error(f"Failed to read historical snapshot {last_commit['snapshot_file']}: {e}")
            return False, f"Error reading historical snapshot: {str(e)}"
        
        if current_lines == last_lines:
            return False, f"No changes detected in '{filename}' since your last save."
            
        delta = generate_delta(last_lines, current_lines)
        try:
            shutil.copy2(abs_filepath, snapshot_dest)
        except IOError as e:
            return False, f"Failed to create snapshot: {e}"
        
        commit_entry = {
            "id": commit_id,
            "timestamp": time.time(),
            "filepath": normalized_path,
            "message": sanitize_string(message),
            "reason": sanitize_string(reason),
            "snapshot_file": snapshot_filename,
            "is_baseline": False,
            "delta": delta
        }
        
        db['tracked_files'][normalized_path]["current_version"] = commit_id
        db['commits'].append(commit_entry)
        txn.mark_dirty()
    
    if is_auto:
        send_notification("💾 Was Time Machine", f"Auto-saved version {commit_id} for {filename}!")
    logger.info(f"Commit saved: {filename} ({commit_id})")
    return True, f"Saved change commit {commit_id} for '{filename}' successfully."


def checkout_file(filepath, version_or_tag):
    """Restores the workspace file to a specific historical checkpoint or tag."""
    abs_filepath = validate_path(filepath)
    normalized_path = os.path.relpath(abs_filepath)
    
    with DBTransaction() as txn:
        db = txn.data
        version_id = resolve_version(db, abs_filepath, version_or_tag)
        
        target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == version_id), None)
        if not target_commit:
            raise ValueError(f"Version or tag '{version_or_tag}' not found for file {filepath}")
        
        snapshot_path = os.path.join(VERSIONS_DIR, target_commit['snapshot_file'])
        
        if not os.path.exists(snapshot_path):
            raise ValueError(f"Historical snapshot '{target_commit['snapshot_file']}' is missing.")
        
        # SAFE RESTORE: Copy to temp, then swap. Preserves workspace on failure.
        temp_restore = abs_filepath + '.was_restoring'
        try:
            shutil.copy2(snapshot_path, temp_restore)
            if os.path.exists(abs_filepath):
                os.remove(abs_filepath)
            shutil.move(temp_restore, abs_filepath)
        except IOError as e:
            if os.path.exists(temp_restore):
                os.remove(temp_restore)
            raise ValueError(f"Failed to restore file: {e}")
        
        db['tracked_files'][normalized_path]["current_version"] = version_id
        txn.mark_dirty()
    
    logger.info(f"Checkout: {filepath} -> {version_id}")


def get_history_log(filepath=None):
    """Retrieves all commit records, optionally filtered by file."""
    db = load_db()
    commits = db['commits']
    if filepath:
        try:
            normalized_path = os.path.relpath(validate_path(filepath))
        except ValueError:
            return []
        commits = [c for c in commits if c['filepath'] == normalized_path]
    return commits


def get_status(filepath):
    """Checks whether the workspace file contains unsaved changes."""
    try:
        abs_filepath = validate_path(filepath)
    except ValueError:
        return "invalid_path", 0, 0

    db = load_db()
    normalized_path = os.path.relpath(abs_filepath)
    
    if normalized_path not in db['tracked_files']:
        return "untracked", 0, 0
        
    if not os.path.exists(abs_filepath):
        return "missing", 0, 0
        
    last_version_id = db['tracked_files'][normalized_path]["current_version"]
    matching = [c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == last_version_id]
    if not matching:
        matching = [c for c in db['commits'] if c['filepath'] == normalized_path]
        if not matching:
            return "missing", 0, 0
        last_commit = sorted(matching, key=lambda x: x['timestamp'], reverse=True)[0]
    else:
        last_commit = matching[0]
        
    last_file_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
    
    if not os.path.exists(last_file_path):
        return "corrupted_snapshot", 0, 0
    
    try:
        last_lines = extract_document_text(last_file_path)
        current_lines = extract_document_text(abs_filepath)
    except Exception:
        return "read_error", 0, 0
        
    if last_lines == current_lines:
        return "unmodified", 0, 0
        
    delta = generate_delta(last_lines, current_lines)
    summary = format_delta_summary(delta)
    return "modified", summary["insertions"], summary["deletions"]


def get_current_diff(filepath):
    """Calculates active differences between disk file and repository."""
    abs_filepath = validate_path(filepath)
    db = load_db()
    normalized_path = os.path.relpath(abs_filepath)
    
    if normalized_path not in db['tracked_files']:
        raise ValueError(f"File '{filepath}' is not tracked yet. Run 'was save' to start.")
        
    last_version_id = db['tracked_files'][normalized_path]["current_version"]
    matching = [c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == last_version_id]
    if not matching:
         matching = [c for c in db['commits'] if c['filepath'] == normalized_path]
         if not matching:
             raise ValueError("No valid version found")
         last_commit = sorted(matching, key=lambda x: x['timestamp'], reverse=True)[0]
    else:
        last_commit = matching[0]
        
    last_file_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
    
    if not os.path.exists(last_file_path):
        raise ValueError(f"Historical snapshot is missing for version {last_commit['id']}")
    
    try:
        last_lines = extract_document_text(last_file_path)
        current_lines = extract_document_text(abs_filepath)
    except Exception as e:
        raise ValueError(f"Error reading files for diff calculation: {e}")
    
    return generate_delta(last_lines, current_lines)


def tag_version(filepath, target_version_id, tag_name):
    """Assigns a friendly nickname to an existing version number."""
    abs_filepath = validate_path(filepath)
    
    with DBTransaction() as txn:
        db = txn.data
        normalized_path = os.path.relpath(abs_filepath)
        
        clean_tag = ''.join(c if c.isalnum() or c in '-_' else '_' for c in tag_name.strip()[:50])
        if not clean_tag:
            return False, "Tag name cannot be empty or contain invalid characters."
        
        target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == target_version_id), None)
        if not target_commit:
            return False, f"Version '{target_version_id}' does not exist for this file."
        
        if "tags" not in db:
            db["tags"] = {}
        
        if clean_tag in db["tags"] and db["tags"][clean_tag]["filepath"] != normalized_path:
            return False, f"Tag '{clean_tag}' already exists for a different file. Choose another name."
        
        db["tags"][clean_tag] = {
            "filepath": normalized_path,
            "version_id": target_version_id
        }
        txn.mark_dirty()
    
    logger.info(f"Tagged: {target_version_id} -> {clean_tag}")
    return True, f"Successfully tagged {target_version_id} of '{filepath}' as '\033[93m{clean_tag}\033[0m'!"


def get_statistics(filepath):
    """Aggregates study-habits and document growth analytics."""
    abs_filepath = validate_path(filepath)
    db = load_db()
    normalized_path = os.path.relpath(abs_filepath)
    
    file_commits = [c for c in db['commits'] if c['filepath'] == normalized_path]
    if not file_commits:
        return None
        
    total_versions = len(file_commits)
    
    days = [time.strftime('%A', time.localtime(c['timestamp'])) for c in file_commits]
    if not days:
        return None
        
    most_common_day, count = Counter(days).most_common(1)[0]
    
    baseline_commit = file_commits[0]
    latest_commit = file_commits[-1]
    
    baseline_path = os.path.join(VERSIONS_DIR, baseline_commit['snapshot_file'])
    latest_path = os.path.join(VERSIONS_DIR, latest_commit['snapshot_file'])
    
    if not os.path.exists(baseline_path) or not os.path.exists(latest_path):
        return None
        
    try:
        baseline_lines = len(extract_document_text(baseline_path))
        latest_lines = len(extract_document_text(latest_path))
    except Exception:
        return None
    
    growth_rate = ((latest_lines - baseline_lines) / baseline_lines * 100) if baseline_lines > 0 else 0
    
    return {
        "total_versions": total_versions,
        "most_active_day": f"{most_common_day} ({count} saves)",
        "baseline_lines": baseline_lines,
        "latest_lines": latest_lines,
        "growth_rate": round(growth_rate, 2)
    }


def rollback_file(filepath):
    """Discards active workspace modifications to match the latest commit state."""
    abs_filepath = validate_path(filepath)
    normalized_path = os.path.relpath(abs_filepath)
    
    # Use a single transaction to avoid double-locking
    with DBTransaction() as txn:
        db = txn.data
        
        if normalized_path not in db['tracked_files']:
            raise ValueError("File is not tracked yet. Nothing to roll back to.")
        
        last_version_id = db['tracked_files'][normalized_path]["current_version"]
        
        # Inline checkout logic to avoid re-entering DBTransaction
        target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == last_version_id), None)
        if not target_commit:
            raise ValueError(f"Version '{last_version_id}' not found for rollback")
        
        snapshot_path = os.path.join(VERSIONS_DIR, target_commit['snapshot_file'])
        if not os.path.exists(snapshot_path):
            raise ValueError(f"Historical snapshot '{target_commit['snapshot_file']}' is missing.")
        
        temp_restore = abs_filepath + '.was_restoring'
        try:
            shutil.copy2(snapshot_path, temp_restore)
            if os.path.exists(abs_filepath):
                os.remove(abs_filepath)
            shutil.move(temp_restore, abs_filepath)
        except IOError as e:
            if os.path.exists(temp_restore):
                os.remove(temp_restore)
            raise ValueError(f"Failed to restore file: {e}")
        
        # No DB change needed — current_version already points to last_version_id
        # But we mark dirty to trigger migration write if needed
        txn.mark_dirty()
    
    logger.info(f"Rollback: {filepath} -> {last_version_id}")


def search_history(query_term):
    """Searches through historical contents for a term and lists exact matches."""
    if not query_term:
        return []
        
    db = load_db()
    results = []
    
    for commit in db['commits']:
        snapshot_path = os.path.join(VERSIONS_DIR, commit['snapshot_file'])
        if os.path.exists(snapshot_path):
            try:
                lines = extract_document_text(snapshot_path)
                matching_lines = [i + 1 for i, line in enumerate(lines) if query_term.lower() in line.lower()]
                if matching_lines:
                    results.append({
                        "commit_id": commit['id'],
                        "filepath": commit['filepath'],
                        "message": commit['message'],
                        "timestamp": commit['timestamp'],
                        "lines": matching_lines
                    })
            except Exception:
                logger.debug(f"Skipping unreadable snapshot: {commit['snapshot_file']}")
                continue
    return results


def export_file(filepath, version_or_tag, dest_filepath):
    """Extracts a historical copy without altering active workspace."""
    abs_filepath = validate_path(filepath)
    abs_dest = os.path.abspath(dest_filepath)
    
    dest_rel = os.path.relpath(abs_dest, os.getcwd())
    if dest_rel == WAS_DIR or dest_rel.startswith(WAS_DIR + os.sep):
        raise ValueError("Cannot export into the .was repository directory.")
    
    db = load_db()
    normalized_path = os.path.relpath(abs_filepath)
    version_id = resolve_version(db, abs_filepath, version_or_tag)
    
    target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == version_id), None)
    if not target_commit:
        raise ValueError(f"Version or tag '{version_or_tag}' not found for file {filepath}")
        
    snapshot_path = os.path.join(VERSIONS_DIR, target_commit['snapshot_file'])
    
    if not os.path.exists(snapshot_path):
        raise ValueError(f"Historical snapshot is missing")
    
    dest_dir = os.path.dirname(abs_dest)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    shutil.copy2(snapshot_path, abs_dest)
    logger.info(f"Exported: {filepath} v{version_id} -> {dest_filepath}")


def purge_history(filepath):
    """Deletes redundant intermediate auto-saves to reclaim disk space."""
    abs_filepath = validate_path(filepath)
    
    with DBTransaction() as txn:
        db = txn.data
        normalized_path = os.path.relpath(abs_filepath)
        
        tagged_versions = set()
        for tag_data in db.get("tags", {}).values():
            if tag_data["filepath"] == normalized_path:
                tagged_versions.add(tag_data["version_id"])
        
        purged_count = 0
        remaining_commits = []
        
        for commit in db['commits']:
            if commit['filepath'] != normalized_path:
                remaining_commits.append(commit)
                continue
                
            is_auto_save = "Auto-save" in commit.get('message', '') or commit.get('reason', '').startswith('Modified at ')
            
            should_keep = False
            if commit['is_baseline']:
                should_keep = True
            elif commit['id'] in tagged_versions:
                should_keep = True
            elif not is_auto_save:
                should_keep = True
                
            if not should_keep:
                snapshot_path = os.path.join(VERSIONS_DIR, commit['snapshot_file'])
                if os.path.exists(snapshot_path):
                    try:
                        os.remove(snapshot_path)
                    except OSError:
                        pass
                purged_count += 1
            else:
                remaining_commits.append(commit)
                
        if purged_count > 0:
            db['commits'] = remaining_commits
            file_commits = [c for c in remaining_commits if c['filepath'] == normalized_path]
            if file_commits:
                db['tracked_files'][normalized_path]["current_version"] = file_commits[-1]["id"]
            txn.mark_dirty()
        
    logger.info(f"Purged {purged_count} auto-saves for {filepath}")
    return purged_count