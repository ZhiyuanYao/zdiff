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
import shutil
import unicodedata
from pathlib import Path

try:
    from wcwidth import wcwidth as _wcwidth
except ImportError:
    _wcwidth = None

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
    RED_SPACE_BG = '\033[48;5;88m'      # Softer dark-red background for space differences
    GREEN_SPACE_BG = '\033[42m'         # Standard green background for space differences
    # Line number gutter
    GRAY = '\033[90m'
    # Full-line background colors for changed lines
    LINE_DEL_BG = '\033[48;5;67m\033[37m'   # Blue-gray background for deleted lines
    LINE_ADD_BG = '\033[48;5;65m\033[37m'   # Green-gray background for added lines


ANSI_ESCAPE_RE = re.compile(r'\x1b\[[0-9;]*m')
WORD_RE = re.compile(r'\w+', flags=re.UNICODE)


def char_display_width(ch, tab_width=4):
    """Return terminal display width for a single character."""
    if ch == '\t':
        return tab_width
    if ch in ('\n', '\r'):
        return 0

    if _wcwidth is not None:
        width = _wcwidth(ch)
        return width if width > 0 else 0

    if unicodedata.combining(ch):
        return 0

    category = unicodedata.category(ch)
    if category.startswith('C'):
        return 0

    return 2 if unicodedata.east_asian_width(ch) in ('W', 'F') else 1


def visible_length(text):
    """Return terminal display width without ANSI escape sequences."""
    plain = ANSI_ESCAPE_RE.sub('', text)
    return sum(char_display_width(ch) for ch in plain)


def clip_visible(text, width, ellipsis='...'):
    """Clip text to target visible width while preserving ANSI escape sequences."""
    if width <= 0:
        return ''

    if visible_length(text) <= width:
        return text

    if visible_length(ellipsis) >= width:
        return '.' * width

    target_width = width - visible_length(ellipsis)
    result = []
    i = 0
    used_width = 0
    text_len = len(text)

    while i < text_len and used_width < target_width:
        match = ANSI_ESCAPE_RE.match(text, i)
        if match:
            result.append(match.group(0))
            i = match.end()
            continue

        ch = text[i]
        ch_width = char_display_width(ch)
        if used_width + ch_width > target_width:
            break

        result.append(ch)
        used_width += ch_width
        i += 1

    clipped = ''.join(result)
    if ANSI_ESCAPE_RE.search(clipped) and not clipped.endswith(Colors.RESET):
        clipped += Colors.RESET

    return clipped + ellipsis


def pad_visible(text, width):
    """Right-pad text to a target visible width."""
    pad_len = width - visible_length(text)
    if pad_len > 0:
        return text + (' ' * pad_len)
    return text


def fit_visible(text, width):
    """Clip then pad text to exact visible width."""
    return pad_visible(clip_visible(text, width), width)


def get_diff_groups(old_text, new_text, context):
    """Return split lines and grouped opcodes used by all renderers."""
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    groups = list(matcher.get_grouped_opcodes(context))
    return old_lines, new_lines, groups


def line_similarity_score(old_line, new_line):
    """Return a robust similarity score for line-level alignment."""
    char_ratio = difflib.SequenceMatcher(None, old_line, new_line, autojunk=False).ratio()

    old_tokens = WORD_RE.findall(old_line)
    new_tokens = WORD_RE.findall(new_line)
    if old_tokens and new_tokens:
        token_ratio = difflib.SequenceMatcher(None, old_tokens, new_tokens, autojunk=False).ratio()
    else:
        token_ratio = 0.0

    # Long token changes can tank char_ratio; token_ratio preserves structural similarity.
    return max(char_ratio, token_ratio)


def iter_aligned_chunk_rows(old_chunk, new_chunk, old_start, new_start):
    """Yield aligned row operations within a replace chunk.

    Uses a similarity-based dynamic-programming alignment so inserted/deleted lines
    inside large replace blocks do not force incorrect positional pairing.
    """
    n_old = len(old_chunk)
    n_new = len(new_chunk)

    # Safety fallback for very large chunks: avoid O(n*m) explosion.
    if n_old * n_new > 50000:
        matcher = difflib.SequenceMatcher(None, old_chunk, new_chunk)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for idx in range(i2 - i1):
                    old_idx = i1 + idx
                    new_idx = j1 + idx
                    yield (
                        'equal',
                        old_start + old_idx + 1,
                        old_chunk[old_idx],
                        new_start + new_idx + 1,
                        new_chunk[new_idx],
                    )
            elif tag == 'delete':
                for old_idx in range(i1, i2):
                    yield (
                        'delete',
                        old_start + old_idx + 1,
                        old_chunk[old_idx],
                        None,
                        None,
                    )
            elif tag == 'insert':
                for new_idx in range(j1, j2):
                    yield (
                        'insert',
                        None,
                        None,
                        new_start + new_idx + 1,
                        new_chunk[new_idx],
                    )
            elif tag == 'replace':
                n_pairs = min(i2 - i1, j2 - j1)
                for idx in range(n_pairs):
                    old_idx = i1 + idx
                    new_idx = j1 + idx
                    yield (
                        'replace',
                        old_start + old_idx + 1,
                        old_chunk[old_idx],
                        new_start + new_idx + 1,
                        new_chunk[new_idx],
                    )
                for old_idx in range(i1 + n_pairs, i2):
                    yield (
                        'delete',
                        old_start + old_idx + 1,
                        old_chunk[old_idx],
                        None,
                        None,
                    )
                for new_idx in range(j1 + n_pairs, j2):
                    yield (
                        'insert',
                        None,
                        None,
                        new_start + new_idx + 1,
                        new_chunk[new_idx],
                    )
        return

    pair_threshold = 0.45
    gap_penalty = -0.35

    # Pre-compute line similarity matrix.
    sim = [[0.0] * n_new for _ in range(n_old)]
    for i in range(n_old):
        for j in range(n_new):
            sim[i][j] = line_similarity_score(old_chunk[i], new_chunk[j])

    # DP tables.
    dp = [[0.0] * (n_new + 1) for _ in range(n_old + 1)]
    bt = [[''] * (n_new + 1) for _ in range(n_old + 1)]

    for i in range(1, n_old + 1):
        dp[i][0] = dp[i - 1][0] + gap_penalty
        bt[i][0] = 'delete'
    for j in range(1, n_new + 1):
        dp[0][j] = dp[0][j - 1] + gap_penalty
        bt[0][j] = 'insert'

    neg_inf = float('-inf')
    for i in range(1, n_old + 1):
        for j in range(1, n_new + 1):
            pair_score = neg_inf
            if sim[i - 1][j - 1] >= pair_threshold:
                pair_score = dp[i - 1][j - 1] + sim[i - 1][j - 1]

            delete_score = dp[i - 1][j] + gap_penalty
            insert_score = dp[i][j - 1] + gap_penalty

            best = pair_score
            op = 'pair'

            # Tie-break preference: pair > delete > insert.
            if delete_score > best:
                best = delete_score
                op = 'delete'
            if insert_score > best:
                best = insert_score
                op = 'insert'

            dp[i][j] = best
            bt[i][j] = op

    # Backtrack to build aligned operations.
    ops = []
    i = n_old
    j = n_new
    while i > 0 or j > 0:
        op = bt[i][j]
        if op == 'pair':
            i -= 1
            j -= 1
            if old_chunk[i] == new_chunk[j]:
                ops.append(('equal', i, j))
            else:
                ops.append(('replace', i, j))
        elif op == 'delete':
            i -= 1
            ops.append(('delete', i, None))
        else:  # insert
            j -= 1
            ops.append(('insert', None, j))

    ops.reverse()

    for row_tag, old_idx, new_idx in ops:
        if row_tag == 'equal':
            yield (
                'equal',
                old_start + old_idx + 1,
                old_chunk[old_idx],
                new_start + new_idx + 1,
                new_chunk[new_idx],
            )
        elif row_tag == 'replace':
            yield (
                'replace',
                old_start + old_idx + 1,
                old_chunk[old_idx],
                new_start + new_idx + 1,
                new_chunk[new_idx],
            )
        elif row_tag == 'delete':
            yield (
                'delete',
                old_start + old_idx + 1,
                old_chunk[old_idx],
                None,
                None,
            )
        else:  # insert
            yield (
                'insert',
                None,
                None,
                new_start + new_idx + 1,
                new_chunk[new_idx],
            )


def format_no_changes_or_eof_diff(old_text, new_text, filename1, filename2):
    """Handle identical files and trailing-EOF-newline-only differences."""
    if old_text == new_text:
        return f"    {Colors.BLUE}No changes detected{Colors.RESET}"

    old_eof = "has trailing newline" if old_text.endswith('\n') else "no trailing newline"
    new_eof = "has trailing newline" if new_text.endswith('\n') else "no trailing newline"
    return '\n'.join([
        f"{Colors.BOLD}--- {filename1}{Colors.RESET}",
        f"{Colors.BOLD}+++ {filename2}{Colors.RESET}",
        f"{Colors.CYAN}@@ EOF newline difference @@{Colors.RESET}",
        f"{Colors.LINE_DEL_BG}- {filename1}: {old_eof}{Colors.RESET}",
        f"{Colors.LINE_ADD_BG}+ {filename2}: {new_eof}{Colors.RESET}",
    ])


def get_block_level_diff(old_text, new_text, old_line_bg=None, new_line_bg=None):
    """Generate word-boundary-aware diff highlighting with consecutive block merging."""
    if old_line_bg is None:
        old_line_bg = Colors.LINE_DEL_BG
    if new_line_bg is None:
        new_line_bg = Colors.LINE_ADD_BG

    # Use character-level diffing for accuracy, then expand to word boundaries
    matcher = difflib.SequenceMatcher(None, old_text, new_text)

    def is_word_char(c):
        """Return True for characters that are part of an identifier (alnum or underscore)."""
        return c.isalnum() or c == '_'

    def trim_insert_region(old_pos, new_start, new_end):
        """Trim borrowed boundary fragments from insert regions when matcher splits inside words."""
        if new_start >= new_end:
            return new_start, new_end

        if not (0 < old_pos < len(old_text)):
            return new_start, new_end

        if not (is_word_char(old_text[old_pos - 1]) and is_word_char(old_text[old_pos])):
            return new_start, new_end

        start = new_start
        end = new_end
        right_idx = old_pos

        # Drop leading fragment borrowed from old right context (e.g., "4 " in "4 n2").
        while (
            start < end and
            right_idx < len(old_text) and
            is_word_char(new_text[start]) and
            is_word_char(old_text[right_idx]) and
            new_text[start] == old_text[right_idx]
        ):
            start += 1
            right_idx += 1

        while (
            start < end and
            right_idx < len(old_text) and
            new_text[start].isspace() and
            old_text[right_idx].isspace()
        ):
            start += 1
            right_idx += 1

        left_idx = old_pos - 1
        # Drop trailing fragment borrowed from old left context (e.g., trailing "e" in "xtra e").
        while (
            start < end and
            left_idx >= 0 and
            is_word_char(new_text[end - 1]) and
            is_word_char(old_text[left_idx]) and
            new_text[end - 1] == old_text[left_idx]
        ):
            end -= 1
            left_idx -= 1

        while start < end and new_text[start].isspace():
            start += 1
        while start < end and new_text[end - 1].isspace():
            end -= 1

        return start, end

    # Collect all change regions first
    change_regions_old = []
    change_regions_new = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'replace':
            change_regions_old.append((i1, i2))
            change_regions_new.append((j1, j2))
        elif tag == 'delete':
            # Keep deleted content highlighted on old side; do not force
            # highlight anchors on the unchanged new side.
            change_regions_old.append((i1, i2))
        elif tag == 'insert':
            # Highlight inserted content on new side and keep a small anchor
            # on old side for readability.
            inserted_starts_mid_word = (
                j1 < j2 and
                i1 > 0 and
                is_word_char(old_text[i1 - 1]) and
                is_word_char(new_text[j1])
            )
            if not inserted_starts_mid_word:
                change_regions_old.append((i1, i2))
            trimmed_j1, trimmed_j2 = trim_insert_region(i1, j1, j2)
            if trimmed_j1 < trimmed_j2:
                change_regions_new.append((trimmed_j1, trimmed_j2))

    # Expand change regions to word boundaries for clean highlighting
    def expand_to_word_boundaries(text, regions):
        """Expand change regions to include complete words."""
        expanded = []

        for start, end in regions:
            block_text = text[start:end]

            # If a multi-word changed block starts and ends mid-word,
            # trim trailing borrowed fragments first (e.g., "xtra e"), then expand.
            # Do not trim normal word-boundary starts, otherwise legitimate
            # deletions like "should dis..." lose "dis" and under-highlight.
            starts_mid_word = (
                start > 0 and start < len(text) and
                is_word_char(text[start - 1]) and is_word_char(text[start])
            )
            if block_text and any(ch.isspace() for ch in block_text) and starts_mid_word:
                while end > start and end < len(text) and is_word_char(text[end - 1]) and is_word_char(text[end]):
                    end -= 1

                block_text = text[start:end]

            # For non-whitespace changes, ignore boundary spaces so expansion does not
            # incorrectly absorb unchanged neighboring words (e.g., "keeps", "comparison").
            if block_text and block_text.strip():
                while start < end and text[start].isspace():
                    start += 1
                while end > start and text[end - 1].isspace():
                    end -= 1

            # For zero-length anchors (insert/delete counterpart), avoid expanding
            # backward into unchanged previous words; prefer the next word only.
            if start == end:
                forward_start = start
                while forward_start < len(text) and not is_word_char(text[forward_start]):
                    forward_start += 1

                if forward_start >= len(text):
                    # No following word to anchor; keep this side unhighlighted.
                    continue

                forward_end = forward_start
                while forward_end < len(text) and is_word_char(text[forward_end]):
                    forward_end += 1

                expanded.append((forward_start, forward_end))
                continue

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
        old_text, merged_old, Colors.DEL_BG, Colors.RED_SPACE_BG, old_line_bg
    )
    new_highlighted = apply_highlights(
        new_text, merged_new, Colors.ADD_BG, Colors.GREEN_SPACE_BG, new_line_bg
    )

    return old_highlighted, new_highlighted


def generate_git_style_diff(old_text, new_text, filename1="file1", filename2="file2", context=3):
    """Generate git-style diff output using SequenceMatcher.get_grouped_opcodes().

    Uses difflib's built-in hunk grouping so context lines, hunk counts, and
    hunk splitting are all correct and respect the caller-supplied context value.
    """
    old_lines, new_lines, groups = get_diff_groups(old_text, new_text, context)

    if not groups:
        return format_no_changes_or_eof_diff(old_text, new_text, filename1, filename2)

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
                for row_tag, old_no, old_line, new_no, new_line in iter_aligned_chunk_rows(
                    old_chunk, new_chunk, i1, j1
                ):
                    if row_tag == 'equal':
                        diff_lines.append(f"{Colors.GRAY}{old_no:4d}{Colors.RESET} {old_line}")

                    elif row_tag == 'delete':
                        diff_lines.append(
                            f"{Colors.GRAY}{old_no:4d}{Colors.RESET} {Colors.LINE_DEL_BG}-{old_line}{Colors.RESET}"
                        )

                    elif row_tag == 'insert':
                        diff_lines.append(
                            f"{Colors.GRAY}{new_no:4d}{Colors.RESET} {Colors.LINE_ADD_BG}+{new_line}{Colors.RESET}"
                        )

                    elif row_tag == 'replace':
                        highlighted_old, highlighted_new = get_block_level_diff(
                            old_line, new_line, old_line_bg='', new_line_bg=''
                        )
                        diff_lines.append(
                            f"{Colors.GRAY}{old_no:4d}{Colors.RESET} -{highlighted_old}"
                        )
                        diff_lines.append(
                            f"{Colors.GRAY}{new_no:4d}{Colors.RESET} +{highlighted_new}"
                        )

        diff_lines.append("")  # blank line between hunks

    return '\n'.join(diff_lines)


def generate_side_by_side_diff(old_text, new_text, filename1="file1", filename2="file2", context=3):
    """Render grouped diff output in two panels with line numbers on both sides."""
    old_lines, new_lines, groups = get_diff_groups(old_text, new_text, context)

    if not groups:
        if old_text == new_text:
            return f"    {Colors.BLUE}No changes detected{Colors.RESET}"

        old_eof = "has trailing newline" if old_text.endswith('\n') else "no trailing newline"
        new_eof = "has trailing newline" if new_text.endswith('\n') else "no trailing newline"
        return '\n'.join([
            f"{Colors.BOLD}--- {filename1}{Colors.RESET}",
            f"{Colors.BOLD}+++ {filename2}{Colors.RESET}",
            f"{Colors.CYAN}@@ EOF newline difference (side-by-side) @@{Colors.RESET}",
            f"     {Colors.LINE_DEL_BG}{old_eof}{Colors.RESET}  ||  {Colors.LINE_ADD_BG}{new_eof}{Colors.RESET}",
        ])

    total_width = shutil.get_terminal_size((120, 20)).columns
    separator = " || "
    panel_width = max(40, (total_width - len(separator)) // 2)
    tab_display_width = 4

    def format_left(line_no, marker, text, changed=False, highlight_affected=False):
        if changed and highlight_affected:
            ln_plain = f"{line_no:4d}" if line_no is not None else "    "
            affected = f"{ln_plain} {marker}{text}"
            highlighted = f"{Colors.LINE_DEL_BG}{affected}{Colors.RESET}"
            return fit_visible(highlighted, panel_width)

        ln = f"{line_no:4d}" if line_no is not None else "    "
        payload = f"{Colors.GRAY}{ln}{Colors.RESET} {marker}{text}"
        if changed:
            payload = f"{Colors.LINE_DEL_BG}{payload}{Colors.RESET}"
        return fit_visible(payload, panel_width)

    def format_right(line_no, marker, text, changed=False, highlight_affected=False):
        if changed and highlight_affected:
            ln_plain = f"{line_no:4d}" if line_no is not None else "    "
            affected = f"{ln_plain} {marker}{text}"
            highlighted = f"{Colors.LINE_ADD_BG}{affected}{Colors.RESET}"
            return fit_visible(highlighted, panel_width)

        ln = f"{line_no:4d}" if line_no is not None else "    "
        payload = f"{Colors.GRAY}{ln}{Colors.RESET} {marker}{text}"
        if changed:
            payload = f"{Colors.LINE_ADD_BG}{payload}{Colors.RESET}"
        return fit_visible(payload, panel_width)

    def add_row(
        lines, lno, lmark, ltext, rno, rmark, rtext, left_changed=False, right_changed=False,
        left_highlight_affected=False, right_highlight_affected=False
    ):
        # Normalize tabs for fixed-width panel rendering; raw tabs break vertical alignment.
        ltext = ltext.replace('\t', ' ' * tab_display_width)
        rtext = rtext.replace('\t', ' ' * tab_display_width)

        left = format_left(
            lno, lmark, ltext, changed=left_changed, highlight_affected=left_highlight_affected
        )
        right = format_right(
            rno, rmark, rtext, changed=right_changed, highlight_affected=right_highlight_affected
        )
        lines.append(f"{left}{separator}{right}")

    diff_lines = [
        f"{Colors.BOLD}--- {filename1}{Colors.RESET}",
        f"{Colors.BOLD}+++ {filename2}{Colors.RESET}",
        f"{fit_visible(f'{Colors.BOLD}LEFT: {filename1}{Colors.RESET}', panel_width)}{separator}"
        f"{fit_visible(f'{Colors.BOLD}RIGHT: {filename2}{Colors.RESET}', panel_width)}",
    ]

    for group in groups:
        first = group[0]
        last = group[-1]
        old_lo, old_hi = first[1], last[2]
        new_lo, new_hi = first[3], last[4]
        header = f"@@ -{old_lo+1},{old_hi-old_lo} +{new_lo+1},{new_hi-new_lo} @@"
        diff_lines.append(f"{Colors.CYAN}{header}{Colors.RESET}")

        for tag, i1, i2, j1, j2 in group:
            if tag == 'equal':
                for idx in range(i2 - i1):
                    old_line_no = i1 + idx + 1
                    new_line_no = j1 + idx + 1
                    text = old_lines[i1 + idx]
                    add_row(diff_lines, old_line_no, ' ', text, new_line_no, ' ', text)

            elif tag == 'delete':
                for i in range(i1, i2):
                    add_row(
                        diff_lines, i + 1, '-', old_lines[i], None, ' ', '',
                        left_changed=True, left_highlight_affected=True
                    )

            elif tag == 'insert':
                for j in range(j1, j2):
                    add_row(
                        diff_lines, None, ' ', '', j + 1, '+', new_lines[j],
                        right_changed=True, right_highlight_affected=True
                    )

            elif tag == 'replace':
                old_chunk = old_lines[i1:i2]
                new_chunk = new_lines[j1:j2]
                for row_tag, old_no, old_line, new_no, new_line in iter_aligned_chunk_rows(
                    old_chunk, new_chunk, i1, j1
                ):
                    if row_tag == 'equal':
                        add_row(diff_lines, old_no, ' ', old_line, new_no, ' ', new_line)

                    elif row_tag == 'delete':
                        add_row(
                            diff_lines, old_no, '-', old_line, None, ' ', '',
                            left_changed=True, left_highlight_affected=True
                        )

                    elif row_tag == 'insert':
                        add_row(
                            diff_lines, None, ' ', '', new_no, '+', new_line,
                            right_changed=True, right_highlight_affected=True
                        )

                    elif row_tag == 'replace':
                        highlighted_old, highlighted_new = get_block_level_diff(
                            old_line, new_line, old_line_bg='', new_line_bg=''
                        )
                        add_row(
                            diff_lines,
                            old_no,
                            '-',
                            highlighted_old,
                            new_no,
                            '+',
                            highlighted_new,
                            left_changed=False,
                            right_changed=False,
                        )

        diff_lines.append("")

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
            sys.exit(2)
    except FileNotFoundError:
        print(f"Error: File not found: {filepath}", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"Error reading file {filepath}: {e}", file=sys.stderr)
        sys.exit(2)


def non_negative_int(value):
    """Argparse type validator for non-negative integers."""
    ivalue = int(value)
    if ivalue < 0:
        raise argparse.ArgumentTypeError("context must be >= 0")
    return ivalue


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
        type=non_negative_int,
        default=3,
        help='Number of context lines to show (default: 3)'
    )
    parser.add_argument(
        '--side-by-side',
        '-s',
        action='store_true',
        help='Show diff in side-by-side panels with line numbers'
    )

    args = parser.parse_args()

    # Validate files exist
    file1_path = Path(args.file1)
    file2_path = Path(args.file2)

    if not file1_path.exists():
        print(f"Error: File not found: {args.file1}", file=sys.stderr)
        sys.exit(2)

    if not file2_path.exists():
        print(f"Error: File not found: {args.file2}", file=sys.stderr)
        sys.exit(2)

    # Disable colors if requested
    if args.no_color:
        for attr in dir(Colors):
            if not attr.startswith('_'):
                setattr(Colors, attr, '')

    # Read file contents as-is (no escape-sequence transformation)
    old_content = read_file(file1_path)
    new_content = read_file(file2_path)

    # Generate and display diff
    if args.side_by_side:
        diff_output = generate_side_by_side_diff(
            old_content,
            new_content,
            str(file1_path),
            str(file2_path),
            context=args.context,
        )
    else:
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
