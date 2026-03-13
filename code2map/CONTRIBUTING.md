[English](./CONTRIBUTING.md) | [日本語](./CONTRIBUTING_ja.md)

# Contributing to code2map

Thank you for your interest in contributing to code2map. This document explains how to contribute to the project.

## Ways to Contribute

You can contribute to the project in the following ways:

- **Bug reports**: If you find a problem, create an Issue
- **Feature proposals**: If you have ideas for new features, propose them via an Issue
- **Pull requests**: Send code fixes or new features as a PR

## Bug Reports

When reporting a bug, create an Issue with the following information:

- **Clear and descriptive title**: A concise title describing the problem
- **Steps to reproduce**: Specific steps to reproduce the problem
- **Expected behavior**: How it should work
- **Actual behavior**: What actually happened, including error messages
- **Sample file** (if possible): An input file that reproduces the problem
- **Environment**:
  - code2map version (`uv run code2map --version`)
  - Python version (`python --version`)
  - OS (macOS, Linux, Windows, etc.)

### Bug Report Example

```markdown
## Title
Parsing fails for methods with decorators in Python 3.12

## Steps to Reproduce
1. Install code2map in a Python 3.12 environment
2. Create a file with the following code:
   ```python
   class Foo:
       @property
       def bar(self):
           return 1
   ```
3. Run `uv run code2map build test.py --out ./out`

## Expected Behavior
The `bar` property is listed in INDEX.md

## Actual Behavior
The following error occurs:
```
ParseError: Unexpected token at line 3
```

## Environment
- code2map: 0.1.0
- Python: 3.12.0
- OS: macOS 14.0
```

## Feature Proposals

When proposing a new feature or improvement, create an Issue with the following information:

- **Clear and descriptive title**: A concise title describing the proposal
- **Detailed description**: A specific explanation of what you want to achieve
- **Use cases and benefits**: Why this feature is needed and when it would be useful
- **Examples or mockups** (if possible): Samples of the expected output format or behavior

## Pull Request Process

### 1. Fork the Repository and Create a Branch

```bash
# Fork the repository (done on GitHub)

# Clone your forked repository
git clone https://github.com/YOUR_USERNAME/code2map.git
cd code2map

# Add upstream
git remote add upstream https://github.com/elvezjp/code2map.git

# Create a working branch
git checkout -b YOUR_USERNAME/YYYYMMDD-feature-name
```

**Branch naming convention**: `{username}/{date YYYYMMDD}-{description}`

Examples:
- `tominaga/20260127-add-typescript-support`
- `yamada/20260201-fix-parse-error`

### 2. Follow the Coding Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
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
uv run pytest tests/test_python_parser.py

# Generate a coverage report
uv run pytest --cov=code2map --cov-report=html
```

### 4. Update Documentation

- If you add a new feature, update README.md
- If there are API changes, update the relevant documentation

### 5. Commit Message Format

Write commit messages in the following format:

```
<type>: <subject>

<body>

<footer>
```

**type**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect code meaning (formatting, etc.)
- `refactor`: Code changes that are neither bug fixes nor new features
- `test`: Adding or modifying tests
- `chore`: Changes to build processes or tools

**Good example**:
```
feat: Add TypeScript parser

Implemented analysis for TypeScript files (.ts, .tsx).
- Supports extraction of classes, functions, and interfaces
- Supports decorator parsing

Closes #123
```

**Bad examples**:
```
fix bug
```
```
update
```

### 6. Push and Submit PR

```bash
# Push changes
git push origin YOUR_USERNAME/YYYYMMDD-feature-name
```

Create a Pull Request on GitHub and include:

- Description of the changes
- Related Issue number (if any)
- How to test

### 7. Respond to Review

- Respond to review comments politely
- For requested changes, add additional commits

### Pre-submission Checklist

- [ ] Code follows PEP 8 style
- [ ] `uv run ruff check .` completes without errors
- [ ] `uv run pytest` passes all tests
- [ ] New features have corresponding tests added
- [ ] Documentation updated as needed
- [ ] Commit messages follow the convention

## Development Environment Setup

### Prerequisites

- Python 3.9 or higher
- [uv](https://docs.astral.sh/uv/) (recommended package manager)
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/elvezjp/code2map.git
cd code2map

# Install including dev dependencies
uv sync --all-extras

# Verify installation
uv run code2map --help
uv run pytest
```

## Running Tests

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run a specific test file
uv run pytest tests/test_python_parser.py

# Run a specific test function
uv run pytest tests/test_python_parser.py::test_parse_class

# Run with coverage
uv run pytest --cov=code2map

# Generate HTML coverage report
uv run pytest --cov=code2map --cov-report=html
open htmlcov/index.html
```

## Coding Guidelines

### Style Guide

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use Ruff as formatter and linter

### Naming Conventions

- **Functions & variables**: snake_case (e.g., `parse_file`, `output_dir`)
- **Classes**: PascalCase (e.g., `PythonParser`, `SymbolInfo`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_OUTPUT_DIR`)
- **Private**: Leading underscore (e.g., `_internal_method`)

### Documentation

- Add docstrings to public functions and classes
- Google-style docstrings are recommended

```python
def parse_file(file_path: str, language: str | None = None) -> ParseResult:
    """Parse a source file and extract symbol information.

    Args:
        file_path: Path to the file to parse
        language: Language override (auto-detected from extension if omitted)

    Returns:
        ParseResult object containing the analysis results

    Raises:
        FileNotFoundError: If the file does not exist
        ParseError: If parsing fails
    """
```

## Contact

- For questions or discussions, create a GitHub Issue
- Attaching a `question` label is appreciated
- GitHub Discussions is also available for general topics

---

We look forward to your contributions!
