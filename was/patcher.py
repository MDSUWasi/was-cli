"""
PATCHER MODULE - For future delta-only storage when needed.
Currently unused since WAS keeps full snapshots (simpler, safer).
To enable: tweak history.py to apply delta during checkout instead of copying full files.
"""

def apply_delta(base_lines, delta_lines):
    """Applies unified diff patch to base lines."""
    if not delta_lines:
        return base_lines[:]
    
    result = []
    src_idx = 0
    in_hunk = False
    
    for line in delta_lines:
        if line.startswith(('---', '+++')):
            continue
        if line.startswith('@@'):
            in_hunk = True
            continue
        
        if not in_hunk:
            continue
        
        if line.startswith(' ') or line == '':
            if src_idx < len(base_lines):
                result.append(base_lines[src_idx])
                src_idx += 1
        elif line.startswith('-'):
            if src_idx < len(base_lines):
                src_idx += 1
        elif line.startswith('+'):
            result.append(line[1:])
    
    result.extend(base_lines[src_idx:])
    return result
