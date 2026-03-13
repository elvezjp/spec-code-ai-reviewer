# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.1] - 2026-03-13

### Added
- **Group review results in ZIP** (#60): Include individual group review results as `split/review-result-{groupId}.md` in ZIP downloads during split review. Added file list to the download contents table on the results screen
- **AI sub-split instructions** (#55): Added a "Notes for splitting (instructions for AI, optional)" text area for AI-mode splitting. Input content is appended to the `# Notes` section of the md2map AI sub-split prompt
- **Section exclusion** (#54): Added "Exclude" checkboxes to the design document parts list in split preview. Excluded sections are omitted from structure matching and group review. Enabling exclusion automatically unchecks "Important" and "Summary". Added "Show content" accordion to each part for easier exclusion decisions

### Fixed
- **Split preview error display** (#52): Fixed error messages disappearing as toasts. Changed to persistent display directly below the split preview button
- **Code split warning display** (#52): Display warning reasons (parse warnings) in the UI when code split results are empty
- **Prevent review execution on split failure** (#53): Disable the review execution button when `codeParts`/`documentParts` are empty
- **Backend validation** (#53): Return an error from the structure matching API when code symbols are empty
- **Structure matching error details** (#53): Display detailed error messages on structure matching errors
- **Split review integration output structure** (#59): Improved the issue where integration results were organized by group name instead of design document chapter/item names. Added explicit column definitions to preset format, restructured integration phase prompt as "final report creation from drafts", and added instructions for using design document item names in group review prompts

### Changed
- **Configuration file updates**: Set v0.9.1 as the latest version
  - `nginx/version-map.conf`: Added v0.9.1 routing, changed default port to 8091
  - `docker-compose.yml`: Added v0.9.1 frontend, port 8091
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.9.1 entry

## [0.9.0] - 2026-02-28

### Added
- **Split review quality improvements** (#48):
  - Simplified structure matching output_format to string arrays of IDs only and added input summary
  - Added "Important" checkbox to split preview, making selected sections shared across all groups
  - Passed full structure information (INDEX.md / MAP.json) to group review and integration review to prevent false positives for unimplemented features
  - Enabled control of NLP/AI mode sub-split limits via `MD2MAP_MAX_SUBSECTIONS` environment variable
  - Auto-skip review for groups with no corresponding design document or code
- **Summarize API separation** (#50): Separated summarization into an independent endpoint `/api/summarize`
- **Pre-summarization** (#50): Pre-summarize design document parts in split preview to reduce token consumption
- **Retry settings panel** (#50): Retry settings UI for batch review and integration review errors

### Fixed
- **Group display fix**: Fixed empty section/symbol names in structure matching results (#48)
- **Display text fix**: Changed display for groups with no correspondence from "(no split)" to "(no match)" (#48)
- **Error display improvement**: Improved error messages during batch review and Markdown organization (#50)
- **Retry display condition fix**: Fixed retry button display conditions (#50)
- **Summary settings fix**: Fixed summary settings on error (#50)

### Changed
- **Configuration file updates**: Set v0.9.0 as the latest version
  - `nginx/version-map.conf`: Added v0.9.0 routing, changed default port to 8090
  - `docker-compose.yml`: Added v0.9.0 frontend, port 8090
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.9.0 entry


## [0.8.2] - 2026-02-24

### Fixed
- **Line number hallucination fix**: Added line number reference method to notes (#43)
- **Line number hallucination fix**: Appended total line count of code files to user prompt (#43)

### Added
- **Review mode display**: Added review mode (batch/split) to review results (#44)
- **Group assignment output**: Output group assignment results to README during split review (#44)
- **md2map mode selection**: Enabled selection from 3 design document splitting modes: heading / NLP / AI (#47)
  - NLP: Semantic splitting using morphological analysis (no LLM required)
  - AI: High-accuracy semantic splitting using LLM (LLM configuration required)

### Changed
- **Configuration file updates**: Set v0.8.2 as the latest version
  - `nginx/version-map.conf`: Added v0.8.2 routing, changed default port to 8082
  - `docker-compose.yml`: Added v0.8.2 frontend, port 8082
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.8.2 entry


## [0.8.1] - 2026-02-13

### Changed
- **Split review mode consolidation**: Changed from separate batch/split selection for design documents and code to a single batch/split selection, simplifying UI operation
- **Configuration file updates**: Set v0.8.1 as the latest version
  - `nginx/version-map.conf`: Added v0.8.1 routing, changed default port to 8081
  - `docker-compose.yml`: Added v0.8.1 frontend, port 8081
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.8.1 entry


## [0.8.0] - 2026-02-06

### Added
- **Semantic split review**: Split and review large files in semantically meaningful units using md2map/code2map
- **Split APIs**: `/api/split/markdown` (split by heading level), `/api/split/code` (split by class/function)
- **Split review APIs**: 3-phase APIs for structure matching, group review, and result integration
- **Split settings UI**: Batch/split mode selection, heading level settings, preview functionality
- **Split review execution screen**: 3-phase progress display, per-group retry/skip on error
- **Supported languages**: Python (.py) / Java (.java) code splitting
- **Token count display**: Added breakdown display
- **md2map/code2map subtree**: Integrated tools for converting Markdown and source code to mind map format

### Changed
- **Configuration file updates**: Set v0.8.0 as the latest version
  - `nginx/version-map.conf`: Added v0.8.0 routing, changed default port to 8080
  - `docker-compose.yml`: Added v0.8.0 frontend, port 8080
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.8.0 entry

### Note
- **Backward compatibility**: Versions prior to v0.7.0 remain available (multi-version architecture maintained)

## [0.7.0] - 2026-01-26

### Added
- **AI Markdown organization**: Added functionality to structure and normalize AI-generated Markdown from Excel
  - "Organize Markdown with AI" button and policy input field
  - Organization policy input UI with templates
  - Before/after diff display using react-diff-viewer
- **Error/warning display**: Alert display for token overflow, timeout, tampering detection, etc.
- **Tool-specific preprocessing**: Added preprocessing methods to markdown_tools to address tool-specific description confusion
- **Estimated token count display**: Display estimated token count before organization execution
- **organize-markdown API**: Added endpoint for per-file Markdown organization
- **Preset library**: Added preset library for prompts and design document types

### Changed
- **excel2md v2.0 support**: Updated git subtree to support v2.0
- **Configuration file updates**: Set v0.7.0 as the latest version
  - `nginx/version-map.conf`: Added v0.7.0 routing, changed default port to 8070
  - `docker-compose.yml`: Added v0.7.0 frontend, port 8070
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.7.0 entry

### Note
- **Backward compatibility**: Versions prior to v0.6.0 remain available (multi-version architecture maintained)

## [0.6.0] - 2026-01-18

### Added
- **React + Vite + TypeScript migration**: Complete frontend overhaul from single HTML file to modern SPA architecture
  - Component-based development with React 19.2.0 + TypeScript 5.9
  - Fast build environment with Vite 7.2.4
  - Routing with React Router v7 (`/` and `/config-file-generator`)
- **Tailwind CSS v4 support**: Optimized CSS generation with `@tailwindcss/vite` integration
- **Test environment**: Unit tests with Vitest + React Testing Library (8 files, 20+ test cases)
  - Core Hooks: useSettings, useModal, useScreenManager, useTokenEstimation
  - Feature Hooks: useFileConversion, useZipExport, useConfigState, useValidation
- **Component design**: Reusable UI component library
  - core/components/ui: Basic UI components such as Button, Modal, Table, Card
  - core/components/shared: Shared functionality such as SettingsModal, VersionSelector
- **React Hooks state management**: Comprehensive Hooks implementation including localStorage integration, modal control, and screen state management
- **lucide-react**: Unified emojis to lucide-react icons for UI consistency

### Changed
- **Frontend startup method**: Separated from backend (development: Vite dev server port 5173, production: built file serving)
- **Project structure**: Feature-based modules (reviewer, config-file-generator) under features/
- **Type safety improvement**: Applied TypeScript type definitions to all components and Hooks
- **Configuration file updates**: Set v0.6.0 as the latest version
  - `nginx/version-map.conf`: Added v0.6.0 routing, changed default port to 8060
  - `docker-compose.yml`: Added v0.6.0 frontend, port 8060
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.6.0 entry

### Note
- **Backward compatibility**: Versions prior to v0.5.2 remain available (multi-version architecture maintained)
- **Startup method change**: From v0.6.0 onward, frontend and backend must be started separately (see README for details)

## [0.5.2] - 2026-01-13

### Added
- **Bedrock Converse API support**: Migrated from `invoke_model` to `converse`, supporting both Anthropic Claude and Amazon Nova models
- **Amazon Nova model support**: Nova Pro, Nova Micro, and other models now available
- **Unified provider design**: Added `get_system_llm_config()` function, centralizing system LLM configuration generation in `llm_service.py`
- **Config file generator improvement**: Display region prefix and token limit notes when Bedrock is selected

### Changed
- **Configuration file updates**: Set v0.5.2 as the latest version
  - `nginx/version-map.conf`: Added v0.5.2 routing, changed default port to 8052
  - `docker-compose.yml`: Added v0.5.2 frontend, port 8052
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.5.2 entry

## [0.5.1] - 2026-01-09

### Added
- **OpenAI GPT-5.2 support**: Added support for `max_completion_tokens` parameter required by GPT-5.2 models
- **Config file generator update**: Added GPT-5.2 models to OpenAI model selection

### Changed
- **OpenAI SDK update**: Raised dependency version to `openai>=2.14.0`
- **Configuration file updates**: Set v0.5.1 as the latest version
  - `nginx/version-map.conf`: Added v0.5.1 routing, changed default port to 8051
  - `docker-compose.yml`: Added v0.5.1 frontend, port 8051
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.5.1 entry
  - `docs/ec2-deployment-spec.md`: Updated port table and VERSIONS array

### Fixed
- Fixed issue where `max_tokens` parameter could not be used with OpenAI GPT-5.2 (Issue #5)

## [0.5.0] - 2025-12-28

### Added
- **Multiple review execution**: Execute 2 reviews sequentially with a single button press, displaying results with tab switching
- **Review data package download**: Save all input/output data (system prompt, design document MD, code, results) as a ZIP file
- **Unified download filenames**: Fixed filenames to `spec-markdown.md` and `code-numbered.txt`

### Changed
- Backward compatibility with v0.4.0 maintained

## [0.4.0] - 2025-12-23

### Added
- **Multi-LLM provider support**: Switch between Bedrock / Anthropic / OpenAI for review execution (falls back to Bedrock when not specified)
- **Configuration file**: Manage LLM settings (provider, authentication, model list) and types in Markdown via `reviewer-config.md`
- **Settings modal overhaul**: Migrated to configuration file upload, model selection persistence/save/clear, connection test (`/api/health`)
- **Backend extensions**: Added `llm_service` (abstraction) and `anthropic_service` / `openai_service`
- **excel2md extension**: Added CSV+Mermaid format support (append flowcharts in Mermaid notation)

### Changed
- Backward compatibility with v0.3.0 maintained

## [0.3.0] - 2025-12-21

### Added
- **Multi-conversion tool support**: Select MarkItDown (standard Markdown conversion) or excel2md (entire sheet to CSV block conversion) per file
- **Version switcher**: Switch to previous versions via pill-shaped button in top-left UI
- **Report enhancements**: Summary judgment section (red/yellow/green) display, token information display
- **Backend structure improvement**: Introduced `markdown_tools` package, refactored conversion tools into a plugin-style extensible architecture
- **Batch settings**: Enabled batch tool changes across all files

### Changed
- Backward compatibility with v0.2.5 maintained

## [0.2.5] - 2025-12-19

### Added
- **Priority and type settings**: Enabled priority settings for main design documents/reference materials
- **UI improvements**: Added per-file dropdown menus
- **Token count display**: Display estimated token counts

### Changed
- Conversion tool fixed to MarkItDown

## [0.1.1] - 2025-12-15

### Added
- **Initial release (MVP)**: Implemented basic file conversion and review functionality
- Simple file selection to conversion UI
- Excel to Markdown conversion (using MarkItDown)
- Source code line numbering (add-line-numbers compatible)
- Review execution via AWS Bedrock (Claude)
- Review report copy and download

---

## Links

- [Repository](https://github.com/elvezjp/spec-code-ai-reviewer)
- [Issues](https://github.com/elvezjp/spec-code-ai-reviewer/issues)

---

## Version Comparison

| Version | Key Features |
|---------|-------------|
| 0.9.1   | Section exclusion, AI sub-split instructions, split preview error display, code split warnings, prevent review on split failure |
| 0.9.0   | Split review quality improvements, pre-summarization, summarize API separation, error display improvements |
| 0.8.2   | Line number hallucination fix, review mode display, md2map 3 modes |
| 0.8.1   | Split review mode consolidation (single batch/split selection) |
| 0.8.0   | Semantic split review, md2map/code2map integration, token breakdown display |
| 0.7.0   | AI Markdown organization, diff display, tool-specific preprocessing, preset library |
| 0.6.0   | React + Vite + TypeScript migration, Tailwind v4, test environment |
| 0.5.2   | Bedrock Converse API support, Amazon Nova model support |
| 0.5.1   | OpenAI GPT-5.2 support |
| 0.5.0   | Multiple review execution, data package download |
| 0.4.0   | Multi-LLM provider, configuration file |
| 0.3.0   | Multi-conversion tool, version switching |
| 0.2.5   | Priority/type settings, token count display |
| 0.1.1   | Initial release (MVP) |
