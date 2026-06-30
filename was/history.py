import os, sys, json, time, shutil, subprocess, uuid, logging
from collections import Counter
from .extractor import extract_document_text
from .differ import generate_delta, format_delta_summary

if sys.platform != "win32":
    import fcntl
else:
    fcntl = None

logger = logging.getLogger("was.history")

WAS_DIR = ".was"
HISTORY_FILE = os.path.join(WAS_DIR, "history.json")
VERSIONS_DIR = os.path.join(WAS_DIR, "versions")
DB_VERSION = "1.4.0"


def _validate_path(filepath):
    """Check path stays within workspace."""
    abs_path = os.path.abspath(filepath)
    cwd = os.getcwd()
    if not os.path.realpath(abs_path).startswith(os.path.realpath(cwd)):
        raise ValueError(f"Path '{filepath}' tries to escape workspace.")
    return abs_path


def _sanitize(value, max_len=500):
    """Clean user input strings."""
    if not value:
        return ""
    s = str(value).strip()[:max_len]
    return ''.join(c for c in s if ord(c) >= 32 or c in '\n\t\r')


def _send_notify(title, message):
    """Linux system notification fallback."""
    try:
        subprocess.run(["notify-send", title, message], check=False, timeout=5)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


class _LockFile:
    """Simple file lock context manager."""
    def __init__(self, filepath, exclusive=True):
        self.filepath, self.exclusive = filepath, exclusive
        self.fd = None
    
    def __enter__(self):
        lock_file = self.filepath + '.lock'
        try:
            self.fd = os.open(lock_file, os.O_CREAT | os.O_RDWR, 0o644)
        except OSError:
            open(lock_file, 'a').close()
            self.fd = os.open(lock_file, os.O_RDWR)
        
        if fcntl:
            try:
                fcntl.flock(self.fd, fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
            except BlockingIOError:
                time.sleep(0.1)
                fcntl.flock(self.fd, fcntl.LOCK_EX if self.exclusive else fcntl.LOCK_SH)
        return self
    
    def __exit__(self, *args):
        if self.fd:
            if fcntl:
                try: fcntl.flock(self.fd, fcntl.LOCK_UN)
                except: pass
            os.close(self.fd)
        lock_file = self.filepath + '.lock'
        if os.path.exists(lock_file) and os.path.getsize(lock_file) == 0:
            os.remove(lock_file)


def init_repository():
    """Initialize new Was repo."""
    if os.path.exists(WAS_DIR):
        return False, "Repository exists here!"
    os.makedirs(WAS_DIR)
    os.makedirs(VERSIONS_DIR)
    
    db = {
        "repository_info": {"created_at": time.time(), "version": DB_VERSION},
        "commits": [], "tracked_files": {}, "tags": {}
    }
    
    tmp = HISTORY_FILE + '.tmp'
    with open(tmp, 'w') as f:
        json.dump(db, f, indent=4)
    shutil.move(tmp, HISTORY_FILE)
    return True, "Repository initialized."


def load_db():
    """Read database."""
    if not os.path.exists(HISTORY_FILE):
        raise RuntimeError("No repository found. Run 'was init'.")
    
    with _LockFile(HISTORY_FILE, exclusive=False):
        with open(HISTORY_FILE, 'r') as f:
            data = json.load(f)
        return _migrate_db(data)


def _migrate_db(db):
    """Handle schema migrations."""
    ver = db.get("repository_info", {}).get("version", "unknown")
    if ver != DB_VERSION:
        logger.info(f"Migrating {ver} -> {DB_VERSION}")
        db.setdefault("repository_info", {})["version"] = DB_VERSION
    return db


def save_commit(filepath, message, reason="", is_auto=False):
    """Save new snapshot."""
    abs_path = _validate_path(filepath)
    if not os.path.exists(abs_path):
        return False, f"{abs_path} does not exist."
    
    rel_path = os.path.relpath(abs_path)
    
    with _LockFile(HISTORY_FILE, exclusive=True) as lf:
        with open(HISTORY_FILE, 'r') as f:
            db = json.load(f)
        db = _migrate_db(db)
        
        try:
            current_lines = extract_document_text(abs_path)
        except Exception as e:
            return False, f"Text extraction failed: {e}"
        
        commit_id = f"v{uuid.uuid4().hex[:8]}"
        snap_file = f"{commit_id}_{os.path.basename(abs_path)}"
        snap_dest = os.path.join(VERSIONS_DIR, snap_file)
        
        if rel_path not in db['tracked_files']:
            shutil.copy2(abs_path, snap_dest)
            db['tracked_files'][rel_path] = {"current_version": commit_id}
            
            commit = {
                "id": commit_id, "timestamp": time.time(),
                "filepath": rel_path, "message": _sanitize(message),
                "reason": _sanitize(reason), "snapshot_file": snap_file,
                "is_baseline": True, "delta": []
            }
            db['commits'].append(commit)
            
            with open(HISTORY_FILE + '.tmp', 'w') as f:
                json.dump(db, f, indent=4)
            shutil.move(HISTORY_FILE + '.tmp', HISTORY_FILE)
            
            if is_auto:
                _send_notify("Was Time Machine", f"Tracking started: {snap_file}")
            return True, f"Saved baseline as {commit_id}"
        
        last_id = db['tracked_files'][rel_path]["current_version"]
        last_commit = next((c for c in db['commits'] 
                           if c['filepath'] == rel_path and c['id'] == last_id), None)
        if not last_commit:
            return False, "Previous version record missing."
        
        last_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
        if not os.path.exists(last_path):
            return False, f"Snapshot {last_commit['snapshot_file']} missing."
        
        try:
            last_lines = extract_document_text(last_path)
        except Exception as e:
            return False, f"History read error: {e}"
        
        if current_lines == last_lines:
            return False, "No changes detected."
        
        delta = generate_delta(last_lines, current_lines)
        shutil.copy2(abs_path, snap_dest)
        
        commit = {
            "id": commit_id, "timestamp": time.time(),
            "filepath": rel_path, "message": _sanitize(message),
            "reason": _sanitize(reason), "snapshot_file": snap_file,
            "is_baseline": False, "delta": delta
        }
        db['tracked_files'][rel_path]["current_version"] = commit_id
        db['commits'].append(commit)
        
        with open(HISTORY_FILE + '.tmp', 'w') as f:
            json.dump(db, f, indent=4)
        shutil.move(HISTORY_FILE + '.tmp', HISTORY_FILE)
    
    if is_auto:
        _send_notify("Was Time Machine", f"Auto-saved {commit_id}")
    return True, f"Commit {commit_id} saved successfully."


def checkout_file(filepath, version_or_tag):
    """Restore to specific version."""
    abs_path = _validate_path(filepath)
    rel_path = os.path.relpath(abs_path)
    
    with _LockFile(HISTORY_FILE, exclusive=True) as lf:
        with open(HISTORY_FILE, 'r') as f:
            db = json.load(f)
        
        if version_or_tag in db.get("tags", {}):
            tag_data = db["tags"][version_or_tag]
            if tag_data["filepath"] == rel_path:
                version_or_tag = tag_data["version_id"]
        
        target = next((c for c in db['commits'] 
                       if c['filepath'] == rel_path and c['id'] == version_or_tag), None)
        if not target:
            raise ValueError(f"Version '{version_or_tag}' not found")
        
        snap_path = os.path.join(VERSIONS_DIR, target['snapshot_file'])
        if not os.path.exists(snap_path):
            raise ValueError(f"Snapshot '{target['snapshot_file']}' missing.")
        
        temp = abs_path + '.was_tmp'
        shutil.copy2(snap_path, temp)
        if os.path.exists(abs_path):
            os.remove(abs_path)
        shutil.move(temp, abs_path)
        
        db['tracked_files'][rel_path]["current_version"] = version_or_tag
        with open(HISTORY_FILE + '.tmp', 'w') as f:
            json.dump(db, f, indent=4)
        shutil.move(HISTORY_FILE + '.tmp', HISTORY_FILE)


def get_history_log(filepath=None):
    """Get commit log."""
    db = load_db()
    commits = db['commits']
    if filepath:
        normalized = os.path.relpath(_validate_path(filepath))
        commits = [c for c in commits if c['filepath'] == normalized]
    return commits


def get_status(filepath):
    """Check if file has uncommitted changes."""
    try:
        abs_path = _validate_path(filepath)
    except ValueError:
        return "invalid_path", 0, 0
    
    db = load_db()
    rel_path = os.path.relpath(abs_path)
    
    if rel_path not in db['tracked_files']:
        return "untracked", 0, 0
    if not os.path.exists(abs_path):
        return "missing", 0, 0
    
    last_id = db['tracked_files'][rel_path]["current_version"]
    last_commit = next((c for c in db['commits'] 
                       if c['filepath'] == rel_path and c['id'] == last_id), None)
    if not last_commit:
        return "missing", 0, 0
    
    last_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
    if not os.path.exists(last_path):
        return "corrupted_snapshot", 0, 0
    
    try:
        last_lines = extract_document_text(last_path)
        current_lines = extract_document_text(abs_path)
    except:
        return "read_error", 0, 0
    
    if last_lines == current_lines:
        return "unmodified", 0, 0
    
    delta = generate_delta(last_lines, current_lines)
    summary = format_delta_summary(delta)
    return "modified", summary["insertions"], summary["deletions"]

def get_current_diff(filepath):
    """Get delta between current file and last commit."""
    try:
        abs_path = _validate_path(filepath)
        db = load_db()
        rel_path = os.path.relpath(abs_path)
        
        if rel_path not in db['tracked_files']:
            return []
        
        last_id = db['tracked_files'][rel_path]["current_version"]
        last_commit = next((c for c in db['commits'] 
                           if c['filepath'] == rel_path and c['id'] == last_id), None)
        
        if not last_commit:
            return []
        
        last_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
        last_lines = extract_document_text(last_path)
        current_lines = extract_document_text(abs_path)
        
        return generate_delta(last_lines, current_lines)
    except Exception as e:
        logger.error(f"Diff calculation failed: {e}")
        return []

def rollback_file(filepath):
    """Discard unsaved changes, restore last commit."""
    abs_path = _validate_path(filepath)
    rel_path = os.path.relpath(abs_path)
    
    with _LockFile(HISTORY_FILE, exclusive=True):
        with open(HISTORY_FILE, 'r') as f:
            db = json.load(f)
        
        if rel_path not in db['tracked_files']:
            raise ValueError("File not tracked.")
        
        last_id = db['tracked_files'][rel_path]["current_version"]
        last_commit = next((c for c in db['commits'] 
                           if c['filepath'] == rel_path and c['id'] == last_id), None)
        if not last_commit:
            raise ValueError(f"Version {last_id} not found")
        
        snap_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
        if not os.path.exists(snap_path):
            raise ValueError("Snapshot missing.")
        
        temp = abs_path + '.was_tmp'
        shutil.copy2(snap_path, temp)
        if os.path.exists(abs_path):
            os.remove(abs_path)
        shutil.move(temp, abs_path)


def tag_version(filepath, version_id, tag_name):
    """Create named tag for version."""
    abs_path = _validate_path(filepath)
    rel_path = os.path.relpath(abs_path)
    
    clean_tag = ''.join(c if c.isalnum() or c in '-_' else '_' 
                       for c in tag_name.strip()[:50])
    if not clean_tag:
        return False, "Invalid tag name."
    
    with _LockFile(HISTORY_FILE, exclusive=True):
        with open(HISTORY_FILE, 'r') as f:
            db = json.load(f)
        
        commit = next((c for c in db['commits'] 
                      if c['filepath'] == rel_path and c['id'] == version_id), None)
        if not commit:
            return False, f"Version '{version_id}' not found."
        
        db.setdefault("tags", {})
        if clean_tag in db["tags"]:
            if db["tags"][clean_tag]["filepath"] != rel_path:
                return False, f"Tag '{clean_tag}' used by different file."
        
        db["tags"][clean_tag] = {"filepath": rel_path, "version_id": version_id}
        
        with open(HISTORY_FILE + '.tmp', 'w') as f:
            json.dump(db, f, indent=4)
        shutil.move(HISTORY_FILE + '.tmp', HISTORY_FILE)
    
    return True, f"Tagged as '{clean_tag}'!"


def get_statistics(filepath):
    """Get document analytics."""
    abs_path = _validate_path(filepath)
    db = load_db()
    rel_path = os.path.relpath(abs_path)
    
    commits = [c for c in db['commits'] if c['filepath'] == rel_path]
    if not commits:
        return None
    
    days = [time.strftime('%A', time.localtime(c['timestamp'])) for c in commits]
    most_common_day, count = Counter(days).most_common(1)[0]
    
    baseline = extract_document_text(os.path.join(VERSIONS_DIR, commits[0]['snapshot_file']))
    latest = extract_document_text(os.path.join(VERSIONS_DIR, commits[-1]['snapshot_file']))
    
    growth = ((len(latest) - len(baseline)) / len(baseline) * 100) if baseline else 0
    
    return {
        "total_versions": len(commits),
        "most_active_day": f"{most_common_day} ({count} saves)",
        "baseline_lines": len(baseline),
        "latest_lines": len(latest),
        "growth_rate": round(growth, 2)
    }


def search_history(query):
    """Find text across all versions."""
    if not query:
        return []
    db = load_db()
    results = []
    
    for commit in db['commits']:
        snap_path = os.path.join(VERSIONS_DIR, commit['snapshot_file'])
        if os.path.exists(snap_path):
            try:
                lines = extract_document_text(snap_path)
                matches = [i+1 for i, l in enumerate(lines) if query.lower() in l.lower()]
                if matches:
                    results.append({
                        "commit_id": commit['id'],
                        "filepath": commit['filepath'],
                        "message": commit['message'],
                        "timestamp": commit['timestamp'],
                        "lines": matches
                    })
            except:
                continue
    return results


def export_file(filepath, version_or_tag, dest):
    """Export version without affecting workspace."""
    abs_path = _validate_path(filepath)
    abs_dest = os.path.abspath(dest)
    
    db = load_db()
    rel_path = os.path.relpath(abs_path)
    
    if version_or_tag in db.get("tags", {}):
        tg = db["tags"][version_or_tag]
        if tg["filepath"] == rel_path:
            version_or_tag = tg["version_id"]
    
    commit = next((c for c in db['commits'] 
                   if c['filepath'] == rel_path and c['id'] == version_or_tag), None)
    if not commit:
        raise ValueError(f"Version '{version_or_tag}' not found")
    
    snap_path = os.path.join(VERSIONS_DIR, commit['snapshot_file'])
    if not os.path.exists(snap_path):
        raise ValueError("Snapshot missing.")
    
    ddir = os.path.dirname(abs_dest)
    if ddir and not os.path.exists(ddir):
        os.makedirs(ddir)
    shutil.copy2(snap_path, abs_dest)


def purge_history(filepath):
    """Remove intermediate auto-saves."""
    abs_path = _validate_path(filepath)
    rel_path = os.path.relpath(abs_path)
    
    with _LockFile(HISTORY_FILE, exclusive=True):
        with open(HISTORY_FILE, 'r') as f:
            db = json.load(f)
        
        tagged = set()
        for t in db.get("tags", {}).values():
            if t["filepath"] == rel_path:
                tagged.add(t["version_id"])
        
        kept = []
        purged = 0
        for c in db['commits']:
            if c['filepath'] != rel_path:
                kept.append(c)
                continue
            
            is_auto = "Auto-save" in c.get('message', '') or c.get('reason', '').startswith('Modified at ')
            if c['is_baseline'] or c['id'] in tagged or not is_auto:
                kept.append(c)
            else:
                spath = os.path.join(VERSIONS_DIR, c['snapshot_file'])
                if os.path.exists(spath):
                    os.remove(spath)
                purged += 1
        
        db['commits'] = kept
        file_commits = [c for c in kept if c['filepath'] == rel_path]
        if file_commits:
            db['tracked_files'][rel_path]["current_version"] = file_commits[-1]["id"]
        
        with open(HISTORY_FILE + '.tmp', 'w') as f:
            json.dump(db, f, indent=4)
        shutil.move(HISTORY_FILE + '.tmp', HISTORY_FILE)
    
    return purged
