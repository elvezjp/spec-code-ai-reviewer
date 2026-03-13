[English](./CHANGELOG.md) | [日本語](./CHANGELOG_ja.md)

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-12

### Changed

- **Replace Java parser with Tree-sitter**: Fully replaced `javalang` with `tree-sitter` + `tree-sitter-java` ([#9](https://github.com/elvezjp/code2map/issues/9))
  - Java 8+ syntax (lambda expressions, method references `Type[]::new`, etc.) now parses correctly
  - On syntax errors, returns a warning with the error line number (partial parse results are returned)
  - Future syntax (records, sealed classes, switch expressions, etc.) can also be supported

### Added

- **Tests**: Added tests for correct parsing of Java 8+ syntax and warning return on parse errors

### Changed (Dependencies)

```diff
- javalang>=0.13.0
+ tree-sitter>=0.21.0
+ tree-sitter-java>=0.21.0
```

- Saved v0.1.3 snapshot to `versions/v0.1.3/`

## [0.1.3] - 2026-03-12

### Fixed

- **Java parse error message improvement**: Fixed an issue where the error message was empty when parsing failed on files containing Java 8+ syntax ([#9](https://github.com/elvezjp/code2map/issues/9))
  - Now uses `description` and `at` attributes of `JavaSyntaxError` to output the cause and location of the error
  - Before: `"Java parse error: "` (empty)
  - After: `"Java parse error: Expected '.' (at Keyword "new" line N, position M)"`

### Added

- **Tests**: Added 3 test cases for Java parse error messages
- **Test fixture**: Added a Java file containing Java 8+ syntax (method reference `Type[]::new`)

### Changed

- Saved v0.1.2 snapshot to `versions/v0.1.2/`

## [0.1.2] - 2026-02-25

### Fixed

- **Filename sanitization**: parts/ filenames now strip Windows-reserved characters (`< > : " / \ | ? *`) ([#5](https://github.com/elvezjp/code2map/issues/5))
  - Java constructor `<init>` filename changed from `User_<init>.java` to `User_init.java`
  - Resolves `git clone` failures on Windows environments
  - Collisions caused by sanitization are still resolved by the existing hash-suffix mechanism

### Added

- **Tests**: Added 3 test cases for filename sanitization

### Changed

- Regenerated sample output files (`docs/examples/java/output/`)
- Added filename sanitization specification to `spec.md`
- Saved v0.1.1 snapshot to `versions/v0.1.1/`

## [0.1.1] - 2026-02-06

### Added

- **Symbol ID feature**: Assigns a unique identifier to each symbol
  - `--id-prefix`: Allows specifying the symbol ID prefix (default: `CD`)
  - INDEX.md: Displays IDs before symbol names in `[CD1]` format
  - MAP.json: Added `id` field at the top
  - parts/: Added `id: CD1` line to headers

- **Tests**: Added tests for the ID feature

### Changed

- Added `id` field to the Symbol model

## [0.1.0] - 2026-01-27

Initial release. MVP version supporting both Python and Java.

### Added

- **CLI command**: Implemented `code2map build` command
  - `--out`: Specify the output directory
  - `--lang`: Explicitly specify the language (auto-detected from extension if omitted)
  - `--verbose`: Output detailed logs
  - `--dry-run`: Display the plan only without generating files

- **Python parser**: Analysis using the `ast` module
  - Supports extraction of classes, methods, and functions
  - Supports docstring extraction
  - Supports call relationship inference
  - Supports import information collection

- **Java parser**: Analysis using the `javalang` library
  - Supports extraction of classes, methods, and fields
  - Supports Javadoc extraction
  - Supports call relationship inference
  - Supports nested classes, constructors, and overloads

- **INDEX.md generation**: Markdown index with class/method/function list and roles
  - Display of call relationships (Calls)
  - Detection and description of side effects (Side Effects)
  - Embedding of warnings (`[WARNING]`)

- **parts/ generation**: Split source code by class/method units
  - Metadata header attachment
  - Language-specific comment prefix support
  - Hash suffix for collision avoidance

- **MAP.json generation**: Machine-readable mapping table (JSON format)
  - Complete mapping of symbol information
  - SHA-256 checksum calculation

- **Tests**: Unit tests, e2e tests, and edge case tests

- **CI/CD**: Automated testing via GitHub Actions (Python 3.9–3.12)

### Known Limitations

This version has the following limitations:

- Single file only (directory-level analysis not yet supported)
- Static analysis only (dynamic dispatch and reflection are not considered)
- Class/method-level splitting only (processing phase-level splitting not supported)
- Supported languages: Java and Python only

## Links

- [Repository](https://github.com/elvezjp/code2map)
- [Issue Tracker](https://github.com/elvezjp/code2map/issues)

[0.2.0]: https://github.com/elvezjp/code2map/compare/v0.1.3...v0.2.0
[0.1.3]: https://github.com/elvezjp/code2map/compare/v0.1.2...v0.1.3
[0.1.2]: https://github.com/elvezjp/code2map/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/elvezjp/code2map/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/elvezjp/code2map/releases/tag/v0.1.0
