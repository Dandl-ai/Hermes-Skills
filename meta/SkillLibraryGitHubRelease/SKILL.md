---
name: SkillLibraryGitHubRelease
description: "Publish a Hermes skill library to GitHub: anonymize, structure, git init."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [GitHub, Publishing, Skills, Anonymization, Open-Source, Release]
    related_skills: [Skill-Authoring-Craft, github-repo-management, github-auth]
---

# Skill Library GitHub Release

Take a local folder of Hermes skills and turn it into a clean, publication-ready GitHub repository: scan for and remove real-target identifiers, add the standard repository scaffolding, and initialise the git history — without leaking the actual systems, hosts, or credentials the skills were derived from.

## When to Use

- Publishing a personal skill library to GitHub (public or private).
- Anonymizing skills that reference a specific real web app, server, domain, or test account.
- Setting up a fresh repo skeleton (README + LICENSE + .gitignore) for a skills collection.
- Reviewing skills before release to avoid leaking internal details.

## Golden Rules / Pitfalls (learned the hard way)

1. **Anonymize BEFORE pushing, and re-scan after.** One leftover real domain or IP makes a "cleaned" repo dangerous. The verification scan is non-negotiable — never skip it.
2. **Do not rename the skills in `~/.hermes/skills/`** — Hermes references them by name. Only rename/copy in the target `Projets/Skills` folder.
3. **Keep commands, URLs, and variables verbatim** while renaming — only replace *real targets* with generic placeholders, never touch functional snippets.
4. **Use reserved test ranges for stripped IPs** (e.g. `192.0.2.0/24` TEST-NET) so a reviewer knows the value is a placeholder, not a guess.
5. **Use ordered replacements, longest/most specific first** (`github.com/Owner/Repo` before the bare project name) to avoid partial-rewrite corruption.
6. **Real secrets that cannot be safely placeholdered should be stripped, not hidden** — never commit a `password=` from a real install even as an example.

## Prerequisites

- `git` installed.
- Read/write access to the target skills folder.
- Optional: `gh` CLI for one-command repository creation (see Step 5).

## Phase 1 — Inventory

Identify which skills are yours to publish (not bundled Hermes skills). Compare against `~/.hermes/skills/.bundled_manifest`:

```bash
# List candidate custom skills (everything not in the bundled manifest)
cd ~/Projets/Skills
find . -name "SKILL.md" | sort
python3 - <<'PY'
import json
bundled = set()
for line in open('~/.hermes/skills/.bundled_manifest'):
    if '|' in line:
        bundled.add(line.split('|')[1])
print("Bundled skills:", len(bundled))
PY
```

## Phase 2 — Sensitive Scan

Scan every file (`.md`, `.js`, `.sh`, etc.) for real identifiers before writing anything:

```bash
cd ~/Projets/Skills
grep -rniE "password|secret|apikey[=:]|api_key|token|/home/[a-z]+|\.rf\.gd|\.fr( |\"|'|$)|github.com/[A-Za-z_]+/[A-Za-z_]+" . 2>/dev/null
```

Look specifically for: real domains, raw IPs, real GitHub repos + commit hashes, names of real platforms/projects, hardcoded credentials, and absolute home paths.

## Phase 3 — Anonymize (scripted)

Apply replacements with the most-specific-first ordering. Use a Python script with an ordered regex list so later broad rules cannot clobber earlier specific ones:

| Real | Safe placeholder |
|---|---|
| `https://github.com/Owner/Repo` | `https://github.com/acme/target-app` |
| `myapp.example.org` | `target-app.example.org` |
| real IP `203.0.113.x` | `192.0.2.1` (TEST-NET) |
| real commit `abc123def` | `abc1234` |
| project `my-app` | `target-app` |
| platform `my-platform` | `acme-platform` |

Rules for the replacement script:
- **Order longest/most-specific first.** Handle the full URL before the bare repo name, the domain before the project name.
- Use word-boundary regex for bare names (`\bPIX\b`) to avoid partial hits.
- **Do not translate** commands, shell variables, URLs, or code — only swap the real target values.

## Phase 4 — Rescan (verification)

Re-run the exact scan from Phase 2 and confirm **zero** matches for the real identifiers:

```bash
grep -rniE "my-real-app|my-host\.gd|real-owner|192\.0\.168|my-platform" . 2>/dev/null \
  || echo "CLEAN — no real identifiers remaining"
```

Tolerate only generic, non-identifying mentions (e.g. naming a generic class of free host, or `runs-on: ubuntu-latest`).

## Phase 5 — Structure + git init

Add the scaffolding and commit:

```bash
cd ~/Projets/Skills
git init -b main
git add -A
# Rename to pro names (PascalCase, distinct) + organise by category BEFORE committing
git commit -m "Initial release: Hermes Agent skill library"
git log --oneline -1
```

Scaffolding files required:
- `README.md` — table of contents, install instructions, license note.
- `LICENSE` — MIT (matching the skills' `license: MIT` frontmatter).
- `.gitignore` — exclude cache, secrets, node_modules, OS files.

Optional (if `gh` is available):
```bash
gh repo create <owner>/<repo> --public --source=. --push
```

## Verification

- [ ] Phase 4 rescan returned zero real identifiers.
- [ ] Every skill's `name` matches its directory (PascalCase).
- [ ] `related_skills` point only to skills that exist in the repo or in the installed Hermes library.
- [ ] `README.md`, `LICENSE`, `.gitignore` present.
- [ ] `git log` shows a clean initial commit; `git status` clean.
- [ ] No secret/credential strings anywhere.

## Out of Scope

- Actually authenticating/pushing to GitHub (depends on user's account/`gh`/SSH — ask, then run).
- Translating skill prose to another language (use a separate step).
- Writing new skills from scratch (see `Skill-Authoring-Craft`).