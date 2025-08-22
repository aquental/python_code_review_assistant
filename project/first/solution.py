import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

@dataclass
class DiffLine:
    line_number: int
    content: str
    change_type: str  # 'added', 'removed', 'context'

@dataclass
class DiffHunk:
    old_start: int
    new_start: int
    lines: List['DiffLine']

@dataclass
class FileDiff:
    file_path: str
    hunks: List['DiffHunk']
    is_new: bool
    is_deleted: bool

def parse_hunk_header(header_line: str) -> Tuple[int, int]:
    """
    Parse a hunk header line to extract the starting line numbers.
    
    Args:
        header_line: A string containing the hunk header (e.g., "@@ -1,4 +1,5 @@")
        
    Returns:
        A tuple of (old_start, new_start) as integers
    """
    pattern = r'@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@'
    match = re.match(pattern, header_line)
    
    if match:
        old_start = int(match.group(1))
        new_start = int(match.group(2))
        return old_start, new_start
    
    # If we can't parse the header, return default values
    return 1, 1

def extract_file_path(header_line: str) -> str:
    """
    Extract the file path from a diff header line.
    
    Args:
        header_line: A diff header line starting with '+++' or '---'
        
    Returns:
        The clean file path without prefixes
    """
    if not header_line.startswith('+++'):
        return "unknown"
    
    # Extract the path portion after the +++ prefix
    path = header_line[4:].split('\t')[0]
    
    # Remove the b/ prefix if present
    if path.startswith('b/'):
        path = path[2:]
        
    return path

def parse_single_hunk(hunk_text: str) -> DiffHunk:
    """
    Parse a single hunk from a unified diff into a DiffHunk object.
    
    Args:
        hunk_text: A multi-line string containing a single hunk (header + lines)
        
    Returns:
        A DiffHunk object with parsed information
    """
    lines = hunk_text.strip().split('\n')
    
    # First line should be the hunk header
    if not lines or not lines[0].startswith('@@'):
        return DiffHunk(1, 1, [])
    
    # Parse the header to get starting line numbers
    old_start, new_start = parse_hunk_header(lines[0])
    
    # Process each line in the hunk
    diff_lines = []
    current_line = new_start
    
    for line in lines[1:]:  # Skip the header line
        if not line:  # Skip empty lines
            continue
            
        if line.startswith('+'):
            # Added line
            diff_lines.append(DiffLine(current_line, line[1:], 'added'))
            current_line += 1
        elif line.startswith('-'):
            # Removed line - no line number in new file
            diff_lines.append(DiffLine(0, line[1:], 'removed'))
        elif line.startswith(' '):
            # Context line
            diff_lines.append(DiffLine(current_line, line[1:], 'context'))
            current_line += 1
    
    return DiffHunk(old_start, new_start, diff_lines)

def parse_unified_diff(diff_text: str) -> FileDiff:
    """Parse a unified diff format"""
    lines = diff_text.split('\n')
    
    # Extract file path
    file_path = "unknown"
    for line in lines:
        if line.startswith('+++'):
            file_path = extract_file_path(line)
            break
    
    # Check file status
    is_new = any('new file mode' in line for line in lines)
    is_deleted = any('deleted file mode' in line for line in lines)
    
    # Parse hunks
    hunks = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Find hunk header
        if line.startswith('@@'):
            # Find the end of this hunk
            hunk_start = i
            i += 1
            while i < len(lines) and not lines[i].startswith('@@'):
                i += 1
            
            # Extract and parse the hunk
            hunk_text = '\n'.join(lines[hunk_start:i])
            hunk = parse_single_hunk(hunk_text)
            hunks.append(hunk)
            # Continue scanning for next hunk (no break)
        else:
            i += 1
    
    return FileDiff(file_path, hunks, is_new, is_deleted)

# Example usage for demonstration:
if __name__ == "__main__":
    # Test with a diff containing multiple hunks
    multi_hunk_diff = """diff --git a/example.py b/example.py
index 83db48f..f735c60 100644
--- a/example.py
+++ b/example.py
@@ -1,4 +1,5 @@
 import os
+import sys
 
 def foo():
-    print("Hello")
+    print("Hello, world!")
@@ -10,6 +11,7 @@ def bar():
     return 42
 
 def baz():
-    print("Baz")
+    print("Baz!")
+    return None
 
"""
    file_diff = parse_unified_diff(multi_hunk_diff)
    print(f"File: {file_diff.file_path}")
    print(f"Number of hunks: {len(file_diff.hunks)}")
    
    for i, hunk in enumerate(file_diff.hunks):
        print(f"\nHunk {i+1}:")
        print(f"  old_start: {hunk.old_start}, new_start: {hunk.new_start}")
        print(f"  lines: {len(hunk.lines)}")
        for line in hunk.lines:
            print(f"    Line {line.line_number}: {line.change_type} - {line.content}")
