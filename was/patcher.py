"""
PATCHER MODULE - Available for future optimization when storing deltas-only.
Currently unused as WAS stores full snapshots for simplicity and reliability.
To activate: Modify history.py to apply delta during checkout instead of copying full files.
"""


def apply_delta(base_lines, delta_lines):
    """
    Applies a unified diff patch (delta_lines) to a list of base text lines (base_lines).
    This reconstructs the next historical version of your document.

    Handles insertions (+), deletions (-), unchanged context lines ( ),
    and variable header formats via clean linear iteration.
    """
    if not delta_lines:
        return base_lines[:]

    result = []
    src_idx = 0
    in_hunk = False

    for line in delta_lines:
        # Skip file-level headers (--- original, +++ modified)
        if line.startswith('---') or line.startswith('+++'):
            continue

        # Hunk headers mark start of actual patch content (@@ ... @@)
        if line.startswith('@@'):
            in_hunk = True
            continue

        if not in_hunk:
            continue

        # Context lines: copy from base at current index
        if line.startswith(' ') or line == '':
            if src_idx < len(base_lines):
                result.append(base_lines[src_idx])
                src_idx += 1

        # Deletion: advance base pointer but don't add to result
        elif line.startswith('-'):
            if src_idx < len(base_lines):
                src_idx += 1

        # Addition: append directly to result
        elif line.startswith('+'):
            result.append(line[1:])

    # Append any remaining base lines not covered by hunks
    while src_idx < len(base_lines):
        result.append(base_lines[src_idx])
        src_idx += 1

    return result