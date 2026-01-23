# add-line-numbers
[English](./README.md) | [日本語](./README_ja.md)

[![Elvez](https://img.shields.io/badge/Elvez-Product-3F61A7?style=flat-square)](https://elvez.co.jp/)
[![IXV Ecosystem](https://img.shields.io/badge/IXV-Ecosystem-3F61A7?style=flat-square)](https://elvez.co.jp/ixv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.8+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Stars](https://img.shields.io/github/stars/elvezjp/add-line-numbers?style=social)](https://github.com/elvezjp/add-line-numbers/stargazers)

A Python script that automatically adds 4-digit right-aligned line numbers to text files. It makes code reviews and AI analysis easier by letting you point to “line X.” No external libraries required—just Python 3.8+.

## Quick Start

1. Clone and move into the repo
   ```bash
   git clone https://github.com/elvezjp/add-line-numbers.git
   cd add-line-numbers
   ```
2. Run as-is (`inputs/` → `outputs/`)
   ```bash
   python add_line_numbers.py
   ```
3. Check the results
   - Converted files are generated in `outputs/`
   - `outputs/README.md` is auto-generated with structure and usage notes

## A Bit More Detail (Beginner Friendly)

- What does it do?
  - Adds a line number prefix (e.g., `   1: `) to each line of text files
  - Copies files to the output while preserving the input directory structure
  - Automatically generates a README in the output directory

- Supported files
  - General UTF-8 text files (.py, .java, .js, .json, .xml, .md, .txt, etc.)
  - Binary files or non-UTF-8 files are automatically skipped

- Requirements
  - Python 3.8 or later
  - No extra pip installs needed

## Usage

### Default (no arguments)
```bash
python add_line_numbers.py
# Reads inputs/ and writes to outputs/
```

### Specify input and output
```bash
python add_line_numbers.py <input_dir> <output_dir>
```
Example:
```bash
python add_line_numbers.py my_project numbered_output
```

### Sample output log
```
Processing: 64 files
Input: inputs
Output: outputs
------------------------------------------------------------
✓ src/main.py
✓ config/settings.json
✓ docs/README.md
------------------------------------------------------------
Done: processed 64 files
✓ README.md generated: outputs/README.md
```

## How the Line Numbers Look

- Format: `   1: ` (4-digit right-aligned + colon + space)

Before:
```python
def hello():
    print("Hello, World!")

if __name__ == "__main__":
    hello()
```

After:
```
   1: def hello():
   2:     print("Hello, World!")
   3:
   4: if __name__ == "__main__":
   5:     hello()
```

## Tips and Gotchas

- If the input directory does not exist, the script exits with an error. Double-check the path.
- Non-UTF-8 or binary files are skipped. Convert them to UTF-8 if needed.
- Large folders can take some time; check the console log for progress.

## Running Tests
```bash
pip install pytest   # if not installed
pytest test.py -v
```

## File Layout
```
add-line-numbers/
├── add_line_numbers.py   # main script
├── test.py               # unit tests
├── spec.md               # detailed specification
├── LICENSE               # MIT license
└── README.md             # this file
```
### Background
This tool originated during the development of **IXV**, a development-support AI for Japanese technical documents and specifications.

IXV focuses on understanding, structuring, and utilizing Japanese documents in system development. This repository publishes a small, practical piece of that effort.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Contact

- **Email**: info@elvez.co.jp
- **Company**: Elvez Inc.
