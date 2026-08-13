---
name: skill-anonymizer
description: "Enforce strict anonymization of Hermes skills before publishing — scan for real domains, IPs, emails, tokens, UUIDs, timestamps, usernames, paths, and project-specific identifiers, then replace them with safe placeholders."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Skills, Anonymity, Meta, OPSEC, Privacy, Publishing, Security]
    related_skills: [Skill-Authoring-Craft, SkillLibraryGitHubRelease]
---

# Skill Anonymizer

Enforce strict, verifiable anonymization of Hermes skills before publishing. This skill goes beyond the basic anonymization section in `Skill-Authoring-Craft` — it provides an exhaustive identifier taxonomy, an automated Python scanner, and a step-by-step redaction protocol with re-verification gates.

## When to Use

- Before publishing a skill to any external destination (GitHub, shared repo, team wiki).
- After authoring or editing a skill derived from a real engagement (pentest, audit, deployment, investigation).
- When auditing an existing skill library for identifier leaks.
- The user says "anonymize", "sanitize", "redact", "scrub", "OPSEC check", or "before publishing".

## Why This Exists

`Skill-Authoring-Craft` covers anonymization in ~40 lines. That is enough for simple skills. It is NOT enough when a skill contains:

- Timestamps that reveal the engagement date
- UUIDs, simulation IDs, report IDs tied to a real system
- Environment variable names specific to a project (e.g. `APP_DB_HOST` that maps to a real project name)
- API proxy domains that reveal the upstream provider chain
- File metadata (git author, file ownership, extended attributes)
- Non-English identifiers (Chinese, French project names)
- Mock data that is too close to the real data

One missed identifier is enough to de-anonymize the entire skill. This skill makes the scan **systematic and automatable**.

## Identifier Taxonomy

Every category below MUST be scanned. "Found zero" is only valid after the scanner confirms it.

### 1. Network Identifiers

| Class | Pattern | Safe Placeholder |
|---|---|---|
| Domain | `foo.target.test` | `target-app.example.org` |
| Subdomain | `api.example.com` | `api.example-proxy.com` |
| URL | `https://example.com/path` | `https://example.com/path` (keep path, swap domain) |
| IPv4 | Any non-reserved public IP | `192.0.2.N` (RFC 5737 TEST-NET-1) |
| IPv6 | Any non-reserved IPv6 | `2001:db8::N` (RFC 3849 documentation range) |
| Port | Non-standard ports tied to a service | Keep if generic (80, 443, 5432); replace if custom |

### 2. Credentials & Secrets

| Class | Pattern | Action |
|---|---|---|
| API keys | `sk-...`, `AIza...`, long hex/alphanumeric strings | Delete entirely, replace with `***` |
| Bearer tokens | `Bearer eyJ...` | Delete, replace with `***` |
| Passwords | `password=...`, `passwd ...` | Delete, replace with `***` |
| `.env` values | Any `KEY=VALUE` where VALUE is non-placeholder | Replace VALUE with `***` or `your-key-here` |
| Connection strings | `postgresql://user:***@host:port/db` | `postgresql://user:***@host:port/db` |
| SSH fingerprints | `SHA256:...` | Delete |
| Cloud account IDs | 12-digit numeric (AWS), numeric (GCP, Azure) | `123456789012` (AWS docs convention) |

### 3. Personal Identifiers

| Class | Pattern | Safe Placeholder |
|---|---|---|
| Real name | `author: john` | `author: anonymized` |
| Email | `user@target.test` | `user@example.com` |
| Username / handle | `@johndoe` | `@testuser` |
| Home directory | `/home/alice` | `~/` or `$HOME` |
| Real path | `/opt/project-foo` | `~/project/` or `/path/to/project/` |
| Git author | `John Doe <john@acme.test>` | `Anonymized <anon@example.com>` |

### 4. Project-Specific Identifiers

| Class | Pattern | Safe Placeholder |
|---|---|---|
| Project name | `MyApp`, `ProjectFoo` | `target-app` or `example-project` |
| Vendor / platform | `AcmeCorp`, internal codenames | `acme-platform` or `the-platform` |
| Repo URL | `github.com/Owner/Repo` | `github.com/acme/target-app` |
| Commit hash | `a1b2c3d` | `abc1234` |
| Simulation/run IDs | `sim_a1b2c3d4e5f6` | `sim_example01` |
| Report IDs | `report_a1b2c3d4e5f6` | `report_example01` |
| Graph IDs | `graph_a1b2c3d4e5f6` | `graph_example01` |
| Task UUIDs | `a1b2c3d4-5678-...` | `00000000-0000-0000-0000-000000000001` |
| DB table names | `appname_users` | `app_users` |
| Env var names | `FOO_DB_HOST`, `BAR_API_KEY` | `APP_DB_HOST`, `EXAMPLE_API_KEY` |

### 5. Temporal Identifiers

| Class | Pattern | Safe Placeholder |
|---|---|---|
| ISO timestamps | `2025-01-01T00:00:00` | `2025-01-01T00:00:00` |
| Unix timestamps | `1700000000` | `1700000000` |
| Date references | `2025-01-01` | `2025-01-01` |
| Relative dates tied to events | "on August 10" | "on the test date" |
| Log entry timestamps | `[2025-01-01 00:00:00]` | `[2025-01-01 00:00:00]` |

### 6. Linguistic Identifiers

| Class | Pattern | Action |
|---|---|---|
| Non-English project names | Chinese/Arabic/etc. names of real platforms | Translate to generic English equivalent |
| Real person names in any language | Non-English names | `TestUser`, `Anon User` |
| Real organization names | Specific NGOs, companies, agencies | Generic role (`the-regulator`, `the-vendor`) |
| Locales / timezones tied to author | `Europe/Paris`, `Asia/Shanghai` | `UTC` or generic `local-timezone` |

### 7. Metadata & Side-Channel

| Class | Pattern | Action |
|---|---|---|
| Git author config | `user.name`, `user.email` in git history | Use `git filter-branch` to rewrite |
| File ownership | `user:group` in tar/zip metadata | `xattr -cr` before archiving; use `tar --owner=0 --group=0` |
| Extended attributes | `xattr` containing paths/usernames | `xattr -cr` before distributing |
| Editor artifacts | `.vscode/`, `.idea/` with workspace paths | Exclude from publish or scrub |
| Comments in code | `# TODO for John`, `# FIXME: acme.com down` | Remove or anonymize |

## Redaction Protocol

Execute these steps in order. Do NOT skip the re-verification gate.

### Step 1 — Build the Identifier Map

Before changing anything, inventory all real identifiers in the skill:

1. Read every file (SKILL.md, references/*, scripts/*, templates/*).
2. For each file, list every match from the taxonomy above.
3. Build a mapping table: `real_value → placeholder_value`.
4. Order replacements **longest first** (full URL before domain before project name) to prevent partial-rewrite corruption.

### Step 2 — Apply Replacements

1. Use `sed -i` or the patch tool for each replacement, longest-first.
2. Use word-boundary matching (`\b...\b`) for bare names to avoid substring collisions (e.g. `book` matching inside `binder`).
3. Do NOT alter commands, shell variables, or URLs beyond swapping the target values — the skill must remain functionally correct.
4. Strip real secrets entirely — do not replace with a "looks-similar" fake, use `***` or `your-key-here`.

### Step 3 — Run the Automated Scanner

```bash
python3 scripts/skill_anonymizer.py --scan /path/to/skill/
```

The scanner reports every remaining match by category. Address every hit.

### Step 4 — Re-Verification Gate

After the scanner reports CLEAN:

1. Re-read the SKILL.md and all referenced files manually.
2. Run the scanner again with `--strict` (enables false-positive-sensitive patterns):
   ```bash
   python3 scripts/skill_anonymizer.py --scan --strict /path/to/skill/
   ```
3. If any hit remains, go back to Step 2.

### Step 5 — Git History Check (if publishing to GitHub)

```bash
cd /path/to/skills-repo
git log --all --format='%an <%ae>' | sort -u
git log --all --format='%cn <%ce>' | sort -u
```

If real names/emails appear in commit history, rewrite before pushing:

```bash
git filter-branch --env-filter '
export GIT_AUTHOR_NAME="Anonymized"
export GIT_AUTHOR_EMAIL="anon@example.com"
export GIT_COMMITTER_NAME="Anonymized"
export GIT_COMMITTER_EMAIL="anon@example.com"
' --tag-name-filter cat -- --all
```

### Step 6 — Final Metadata Check

```bash
# File permissions (should not reveal user)
stat -c '%a %U:%G %n' /path/to/skill/**
# Extended attributes
xattr -l /path/to/skill/** 2>/dev/null || echo "No xattrs"
# Editor artifacts
find /path/to/skill -name '.vscode' -o -name '.idea' -o -name '*.swp' -o -name '.DS_Store'
```

## Golden Rules

1. **Anonymize before writing, re-scan after every edit.** The final scan is non-negotiable.
2. **Longest/most-specific replacements first.** Full URL before bare domain before project name.
3. **Word-boundary matching for bare names** to prevent substring corruption.
4. **Use RFC-reserved ranges for IPs** (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` for IPv4; `2001:db8::/32` for IPv6) so reviewers instantly recognize placeholders.
5. **Strip real secrets, do not soften them.** `password=hunter2` → delete entirely, not `password=hunter3`.
6. **Scrub the anonymizer skill itself.** The examples in this file may embed the very names you are trying to remove — re-scan your own instructions.
7. **Never translate commands, env vars, or URLs.** Swap only target values; keep functional correctness.
8. **Temporal identifiers count.** A timestamp `2025-01-01T00:00:00` is as identifying as a domain name.
9. **Git history is a side channel.** `git log` author/email metadata persists across clones — rewrite before publishing.

## Pitfalls

### P1 — Substring collision during replacement
**Problem:** Replacing `book` corrupts `binder` and `bookmark`.
**Fix:** Use `\bbook\b` word-boundary matching. Always test replacements on a copy first.

### P2 — UUIDs and run IDs missed
**Problem:** `sim_a1b2c3d4e5f6` looks like a generic hex string and gets ignored.
**Fix:** The scanner treats any `<prefix>_<hex{8+}>` pattern as a potential identifier. Review each hit manually.

### P3 — Timestamps in JSONL or log examples
**Problem:** `"timestamp": "2025-01-01T00:00:00.000000"` in example data reveals the engagement date.
**Fix:** Replace all ISO timestamps with a fixed placeholder date. The scanner flags ISO 8601 patterns.

### P4 — Proxy chains revealing upstream providers
**Problem:** `.env` says `api.example-proxy.com` but an error message in the skill body mentions the upstream provider by name — revealing the proxy's backend.
**Fix:** Scan for upstream provider names in error messages and error-handling sections. Replace with "the upstream provider" or "the backend model service".

### P5 — Non-English identifiers
**Problem:** A Chinese platform name or French tool name passes regex filters designed for ASCII.
**Fix:** The scanner includes Unicode-aware patterns. Additionally, manually review content in non-English languages.

### P6 — Git history leaks after publishing
**Problem:** Files are anonymized but `git log --format='%an'` still shows the real author name.
**Fix:** Run the git history check (Step 5) BEFORE the first push. Rewriting history after others have cloned is destructive.

### P7 — False positives in the scanner
**Problem:** The scanner flags `example.com` (already a placeholder) or `192.0.2.1` (TEST-NET).
**Fix:** The scanner excludes RFC-reserved ranges and common placeholder patterns. For custom false positives, use `--allowlist patterns.txt` to suppress known-safe matches.

## Verification

Before considering a skill anonymized:

- [ ] Scanner reports CLEAN (zero hits) on all files
- [ ] Scanner reports CLEAN on `--strict` mode
- [ ] No real domains, IPs, emails, tokens, UUIDs, or timestamps in any file
- [ ] Placeholder IPs are from RFC reserved ranges
- [ ] Placeholder dates use a fixed neutral value (e.g. `2025-01-01`)
- [ ] Git history author/committer shows anonymized identity
- [ ] No editor artifacts (`.vscode/`, `.idea/`, `.DS_Store`)
- [ ] No extended attributes on files
- [ ] Manual re-read of SKILL.md + all referenced files finds nothing

## Out of Scope

- Authoring the skill content itself (see `Skill-Authoring-Craft`)
- Publishing workflow (see `SkillLibraryGitHubRelease`)
- Hermes-specific CLI configuration (see `hermes-agent`)
- Legal compliance (GDPR, CCPA) — this skill handles technical anonymization of skill files only, not legal data protection
