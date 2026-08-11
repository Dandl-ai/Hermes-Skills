---
name: WebInvestigationMethodology
description: "Web security audit methodology: recon, SAST, live testing, business logic, reporting."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Security, Analysis, Methodology, Audit]
    related_skills: []
---

## When to Use

Use this skill for a security analysis of a web application, a full application audit, or when you need an audit methodology.

## Prerequisites

- Access to the source code (Git repo)
- Access to the live instance (if possible)
- Tools: curl, Node.js, Docker, grep/rg, semgrep

## Golden Rules / Pitfalls

- Scope: Web applications (PHP, Node.js, Python, etc.), REST/GraphQL APIs, and associated infrastructure (Docker, DB, reverse proxy).

## 🔍 Phase 1 — Reconnaissance (Recon)

### 1.1 Scope & Asset Inventory
- [ ] Identify the target URL, IP, DNS, and open ports
- [ ] List subdomains, APIs, and known endpoints
- [ ] Identify the technical stack (language, framework, DB, reverse proxy, CDN)
- [ ] Verify TLS certificates, HSTS, and CSP

### 1.2 Codebase Mapping
```bash
git clone --depth 1 <repo_url>
find . -type f -name "*.php" -o -name "*.js" -o -name "*.py" | wc -l
grep -r "require\|import\|use " --include="*.php" --include="*.js" | head -20
```

### 1.3 Entry Points
- [ ] Authentication forms (login, register, forgot password)
- [ ] API endpoints (REST, GraphQL, webhooks)
- [ ] File upload, CSV/XML import
- [ ] Admin panels, installers, maintenance scripts

---

## 🔬 Phase 2 — Static Analysis (SAST)

### 2.1 Dependencies
```bash
composer audit
npm audit --omit=dev
pip-audit
```

### 2.2 Dangerous patterns
| Category | Patterns |
|-----------|----------|
| **SQL Injection** | `query(`, `execute(`, `prepare(` without parameters |
| **XSS** | `echo $_GET`, `echo $_POST`, `innerHTML` |
| **RCE** | `eval(`, `exec(`, `shell_exec(`, `preg_replace(/e`, `var_export` |
| **Path Traversal** | `../`, `file_get_contents`, `fopen`, `include` with user input |
| **Auth bypass** | `if ($user->id == 1)`, `grade == 1`, `role == 'admin'` hardcoded |
| **Secrets** | `password`, `secret`, `key`, `token` in the code |

### 2.3 Configuration
- [ ] `.env`, `config.php` → no hardcoded secrets
- [ ] `display_errors = Off`, `expose_php = Off`
- [ ] Security headers in the code

### 2.4 Automated tools
```bash
semgrep --config=auto --config=p/security-audit .
phpstan analyse src/
eslint --plugin security .
```

---

## 🌐 Phase 3 — Dynamic Analysis (Live Recon)

### 3.1 Connectivity & Challenge
- [ ] DNS, ports 80/443, TLS, HSTS
- [ ] Detect anti-bot challenge (JS, CAPTCHA, WAF)
- [ ] Bypass if necessary (Node + slowAES, headless browser)

### 3.2 Authentication & Session
- [ ] Login: CSRF token, rate-limit, generic error messages
- [ ] Cookies: `Secure`, `HttpOnly`, `SameSite`
- [ ] Session fixation: regeneration after login
- [ ] Remember-me: strong token, bound to IP, expiration

### 3.3 Access Control
- [ ] Modify `id` → IDOR
- [ ] Change `role`/`grade` → privilege escalation
- [ ] Admin access without being admin

### 3.4 Rate Limiting & DoS
- [ ] Login: 5 attempts / 15 min? (IP + account)
- [ ] API: 100 req/min? Burst?
- [ ] Can it be reset via a new cookie / IP rotation?

### 3.5 CORS & Headers
```bash
curl -H "Origin: https://evil.com" -I https://target.com/api
```

### 3.6 Injection & Business Logic
- [ ] SQLi: `' OR 1=1--` in login, search, id
- [ ] XSS: `<img src=x onerror=alert(1)>`
- [ ] Upload: double extension, MIME bypass
- [ ] Race condition: double submission

---

## 🏢 Phase 4 — Business Logic

| Scenario | Test |
|----------|------|
| **First user = admin** | Empty users table → sign up → check grade |
| **User import** | CSV with `custom_grade=1` → promotion |
| **Password reset** | Predictable token? Reusable? |
| **Account deletion** | Self-deletion of admin? CSRF? |
| **Multi-step workflow** | Bypass a step (payment, validation) |

---

## 📊 Phase 5 — Reporting & Remediation

### 5.1 Finding format
```markdown
## [CVE-ID or CUSTOM-XXX] Title
**Severity** : Critical / Major / Minor (CVSS if possible)
**Location** : file:line / endpoint
**Proof** : curl command / code snippet / screenshot
**Impact** : what an attacker can concretely do
**Remediation** : patch code + config + validation test
```

### 5.2 Prioritization
| Priority | Criteria |
|----------|----------|
| **P0 (Critical)** | RCE, admin take-over, session theft, DB leak |
| **P1 (Major)** | IDOR, stored XSS, brute-force, privilege escalation |
| **P2 (Minor)** | Reflected XSS, info disclosure, missing headers |
| **P3 (Info)** | Best practices, hardening, cleanup |

### 5.3 Deliverables
- `audit-<target>-<date>.md` : full report
- `findings.csv` : exploitable list for tracking
- `patches/` : diffs ready to apply
- `evidence/` : curl logs, screenshots, code snippets

---

## 🛠️ Recommended Toolbox

| Tool | Usage |
|-------|-------|
| `curl` / `httpie` | HTTP requests, headers, cookies |
| `node` + `vm` | JS challenge bypass (slowAES, etc.) |
| `semgrep` | Multi-language SAST |
| `nmap` / `masscan` | Port scanning |
| `openssl` | TLS, certificates |
| `jq` | JSON API parsing |
| `sqlite3` / `psql` | Local DB inspection |
| `docker` | Isolated environments |

---

## Verification

## ✅ Post-patch validation checklist

- [ ] Re-run Phase 3 (live) on every fixed finding
- [ ] Verify complete security headers
- [ ] Confirm effective rate-limiting (test 10+ requests)
- [ ] Test CORS with a malicious origin
- [ ] Verify CSRF on all POST requests
- [ ] Scan dependencies (`npm audit`, `composer audit`)
- [ ] Commit + green CI

---

## Out of Scope

- [ ] NOT in scope: anything not listed in the audit scope or the associated infrastructure (Docker, DB, reverse proxy).

---

*This skill is used by loading `security-analysis-methodology` and then following the 5 phases. It produces a full report in `~/Documents/audit-<target>-<date>.md` with evidence, CVSS, patches, and prioritization.*