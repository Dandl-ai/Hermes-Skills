---
name: Skill-Authoring-Craft
description: "Author high-quality Hermes skills: structure, triggers, pitfalls, verification."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Skills, Authoring, Meta, Documentation, Best-Practices, Anonymity, Privacy, OPSEC]
    related_skills: [hermes-agent-skill-authoring, SkillLibraryGitHubRelease]
---

# Skill Authoring Craft

How to write Hermes skills that are actually effective: correctly structured, reliably triggered, easy for an agent to follow, and free of the failures that (re)discovery repeatedly exposes. This is a meta-skill — it teaches how to author other skills.

## When to Use

- Creating a new skill for the first time.
- Reviewing or improving an existing skill that underperformed (never triggered, confusing steps, missing pitfalls).
- Standardizing skills across a team, a project, or a personal library.
- Before converting a real-world workflow (e.g. an audit or a deployment) into a reusable skill.

## The Purpose of a Skill

A skill is **procedural memory**: it lets a future agent reproduce a proven workflow without rediscovering it. It is not documentation, not a wiki page, not a tutorial. Everything in the file should exist to make the *execution* of the workflow more reliable and faster.

Write skills for the **cold-start agent**: the version of you that has none of the context you have now. If it can run the workflow from the file alone, the skill works.

## File Structure

```
skill-name/
├── SKILL.md              # mandatory: frontmatter + body
├── scripts/              # optional: reusable scripts/binaries
├── references/           # optional: long reference material
└── templates/            # optional: scaffolding files
```

### The frontmatter (recipe for detection)

```yaml
---
name: skill-name                              # lowercase, kebab-case, descriptive
description: "Verbe au présent + contexte du déclenchement. Max ~160 chars."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos]                     # only where it genuinely applies
metadata:
  hermes:
    tags: [Domain, Category, Adjacent-Terms]
    related_skills: [other-skill-a, related-skill-b]
---
```

Detection rules (critical):
- The **name** must be lowercase kebab-case (e.g. `my-first-skill`), ≤ 64 chars.
- The **description** is the main trigger. Front-load it with the exact situation it applies to. Generic descriptions like "useful tool" get misfiled and never matched.
- Tags are searchable synonyms: include the verb, the nouns, the framework, and the edge-case wording a user might type.
- Every frontmatter line matters. Omit none.

## The Body — A Proven Structure

Order the sections the way an agent actually executes:

1. **Title + one-line purpose.** State plainly what the workflow achieves.
2. **When to Use** (triggers). Exact conditions, in a checklist or bullets with concrete examples of matching user language.
3. **Golden Rules / Pitfalls (learned the hard way).** Put the biggest failure modes up top, before the steps. These prevent the agent from repeating history.
4. **Numbered phases/steps.** Break the workflow into sequential, named phases. Each step: one actionable sentence, then the exact commands.
5. **Verification.** How to confirm each phase really worked (status codes, output to grep, files to check for non-empty). This is what separates a script from a skill.
6. **Out-of-scope / edge cases.** What this skill deliberately does NOT handle and what to do instead.

### Writing rules that measurably improve outcomes

- **Commands above prose.** Prefer verbatim, copy-pasteable shell/curl/python blocks over describing what to do. Agents execute code more reliably than instructions.
- **Be prescriptive, not descriptive.** "Run X" beats "it is common to consider running X". Give the agent orders, not options.
- **Every step → a verification signal.** If a step cannot be verified, it is not a reliable step.
- **Prefer action verbs in headings** (`Map the surface`, `Exploit`, `Escalate`) over nouns (`Surface`, `Exploitation`).
- **Never hand-wave auth or prerequisites.** If the workflow needs a token, a tool, or a permission, list the exact command to obtain/check it.
- **Keep prose tight.** For each paragraph ask: "does this help a cold-start agent execute?" If it only explains rationale without changing behavior, cut it or move it to a reference.
- **Use tables** for checklists, mappings, and status-to-action tables. They compress decisions.

## Command-Line Authority, Honesty, and Safety

These three rules are non-negotiable in skills that touch systems or the network:

1. **Ask before active actions on third-party/remote targets.** If the skill triggers active scanning or exploitation, it MUST instruct the agent to request confirmation from the user first. The user decides scope.
2. **Never fake success.** If a step requires access that is missing (credentials, volumes, permissions), the skill must instruct the agent to say so plainly rather than invent a fabricated result.
3. **Document every proof.** When a finding claims success (HTTP status, response snippet, file output), the skill should require capturing that evidence verbatim.

## Long Material → References, Not the Body

If a section is long but rarely read inline (full checklists, historical findings, large config snapshots), split it into `references/<topic>.md` and link it: `see references/<topic>.md`. The body stays scannable; the detail is one `skill_view(name, file_path)` away.

- Use `references/` for reference data (checklists, findings, catalogs).
- Use `scripts/` for anything executable the agent should run verbatim.
- Use `templates/` for files the workflow scaffolds.
- A skill with `scripts/` must explicitly tell the agent **when and how** to call them — a script with no calling instruction is dead weight.

## Anonymity in Skills

Skills are often derived from **real engagements** — a real web app, a live server, a specific platform, test accounts. Before publishing anywhere (especially GitHub, public or private), a skill must be scrubbed so it reveals nothing about the actual target or author that was not already public. This section is **mandatory** when a skill contains reconnaissance, exploitation, or hosting steps tied to a real project.

### Why it matters
- A "cleaned" repo with one leftover domain or IP hands future attackers a live target and how to hit it.
- Real identifiers in example commands get copied by agents and copied again — a single leak propagates.
- The cost of a re-release is low only if anonymization is built into the authoring step, not bolted on after the leak.

### Identifiers to scan for (before and after authoring)
| Class | Example | Safe placeholder |
|---|---|---|
| Real domain | `myapp.realprovider.gd` | `target-app.example.org` |
| Real IP | `203.0.113.x` or actual public IP | `192.0.2.1` (TEST-NET) |
| Real repo | `github.com/Owner/Repo` | `github.com/acme/target-app` |
| Real commit | `a1b2c3d` | `abc1234` |
| Project name | `ExampleApp` | `target-app` |
| Platform/vendor | `AcmeCorp`, `PIX` | `acme-platform` |
| Real test account | `jdoe`, `trial01` | `testuser` |
| Real username / home | `/home/alice` | `~/` or `$HOME` |
| Hosting provider tied to target | specific `*.gd` host | generic "free host" |

### Anonymization rules (learned the hard way)
1. **Anonymize BEFORE writing, and re-scan after every edit.** The final scan is non-negotiable.
2. **Use ordered replacements, longest/most-specific first** — the full URL before the bare repo name, the domain before the project name. A broad rule applied early will destroy a specific replacement applied later.
3. **Do not translate code.** Swap only the *target values*; never alter commands, shell variables, URLs, or endpoints — those must stay functionally correct for whoever reuses the technique.
4. **Use word-boundary matching** for bare names (`\bExampleApp\b`) to avoid partial-rewrite corruption (`book`/`binder` colliding).
5. **Structured IPs go to reserved documentation ranges** (`192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24` — RFC 5737 TEST-NET) so a reviewer instantly recognizes a placeholder.
6. **Scrub even the anonymization skill itself.** The meta/examples you write may embed the very names you are trying to remove — re-scan your own instructions and example tables.
7. **Strip real secrets rather than soften them.** A real `password=` or API key from an install must be deleted, not replaced with a closer one.

### Verification scan (copy-paste into your authoring loop)
```bash
cd /path/to/skills
grep -rniE "real-host|real-owner|real-project|203\.0\.113|[0-9]{1,3}(\.[0-9]{1,3}){3}" \
  --include="*.md" --include="*.js" --include="*.sh" --include="*.yml" --include="*.html" . \
  || echo "CLEAN — no real identifiers remaining"
```

### Added to the publishing checklist
- [ ] No real domains, IPs, repos, commit hashes, project/vendor names, test accounts, or user home paths anywhere.
- [ ] Placeholder IPs are from a reserved TEST-NET range (`192.0.2.0/24`, etc.).
- [ ] Re-scan run AFTER the final write, not just before.

## Pitfalls (learned from real skill failures)

- **Massive single SKILL.md.** Files beyond a few hundred lines become unreadable and the agent fights the token budget. Split to references.
- **Vague triggers.** If the description/tags don't match how users phrase the request, the skill never loads. Re-read from the user's vocabulary.
- **Commands assumed installed.** State the install command or a preflight check (`command -v X`) at the start.
- **No verification step.** Skills that "did the thing" with no output to check produce unverifiable claims and false confidence.
- **Translating commands/URLs/variables.** Never translate commands, env vars, or URLs when localizing a skill — only prose.
- **Claiming breadth it doesn't have.** A skill that lists every scenario but only covers one creates over-triggering. Scope it honestly.
- **Stale after an upgrade.** When a tool's CLI or an API changes, the skill degrades silently. Add a note on where to re-verify.

## Verification Before Publishing

Before you (or the agent) consider a skill done, run this checklist:

- [ ] `description` names the exact trigger in the first ~110 chars.
- [ ] `name` is lowercase kebab-case, ≤ 64 chars.
- [ ] Every command can run from a cold shell (deps/preflight handled).
- [ ] Every step has a verification signal (exit code, grep-able output, file existence).
- [ ] Confirmation-before-active-action instructions present where scope matters.
- [ ] Long content is split into `references/` and linked.
- [ ] No secrets, no real credentials in the file.
- [ ] A human could hand this file to a fresh instance and get the workflow working.

## Out of Scope

This skill does not cover Hermes-specific CLI, config, or theming quirks — for those see the `hermes-agent` skill. It focuses purely on authoring quality SKILL.md files.