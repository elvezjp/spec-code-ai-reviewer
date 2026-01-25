# Spec Doc–Java Program Matching AI Reviewer

[English](./README.md) | [日本語](./README_ja.md)

[![Elvez](https://img.shields.io/badge/Elvez-Product-3F61A7?style=flat-square)](https://elvez.co.jp/)
[![IXV Ecosystem](https://img.shields.io/badge/IXV-Ecosystem-3F61A7?style=flat-square)](https://elvez.co.jp/ixv/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue?style=flat-square&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Stars](https://img.shields.io/github/stars/elvezjp/spec-code-ai-reviewer?style=social)](https://github.com/elvezjp/spec-code-ai-reviewer/stargazers)

A web application that uses AI to cross-check design documents (Excel format) against program code and verify consistency.

https://github.com/user-attachments/assets/fa387d12-1c8a-4bf2-aeb4-758595479982

## Features

- **Design document conversion**: Convert Excel (.xlsx, .xls) to Markdown (using MarkItDown, excel2md)
- **Program conversion**: Add line numbers to any text file (add-line-numbers compatible)
- **Cross-check review**: Verify consistency between the design doc and code using LLMs (Bedrock / Anthropic / OpenAI)
- **Report output**: Generate a Markdown review report

For detailed feature specs, see [latest/spec.md](latest/spec.md).

## System Architecture

- **Frontend**:
  - v0.6.0 and later: Vite + React + TypeScript + Tailwind CSS
  - v0.5.2 and earlier: Single HTML file + Tailwind CSS (CDN)
- **Backend**: Python / FastAPI
  - MarkItDown / excel2md (Excel to Markdown conversion)
  - add-line-numbers compatible (line numbering)
  - Multi-LLM provider support (Bedrock / Anthropic / OpenAI)

## Usage

1. **Upload design documents**: Select Excel (.xlsx, .xls) files (multiple allowed)
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

There are two ways to run the app locally.

- **Single-version launch**: Start directly with uvicorn (for development)
- **Docker Compose launch**: Multi-version environment equivalent to production (for verification)

For production deployment on EC2, see [EC2 Deployment Spec](docs/ec2-deployment-spec.md).

### Prerequisites

#### Python Version

- **Required**: Python 3.10 or later
- **Recommended**: Python 3.11 or 3.12
- **How to check**: Run `python --version` or `python3 --version`

uv automatically uses an appropriate Python version. The installed Python 3.10+ on your system will be used as-is.

#### Node.js Version (v0.6.0 and later)

- **Required**: Node.js 18 or later
- **Recommended**: Node.js 20 LTS or 22 LTS
- **How to check**: Run `node --version`

Required for developing/building the v0.6.0+ frontend (Vite + React + TypeScript). Not needed if you only use v0.5.2 or earlier.

#### Other

- [uv](https://docs.astral.sh/uv/) (Python package manager)

### Installation

```bash
# Install uv (if not installed)
# See: https://docs.astral.sh/uv/getting-started/installation/

# Install Node.js (if using v0.6.0 or later)
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

# Option 2: Configure with AWS CLI
aws configure
```

### Single-Version Launch

#### v0.6.0 and later (Vite + React)

For v0.6.0 and later, start frontend and backend separately.

**Terminal 1: Start backend**

```bash
cd versions/v0.7.0/backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

**Terminal 2: Start frontend**

```bash
cd versions/v0.7.0/frontend
npm install
npm run dev
```

Access http://localhost:5173 (Vite dev server)

**Note**: The frontend runs on the Vite dev server (port 5173), and API requests are proxied to the backend (port 8000).

#### v0.5.2 and earlier (Single HTML file)

For v0.5.2 and earlier, only the backend runs (frontend is served by the backend).

```bash
cd versions/v0.5.2/backend
uv sync
uv run uvicorn app.main:app --reload --port 8000
```

Access http://localhost:8000

**Note**: A version switch balloon appears at the top-left, but in single-version launch mode only the running version works. Check the running version number from the "Settings" icon in the top-right.

### Docker Compose Launch (Multi-Version)

You can start a development environment with version switching equivalent to production.

```bash
# Set AWS credentials (if using system LLM)
cp .env.example .env
# Edit .env to set AWS credentials

# Start
docker-compose up -d --build

# Open in browser
open http://localhost:8000

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Note**: If you do not have an AWS environment, you do not need to create `.env`. You can use Anthropic API or OpenAI API by uploading a config file via the web UI.

You can switch versions from the top-left balloon (routing via Cookie + Nginx map).

### Run Tests

Run tests in each version's directory.

```bash
# v0.7.0 backend tests
cd versions/v0.7.0/backend
uv run pytest tests/ -v

# v0.7.0 frontend tests
cd versions/v0.7.0/frontend
npm test

# v0.5.2 and earlier tests (backend only)
cd versions/v0.5.2/backend
uv run pytest tests/ -v
```

### Version Sync

Version numbers are centrally managed in `backend/pyproject.toml`.
To sync version labels in the frontend:

```bash
python3 scripts/sync_version.py
```

This script does the following:

1. **Sync version numbers**: Reads versions from each `backend/pyproject.toml` and updates the display in the corresponding `frontend/index.html`
2. **Update VERSIONS array**: Updates the version switcher `VERSIONS` array in all frontends with all available versions

#### Options

```bash
# Sync all versions + update VERSIONS array (default)
python3 scripts/sync_version.py

# Sync only a specific version (no VERSIONS array update)
python3 scripts/sync_version.py v0.5.0

# Skip updating the VERSIONS array
python3 scripts/sync_version.py --no-versions-array
```

## Environment Variables (System LLM)

These environment variables are used to run the system LLM (AWS Bedrock).

**Note**: If you run with a config file uploaded from the web UI, that configuration takes precedence (see the "[Usage](#usage)" section).

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | - |
| `AWS_REGION` | AWS region | `ap-northeast-1` |
| `BEDROCK_MODEL_ID` | Model ID to use | `global.anthropic.claude-haiku-4-5-20251001-v1:0` |
| `BEDROCK_MAX_TOKENS` | Max response tokens | `16384` |

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
| POST | `/api/convert/add-line-numbers` | Add line numbers |
| GET | `/api/convert/available-tools` | List available conversion tools |
| POST | `/api/review` | Run review |

## Directory Structure

```
spec-code-ai-reviewer/
├── docker-compose.yml           # Docker Compose config (multi-version dev)
├── Dockerfile.dev               # Dev Dockerfile (Ubuntu)
├── docker-entrypoint.sh         # Docker startup script
├── ecosystem.config.js          # PM2 config (production)
├── dev.ecosystem.config.js      # PM2 config (development)
├── nginx/
│   ├── dev.conf                 # Dev Nginx config
│   ├── spec-code-ai-reviewer.conf  # Production Nginx config
│   └── version-map.conf         # Version switch map (shared)
├── latest -> versions/v0.7.0    # Symlink to latest
│
├── versions/                    # All versions
│   ├── README.md                # Version management notes
│   ├── v0.5.0/                  # Old version
│   │   ├── backend/
│   │   ├── frontend/
│   │   ├── config-file-generator-spec.md
│   │   └── spec.md
│   ├── v0.5.1/                  # Old version
│   │   ├── backend/
│   │   ├── frontend/
│   │   ├── config-file-generator-spec.md
│   │   └── spec.md
│   ├── v0.5.2/                  # Old version
│   │   ├── backend/
│   │   ├── frontend/
│   │   ├── config-file-generator-spec.md
│   │   └── spec.md
│   ├── v0.6.0/                  # Old version (Vite + React)
│   │   ├── backend/
│   │   ├── frontend/            # Vite + React + TypeScript
│   │   ├── config-file-generator-spec.md
│   │   └── spec.md
│   └── v0.7.0/                  # Latest (Vite + React)
│       ├── backend/
│       ├── frontend/            # Vite + React + TypeScript
│       ├── config-file-generator-spec.md
│       └── spec.md
│
├── docs/                        # Docs
│   └── ec2-deployment-spec.md   # EC2 deployment spec
│
├── scripts/                     # Utility scripts
│   └── sync_version.py          # Version sync script
│
├── tests/                       # Test cases
│   └── README.md
│
├── add-line-numbers/            # Subtree (elvezjp)
├── excel2md/                    # Subtree (elvezjp)
├── markitdown/                  # Subtree (Microsoft)
└── README.md                    # This file
```

## Git Subtrees

This repository includes the following external repositories via git subtree.

| Directory | Repository | Description |
|-------------|-----------|-------------|
| `add-line-numbers/` | https://github.com/elvezjp/add-line-numbers | Tool to add line numbers to files |
| `excel2md/` | https://github.com/elvezjp/excel2md | Excel to CSV Markdown conversion tool |
| `markitdown/` | https://github.com/microsoft/markitdown | Tool to convert various file formats to Markdown |

### Updating Subtrees

```bash
# Update add-line-numbers
git subtree pull --prefix=add-line-numbers https://github.com/elvezjp/add-line-numbers.git main --squash

# Update excel2md
git subtree pull --prefix=excel2md https://github.com/elvezjp/excel2md.git main --squash

# Update markitdown
git subtree pull --prefix=markitdown https://github.com/microsoft/markitdown.git main --squash
```

## Version Management

### Port Assignment Rule

A port assignment rule based on semantic versioning (`vX.Y.Z`) is used.

```
Port = 8000 + (minor version x 10) + patch version
Example: v0.2.5 -> 8000 + (2 x 10) + 5 = 8025
```

| Version | Port |
|-----------|------|
| v0.7.0 (latest) | 8070 |
| v0.6.0 | 8060 |
| v0.5.2 | 8052 |
| v0.5.1 | 8051 |
| v0.5.0 | 8050 |

### Changes Required When Adding a New Version

When adding a new version (e.g., v0.7.0), update the following files.

#### Add and Update Version Directory

| File | Change |
|---------|---------|
| `versions/v0.7.0/` | Add the new version code |
| `versions/v0.7.0/spec.md` | Update version numbers (top, review examples, test items) |
| `versions/v0.7.0/config-file-generator-spec.md` | Update target version |
| `versions/v0.7.0/frontend/package.json` | Update version (v0.6.0+ only) |
| `versions/v0.7.0/backend/pyproject.toml` | Update version |
| `latest` symlink | Update to point to new version (`rm latest && ln -s versions/v0.7.0 latest`) |
| `versions/v0.5.x/frontend/index.html` | Update VERSIONS array (run `scripts/sync_version.py`, v0.5.x and earlier only) |

#### Update Config and Docs

| File | Change |
|---------|---------|
| `docker-compose.yml` | Add new port to backend expose; add new frontend to nginx volumes |
| `nginx/version-map.conf` | Add new routing; update default port |
| `ecosystem.config.js` | Add new version to VERSIONS array (see below) |
| `dev.ecosystem.config.js` | Add new version to VERSIONS array |
| `docs/ec2-deployment-spec.md` | Add new version to config examples |
| `versions/README.md` | Add directory structure, version comparison table, and update history |
| `README.md` | Update directory structure and port table |
| `CHANGELOG.md` | Append change history |

#### Example: Add to ecosystem.config.js

Add the new version to the VERSIONS array. `latest` is a symlink, so only real versions are started.

```javascript
const VERSIONS = [
  // latest is a symlink, so only real versions are started
  { name: 'spec-code-ai-reviewer-v0.7.0', cwd: 'versions/v0.7.0', port: 8070 },  // add
  { name: 'spec-code-ai-reviewer-v0.6.0', cwd: 'versions/v0.6.0', port: 8060 },
  { name: 'spec-code-ai-reviewer-v0.5.0', cwd: 'versions/v0.5.0', port: 8050 },
];
```

**Note**: There is no need for a `latest` process. Since `version-map.conf` routes the `default` port to the latest version, requests without a cookie are routed to the latest version.

**Note**: `PYTHONPATH` is configured with the `add-line-numbers` subtree path, so the `add_line_numbers` module can be imported.

#### Example: Add to nginx/version-map.conf

```nginx
# Route backend port based on Cookie value
map $cookie_app_version $backend_port {
    "v0.7.0"  8070;  # add
    "v0.6.0"  8060;
    "v0.5.0"  8050;
    default   8070;  # latest (v0.7.0)
}

# Route frontend based on Cookie value
map $cookie_app_version $frontend_root {
    "v0.7.0"  /var/www/spec-code-ai-reviewer/versions/v0.7.0/frontend;  # add
    "v0.6.0"  /var/www/spec-code-ai-reviewer/versions/v0.6.0/frontend;
    "v0.5.0"  /var/www/spec-code-ai-reviewer/versions/v0.5.0/frontend;
    default   /var/www/spec-code-ai-reviewer/latest/frontend;
}
```

### Production Update Steps

```bash
# (Run locally) Add the private key corresponding to the registered GitHub public key to ssh-agent
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_rsa   # Adjust file name as needed

# SSH into the server (enable ssh-agent forwarding to access GitHub)
ssh -A user@example.com

# Deploy new version
cd /var/www/spec-code-ai-reviewer
git pull origin main

# Install dependencies
cd versions/v0.5.1/backend
uv sync

# Rebuild PM2 process list (add new version)
cd /var/www/spec-code-ai-reviewer
pm2 delete all
pm2 start ecosystem.config.js
pm2 save

# Apply Nginx config changes (reflect version-map.conf)
sudo cp nginx/version-map.conf /etc/nginx/conf.d/
sudo nginx -t
sudo nginx -s reload
```

**Notes:**
- The `latest` symlink is updated automatically by `git pull` (Git tracks symlinks)
- `pm2 reload` only restarts existing processes. When adding a new version, run `pm2 delete all && pm2 start` to rebuild.
- `spec-code-ai-reviewer.conf` uses the `$backend_port` variable, so only `version-map.conf` needs updating

## Update History

For detailed change history, see [CHANGELOG.md](CHANGELOG.md).

## Background

This tool is a small practical product born from the development of the Japanese development document support AI **IXV (Ikushibu)**.

In IXV, we tackle the challenge of understanding, structuring, and utilizing Japanese documents in system development. This repository publishes a cut-out part of that effort.

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contact

- **Email**: info@elvez.co.jp
- **To**: Elvez Co., Ltd.
