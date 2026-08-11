# Hermes Agent Skills Library

A curated collection of procedural skills written for [Hermes Agent](https://hermes-agent.nousresearch.com). Each skill encapsulates a proven, field-tested methodology, enabling agents to execute complex, multi-step workflows reliably and repeatably without having to rediscover the necessary steps.

> **What is a Hermes skill?** A `SKILL.md` file plus optional `scripts/`, `references/`, and `templates/` that tells the agent *when* to apply a workflow, *how* to execute it step by step, and *how to verify* it worked. See [`software-development/Skill-Authoring-Craft/`](software-development/Skill-Authoring-Craft/) for the authoring guide.

---

## 📚 Contents

### 🔒 `security/` — Offensive & Defensive Web Security

| Skill | Purpose |
|---|---|
| [`PhpMySqlWebAppPenetrationTesting`](security/PhpMySqlWebAppPenetrationTesting/) | Full audit methodology for PHP/MySQL apps: static code review, online testing, anti-bot challenge bypass, privilege escalation. Includes a Node.js slowAES solver script. |
| [`FullStackWebSecurityReview`](security/FullStackWebSecurityReview/) | End-to-end web security review — static analysis + live server reconnaissance (headers, CORS, rate limiting, auth). Ships with reference checklists. |
| [`WebInvestigationMethodology`](security/WebInvestigationMethodology/) | Structured web security investigation: recon → SAST → live testing → business logic → reporting. |
| [`StaticApplicationSecurityTesting`](security/StaticApplicationSecurityTesting/) | SAST pack: semgrep patterns, grep heuristics, and CI/CD audit recipes. |
| [`DynamicRuntimeSecurityAnalysis`](security/DynamicRuntimeSecurityAnalysis/) | Runtime analysis pack: live recon, authentication testing, rate limiting, CORS, and header review. |
| [`SecurityFindingsReporting`](security/SecurityFindingsReporting/) | Reporting pack: structured findings, CVSS scoring, evidence capture, remediation tracking. |
| [`OffensiveAuditOrchestration`](security/OffensiveAuditOrchestration/) | Orchestration of a security audit — risk vs. accuracy vs. cost vs. autonomy, with explicit stopping criteria. |
| [`OidcPkceAuthorizationCode`](security/OidcPkceAuthorizationCode/) | OpenID Connect Authorization Code + PKCE (RFC 7636) implementation guidance (platform-agnostic). |

### ⚙️ `software-development/` — Tooling & Methodology

| Skill | Purpose |
|---|---|
| [`RootlessLocalDeployment`](software-development/RootlessLocalDeployment/) | Host heavy local applications (Node monorepos, Postgres/Redis/S3) **without root**: rootless Docker, nvm, native services. |

### 🧠 `meta/` — Skills about Skills

| Skill | Purpose |
|---|---|
| [`Skill-Authoring-Craft`](meta/Skill-Authoring-Craft/) | Meta-skill: how to author high-quality Hermes skills — structure, triggers, pitfalls, verification, and anonymity. |
| [`SkillLibraryGitHubRelease`](meta/SkillLibraryGitHubRelease/) | Publish a Hermes skill library to GitHub: anonymize real targets, add repo scaffolding, git init. |

---

## 🚀 Install

Skills can be added to your Hermes profile by copying the skill folders into `~/.hermes/skills/<category>/`:

```bash
# Example: install just the PHP audit skill
mkdir -p ~/.hermes/skills/security
cp -r security/PhpMySqlWebAppPenetrationTesting ~/.hermes/skills/security/
```

Then start a new Hermes session — the skills will be available to the agent.

---

## 🧭 Authoring Guide

New to writing skills? Read [`Skill-Authoring-Craft/SKILL.md`](software-development/Skill-Authoring-Craft/) — it covers the exact structure, detection rules, and verification checklist used by every skill in this library.

---

## ⚠️ Responsible Use

These are **security testing methodologies** intended for use on systems you own or are explicitly authorized to test. Always obtain written authorization before performing any active security testing against a system you do not control. The authors assume no liability for misuse.

---

## 📄 License

This project is licensed under the **MIT License** — see [`LICENSE`](LICENSE) for the full text.
