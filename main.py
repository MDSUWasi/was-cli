#!/usr/bin/env python3
import sys
import os
import time
from history import init_repository, save_commit, get_history_log, load_db, reconstruct_to_version
from extractor import write_document_text
from differ import format_delta_summary

def print_help():
    print("""
======================================================
  WAS - The Document Time Machine CLI (v1.0.0)
======================================================
Usage: was <command> [arguments]

Commands:
  init                           Initialize a new Was repository.
  save <file> "<msg>" ["<why>"]  Commit changes to the timeline.
  log [<file>]                   View history log of all commits.
  checkout <file> <ver>          Restore a document to a previous state.
  diff <file>                    View current pending changes.

Examples:
  was init
  was save chemistry.docx "Updated Alkene structures" "Teacher simplified notes"
  was log chemistry.docx
  was checkout chemistry.docx v1
    """)

def handle_init():
    success, message = init_repository()
    print(message)

def handle_save():
    if len(sys.argv) < 4:
        print("Error: Missing file or save message.")
        print("Usage: was save <file> \"<message>\" [\"<reason_why>\"]")
        return
        
    filepath = sys.argv[2]
    message = sys.argv[3]
    reason = sys.argv[4] if len(sys.argv) > 4 else ""
    
    success, msg = save_commit(filepath, message, reason)
    print(msg)

def handle_log():
    filepath = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        commits = get_history_log(filepath)
        if not commits:
            print("No commits found in timeline history.")
            return
            
        print("\n=== TIMELINE LOG ===")
        for c in reversed(commits):
            dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c['timestamp']))
            print(f"\nCommit ID: \033[94m{c['id']}\033[0m")
            print(f"Date:      {dt}")
            print(f"File:      {c['filepath']}")
            print(f"What:      \033[92m{c['message']}\033[0m")
            if c['reason']:
                print(f"Why:       \033[93m{c['reason']}\033[0m")
            if not c['is_baseline']:
                sum_info = format_delta_summary(c['delta'])
                print(f"Delta:     +{sum_info['insertions']} insertions, -{sum_info['deletions']} deletions")
            else:
                print("Delta:     [Initial Base Baseline Document]")
            print("-" * 40)
    except Exception as e:
        print(f"Error reading history: {e}")

def handle_checkout():
    if len(sys.argv) < 4:
        print("Error: Missing file or version ID.")
        print("Usage: was checkout <file> <version_id>")
        return
        
    filepath = sys.argv[2]
    version_id = sys.argv[3]
    normalized_path = os.path.relpath(filepath)
    
    try:
        db = load_db()
        # Fetch actual lines representing version
        restored_lines = reconstruct_to_version(db, normalized_path, version_id)
        
        # Write back to document in original format (.docx or .txt)
        write_document_text(filepath, restored_lines)
        print(f"\n\033[92mSuccess!\033[0m Successfully rolled '{filepath}' back to version \033[94m{version_id}\033[0m.")
    except Exception as e:
        print(f"Failed to travel back in time: {e}")

def main():
    if len(sys.argv) < 2:
        print_help()
        return
        
    command = sys.argv[1].lower()
    
    if command == "init":
        handle_init()
    elif command == "save":
        handle_save()
    elif command == "log":
        handle_log()
    elif command == "checkout":
        handle_checkout()
    elif command in ["help", "-h", "--help"]:
        print_help()
    else:
        print(f"Unknown command: '{command}'")
        print_help()

if __name__ == "__main__":
    main()