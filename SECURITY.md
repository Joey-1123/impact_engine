# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.6.x   | Yes       |
| < 0.6   | No        |

## Reporting a Vulnerability

If you discover a security vulnerability in Impact Engine, please report it
privately by opening a security advisory at:

https://github.com/Joey-1123/impact_engine/security/advisories/new

Do **not** report security vulnerabilities via public GitHub issues.

You should receive a response within 48 hours. If you do not, please follow
up to ensure the message was received.

## What to Include

- Description of the vulnerability
- Steps to reproduce
- Affected versions
- Any potential impact or exploit scenario

## Scope

The following are in scope:
- The `impact-engine` Python package
- The `impact_web` Django dashboard
- CI/CD configuration files
- Build and deployment scripts

Out of scope:
- Third-party dependencies (report those to their respective maintainers)
- The VS Code extension (it is a stub with no runtime)

## Security Measures

Impact Engine uses the following security practices:

- **Input sanitization:** HTML export escapes node IDs via `html.escape()`
- **Shell injection prevention:** Git ref parameters are quoted with `shlex.quote()`
- **No code execution:** Analysis is purely static (AST/regex) — no runtime execution of target code
- **Optional authentication:** Web dashboard supports HMAC webhook verification and API key auth
- **Dependency isolation:** Optional extras (`web`, `terminal`, `visual`, `watch`) avoid unnecessary dependencies
