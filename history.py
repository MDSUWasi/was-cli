import os
import json
import time
import shutil
import subprocess
from collections import Counter
from extractor import extract_document_text
from differ import generate_delta, format_delta_summary

WAS_DIR = ".was"
HISTORY_FILE = os.path.join(WAS_DIR, "history.json")
VERSIONS_DIR = os.path.join(WAS_DIR, "versions")

def send_notification(title, message):
    """
    Triggers a native Linux system notification using 'notify-send'.
    Falls back gracefully if the system utility is missing.
    """
    try:
        subprocess.run(["notify-send", title, message], check=False)
    except FileNotFoundError:
        # Graceful pass if notify-send is not installed on the system
        pass

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
            "version": "1.3.0"
        },
        "commits": [],
        "tracked_files": {},
        "tags": {}  # Stores: { "tag_name": { "filepath": "relative_path", "version_id": "v1" } }
    }
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(initial_db, f, indent=4)
        
    return True, "Initialized empty 'Was' repository successfully."

def load_db():
    """Safely loads the repository history database."""
    if not os.path.exists(HISTORY_FILE):
        raise RuntimeError("No 'Was' repository found. Initialize one with 'was init' first.")
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(db):
    """Saves updates back to the repository history database."""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4)

def resolve_version(db, filepath, version_or_tag):
    """
    Checks if the requested key is a custom milestone tag.
    If so, returns the associated version ID; otherwise, returns the input directly.
    """
    normalized_path = os.path.relpath(filepath)
    
    if "tags" in db and version_or_tag in db["tags"]:
        tag_data = db["tags"][version_or_tag]
        if tag_data["filepath"] == normalized_path:
            return tag_data["version_id"]
            
    return version_or_tag

def save_commit(filepath, message, reason="", is_auto=False):
    """
    Saves a new snapshot of the active file. If it is the first time tracking,
    it saves a baseline. Otherwise, it calculates changes and stores the new file version.
    """
    if not os.path.exists(filepath):
        return False, f"File {filepath} does not exist."
        
    db = load_db()
    filename = os.path.basename(filepath)
    normalized_path = os.path.relpath(filepath)
    
    try:
        current_lines = extract_document_text(filepath)
    except Exception as e:
        return False, f"Error reading document text: {str(e)}"
        
    commit_id = f"v{len(db['commits']) + 1}"
    snapshot_filename = f"{commit_id}_{filename}"
    snapshot_dest = os.path.join(VERSIONS_DIR, snapshot_filename)
    
    # 1. Handle Initial Baseline Setup
    if normalized_path not in db['tracked_files']:
        shutil.copy2(filepath, snapshot_dest)
        db['tracked_files'][normalized_path] = {"current_version": commit_id}
        
        commit_entry = {
            "id": commit_id,
            "timestamp": time.time(),
            "filepath": normalized_path,
            "message": message,
            "reason": reason,
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
    last_commit = next(c for c in reversed(db['commits']) if c['filepath'] == normalized_path and c['id'] == last_version_id)
    last_file_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
    last_lines = extract_document_text(last_file_path)
    
    if current_lines == last_lines:
        return False, f"No changes detected in '{filename}' since your last save."
        
    # Calculate difference and write the commit entry
    delta = generate_delta(last_lines, current_lines)
    shutil.copy2(filepath, snapshot_dest)
    
    commit_entry = {
        "id": commit_id,
        "timestamp": time.time(),
        "filepath": normalized_path,
        "message": message,
        "reason": reason,
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
    db = load_db()
    normalized_path = os.path.relpath(filepath)
    version_id = resolve_version(db, filepath, version_or_tag)
    
    target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == version_id), None)
    if not target_commit:
        raise ValueError(f"Version or tag '{version_or_tag}' not found for file {filepath}")
        
    snapshot_path = os.path.join(VERSIONS_DIR, target_commit['snapshot_file'])
    
    if os.path.exists(filepath):
        os.remove(filepath)
    shutil.copy2(snapshot_path, filepath)
    
    db['tracked_files'][normalized_path]["current_version"] = version_id
    save_db(db)

def get_history_log(filepath=None):
    """Retrieves all commit records, optionally filtered by a specific file."""
    db = load_db()
    commits = db['commits']
    if filepath:
        normalized_path = os.path.relpath(filepath)
        commits = [c for c in commits if c['filepath'] == normalized_path]
    return commits

def get_status(filepath):
    """Checks whether the workspace file contains unsaved changes."""
    db = load_db()
    normalized_path = os.path.relpath(filepath)
    
    if normalized_path not in db['tracked_files']:
        return "untracked", 0, 0
        
    if not os.path.exists(filepath):
        return "missing", 0, 0
        
    last_version_id = db['tracked_files'][normalized_path]["current_version"]
    last_commit = next(c for c in reversed(db['commits']) if c['filepath'] == normalized_path and c['id'] == last_version_id)
    last_file_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
    
    last_lines = extract_document_text(last_file_path)
    current_lines = extract_document_text(filepath)
    
    if last_lines == current_lines:
        return "unmodified", 0, 0
        
    delta = generate_delta(last_lines, current_lines)
    summary = format_delta_summary(delta)
    return "modified", summary["insertions"], summary["deletions"]

def get_current_diff(filepath):
    """Calculates active differences between disk file and repository."""
    db = load_db()
    normalized_path = os.path.relpath(filepath)
    
    if normalized_path not in db['tracked_files']:
        raise ValueError(f"File '{filepath}' is not tracked yet. Run 'was save' to start.")
        
    last_version_id = db['tracked_files'][normalized_path]["current_version"]
    last_commit = next(c for c in reversed(db['commits']) if c['filepath'] == normalized_path and c['id'] == last_version_id)
    last_file_path = os.path.join(VERSIONS_DIR, last_commit['snapshot_file'])
    
    last_lines = extract_document_text(last_file_path)
    current_lines = extract_document_text(filepath)
    
    return generate_delta(last_lines, current_lines)

def tag_version(filepath, target_version_id, tag_name):
    """Assigns a friendly nickname to an existing version number."""
    db = load_db()
    normalized_path = os.path.relpath(filepath)
    
    target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == target_version_id), None)
    if not target_commit:
        return False, f"Version '{target_version_id}' does not exist for this file."
        
    if "tags" not in db:
        db["tags"] = {}
        
    db["tags"][tag_name] = {
        "filepath": normalized_path,
        "version_id": target_version_id
    }
    save_db(db)
    return True, f"Successfully tagged {target_version_id} of '{filepath}' as '\033[93m{tag_name}\033[0m'!"

def get_statistics(filepath):
    """Aggregates study-habits and document growth analytics."""
    db = load_db()
    normalized_path = os.path.relpath(filepath)
    
    file_commits = [c for c in db['commits'] if c['filepath'] == normalized_path]
    if not file_commits:
        return None
        
    total_versions = len(file_commits)
    
    # Calculate most active day of the week
    days = []
    for c in file_commits:
        days.append(time.strftime('%A', time.localtime(c['timestamp'])))
    most_common_day, count = Counter(days).most_common(1)[0]
    
    # Analyze line progression
    baseline_commit = file_commits[0]
    latest_commit = file_commits[-1]
    
    baseline_lines = len(extract_document_text(os.path.join(VERSIONS_DIR, baseline_commit['snapshot_file'])))
    latest_lines = len(extract_document_text(os.path.join(VERSIONS_DIR, latest_commit['snapshot_file'])))
    
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
    db = load_db()
    normalized_path = os.path.relpath(filepath)
    
    if normalized_path not in db['tracked_files']:
        raise ValueError("File is not tracked yet. Nothing to roll back to.")
        
    last_version_id = db['tracked_files'][normalized_path]["current_version"]
    checkout_file(filepath, last_version_id)

def search_history(query_term):
    """Searches through historical contents for a term and lists exact matches."""
    db = load_db()
    results = []
    
    for commit in db['commits']:
        snapshot_path = os.path.join(VERSIONS_DIR, commit['snapshot_file'])
        if os.path.exists(snapshot_path):
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
    return results

def export_file(filepath, version_or_tag, dest_filepath):
    """Extracts a historical copy to a new location without altering active workspace."""
    db = load_db()
    normalized_path = os.path.relpath(filepath)
    version_id = resolve_version(db, filepath, version_or_tag)
    
    target_commit = next((c for c in db['commits'] if c['filepath'] == normalized_path and c['id'] == version_id), None)
    if not target_commit:
        raise ValueError(f"Version or tag '{version_or_tag}' not found for file {filepath}")
        
    snapshot_path = os.path.join(VERSIONS_DIR, target_commit['snapshot_file'])
    shutil.copy2(snapshot_path, dest_filepath)

def purge_history(filepath):
    """Deletes redundant intermediate background auto-saves to reclaim disk space."""
    db = load_db()
    normalized_path = os.path.relpath(filepath)
    
    tagged_versions = {tag_data["version_id"] for tag_data in db.get("tags", {}).values() if tag_data["filepath"] == normalized_path}
    
    purged_count = 0
    remaining_commits = []
    
    for commit in db['commits']:
        if commit['filepath'] != normalized_path:
            remaining_commits.append(commit)
            continue
            
        # Keep baselines and manually tagged milestone versions
        is_auto = "Auto-save" in commit['message']
        if is_auto and not commit['is_baseline'] and (commit['id'] not in tagged_versions):
            snapshot_path = os.path.join(VERSIONS_DIR, commit['snapshot_file'])
            if os.path.exists(snapshot_path):
                os.remove(snapshot_path)
            purged_count += 1
        else:
            remaining_commits.append(commit)
            
    if purged_count > 0:
        db['commits'] = remaining_commits
        file_commits = [c for c in remaining_commits if c['filepath'] == normalized_path]
        if file_commits:
            db['tracked_files'][normalized_path]["current_version"] = file_commits[-1]["id"]
        save_db(db)
        
    return purged_count