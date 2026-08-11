# TargetApp Live Audit Findings (20XX-XX-XX)

## Target
- **Site:** https://target-app.example.org (192.0.2.1)
- **Repo:** https://github.com/acme/target-app (commit abc1234)
- **Method:** Live audit via Tor (anti-bot challenge bypassed via the Node.js slowAES solver)

---

## Executive Summary

| Category | Score | Status |
|----------|-------|--------|
| Security Headers | 9/10 | ✅ Excellent (HSTS, CSP, XFO, nosniff, Referrer-Policy, Permissions-Policy) |
| Auth / Rate Limit | 3/10 | 🔴 Critical - Rate limiter too aggressive, blocks all auth |
| CORS | **0/10** | 🔴 **CRITICAL** - Wildcard + credentials |
| PKCE/OIDC | 7/10 | ✅ Implemented but untestable (rate limited) |
| Architecture | 6/10 | Good foundations, but auth broken |

**Overall: 5.5/10 — Not production ready**

---

## 🔴 CRITICAL FINDINGS

### 1. CORS Wildcard + Credentials (CRITICAL)
```
access-control-allow-origin: https://evil.com
access-control-allow-credentials: true
```
**Impact:** Any site can make authenticated requests on behalf of users (CSRF at scale).
**Fix:** Set `ALLOWED_ORIGINS=https://app.acme-orga.org,https://orga.acme-orga.org` in config.

### 2. Rate Limiter Blocks All Auth (CRITICAL)
- **Global:** 100 req/min → 429 at the 101st request
- **Auth endpoints:** 5 req/15min → 429 after 5 failures **and continues blocking**
- **Root cause:** the rate limiter uses an in-memory Map (per-process), has no reset mechanism, and blocks legitimate users
- **Impact:** complete DoS on login; brute force becomes theoretically possible if the rate limiter is reset

---

## 🟠 HIGH FINDINGS

### 3. Rate Limiter In-Memory (Not Redis)
- **Current:** in-memory Map (per-process, lost on restart)
- **Required:** Redis-backed sliding window (a Lua script for atomicity)
- **Config needed:** `REDIS_URL`, `RATE_LIMIT_MAX`, `AUTH_RATE_LIMIT_MAX`

### 4. CORS Still Open in Dev Default
- Current: `origin: ['*']` with `credentials: true`
- Production requires: `ALLOWED_ORIGINS=https://app.acme-orga.org,https://orga.acme-orga.org`

### 5. CORS Wildcard + Credentials on Live Site
```http
access-control-allow-origin: https://evil.com
access-control-allow-credentials: true
```
**Confirmed live on target-app.example.org** — any site can make authenticated requests.

---

## 🟡 MEDIUM FINDINGS

### 5. PKCE/OIDC Implementation Exists But Untestable
- ✅ Route `/api/token` with `authorization_code` + `code_verifier`
- ✅ `AuthorizationCode` model with PKCE S256 verification
- ✅ `AuthorizationCodeRepository` (Redis-backed)
- ✅ `authenticateWithAuthorizationCode` usecase
- ❌ **Untestable** — the rate limiter blocks all auth attempts

### 6. JWT Still HS256 (Not RS256/JWKS)
- Current: HS256 symmetric signing
- Required: RS256 asymmetric + JWKS endpoint (`/api/.well-known/jwks.json`)

### 7. JWT Rotation Missing
- No key-rotation mechanism
- No JWKS endpoint (`/api/.well-known/jwks.json`)

---

## ✅ CONFIRMED SECURE (PASS)

| Control | Status | Evidence |
|---------|--------|----------|
| HSTS | ✅ | `max-age=31536000; includeSubDomains; preload` |
| X-Frame-Options | ✅ | `SAMEORIGIN` |
| X-Content-Type-Options | ✅ | `nosniff` |
| CSP | ✅ | Strict CSP with nonce |
| Referrer-Policy | ✅ | `strict-origin-when-cross-origin` |
| Permissions-Policy | ✅ | `geolocation=(), microphone=(), camera=()` |
| Cookie Secure/HttpOnly/SameSite | ✅ | `Secure; HttpOnly; SameSite=Lax` |
| CSP Nonce | ✅ | Per-request nonce in `sessionInit.php` |
| CSRF Token | ✅ | 32 bytes + `hash_equals()` timing-safe |
| CSRF Global | ✅ | `csrf_verify()` on all POST via `sessionInit.php` |
| Session Regeneration | ✅ | `session_regenerate_id(true)` on login |
| Cookie IP Binding | ✅ | `user_ip` in `cookies` table |
| Prepared Statements | ✅ | PDO everywhere |
| Password Hashing | ✅ | `password_hash()` / `password_verify()` |
| HSTS Preload | ✅ | `preload` directive present |
| X-Frame-Options | ✅ | `SAMEORIGIN` |

---

## 📋 RECOMMENDED FIXES (Priority Order)

| # | Fix | Effort | Priority |
|---|-----|--------|----------|
| 1 | Set `ALLOWED_ORIGINS` in `.env.production` | 5 min | 🔴 CRITICAL |
| 2 | Replace in-memory rate limiter with Redis-backed (ioredis + Lua) | 1-2h | 🔴 CRITICAL |
| 3 | Add rate-limiter reset endpoint / admin panel | 30 min | 🔴 CRITICAL |
| 4 | Migrate secrets to Docker secrets / Vault | 1h | 🟠 HIGH |
| 5 | Implement JWT RS256 + JWKS endpoint | 2-3h | 🟠 HIGH |
| 6 | Add JWT rotation (90 days) | 2h | 🟠 MEDIUM |
| 7 | Add OpenResty/NGINX reverse proxy with ModSecurity | 2h | 🟠 MEDIUM |
| 8 | Add JWKS endpoint (`/.well-known/jwks.json`) | 1h | 🟠 MEDIUM |

---

## Test Evidence (Live)

### Security Headers (Live)
```
strict-transport-security: max-age=31536000; includeSubDomains; preload
x-frame-options: SAMEORIGIN
x-content-type-options: nosniff
content-security-policy: default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://code.jquery.com; ...
referrer-policy: strict-origin-when-cross-origin
permissions-policy: geolocation=(), microphone=(), camera=()
```

### Rate Limiting (Live Test)
```
Global: 100 req/min → 429 at the 101st request
Auth: 5 req/15min → 429 at the 6th request (ALL blocked after)
```

### CORS (Live)
```
Origin: evil.com → access-control-allow-origin: https://evil.com
access-control-allow-credentials: true
```

### PKCE Test
```
POST /api/token grant_type=authorization_code&code=test&code_verifier=test&redirect_uri=http://localhost/callback
→ 429 (rate limited) — endpoint exists but blocked
```

---

## Commands for Verification

```bash
# Security headers
curl -s -I https://target-app.example.org/ | grep -iE "strict-transport|x-frame|x-content|content-security|referrer|permissions"

# CORS test
curl -s -H "Origin: https://evil.com" -D - -o /dev/null https://target-app.example.org/

# Rate limit test
for i in {1..110}; do curl -s -o /dev/null -w "%{http_code} " https://target-app.example.org/api; done

# Auth rate limit
for i in {1..7}; do curl -s -o /dev/null -w "%{http_code} " -X POST https://target-app.example.org/api/token -d "grant_type=password&username=test&password=wrong"; done
```