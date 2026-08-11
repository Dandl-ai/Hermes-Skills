---
name: PhpMySqlWebAppPenetrationTesting
description: "Audit of PHP/MySQL web apps: code review, bot challenges, privilege escalation."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]
metadata:
  hermes:
    tags: [Security, PHP, Pentest, Audit, XSS, SQL, CSRF]
    related_skills: [github-code-review, systematic-debugging]
---

# PHP/MySQL Web Application Security Audit

Complete methodology for auditing a PHP/MySQL application (typically framework-less): static code review, active online testing, bypassing anti-bot challenges, and privilege escalation. Drawn from a complete real-world audit (TargetApp project, PHP 8.3, MySQL, InfinityFree hosting).

## Triggers

## When to Use
- The user asks to "check the security", "audit", or "find vulnerabilities" in a GitHub repo plus a test server
- Legacy PHP/MySQL project with sessions, POST forms, and an admin panel
- A live site serves a JS challenge (cookie `__test`) before the application

## Golden rules (learned the hard way)
1. **Always ask for confirmation before any active action** on a third-party server (the user prefers to be consulted).
2. **Never fake a success**: if some access is missing (FTP/DB), state it clearly. FTP/DB credentials are not meant to be guessed.
3. **Stay within the authorized scope** (the owner's test server only).
4. Document each piece of evidence (HTTP status, response excerpt) for every vulnerability.

## Phase 1 — Code reconnaissance (static, without touching the server)

```bash
git clone --depth 1 https://github.com/OWNER/REPO.git /tmp/audit && cd /tmp/audit
```

### 1.1 Map of sensitive files
```bash
find . -type f -not -path '*/.git/*' | sed 's|^\\./||' | sort
```

### 1.2 Dangerous patterns (RCE, inclusions, secrets)
```bash
grep -rn --include=*.php -E "eval\\(|system\\(|exec\\(|shell_exec|passthru|assert\\(|unserialize\\(|file_put_contents|fwrite" .
grep -rn --include=*.php -E "include.*\\$(GET|POST|REQUEST)|require.*\\$(GET|POST|REQUEST)" .   # LFI ?
```

### 1.3 SQL queries: prepared or concatenated?
```bash
grep -rn --include=*.php -E "->query\\(|->exec\\(|\\$bdd->query" .   # suspect si input utilisateur
grep -rn --include=*.php "prepare\\(\" .                              # bon signe
```

### 1.4 XSS encoding: look for echoes of raw variables
```bash
grep -rn --include=*.php -E "echo.*\\$(GET|POST|REQUEST|_SESSION)" . | grep -v htmlspecialchars
```

### 1.5 Access control (THE critical point of PHP home-grown apps)
```bash
# For each action file: does it have its own internal guard?
for f in $(find . -name '*Action.php'); do
  g=$(grep -cE "securityAction|securityAdminAction|grade" "$f")
  echo "$g  $f"
done | sort -rn
# ⚠️ Si une action n'a PAS de garde, elle dépend de la page qui l'inclut
#    → vérifier l'ORDRE : le require est-il AVANT le check de grade ?
#    → vérifier l'accès DIRECT : POST /actions/xxx.php sans session
```

### 1.6 Exposed installers / config pages
```bash
ls configuration.php install.php setup.php 2>/dev/null
grep -rn --include=*.php "file_put_contents.*database\\|preg_replace.*\\\\\\$\\$\" .  # écriture de config via formulaire = RCE
```

### 1.7 CSRF: do the forms have a token?
```bash
grep -rn --include=*.php "csrf\\|_token\\|nonce" . | head
```

### 1.8 SQL file: default passwords, seeded accounts
```bash
grep -niE "INSERT INTO users|password|mdp|grade" actions/*.sql 2>/dev/null | head -30
```

## Phase 2 — Server reconnaissance (passive, then lightly active)

### 2.1 Headers + TLS + banner
```bash
curl -sI https://domain/ | grep -iE "server|strict|frame|content-type|cookie"
openssl s_client -connect domain:443 -servername domain </dev/null 2>/dev/null | grep -E "subject:|Verify"
```

### 2.2 Ports (light)
```bash
nmap -Pn --top-ports 30 -T3 --open domain
```

### 2.3 Check known files in production
```bash
for p in /configuration.php /adminer.php /phpmyadmin/ /.git/config /actions/database.php /backup.sql; do
  curl -s -o /dev/null -w "$p -> %{http_code}\\n" "https://domain$p"
done
```

### 2.4 Quick PHP error test
```bash
curl -s "https://domain/page.php?s=%00" | grep -iE "Fatal error|Warning|Notice"
```

## Phase 3 — Bypassing a JS anti-bot challenge (slowAES)

Many free hosts (e.g. InfinityFree-style) serve a JS challenge before the app: a cookie `__test` = result of `slowAES.decrypt(c, 2, key, iv)`, redirecting to `/?i=N` at each step.

### Method (Node.js, no browser required)
1. Download the challenge's `/aes.js`
2. Load slowAES into a vm context, reproduce `toNumbers`/`toHex`
3. Loop: parse `a`, `b`, `c` from the HTML → decrypt → cookie → follow `location.href` → repeat until no challenge is found

Sample script (see `scripts/solve_js_challenge.js`).

**Pitfalls:**
- The challenge is **iterative** (a new ciphertext at each `/?i=N`) → loop, don't solve once
- nginx/openresty **rejects `<`, `>`, `"` in the path** (400) → no injection via URI; go through the POST body
- The rate-limit eventually **blacklists the IP** → space out requests, and expect the server to become unreachable (000) after ~30 close requests

## Phase 4 — Typical privilege-escalation chains (home-grown PHP apps)

### 4.1 Empty database = first registrant becomes admin
Many apps do: `if (users.count == 0) grade = 1`. If one can empty/observe the table (`count_data.php` without auth), register → **direct admin**.

### 4.2 DB credential leak via pre-filled form
Admin pages that display the DB config with `value="<?= $password ?>"` **disclose the MySQL password in clear text** to any admin. → full DB access → deletion/exfiltration/RCE.

### 4.3 Stored XSS in logs → admin session
If logs re-display user data **without encoding** and an admin views them (auto-refresh = bonus), a payload `<img onerror=fetch(...)>` can **promote the attacker's account** in the admin session. Verifiable chain: inject → verify the payload is stored (reflected from the database) → wait for the trigger.

### 4.4 Config rewrite via form (RCE)
`preg_replace` with unescaped POST values into a PHP file (e.g. `database.php`) = PHP injection → RCE, **if** a preliminary connection test can pass (leaked credentials = the key).

## Phase 5 — Deliverable

Structured report in a markdown file:
```
1. Executive summary + verdict
2. Critical (each vulnerability: file:line, code excerpt, evidence, complete fix)
3. Important / Minor
4. Positives (to keep)
5. Prioritized action plan (table # / action / priority / effort)
6. Hardening recommendations
```

Format for each vulnerability: **Problem → Evidence → Fix (copy-ready code)**. Do not be shy on the details (the user explicitly asks for it).

## Cross-cutting pitfalls
- **`$bdd` undefined**: action files called directly fail (500) because `database.php` is only included by the parent page → direct access is often NOT exploitable, verify this before asserting it
- **`if($x = true)`**: assignment instead of comparison = frequent logic bug (uniqueness check bypassed)
- **`while($x = false)`**: dead loops = misleading code
- **`crypt($pass, PASSWORD_DEFAULT)`**: incorrect use of crypt() (do not confuse with password_hash)
- **Session cookie**: look for `Secure`/`SameSite` in the Set-Cookie, `session_regenerate_id` after login
- **auto-generated username** (first 1st letter of first name + 7 letters of last name): to log in after signup, recompute the exact username, otherwise you get 200 instead of 302
- A **successful login = 302**, failure = 200 + message → username enumeration oracle via distinct messages

## Verification
- Each critical vulnerability must have **real evidence** (HTTP status, response excerpt, or a verified stored payload)
- The report ends with **per-file fixes with code** and a prioritized plan
- Clearly state what could NOT be done (missing access) — never fake a success

## Out of Scope
- Non-PHP stacks (Node.js, Python, Java, etc.) and non-MySQL databases
- Automated scanner-only runs (e.g. a bare OWASP ZAP / wpscan sweep) as a substitute for the manual methodology
- Remediation implementation: this skill finds and documents fixes but does not apply them
- Reporting/deliverable structure beyond this skill's outline (detailed client-facing reports live in another skill)
- Legal and authorization advice — always secure explicit permission and confirm scope before any active testing