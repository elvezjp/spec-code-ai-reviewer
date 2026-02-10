# md2map

[English](./README.md) | [日本語](./README_ja.md)

[![Elvez](https://img.shields.io/badge/Elvez-Product-3F61A7?style=flat-square)](https://elvez.co.jp/)
[![IXV Ecosystem](https://img.shields.io/badge/IXV-Ecosystem-3F61A7?style=flat-square)](https://elvez.co.jp/ixv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Stars](https://img.shields.io/github/stars/elvezjp/md2map?style=social)](https://github.com/elvezjp/md2map/stargazers)

A CLI tool that transforms large markdown documents into "semantic maps (index + document parts)" for AI analysis and review.

![Input/Output Example](docs/assets/example.png)

## Use Cases

- **AI Document Review**: Split large markdown files into AI-friendly semantic units to improve review accuracy
- **Document Structure Visualization**: Output heading hierarchy and section summaries as an index
- **Line Number Mapping**: Reliably map AI feedback to original file line numbers
- **Documentation Management**: Manage large specification documents by splitting them into maintainable parts

## Development Background

This tool was born as a small utility during the development of **IXV (Ixiv)**, an AI development assistant focused on Japanese development documents and specifications.

IXV tackles the challenges of understanding, structuring, and utilizing Japanese documents in system development. This repository publishes a portion of that work as open source.

## Features

- **Heading-Based Splitting**: Split documents by H1, H2, H3 (and deeper) heading levels
- **Markdown Index Generation**: Auto-generate INDEX.md with structure tree and section details
- **Line Number Mapping**: Provide correspondence between parts and original file in MAP.json (machine-readable)
- **Japanese Support**: Full support for Japanese document processing and character counting
- **Code Block Awareness**: Correctly handle headings inside code blocks (skip them)
- **Dry Run**: Preview generation plan before actual output

## Documents

- [CHANGELOG.md](CHANGELOG.md) - Version history
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [SECURITY.md](SECURITY.md) - Security policy
- [spec.md](spec.md) - Technical specification

## Setup

### Requirements

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) (recommended package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/elvezjp/md2map.git
cd md2map

# Install dependencies with uv (virtual environment created automatically)
uv sync --all-extras

# Verify installation
uv run md2map --help
```

## Usage

### Basic Execution

```bash
# Analyze a markdown file
uv run md2map build document.md --out ./output

# Analyze with custom depth (H1-H2 only)
uv run md2map build document.md --out ./output --max-depth 2
```

### Check Output

```bash
# View the index
cat output/INDEX.md

# View the split document parts
ls output/parts/

# View the line number mapping
cat output/MAP.json
```

### Dry Run (Preview)

```bash
# Preview the plan without generating files
uv run md2map build document.md --dry-run
```

## Main Options

| Option | Default | Description |
|--------|---------|-------------|
| `--out <DIR>` | `./md2map-out` | Output directory |
| `--max-depth <N>` | `3` | Maximum heading depth to process (1-6) |
| `--id-prefix <PREFIX>` | `MD` | Section ID prefix (MD1, MD2, ...) |
| `--verbose` | false | Output detailed logs |
| `--dry-run` | false | Preview only, no file generation |

For details, see `uv run md2map build --help`.

## Output Examples

### INDEX.md

```markdown
# Index: specification.md

## Structure Tree

- [MD1] Introduction (L1–L25) → [parts/Introduction.md](parts/Introduction.md)
  - [MD2] Background (L3–L10) → [parts/Introduction_Background.md](parts/Introduction_Background.md)
  - [MD3] Purpose (L11–L25) → [parts/Introduction_Purpose.md](parts/Introduction_Purpose.md)
- [MD4] Requirements (L26–L50) → [parts/Requirements.md](parts/Requirements.md)

## Section Details

### [MD1] Introduction (H1)
- lines: L1–L25
- summary: This document describes the system specification...
- keywords: system, specification, overview
```

### MAP.json

```json
[
  {
    "id": "MD1",
    "section": "Introduction",
    "level": 1,
    "path": "Introduction",
    "original_file": "specification.md",
    "original_start_line": 1,
    "original_end_line": 25,
    "word_count": 150,
    "part_file": "parts/Introduction.md",
    "checksum": "a1b2c3d4..."
  }
]
```

### Part Files

Each part file includes a metadata header:

```markdown
<!--
md2map fragment
id: MD1
original: specification.md
lines: 1-25
section: Introduction
level: 1
-->
# Introduction

This document describes the system specification...
```

## Directory Structure

```text
md2map/
├── md2map/                # Main package
│   ├── cli.py             # CLI entry point
│   ├── generators/        # Output generation modules
│   │   ├── index_generator.py   # INDEX.md generation
│   │   ├── map_generator.py     # MAP.json generation
│   │   └── parts_generator.py   # parts/ generation
│   ├── models/            # Data models
│   │   └── section.py     # Section information class
│   ├── parsers/           # Document parsers
│   │   ├── base_parser.py       # Base class
│   │   └── markdown_parser.py   # Markdown parser
│   └── utils/             # Utilities
│       ├── file_utils.py  # File operations
│       └── logger.py      # Log configuration
├── tests/                 # Test code
│   └── fixtures/          # Test fixtures
├── docs/                  # Documentation
├── CHANGELOG.md           # Version history
├── CONTRIBUTING.md        # Contribution guidelines
├── README.md              # This file (English)
├── README_ja.md           # Japanese README
├── SECURITY.md            # Security policy
├── spec.md                # Technical specification
└── pyproject.toml         # Project configuration
```

## Limitations

- **Single File Processing**: Currently processes one file at a time
- **ATX Headings Only**: Setext-style headings (underline) are not supported
- **No Link Correction**: Internal links are detected but not automatically corrected in parts

For details, see [spec.md](spec.md).

## Related Projects

- [code2map](https://github.com/elvezjp/code2map) - Similar tool for source code analysis

## Security

For security details, see [SECURITY.md](SECURITY.md).

- Use caution when processing files from untrusted sources
- Output files contain content from the original document

## Contributing

Contributions are welcome. For details, see [CONTRIBUTING.md](CONTRIBUTING.md).

- Bug reports and feature requests: [Issues](https://github.com/elvezjp/md2map/issues)
- Pull requests: Branch naming convention `{username}/{date}-{description}`

## Changelog

For details, see [CHANGELOG.md](CHANGELOG.md).

## License

MIT License - For details, see [LICENSE](LICENSE).

## Contact

- **Issues**: [GitHub Issues](https://github.com/elvezjp/md2map/issues)
- **Email**: info@elvez.co.jp
- **Company**: [Elvez Inc.](https://elvez.co.jp/)
