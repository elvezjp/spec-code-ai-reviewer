# Security Policy

[English](./SECURITY.md) | [日本語](./SECURITY_ja.md)

## Supported Versions

The latest version is supported:

| Version | Supported          |
| ------- | ------------------ |
| 0.10.0   | :white_check_mark: |
| < 0.10.0 | :x:                |

## Intended Environment

**spec-code-ai-reviewer is meant to be run locally, and the application itself has no authentication or authorization.** This is a deliberate design decision, recorded as "option A: no authentication" in [Issue #134](https://github.com/elvezjp/spec-code-ai-reviewer/issues/134).

### What is not guaranteed

Every API endpoint can be called without credentials. Network reachability is the only line of defense, and anyone who can reach the service can:

- Call the configured LLM without limit (cost abuse)
- Read the uploaded design documents, source code, and review results
- Invoke any of the conversion, split, and review APIs

### What we ask of operators

1. **Do not expose it on a network.** Start the backend bound to `127.0.0.1` (see "Launch" in the README). Binding to `0.0.0.0` lets anyone on the same network call every endpoint
2. **Put authentication in front of it if you do expose it.** When the service has to sit on a network, require authentication at a reverse proxy. [docs/ec2-deployment-spec.md](docs/ec2-deployment-spec.md) describes a setup using nginx Basic authentication (`auth_basic`)
3. **Do not widen the CORS allowlist.** The default is local development origins only. Avoid `CORS_ORIGINS=*`, which lets any site read this API's responses from a browser

### Background

Up to v0.9.9, the multi-version layout shipped an nginx configuration (`nginx/spec-code-ai-reviewer.conf`) that performed Basic authentication. That configuration was removed in v0.10.0 along with the rest of the multi-version infrastructure ([#118](https://github.com/elvezjp/spec-code-ai-reviewer/issues/118)), so the front-facing authentication is now the operator's responsibility.

## Reporting a Vulnerability

If you discover a security vulnerability in spec-code-ai-reviewer, please follow these steps for responsible disclosure:

### How to Report

1. **Do not** create a public GitHub Issue for security vulnerabilities
2. Send a detailed report to the maintainers using one of the following methods:
   - Create a private security advisory on GitHub (recommended)
   - For low-severity issues, create an Issue with the "security" label

### What to Include

Please include the following information in your report:

- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact and severity
- Proposed fix or mitigation (if any)
- Contact information (optional)

### Example Report

```
Subject: [SECURITY] Potential vulnerability in file upload

Description:
When uploading a specially crafted Excel file,
unexpected behavior may occur on the server side.

Steps to Reproduce:
1. Create an Excel file with malicious macros
2. Upload the file
3. Execute the conversion process

Impact:
Could cause excessive server resource consumption or denial of service.

Proposed Fix:
Strengthen file size and cell count limits.
```

## Response Timeline

- **Initial response**: Within 48 hours
- **Status update**: Within 7 days
- **Resolution**: Based on severity
  - Critical: Within 14 days
  - High: Within 30 days
  - Medium: Within 60 days
  - Low: Next release cycle

## Security Considerations

### File Processing

spec-code-ai-reviewer processes files that may contain:

- Excel files (macros, external links, embedded objects)
- Source code files (arbitrary text files)
- Configuration files (API keys, credentials)

**Recommendations:**

1. Only process files from trusted sources
2. Review files received from external sources before processing
3. Use a sandbox environment when processing untrusted files
4. Carefully manage configuration files containing API keys or credentials

### API Key Management

This application may use the following APIs:

- AWS Bedrock
- Anthropic API
- OpenAI API

**Recommendations:**

1. Manage API keys via environment variables; do not hardcode them
2. Follow the principle of least privilege, granting only necessary permissions
3. Rotate API keys regularly
4. Use different API keys for production and development environments

### Input Validation

spec-code-ai-reviewer includes the following security measures:

- Uses `read_only=True` mode for Excel file processing
- File size limits
- Input file validation

### Output Security

Notes when using generated review reports:

- Reports may contain content from input files
- If files containing sensitive information are reviewed, the report will also contain sensitive information
- Review report content before sharing

### Dependencies

This project uses the following key dependencies:

- `fastapi`: Web framework
- `markitdown`: Excel to Markdown conversion
- `openpyxl`: Excel file processing
- `boto3`: AWS Bedrock integration
- `anthropic`: Anthropic API integration
- `openai`: OpenAI API integration

We monitor security advisories for these dependencies and update as needed.

### Dependabot Alert Policy

This repository keeps only the latest code at the root (`backend/` / `frontend/`); older releases are referenced via git tags and are not scanned by Dependabot. External tools (`add-line-numbers`, `code2map`, `excel2md`, `markitdown`, `md2map`) are consumed as dependencies via uv, so their vulnerabilities surface through the root lockfiles. We operate Dependabot alerts as follows.

**Malware tab**: Always fix, regardless of where it is detected.

**Vulnerable**: Follow the table below.

| Target | Action |
|--------|--------|
| Lockfiles at the root (`backend/uv.lock`, `frontend/package-lock.json`) | **Fix** (dependency update / PR) |

A dismissed alert will not reappear for the same combination of manifest × package × CVE, but a new CVE published for the same package will be raised as a new alert.

## Security Best Practices

Recommendations when using spec-code-ai-reviewer:

1. **Stay up to date**: Always use the latest version
2. **Verify input**: Inspect files before processing
3. **Sandbox processing**: Use containers or VMs for untrusted files
4. **Validate output**: Review generated reports before use
5. **Limit permissions**: Run with minimum required privileges
6. **Monitor dependencies**: Keep dependency libraries up to date
7. **Protect credentials**: Manage API keys securely

## Known Security Limitations

1. **No authentication or authorization** (CWE-306): Every API endpoint is open. This is by design — see "Intended Environment" above for what it means and how to operate the tool safely
2. **Macro detection**: Excel file macros are not executed but their presence is not warned about
3. **External links**: External links in Excel files are processed but not validated
4. **File size**: Very large files may cause memory issues
5. **LLM output**: AI-generated output is not always accurate. Human review is required for critical decisions

## Security Updates

Security updates are released as follows:

- Patch versions for minor issues (e.g., 0.5.1)
- Minor versions for critical issues (e.g., 0.6.0)
- Listed in CHANGELOG.md with a `[SECURITY]` prefix

## Acknowledgments

We appreciate security researchers who responsibly report vulnerabilities. Those who report valid security issues will be acknowledged in:

- CHANGELOG.md (unless anonymity is preferred)
- Fix release notes

## Questions

For security-related questions that are not vulnerabilities, please contact us via:

- Create an Issue with the "security" label
- Contact the maintainers
