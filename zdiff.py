#!/usr/bin/env python3
"""
#===============================================================================
  Description: Advanced Text Diff Tool
  ------------------------------------
      
  A professional diff tool that provides git-style output with intelligent block-level
  highlighting, consecutive word merging, and clean visual formatting.

  Features:
  - Git-style diff output with hunk headers and line numbers
  - Word-boundary-aware highlighting with consecutive block merging
  - Professional color scheme optimized for readability
  - Smart LaTeX command preservation
  - Context-aware formatting

  Usage:
      python zdiff.py file1.txt file2.txt
      python zdiff.py --help

    Version:  1.0
    Created:  2025-08-08 17:10
     Author:  Zhiyuan Yao, zhiyuan.yao@icloud.com
  Institute:  Lanzhou Center for Theoretical Physics, Lanzhou University
#===============================================================================
"""
import re
import sys
import difflib
import argparse
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    RESET = '\033[0m'
    BOLD = '\033[1m'
    # Background colors for highlighting specific words with white text
    RED_BG = '\033[48;5;74m\033[37m'    # Blue background with white text for deletions
    GREEN_BG = '\033[48;5;36m\033[37m'  # Green background with white text for additions
    # Standard ANSI colors for space differences
    RED_SPACE_BG = '\033[41m'    # Standard red background for space differences
    GREEN_SPACE_BG = '\033[42m'  # Standard green background for space differences
    # Gray color for line numbers
    GRAY = '\033[90m'            # Gray color for line numbers
    # Professional line background colors with white text for entire modified lines
    LINE_RED_BG = '\033[48;5;67m\033[37m'    # Blue-gray background with white text for - lines
    LINE_GREEN_BG = '\033[48;5;65m\033[37m'  # Green-gray background with white text for + lines


def get_block_level_diff(old_text, new_text):
    """Generate word-boundary-aware diff highlighting with consecutive block merging."""
    
    # Use character-level diffing for accuracy, then expand to word boundaries
    matcher = difflib.SequenceMatcher(None, old_text, new_text)
    
    # Collect all change regions first
    change_regions_old = []
    change_regions_new = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag != 'equal':
            change_regions_old.append((i1, i2))
            change_regions_new.append((j1, j2))
    
    # Expand change regions to word boundaries for clean highlighting
    def expand_to_word_boundaries(text, regions):
        """Expand change regions to include complete words."""
        expanded = []
        
        for start, end in regions:
            # Expand backward to start of word
            expanded_start = start
            while expanded_start > 0 and text[expanded_start - 1].isalnum():
                expanded_start -= 1
            
            # Expand forward to end of word
            expanded_end = end
            while expanded_end < len(text) and text[expanded_end].isalnum():
                expanded_end += 1
            
            expanded.append((expanded_start, expanded_end))
        
        return expanded
    
    expanded_old = expand_to_word_boundaries(old_text, change_regions_old)
    expanded_new = expand_to_word_boundaries(new_text, change_regions_new)
    
    # Helper function to check small gaps
    def is_small_gap(text, start, end):
        """Check if the gap between regions contains only whitespace, punctuation, or single characters."""
        if start >= len(text) or end > len(text) or start >= end:
            return False
        
        gap_text = text[start:end]
        
        # Merge if gap contains only:
        # - Whitespace (spaces, tabs)
        # - Single punctuation marks  
        # - Short sequences of non-alphanumeric characters
        # - Single characters
        
        # Remove whitespace to check remaining content
        non_space_gap = gap_text.replace(' ', '').replace('\t', '').replace('\n', '')
        
        # If only whitespace, merge
        if not non_space_gap:
            return True
            
        # If gap is very short (1-2 characters) and contains punctuation/symbols, merge
        if len(non_space_gap) <= 2 and not non_space_gap.isalnum():
            return True
            
        # If gap contains only single non-alphanumeric character, merge
        if len(non_space_gap) == 1:
            return True
            
        return False
    
    # Merge overlapping regions and nearby regions separated by small gaps
    def merge_regions(regions, text, merge_threshold=5):
        """Merge overlapping or nearby regions separated by small gaps."""
        if not regions:
            return []
        
        regions = sorted(regions)
        merged = [regions[0]]
        
        for current in regions[1:]:
            last = merged[-1]
            gap_start = last[1]
            gap_end = current[0]
            gap_size = gap_end - gap_start
            
            # Check if regions overlap, are adjacent, or have a small gap
            should_merge = (
                current[0] <= last[1] or  # Overlapping or adjacent
                (gap_size <= merge_threshold and gap_size > 0 and 
                 is_small_gap(text, gap_start, gap_end))
            )
            
            if should_merge:
                merged[-1] = (last[0], max(last[1], current[1]))
            else:
                merged.append(current)
        
        return merged
    
    merged_old = merge_regions(expanded_old, old_text)
    merged_new = merge_regions(expanded_new, new_text)
    
    # Apply highlighting to merged regions
    def apply_highlights(text, regions, color, space_color):
        """Apply highlighting to specified regions."""
        if not regions:
            return text
        
        result = []
        pos = 0
        
        for start, end in regions:
            # Add unchanged text before this region
            result.append(text[pos:start])
            
            # Add highlighted region
            block = text[start:end]
            
            # Check if this is primarily a whitespace difference
            content = block.replace(' ', '').replace('\t', '').replace('\n', '').replace('\r', '')
            is_space_only = len(content.strip()) == 0
            
            highlight_color = space_color if is_space_only else color
            
            if block.strip() or is_space_only:
                # For block highlights, preserve line background
                result.append(f"{highlight_color}{block}\033[0m\033[48;5;67m\033[37m" if color == Colors.RED_BG else f"{highlight_color}{block}\033[0m\033[48;5;65m\033[37m")
            else:
                result.append(block)
            
            pos = end
        
        # Add remaining unchanged text
        result.append(text[pos:])
        
        return ''.join(result)
    
    old_highlighted = apply_highlights(old_text, merged_old, Colors.RED_BG, Colors.RED_SPACE_BG)
    new_highlighted = apply_highlights(new_text, merged_new, Colors.GREEN_BG, Colors.GREEN_SPACE_BG)
    
    return old_highlighted, new_highlighted


def safe_unescape(text):
    """Safely unescape string content without breaking LaTeX commands."""
    import re
    
    # Handle common escape sequences, but avoid LaTeX commands
    result = text.replace('\\\\\\\\n', '\n')  # Handle double-escaped newlines first
    result = result.replace('\\\\n', '\n')   # Then single-escaped newlines
    
    # Smart \t handling: only convert \t to tab when it's NOT followed by a letter
    # This preserves LaTeX commands like \text, \tan, \times, etc.
    # but still allows genuine tab escapes like "\t" (standalone) or "\t123"
    result = re.sub(r'\\t(?![a-zA-Z])', '\t', result)
    
    result = result.replace('\\\\"', '"')
    result = result.replace("\\\\'", "'")
    
    # Don't replace \r at all - it's too risky with LaTeX commands
    # Most content doesn't use \r anyway, and if it does, it's usually \r\n
    # which we can handle as separate \n processing
    
    result = result.replace('\\\\\\\\', '\\\\')
    return result


def generate_git_style_diff(old_text, new_text, filename1="file1", filename2="file2"):
    """Generate git-style diff output with gray line numbers before -/+ prefixes."""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    
    # Use SequenceMatcher for line-level comparison
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    
    diff_lines = []
    old_line_num = 1
    new_line_num = 1
    context_size = 3
    
    # Add file header
    diff_lines.append(f"{Colors.BOLD}--- {filename1}{Colors.RESET}")
    diff_lines.append(f"{Colors.BOLD}+++ {filename2}{Colors.RESET}")
    
    def format_line_with_number(line_num, prefix, content, is_context=False):
        """Format a line with gray line number, prefix, and content."""
        if is_context:
            return f"{Colors.GRAY}{line_num:4d}{Colors.RESET} {prefix}{content}"
        elif prefix == '-':
            # For deletions, show line with red prefix but no full-line highlighting
            return f"{Colors.GRAY}{line_num:4d}{Colors.RESET} {Colors.RED}{prefix}{Colors.RESET}{content}"
        elif prefix == '+':
            # For additions, show line with green prefix but no full-line highlighting
            return f"{Colors.GRAY}{line_num:4d}{Colors.RESET} {Colors.GREEN}{prefix}{Colors.RESET}{content}"
        else:
            return f"{Colors.GRAY}{line_num:4d}{Colors.RESET} {prefix}{content}"
    
    # Track ranges for hunk headers
    current_hunk = []
    hunk_old_start = None
    hunk_new_start = None
    
    def flush_current_hunk():
        """Output the current hunk with proper header."""
        nonlocal current_hunk, hunk_old_start, hunk_new_start
        
        if current_hunk and hunk_old_start is not None and hunk_new_start is not None:
            # Count lines in hunk
            old_count = sum(1 for line in current_hunk if line.split(' ', 1)[1].startswith((' ', '-')))
            new_count = sum(1 for line in current_hunk if line.split(' ', 1)[1].startswith((' ', '+')))
            
            # Add hunk header
            header = f"@@ -{hunk_old_start},{old_count} +{hunk_new_start},{new_count} @@"
            diff_lines.append(f"{Colors.CYAN}{header}{Colors.RESET}")
            
            # Add hunk content
            diff_lines.extend(current_hunk)
            diff_lines.append("")  # Blank line between hunks
        
        # Reset
        current_hunk = []
        hunk_old_start = None
        hunk_new_start = None
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # Handle context lines
            equal_lines = i2 - i1
            
            if current_hunk:
                # Add context after changes (up to context_size lines)
                for i in range(i1, min(i1 + context_size, i2)):
                    line_content = old_lines[i] if i < len(old_lines) else ""
                    current_hunk.append(format_line_with_number(old_line_num + i - i1, ' ', line_content, is_context=True))
                
                # If there are many equal lines, flush current hunk
                if equal_lines > context_size * 2:
                    flush_current_hunk()
                    # Skip to near the end for next context
                    skip_count = equal_lines - context_size
                    old_line_num += skip_count
                    new_line_num += skip_count
                    
                    # Start new hunk context if more changes are coming
                    remaining_ops = list(matcher.get_opcodes())
                    current_index = remaining_ops.index((tag, i1, i2, j1, j2))
                    if current_index < len(remaining_ops) - 1:
                        # There are more changes, prepare context
                        hunk_old_start = old_line_num
                        hunk_new_start = new_line_num
                        
                        # Add context before next changes
                        context_start = max(i1, i2 - context_size)
                        for i in range(context_start, i2):
                            line_content = old_lines[i] if i < len(old_lines) else ""
                            current_hunk.append(format_line_with_number(old_line_num + i - context_start, ' ', line_content, is_context=True))
                else:
                    # Add all remaining equal lines as context
                    for i in range(i1 + context_size, i2):
                        line_content = old_lines[i] if i < len(old_lines) else ""
                        current_hunk.append(format_line_with_number(old_line_num + i - i1, ' ', line_content, is_context=True))
            
            old_line_num += equal_lines
            new_line_num += equal_lines
            
        else:
            # Start new hunk if needed
            if hunk_old_start is None:
                hunk_old_start = max(1, old_line_num - context_size)
                hunk_new_start = max(1, new_line_num - context_size)
                
                # Add context before changes
                context_start = max(0, i1 - context_size)
                for i in range(context_start, i1):
                    if i < len(old_lines):
                        adjusted_line_num = hunk_old_start + (i - context_start)
                        line_content = old_lines[i]
                        current_hunk.append(format_line_with_number(adjusted_line_num, ' ', line_content, is_context=True))
            
            # Handle different change types
            if tag == 'delete':
                for i in range(i1, i2):
                    if i < len(old_lines):
                        line_content = old_lines[i]
                        # Apply both full-line highlighting and block-level highlighting for deleted line
                        highlighted_content, _ = get_block_level_diff(line_content, "")
                        current_hunk.append(f"{Colors.GRAY}{old_line_num:4d}{Colors.RESET} {Colors.LINE_RED_BG}-{highlighted_content}{Colors.RESET}")
                        old_line_num += 1
                        
            elif tag == 'insert':
                for j in range(j1, j2):
                    if j < len(new_lines):
                        line_content = new_lines[j]
                        # Apply both full-line highlighting and block-level highlighting for added line
                        _, highlighted_content = get_block_level_diff("", line_content)
                        current_hunk.append(f"{Colors.GRAY}{new_line_num:4d}{Colors.RESET} {Colors.LINE_GREEN_BG}+{highlighted_content}{Colors.RESET}")
                        new_line_num += 1
                        
            elif tag == 'replace':
                # Handle line-by-line replacements with intra-line highlighting
                max_lines = max(i2 - i1, j2 - j1)
                
                for idx in range(max_lines):
                    old_idx = i1 + idx
                    new_idx = j1 + idx
                    
                    # Handle old line (deletion)
                    if old_idx < i2 and old_idx < len(old_lines):
                        old_line_content = old_lines[old_idx]
                        # Find corresponding new line for comparison
                        new_line_content = ""
                        if new_idx < j2 and new_idx < len(new_lines):
                            new_line_content = new_lines[new_idx]
                        
                        # Apply both full-line highlighting and block-level diff highlighting
                        highlighted_old, _ = get_block_level_diff(old_line_content, new_line_content)
                        current_hunk.append(f"{Colors.GRAY}{old_line_num:4d}{Colors.RESET} {Colors.LINE_RED_BG}-{highlighted_old}{Colors.RESET}")
                        old_line_num += 1
                    
                    # Handle new line (addition)  
                    if new_idx < j2 and new_idx < len(new_lines):
                        new_line_content = new_lines[new_idx]
                        # Find corresponding old line for comparison
                        old_line_content = ""
                        if old_idx < i2 and old_idx < len(old_lines):
                            old_line_content = old_lines[old_idx]
                        
                        # Apply both full-line highlighting and block-level diff highlighting
                        _, highlighted_new = get_block_level_diff(old_line_content, new_line_content)
                        current_hunk.append(f"{Colors.GRAY}{new_line_num:4d}{Colors.RESET} {Colors.LINE_GREEN_BG}+{highlighted_new}{Colors.RESET}")
                        new_line_num += 1
    
    # Flush final hunk
    flush_current_hunk()
    
    return '\n'.join(diff_lines) if diff_lines else f"    {Colors.BLUE}No changes detected{Colors.RESET}"


def read_file(filepath):
    """Read file content safely with proper encoding handling."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file {filepath}: {e}", file=sys.stderr)
            sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="""
zdiff - Advanced Text Diff Tool with Git-Style Output

Features intelligent block-level highlighting, consecutive word merging,
and professional formatting optimized for code and text comparison.
        """.strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        'file1',
        help='First file to compare'
    )
    parser.add_argument(
        'file2', 
        help='Second file to compare'
    )
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    parser.add_argument(
        '--context',
        '-c',
        type=int,
        default=3,
        help='Number of context lines to show (default: 3)'
    )
    
    args = parser.parse_args()
    
    # Validate files exist
    file1_path = Path(args.file1)
    file2_path = Path(args.file2)
    
    if not file1_path.exists():
        print(f"Error: File not found: {args.file1}", file=sys.stderr)
        sys.exit(1)
    
    if not file2_path.exists():
        print(f"Error: File not found: {args.file2}", file=sys.stderr)
        sys.exit(1)
    
    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')
    
    # Read file contents
    old_content = read_file(file1_path)
    new_content = read_file(file2_path)
    
    # Process content (unescape if needed for special characters)
    old_processed = safe_unescape(old_content)
    new_processed = safe_unescape(new_content)
    
    # Generate and display diff
    diff_output = generate_git_style_diff(
        old_processed, 
        new_processed, 
        str(file1_path), 
        str(file2_path)
    )
    
    print(diff_output)
    
    # Exit with appropriate code
    if old_processed != new_processed:
        sys.exit(1)  # Files differ
    else:
        sys.exit(0)  # Files are identical


if __name__ == "__main__":
    main()
