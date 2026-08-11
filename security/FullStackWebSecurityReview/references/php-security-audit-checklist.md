# PHP Security Audit Checklist

Static-review patterns that reliably surface bugs in PHP applications without a framework. This consolidates the lessons from an audit in which the database and authentication code looked clean yet the application remained fully exploitable.

## Auth model
- Locate the database connection file (often `actions/database.php`, `config.php`) and the login handler first. Note that connection files may be shipped **empty** in the repository (credentials blank) and only filled in by hand on the server — that fact matters for reconnaissance (see below).
- Identify the roles/grades and exactly where each is set and checked. In this codebase the grades were `1=admin, 2=manager, 3=assistant, 0=user`.

## The guard-placement flaw (highest-value check)
The pattern that made the audit work:
- Pages (`gestion/*.php`) called `require securityAction.php` + `require securityAdminAction.php` at the top.
- But the **action files** (`gestion/actions/**/*.php`) had **no guard of their own** — they relied on the including page.
- Consequence to test: can an action be POSTed **directly by URL**? Determine whether `$bdd`/`$_SESSION` being unset stops it (fatal error) or enables it (authorisation bypass). A `require_once database.php` inside an action means it self-initialises and can be called standalone.

Greps to run:
```bash
# who requires the guard vs who doesn't
for f in $(find gestion -name '*.php'); do
  echo "$(grep -c securityAction "$f")  $f"
done | sort -rn

# actions that self-include the DB (standalone-callable candidates)
grep -rln "actions/database.php" gestion/actions/
```

## Order-of-operations authz bug
A page may `require` a sensitive action file (e.g. an importer) **before** the `if ($_SESSION['grade'] != '1') { 403 }` check. If a lower-grade user can select that tab via a query parameter, the action runs during `require`, before the guard fires. Fix: move the grade check above the `require` block.

## False negatives to watch
- The login used `password_verify` plus prepared statements correctly — **that did not make it safe**. The escaping was applied on the *page* (profile/navbar) but *not* on the **logs**.
- `htmlspecialchars` being present on the main pages is not a guarantee: always grep the admin/log/report sinks too.
- `while($x = false)` / `if($x = true)` — assignment-in-condition bugs (`=` instead of `==`). Whether real (bypassing uniqueness checks) or dead code, call them out.

## The logs-as-XSS-sink pattern (commonly missed)
- A `SaveLog()`/audit function inserts a user-controlled string (profile name, comment) into a `logs.comment` / `logs.page` column **unescaped**.
- The admin log viewer (`loadLogs.php` etc.) renders that column **without `htmlspecialchars`**.
- Because log pages often auto-refresh, the payload fires reliably in the admin's session.
- Payload that worked for privilege escalation:
  ```html
  <img src=x onerror="fetch('/gestion/update-user.php?id=4',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:'validateGrade=1&grade=1'})">
  ```
- **Fix on both ends**: `htmlspecialchars(..., ENT_QUOTES)` at the rendering sink AND in `SaveLog()` (defense in depth). Sanitised output should be the rule.

## Installers / self-config scripts (RCE source)
- Watch for `configuration.php` / `setup.php` that `preg_replace` POSTed `host`/`user`/`password` values straight into a `.php` file:
  ```php
  preg_replace("/\\\$host = '';/", "\$host = '$host';", $fileContent);
  file_put_contents($filePath, $fileContent);
  ```
  `host = x'; system($_GET['c']); //` → RCE. **Fix:** use `var_export($var, true)` for safe PHP literal embedding, or write to a non-PHP configuration file — never inject raw values into code files. **And remove the installer from production**; leaving it live is a standing RCE.

## Other checks to run
- **CSRF:** is there any token on POST forms? (This application had none anywhere.)
- **Brute force / enumeration:** distinct login errors ("no account" vs "wrong password") = username enumeration; absence of rate limiting = brute force.
- **Session:** `session_regenerate_id()` after login? `session_set_cookie_params` (Secure/HttpOnly/SameSite)?
- **Open redirect:** `header('Location: '.htmlspecialchars($_GET['redirect']))` — `htmlspecialchars` does NOT stop external-domain redirects; whitelist `^/#[a-zA-Z0-9_/?=&.-]`.
- **Default passwords** in bulk imports (e.g. `ChangeMe123!`).
- **Info leak:** standalone `count_data.php`-style JSON endpoints that never call the guard → reachable without authentication.

## Live-recon angle on a partly-secret DB
If `actions/database.php` in the repository is empty (credentials blank) but the deployed site works, assume the server copy holds real credentials (often hidden behind a hosting panel). You cannot read them; exploitation vectors that require DB credentials (e.g. a PDO-verified config rewrite) are **locked** — state that rather than keep probing. Empty-repo connection files that work on the server also reveal that the author deploys updates via FTP rather than the shared workflow.