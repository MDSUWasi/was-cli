import os
import json
import time
import shutil
import subprocess
import uuid
import fcntl
from collections import Counter
from .extractor import extract_document_text
from .differ import generate_delta, format_delta_summary


WAS_DIR = ".was"
HISTORY_FILE = os.path.join(WAS_DIR, "history.json")
VERSIONS_DIR = os.path.join(WAS_DIR, "versions")


# --- SECURITY HELPERS ---
def validate_path(filepath):
    """
    Validates that the path does not attempt to escape the current working directory.
    Raises ValueError if path traversal or symlink attacks are detected.
    """
    abs_path = os.path.abspath(filepath)
    cwd = os.getcwd()
    
    # Resolve any symlinks to catch symlink escape attempts
    real_path = os.path.realpath(abs_path)
    real_cwd = os.path.realpath(cwd)
    
    # Normalize paths to remove '..' segments safely
    normalized_cwd = os.path.normpath(real_cwd)
    normalized_abs = os.path.normpath(real_path)
    
    # Ensure resolved path is within the workspace
    if not normalized_abs.startswith(normalized_cwd + os.sep) and normalized_abs != normalized_cwd:
        raise ValueError(f"Security violation: Path '{filepath}' attempts to access outside the workspace.")
    return normalized_abs


def sanitize_string(value, max_length=500):
    """Sanitizes user-provided strings to prevent injection issues."""
    if value is None:
        return ""
    sanitized = str(value).strip()
    # Limit length to prevent storage abuse
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    # Remove potential control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\n\t\r')
    return sanitized


def send_notification(title, message):
    """
    Triggers a native Linux system notification using 'notify-send'.
    Falls back gracefully if the system utility is missing.
    """
    try:
        subprocess.run(["notify-send", title, message], check=False, timeout=5)
    except FileNotFoundError:
        # Graceful pass if notify-send is not installed on the system
        pass
    except subprocess.TimeoutExpired:
        # Notification timed out, fail silently
        pass


class LockedFile:
    """Context manager for safe file locking with automatic cleanup."""
    
    def __init__(self, filepath, exclusive=True):
        self.filepath = filepath
        self.exclusive = exclusive
        self.fd = None
        self.lock_fd = None
    
    def __enter__(self):
        # Create lock file atomically if it doesn't exist
        lock_file = self.filepath + '.lock'
        try:
            self.lock_fd = os.open(lock_file, os.O_CREAT | os.O_RDWR, 0o644)
        except OSError:
            # Fallback if atomic creation fails
            if not os.path.exists(lock_file):
                open(lock_file, 'a').close()
            self.lock_fd = os.open(lock_file, os.O_RDWR)
        
        fd = os.open(self.filepath, os.O_RDONLY if not self.exclusive else os.O_RDWR)
        self.fd = fd
        
        lock_type = fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH
        
        try:
            fcntl.flock(self.lock_fd, lock_type)
        except BlockingIOError:
            # Lock unavailable, retry once after brief delay
            import time
            time.sleep(0.1)
            fcntl.flock(self.lock_fd, lock_type)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.fd is not None:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            except Exception:
                pass
            try:
                os.close(self.lock_fd)
            except Exception:
                pass
            try:
                os.close(self.fd)
            except Exception:
                pass
        
        # Clean up orphaned lock files occasionally (every 10th call would be ideal but keeping simple)
        lock_file = self.filepath + '.lock'
        if os.path.exists(lock_file) and os.path.getsize(lock_file) == 0:
            try:
                os.remove(lock_file)
            except Exception:
                pass
        
        return False


def init_repository():
    """
    Initializes a new Was workspace directory. Creates the hidden database 
    and directories to store file snapshots.
    """
    if os.path.exists(WAS_DIR):
        return False, "A 'Was' repository is already initialized here!"
    
    os.makedirs(WAS_DIR)
    os.makedirs(VERSIONS_DIR)
    
    initial_db = {
        "repository_info": {
            "created_at": time.time(),
            "version": "1.4.0"
        },
        "commits": [],
        "tracked_files": {},
        "tags": {}  # Stores: { "tag_name": { "filepath": "relative_path", "version_id": "v1" } }
    }
    
    temp_file = HISTORY_FILE + '.tmp'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(initial_db, f, indent=4)
        # Atomic move
        shutil.move(temp_file, HISTORY_FILE)
    except Exception:
        # Clean up temp file on failure
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise
        
    return True, "Initialized empty 'Was' repository successfully."


def load_db():
    """
    Safely loads the repository history database with JSON integrity check and locking.
    """
    if not os.path.exists(HISTORY_FILE):
        raise RuntimeError("No 'Was' repository found. Initialize one with 'was init' first.")
    
    with LockedFile(HISTORY_FILE, exclusive=False) as lock:
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
                return data
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Database corrupted (Invalid JSON): {e}")
        except Exception as e:
            raise RuntimeError(f"Error reading database: {e}")


def save_db(db):
    """
    Saves updates back to the repository history database with exclusive locking.
    """
    with LockedFile(HISTORY_FILE, exclusive=True):
        # Write to temp file first to avoid corruption on crash
        temp_file = HISTORY_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(db, f, indent=4)
        
        # Atomic move
        shutil.move(temp_file, HISTORY_FILE)


def resolve_version(db, filepath, version_or_tag):
    """
    Checks if the requested key is a custom milestone tag.
    If so, returns the associated version ID; otherwise, returns the input directly.
    Includes safety check for tag mismatch.
    """
    normalized_path = os.path.relpath(filepath)
    
    if "tags" in db and version_or_tag in db["tags"]:
        tag_data = db["tags"][version_or_tag]
        if tag_data["filepath"] == normalized_path:
            return tag_data["version_id"]
        # If tag exists but points to different file, we ignore it and treat as literal version ID
        # This prevents accidental cross-file checkout
    
    return version_or_tag


def save_commit(filepath, message, reason="", is_auto=False):
    """
    Saves a new snapshot of the active file. If it is the first time tracking,
    it saves a baseline. Otherwise, it calculates changes and stores the new file version.
    """
    # Security Check
    abs_filepath = validate_path(filepath)
    
    if not os.path.exists(abs_filepath):
        return False, f"File {abs_filepath} does not exist."
        
    db = load_db()
    filename = os.path.basename(abs_filepath)
    normalized_path = os.path.relpath(abs_filepath)
    
    try:
        current_lines = extract_document_text(abs_filepath)
    except Exception as e:
        return False, f"Error reading document text: {str(e)}"
    
    # Generate UUID-based commit ID to prevent collisions after purge
    commit_id = f"v{str(uuid.uuid4())[:8]}"
    snapshot_filename = f"{commit_id}_{filename}"
    snapshot_dest = os.path.join(VERSIONS_DIR, snapshot_filename)
    
    # 1. Handle Initial Baseline Setup
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
        save_db(db)
        
        if is_auto:
            send_notification("💾 Was Time Machine", f"Tracking started: {filename} ({commit_id})")
        return True, f"Saved base state of '{filename}' as {commit_id}."
        
    # 2. Check for modifications against the latest saved version
    last_version_id = db['tracked_files'][normalized_path]["current_version"]
    # Robust lookup for last commit
    matching_commits = [c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == last_version_id]
    if not matching_commits:
        # Fallback if data inconsistency occurs
        last_commit = next((c for c in reversed(db['commits']) if c['filepath'] == normalized_path), None)
        if not last_commit:
             return False, "Could not find previous version record."
    else:
        last_commit = matching_commits[-1] # Take the most recent match if duplicates somehow exist
        
    last_file_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
    
    if not os.path.exists(last_file_path):
        return False, f"Historical snapshot {last_commit['snapshot_file']} is missing."
    
    try:
        last_lines = extract_document_text(last_file_path)
    except Exception as e:
        return False, f"Error reading historical snapshot: {str(e)}"
    
    if current_lines == last_lines:
        return False, f"No changes detected in '{filename}' since your last save."
        
    # Calculate difference and write the commit entry
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
    save_db(db)
    
    if is_auto:
        send_notification("💾 Was Time Machine", f"Auto-saved version {commit_id} for {filename}!")
    return True, f"Saved change commit {commit_id} for '{filename}' successfully."


def checkout_file(filepath, version_or_tag):
    """Restores the workspace file to a specific historical checkpoint or tag."""
    abs_filepath = validate_path(filepath)
    normalized_path = os.path.relpath(abs_filepath)
    
    db = load_db()
    version_id = resolve_version(db, abs_filepath, version_or_tag)
    
    target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == version_id), None)
    if not target_commit:
        raise ValueError(f"Version or tag '{version_or_tag}' not found for file {filepath}")
        
    snapshot_path = os.path.join(VERSIONS_DIR, target_commit['snapshot_file'])
    
    if not os.path.exists(snapshot_path):
        raise ValueError(f"Historical snapshot '{target_commit['snapshot_file']}' is missing.")
    
    if os.path.exists(abs_filepath):
        os.remove(abs_filepath)
    try:
        shutil.copy2(snapshot_path, abs_filepath)
    except IOError as e:
        raise ValueError(f"Failed to restore file: {e}")
    
    db['tracked_files'][normalized_path]["current_version"] = version_id
    save_db(db)


def get_history_log(filepath=None):
    """Retrieves all commit records, optionally filtered by a specific file."""
    db = load_db()
    commits = db['commits']
    if filepath:
        try:
            normalized_path = os.path.relpath(validate_path(filepath))
        except ValueError:
            return []  # Return empty list for invalid paths
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
    # Safe lookup
    matching = [c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == last_version_id]
    if not matching:
        # Fallback to last known commit for this file if version ID mismatch
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
    db = load_db()
    normalized_path = os.path.relpath(abs_filepath)
    
    # Sanitize tag name - must be alphanumeric with hyphens/underscores
    clean_tag = ''.join(c if c.isalnum() or c in '-_' else '_' for c in tag_name.strip()[:50])
    if not clean_tag:
        return False, "Tag name cannot be empty or contain invalid characters."
    
    target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == target_version_id), None)
    if not target_commit:
        return False, f"Version '{target_version_id}' does not exist for this file."
        
    if "tags" not in db:
        db["tags"] = {}
        
    # Warn if tag already exists for different file
    if clean_tag in db["tags"] and db["tags"][clean_tag]["filepath"] != normalized_path:
        return False, f"Tag '{clean_tag}' already exists for a different file. Choose another name."
        
    db["tags"][clean_tag] = {
        "filepath": normalized_path,
        "version_id": target_version_id
    }
    save_db(db)
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
    
    # Calculate most active day of the week
    days = []
    for c in file_commits:
        days.append(time.strftime('%A', time.localtime(c['timestamp'])))
    
    # Safety check if days list is empty (shouldn't happen given file_commits check)
    if not days:
        return None
        
    most_common_day, count = Counter(days).most_common(1)[0]
    
    # Analyze line progression
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
    db = load_db()
    normalized_path = os.path.relpath(abs_filepath)
    
    if normalized_path not in db['tracked_files']:
        raise ValueError("File is not tracked yet. Nothing to roll back to.")
        
    last_version_id = db['tracked_files'][normalized_path]["current_version"]
    checkout_file(abs_filepath, last_version_id)


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
                # Skip corrupted snapshot files silently
                continue
    return results


def export_file(filepath, version_or_tag, dest_filepath):
    """Extracts a historical copy to a new location without altering active workspace."""
    abs_filepath = validate_path(filepath)
    # Validate destination too - ensure it's also within workspace
    abs_dest = validate_path(dest_filepath)
    
    db = load_db()
    normalized_path = os.path.relpath(abs_filepath)
    version_id = resolve_version(db, abs_filepath, version_or_tag)
    
    target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == version_id), None)
    if not target_commit:
        raise ValueError(f"Version or tag '{version_or_tag}' not found for file {filepath}")
        
    snapshot_path = os.path.join(VERSIONS_DIR, target_commit['snapshot_file'])
    
    if not os.path.exists(snapshot_path):
        raise ValueError(f"Historical snapshot is missing")
    
    # Ensure destination directory exists
    dest_dir = os.path.dirname(abs_dest)
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir)
        
    shutil.copy2(snapshot_path, abs_dest)


def purge_history(filepath):
    """Deletes redundant intermediate background auto-saves to reclaim disk space."""
    abs_filepath = validate_path(filepath)
    db = load_db()
    normalized_path = os.path.relpath(abs_filepath)
    
    # Collect tagged versions first
    tagged_versions = set()
    for tag_data in db.get("tags", {}).values():
        if tag_data["filepath"] == normalized_path:
            tagged_versions.add(tag_data["version_id"])
    
    purged_count = 0
    remaining_commits = []
    
    # Build new list of commits safely (Filter First, Then Assign)
    for commit in db['commits']:
        if commit['filepath'] != normalized_path:
            remaining_commits.append(commit)
            continue
            
        # Keep baselines and manually tagged milestone versions
        is_auto_save = "Auto-save" in commit.get('message', '') or commit.get('reason', '').startswith('Modified at ')
        
        should_keep = False
        if commit['is_baseline']:
            should_keep = True
        elif commit['id'] in tagged_versions:
            should_keep = True
        elif not is_auto_save:
            should_keep = True
            
        if not should_keep:
            # Delete the snapshot file
            snapshot_path = os.path.join(VERSIONS_DIR, commit['snapshot_file'])
            if os.path.exists(snapshot_path):
                try:
                    os.remove(snapshot_path)
                except OSError:
                    # Log warning but don't fail entire purge
                    pass
            purged_count += 1
        else:
            remaining_commits.append(commit)
            
    if purged_count > 0:
        db['commits'] = remaining_commits
        file_commits = [c for c in remaining_commits if c['filepath'] == normalized_path]
        if file_commits:
            # Ensure we point to the latest valid commit after purge
            db['tracked_files'][normalized_path]["current_version"] = file_commits[-1]["id"]
        save_db(db)
        
    return purged_count