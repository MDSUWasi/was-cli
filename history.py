import os
import json
import time
import shutil
from extractor import extract_document_text
from differ import generate_delta
from patcher import apply_delta

WAS_DIR = ".was"
HISTORY_FILE = os.path.join(WAS_DIR, "history.json")
BASELINE_DIR = os.path.join(WAS_DIR, "baselines")

def init_repository():
    """Initializes a new Was time machine repository in the current working directory."""
    if os.path.exists(WAS_DIR):
        return False, "A 'Was' repository is already initialized here!"
        
    os.makedirs(WAS_DIR)
    os.makedirs(BASELINE_DIR)
    
    initial_db = {
        "repository_info": {
            "created_at": time.time(),
            "version": "1.0.0"
        },
        "commits": [],
        "tracked_files": {}
    }
    
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(initial_db, f, indent=4)
        
    return True, "Initialized empty 'Was' time-machine repository in " + os.path.abspath(WAS_DIR)

def load_db():
    """Helper to load historical changes from the json database."""
    if not os.path.exists(HISTORY_FILE):
        raise RuntimeError("No 'Was' repository found in this directory. Run 'was init' first.")
    with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(db):
    """Helper to serialize updates to our database."""
    with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, indent=4)

def save_commit(filepath, message, reason=""):
    """
    Saves a snapshot/delta commit of the selected file.
    If it's the first commit, it saves the file as the baseline.
    If it's modified, it stores only the patch (delta).
    """
    if not os.path.exists(filepath):
        return False, f"File {filepath} does not exist."
        
    db = load_db()
    filename = os.path.basename(filepath)
    normalized_path = os.path.relpath(filepath)
    
    # 1. Extract raw lines of current document state
    try:
        current_lines = extract_document_text(filepath)
    except Exception as e:
        return False, f"Error parsing document: {str(e)}"
        
    commit_time = time.time()
    commit_id = f"v{len(db['commits']) + 1}"
    
    # 2. Check if file has a baseline saved yet
    if normalized_path not in db['tracked_files']:
        # Save baseline text representation to baseline directory
        baseline_filename = f"{commit_id}_{filename}.txt"
        baseline_path = os.path.join(BASELINE_DIR, baseline_filename)
        
        with open(baseline_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(current_lines))
            
        db['tracked_files'][normalized_path] = {
            "baseline_file": baseline_filename,
            "current_version": commit_id
        }
        
        commit_entry = {
            "id": commit_id,
            "timestamp": commit_time,
            "filepath": normalized_path,
            "message": message,
            "reason": reason,
            "is_baseline": True,
            "delta": [] # Baselines have empty deltas
        }
        
        db['commits'].append(commit_entry)
        save_db(db)
        return True, f"Successfully saved base state of '{filename}' as {commit_id}."
        
    # 3. If file is tracked, reconstruct the previous state first to calculate the delta
    reconstructed_lines = reconstruct_to_version(db, normalized_path, "latest")
    
    # Check if there are actually any changes made
    if reconstructed_lines == current_lines:
        return False, f"No changes detected in '{filename}' since your last save!"
        
    # Generate delta
    delta = generate_delta(reconstructed_lines, current_lines)
    
    # Write commit record
    commit_entry = {
        "id": commit_id,
        "timestamp": commit_time,
        "filepath": normalized_path,
        "message": message,
        "reason": reason,
        "is_baseline": False,
        "delta": delta
    }
    
    db['tracked_files'][normalized_path]["current_version"] = commit_id
    db['commits'].append(commit_entry)
    save_db(db)
    
    return True, f"Saved change commit {commit_id} for '{filename}' successfully."

def reconstruct_to_version(db, filepath, target_version_id="latest"):
    """
    Sequentially applies the delta chain starting from the baseline
    to recreate the requested historical version of a file.
    """
    tracked_info = db['tracked_files'].get(filepath)
    if not tracked_info:
        raise ValueError(f"File {filepath} is not currently tracked by Was.")
        
    baseline_path = os.path.join(BASELINE_DIR, tracked_info['baseline_file'])
    
    # Start with baseline text
    with open(baseline_path, 'r', encoding='utf-8') as f:
        current_text = f.read().splitlines()
        
    # Gather and filter commits relevant to this file
    file_commits = [c for c in db['commits'] if c['filepath'] == filepath]
    
    for commit in file_commits:
        # Skip the baseline commit (already loaded)
        if commit['is_baseline']:
            continue
            
        # Apply patch to advance version step by step
        current_text = apply_delta(current_text, commit['delta'])
        
        # Break once we've reached our destination version
        if commit['id'] == target_version_id:
            break
            
    return current_text

def get_history_log(filepath=None):
    """Retrieves list of saved snapshots, filtered by a file if requested."""
    db = load_db()
    commits = db['commits']
    if filepath:
        normalized_path = os.path.relpath(filepath)
        commits = [c for c in commits if c['filepath'] == normalized_path]
    return commits