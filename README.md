# Hermes Skills

A collection of procedural skills for [Hermes Agent](https://hermes-agent.nousresearch.com). Each skill is a `SKILL.md` file with optional `scripts/`, `references/`, and `templates/` that tells the agent when and how to execute a specific workflow.

## Install

Clone the repo and copy the skills you want into your Hermes skills directory:

```bash
git clone https://github.com/Dandl-ai/Hermes-Skills.git
cp -r Hermes-Skills/security/FullStackWebSecurityReview ~/.hermes/skills/security/
```

Or copy everything:

```bash
cp -r Hermes-Skills/* ~/.hermes/skills/
```

## Contents

### security/

| Skill | Description |
|---|---|
| [DynamicRuntimeSecurityAnalysis](security/DynamicRuntimeSecurityAnalysis/) | Runtime security analysis: live recon, auth testing, rate-limit, CORS, headers. |
| [FullStackWebSecurityReview](security/FullStackWebSecurityReview/) | Full-stack web app security review: static code analysis + live server recon. Includes PHP checklist, JS anti-bot bypass, and live findings references. |
| [OffensiveAuditOrchestration](security/OffensiveAuditOrchestration/) | Security orchestrator: risk assessment, evidence collection, validation gates, stopping criteria. Coordinates multiple audit skills. |
| [OidcPkceAuthorizationCode](security/OidcPkceAuthorizationCode/) | OIDC PKCE Authorization Code flow implementation. |
| [PhpMySqlWebAppPenetrationTesting](security/PhpMySqlWebAppPenetrationTesting/) | PHP/MySQL web app penetration testing: code review, bot challenges, privilege escalation. Includes JS challenge solver script. |
| [SecurityFindingsReporting](security/SecurityFindingsReporting/) | Security reporting: findings, CVSS scoring, evidence, patches, tracking. |
| [StaticApplicationSecurityTesting](security/StaticApplicationSecurityTesting/) | SAST pack: semgrep rules, pattern matching, CI/CD code audit. |
| [WebInvestigationMethodology](security/WebInvestigationMethodology/) | Web security audit methodology: recon, SAST, live testing, business logic, reporting. |

### software-development/

| Skill | Description |
|---|---|
| [RootlessLocalDeployment](software-development/RootlessLocalDeployment/) | Host local repositories without root: Docker rootless, nvm, monorepo setup. |

### tools/

| Skill | Description |
|---|---|
| [MiroFish](tools/MiroFish/) | Operate the MiroFish swarm-intelligence prediction engine: launch, monitor, stop multi-agent social simulations via Flask REST API. Includes API endpoint map and actions.jsonl format reference. |

### meta/

| Skill | Description |
|---|---|
| [SkillAnonymizer](meta/SkillAnonymizer/) | Enforce strict anonymization before publishing: scan for domains, IPs, emails, tokens, UUIDs, timestamps, usernames, paths, project identifiers. Includes automated Python scanner. |
| [SkillAuthoringCraft](meta/SkillAuthoringCraft/) | How to author Hermes skills: structure, triggers, pitfalls, verification, anonymity. |
| [SkillLibraryGitHubRelease](meta/SkillLibraryGitHubRelease/) | Publish a skill library to GitHub: anonymize targets, structure repo, git init. |

## License

MIT
