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

    Version:  1.1
    Created:  2025-08-08 17:10
    Updated:  2026-02-21
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
    # Intra-line diff highlight colors (word/block level)
    DEL_BG = '\033[48;5;74m\033[37m'    # Steel-blue background for deleted words
    ADD_BG = '\033[48;5;36m\033[37m'    # Teal background for added words
    # Space-only difference markers
    RED_SPACE_BG = '\033[41m'           # Standard red background for space differences
    GREEN_SPACE_BG = '\033[42m'         # Standard green background for space differences
    # Line number gutter
    GRAY = '\033[90m'
    # Full-line background colors for changed lines
    LINE_DEL_BG = '\033[48;5;67m\033[37m'   # Blue-gray background for deleted lines
    LINE_ADD_BG = '\033[48;5;65m\033[37m'   # Green-gray background for added lines


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

    def is_word_char(c):
        """Return True for characters that are part of an identifier (alnum or underscore)."""
        return c.isalnum() or c == '_'

    # Expand change regions to word boundaries for clean highlighting
    def expand_to_word_boundaries(text, regions):
        """Expand change regions to include complete words."""
        expanded = []

        for start, end in regions:
            # Expand backward to start of word
            expanded_start = start
            while expanded_start > 0 and is_word_char(text[expanded_start - 1]):
                expanded_start -= 1

            # Expand forward to end of word
            expanded_end = end
            while expanded_end < len(text) and is_word_char(text[expanded_end]):
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
    def apply_highlights(text, regions, color, space_color, line_bg):
        """Apply highlighting to specified regions, restoring line background after each block."""
        if not regions:
            return text

        result = []
        pos = 0

        for start, end in regions:
            # Add unchanged text before this region
            result.append(text[pos:start])

            block = text[start:end]
            is_space_only = not block.strip()
            highlight_color = space_color if is_space_only else color

            # Restore the line background color after the inline highlight resets it
            result.append(f"{highlight_color}{block}{Colors.RESET}{line_bg}")
            pos = end

        # Add remaining unchanged text
        result.append(text[pos:])

        return ''.join(result)

    old_highlighted = apply_highlights(
        old_text, merged_old, Colors.DEL_BG, Colors.RED_SPACE_BG, Colors.LINE_DEL_BG
    )
    new_highlighted = apply_highlights(
        new_text, merged_new, Colors.ADD_BG, Colors.GREEN_SPACE_BG, Colors.LINE_ADD_BG
    )

    return old_highlighted, new_highlighted


def generate_git_style_diff(old_text, new_text, filename1="file1", filename2="file2", context=3):
    """Generate git-style diff output using SequenceMatcher.get_grouped_opcodes().

    Uses difflib's built-in hunk grouping so context lines, hunk counts, and
    hunk splitting are all correct and respect the caller-supplied context value.
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()

    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    groups = list(matcher.get_grouped_opcodes(context))

    if not groups:
        return f"    {Colors.BLUE}No changes detected{Colors.RESET}"

    diff_lines = []
    diff_lines.append(f"{Colors.BOLD}--- {filename1}{Colors.RESET}")
    diff_lines.append(f"{Colors.BOLD}+++ {filename2}{Colors.RESET}")

    for group in groups:
        first = group[0]
        last = group[-1]
        old_lo, old_hi = first[1], last[2]
        new_lo, new_hi = first[3], last[4]

        header = f"@@ -{old_lo+1},{old_hi-old_lo} +{new_lo+1},{new_hi-new_lo} @@"
        diff_lines.append(f"{Colors.CYAN}{header}{Colors.RESET}")

        for tag, i1, i2, j1, j2 in group:

            if tag == 'equal':
                for i in range(i1, i2):
                    diff_lines.append(f"{Colors.GRAY}{i+1:4d}{Colors.RESET} {old_lines[i]}")

            elif tag == 'delete':
                for i in range(i1, i2):
                    content = old_lines[i]
                    diff_lines.append(
                        f"{Colors.GRAY}{i+1:4d}{Colors.RESET} {Colors.LINE_DEL_BG}-{content}{Colors.RESET}"
                    )

            elif tag == 'insert':
                for j in range(j1, j2):
                    content = new_lines[j]
                    diff_lines.append(
                        f"{Colors.GRAY}{j+1:4d}{Colors.RESET} {Colors.LINE_ADD_BG}+{content}{Colors.RESET}"
                    )

            elif tag == 'replace':
                old_chunk = old_lines[i1:i2]
                new_chunk = new_lines[j1:j2]
                n_pairs = min(len(old_chunk), len(new_chunk))

                # Paired lines: show interleaved with intra-line highlighting
                for idx in range(n_pairs):
                    old_line = old_chunk[idx]
                    new_line = new_chunk[idx]
                    highlighted_old, highlighted_new = get_block_level_diff(old_line, new_line)
                    diff_lines.append(
                        f"{Colors.GRAY}{i1+idx+1:4d}{Colors.RESET} {Colors.LINE_DEL_BG}-{highlighted_old}{Colors.RESET}"
                    )
                    diff_lines.append(
                        f"{Colors.GRAY}{j1+idx+1:4d}{Colors.RESET} {Colors.LINE_ADD_BG}+{highlighted_new}{Colors.RESET}"
                    )

                # Unpaired old lines (no corresponding new line to compare against)
                for idx in range(n_pairs, len(old_chunk)):
                    content = old_chunk[idx]
                    diff_lines.append(
                        f"{Colors.GRAY}{i1+idx+1:4d}{Colors.RESET} {Colors.LINE_DEL_BG}-{content}{Colors.RESET}"
                    )

                # Unpaired new lines (no corresponding old line to compare against)
                for idx in range(n_pairs, len(new_chunk)):
                    content = new_chunk[idx]
                    diff_lines.append(
                        f"{Colors.GRAY}{j1+idx+1:4d}{Colors.RESET} {Colors.LINE_ADD_BG}+{content}{Colors.RESET}"
                    )

        diff_lines.append("")  # blank line between hunks

    return '\n'.join(diff_lines)


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

    # Read file contents as-is (no escape-sequence transformation)
    old_content = read_file(file1_path)
    new_content = read_file(file2_path)

    # Generate and display diff
    diff_output = generate_git_style_diff(
        old_content,
        new_content,
        str(file1_path),
        str(file2_path),
        context=args.context,
    )

    print(diff_output)

    # Exit with appropriate code
    if old_content != new_content:
        sys.exit(1)  # Files differ
    else:
        sys.exit(0)  # Files are identical


if __name__ == "__main__":
    main()
