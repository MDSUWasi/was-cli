def apply_delta(base_lines, delta_lines):
    """
    Applies a unified diff patch (delta_lines) to a list of base text lines (base_lines).
    This reconstructs the next historical version of your document.
    
    This matches the standard diff/patch algorithm and handles insertions (+),
    deletions (-), and unchanged context lines ( ) precisely.
    """
    if not delta_lines:
        return base_lines

    result = []
    delta_iter = iter(delta_lines)
    
    # 1. Skip standard unified diff header lines (e.g. '--- original', '+++ modified')
    try:
        next(delta_iter)
        next(delta_iter)
    except StopIteration:
        return base_lines

    src_line_idx = 0
    while True:
        try:
            line = next(delta_iter)
        except StopIteration:
            break

        # 2. Process hunk headers (e.g., '@@ -1,4 +1,5 @@')
        if line.startswith('@@'):
            parts = line.split(' ')
            # Extract the starting line number for this hunk (offsetting for 0-index)
            src_start = int(parts[1].split(',')[0].replace('-', '')) - 1
            if src_start < 0:
                src_start = 0
                
            # Copy all unchanged lines from base_lines up to the start of this hunk
            while src_line_idx < src_start and src_line_idx < len(base_lines):
                result.append(base_lines[src_line_idx])
                src_line_idx += 1
                
        # 3. Process unchanged context lines
        elif line.startswith(' '):
            if src_line_idx < len(base_lines):
                result.append(base_lines[src_line_idx])
                src_line_idx += 1
                
        # 4. Process deleted lines (we skip them from base_lines to effectively remove them)
        elif line.startswith('-'):
            if src_line_idx < len(base_lines):
                src_line_idx += 1
                
        # 5. Process added lines (we insert them into our reconstructed result)
        elif line.startswith('+'):
            result.append(line[1:])

    # 6. Copy any remaining unchanged lines left at the end of the base document
    while src_line_idx < len(base_lines):
        result.append(base_lines[src_line_idx])
        src_line_idx += 1

    return result