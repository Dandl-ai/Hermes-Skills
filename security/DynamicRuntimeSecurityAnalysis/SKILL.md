---
name: DynamicRuntimeSecurityAnalysis
description: "Runtime security analysis pack: live recon, auth, rate-limit, CORS, headers."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Security, Runtime, DynamicAnalysis, LiveRecon]
    related_skills: [WebInvestigationMethodology, FullStackWebSecurityReview]
---

## 📦 Dynamic / Runtime Analysis Pack

Live dynamic security analysis against a running target: full reconnaissance, authentication + rate-limit testing, anti-bot challenge solving, and CORS/security-header checks via curl, openssl, and node.js.

## When to Use

- Analyze an application in production.
- Test auth, rate-limit, CORS live.
- Perform dynamic reconnaissance on a target.

## Prerequisites

- curl, node.js, openssl
- Network access to the target
- Written user authorization to run active checks against the target before proceeding

## Golden Rules / Pitfalls

- **Ask for authorization first.** Running these scripts sends live, sometimes state-changing requests to the target. Get explicit written user confirmation of scope before executing the active checks (auth test, rate-limit, challenge solver).
- **Never fake success.** If a step fails because access is missing (credentials, network, permissions), say so plainly. Do not report a "pass" or fabricated status for a check you could not actually run.
- **Capture evidence verbatim.** Every finding is a claim about the live target: record the exact HTTP status, response snippet, headers, and timestamps so results are reproducible and reportable.
- **Run passive checks first.** Do TLS, headers, and CORS checks before the auth or rate-limit scripts to avoid disturbing the login flow of a real production system.
- **Labels only, no credentials.** Never place real username/password pairs in these scripts; use the supplied test/wrong credentials only.
- **Rate-limit scripts hammer the target.** The 120-request loop is loud. Confirm the target can tolerate it before running.

### 1. Live Recon Scripts

#### `live-recon.sh` - Full reconnaissance
```bash
#!/bin/bash
TARGET="${1:-https://example.com}"

echo "=== Live Recon: $TARGET ==="

# 1. TLS & Certificate
echo "--- TLS/Certificate ---"
openssl s_client -connect $(echo $TARGET | sed 's|https://||' | cut -d'/' -f1):443 -servername $(echo $TARGET | sed 's|https://||' | cut -d'/' -f1) </dev/null 2>/dev/null | openssl x509 -noout -text | grep -E "Subject:|Issuer:|Not Before|Not After|DNS:"

# 2. Security headers
echo "--- Security Headers ---"
curl -s -I "$TARGET" | grep -iE "strict-transport|x-frame|x-content|content-security|referrer|permissions|server|x-powered"

# 3. CORS
echo "--- CORS ---"
curl -s -H "Origin: https://evil.com" -D - -o /dev/null "$TARGET" | grep -iE "access-control|vary"

# 4. HTTP methods
echo "--- HTTP Methods ---"
for m in GET POST PUT DELETE PATCH OPTIONS TRACE; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X $m "$TARGET")
  echo "$m: $code"
done
```

#### `auth-test.sh` - Authentication test
```bash
#!/bin/bash
LOGIN_URL="${1:-https://example.com/login}"
USER="${2:-test}"
PASS="${3:-wrong}"

echo "=== Auth Test: $LOGIN_URL ==="

# 1. Retrieve CSRF + session
RESP=$(curl -s -c cookies.txt -D - "$LOGIN_URL")
CSRF=$(echo "$RESP" | grep -o 'csrf_token" value="[^"]*"' | sed 's/.*value="\([^"]*\)".*/\1/')
PHPSESSID=$(echo "$RESP" | grep -o 'PHPSESSID=[^;]*' | head -1)
echo "CSRF: $CSRF | PHPSESSID: $PHPSESSID"

# 2. Test login (wrong password)
RESP=$(curl -s -b cookies.txt -c cookies.txt -X POST "$LOGIN_URL" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "validate=1&csrf_token=$CSRF&username=$USER&password=$PASS")
echo "Status: $(echo "$RESP" | grep -o 'HTTP/[0-9.]* [0-9]*' | head -1)"
echo "Message: $(echo "$RESP" | grep -o 'msg-alerte[^>]*>[^<]*' | sed 's/.*>//')"

# 3. Rate limit test
echo "--- Rate Limit Test (7 attempts) ---"
for i in {1..7}; do
  RESP=$(curl -s -b cookies.txt -c cookies.txt -X POST "$LOGIN_URL" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "validate=1&csrf_token=$CSRF&username=$USER&password=$PASS$i")
  code=$(echo "$RESP" | grep -o 'HTTP/[0-9.]* [0-9]*' | head -1 | cut -d' ' -f2)
  blocked=$(echo "$RESP" | grep -c "Trop de tentatives")
  echo "Attempt $i: HTTP $code $([ $blocked -gt 0 ] && echo '[BLOCKED]')"
done
```

### 2. Node.js Challenge Solver (anti-bot)
```javascript
// solve-challenge.js - Solves JS challenges of the slowAES type
const { execFileSync } = require('child_process');
const fs = require('fs'), vm = require('vm');

function curl(path, cookie) {
  const args = ['-s', '--max-time', '30', '-A', 'Mozilla/5.0', '-k', '-D', '-'];
  if (cookie) args.push('-H', 'Cookie: ' + cookie);
  args.push('https://target.com' + path);
  const out = execFileSync('curl', args, { encoding: 'utf8', timeout: 30000 });
  const sep = out.indexOf('\r\n\r\n');
  return { head: out.slice(0, sep), body: out.slice(sep + 4) };
}

let aesCtx = null;
function initAes() {
  const r = curl('/aes.js', null);
  fs.writeFileSync('/tmp/aes.js', r.body);
  const ctx = {}; vm.createContext(ctx); vm.runInContext(r.body, ctx);
  return ctx;
}

function toNumbers(d) { const e = []; d.replace(/(..)/g, x => e.push(parseInt(x, 16))); return e; }
function toHex(a) { let e = ''; for (const f of a) e += (16 > f ? '0' : '') + f.toString(16); return e.toLowerCase(); }

function solve() {
  const ctx = initAes();
  let cookie = null, res = curl('/');
  for (let s = 1; s <= 20; s++) {
    const m = res.body.match(/a=toNumbers\("([0-9a-f]+)"\),b=toNumbers\("([0-9a-f]+)"\),c=toNumbers\("([0-9a-f]+)"\)/);
    if (!m) return cookie;
    const [, a, b, c] = m;
    cookie = '__test=' + toHex(ctx.slowAES.decrypt(toNumbers(c), 2, toNumbers(a), toNumbers(b)));
    const red = (res.body.match(/location\.href="([^"]+)"/) || [])[1];
    const next = red ? red.replace(/^https?:\/\/[^/]+/, '') : '/?i=' + (s + 1);
    res = curl(next, cookie);
  }
  return cookie;
}

console.log('Cookie:', solve());
```

### 3. Rate Limit Tester
```bash
#!/bin/bash
# rate-limit-test.sh
URL="${1:-https://example.com/api}"
HEADER="${2:-Cookie: session=xxx}"

echo "=== Rate Limit Test: $URL ==="
for i in {1..120}; do
  code=$(curl -s -o /dev/null -w "%{http_code}" -H "$HEADER" "$URL")
  echo -n "$code "
  [ $((i % 20)) -eq 0 ] && echo
  [ "$code" = "429" ] && echo -e "\n[BLOCKED at request $i]" && break
  sleep 0.1
done
echo
```

### 4. CORS & Security Headers Checker
```bash
#!/bin/bash
# cors-check.sh
TARGET="${1:-https://example.com}"
ORIGINS=("https://evil.com" "https://app.example.com" "null" "*" "https://$(date +%s).com")

for o in "${ORIGINS[@]}"; do
  echo "--- Origin: $o ---"
  curl -s -H "Origin: $o" -D - -o /dev/null "$TARGET" | grep -iE "access-control|vary"
done
```

---

## 🚀 Usage
```bash
# Full recon
./live-recon.sh https://target.com

# Auth + rate limit test
./auth-test.sh https://target.com/login testuser wrongpass

# Rate limit only
./rate-limit-test.sh https://target.com/api "Cookie: sess=xxx"

# CORS check
./cors-check.sh https://target.com

# Challenge solver
node solve-challenge.js
```

---

## 📊 Test Metrics

| Test      | Pass Criteria                       | Fail Criteria                    |
|-----------|-------------------------------------|----------------------------------|
| TLS       | TLS 1.2+, valid cert, HSTS          | TLS 1.0/1.1, expired cert, no HSTS |
| Headers   | HSTS, CSP, X-Frame, X-Content, Referrer, Permissions | Missing                    |
| CORS      | Strict whitelist, no credentials with * | Wildcard + credentials         |
| Auth      | CSRF token, rate-limit 5/15min, generic messages | No CSRF, no rate-limit, user enumeration |
| Rate Limit | 429 after threshold, reset after window | No limit, reset by cookie      |
| Challenge | Solved in < 5 steps                  | Failure or infinite loop        |

---

## Out of Scope

This pack does NOT cover:

- Static/source code analysis of the target (use `StaticApplicationSecurityTesting`).
- Full-stack review including business logic, integration, and data flow (use `FullStackWebSecurityReview`).
- Offensive exploitation, privilege escalation, or payload delivery beyond the recon/auth/rate-limit/CORS checks shown here (use `OffensiveAuditOrchestration`).
- Reconnaissance of targets you are not explicitly authorized to test. If authorization is missing, stop and obtain written scope approval first.
- Non-HTTP targets (APIs over gRPC/WebSocket, mobile, desktop binaries).

---

## Verification

Live recon results are only as good as their accuracy. Confirm each finding before reporting it:

- **Re-run the exact command** and diff the output. Transient failures (network blips, CDN cache) should not produce a stable finding; repeat twice more before trusting a result.
- **Sanity-check the response source.** Confirm the response actually comes from the target (resolve the hostname, check Server/X-Powered-By headers, match the TLS cert Subject/Issuer to the expected host) so you are not reading a CDN, WAF block page, or captive portal.
- **Validate TLS facts independently.** Cross-check `openssl s_client` output with an external tool (e.g. `curl -vI` verbose handshake, or a public checker) for the connection to a clearly trusted domain.
- **Confirm HTTP status codes manually.** For each method/request, re-issue `curl -si` and read the raw status line yourself rather than trusting a `-w "%{http_code}"` summary alone.
- **Attribute the result to the right layer.** Distinguish a real vulnerability from infrastructure behavior: a 429 might be a WAF rate-limit, not the app; a missing header might be appended upstream or stripped by a proxy. Note where the response came from.
- **Retest the risky checks (auth, rate-limit) at a quiet time.** Live mutations can trip app blocks; a second pass on a prepared test account confirms the finding is stable and not a false alarm.
- **Log evidence to the report as it verifies.** Only findings that reproduced 2–3 times and were captured verbatim (status codes, headers, snippets, timestamps) belong in the final report.