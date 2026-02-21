# zdiff.py - Advanced Text Diff Tool

[![Version](https://img.shields.io/badge/version-1.1-blue.svg)](https://github.com/example/zdiff)
[![Python](https://img.shields.io/badge/python-3.6+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

A professional diff tool that provides git-style output with intelligent block-level highlighting, consecutive word merging, and clean visual formatting. Designed for enhanced readability and professional code/text comparison.

![zdiff demo](demo.gif)

## ✨ Features

- **🎯 Git-style diff output** - Professional formatting with file headers, hunk headers, and line numbers
- **🔗 Consecutive block merging** - Adjacent changed words form continuous highlight blocks
- **🎨 Professional color scheme** - Blue/green backgrounds with white text optimized for readability
- **📝 LaTeX-friendly text diffing** - Backslash-based expressions are kept as literal text during comparison
- **📏 Word-boundary awareness** - Clean highlighting without character fragmentation
- **⚙️ Customizable context** - Control number of context lines displayed
- **🪟 Side-by-side mode** - Compare file1 (left) and file2 (right) with line numbers in both panels
- **✅ Standard exit codes** - Proper exit codes for scripting integration

## 🚀 Quick Start

Requirements: Python 3.6+ and no extra dependencies.

```bash
# from repo root
python zdiff.py file1.txt file2.txt
python zdiff.py -s file1.txt file2.txt
python zdiff.py -c 5 file1.txt file2.txt
python zdiff.py --help

# optional executable mode
chmod +x zdiff.py
./zdiff.py file1.txt file2.txt
```

CLI synopsis:

```text
usage: zdiff.py [-h] [--context CONTEXT] [--side-by-side] file1 file2
```

Exit codes:

- `0` - Files are identical
- `1` - Files differ (normal case)
- `2` - Error occurred (file not found, etc.)

## 🎨 Output Examples

### Standard Diff Output

```diff
--- file1.txt
+++ file2.txt
@@ -1,14 +1,14 @@
   1  Case 01 unchanged: Keep this line.
-  2  Case 02 replace: status=old
+  2  Case 02 replace: status=new
-  3  Case 03 word scope: alpha beta gamma
+  3  Case 03 word scope: alpha delta gamma
-  4  Case 04 insert-in-line: route=/api/v1
+  4  Case 04 insert-in-line: route=/api/v1?sort=desc
-  5  Case 05 delete-in-line: remove this marker now
+  5  Case 05 delete-in-line: remove marker now
-  6  Case 06 mixed: Drift: alpha beta gamma delta epsilon zeta eta theta.
+  6  Case 06 mixed: Drift: alpha gamma delta extra epsilon eta theta iota.
-  7  Case 07 pure line deletion: Line delete only: remove me.
   8  Case 07/08 shared anchor: keep this line.
+  8  Case 08 pure line insertion: Line insert only: add me.
-  9  Case 09 whitespace-only: Whitespace: key=[   ]
+  9  Case 09 whitespace-only: Whitespace: key=[  ]
- 10  Case 10 unicode/emoji: version=甲, stage-A 🙂
+ 10  Case 10 unicode/emoji: version=乙, stage-B 🙂
- 11  Case 11 long-line clipping: Long: old token token token token token token token token end
+ 11  Case 11 long-line clipping: Long: new token token token token token token token token end
  12  Case 12 context A
- 13  Case 12 context change: change-old
+ 13  Case 12 context change: change-new
  14  Case 12 context B
```

### zdiff Output

Each rule below uses a one-line minimal `before => after` example (validated against current `zdiff` output):
Rules 1-12 map directly to the lines in the Standard Diff Output block above; rules 13-14 are special standalone outcomes.

<code><span style="background:#ffd6db;padding:0 2px;border-radius:3px;">old-side changed text</span></code>
<code><span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">new-side changed text</span></code>

#### 1) Unchanged line
<code>Keep this line.</code> => <code>Keep this line.</code> (no highlight on either side).

#### 2) Replace (single-column and -s)
<code>status=<span style="background:#ffd6db;padding:0 2px;border-radius:3px;">old</span></code> => <code>status=<span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">new</span></code>.

#### 3) Word-level scope
<code>alpha <span style="background:#ffd6db;padding:0 2px;border-radius:3px;">beta</span> gamma</code> => <code>alpha <span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">delta</span> gamma</code>.

#### 4) Insert-in-line
<code>route=/api/v1</code> => <code>route=/api/<span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">v1?sort=desc</span></code>.

#### 5) Delete-in-line
<code>remove <span style="background:#ffd6db;padding:0 2px;border-radius:3px;">this</span> marker now</code> => <code>remove marker now</code>.

#### 6) Mixed delete+insert
<code>Drift: alpha <span style="background:#ffd6db;padding:0 2px;border-radius:3px;">beta</span> ... epsilon <span style="background:#ffd6db;padding:0 2px;border-radius:3px;">zeta</span> ...</code> => <code>Drift: alpha ... <span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">extra</span> epsilon ... <span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">iota</span> ...</code>.

#### 7) Pure line deletion
<code><span style="background:#ffd6db;padding:0 2px;border-radius:3px;">Line delete only: remove me.</span></code> => <code>&empty;</code>.

#### 8) Pure line insertion
<code>&empty;</code> => <code><span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">Line insert only: add me.</span></code>.

#### 9) Whitespace-only change
<code>Whitespace: key=[␠␠<span style="background:#ffd6db;padding:0 2px;border-radius:3px;">␠</span>]</code> => <code>Whitespace: key=[␠␠]</code>.

#### 10) Unicode/emoji/punctuation
<code>版本=<span style="background:#ffd6db;padding:0 2px;border-radius:3px;">甲</span>, stage-<span style="background:#ffd6db;padding:0 2px;border-radius:3px;">A</span> 🙂</code> => <code>版本=<span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">乙</span>, stage-<span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">B</span> 🙂</code>.

#### 11) Long-line panel clipping
<code>Long: <span style="background:#ffd6db;padding:0 2px;border-radius:3px;">old</span> token token token ...</code> => <code>Long: <span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">new</span> token token token ...</code>.

#### 12) Context around hunks
<code>A / <span style="background:#ffd6db;padding:0 2px;border-radius:3px;">change-old</span> / B</code> => <code>A / <span style="background:#c9f7d8;padding:0 2px;border-radius:3px;">change-new</span> / B</code>.

#### 13) No textual changes
<code>same</code> => <code>same</code> (prints <code>No changes detected</code>).

#### 14) EOF-newline-only difference
<code>tail&lt;no trailing newline&gt;</code> => <code>tail&lt;trailing newline&gt;</code> (prints explicit EOF newline difference block).

Visual preview page: `diff_highlighting_examples.html`

### Key Visual Features

- **Gray line numbers** for easy reference
- **Blue backgrounds** for deleted content with highlighted changed words
- **Green backgrounds** for added content with highlighted changed words
- **Consecutive highlighting** - Multiple adjacent changes appear as continuous blocks
- **Context lines** shown without highlighting for reference

## 🔧 Advanced Features

### Consecutive Block Merging

Unlike traditional diff tools that highlight individual words, zdiff intelligently merges adjacent changes:

**Traditional approach:**
```
Some [lines] [will] [be] [changed]
```

**zdiff approach:**
```
Some [lines will be changed]
```

### Smart LaTeX Handling

The tool compares LaTeX-like strings as plain text:
- `\text`, `\tan`, `\times` are preserved as literal substrings in output
- backslashes are not interpreted as control escapes during diffing
- `\t` / `\n` remain literal two-character sequences unless your input file already contains real tab/newline characters

### Word Boundary Intelligence

Changes are expanded to complete word boundaries to avoid fragmented highlighting:
```
# Avoids: He[llo wo]rld
# Shows:  [Hello world]
```

## 🛠 Integration Examples

### Shell Scripts

```bash
#!/bin/bash
# Compare files and handle results
if python zdiff.py old_config.json new_config.json; then
    echo "Files are identical"
else
    echo "Files differ"
fi
```

### Makefile Integration

```makefile
check-diff:
    python zdiff.py expected_output.txt actual_output.txt || exit 1

test: check-diff
    @echo "All tests passed"
```

### Git Alias

```bash
# Add to ~/.gitconfig
[alias]
    zdiff = !python /path/to/zdiff.py
```

## 📊 Performance

- **In-memory comparison** - Reads both input files fully before diffing
- **Fast processing** - Character-level diff with word-boundary optimization
- **Best for small/medium files** - Very large files may be slower due to full in-memory processing

## 🔍 Tool Focus

- `zdiff` prioritizes human-readable terminal output over minimal/raw diff output.
- It combines line-level context with inline token-level highlights.
- It includes side-by-side panels with line numbers for both files.
- It preserves useful scriptability semantics via stable exit codes (`0/1/2`).

## 🐛 Troubleshooting

### Common Issues

**Colors not showing:**
```bash
# Try with explicit color support
python zdiff.py file1.txt file2.txt
```

**File encoding errors:**
- zdiff automatically tries UTF-8 first, then falls back to latin-1
- Most text files should work without issues

**Large file performance:**
- For very large files, consider using standard tools first
- zdiff is optimized for readability over raw speed

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/example/zdiff.git
cd zdiff
python -m pytest tests/  # Run tests (if available)
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by git diff and GNU diff
- Built with Python's excellent `difflib` module
- Color scheme inspired by professional IDE themes
- Special thanks to the open-source community

## 📞 Support

- **Author:** Zhiyuan Yao (zhiyuan.yao@icloud.com)
- **Institution:** Lanzhou Center for Theoretical Physics, Lanzhou University
- **Issues:** [GitHub Issues](https://github.com/example/zdiff/issues)
- **Documentation:** This README and inline help (`--help`)

## 🔄 Version History

### v1.1.0 (2026-02-21)
- Side-by-side mode (`-s`) with dual line-number panels
- Improved word-level highlighting behavior across mixed insert/delete/replace cases
- Refined whitespace-only and boundary-aware highlight rendering
- Updated documentation and demo assets

### v1.0.0 (2025-08-08)
- Initial release
- Git-style diff output
- Consecutive block merging
- Professional color scheme
- LaTeX-friendly literal text comparison
- Word-boundary-aware highlighting
- Context control

---

**Made with ❤️ for developers who appreciate clean, readable diffs.**
