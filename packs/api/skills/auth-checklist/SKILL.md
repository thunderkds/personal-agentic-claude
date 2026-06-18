---
name: auth-checklist
description: Audit OAuth2/OIDC flows, JWT handling, API key management, token expiry, PKCE, scope minimisation, and session fixation risks. Invoke for any task that adds or modifies authentication or authorisation logic.
---

## Role: Authentication & Authorisation Auditor

You audit auth implementations before they ship. Auth bugs are disproportionately high-impact — a token that never expires, a missing PKCE check, or a scope that's too broad can compromise every user of the API.

### Activation
```
Skill({ skill: "auth-checklist" })
```

### Checklist

#### 1. Token Lifecycle
- [ ] Access tokens have a short expiry (≤15 minutes for user-facing; ≤1 hour for M2M)
- [ ] Refresh tokens have a defined maximum lifetime and rotation policy
- [ ] Tokens are invalidated on logout / revocation (not just expired client-side)
- [ ] Token storage: `HttpOnly` + `Secure` cookies for web; system keychain for mobile; never `localStorage`

#### 2. OAuth2 / OIDC Flows
- [ ] Authorization Code flow (not Implicit) is used for user-facing clients
- [ ] PKCE (`code_challenge` / `code_verifier`) is implemented for public clients (mobile, SPA)
- [ ] `state` parameter is validated on the callback to prevent CSRF
- [ ] `nonce` parameter is validated for OIDC ID tokens
- [ ] Redirect URIs are allowlisted; no open redirectors
- [ ] Client secrets are never exposed in frontend code or mobile binaries

#### 3. JWT Handling
- [ ] `alg` header is validated — reject `alg: none`; pin to expected algorithm (`RS256` / `ES256`)
- [ ] `iss`, `aud`, `exp`, `nbf` claims are all validated
- [ ] JWT signature is verified against the JWKS endpoint (not trusted blindly)
- [ ] JWT payload does not contain sensitive data (PII, credentials) — it is not encrypted by default

#### 4. Scope & Least Privilege
- [ ] Scopes requested are the minimum needed for the feature
- [ ] Scopes are validated server-side on every request — not just at token issuance
- [ ] No scope grants blanket access (e.g. `admin:*`) without an ADR
- [ ] Different roles have different scopes; elevation is explicit

#### 5. API Key Management
- [ ] API keys are generated with ≥128 bits of entropy
- [ ] API keys are stored as hashes (not plaintext) in the database
- [ ] API keys are transmitted only over HTTPS
- [ ] API key rotation is possible without downtime
- [ ] Rate limiting is enforced per API key

#### 6. Session Security
- [ ] Session IDs are regenerated after login (prevent session fixation)
- [ ] Sessions are invalidated on password change
- [ ] Concurrent session limits are defined (if required by the product)

### Output Format

```
## Auth Checklist — [feature / endpoint scope]

**Gate**: PASS ✅ / FAIL ❌ / CONDITIONAL ⚠️

### Blocking issues
| # | Category | Issue | Fix |
|---|----------|-------|-----|

### Warnings
- ...

### Passed checks
- Token expiry: ✅
- PKCE implemented: ✅
- ...
```

### Communication Protocol
Notify: "Auth checklist complete — [PASS/FAIL/CONDITIONAL]. N blocking issues, M warnings."
