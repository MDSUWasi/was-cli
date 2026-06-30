#!/usr/bin/env python3
import sys, os, time, logging
from .history import (
    init_repository, save_commit, get_history_log, load_db, checkout_file,
    get_status, search_history, export_file, purge_history, tag_version,
    get_statistics, rollback_file
)
from .differ import print_colored_diff
from .history import get_current_diff

logging.basicConfig(level=logging.WARNING, format="%(levelname)s: %(message)s")
logger = logging.getLogger("was")

def print_help():
    print("""
======================================================
  WAS - Document Time Machine CLI (v2.0.0)
======================================================
Commands:
  init                        Init repo
  save <file> "<msg>" ["<why>"] Commit manually
  log [<file>]               View history
  checkout <file> <ver/tag>  Restore version
  watch <file>              Auto-monitor mode
  status <file>             Check changes
  diff <file>               Show colored diff
  tag <file> <ver> <name>   Create tag
  stats <file>              Document analytics
  rollback <file>           Undo local edits
  search "<term>"          Find in history
  export <f> <v> <dest>     Export version
  purge <file>             Clean auto-saves
""")

def handle_init():
    ok, msg = init_repository()
    print(msg); return 0 if ok else 1

def handle_save():
    if len(sys.argv) < 4:
        print("Usage: was save <file> \"<msg>\" [\"<reason>\"]"); return 1
    fp, msg = sys.argv[2], sys.argv[3]
    reason = sys.argv[4] if len(sys.argv) > 4 else ""
    ok, m = save_commit(fp, msg, reason)
    print(m); return 0 if ok else 1

def handle_log():
    fp = sys.argv[2] if len(sys.argv) > 2 else None
    commits = get_history_log(fp)
    if not commits: print("No commits."); return 0
    
    db = load_db(); tags_map = db.get("tags", {})
    print("\n=== TIMELINE LOG ===")
    for c in reversed(commits):
        dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(c['timestamp']))
        tags = [k for k,v in tags_map.items() 
                if v["filepath"]==c["filepath"] and v["version_id"]==c['id']]
        tag_str = f" [\033[93mTags:{','.join(tags)}\033[0m]" if tags else ""
        print(f"\nCommit ID: \033[94m{c['id']}\033[0m{tag_str}")
        print(f"Date: {dt}; File: {c['filepath']}")
        print(f"What: \033[92m{c['message']}\033[0m")
        if c['reason']: print(f"Why: \033[93m{c['reason']}\033[0m")
        print("-"*40)
    return 0

def handle_checkout():
    if len(sys.argv) < 4:
        print("Missing args"); return 1
    try:
        checkout_file(sys.argv[2], sys.argv[3])
        print(f"\033[92mRestored to {sys.argv[3]}\033[0m"); return 0
    except Exception as e:
        print(f"Failed: {e}"); return 1

def handle_watch():
    if len(sys.argv) < 3: print("Need filepath"); return 1
    fp = sys.argv[2]
    if not os.path.exists(fp): print(f"{fp} missing"); return 1
    
    print(f"Watching '{fp}'. Ctrl+C to stop.")
    save_commit(fp, "Watch baseline", "Auto-start")
    
    mtime = os.path.getmtime(fp)
    try:
        while True:
            time.sleep(2)
            if os.path.exists(fp) and os.path.getmtime(fp) != mtime:
                mtime = os.path.getmtime(fp)
                ts = time.strftime('%Y-%m-%d %H:%M:%S')
                save_commit(fp, "Auto-save", f"Modified at {ts}", is_auto=True)
    except KeyboardInterrupt:
        print("Stopped.")
    return 0

def handle_status():
    if len(sys.argv) < 3: print("Usage: was status <file>"); return 1
    st, ins, dels = get_status(sys.argv[2])
    msgs = {
        "untracked": "🔴 Untracked",
        "missing": "⚠️ Missing",
        "corrupted_snapshot": "⚠️ Corrupted snapshot",
        "read_error": "⚠️ Read error",
        "unmodified": "🟢 Up to date",
        "modified": f"🟡 Modified (+{ins}/-{dels})"
    }
    print(msgs.get(st, f"Unknown: {st}")); return 0

def handle_diff():
    if len(sys.argv) < 3: print("Usage: was diff <file>"); return 1
    try:
        delta = get_current_diff(sys.argv[2])
        print_colored_diff(delta); return 0
    except Exception as e: print(f"Error: {e}"); return 1

def handle_tag():
    if len(sys.argv) < 5: print("Usage: was tag <f> <v> <n>"); return 1
    ok, m = tag_version(*sys.argv[2:5]); print(m); return 0 if ok else 1

def handle_stats():
    if len(sys.argv) < 3: print("Usage: was stats <file>"); return 1
    st = get_statistics(sys.argv[2])
    if not st: print("Not tracking."); return 1
    print(f"\n📊 Stats for {sys.argv[2]}:")
    print(f"  Versions: {st['total_versions']}")
    print(f"  Most active: {st['most_active_day']}")
    print(f"  Lines: {st['baseline_lines']} -> {st['latest_lines']}")
    print(f"  Growth: \033[92m+{st['growth_rate']}%\033[0m"); return 0

def handle_rollback():
    if len(sys.argv) < 3: print("Usage: was rollback <file>"); return 1
    try: rollback_file(sys.argv[2]); print("Rolled back."); return 0
    except Exception as e: print(f"Failed: {e}"); return 1

def handle_search():
    if len(sys.argv) < 3: print("Usage: was search \"<term>\""); return 1
    results = search_history(sys.argv[2])
    if not results: print(f"No matches."); return 0
    print(f"\nFound '{sys.argv[2]}':")
    for r in results:
        dt = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(r['timestamp']))
        print(f"  {r['commit_id']}: {r['filepath']} @ {dt}")
        print(f"    Lines: {r['lines']} | \"{r['message']}\"")
    return 0

def handle_export():
    if len(sys.argv) < 5: print("Usage: was export <f> <v> <dest>"); return 1
    try:
        export_file(sys.argv[2], sys.argv[3], sys.argv[4])
        print(f"Exported.{sys.argv[3]} -> {sys.argv[4]}"); return 0
    except Exception as e: print(f"Failed: {e}"); return 1

def handle_purge():
    if len(sys.argv) < 3: print("Usage: was purge <file>"); return 1
    cnt = purge_history(sys.argv[2])
    print(f"Purged {cnt} auto-saves."); return 0

def main():
    if len(sys.argv) < 2: print_help(); return 0
    cmd = sys.argv[1].lower()
    
    cmds = {
        "--version": lambda: print("WAS v2.0.0"),
        "-v": lambda: print("WAS v2.0.0"),
        "--help": print_help, "-h": print_help,
        "init": handle_init, "save": handle_save,
        "log": handle_log, "checkout": handle_checkout,
        "watch": handle_watch, "status": handle_status,
        "diff": handle_diff, "tag": handle_tag,
        "stats": handle_stats, "rollback": handle_rollback,
        "search": handle_search, "export": handle_export,
        "purge": handle_purge,
    }
    
    handler = cmds.get(cmd)
    if handler: 
        val = handler() if callable(handler) else handler
        return 0 if isinstance(val, bool) and val else (val or 0)
    print(f"Unknown: {cmd}"); print_help(); return 1

if __name__ == "__main__":
    sys.exit(main())
