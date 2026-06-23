import difflib

def generate_delta(old_lines, new_lines):
    """
    Compares old text lines and new text lines, generating a unified diff.
    This diff outlines EXACTLY what changed, where, and how.
    """
    # difflib.unified_diff generates the classic patch format
    diff_generator = difflib.unified_diff(
        old_lines, 
        new_lines, 
        fromfile='original', 
        tofile='modified', 
        lineterm=''
    )
    return list(diff_generator)

def format_delta_summary(delta_lines):
    """
    Analyzes raw delta lines and returns a readable summary
    detailing additions, deletions, and modifications.
    """
    added = 0
    removed = 0
    for line in delta_lines:
        if line.startswith('+') and not line.startswith('+++'):
            added += 1
        elif line.startswith('-') and not line.startswith('---'):
            removed += 1
            
    return {
        "insertions": added,
        "deletions": removed
    }