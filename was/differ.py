import difflib

def generate_delta(old, new):
    """Unified diff between two line lists."""
    return list(difflib.unified_diff(old, new, 
                                     fromfile='original', tofile='modified', lineterm=''))

def format_delta_summary(delta):
    """Count insertions/deletions."""
    added = sum(1 for l in delta if l.startswith('+') and not l.startswith('+++'))
    removed = sum(1 for l in delta if l.startswith('-') and not l.startswith('---'))
    return {"insertions": added, "deletions": removed}

def print_colored_diff(delta):
    """Terminal output with colors."""
    if not delta:
        print("🟢 No differences found!")
        return
    for line in delta:
        if line.startswith('+') and not line.startswith('+++'):
            print(f"\033[92m{line}\033[0m")
        elif line.startswith('-') and not line.startswith('---'):
            print(f"\033[91m{line}\033[0m")
        elif line.startswith('@@'):
            print(f"\033[96m{line}\033[0m")
        else:
            print(line)
