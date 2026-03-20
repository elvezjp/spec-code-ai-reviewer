# Changelog

[English](./CHANGELOG.md) | [日本語](./CHANGELOG_ja.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.1] - 2026-03-20

Added heading list retrieval and per-section split setting overrides. You can now apply different split settings (split_mode, max_subsections, etc.) to specific sections individually.

### Added

- **Heading list retrieval**: Added `headings` subcommand / `MarkdownParser.extract_headings()` method
  - Lightweight heading list retrieval before splitting (no LLM required, fast processing)
  - JSON output with `title`, `level`, `start_line`, `end_line`, `estimated_chars`
  - Uses the same code path as the `build` command, guaranteeing `start_line` consistency

- **Per-section overrides**: Added `--section-overrides` CLI option / `section_overrides` parameter
  - Identify sections by `start_line` and override `split_mode`, `split_threshold`, `max_subsections`, `ai_prompt_extra_notes` individually
  - Specify as a JSON file path or inline JSON string
  - Unspecified fields inherit from constructor arguments (CLI options)

- **Lazy initialization**: Added lazy initialization for LLM provider / NLP tokenizer
  - Auto-initializes when `ai` / `nlp` mode is needed via overrides, even if default is `heading` mode

- **Sample output**: Added heading / nlp / ai mode output examples and `headings.json` to `docs/examples/v0.3.1/`

- **Examples README**: Added regeneration commands for each version to `docs/examples/README.md`

### Changed

- **_refine_sections()**: Changed to resolve settings per section before performing splits
- **_build_ai_system_prompt()**: Added support for per-section `ai_prompt_extra_notes` overrides
- **Specification**: Added `headings` command spec, `--section-overrides` option, settings resolution flow, and lazy initialization

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.3.0] - 2026-03-11

Added AI subsplit prompt customization. Redesigned prompt structure into 4-part composition and enabled appending to the notes section. Also changed subsplit naming from LLM-generated titles to static `part-N` format for improved stability.

### Added

- **AI prompt customization**: Added `--ai-prompt-extra-notes` CLI option / `ai_prompt_extra_notes` parameter
  - Append user-specified text to the AI subsplit system prompt `notes` section
  - Flexibly specify domain-specific split rules (e.g., "Do not split in the middle of Mermaid blocks")

### Changed

- **AI prompt structure**: Redesigned hardcoded prompt into 4-part dictionary `DEFAULT_AI_PROMPT_PARTS` (`role` / `purpose` / `format` / `notes`)
  - `role`, `purpose`, `format` are tightly coupled with core functionality and not externally modifiable
  - Only `notes` section allows appending
- **Subsplit naming**: Changed from `<section name>: <LLM-generated title>` to `<section name>: part-N`
  - LLM no longer generates titles; focuses solely on determining split positions
  - Removed `title` field from LLM response, simplified to `start_line` / `end_line` only
- **User message**: Changed to include total line count (`total_lines`) in the prompt

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.2.0] - 2026-02-19

Added multi-stage splitting and multi-LLM provider support. In addition to heading-based splitting, semantic re-splitting via NLP (morphological analysis) or AI (LLM) is now available.

### Added

- **Multi-stage splitting**: Added re-splitting for long sections on top of heading-based splitting
  - `--split-mode heading`: Conventional heading-based splitting (default)
  - `--split-mode nlp`: Semantic splitting via morphological analysis (SudachiPy)
  - `--split-mode ai`: Semantic splitting via LLM
  - `--split-threshold`: Specify minimum character/word count for re-splitting (default: 500)
  - `--max-subsections`: Specify maximum number of subsections per section (default: 5)

- **Multi-LLM provider**: Multiple LLM providers selectable in AI mode
  - `--ai-provider openai`: OpenAI API (default model: `gpt-4o-mini`)
  - `--ai-provider anthropic`: Anthropic API (default model: `claude-haiku-4-5-20251001`)
  - `--ai-provider bedrock`: Amazon Bedrock (default, default model: `global.anthropic.claude-haiku-4-5-20251001-v1:0`)
  - `--ai-model`: Explicitly specify model ID
  - `--ai-region`: Specify Bedrock region

- **LLM provider abstraction layer**: Added `md2map/llm/` module
  - `BaseLLMProvider`: Common provider interface
  - `OpenAIProvider` / `AnthropicProvider` / `BedrockProvider`: Provider implementations
  - `LLMConfig`: Provider configuration dataclass
  - Factory pattern for provider creation

- **add-line-numbers**: Integrated line numbering utility as a subtree

- **Tests**: Added unit tests for LLM providers (`tests/test_llm.py`)

- **Documentation**: Reorganized sample output to `docs/examples/v0.1/` and `docs/examples/v0.2/`, added output examples for heading / nlp / ai modes

### Changed

- **INDEX.md generation**: Added support for subsection (re-split section) display
- **MAP.json generation**: Added subsection information output
- **parts/ generation**: Added subsection file generation
- **Specification**: Added NLP mode and AI mode specifications

### Known Limitations

This version has the following limitations:

- NLP mode requires SudachiPy installation
- AI mode requires API keys or AWS credentials for each provider
- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)

## [0.1.0] - 2026-02-06

Initial release. MVP version that transforms Markdown documents into semantic maps.

### Added

- **CLI command**: Implemented `md2map build` command
  - `--out`: Specify output directory (default: `./md2map-out`)
  - `--max-depth`: Specify maximum heading depth to process (1-6, default: 3)
  - `--id-prefix`: Specify section ID prefix (default: `MD`)
  - `--verbose`: Enable detailed log output
  - `--dry-run`: Preview plan without generating files

- **Markdown parser**: Heading-based document splitting
  - ATX-style heading (`#`, `##`, `###`, etc.) parsing support
  - Correctly skips headings inside code blocks
  - Japanese document character counting support

- **INDEX.md generation**: Markdown index for document structure visualization
  - Auto-generated structure tree
  - Section details (path, line numbers, summary, keywords, ID)

- **parts/ generation**: Split documents into section-level parts
  - Metadata header (original file, line numbers, section info)
  - Hierarchical splitting based on heading levels

- **MAP.json generation**: Machine-readable mapping (JSON format)
  - Complete section information mapping
  - Line number correspondence with original file
  - SHA-256 checksum calculation

- **Tests**: Unit tests, e2e tests, and edge case tests

- **CI/CD**: Automated testing via GitHub Actions (Python 3.9-3.12)

### Known Limitations

This version has the following limitations:

- Single file processing only (directory-level analysis not supported)
- ATX-style headings only (Setext-style underline headings not supported)
- Internal link auto-correction not supported (detection only)

## Links

- [Repository](https://github.com/elvezjp/md2map)
- [Issue Tracker](https://github.com/elvezjp/md2map/issues)
