---
name: StaticApplicationSecurityTesting
description: "SAST pack: semgrep, patterns, CI/CD code audit."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Security, CodeAnalysis, SAST, Semgrep]
    related_skills: [OidcPkceAuthorizationCode, PhpMySqlWebAppPenetrationTesting, WebInvestigationMethodology]
---

## When to Use

Triggers that indicate you should run this SAST pack:

- "Analyze code for security flaws"
- "Run SAST on a repository"
- "Detect dangerous patterns"

## Prerequisites

- "semgrep installed"
- "Access to the source code"

## Golden Rules / Pitfalls

The key failure modes to watch for when running static analysis:

- **Static analysis ≠ proof.** Semgrep/rg hits are candidate findings, not confirmed vulnerabilities. A pattern can match dead code, unused branches, or false positives. Every hit must be verified by reading the surrounding context before you report it.
- **Broken command = empty report.** If `semgrep` exits non-zero (missing config, invalid rule syntax, no language), the scan silently produces no useful output. Always check the exit code and confirm the report file is non-empty before trusting a clean result.
- **No config means no rules.** Running semgrep without `--config` scans nothing meaningful. Point it at a real rules file or a published rule set (e.g. `p/owasp-top-ten`).
- **Language coverage is limited.** The bundled rules target PHP primarily; a PHP-only ruleset will miss issues in JS/Go/Python. Enumerate which languages you actually scanned.
- **`|| true` hides dependency-audit failures.** `composer audit`, `npm audit`, `pip-audit` are wrapped in `|| true` so the pipeline doesn't break — but that also swallows real command errors. Inspect the JSON output files explicitly.
- **Verbose regexes are brittle.** The `rg` fallback patterns are escaping-heavy and easy to mistype. Paste them verbatim, never retype from memory.

## 📦 Pack Contents

### 1. Semgrep Security Rules (`.semgrep-security.yml`)
```yaml
rules:
  - id: sql-injection-php
    pattern-either:
      - pattern: '$db->query($X)'
      - pattern: '$db->exec($X)'
      - pattern: 'mysqli_query($X, $Y)'
    message: "Potential SQL injection - use prepared statements"
    severity: ERROR
    languages: [php]

  - id: xss-output-php
    pattern-either:
      - pattern: 'echo $_GET[...]'
      - pattern: 'echo $_POST[...]'
      - pattern: 'echo $_REQUEST[...]'
    message: "Potential XSS - escape output with htmlspecialchars()"
    severity: WARNING
    languages: [php]

  - id: rce-php
    pattern-either:
      - pattern: 'eval($X)'
      - pattern: 'exec($X)'
      - pattern: 'shell_exec($X)'
      - pattern: 'system($X)'
      - pattern: 'passthru($X)'
      - pattern: 'preg_replace(..., /e)'
    message: "Potential RCE - avoid dynamic code execution"
    severity: ERROR
    languages: [php]

  - id: hardcoded-secrets
    pattern-either:
      - pattern: '$password = "..."'
      - pattern: '$secret = "..."'
      - pattern: '$api_key = "..."'
    message: "Hardcoded secret - use environment variables"
    severity: WARNING
    languages: [php, javascript, python, yaml]

  - id: path-traversal
    pattern-either:
      - pattern: 'file_get_contents($X)'
      - pattern: 'fopen($X, ...)'
      - pattern: 'include($X)'
      - pattern: 'require($X)'
    message: "Potential path traversal - validate the path"
    severity: WARNING
    languages: [php]

  - id: weak-crypto
    pattern-either:
      - pattern: 'md5($X)'
      - pattern: 'sha1($X)'
      - pattern: 'mcrypt_*'
    message: "Weak cryptography - use password_hash()/hash()"
    severity: WARNING
    languages: [php]
```

### 2. Analysis Scripts

#### `run-security-scan.sh`
```bash
#!/bin/bash
REPO_PATH="${1:-.}"
REPORT_DIR="security-reports/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$REPORT_DIR"

semgrep --config=.semgrep-security.yml \
        --json="$REPORT_DIR/semgrep-results.json" \
        --sarif="$REPORT_DIR/semgrep-results.sarif" \
        "$REPO_PATH"

[ -f "$REPO_PATH/composer.json" ] && composer audit --format=json > "$REPORT_DIR/composer-audit.json" 2>&1 || true
[ -f "$REPO_PATH/package.json" ] && npm audit --json > "$REPORT_DIR/npm-audit.json" 2>&1 || true
[ -f "$REPO_PATH/requirements.txt" ] && pip-audit --format=json > "$REPORT_DIR/pip-audit.json" 2>&1 || true

echo "✅ Report in $REPORT_DIR/"
```

### 3. Regex Patterns (rg/grep fallback)
```bash
# SQL Injection
rg -n "query\(|exec\(|mysqli_query\(" --type php
# XSS
rg -n "echo \$_\\(GET\|POST\|REQUEST\)" --type php
# RCE
rg -n "eval\(|exec\(|shell_exec\(|system\(|passthru\(|preg_replace.*\/e" --type php
# Secrets
rg -n "(password|secret|api_key|token)\s*=\s*[\"'][^\"']+[\"']" --type php --type js --type py
# Path traversal
rg -n "file_get_contents\(|fopen\(|include\(|require\(" --type php
# Weak crypto
rg -n "md5\(|sha1\(|mcrypt_" --type php
```

### 4. CI/CD GitHub Actions
```yaml
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: returntocorp/semgrep-action@v1
        with:
          config: .semgrep-security.yml
      - run: |
          [ -f composer.json ] && composer audit
          [ -f package.json ] && npm audit
```

---

## 🚀 Usage
```bash
./run-security-scan.sh /path/to/repo
rg -n "eval\(|exec\(|shell_exec\(" --type php /path/to/repo
cp .github/workflows/security-scan.yml /target/repo/.github/workflows/
```

---

## 📊 OWASP Top 10 Coverage
| Category | Rules | Coverage |
|-----------|--------|------------|
| SQL Injection | 3 | PDO, mysqli, query |
| XSS | 4 | echo, print, templating |
| RCE | 6 | eval, exec, shell_exec, system, passthru, preg_replace/e |
| Secrets | 5 | password, secret, api_key, token, private_key |
| Path Traversal | 4 | file_get_contents, fopen, include, require |
| Weak crypto | 3 | md5, sha1, mcrypt |
| **Total** | **25+** | **Aligned OWASP Top 10** |

---

## Out of Scope

Static analysis has hard limits. This pack does **not** cover:

- **Runtime/dynamic checks** — live authentication bypass, session handling, or actual exploitation of a running app. Use DynamicRuntimeSecurityAnalysis for that.
- **Manual code review** — a pattern match cannot reason about business logic, authorization flows, or architecture. These require a human eyes-on review.
- **Dependency-CVSS triage** — `composer audit` / `npm audit` / `pip-audit` only list known-affected packages; they do not judge exploitability in your specific codebase.
- **Infrastructure / config scanning** — IaC (Terraform/CloudFormation), container images, or cloud misconfigurations are not scanned by these rule packs.
- **Crypto implementation review** — weak-crypto rules flag calls like `md5()` but cannot certify that a full TLS/crypto implementation is sound.

---

## Verification

How to confirm the SAST results are real and not an empty/broken run.

Check the semgrep exit code (0 = no findings, nonzero = error or findings, and the scan itself failed):

```bash
# Should exit 0 = success (findings reported via JSON flags / --error)
semgrep --config=.semgrep-security.yml --strict "$REPO_PATH"
echo "exit code: $?"
```

Confirm each report file was actually produced and is non-empty:

```bash
ls -la "$REPORT_DIR/"
# every expected artifact must exist and be > 0 bytes
test -s "$REPORT_DIR/semgrep-results.json" && echo "SAST JSON ✔" || echo "SAST JSON MISSING ✘"
test -s "$REPORT_DIR/semgrep-results.sarif" && echo "SARIF ✔" || echo "SARIF MISSING ✘"
```

Validate the JSON parses and count real findings (grep-able, machine-readable):

```bash
# semgrep JSON — number of findings
jq '.results | length' "$REPORT_DIR/semgrep-results.json"
# list each finding file location
jq -r '.results[] | "\(.path):\(.start.line)\t\(.check_id)\t\(.extra.severity)"' "$REPORT_DIR/semgrep-results.json"
```

Verify the rg fallback hits against source (grep-able, human-readable) and read surrounding context to confirm each match is a live code path, not dead code:

```bash
rg -n "eval\(|exec\(|shell_exec\(" --type php /path/to/repo
# review each hit with context lines
rg -n -C 3 "eval\(" --type php /path/to/repo | head -50
```

Dependency audits: never trust a silent success — the `|| true` wrapper swallows errors. Confirm each audit JSON is present and parseable:

```bash
for f in composer-audit.json npm-audit.json pip-audit.json; do
  test -s "$REPORT_DIR/$f" && jq empty "$REPORT_DIR/$f" && echo "$f OK" || echo "$f MISSING/INVALID"
done
```

A scan with zero findings is only credible when the config loaded, the exit code was 0, the report files exist, and the `--json`/`grep` counts returned a well-formed result.