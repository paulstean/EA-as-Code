# Security

## Reporting a Vulnerability

This repository contains the enterprise architecture model of an organisation's IT landscape. Exposure of this information could reveal system dependencies, integration patterns, or technology choices that may be useful to an attacker.

If you discover a security vulnerability:

1. **Do not** open a public GitHub issue
2. Email the project maintainers directly or use the GitHub Security Advisory "Report a Vulnerability" feature
3. Provide a clear description of the issue and its potential impact

## Responsible Disclosure

We request that you give us a reasonable timeframe to address any reported issues before public disclosure.

## Best Practices

- Do not commit secrets, passwords, or connection strings to any catalog file
- Do not include personally identifiable information in seed data
- Review all PRs for unintended exposure of internal architecture details
- Keep the `GITHUB_TOKEN` and any Copilot API credentials secure
