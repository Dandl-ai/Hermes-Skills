---
name: FullStackWebSecurityReview
description: "Perform a full-stack web application security review: static code analysis and live server reconnaissance."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [Security, Audit, Pentest, Code-Review, Recon, XSS, AuthZ, CSRF]
    related_skills: [github-code-review, codebase-inspection, requesting-code-review]
---

# Full-Stack Web Application Security Review

Identify and — with explicit authorisation — demonstrate vulnerabilities in a web application. The process runs in two phases: a **static code review** of the source, followed by **live server reconnaissance**. Before any active or exploitative step against a live server, confirm you have authorisation (this may be the user's own server, which is fine, but always confirm the Scope of engagement first).

## When to use
- "Check / audit / test the security of `<repo>` / `<site.domain>`"
- "Find vulnerabilities," "Is my app secure," "Hack / scan X"
- Post-mortem security reviews of an application someone owns.

## Workflow

### Phase 1 — Static review (perform this first; it is free and non-intrusive)
1. Clone the repository read-only (a shallow clone is sufficient). If a prior clone is owned by another user, fix ownership/permissions first (`git config --global --add safe.directory`).
2. **Map the language and the authorisation model.** Locate the database connection file, the login handler, and the admin/backend pages. Understand the roles/grades and where each is enforced.
3. Run targeted greps (see `references/php-security-audit-checklist.md` for PHP-specific patterns):
   - Dangerous functions: `eval(`, `exec(`, `system(`, `shell_exec`, `passthru`, `assert(`, `unserialize(`
   - SQL-injection shape: string-concatenated queries with `$_GET`/`$_POST` values in the query string (as opposed to parameterised `prepare`/`execute`)
   - XSS: `echo` / `<?= ` of user input WITHOUT `htmlspecialchars`; pay particular attention to **logs** and **error messages** (commonly left unescaped)
   - CSRF: whether any token is present on POST forms
   - Secrets: hardcoded `password=`, `secret`, `api_key`, `token`
4. **Ask the key question: are the guard checks placed only on the *inclusion page*, or also *inside each action file*?** A very common PHP flaw: pages `require` a guard (e.g. `securityAdminAction.php`) but the included action files have no guard of their own and rely on the including page. If an action is reachable directly by URL, `$_SESSION`/`$db` may be unset — determine whether that stops the exploit or actually enables it.
5. Look for **order-of-operations authorisation bugs**: does a page `require` a sensitive action file BEFORE the `grade/role != X` check that was meant to guard it?
6. Look for **installers / self-configuration scripts shipped in the repository** (`configuration.php`, `setup.php`, forms that write to a `.php` file). These often write sanitised-uncontrolled values into a PHP file via `preg_replace`, which leads to RCE if the script is still live on the server.

### Phase 2 — Live reconnaissance (only after Phase 1 indicates what to probe)
1. **DNS and ports:** `dig +short`, `nmap -Pn --top-ports 30`. Note the `Server:` / `X-Powered-By` headers, the TLS version, and any redirects.
2. **Security headers and cookies:** check `HSTS`, `X-Frame-Options`, `X-Content-Type-Options`, `CSP`, `Referrer-Policy`; check cookie flags (`Secure`, `HttpOnly`, `SameSite`).
3. **Probe the interesting files surfaced in Phase 1** — for example, is `configuration.php`, an action endpoint, or `count_data.php` reachable without authentication? (HTTP 200 where a 403 is expected indicates an information leak).
4. **Anti-bot / JS challenge:** if the homepage returns a JavaScript challenge (often `slowAES` plus a `__test` cookie and iterative `/?i=N` redirects), do not give up — see `references/bypass-js-anti-bot-challenge.md` for a working Node.js solver.
5. Only with clear authorisation, **demonstrate an exploit chain** (build a proof-of-concept script, prove the payload lands, then clean it up).

## Pitfalls
- **Never skip Phase 1.** Live probing without understanding the authorisation model wastes time and misses the check-on-page-vs-action flaw.
- Confirm that the security-header and cookie findings are actually **server configuration** rather than something the repository controls; report both layers separately.
- The **logs-as-XSS-sink** pattern is extremely common and easy to miss: input stored unsanitised in a log column, then rendered without `htmlspecialchars` in an admin log viewer. Auto-refreshing log pages make it fire reliably.
- When you find a real, fixable flaw, still check whether any *other* sink uses the same pattern before concluding.
- A guard that compares `$_SESSION['grade'] !== 0` may only be bypassable if the variable is unset in a way that passes the check — verify with a live request before claiming it.

## Verification
Confirm every finding before reporting it — a reported vulnerability must be reproducible by someone else, not just plausible.

- **Static findings:** record the exact command, flag, file, and line (e.g. `.php` grep output) so each claim maps to a grep-able result. Save the raw command output to a notes file or report appendix rather than relying on memory.
- **Live findings:** save the raw HTTP evidence — status codes, response headers, cookies, and the body of the request that triggered the issue. Paste the exact `curl`/`nmap`/`dig` command and its output verbatim into the report.
- **Exit codes matter:** a command that fails (non-zero exit code, empty output, connection refused) is not evidence of a finding — capture the exit code and the error so a false negative/false positive is obvious.
- **Manual confirmation:** for anything interactive or context-dependent (an unset `$_SESSION` check, a header bested by a proxy, a `preg_replace`-based installer), confirm it with a real request and note that confirmation in the report. Do not claim a guard bypass from code reading alone.
- **Cross-source reproducibility:** each Critical/Important finding should be reproducible by the command recorded in the report. If it cannot be reproduced, downgrade or drop it.

## Deliverable
Write the findings as a structured report (Critical / Important / Minor / Positives), with each item containing: file and line, the affected exploit, and a concrete patch (real code, not just advice). Include a prioritised action plan. Offer to apply the patches in the cloned repository and show the diffs.

See `references/php-security-audit-checklist.md` for the PHP-specific checklist and `references/bypass-js-anti-bot-challenge.md` for the challenge solver.

## Out of Scope
- **Exploiting without authorisation:** active exploitation, exploit chains, or credential attacks against a server for which no engagement scope has been confirmed.
- **Dependencies / supply chain:** deep audit of third-party libraries, package manifests, or building a Software Bill of Materials (SBOM). Dependency CVEs are noted only if they surface during the static review.
- **Infrastructure exclusively:** OS, network, or cloud configuration reviews, TLS config hardening beyond noting headers/version, and firewall or hosting-provider settings.
- **Post-exploitation:** lateral movement, privilege escalation on a compromised host, or data exfiltration.
- **Physical / social engineering:** physical access attacks, phishing, or other human-led compromise.
- **Remediation beyond the repo:** deploying patches to production, changing production secrets, or applying fixes to servers directly. Patches are proposed and demonstrated in the cloned repository only.
- **Non-security code review:** performance, correctness, style, or maintainability review. The deliverable is security findings only.
