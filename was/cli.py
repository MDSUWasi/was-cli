#!/usr/bin/env python3
import sys
import os
import time
import logging
from .history import (
    init_repository, save_commit, get_history_log, load_db, checkout_file,
    get_status, get_current_diff, tag_version, get_statistics, rollback_file,
    search_history, export_file, purge_history
)
from .differ import print_colored_diff

logger = logging.getLogger("was")

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")


def print_help():
    """Prints the help menu."""
    print("""
======================================================
  WAS - Your Document Time Machine CLI (v1.4.0)
======================================================
Usage: was <command> [arguments]

Core Commands:
  init                           Initialize a new Was repository.
  save <file> "<msg>" ["<why>"]  Commit changes manually to the timeline.
  log [<file>]                   View history log of all commits.
  checkout <file> <ver/tag>      Restore a document to a previous state.
  watch <file>                   Launch foreground monitoring to auto-save updates.

Extended Power Commands:
  status <file>                  Show if file changed compared to last save.
  diff <file>                    View colorized differences in current terminal.
  tag <file> <ver> <tag_name>    Assign a milestone name (e.g. 'exam-prep').
  stats <file>                   View study habits and document statistics.
  rollback <file>                Quickly revert uncommitted active edits.
  search "<term>"               Search entire history files for a word/phrase.
  export <file> <ver/tag> <dest> Export specific version copy without swapping active.
  purge <file>                   Clean up automatic background saves to free disk space.

Other:
  --version, -v                  Print WAS version.
  --help, -h                     Show this help message.
    """)


def handle_init():
    success, message = init_repository()
    print(message)
    return 0 if success else 1


def handle_save():
    if len(sys.argv) < 4:
        print("Error: Missing arguments.\nUsage: was save <file> \"<msg>\" [\"<reason>\"]")
        return 1
    filepath = sys.argv[2]
    message = sys.argv[3]
    reason = sys.argv[4] if len(sys.argv) > 4 else ""
    success, msg = save_commit(filepath, message, reason)
    print(msg)
    return 0 if success else 1


def handle_log():
    filepath = sys.argv[2] if len(sys.argv) > 2 else None
    try:
        commits = get_history_log(filepath)
        if not commits:
            print("No commits found in timeline history.")
            return 0

        db = load_db()
        tags_map = db.get("tags", {})

        print("\n=== TIMELINE LOG ===")
        for c in reversed(commits):
            dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c['timestamp']))
            associated_tags = [name for name, t in tags_map.items()
                             if t["filepath"] == c["filepath"] and t["version_id"] == c['id']]
            tag_str = f" [\033[93mTags: {', '.join(associated_tags)}\033[0m]" if associated_tags else ""

            print(f"\nCommit ID: \033[94m{c['id']}\033[0m{tag_str}")
            print(f"Date:      {dt}")
            print(f"File:      {c['filepath']}")
            print(f"What:      \033[92m{c['message']}\033[0m")
            if c['reason']:
                print(f"Why:       \033[93m{c['reason']}\033[0m")
            print("-" * 40)
        return 0
    except Exception as e:
        logger.error(f"Log command failed: {e}", exc_info=True)
        print(f"Error reading history: {e}")
        return 1


def handle_checkout():
    if len(sys.argv) < 4:
        print("Error: Missing file or version/tag ID.")
        return 1
    filepath = sys.argv[2]
    version_or_tag = sys.argv[3]
    try:
        checkout_file(filepath, version_or_tag)
        print(f"\n\033[92mSuccess!\033[0m Reverted '{filepath}' back to \033[94m{version_or_tag}\033[0m.")
        return 0
    except Exception as e:
        logger.error(f"Checkout failed: {e}", exc_info=True)
        print(f"Failed to travel back: {e}")
        return 1


def handle_watch():
    if len(sys.argv) < 3:
        print("Error: Specify a target file to watch.")
        return 1
    filepath = sys.argv[2]
    if not os.path.exists(filepath):
        print(f"Error: {filepath} does not exist.")
        return 1

    print(f"👁️  Was is watching '{filepath}'... Press Ctrl+C to stop.")
    success, msg = save_commit(filepath, "Initial baseline via Watch mode", "Auto-start monitoring")
    print(msg)
    if not success:
        return 1

    last_mtime = os.path.getmtime(filepath)
    try:
        while True:
            time.sleep(2)
            if os.path.exists(filepath):
                current_mtime = os.path.getmtime(filepath)
                if current_mtime != last_mtime:
                    last_mtime = current_mtime
                    timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S')
                    print(f"Modification detected at {timestamp_str}. Processing change...")
                    time.sleep(0.5)
                    success, msg = save_commit(
                        filepath=filepath,
                        message="Auto-save snapshot",
                        reason=f"Modified at {timestamp_str}",
                        is_auto=True
                    )
                    print(msg)
    except KeyboardInterrupt:
        print("\nStopping Watcher mode. Your time machine remains active and healthy.")
    return 0


def handle_status():
    if len(sys.argv) < 3:
        print("Error: Usage: was status <file>")
        return 1
    filepath = sys.argv[2]
    try:
        status, ins, dels = get_status(filepath)
        if status == "untracked":
            print(f"🔴 File '{filepath}' is \033[91muntracked\033[0m by Was.")
        elif status == "missing":
            print(f"⚠️ Tracked file '{filepath}' is \033[31mmissing from workspace\033[0m.")
        elif status == "corrupted_snapshot":
            print(f"⚠️ Tracked file '{filepath}' has a \033[31mcorrupted or missing snapshot\033[0m.")
        elif status == "read_error":
            print(f"⚠️ Error reading file '{filepath}'. Check file accessibility.")
        elif status == "unmodified":
            print(f"🟢 File '{filepath}' has \033[92mno unsaved changes\033[0m.")
        elif status == "modified":
            print(f"🟡 File '{filepath}' is \033[93mModified\033[0m (Unsaved: +{ins} insertions, -{dels} deletions).")
        else:
            print(f"⚠️ Unknown status for '{filepath}'.")
        return 0
    except Exception as e:
        logger.error(f"Status command failed: {e}", exc_info=True)
        print(f"Error checking status: {e}")
        return 1


def handle_diff():
    if len(sys.argv) < 3:
        print("Error: Usage: was diff <file>")
        return 1
    filepath = sys.argv[2]
    try:
        delta = get_current_diff(filepath)
        print_colored_diff(delta)
        return 0
    except Exception as e:
        logger.error(f"Diff command failed: {e}", exc_info=True)
        print(f"Error executing diff: {e}")
        return 1


def handle_tag():
    if len(sys.argv) < 5:
        print("Error: Usage: was tag <file> <ver> <tag_name>")
        return 1
    filepath = sys.argv[2]
    ver = sys.argv[3]
    tag_name = sys.argv[4]
    try:
        success, msg = tag_version(filepath, ver, tag_name)
        print(msg)
        return 0 if success else 1
    except Exception as e:
        logger.error(f"Tag command failed: {e}", exc_info=True)
        print(f"Failed to tag: {e}")
        return 1


def handle_stats():
    if len(sys.argv) < 3:
        print("Error: Usage: was stats <file>")
        return 1
    filepath = sys.argv[2]
    try:
        stats = get_statistics(filepath)
        if not stats:
            print("No statistics available. Start tracking this file first!")
            return 1
        print(f"\n📊 \033[95mSTUDY ANALYTICS FOR {filepath}\033[0m")
        print(f"  * Total Versions Stacked:  {stats['total_versions']}")
        print(f"  * High Activity Day:      {stats['most_active_day']}")
        print(f"  * Baseline Line Count:     {stats['baseline_lines']} lines")
        print(f"  * Current Line Count:      {stats['latest_lines']} lines")
        print(f"  * Document Line Growth:    \033[92m+{stats['growth_rate']}%\033[0m")
        return 0
    except Exception as e:
        logger.error(f"Stats command failed: {e}", exc_info=True)
        print(f"Error calculating stats: {e}")
        return 1


def handle_rollback():
    if len(sys.argv) < 3:
        print("Error: Usage: was rollback <file>")
        return 1
    filepath = sys.argv[2]
    try:
        rollback_file(filepath)
        print(f"\033[92mSuccess!\033[0m Discarded all active unsaved edits for '{filepath}'.")
        return 0
    except Exception as e:
        logger.error(f"Rollback command failed: {e}", exc_info=True)
        print(f"Rollback failed: {e}")
        return 1


def handle_search():
    if len(sys.argv) < 3:
        print("Error: Usage: was search \"<term>\"")
        return 1
    term = sys.argv[2]
    try:
        results = search_history(term)
        if not results:
            print(f"No occurrences of '{term}' found in document logs.")
            return 0
        print(f"\n🔍 Found '{term}' in the following historical backups:")
        for r in results:
            dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r['timestamp']))
            print(f"  * Version: \033[94m{r['commit_id']}\033[0m | File: {r['filepath']} | Date: {dt}")
            print(f"    Lines matched: {r['lines']}")
            print(f"    Save context: \"{r['message']}\"")
        return 0
    except Exception as e:
        logger.error(f"Search command failed: {e}", exc_info=True)
        print(f"Search failed: {e}")
        return 1


def handle_export():
    if len(sys.argv) < 5:
        print("Error: Usage: was export <file> <ver/tag> <destination>")
        return 1
    filepath = sys.argv[2]
    ver_tag = sys.argv[3]
    dest = sys.argv[4]
    try:
        export_file(filepath, ver_tag, dest)
        print(f"\033[92mSuccess!\033[0m Version {ver_tag} successfully written to custom copy '{dest}'.")
        return 0
    except Exception as e:
        logger.error(f"Export command failed: {e}", exc_info=True)
        print(f"Export failed: {e}")
        return 1


def handle_purge():
    if len(sys.argv) < 3:
        print("Error: Usage: was purge <file>")
        return 1
    filepath = sys.argv[2]
    try:
        count = purge_history(filepath)
        print(f"\033[92mPurge Complete!\033[0m Deleted {count} intermediate auto-save caches.")
        return 0
    except Exception as e:
        logger.error(f"Purge command failed: {e}", exc_info=True)
        print(f"Purge failed: {e}")
        return 1


def main():
    if len(sys.argv) < 2:
        print_help()
        return 0

    command = sys.argv[1].lower()

    if command in ("--version", "-v"):
        print("WAS v1.4.0")
        return 0
    elif command in ("--help", "-h"):
        print_help()
        return 0
    elif command == "init":
        return handle_init()
    elif command == "save":
        return handle_save()
    elif command == "log":
        return handle_log()
    elif command == "checkout":
        return handle_checkout()
    elif command == "watch":
        return handle_watch()
    elif command == "status":
        return handle_status()
    elif command == "diff":
        return handle_diff()
    elif command == "tag":
        return handle_tag()
    elif command == "stats":
        return handle_stats()
    elif command == "rollback":
        return handle_rollback()
    elif command == "search":
        return handle_search()
    elif command == "export":
        return handle_export()
    elif command == "purge":
        return handle_purge()
    else:
        print(f"Unknown command: '{command}'\n")
        print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())