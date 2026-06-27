import difflib


def generate_delta(old_lines, new_lines):
    """
    Compares two lists of text lines and returns a list representing the 
    unified differences (the delta patch) between them.
    
    This is extremely efficient because we only save what changed, 
    rather than duplicating your entire notes file!
    """
    return list(difflib.unified_diff(
        old_lines, 
        new_lines, 
        fromfile='original', 
        tofile='modified', 
        lineterm=''
    ))


def format_delta_summary(delta_lines):
    """
    Scans through a list of unified diff lines to calculate and return
    the exact number of line additions and deletions.
    
    This gives you a quick numerical metric of how your study notes changed.
    """
    added = 0
    removed = 0
    for line in delta_lines:
        # Standard diffs use '+' for additions and '-' for deletions.
        # We skip the standard file comparison headers (+++ and ---).
        if line.startswith('+') and not line.startswith('+++'):
            added += 1
        elif line.startswith('-') and not line.startswith('---'):
            removed += 1
            
    return {
        "insertions": added,
        "deletions": removed
    }


def print_colored_diff(delta_lines):
    """
    Renders human-friendly, color-coded diff output in the terminal.
    - Green lines represent new additions (+).
    - Red lines represent deleted sections (-).
    - Cyan lines represent the changed locations or line-group range headers (@@).
    """
    if not delta_lines:
        print("🟢 No differences found. Both files are identical!")
        return
        
    for line in delta_lines:
        if line.startswith('+') and not line.startswith('+++'):
            # Light Green for added text
            print(f"\033[92m{line}\033[0m")
        elif line.startswith('-') and not line.startswith('---'):
            # Light Red for removed text
            print(f"\033[91m{line}\033[0m")
        elif line.startswith('@@'):
            # Light Cyan for coordinate markers
            print(f"\033[96m{line}\033[0m")
        else:
            # Normal text for context lines (with a space prefix)
            print(line)