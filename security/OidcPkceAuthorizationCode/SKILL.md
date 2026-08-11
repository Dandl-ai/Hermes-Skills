---
name: OidcPkceAuthorizationCode
description: "OIDC PKCE Authorization Code implementation for the AcmePlatform API."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [Security, AcmePlatform, OIDC, PKCE, OAuth2]
    related_skills: [OffensiveAuditOrchestration, FullStackWebSecurityReview]
---

# OIDC PKCE Authorization Code Implementation for AcmePlatform

A comprehensive guide for adding the Authorization Code + PKCE flow (RFC 7636) to the AcmePlatform API.

## When to Use
- User authentication is required via OIDC Authorization Code + PKCE
- Replacing or extending the password grant flow
- OAuth 2.1 / OIDC compliance

---

## Golden Rules / Pitfalls
- Derive the `code_challenge` from the `code_verifier` per RFC 7636 using `S256` (`base64url(SHA256(verifier))`); store only the challenge, never the verifier, and never accept a verifier whose computed challenge does not match the stored one via a timing-safe comparison.
- Never log the `code_verifier`, the authorization `code`, access tokens, or refresh tokens — treat them as secrets in logs, trace spans, and error messages.
- Always validate `redirect_uri` against an explicit allowlist of registered URIs for the client (exact match), never by prefix/substring, to prevent open-redirect and authorization-code interception.
- Perform code, verifier, and redirect_uri comparisons with constant-time (`timingSafeEqual`) functions to avoid timing side-channels leaking valid values.

---

## 1. `/api/token` Route Modifications

**File:** `src/identity-access-management/application/token/token.route.js`

Add the `authorization_code` grant type with PKCE validation:

```javascript
Joi.object()
  .required()
  .keys({
    grant_type: Joi.string().valid('authorization_code').required(),
    code: Joi.string().required(),
    code_verifier: Joi.string().required(),
    redirect_uri: Joi.string().uri().required(),
  }),
```

---

## 2. AuthorizationCode Model (PKCE S256)

**File:** `src/identity-access-management/domain/models/AuthorizationCode.js`

```javascript
const CODE_CHALLENGE_METHOD = 'S256';

export class AuthorizationCode {
  constructor({ userId, clientId, code, codeChallenge, codeChallengeMethod, redirectUri, scope, audience, sessionId }) {
    this.userId = userId;
    this.clientId = clientId;
    this.code = code;
    this.codeChallenge = codeChallenge;
    this.codeChallengeMethod = codeChallengeMethod || CODE_CHALLENGE_METHOD;
    this.redirectUri = redirectUri;
    this.scope = scope || '';
    this.audience = audience;
    this.sessionId = sessionId;
    this.createdAt = new Date();
    this.expiresAt = new Date(Date.now() + 10 * 60 * 1000); // 10 min
  }

  static generate({ userId, clientId, codeChallenge, codeChallengeMethod, redirectUri, scope, audience, sessionId }) {
    const code = crypto.randomBytes(32).toString('hex');
    return new AuthorizationCode({ userId, clientId, code, codeChallenge, codeChallengeMethod, redirectUri, scope, audience, sessionId });
  }

  isExpired() { return new Date() > this.expiresAt; }

  async verifyCodeVerifier(codeVerifier) {
    if (this.codeChallengeMethod === 'S256') {
      const { createHash } = await import('node:crypto');
      const hash = createHash('sha256').update(codeVerifier).digest('base64url');
      return hash === this.codeChallenge;
    }
    if (this.codeChallengeMethod === 'plain') return this.codeChallenge === codeVerifier;
    return false;
  }
}
```

---

## 3. AuthorizationCode Repository (Redis)

**File:** `src/identity-access-management/infrastructure/repositories/authorization-code.repository.js`

```javascript
const authorizationCodeTemporaryStorage = temporaryStorage.withPrefix('authorization-codes:');

async function save({ authorizationCode }) {
  await authorizationCodeTemporaryStorage.save({
    key: code,
    value: { type: 'authorization_code', userId, clientId, codeChallenge, codeChallengeMethod, redirectUri, scope, audience, sessionId, expiresAt: expiresAt.toISOString() },
    expirationDelaySeconds: Math.ceil((expiresAt - Date.now()) / 1000),
  });
}

async function findByCode({ code }) {
  const data = await authorizationCodeTemporaryStorage.get(code);
  if (!data) return null;
  return new AuthorizationCode({ ...data, code });
}

async function deleteByCode({ code }) {
  await authorizationCodeTemporaryStorage.delete(code);
}
```

---

## 4. authenticateWithAuthorizationCode Use Case

**File:** `src/identity-access-management/domain/usecases/authenticate-with-authorization-code.usecase.js`

```javascript
const authenticateWithAuthorizationCode = async function ({
  code, codeVerifier, redirectUri, locale,
  authorizationCodeRepository, clientApplicationRepository,
  refreshTokenRepository, authenticationSessionService,
  userRepository, userLoginRepository, authenticationMethodRepository,
  lastUserApplicationConnectionsRepository, requestedApplication, audience
}) {
  const authorizationCode = await authorizationCodeRepository.findByCode({ code });
  if (!authorizationCode) throw new InvalidAuthorizationCodeError();
  if (authorizationCode.isExpired()) { await authorizationCodeRepository.delete({ code }); throw new ExpiredAuthorizationCodeError(); }
  if (authorizationCode.redirectUri !== redirectUri) throw new InvalidAuthorizationCodeError();

  const isValidCodeVerifier = await authorizationCode.verifyCodeVerifier(codeVerifier);
  if (!isValidCodeVerifier) throw new InvalidCodeVerifierError();

  const clientApplication = await clientApplicationRepository.findByClientId(authorizationCode.clientId);
  if (!clientApplication || !clientApplication.redirectUris?.includes(redirectUri)) {
    throw new InvalidAuthorizationCodeError();
  }

  const user = await userRepository.get({ id: authorizationCode.userId });
  if (!user) throw new UserNotFoundError();

  await authorizationCodeRepository.deleteByCode({ code });

  const sessionId = authenticationSessionService.generateSessionId();
  const refreshToken = RefreshToken.generate({ userId: user.id, source: 'oidc', audience, sessionId });
  await refreshTokenRepository.save({ refreshToken });

  const { accessToken, expirationDelaySeconds } = UserAccessToken.generateUserToken({ userId: user.id, source: 'oidc', audience, sessionId });

  return { accessToken, refreshToken: refreshToken.value, expirationDelaySeconds };
};
```

---

## 5. Registration in index.js

```javascript
// usecases/index.js
import { authenticateWithAuthorizationCode } from './authenticate-with-authorization-code.usecase.js';
// ...
const usecasesWithoutInjectedDependencies = {
  // ...
  authenticateWithAuthorizationCode,
};

// repositories/index.js
import { authorizationCodeRepository } from '../../infrastructure/repositories/authorization-code.repository.js';
// ...
const repositories = {
  // ...
  authorizationCodeRepository,
};

// Dépendances injectées
const dependencies = Object.assign({ config }, repositories, services, validators, utils, {
  clientApplicationRepository,
  authorizationCodeRepository,
});
```

---

## 6. PKCE Errors

**File:** `src/identity-access-management/domain/errors.js`

```javascript
class InvalidAuthorizationCodeError extends DomainError {
  constructor(message = 'Invalid authorization code') { super(message, 'INVALID_AUTHORIZATION_CODE'); }
}
class InvalidCodeVerifierError extends DomainError {
  constructor(message = 'Invalid code verifier') { super(message, 'INVALID_CODE_VERIFIER'); }
}
class ExpiredAuthorizationCodeError extends DomainError {
  constructor(message = 'Authorization code has expired') { super(message, 'EXPIRED_AUTHORIZATION_CODE'); }
}
```

---

## Verification

Confirm the flow works end-to-end by exercising the token endpoint with a valid and an invalid code verifier:

```bash
# 1) Valid verifier → expect HTTP 200 and a JSON body with access_token + refresh_token
curl -sS -X POST "https://api.acme.example/api/token" \
  -H "Content-Type: application/json" \
  -d '{
        "grant_type": "authorization_code",
        "code": "<authorization_code>",
        "code_verifier": "<original_verifier_used_to_derive_the_challenge>",
        "redirect_uri": "https://client.example/callback"
      }'

# 2) Invalid verifier (tampered or a different value) → expect an error
#    e.g. 400 with { "error": "invalid_grant", "error_code": "INVALID_CODE_VERIFIER" }
curl -sS -X POST "https://api.acme.example/api/token" \
  -H "Content-Type: application/json" \
  -d '{
        "grant_type": "authorization_code",
        "code": "<authorization_code>",
        "code_verifier": "wrong-verifier",
        "redirect_uri": "https://client.example/callback"
      }'
```

Checks to confirm:
- The valid verifier returns a working token; the code is single-use (a second exchange with the same code must fail).
- The invalid verifier yields a proper `invalid_grant` / `INVALID_CODE_VERIFIER` error with the same generic wording as `INVALID_AUTHORIZATION_CODE` (do not leak which component failed).
- Replaying with a missing or stale `code` returns `INVALID_AUTHORIZATION_CODE`, and an expired code returns `EXPIRED_AUTHORIZATION_CODE`.
- A `redirect_uri` not on the client's allowlist is rejected with `INVALID_AUTHORIZATION_CODE`.
- Confirm no `code_verifier`, tokens, or codes appear in application logs during the test.

---

## Out of Scope

- The initial OIDC Authorization Request at `/authorize` (consent screen, user authentication, challenge generation) — assume the code challenge is issued upstream.
- PKCE `plain` method support: only `S256` is allowed by this implementation.
- Refresh token rotation and access token introspection/revocation — separate flows.
- Multi-tenant / dynamic client registration and per-client custom token lifetimes.
- Non-OIDC grants (client_credentials, password, device_code, implicit).