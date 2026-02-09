# Security Audit: Auth Service

## Context
Comprehensive security analysis of the auth-service codebase, covering authentication flows, cryptography, injection vectors, session management, infrastructure, and attack scenarios.

---

## Overall Verdict: Solid Foundation, Some Gaps

The service demonstrates strong security awareness — Argon2id password hashing, parameterized queries everywhere, opaque hashed refresh tokens, CSRF with constant-time comparison, multi-tier rate limiting, and email enumeration prevention. It's well above average for a project at this stage. Below are the specific findings.

---

## CRITICAL Issues (Fix Before Production)

### 1. JWT Secret Key Defaults to Placeholder
- **File:** `app/config.py:18` — `JWT_SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"`
- **Mitigation exists:** `app/main.py:28-50` blocks startup in non-DEBUG mode with the default. Good.
- **Gap:** In DEBUG mode, it only warns. If someone accidentally runs DEBUG=true behind a public IP, tokens are forgeable.
- **Attack:** Attacker crafts arbitrary JWTs with the known default secret → full account takeover, admin escalation.

### 2. No HSTS Header
- **File:** `app/middleware/security.py` — Missing `Strict-Transport-Security`
- **Attack:** SSL stripping (MITM downgrades HTTPS to HTTP, intercepts tokens/credentials in transit).
- **Fix:** Add `Strict-Transport-Security: max-age=31536000; includeSubDomains`

---

## HIGH Risk Issues

### 3. Rate Limit Bypass via Content-Type Manipulation
- **File:** `app/middleware/rate_limit.py:116-132`
- Email extraction only works when `Content-Type: application/json`. Sending `text/plain` with a JSON body skips the per-email rate limit entirely.
- **Attack:** Credential stuffing at 20 req/min/IP (instead of 5 req/min/IP+email). With rotating proxies, effectively unlimited.
- **Fix:** Parse body regardless of Content-Type, or reject non-JSON requests to auth endpoints.

### 4. Rate Limiting Fails Open by Default
- **File:** `app/config.py:59` — `RATE_LIMIT_FAIL_OPEN: bool = True`
- If the DB is unreachable (e.g., connection pool exhausted under load), all rate limits vanish.
- **Attack:** DDoS the DB connection pool → rate limits drop → brute-force credentials.
- **Fix:** Default to `False` in production. Add in-memory fallback (e.g., a simple dict with TTL) when DB is unavailable.

### 5. No JWT Audience (`aud`) Claim
- **File:** `app/services/token.py:31-43` — Payload only has `sub`, `role`, `exp`, `iat`
- **Attack:** If you ever run a second service that shares the JWT secret, tokens are interchangeable. An attacker with a low-privilege token from service B could authenticate to this service.
- **Fix:** Add `"aud": "auth-service"` to token payload and validate on decode.

### 6. Minimal Password Policy
- **File:** `app/models/auth.py:6` — Only enforces `min_length=8`
- Allows `aaaaaaaa`, `12345678`, `password` (unless caught by breach check).
- The breach check Bloom filter is a good backstop, but it only catches known breached passwords, not weak novel ones.
- **Fix:** Add complexity requirements (mixed case + digit + special) or adopt zxcvbn-style strength scoring.

---

## MEDIUM Risk Issues

### 7. No Refresh Token Binding (IP or Device Fingerprint)
- **Files:** `app/db/tokens.py`, `app/services/token.py`
- IP and user-agent are stored but never validated on token use.
- **Attack:** Stolen refresh token works from any IP/device for 30 days.
- **Fix:** Optional IP-binding or user-agent validation on refresh, with configurable strictness.

### 8. Error Messages Leak Implementation Details
- **File:** `app/api/auth.py:40-55` — `raise HTTPException(status_code=400, detail=str(exc))`
- Passes raw `ValueError` messages to clients: "This password has been found in a data breach", "Email is already registered"
- **Attack:** Confirms whether an email is registered (enumeration via registration endpoint). Reveals breach-check implementation.
- **Fix:** Map internal errors to generic client-facing messages. The forgot-password flow already does this correctly — apply the same pattern to registration.

### 9. Account Enumeration via Registration
- **File:** `app/services/auth.py` — Registration returns a distinct error when email exists.
- Login and forgot-password are properly generic, but registration leaks this info.
- **Attack:** Enumerate valid emails by attempting registration.
- **Fix:** Always return "Check your email to verify" (even if already registered), and send a "someone tried to register with your email" notification to existing users.

### 10. XSS Risk in Template Error Rendering
- **File:** `app/pages/auth.py:69-73` — Error from `ValueError` rendered in Jinja2 template.
- If Jinja2 auto-escaping is disabled or the template uses `|safe`, attacker-controlled error content could execute JS.
- **Mitigation:** Jinja2 auto-escapes by default in `.html` templates. Verify no `|safe` filters on error variables.

### 11. Profile Fields Missing Length Limits
- **File:** `app/models/user.py:21-24` — `display_name` and `phone` have no `max_length`
- **Attack:** Send a 10MB display_name → DB bloat, potential OOM on rendering.
- **Fix:** `display_name: str | None = Field(None, max_length=255)`, `phone: str | None = Field(None, max_length=32)`

### 12. User-Agent Stored Without Sanitization
- **File:** `app/pages/auth.py:63` — Raw `User-Agent` header stored in DB
- Stored in session listing and audit logs. If these are ever rendered in an admin UI without escaping → stored XSS.
- **Fix:** Truncate to 512 chars (already limited by DB column), ensure HTML-escaping on any admin display.

---

## LOW Risk Issues

### 13. No Dependency Vulnerability Scanning in CI
- **File:** `.github/workflows/ci.yml` — Has Bandit (good) but no `pip-audit` or `safety`
- Won't catch known CVEs in transitive dependencies.

### 14. Debug Logging Leaks Email
- **File:** `app/api/auth.py:81` — `logger.debug("forgot_password suppressed error for %s", body.email)`
- In DEBUG mode, writes user emails to logs.

### 15. CORS Allows All Methods and Headers
- **File:** `app/main.py:84-90` — `allow_methods=["*"]`, `allow_headers=["*"]`
- Overly permissive. Should whitelist specific methods and headers.

### 16. Argon2 Parallelism Set to 1
- **File:** `app/config.py:56` — `ARGON2_PARALLELISM=1`
- Conservative. Increasing to 4 makes offline cracking harder without significant performance cost.

### 17. No Secret Scanning in CI
- No `detect-secrets` or `truffleHog` to catch accidentally committed credentials.

---

## What's Done Well (Attacker's Perspective: "This Is Annoying")

| Defense | Details |
|---------|---------|
| **Argon2id** | GPU/ASIC-resistant password hashing with configurable work factors |
| **Parameterized queries everywhere** | Zero SQL injection surface found |
| **Opaque refresh tokens, hash-only storage** | DB breach doesn't expose usable tokens |
| **Multi-tier rate limiting** | Per-IP, per-email, per-IP+email combination |
| **Email enumeration prevention** | Login + forgot-password return generic messages |
| **Breached password bloom filter** | Blocks known-compromised passwords |
| **CSRF with `secrets.compare_digest()`** | Constant-time comparison prevents timing attacks |
| **Secure proxy trust defaults** | X-Forwarded-For ignored unless explicitly configured |
| **JWT startup validation** | Production won't start with default secret |
| **Token rotation on refresh** | Old refresh token auto-revoked |
| **Force logout on password change/reset** | All sessions invalidated |
| **Non-root Docker container** | Limits blast radius of container escape |
| **Audit logging** | Non-blocking async event trail |

---

## Realistic Attack Scenarios

### Scenario 1: Credential Stuffing
**How:** Attacker uses leaked credential lists, sends `Content-Type: text/plain` to bypass email rate limit, rotates through proxy IPs.
**Current defense:** 20 req/min/IP still applies. Breach check blocks known passwords.
**Gap:** No email-level protection with wrong Content-Type. No CAPTCHA or progressive delay.

### Scenario 2: Token Theft via XSS
**How:** Find XSS in template rendering → steal JWT from `Authorization` header or refresh token from response.
**Current defense:** CSP blocks inline scripts. Short-lived JWTs (15 min).
**Gap:** `unsafe-inline` in style-src could be leveraged in some XSS chains. No refresh token binding to IP/device.

### Scenario 3: Database Breach
**How:** SQL injection elsewhere in infra, or compromised backup.
**Current defense:** Passwords are Argon2id hashed. Refresh tokens and API keys stored as SHA-256 hashes.
**Impact:** Attacker gets hashes but can't reverse them. Would need to crack Argon2id offline (very expensive at 32MB memory cost per guess).

### Scenario 4: JWT Forgery
**How:** If JWT secret is weak or leaked.
**Current defense:** Startup validation blocks default secret in production.
**Gap:** No `aud` claim means a token from another service sharing the secret would be accepted. HS256 (symmetric) means the secret must be shared with any service that validates tokens.

### Scenario 5: Account Takeover via Password Reset
**How:** Intercept reset email, or brute-force reset token.
**Current defense:** Token is 32 bytes of `secrets.token_urlsafe` (256 bits entropy). 1-hour expiry. One-time use. All sessions revoked after reset.
**Assessment:** Very strong. Brute-forcing 256 bits is infeasible.

---

## Recommended Fix Priority

| Priority | Issue | Effort |
|----------|-------|--------|
| **P0** | Add HSTS header | 1 line |
| **P0** | Fix rate limit Content-Type bypass | Small |
| **P1** | Default rate limit fail-closed in prod | Config change |
| **P1** | Add JWT `aud` claim | Small |
| **P1** | Sanitize error messages to clients | Medium |
| **P1** | Fix registration enumeration | Medium |
| **P2** | Add profile field length limits | Small |
| **P2** | Strengthen password policy | Small |
| **P2** | Add `pip-audit` to CI | Small |
| **P2** | Optional refresh token IP binding | Medium |
| **P3** | Tighten CORS methods/headers | Small |
| **P3** | Remove email from debug logs | 1 line |
| **P3** | Increase Argon2 parallelism | Config change |
| **P3** | Add secret scanning to CI | Small |
