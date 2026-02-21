# zdiff.py - Advanced Text Diff Tool

[![Version](https://img.shields.io/badge/version-1.0-blue.svg)](https://github.com/example/zdiff)
[![Python](https://img.shields.io/badge/python-3.6+-green.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange.svg)](LICENSE)

A professional diff tool that provides git-style output with intelligent block-level highlighting, consecutive word merging, and clean visual formatting. Designed for enhanced readability and professional code/text comparison.

![zdiff demo](demo.gif)

## ✨ Features

- **🎯 Git-style diff output** - Professional formatting with file headers, hunk headers, and line numbers
- **🔗 Consecutive block merging** - Adjacent changed words form continuous highlight blocks
- **🎨 Professional color scheme** - Blue/green backgrounds with white text optimized for readability
- **📝 Smart LaTeX preservation** - Intelligent handling of LaTeX commands and escape sequences
- **📏 Word-boundary awareness** - Clean highlighting without character fragmentation
- **⚙️ Customizable context** - Control number of context lines displayed
- **🪟 Side-by-side mode** - Compare file1 (left) and file2 (right) with line numbers in both panels
- **✅ Standard exit codes** - Proper exit codes for scripting integration

## 🚀 Installation

### Prerequisites

- Python 3.6 or higher
- No additional dependencies required (uses only standard library)

### Quick Install

```bash
# Clone or download zdiff.py
wget https://raw.githubusercontent.com/example/zdiff/main/zdiff.py
chmod +x zdiff.py

# Or clone the repository
git clone https://github.com/example/zdiff.git
cd zdiff
chmod +x zdiff.py
```

## 📖 Usage

### Basic Usage

```bash
# Compare two files
python zdiff.py file1.txt file2.txt

# Make executable and use directly
./zdiff.py file1.txt file2.txt
```

### Command Line Options

```bash
# Show help
python zdiff.py --help

# Custom context lines (default: 3)
python zdiff.py --context 5 file1.txt file2.txt
python zdiff.py -c 5 file1.txt file2.txt

# Side-by-side layout (left: file1, right: file2)
python zdiff.py --side-by-side file1.txt file2.txt
python zdiff.py -s file1.txt file2.txt
```

### Full Command Reference

```
usage: zdiff.py [-h] [--context CONTEXT] [--side-by-side] file1 file2

zdiff - Advanced Text Diff Tool with Git-Style Output

Features intelligent block-level highlighting, consecutive word merging,
and professional formatting optimized for code and text comparison.

positional arguments:
  file1                 First file to compare
  file2                 Second file to compare

options:
  -h, --help            show this help message and exit
  --context CONTEXT, -c CONTEXT
                        Number of context lines to show (default: 3)
  --side-by-side, -s    Show diff in side-by-side panels with line numbers
```

## 🎨 Output Examples

### Standard Diff Output

```diff
--- file1.txt
+++ file2.txt
@@ -1,5 +1,5 @@
   1  Hello world! This is a test file.
   2  It contains multiple lines of text.
-  3  Some lines will be changed.
+  3  Some lines have been modified here.
   4  Others will remain the same.
-  5  This is line five.
+  5  This is line five with extra content.
```

### Key Visual Features

- **Gray line numbers** for easy reference
- **Blue backgrounds** for deleted content with highlighted changed words
- **Green backgrounds** for added content with highlighted changed words
- **Consecutive highlighting** - Multiple adjacent changes appear as continuous blocks
- **Context lines** shown without highlighting for reference

## 📏 Diff Highlighting Rules (Final Output)

One-line concrete examples (`file1 => file2`):

- `Unchanged line`: `Keep this line.` => `Keep this line.` (no highlight on either side).
- `Changed line (single-column)`: `- Mod: speed` => `+ Mod: distance` (only changed tokens are highlighted).
- `Changed line (side-by-side -s)`: `L: -Mod: speed || R: +Mod: distance` (same changed-token highlight in both panels).
- `Word-level scope`: `alpha beta gamma` => `alpha delta gamma` (only `beta`/`delta` highlighted, not neighbors).
- `Replace case`: `status=old` => `status=new` (old token highlighted left, new token highlighted right).
- `Insert-in-line case`: `route=/api/v1` => `route=/api/v2?sort=desc` (inserted part highlighted on right only).
- `Delete-in-line case`: `remove this marker now` => `remove marker now` (deleted part highlighted on left only).
- `Mixed edit case`: `A beta C zeta` => `A extra C iota` (delete+insert spans highlighted where they exist).
- `Pure line deletion`: `Line delete only: remove me.` => `<no line>` (full deleted line shown on left only).
- `Pure line insertion`: `<no line>` => `Line insert only: add me.` (full inserted line shown on right only).
- `Whitespace-only change`: `key=[␠␠␠]` => `key=[␠␠]` (space-only segment gets whitespace highlight color).
- `Unicode/emoji/punctuation`: `版本=甲, stage-A 🙂` => `版本=乙, stage-B 🙂` (only changed spans highlighted).
- `Long lines`: `long ... old-tail` => `long ... new-tail` (line may clip with `...`, highlight stays on changed part).
- `Context around hunks`: `Context A` => `Context A` (shown as plain context without highlight).
- `No textual changes`: `same file` => `same file` (prints `No changes detected`).
- `EOF-newline-only difference`: `tail<no trailing newline>` => `tail<trailing newline>` (prints EOF newline difference block).

Visual preview page: `diff_highlighting_examples.html`

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

The tool preserves LaTeX commands while properly handling escape sequences:
- `\text`, `\tan`, `\times` → Preserved as LaTeX commands
- `\t` (standalone) → Converted to tab character
- `\n` → Converted to newline

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

- **Memory efficient** - Streams file content without loading entire files into memory
- **Fast processing** - Character-level diff with word-boundary optimization
- **Large file support** - Handles files of any size with proper encoding detection

## 🔍 Comparison with Standard Tools

| Feature | zdiff.py | git diff | GNU diff | diff-so-fancy |
|---------|----------|----------|----------|---------------|
| Consecutive block merging | ✅ | ❌ | ❌ | ❌ |
| Word-boundary awareness | ✅ | ❌ | ❌ | ✅ |
| LaTeX command preservation | ✅ | ❌ | ❌ | ❌ |
| Professional color scheme | ✅ | ✅ | ❌ | ✅ |
| No dependencies | ✅ | ❌ | ✅ | ❌ |
| Cross-platform | ✅ | ✅ | ✅ | ❌ |

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

### Exit Codes

- `0` - Files are identical
- `1` - Files differ (normal case)
- `2` - Error occurred (file not found, etc.)

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

### v1.0.0 (2025-08-08)
- Initial release
- Git-style diff output
- Consecutive block merging
- Professional color scheme
- Smart LaTeX command preservation
- Word-boundary-aware highlighting
- Context control

---

**Made with ❤️ for developers who appreciate clean, readable diffs.**
