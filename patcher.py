def apply_delta(base_lines, delta_lines):
    """
    Applies a unified diff patch (delta_lines) to a list of base text lines (base_lines).
    This reconstructs the next historical version of your document.
    
    Robustly handles insertions (+), deletions (-), unchanged context lines ( ), 
    and variable header formats.
    """
    if not delta_lines:
        return base_lines[:] # Return a copy to avoid mutating input

    result = []
    delta_iter = iter(delta_lines)
    
    # 1. Skip standard unified diff header lines dynamically
    # Instead of assuming exactly 2 lines, skip until we hit the first hunk (@@)
    # This makes the function robust against variations in header formatting.
    first_hunk_found = False
    while True:
        try:
            line = next(delta_iter)
            if line.startswith('@@'):
                # We found the first hunk, break out to process it immediately
                first_hunk_found = True
                break
        except StopIteration:
            # No hunks found at all (empty diff or invalid format)
            return base_lines[:]

    src_line_idx = 0
    
    # If we didn't find a hunk immediately, we need to re-process the first line we just read
    # But since we broke out on '@@', we can proceed directly.
    # We need to handle the current 'line' which is the hunk header.
    
    while True:
        # If we haven't processed the current hunk header yet (the one that broke the loop above)
        if first_hunk_found and 'line' in locals() and line.startswith('@@'):
            first_hunk_found = False
        else:
            try:
                line = next(delta_iter)
            except StopIteration:
                break

        # 2. Process hunk headers (e.g., '@@ -1,4 +1,5 @@')
        if line.startswith('@@'):
            parts = line.split(' ')
            try:
                # Extract the starting line number for source (offsetting for 0-index)
                # Format is usually "-start,count"
                src_part = parts[1]
                if ',' in src_part:
                    src_start_str = src_part.split(',')[0]
                else:
                    src_start_str = src_part
                
                src_start = int(src_start_str.replace('-', '')) - 1
                if src_start < 0:
                    src_start = 0
                    
                # Safety check: Ensure we don't jump backwards (corrupted diff)
                if src_start > len(base_lines):
                    # If the hunk says it's beyond the file, clamp to end
                    src_start = len(base_lines)
                
                # Copy all unchanged lines from base_lines up to the start of this hunk
                while src_line_idx < src_start and src_line_idx < len(base_lines):
                    result.append(base_lines[src_line_idx])
                    src_line_idx += 1
            except (ValueError, IndexError):
                # If header parsing fails, skip the header and continue to content
                # This prevents crashing on malformed diffs
                continue
                
        # 3. Process unchanged context lines
        elif line.startswith(' '):
            if src_line_idx < len(base_lines):
                result.append(base_lines[src_line_idx])
                src_line_idx += 1
            else:
                # Edge case: Context line claims to exist but file ended earlier.
                # In strict diffs this shouldn't happen, but we handle it gracefully.
                pass
                
        # 4. Process deleted lines (we skip them from base_lines to effectively remove them)
        elif line.startswith('-'):
            if src_line_idx < len(base_lines):
                src_line_idx += 1
            # If src_line_idx is already past end, ignore the delete (malformed diff)
                
        # 5. Process added lines (we insert them into our reconstructed result)
        elif line.startswith('+'):
            result.append(line[1:])

    # 6. Copy any remaining unchanged lines left at the end of the base document
    while src_line_idx < len(base_lines):
        result.append(base_lines[src_line_idx])
        src_line_idx += 1

    return result