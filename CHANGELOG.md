# Changelog

[English](./CHANGELOG.md) | [日本語](./CHANGELOG_ja.md)

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.10.0] - Unreleased

### Added
- **Base URL support for OpenAI-compatible APIs (Kimi / Moonshot AI, etc.)** (#123): The config file generator's `openai` provider now has an optional "Base URL" field, passed through the config file to the backend as part of `llmConfig`. When set, the OpenAI client connects to the specified endpoint (e.g. `https://api.moonshot.ai/v1`) and sends `max_tokens` instead of `max_completion_tokens` for compatibility. When left empty, behavior is unchanged (official OpenAI API)
- **Reasoning effort setting for reasoning models** (#128): The config file generator's `openai` provider now has an optional "Reasoning Effort" field; `reasoning_effort` is sent to the API only when specified (applies to bulk/split reviews, Markdown organizing, the connection test, and the split preview's AI summary generation / AI split via md2map). Allowed values are model-dependent and passed through without validation. With Kimi K3, setting `low` cuts review time to roughly a quarter (measurements: `docs/20260722-kimi-k3-reasoning-effort-benchmark.md`). When unset, the parameter is not sent and behavior is unchanged

### Changed
- **Parallelized the split preview's AI calls** (#129): Per-section AI calls in the split preview (AI summary generation / AI split) now run in parallel to reduce response time. Enables md2map's concurrency feature with a fixed level of 4 (constant `AI_CONCURRENCY`); the effective concurrency is `min(4, number of sections)`
- **Trimmed the config file generator's default OpenAI models** (#128): Now `gpt-5.2` / `gpt-5.2-pro` only (removed `gpt-5.2-chat-latest`, `gpt-5.1`, `gpt-4o`, and `gpt-4o-mini`)
- **Repository restructured to keep only the latest code at the root** (#103): The `versions/` directory (v0.5.0–v0.9.9 snapshots) has been removed; `versions/v0.9.9/backend` and `versions/v0.9.9/frontend` were promoted to `backend/` and `frontend/` at the repository root. Version management now uses git tags — to use the old multi-version layout, check out the `v0.9.9` tag
- **excel2md is now installed from PyPI** (#100): Replaced the `sys.path` injection of the local `excel2md/` directory with a normal dependency (`excel2md>=2.2.1`) and direct imports of `excel2md.cli` / `excel2md.runner`
- `spec.md` and `config-file-generator-spec.md` moved to `docs/`

### Removed
- **Runtime version switching** (#118): The version-selector balloon UI (`VersionSelector` / `useVersions`), the `app_version` cookie, and the Cookie + Nginx map routing have been removed. The settings modal still shows the running version
- **Multi-version infrastructure** (#118): `nginx/` (including `version-map.conf`), `docker-compose.yml`, `Dockerfile.dev`, `docker-entrypoint.sh`, `ecosystem.config.js`, and `dev.ecosystem.config.js`. The app now starts as a single version via uvicorn + Vite
- **Unused subtree directories** (#96, #100, #103): `markitdown/`, `excel2md/`, `add-line-numbers/`, `code2map/`, and `md2map/` — all are consumed from PyPI or git sources via uv. Clone the upstream repositories if you need the sources for reference
- `latest` symlink and `scripts/sync_version.py` (no longer needed with a single version at the root)

### Fixed
- **Config-file Base URL / Max Tokens were not propagated to the split preview's AI summary generation** (#127): The md2map conversion dropped `baseUrl`, so requests went to the official OpenAI API with an OpenAI-compatible API key and failed with 401. Also replaced the hard-coded `max_tokens=800` with the config file's `maxTokens`, fixing empty responses (`OpenAI API returned empty response`) from thinking models (kimi-k3, etc.) whose reasoning tokens consumed the limit. md2map updated to the base_url-capable version (v0.5.0)

## [0.9.9] - 2026-06-17

### Changed
- **Minimum Python raised to 3.11** (#104): `add-line-numbers`, `md2map`, and `code2map` upstream `main` now require Python `>=3.11`, so `requires-python` is bumped to `>=3.11`
  - `versions/v0.9.9/backend/pyproject.toml`: `requires-python = ">=3.11"`
  - `.github/workflows/ci.yml`: Python matrix changed from `["3.10", "3.13"]` to `["3.11", "3.13"]`
- **Configuration file updates**: Set v0.9.9 as the latest version
  - `nginx/version-map.conf`: Added v0.9.9 routing, changed default port to 8099
  - `latest` symlink retargeted to `versions/v0.9.9`

### Fixed
- **Resolved test-mock type errors surfaced by `tsc -b`**: Test mocks had fallen behind the latest production type definitions, causing `npm run build` (`tsc -b`) to fail with type errors (a gap in the test mocks, not a product bug)
  - `SplitSettingsSection.test.tsx`: Added required props `hasAnyPendingSummarize` / `onExecuteAllSummarize` to `defaultProps`, and added the required `documentWarnings` to `makePreviewResult`, also resolving `TS2322`
  - `split_api.test.ts`: Added the required `maxTokens` to the `LlmConfig` mock

### Security
- **[SECURITY] Bumped `starlette` from 1.0.1 to 1.3.1** to resolve Dependabot alerts [#911](https://github.com/elvezjp/spec-code-ai-reviewer/security/dependabot/911) / [#912](https://github.com/elvezjp/spec-code-ai-reviewer/security/dependabot/912) / [#913](https://github.com/elvezjp/spec-code-ai-reviewer/security/dependabot/913) / [#914](https://github.com/elvezjp/spec-code-ai-reviewer/security/dependabot/914) (`starlette < 1.3.1` and related). Also regenerated `uv.lock`.
- **Dependabot alert #502 resolved** (GHSA-65pc-fj4g-8rjx): Regenerated `uv.lock` to pick up `idna >= 3.16`

## [0.9.8] - 2026-05-11

### Changed
- **excel2md subtree updated to v2.1.1** (#101): Pulled upstream `elvezjp/excel2md` `main` (commit `c853eb2`, v2.1.1) into the `excel2md/` subtree
  - `versions/v0.9.8/backend/app/markdown_tools/excel2md_tool.py`: switched `_DEFAULT_EXCEL2MD_PATH` from `excel2md/v2.0` to `excel2md/v2.1.1`
  - Brings the following upstream fixes (v2.0 → v2.1.1):
    - Restored v1.x backward-compatible re-exports of `is_code_block` / `build_code_block_from_rows` (excel2md #15)
    - Fixed `extract_table()` truncation path tuple arity inconsistency (excel2md #24)
    - Fixed duplicated footnote numbering across multiple tables (excel2md #25)
    - Fixed sheet-scope footnote definitions being dropped in non-`split-by-sheet` mode
    - Fixed missing `is_code_block` import in `mermaid_generator.py` (excel2md #13)
  - Brings the following upstream dependency / Python requirement updates:
    - Minimum Python raised to 3.10 (already satisfied by this project)
    - pytest 9.0.3 (CVE-2025-71176) / Pygments 2.20.0 (CVE-2026-4539)
- **Configuration file updates**: Set v0.9.8 as the latest version
  - `nginx/version-map.conf`: Added v0.9.8 routing, changed default port to 8098

## [0.9.7] - 2026-04-07

### Added
- **Word (.docx) file support** (#95, Issue #26): Added Word (.docx) as a supported design document input format in addition to Excel
  - Added new `POST /api/convert/word-to-markdown` endpoint
  - `.docx` files are converted using MarkItDown (tool is fixed; excel2md does not support Word)
  - Added `.docx` to the frontend file selector, enabling Word documents to be converted and reviewed
  - Tool selector for `.docx` rows is disabled, showing "WordはMarkItDownのみ対応" (Word supports MarkItDown only)
  - Bulk tool change (`applyToolToAll`) preserves MarkItDown for `.docx` files
- **Backend dependency update**: Changed to `markitdown[xlsx,docx]`

### Changed
- **Service function rename**: Renamed `convert_excel_to_markdown` to `convert_to_markdown` in `markitdown_service.py` to handle both Excel and Word uniformly (added `.docx` to `SUPPORTED_EXTENSIONS`)
- **Configuration file updates**: Set v0.9.7 as the latest version
  - `nginx/version-map.conf`: Added v0.9.7 routing, changed default port to 8097

## [0.9.6] - 2026-03-28

### Added
- **Code part exclude, important designation, and summarize features** (#90): Added exclude, important designation, and summarize functionality to code parts in split review, equivalent to design document parts
  - Added "Important", "Summarize", and "Exclude" checkboxes to code parts table
  - Exclude large class symbols (20,000+ lines) from review and review at method level instead
  - Pre-summarize code parts using `targetType: "code"` to reduce token consumption
  - Inject important-designated code symbols into all groups
  - Added content preview and summarized text preview to code parts table
  - Unified design document and code summarize execution buttons into a single button at the bottom of preview results (executes design → code sequentially)
- **Integration retry group skip feature** (#93): Added "Skip" option to integration retry settings. When token limit is exceeded with many groups, skip less important groups to efficiently reduce token consumption without summarizing every group
  - Added "Original / Summarize / Skip" radio buttons to retry settings panel
  - Skipped groups shown with greyed-out styling, all-skip prevention with warning message
  - Skipped groups' review results are still included in ZIP downloads

### Fixed
- **Design document part defensive filter**: Added `!p.excluded` filter to `executeSummarize` / `hasPendingSummarize` to resolve inconsistency with code parts
- **Preview clear summarize error state**: Fixed `clearPreview` not clearing `summarizeError` / `codeSummarizeError`
- **Estimated review count excludes excluded parts**: Fixed `estimatedReviewCount` to exclude excluded parts from count
- **Retry settings summarize preview left-align**: Fixed summarized text being center-aligned in retry settings panel during split review execution
- **Code parts table horizontal scroll fix**: Inlined symbol type into symbol name column and used `table-fixed` to prevent horizontal scrolling
- **Integration retry button not enabling after summarization** (#92): Fixed retry button remaining disabled after all group summarizations complete. The pending check was referencing stale props instead of local summarization results

### Changed
- **md2map update**: Updated subtree to latest
- **Configuration file updates**: Set v0.9.6 as the latest version
  - `nginx/version-map.conf`: Added v0.9.6 routing, changed default port to 8096
  - `docker-compose.yml`: Added v0.9.6 frontend, port 8096
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.9.6 entry

## [0.9.5] - 2026-03-26

### Added
- **Frontend-backend version mismatch detection** (#81): Check backend version on startup and display a warning banner if it doesn't match the frontend version
  - Added `GET /api/health` endpoint (shared logic with existing `GET /health`)
  - Also warns when older backends don't support `/api/health` (404/405)

### Fixed
- **AI split preview silent fallback fix** (#84): Fixed issue where split preview returned results without error even when LLM credentials were invalid
  - Added `warnings` field to `SplitMarkdownResponse` to propagate md2map `parse()` warnings to the frontend
  - Added document split warning panel (same UI format as code split warnings)
  - Simplified `llmConfig` to always be sent to the `splitMarkdown` API regardless of split mode
- **Split mode source mismatch fix** (#86): Fixed issue where UI split mode selection was not reflected in API requests when no pre-important sections were selected
  - Unified `splitMode` / `maxDepth` / `aiPromptExtraNotes` source to always use `normalSplitSettings`
- **HTTP response check for all API functions** (#79): Added `response.ok` check to all API functions including `fetchHeadings()`, ensuring non-2xx responses (405, 500, etc.) are properly detected
  - Fixed a bug where the pre-important panel was not displayed when the backend was an older version (e.g., v0.9.1) that returned 405 for `POST /api/split/headings`
  - Introduced `assertResponseOk()` helper function and applied uniform non-2xx response error handling to all 12 API functions
  - Added `result.error` check to `useSplitSettings.ts` error detection for robustness

## [0.9.4] - 2026-03-26

### Added
- **Summary mode options** (#71): Added `summaryMode` (`text`/`ai`) and `summaryMaxChars` parameters to split preview settings for controlling INDEX.md summary generation
  - `summaryMode`: Choose between rule-based (`text`) and LLM-based (`ai`, default) summary generation
  - `summaryMaxChars`: Control maximum summary character count (default: 100 for normal sections, 300 for pre-important sections)
  - Summary settings can be configured independently for pre-important and normal sections
  - Summary mode auto-syncs with split mode: AI split → AI summary, heading/NLP split → rule-based summary (manual override allowed)
- **Max subsections UI control**: Promoted `maxSubsections` from environment variable to frontend UI input
  - Number input shown for NLP/AI split modes (hidden for heading mode)
  - Default value: 5 (backward compatible)
- **MAP.json / INDEX.md download from split preview** (#73): Download design document and code MAP.json / INDEX.md individually from the split preview screen before starting review
  - Added `spec-INDEX.md` / `spec-MAP.json` download buttons to design document parts heading
  - Added `code-INDEX.md` / `code-MAP.json` download buttons to code parts heading
- **Split preview re-run** (#76): After preview execution, the button changes to "Re-run preview", enabling one-click result clear and re-execution
  - Re-preview after settings change completes in a single click
  - Displays completion message next to the button ("✓ Split preview complete: Please re-run if you changed settings.")

### Removed
- **`MD2MAP_MAX_SUBSECTIONS` environment variable**: Replaced by frontend UI control. The parameter is now sent directly from the frontend request

### Changed
- **Configuration file updates**: Set v0.9.4 as the latest version
  - `nginx/version-map.conf`: Added v0.9.4 routing, changed default port to 8094
  - `docker-compose.yml`: Added v0.9.4 frontend, port 8094
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.9.4 entry

## [0.9.3] - 2026-03-24

### Added
- **Pre-split exclusion designation** (#68): Designate sections as "pre-excluded" before splitting, completely removing unnecessary sections (changelogs, table of contents, etc.) from split processing
  - Added `preExcludedSections` parameter to `POST /api/split/markdown`
  - Pre-excluded sections are completely removed from `parse()` results via md2map's `skip` feature and do not appear in split preview results
  - Mutual exclusion control between pre-important and pre-excluded designations (cannot check both on the same section)
  - Reduces processing time, LLM API calls, and token consumption

### Changed
- **md2map update**: Updated to v0.3.2 (added `skip` option to `section_overrides`)
- **Pre-designation panel rename**: Renamed "Pre-important designation" panel to "Pre-designation", integrating both pre-important and pre-exclusion features
- **Configuration file updates**: Set v0.9.3 as the latest version
  - `nginx/version-map.conf`: Added v0.9.3 routing, changed default port to 8093
  - `docker-compose.yml`: Added v0.9.3 frontend, port 8093
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.9.3 entry

## [0.9.2] - 2026-03-20

### Added
- **Pre-split importance designation** (#66): Designate sections as "pre-important" before splitting, allowing different split settings (split mode, heading level, AI instructions) for pre-important vs. normal sections
  - Added `POST /api/split/headings` endpoint (H2 heading list retrieval)
  - Added `preImportantSections`, `preImportantSplitSettings`, `normalSplitSettings` parameters to `POST /api/split/markdown`
  - Non-subsplit parts from pre-important sections are automatically set as important (user can override)
  - Heading list is cached across batch/split mode toggles; reset on design markdown change
  - Uses md2map v0.3.1 `extract_headings()` / `section_overrides` features

### Fixed
- **Retry with summarized spec not working** (#66): Fixed issue where clicking the retry button during group review did not pass the selected doc/code mode (original/summarize) to the retry handler, causing retries to always use the original (unsummarized) content even when "要約" was selected

### Changed
- **md2map update**: Updated to v0.3.1 (heading list extraction, section-level override feature)
- **Configuration file updates**: Set v0.9.2 as the latest version
  - `nginx/version-map.conf`: Added v0.9.2 routing, changed default port to 8092
  - `docker-compose.yml`: Added v0.9.2 frontend, port 8092
  - `ecosystem.config.js`, `dev.ecosystem.config.js`: Added v0.9.2 entry

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

For a detailed feature comparison table across old versions (v0.5.0–v0.9.9), see [versions/README.md in the v0.9.9 tag](https://github.com/elvezjp/spec-code-ai-reviewer/blob/v0.9.9/versions/README.md).

| Version | Key Features |
|---------|-------------|
| 0.9.9   | Minimum Python raised to 3.11; pulled in `idna >= 3.16` (Dependabot #502) |
| 0.9.8   | excel2md subtree updated to v2.1.1 (re-exports / footnote / truncation fixes, Python 3.10+) |
| 0.9.7   | Word (.docx) file support, new `/api/convert/word-to-markdown` endpoint |
| 0.9.6   | Code part exclude/important/summarize features, unified summarize button, defensive filter and error state fixes |
| 0.9.5   | Frontend-backend version mismatch detection, HTTP response check for all API functions, AI split silent fallback fix, split mode source mismatch fix |
| 0.9.4   | Summary mode options (text/AI), max subsections UI control, MD2MAP_MAX_SUBSECTIONS env var removed, MAP.json/INDEX.md download from split preview, split preview re-run |
| 0.9.3   | Pre-split exclusion designation (completely exclude unnecessary sections from split processing) |
| 0.9.2   | Pre-split importance designation (per-section split settings) |
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
