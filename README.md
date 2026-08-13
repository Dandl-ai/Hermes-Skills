<div align="center">

<h1>Hermes Skills</h1>

<h3>Procedural playbooks for&nbsp;<a href="https://hermes-agent.nousresearch.com">Hermes Agent</a></h3>

<p>
  Field-tested workflows — triggers, exact commands, pitfalls, and verification gates.<br/>
  No fluff, no theory. Just proven playbooks an agent can execute cold.
</p>

<br/>

<sub>Built from real engagements — web audits, deployments, multi-agent simulations. Refined through actual use, not written speculatively.</sub>

</div>

<br/>

## Install

```bash
git clone https://github.com/Dandl-ai/Hermes-Skills.git
cd Hermes-Skills

# Copy specific skills
cp -r security/FullStackWebSecurityReview ~/.hermes/skills/security/

# Or copy everything
cp -r * ~/.hermes/skills/
```

Skills are auto-detected by Hermes on startup — no registration needed.

<br/>

## Architecture

Each skill is a directory containing:

```
SkillName/
├── SKILL.md            # mandatory — frontmatter (name, triggers, tags) + structured body
├── scripts/            # optional — reusable scripts (Python, Node.js, bash)
└── references/         # optional — long reference material (checklists, API maps, formats)
```

The body follows a fixed structure:

| Section | Purpose |
|---|---|
| **When to Use** | Exact trigger conditions — matching user language, not generic keywords |
| **Golden Rules / Pitfalls** | Failure modes learned the hard way, placed before the steps |
| **Numbered Phases** | Sequential, named phases with verbatim commands |
| **Verification** | How to confirm each phase worked (status codes, output checks, file presence) |
| **Out-of-Scope** | What this skill deliberately does NOT handle |

<br/>

## 🧠 Meta

Skills about skills — authoring, anonymizing, and publishing.

| Skill | Description | Includes |
|---|---|---|
| [SkillAuthoringCraft](meta/SkillAuthoringCraft/) | How to write skills that work: frontmatter detection, body structure, verification gates | Template, detection rules, golden rules |
| [SkillAnonymizer](meta/SkillAnonymizer/) | Exhaustive anonymization before publishing: 8-category identifier taxonomy | `skill_anonymizer.py` scanner, redaction protocol, allowlist |
| [SkillLibraryGitHubRelease](meta/SkillLibraryGitHubRelease/) | Turn a local skills folder into a clean, publication-ready GitHub repo | Sensitive scan, ordered anonymization, repo scaffolding |

<br/>

## 🔒 Security

A complete web application audit pipeline — from methodology to exploitation to reporting.

| Skill | Description | Includes |
|---|---|---|
| [WebInvestigationMethodology](security/WebInvestigationMethodology/) | Master methodology: 5-phase audit workflow (recon → SAST → live testing → business logic → reporting) | Checklist, tool requirements |
| [FullStackWebSecurityReview](security/FullStackWebSecurityReview/) | Two-phase review: static code analysis then live server recon | PHP checklist, JS anti-bot bypass, live findings template |
| [OffensiveAuditOrchestration](security/OffensiveAuditOrchestration/) | Control layer: risk classification, multi-agent routing, budget tracking, stopping criteria | Parallel agent coordination (max 3 children) |
| [StaticApplicationSecurityTesting](security/StaticApplicationSecurityTesting/) | SAST pack: semgrep rules, custom greps, CI/CD code audit | Dangerous function patterns, SQLi/XSS sink detection |
| [DynamicRuntimeSecurityAnalysis](security/DynamicRuntimeSecurityAnalysis/) | Runtime analysis: live recon, auth probing, rate-limit, CORS, headers | Probing checklist for post-static-review |
| [PhpMySqlWebAppPenetrationTesting](security/PhpMySqlWebAppPenetrationTesting/) | Hands-on PHP/MySQL pentest: code review, bot bypass, privilege escalation | `solve_js_challenge.js` solver script |
| [OidcPkceAuthorizationCode](security/OidcPkceAuthorizationCode/) | OIDC Authorization Code + PKCE (RFC 7636) implementation | Route + model code, timing-safe comparisons |
| [SecurityFindingsReporting](security/SecurityFindingsReporting/) | Structured reporting: CVSS scoring, PoC format, evidence traceability | Finding template, patch format, tracking |
| [WebPentestToolkit](security/WebPentestToolkit/) | Web pentest pipeline: nmap, httpx, ffuf, nuclei, sqlmap, semgrep, hydra, john | Quick reference for 9 tools, pipeline procedure, pitfalls |
| [WindowsDesktopAudit](security/WindowsDesktopAudit/) | Black-box audit of Windows desktop apps: privesc, DLL hijacking, UAC bypass, credential extraction | 5-phase methodology, technique matrix, IPC abuse |
| [WindowsDesktopRuntimeAudit](security/WindowsDesktopRuntimeAudit/) | Runtime black-box audit of Windows desktop apps in VM — process instrumentation, secrets, config | 6-phase methodology, VM setup, DLL hijacking procedure, tool reference |

<br/>

## 🛠 Software Development

| Skill | Description | Includes |
|---|---|---|
| [RootlessLocalDeployment](software-development/RootlessLocalDeployment/) | Host heavy apps (Node/Ember/NestJS monorepos + Postgres/Redis/S3) without root or sudo | Docker rootless, nvm, compose plugin, verified launch sequence |

<br/>

## 🔧 Tools

| Skill | Description | Includes |
|---|---|---|
| [MiroFish](tools/MiroFish/) | Swarm-intelligence prediction engine: launch, monitor, stop simulations | API endpoint map, `actions.jsonl` format reference |

<br/>

<div align="center">

## License

**MIT** — see [LICENSE](LICENSE)

</div>
