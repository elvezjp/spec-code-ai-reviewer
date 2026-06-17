# Contributing to spec-code-ai-reviewer

[English](./CONTRIBUTING.md) | [日本語](./CONTRIBUTING_ja.md)

This document describes guidelines for contributing to the project.

## How to Contribute

### Reporting Bugs

If you find a bug, please create a GitHub Issue with the following information:

- A clear, descriptive title
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Sample files (if possible)
- Python version (for backend issues)
- Node.js version (for frontend issues)
- Operating system

### Suggesting Enhancements

We welcome enhancement suggestions! Please create an Issue with:

- A clear, descriptive title
- Detailed description of the proposed feature
- Use cases and benefits
- Related examples or mockups

### Pull Requests

1. **Fork the repository** and create a branch from `main` (username/dateYYYYMMDD-description)
   ```bash
   git checkout -b user/20260105-fix-feature
   ```

2. **Follow the existing codebase's coding style**
   - Use meaningful variable and function names
   - Add comments for complex logic
   - Follow PEP 8 style guidelines

3. **Write tests** for your changes
   ```bash
   # Run backend tests
   cd versions/v0.9.9/backend
   uv run pytest tests/ -v

   # Run backend tests with coverage
   uv run pytest tests/ --cov=app --cov-report=html

   # Run frontend tests
   cd versions/v0.9.9/frontend
   npm run test:run

   # Run frontend tests with coverage
   npm run test:coverage
   ```

4. **Update documentation** as needed
   - Update README.md for user-facing changes
   - Update spec.md for specification changes
   - Add examples for new features

5. **Commit your changes** with clear commit messages
   ```bash
   git commit -m "Add feature: description of your changes"
   ```

6. **Push to your fork** and submit a pull request
   ```bash
   git push origin user/20260105-fix-feature
   ```

7. **Wait for review** — maintainers will review your PR and may request changes

## Development Environment Setup

### Prerequisites

- Python 3.11 or later
- Node.js 20 or later
- [uv](https://docs.astral.sh/uv/) package manager
- AWS account (with Bedrock access) or Anthropic/OpenAI API key

### Installation

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/spec-code-ai-reviewer.git
cd spec-code-ai-reviewer

# Install backend dependencies
cd versions/v0.9.9/backend
uv sync

# Install frontend dependencies
cd ../frontend
npm install
```

### Running Tests

```bash
# Backend: Run all tests
cd versions/v0.9.9/backend
uv run pytest tests/ -v

# Backend: Run a specific test file
uv run pytest tests/test_convert.py -v

# Backend: Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Frontend: Run all tests
cd versions/v0.9.9/frontend
npm run test:run

# Frontend: Run tests in watch mode
npm run test

# Frontend: Run with coverage
npm run test:coverage
```

### Testing Your Changes

Before submitting a PR, verify the following:

1. All existing tests pass
2. New tests are added for new features
3. Code coverage is maintained or improved
4. The application works correctly with various files

## Coding Guidelines

### Python Style (Backend)

- Follow PEP 8 style guidelines
- Use type hints where appropriate
- Maximum line length: 100 characters (flexible for long strings)
- Use meaningful variable names

### TypeScript/React Style (Frontend)

- Follow ESLint configuration (`npm run lint` to check)
- Use TypeScript strict mode
- Write function components
- Style with Tailwind CSS
- Use meaningful component and variable names

### Documentation

- Add docstrings/JSDoc to all public functions and classes
- Use clear, concise language
- Include examples in docstrings when helpful

### Commit Messages

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or fewer
- Reference issues and pull requests when relevant

Example:
```
Add multi-provider LLM support

- Add Anthropic API integration
- Add OpenAI API integration
- Update configuration file format

Closes #123
```

## Version Management

When contributing:
- Focus on the latest version (`versions/v0.9.9/`)
- Maintain backward compatibility where possible
- Clearly document breaking changes

### When to bump the version

Bump the version when there is a meaningful change to the repository — new features, bug fixes, or significant documentation additions. Dependency-only updates (e.g. routine security patches from Dependabot) do **not** trigger a version bump on their own; record them in `[Unreleased]` and include them in the next release that has a meaningful change.

### Tagging a release

After the version-bump commit is merged into `main`, tag it and push:

```bash
git tag -a v1.0.0 -m "Release v1.0.0"
git push origin v1.0.0
```

## Code Review Process

1. Maintainers will review your pull request
2. There may be change requests or questions
3. Once approved, the PR will be merged
4. Contributions will be acknowledged in release notes

## Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help others when possible
- Follow the code of conduct

## Questions

If you have questions about contributing, feel free to:
- Create an Issue with the "question" label
- Contact the maintainers
