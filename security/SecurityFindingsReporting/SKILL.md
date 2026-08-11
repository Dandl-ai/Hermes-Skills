---
name: SecurityFindingsReporting
description: "Reporting pack: findings, CVSS, evidence, patches, tracking."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Security, Reporting, Evidence, CVSS, Documentation]
    related_skills:
      - DynamicRuntimeSecurityAnalysis
      - FullStackWebSecurityReview
      - WebInvestigationMethodology
---

## When to Use

Use this skill when you need to:

- Document security vulnerabilities
- Generate a full audit report
- Track vulnerabilities through their discovery, remediation, and verification lifecycle
- Produce standardized findings with CVSS scoring, evidence, and patches

## Prerequisites

- Markdown, git tooling
- CVSS v3.1 knowledge
- Access to the target, the vulnerable artifacts, and the evidence to be reported

## Golden Rules / Pitfalls

- **Evidence over assertion** — every finding must carry timestamped proof (curl output, headers, code, diff). A report without evidence is an opinion, not a finding.
- **One finding per ID** — use the `CUSTOM-YYYY-NNN` scheme consistently across `finding-template.md`, `findings.csv`, and `findings.json`, so tracking stays aligned across all deliverables.
- **Score the CVSS, never guess it** — calculate CVSS v3.1 from the actual vector, not the title's severity. The severity label and the CVSS score must match.
- **Keep the timeline complete** — record discovery → triage → fix → verify. A finding with no verification date is still open, regardless of the claimed status.
- **Never invent references** — only link CWE/OWASP/CVE entries you actually confirmed; a placeholder CVE in a delivered report is a defect.
- **Preserve raw evidence verbatim** — store the collector's raw output unchanged (no redaction that hides the proof). Anonymize only credentials/sensitive tokens, and note the redaction.
- **Don't report damage as success** — distinguish expected vs observed result in the PoC; an "observed = expected" marker must genuinely reproduce the issue.

## 📦 Reporting & Evidence Pack

### 1. Standardized Finding Template

#### `finding-template.md`
```markdown
## [CUSTOM-YYYY-NNN] Short Vulnerability Title

**Severity** : Critical / Major / Minor / Info
**CVSS v3.1** : [Score] - [Vector String]
**Status** : Open / In Progress / Fixed / Won't Fix / False Positive
**Discovered** : YYYY-MM-DD
**Target** : [App / API / Endpoint / Component]
**Affects** : [Versions / Environments]

---

### Description
Clear technical description of the vulnerability.

### Location
- **File** : `path/to/file.php:123`
- **Endpoint** : `POST /api/v1/login`
- **Parameter** : `username` / `password` / `csrf_token`

### Proof of Concept (PoC)
```bash
curl -X POST https://target.com/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin'--&password=anything"
```

**Expected result** : HTTP 200 + admin session
**Observed result** : HTTP 200 + admin session ✓

### Business Impact
- **Confidentiality** : Access to user data / database
- **Integrity** : Data modification/deletion
- **Availability** : DoS, service destruction
- **Compliance** : GDPR, PCI-DSS, ISO 27001

**Real-world attack scenario** :
1. Attacker sends payload...
2. System executes...
3. Attacker obtains...

### Root Cause
Technical explanation: missing validation, unprepared query, etc.

### Remediation
#### Code Fix
```diff
- $query = "SELECT * FROM users WHERE username = '$username'";
+ $stmt = $pdo->prepare("SELECT * FROM users WHERE username = ?");
+ $stmt->execute([$username]);
```

#### Configuration
```ini
display_errors = Off
expose_php = Off
session.cookie_secure = 1
session.cookie_httponly = 1
session.cookie_samesite = "Lax"
```

#### Validation Tests
- [ ] Unit test: SQL injection blocked
- [ ] Integration test: normal login works
- [ ] Regression test: no regressions

### References
- [CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
- [OWASP A03:2021 Injection](https://owasp.org/Top10/A03_2021-Injection/)
- [CVE-XXXX-XXXX](https://nvd.nist.gov/vuln/detail/CVE-XXXX-XXXX)

---

### Tracking
| Date | Author | Action | Comment |
|------|--------|--------|-------------|
| YYYY-MM-DD | [Name] | Created | Initial discovery |
| YYYY-MM-DD | [Name] | Triaged | Confirmed Critical |
| YYYY-MM-DD | [Dev] | Fixed | PR #123 merged |
| YYYY-MM-DD | [Sec] | Verified | Retest OK |
```

### 2. CSV/JSON Tracking File

#### `findings.csv`
```csv
ID,Title,Severity,CVSS,Status,Component,File,Line,Discovered,Fixed,Verified
CUSTOM-2024-001,SQL Injection Login,Critique,9.8,Fixed,Auth,login.php,45,20XX-XX-XX,20XX-XX-XX,20XX-XX-XX
CUSTOM-2024-002,XSS Stored Comments,Majeur,7.1,Open,Comments,comment.php,112,20XX-XX-XX,,,
CUSTOM-2024-003,Weak JWT Secret,Mineur,5.3,In Progress,Auth,config.php,12,20XX-XX-XX,,,
```

#### `findings.json`
```json
{
  "audit": "TargetApp-20XX-XX-XX",
  "target": "https://target-app.example.org",
  "date": "20XX-XX-XX",
  "scope": ["Web App", "API", "Database"],
  "findings": [
    {
      "id": "CUSTOM-2024-001",
      "title": "SQL Injection in Login",
      "severity": "Critical",
      "cvss": {"score": 9.8, "vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"},
      "status": "Fixed",
      "component": "Authentication",
      "location": {"file": "actions/users/loginAction.php", "line": 45},
      "description": "Username parameter not sanitized in prepared statement",
      "poc": "curl -X POST ... -d \"username=admin'--&password=x\"",
      "impact": "Full authentication bypass, admin access",
      "root_cause": "Direct string concatenation in SQL query",
      "remediation": "Use prepared statements with parameter binding",
      "patch": "PR #123",
      "references": ["CWE-89", "OWASP A03"],
      "timeline": {"discovered": "20XX-XX-XX", "fixed": "20XX-XX-XX", "verified": "20XX-XX-XX"}
    }
  ],
  "summary": {"critical": 2, "high": 3, "medium": 5, "low": 8, "total": 18}
}
```

### 3. Full Report Generator

#### `generate-report.sh`
```bash
#!/bin/bash
AUDIT_DIR="${1:-.}"
REPORT_FILE="audit-report-$(date +%Y%m%d).md"
HTML_FILE="audit-report-$(date +%Y%m%d).html"

cat > "$REPORT_FILE" << EOF
# 🔒 Security Audit Report

**Target** : $TARGET
**Date** : $(date +%Y-%m-%d)
**Auditor** : $AUDITOR
**Scope** : $SCOPE

## Executive Summary

| Metric | Value |
|----------|--------|
| Overall Score | $SCORE/10 |
| Critical | $CRIT_COUNT |
| High | $HIGH_COUNT |
| Medium | $MED_COUNT |
| Low | $LOW_COUNT |

## Findings

EOF

for f in findings/*.md; do
  cat "$f" >> "$REPORT_FILE"
  echo -e "\n---\n" >> "$REPORT_FILE"
done

if command -v pandoc &> /dev/null; then
  pandoc "$REPORT_FILE" -o "$HTML_FILE" --toc --number-sections
  echo "✅ HTML generated: $HTML_FILE"
fi

echo "✅ Report generated: $REPORT_FILE"
```

### 4. Evidence Collector

#### `evidence-collector.sh`
```bash
#!/bin/bash
FINDING_ID="${1:-CUSTOM-2024-001}"
EVIDENCE_DIR="evidence/$FINDING_ID"
mkdir -p "$EVIDENCE_DIR"

curl -v -X POST https://target.com/api/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin'--&password=x" \
  > "$EVIDENCE_DIR/request-response.txt" 2>&1

curl -s -I https://target.com/ > "$EVIDENCE_DIR/security-headers.txt" 2>&1

curl -s -H "Origin: https://evil.com" -D - -o /dev/null https://target.com/ \
  > "$EVIDENCE_DIR/cors.txt" 2>&1

openssl s_client -connect target.com:443 -servername target.com </dev/null 2>/dev/null \
  | openssl x509 -noout -text > "$EVIDENCE_DIR/tls-cert.txt"

cp /path/to/vulnerable/file.php "$EVIDENCE_DIR/vulnerable-code.php"
git diff HEAD~1 -- path/to/fixed/file.php > "$EVIDENCE_DIR/patch.diff"

tar -czf "evidence-$FINDING_ID-$(date +%Y%m%d).tar.gz" "$EVIDENCE_DIR"
echo "✅ Evidence archived: evidence-$FINDING_ID-$(date +%Y%m%d).tar.gz"
```

### 5. Tracking Dashboard

#### `dashboard.html`
```html
<!DOCTYPE html>
<html><head><title>Security Findings Dashboard</title>
<style>
  body{font-family:Arial,sans-serif;margin:20px}
  table{border-collapse:collapse;width:100%}
  th,td{border:1px solid #ddd;padding:8px;text-align:left}
  th{background:#333;color:white}
  .critical{background:#ffebee}.high{background:#fff3e0}.medium{background:#fffde7}.low{background:#e8f5e9}
  .open{font-weight:bold}.fixed{text-decoration:line-through;color:#666}
</style></head><body>
<h1>🔒 Security Findings Dashboard</h1>
<table id="findings"><thead><tr>
  <th>ID</th><th>Title</th><th>Severity</th><th>CVSS</th><th>Status</th><th>Component</th><th>Discovered</th><th>Fixed</th>
</tr></thead><tbody></tbody></table>
<script>
fetch('findings.json').then(r=>r.json()).then(d=>{
  d.findings.forEach(f=>{
    const row=document.createElement('tr');
    row.className=f.severity.toLowerCase()+' '+f.status.toLowerCase();
    row.innerHTML=`<td>${f.id}</td><td>${f.title}</td><td>${f.severity}</td><td>${f.cvss?.score||'N/A'}</td><td>${f.status}</td><td>${f.component}</td><td>${f.timeline?.discovered||''}</td><td>${f.timeline?.fixed||''}</td>`;
    document.querySelector('#findings tbody').appendChild(row);
  });
});
</script>
</body></html>
```

---

## 🚀 Full Workflow

```bash
# 1. Create finding
cp finding-template.md findings/CUSTOM-2024-001.md

# 2. Collect evidence
./evidence-collector.sh CUSTOM-2024-001

# 3. Update tracking (findings.csv / findings.json)

# 4. Generate report
./generate-report.sh

# 5. Live dashboard
python3 -m http.server 8080
# http://localhost:8080/dashboard.html
```

---

## 📊 Standard Deliverables

| Deliverable | Format | Usage |
|----------|--------|-------|
| `audit-<target>-<date>.md` | Markdown | Main report |
| `audit-<target>-<date>.html` | HTML | Browser sharing |
| `findings.csv` | CSV | Jira/GitLab/Trello import |
| `findings.json` | JSON | API, dashboard, automation |
| `evidence-<ID>-<date>.tar.gz` | Archive | Timestamped evidence |
| `dashboard.html` | HTML | Real-time tracking |

---

## ✅ Report Quality Checklist

- [ ] Each finding has: ID, Title, Severity, CVSS, PoC, Impact, Remediation
- [ ] Timestamped evidence attached (curl, headers, code, diff)
- [ ] CVSS v3.1 correctly calculated
- [ ] CWE/OWASP/CVE references included
- [ ] Complete timeline (discovery → fix → verification)
- [ ] Executive summary with overall score
- [ ] Prioritized recommendations (P0, P1, P2, P3)
- [ ] Appendices: scope, methodology, tools, exclusions

---

## 📤 Out of Scope

- **Remediating or patching the code** — this skill documents findings and tracks fixes; it does not implement them.
- **Exploiting or weaponizing vulnerabilities** beyond the PoC required for verification — no persistence, no data exfiltration, no destructive actions.
- **Scanning, recon, or live exploitation** — use the dedicated audit skills (recon, SAST, runtime analysis) to *produce* findings; this skill only *reports and tracks* them.
- **Authoring the executive/business narrative** beyond the summary metrics — program-level risk scoring and strategic mitigation planning are out of scope.
- **Sharing or distributing the report** outside the intended, authorized recipients — distribution is the requester's responsibility.
- **Non-security tasks** — style/UX fixes, feature requests, or general documentation unrelated to vulnerabilities.

---

## ✅ Verification

Confirm the report is complete and evidence-backed before delivering:

- [ ] Every finding carries an ID (`CUSTOM-YYYY-NNN`), Title, Severity, CVSS v3.1 score **and** vector string, Status, PoC (expected vs observed), Business Impact, Root Cause, and Remediation.
- [ ] Each finding has timestamped, archived evidence (`evidence-<ID>-<date>.tar.gz`) whose contents match the PoC/observed result claimed.
- [ ] CVSS scores in `finding-template.md`, `findings.csv`, and `findings.json` are consistent with the severity labels and derived from real vectors, not guessed.
- [ ] All CWE/OWASP/CVE references resolve to real, verified entries (no placeholder `CVE-XXXX-XXXX` left in final output).
- [ ] The timeline is complete for each finding: discovered → triaged → fixed → verified. Any finding without a verified date is explicitly marked Open/In Progress.
- [ ] Cross-check reconciliation: `findings.csv`, `findings.json`, and the markdown findings all reference the same IDs, severities, and statuses.
- [ ] The generated report (`audit-report-<date>.md` / `.html`) includes an executive summary with the overall score and prioritized recommendations.
- [ ] No finding claims a fix without a verification entry showing the retest result.