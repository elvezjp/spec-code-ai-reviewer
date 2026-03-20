# Security Policy

[English](./SECURITY.md) | [日本語](./SECURITY_ja.md)

## Supported Versions

Security updates are provided for the following versions. We recommend using the latest version.

| Version | Supported          |
| ------- | ------------------ |
| 0.3.x   | :white_check_mark: |
| < 0.3   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, **please do not create a public Issue**.

### How to Report

Please report using one of the following methods:

1. **GitHub Security Advisory** (recommended)
   - Report privately via [Security Advisories](https://github.com/elvezjp/md2map/security/advisories/new)

2. **Email**
   - Contact us at the email address listed in the [README](README.md#contact)

### Information to Include

- **Description of the vulnerability**: Overview and type of the issue
- **Steps to reproduce**: Specific steps to reproduce the problem
- **Potential impact**: Expected damage scope and severity
- **Suggested fix** (if possible): Mitigation or fix proposals
- **Contact information** (optional): For follow-up communication

### Example Report

```
Subject: [SECURITY] Vulnerability in file path handling

Description:
Insufficient validation of input file paths allows directory traversal attacks.

Steps to reproduce:
1. Run md2map build "../../../etc/passwd" --out ./out
2. Unintended files are processed

Impact:
Arbitrary files may be read. Severity: High

Suggested fix:
Add input path normalization and validation to ensure files are within allowed directories.
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

- md2map reads specified Markdown files and writes analysis results to an output directory
- Exercise caution when processing files from untrusted sources
- Specify a safe location with write permissions for the output directory

### Input Validation

- Input files are expected to be in Markdown format (`.md`)
- Malformed files are handled as parse errors
- Exercise caution with symbolic link traversal

### Output Security

- Generated files contain fragments of the original Markdown document
- When processing documents containing sensitive information, handle output files with care
- `MAP.json` contains path information of the original file

### Dependencies

- Dependencies are regularly scanned for vulnerabilities
- Use `uv sync` to get the latest dependencies

## Security Best Practices

To use md2map safely, follow these recommendations:

1. **Use the latest version**: It may contain security fixes
2. **Verify input files**: Review content before processing files from untrusted sources
3. **Restrict output directory**: Manage write destinations appropriately and avoid writing to sensitive directories
4. **Handle generated files with care**: Output files contain original document content, so set appropriate access controls
5. **Run in a sandbox environment**: Consider running in an isolated environment when processing untrusted documents

## Known Security Limitations

- This tool performs static analysis of Markdown only and does not access external links
- Malicious content pattern detection is not provided
- Markdown containing HTML tags is output as-is

## Contact

For security-related questions that are not vulnerabilities:

- Create an Issue on GitHub with the `security` label
- For general questions, use Discussions

## Acknowledgments

We thank security researchers who report vulnerabilities. With the reporter's consent, acknowledgments will be included in the fix release.
