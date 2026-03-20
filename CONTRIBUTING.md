# Contributing to md2map

[English](./CONTRIBUTING.md) | [日本語](./CONTRIBUTING_ja.md)

Thank you for your interest in contributing to md2map. This document explains how to contribute to the project.

## Ways to Contribute

You can contribute to the project in the following ways:

- **Bug reports**: Create an Issue if you find a problem
- **Feature proposals**: Propose new feature ideas via Issues
- **Pull requests**: Submit code fixes or feature additions via PRs

## Bug Reports

When reporting a bug, create an Issue with the following information:

- **Clear, descriptive title**: A title that concisely describes the issue
- **Steps to reproduce**: Specific steps to reproduce the problem
- **Expected behavior**: How it should work
- **Actual behavior**: What actually happened, including error messages
- **Sample file** (if possible): An input Markdown file that reproduces the issue
- **Environment information**:
  - md2map version (`uv run md2map --version`)
  - Python version (`python --version`)
  - OS (macOS, Linux, Windows, etc.)

### Bug Report Example

```markdown
## Title
Headings inside code blocks are incorrectly split

## Steps to Reproduce
1. Install md2map
2. Create a Markdown file with the following content:
   ```markdown
   # Introduction

   Here is some sample code:

   ```python
   # This is a comment, not a heading
   def foo():
       pass
   ```
   ```
3. Run `uv run md2map build test.md --out ./out`

## Expected Behavior
`# This is a comment` inside the code block is not recognized as a heading

## Actual Behavior
The comment inside the code block is split as a heading

## Environment
- md2map: 0.1.0
- Python: 3.11.0
- OS: macOS 14.0
```

## Feature Proposals

When proposing a new feature or improvement, create an Issue with the following information:

- **Clear, descriptive title**: A title that concisely describes the proposal
- **Detailed description**: Specific explanation of what you want to achieve
- **Use cases and benefits**: Why this feature is needed and in what scenarios it would be useful
- **Related examples or mockups** (if possible): Samples of expected output format or behavior

## Pull Request Process

### 1. Fork and Create a Branch

```bash
# Fork the repository (on GitHub)

# Clone your fork
git clone https://github.com/YOUR_USERNAME/md2map.git
cd md2map

# Add upstream
git remote add upstream https://github.com/elvezjp/md2map.git

# Create a working branch
git checkout -b YOUR_USERNAME/YYYYMMDD-feature-name
```

**Branch naming convention**: `{username}/{dateYYYYMMDD}-{description}`

Examples:
- `tominaga/20260203-add-frontmatter-support`
- `yamada/20260210-fix-codeblock-detection`

### 2. Follow Coding Style

- Follow the [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use Ruff to format your code

```bash
# Format and lint code
uv run ruff format .
uv run ruff check . --fix
```

### 3. Write and Run Tests

Add corresponding tests for new features and bug fixes.

```bash
# Run all tests
uv run pytest

# Run a specific test file
uv run pytest tests/test_markdown_parser.py

# Generate coverage report
uv run pytest --cov=md2map --cov-report=html
```

### 4. Update Documentation

- Update README.md if you add new features
- Update related documentation if there are API changes

### 5. Commit Message Guidelines

Write commit messages in the following format:

```
<type>: <subject>

<body>

<footer>
```

**type**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation-only changes
- `style`: Changes that don't affect code meaning (formatting, etc.)
- `refactor`: Code changes that are neither bug fixes nor new features
- `test`: Adding or modifying tests
- `chore`: Build process or tool changes

**Good example**:
```
feat: Add frontmatter parsing support

Implemented parsing for Markdown files containing YAML frontmatter.
- Added frontmatter skipping support
- Added metadata extraction support

Closes #123
```

**Bad examples**:
```
fix bug
```
```
fixed
```

### 6. Push and Submit PR

```bash
# Push your changes
git push origin YOUR_USERNAME/YYYYMMDD-feature-name
```

Create a Pull Request on GitHub and include:

- Description of changes
- Related Issue number (if any)
- How to test

### 7. Address Reviews

- Respond to review comments politely
- If fixes are needed, add additional commits

### Pre-PR Checklist

- [ ] Code follows PEP 8 style
- [ ] `uv run ruff check .` completes without errors
- [ ] `uv run pytest` all pass
- [ ] Added corresponding tests for new features
- [ ] Updated documentation as needed
- [ ] Commit messages follow the convention

## Development Environment Setup

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/elvezjp/md2map.git
cd md2map

# Install with development dependencies
uv sync --all-extras

# Verify installation
uv run md2map --help
uv run pytest
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_markdown_parser.py

# Run a specific test function
uv run pytest tests/test_markdown_parser.py::test_parse_headings

# Run with coverage
uv run pytest --cov=md2map

# Generate HTML coverage report
uv run pytest --cov=md2map --cov-report=html
open htmlcov/index.html
```

## Coding Guidelines

### Style Guide

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use Ruff as the formatter and linter

### Naming Conventions

- **Functions/variables**: snake_case (e.g., `parse_markdown`, `output_dir`)
- **Classes**: PascalCase (e.g., `MarkdownParser`, `Section`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_OUTPUT_DIR`)
- **Private**: Leading underscore (e.g., `_internal_method`)

### Documentation

- Add docstrings to public functions and classes
- Google-style docstrings are recommended

```python
def parse_markdown(file_path: str, max_depth: int = 3) -> list[Section]:
    """Parse a Markdown file and extract section information.

    Args:
        file_path: Path to the Markdown file to parse
        max_depth: Maximum heading depth to process (1-6)

    Returns:
        List of section information

    Raises:
        FileNotFoundError: If the file does not exist
        ParseError: If parsing fails
    """
```

## Contact

- For questions or discussions, create an Issue on GitHub
- Adding the `question` label would be helpful
- For general discussions, GitHub Discussions is also available

---

We look forward to your contributions!
