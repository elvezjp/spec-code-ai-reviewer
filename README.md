# spec-code-ai-reviewer

[English](./README.md) | [日本語](./README_ja.md)

[![Elvez](https://img.shields.io/badge/Elvez-Product-3F61A7?style=flat-square)](https://elvez.co.jp/)
[![IXV Ecosystem](https://img.shields.io/badge/IXV-Ecosystem-3F61A7?style=flat-square)](https://elvez.co.jp/ixv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Stars](https://img.shields.io/github/stars/elvezjp/spec-code-ai-reviewer?style=social)](https://github.com/elvezjp/spec-code-ai-reviewer/stargazers)

A web application that uses AI to cross-check design documents (Excel / Word format) against program code and verify consistency.

https://github.com/user-attachments/assets/8c72f49b-35c5-43af-b1f2-29b6b6b71e30

## Features

- **Design document conversion**: Convert Excel (.xlsx, .xls) / Word (.docx) to Markdown (using MarkItDown, excel2md; Word supports MarkItDown only)
- **Program conversion**: Add line numbers to any text file (add-line-numbers compatible)
- **Cross-check review**: Verify consistency between the design doc and code using LLMs (Bedrock / Anthropic / OpenAI)
- **Split review**: Semantically split large design docs and code that exceed token limits for review (using md2map / code2map)
- **Report output**: Generate a Markdown review report

### Split Review for Large Files ([Details](docs/split-review.md))

LLMs have input token limits, so large design documents or source code with thousands of lines may not be reviewable as-is.
Naive line-based splitting can cut through sections, classes, or functions, losing context and reducing review accuracy.

This application splits Markdown-converted design documents and source code into semantically meaningful units, grouping related parts together for cross-check review.

**Design document / code splitting**:
- [md2map](https://github.com/elvezjp/md2map): Splits Markdown-converted design documents into section-level files and creates a JSON map.
- [code2map](https://github.com/elvezjp/code2map): Splits source code into class/function-level files and creates a JSON map.

**AI-powered split review** (executed in 3 steps):
1. **Structure matching**: AI analyzes the JSON maps of the design document and code, and groups highly related design document sections and code together.
2. **Group review**: For each group, AI performs a cross-check review by combining the split design document sections and code.
3. **Result integration**: AI integrates the review results from all groups and generates the final review report.

## System Architecture

- **Frontend**: Vite + React + TypeScript + Tailwind CSS
- **Backend**: Python / FastAPI
  - MarkItDown / excel2md (Excel to Markdown conversion)
  - add-line-numbers compatible (line numbering)
  - Multi-LLM provider support (Bedrock / Anthropic / OpenAI)

## Usage

Sample files (an Excel design document and Java code) for trying out the AI review are available in [docs/sample](docs/sample/). See [docs/sample/README.md](docs/sample/README.md) (Japanese) for usage and the list of seeded inconsistencies.

1. **Upload design documents**: Select Excel (.xlsx, .xls) or Word (.docx) files (multiple allowed)
   - **Role**: Select one main design document (others are treated as reference materials)
   - **Type**: Choose from 9 types such as design doc, requirements doc, coding guidelines, etc.
   - **Conversion tool**: Choose MarkItDown / excel2md (CSV) / excel2md (CSV+Mermaid)
2. **Click "Convert to Markdown"**: Converted Markdown is shown in preview
3. **Upload programs**: Select any source code files (multiple allowed)
4. **Click "Convert with add-line-numbers"**: Line numbers are added and shown in preview
5. **Click "Run Review"**: AI runs the review twice with the same settings
6. **Review results**: Switch tabs to view each run, then copy or download

### Switching LLM Providers and Credentials

By default, the system LLM (AWS Bedrock configured on the server side) is used. If you want to use your own LLM credentials, upload a configuration file using the steps below.

1. Open the settings modal from the "Settings" icon in the top-right
2. On the [Config File Generator](/config-file-generator/) page, select an LLM provider (Bedrock / Anthropic API / OpenAI API), enter the required API keys, and generate a configuration file
3. Return to the settings modal and upload the configuration file
4. Select the LLM models to use (multiple can be specified)

## Setup

### Prerequisites

#### Python Version

- **Required**: Python 3.11 or later
- **Recommended**: Python 3.11 or 3.13
- **How to check**: Run `python --version` or `python3 --version`

uv automatically uses an appropriate Python version. The installed Python 3.11+ on your system will be used as-is.

#### Node.js Version

- **Required**: Node.js 20 or later
- **Recommended**: Node.js 22 LTS
- **How to check**: Run `node --version`

Required for developing/building the frontend (Vite + React + TypeScript).

#### Other

- [uv](https://docs.astral.sh/uv/) (Python package manager)
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

### Installation

```bash
# Install uv (if not installed)
# See: https://docs.astral.sh/uv/getting-started/installation/

# Install Node.js (if not installed)
# See: https://nodejs.org/
# macOS (Homebrew): brew install node
# Windows: Download the installer from https://nodejs.org/

# Clone the repository
git clone git@github.com:elvezjp/spec-code-ai-reviewer.git
cd spec-code-ai-reviewer
```

### System LLM Auth Setup (AWS Bedrock)

**Note**: If you do not have an AWS environment, this setup is not required. You can upload your own LLM config file via the web UI (see the "[Usage](#usage)" section).

```bash
# Option 1: Environment variables
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
export AWS_REGION=ap-northeast-1

# Option 2: .env file
cp .env.example .env
# Edit .env to set AWS credentials

# Option 3: Configure with AWS CLI
aws configure
```

### Launch

Start frontend and backend separately.

**Terminal 1: Start backend**

```bash
cd backend
uv sync
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**Note**: `--host 127.0.0.1` is specified explicitly. This API is served without authentication, so binding to `0.0.0.0` lets anyone on the same network call every endpoint. Do not change it unless you intend to expose the service on a network.

**Terminal 2: Start frontend**

```bash
cd frontend
npm install
npm run dev
```

Access http://localhost:5173 (Vite dev server)

**Note**: The frontend runs on the Vite dev server (port 5173), and API requests are proxied to the backend (port 8000).

### Run Tests

```bash
# Backend tests
cd backend
uv run pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## Environment Variables

### System LLM (AWS Bedrock)

These environment variables are used to run the system LLM (AWS Bedrock).

**Note**: If you run with a config file uploaded from the web UI, that configuration takes precedence (see the "[Usage](#usage)" section).

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `AWS_REGION` | AWS region | `ap-northeast-1` |
| `BEDROCK_MODEL_ID` | Model ID to use | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `BEDROCK_MAX_TOKENS` | Max response tokens | `16384` |

### Local LLM connections

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_ALLOW_PRIVATE_BASE_URL` | Allow `baseUrl` to point at internal addresses (`127.0.0.1`, `192.168.x.x`, etc.) | `false` |

The OpenAI-compatible endpoint (`baseUrl`) rejects internal network
addresses by default. This API is served without authentication, so an
unvalidated `baseUrl` would let anyone use the server to reach internal
services or a cloud metadata endpoint.

**Set this variable when connecting to an LLM running locally:**

```bash
LLM_ALLOW_PRIVATE_BASE_URL=1
```

Do not enable it where untrusted callers can reach this API.

### CORS

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Comma-separated origins allowed to make cross-origin browser requests | Local development origins only |

When unset, only the Vite development server and preview origins are allowed
(`http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:4173`,
`http://127.0.0.1:4173`). This API is served without authentication, so the
allowed set directly determines who can reach it from a browser.

In production, name the origin that serves the frontend:

```bash
CORS_ORIGINS=https://example.com
```

`*` (allow all) is accepted, but credentials are then disabled. It lets any
site read the responses, so it is not recommended.

**Note**: a normal setup does not need this variable. In development the Vite
proxy forwards `/api` requests server-side, and in production the same FastAPI
app serves the frontend — in both cases the browser sees a single origin and no
CORS exchange takes place. Set it only when the frontend runs on a different
host.

---

## FAQ / Troubleshooting

### 1. I can register multiple LLM models. What is this used for?

By registering multiple models in the config file, you can select which model to use for review execution from the settings screen.

### 2. "Connection error." is shown when using OpenAI API

This error is often caused by network issues.

**Possible causes:**
- Unstable internet connection
- Proxy settings not configured in a proxy environment
- Firewall blocks API traffic to the LLM provider (e.g., `api.openai.com`)
- VPN connection issues

**How to fix:**
1. Check your internet connection
2. Check proxy settings
3. Confirm that the firewall allows outbound traffic to the LLM provider API

### 3. "on-demand throughput isn't supported." is shown when using Bedrock

```
ValidationException: Invocation of model ID amazon.nova-pro-v1:0 with on-demand throughput isn't supported.
Retry your request with the ID or ARN of an inference profile that contains this model.
```

**Cause:**
- Missing region prefix (`us.` or `apac.`)
- Incorrect model ID

**How to fix:**
- Check the Bedrock model ID
- Specify the cross-region inference "inference profile ID"
  - Example (error): `amazon.nova-pro-v1:0`
  - Example (correct): `us.amazon.nova-pro-v1:0` or `apac.amazon.nova-pro-v1:0`

### 4. "maximum tokens you requested exceeds the model limit" is shown when using Bedrock

```
The maximum tokens you requested exceeds the model limit of 10000.
Try again with a maximum tokens value that is lower than 10000.
```

**Cause:**
- `max_tokens` in the config file exceeds the model limit
  - Amazon Nova Lite / Micro / Pro: 10,000
  - Anthropic Claude Haiku 4.5: 16,384

**How to fix:**
- Regenerate the config file in the config file generator
- Set `max_tokens` to a value within the model limit

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Serve frontend |
| GET | `/api/health` | Health check |
| POST | `/api/convert/excel-to-markdown` | Excel to Markdown conversion |
| POST | `/api/convert/word-to-markdown` | Word to Markdown conversion |
| POST | `/api/convert/add-line-numbers` | Add line numbers |
| GET | `/api/convert/available-tools` | List available conversion tools |
| POST | `/api/review` | Run review |
| POST | `/api/test-connection` | Test LLM connection |
| POST | `/api/review/structure-matching` | Structure matching (split review) |
| POST | `/api/review/group` | Group review (split review) |
| POST | `/api/review/integrate` | Integrate results (split review) |
| POST | `/api/organize-markdown` | AI Markdown organization |
| POST | `/api/split/headings` | Get H2 heading list |
| POST | `/api/split/markdown` | Split design document |
| POST | `/api/split/code` | Split source code |
| POST | `/api/summarize` | Generate summary |

## Directory Structure

```
spec-code-ai-reviewer/
├── backend/                     # Backend (Python / FastAPI)
│   ├── app/
│   ├── tests/
│   ├── pyproject.toml           # Version is managed here
│   └── uv.lock
├── frontend/                    # Frontend (Vite + React + TypeScript)
│   ├── src/
│   └── package.json
├── docs/                        # Docs
│   ├── spec.md                  # Application spec
│   ├── config-file-generator-spec.md  # Config file generator spec
│   ├── split-review.md          # Split review feature details
│   ├── ec2-deployment-spec.md   # (OLD) EC2 deployment spec for the multi-version era
│   └── tests/                   # Test cases
│       └── README.md
├── .env.example                 # Env var template (AWS Bedrock)
└── README.md                    # This file
```

## Related Projects

The following external tools are used as dependencies (installed via uv from PyPI or git sources — see `backend/pyproject.toml`).

| Package | Repository | Description |
|-------------|-----------|-------------|
| add-line-numbers | https://github.com/elvezjp/add-line-numbers | Tool to add line numbers to files |
| code2map | https://github.com/elvezjp/code2map | Source code to mind map conversion tool |
| excel2md | https://github.com/elvezjp/excel2md | Excel to CSV Markdown conversion tool |
| markitdown | https://github.com/microsoft/markitdown | Tool to convert various file formats to Markdown |
| md2map | https://github.com/elvezjp/md2map | Markdown to mind map conversion tool |

If you need the sources for reference, clone the upstream repositories directly (e.g., `git clone https://github.com/elvezjp/excel2md.git`). These repositories were previously embedded as git subtrees; that layout is preserved in the `v0.9.9` tag.

## Version Management

Only the latest code is kept at the repository root. Versions are managed with git tags.

- The `main` branch accumulates changes for the next version under a `## [X.Y.Z] - Unreleased` heading in [CHANGELOG.md](CHANGELOG.md)
- On release, the heading date is finalized, the version in `backend/pyproject.toml` (and the frontend version labels) is confirmed, and a `vX.Y.Z` tag is created

### Using Old Versions

Old versions (v0.5.0–v0.9.9) were previously kept as snapshots under a `versions/` directory. That layout, including the multi-version infrastructure (nginx / PM2 / Docker) and embedded subtrees, is preserved in the `v0.9.9` tag:

```bash
git checkout v0.9.9
# Old versions are under versions/v0.5.0 ... versions/v0.9.9
```

**Note**: Do not delete or move the `v0.9.9` tag — it serves as the archive reference point for the old layout.

## Update History

For detailed change history, see [CHANGELOG.md](CHANGELOG.md).

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Security

For reporting vulnerabilities, see [SECURITY.md](SECURITY.md). Our Dependabot alert handling policy is also documented there.

## Background

This tool was created during the development of **IXV**, an AI development ecosystem designed for Japanese engineering teams.

IXV delivers a methodology and OSS that put AI to practical use in real development workflows. This repository publishes a portion of that work.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contact

- **Email**: info@elvez.co.jp
- **To**: Elvez Co., Ltd.
