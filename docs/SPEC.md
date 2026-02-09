# Project Specification

> This is a **living document** that evolves with the project. Claude updates it after major features and decisions.

## Overview

**auth-service** — A production-grade backend authentication service built with Python and FastAPI. Provides user registration, login, JWT-based authentication, API key management, and admin operations via a REST API, plus hosted HTML auth pages.

**Target users**: Other services and applications needing authentication

**Primary goal**: Provide a standalone, reusable authentication layer

## Current State

- **Status**: MVP Complete + Security Hardening
- **Last updated**: 2026-02-08
- **Test coverage**: ~100 tests (unit + integration), ~54% line coverage

## Requirements

### Functional

- User registration and login with email verification
- JWT-based authentication with refresh token rotation
- API key management (create, rotate, revoke)
- Admin operations (user management, audit log)
- Hosted HTML auth pages
- Password reset flow via email

### Non-Functional

- **Security**: All auth endpoints rate-limited, Argon2id password hashing, JWT secret validated at startup, CSRF on forms, trusted proxy support, breached password detection
- **CI/Quality**: mypy type checking, pytest-cov coverage (~54%), bandit security scanning, ruff linting
- **Performance**: Async throughout (FastAPI + aiomysql), thread pool for Argon2, connection pooling
- **Observability**: Audit log for security events, structured error responses

## Architecture

### Tech Stack

- **Language**: Python 3.9+ (SDK), Python 3.11+ (service)
- **Framework**: FastAPI (async)
- **Database**: MySQL 8.0 (aiomysql async driver)
- **Password hashing**: Argon2id (argon2-cffi)
- **JWT**: PyJWT (HS256)
- **Templates**: Jinja2
- **Email**: aiosmtplib
- **Containerization**: Docker + docker-compose
- **Testing**: pytest + pytest-asyncio + pytest-cov + httpx
- **Type checking**: mypy (conservative mode)
- **Security scanning**: bandit
- **Load testing**: Locust

### Project Structure

```
auth-service/
├── app/
│   ├── main.py              # FastAPI app + lifespan + middleware
│   ├── config.py            # Pydantic settings from env
│   ├── dependencies.py      # FastAPI deps + trusted proxy IP resolution
│   ├── api/
│   │   ├── health.py        # GET /health
│   │   ├── auth.py          # /api/auth/* endpoints
│   │   ├── keys.py          # /api/keys/* endpoints
│   │   └── admin.py         # Admin endpoints
│   ├── db/
│   │   ├── pool.py          # aiomysql connection pool
│   │   ├── users.py         # User CRUD
│   │   ├── tokens.py        # Token CRUD (refresh, verification, reset)
│   │   ├── api_keys.py      # API key CRUD
│   │   ├── audit.py         # Audit log queries
│   │   └── migrations/
│   │       └── 001_initial.sql
│   ├── middleware/
│   │   ├── csrf.py          # Double-submit cookie CSRF
│   │   ├── rate_limit.py    # 3-tier rate limiting (configurable fail-open/closed)
│   │   └── security.py      # Security headers
│   ├── models/
│   │   ├── auth.py          # Request/response schemas
│   │   ├── user.py          # User schemas
│   │   └── api_key.py       # API key schemas
│   ├── pages/
│   │   └── auth.py          # HTML form routes
│   └── services/
│       ├── auth.py          # Auth business logic
│       ├── password.py      # Argon2 hashing (thread pool)
│       ├── token.py         # JWT + refresh tokens
│       ├── api_key.py       # API key lifecycle
│       ├── email.py         # Async SMTP
│       ├── rate_limit.py    # Rate limit service
│       ├── audit.py         # Audit logging
│       └── breach_check.py  # Bloom filter breach check
├── data/
│   └── breached_passwords.txt  # Top 100K breached passwords
├── tests/
│   ├── conftest.py          # Root fixtures (DB pool, test client)
│   ├── unit/                # ~40 unit tests (mocked DB)
│   ├── integration/         # ~45 integration tests (real MySQL)
│   └── load/                # Locust load tests
├── static/                  # CSS + JS for hosted pages
├── templates/               # Jinja2 HTML templates
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt
```

### Key Components

**Layered Architecture:**
1. **API Layer** (`app/api/`) — FastAPI route handlers
2. **Service Layer** (`app/services/`) — Business logic
3. **Data Layer** (`app/db/`) — MySQL operations via aiomysql
4. **Middleware** (`app/middleware/`) — CSRF, rate limiting, security headers

## API Reference

### Health

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | None | Service health + DB connectivity |

### Auth (Public)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/register` | None | Create account, send verification email |
| POST | `/api/auth/login` | None | Authenticate, return JWT + refresh token |
| POST | `/api/auth/refresh` | None | Exchange refresh token for new pair |
| POST | `/api/auth/forgot-password` | None | Send password reset email |
| POST | `/api/auth/reset-password` | None | Reset password with token |
| POST | `/api/auth/verify-email` | None | Verify email with token |

### Auth (Authenticated)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/auth/me` | Bearer | Get current user profile |
| PUT | `/api/auth/me` | Bearer | Update profile |
| PUT | `/api/auth/password` | Bearer | Change password |
| DELETE | `/api/auth/me` | Bearer | Delete account (GDPR) |
| POST | `/api/auth/logout` | Bearer | Revoke single refresh token |
| POST | `/api/auth/logout-all` | Bearer | Revoke all refresh tokens |
| GET | `/api/auth/sessions` | Bearer | List active sessions |

### Admin

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/api/auth/users` | Admin | List users (paginated) |
| PUT | `/api/auth/users/{id}/role` | Admin | Change user role |
| PUT | `/api/auth/users/{id}/active` | Admin | Activate/deactivate user |
| GET | `/api/admin/audit-log` | Admin | Query audit log |

### API Keys (Admin)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/keys/` | Admin | Create API key |
| GET | `/api/keys/` | Admin | List API keys |
| GET | `/api/keys/{id}` | Admin | Get key details |
| POST | `/api/keys/{id}/rotate` | Admin | Rotate key (grace period) |
| DELETE | `/api/keys/{id}` | Admin | Revoke key |

### Hosted Pages

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET/POST | `/auth/login` | Login form |
| GET/POST | `/auth/register` | Registration form |
| GET/POST | `/auth/forgot-password` | Forgot password form |
| GET/POST | `/auth/reset-password` | Reset password form |
| GET | `/auth/verify-email` | Email verification |

## Data Models

### Database Tables (7)

1. **users** — id, email, password_hash, role (user/admin), is_active, is_verified, display_name, phone, metadata (JSON), timestamps
2. **refresh_tokens** — id, user_id (FK), token_hash, expires_at, revoked_at, user_agent, ip_address
3. **api_keys** — id, name, key_prefix, key_hash, created_by (FK), expires_at, revoked_at, usage_count, rate_limit
4. **rate_limits** — id, key_type, key_value (unique), attempts, window_start, blocked_until
5. **email_verification_tokens** — id, user_id (FK), token_hash, expires_at, used_at
6. **password_reset_tokens** — id, user_id (FK), token_hash, expires_at, used_at
7. **audit_log** — id, user_id, event, ip_address, user_agent, details (JSON)

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| Argon2id for passwords | Memory-hard, resistant to GPU/ASIC attacks |
| JWT + opaque refresh tokens | Stateless access (15-min), revocable refresh (30-day) |
| SHA-256 for token storage | Only hashes stored in DB; raw tokens never persisted |
| MySQL-backed rate limiting | No additional infrastructure (Redis), atomic upserts |
| Configurable fail-open/closed rate limiter | Backwards-compatible default (fail-open), production can opt into fail-closed |
| Trusted proxy for X-Forwarded-For | Strictest default (ignore header); only trust when explicitly configured |
| JWT secret validation at startup | Block production with default/weak secret; warn in debug mode |
| Double-submit cookie CSRF | Standard pattern for form-based auth pages |
| Bloom filter for breach check | O(1) lookup, ~170KB memory for 100K passwords, 0.1% FP |
| Fail-open breach check | Availability over strictness if filter fails to load |
| Thread pool for Argon2 | Prevents blocking the async event loop |

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | No | `mysql://auth_user:auth_pass@mysql:3306/auth_db` | MySQL connection URL (use `mysql` host for Docker, `localhost` for local) |
| `DB_POOL_MIN` | No | 5 | Min pool connections |
| `DB_POOL_MAX` | No | 20 | Max pool connections |
| `JWT_SECRET_KEY` | **Yes** | `CHANGE-ME-IN-PRODUCTION` | JWT signing secret |
| `JWT_ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | 15 | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | No | 30 | Refresh token TTL |
| `SMTP_HOST` | No | `localhost` | SMTP server |
| `SMTP_PORT` | No | 587 | SMTP port |
| `SMTP_USER` | No | — | SMTP username |
| `SMTP_PASSWORD` | No | — | SMTP password |
| `SMTP_FROM_EMAIL` | No | `noreply@example.com` | Sender address |
| `CORS_ORIGINS` | No | — | Comma-separated allowed origins |
| `TRUSTED_PROXIES` | No | — | Comma-separated trusted proxy IPs/CIDRs (e.g., `10.0.0.1,172.16.0.0/12`) |
| `RATE_LIMIT_FAIL_OPEN` | No | True | Allow requests when rate limiter DB fails (False = return 503) |
| `ARGON2_TIME_COST` | No | 2 | Argon2 iterations |
| `ARGON2_MEMORY_COST` | No | 32768 | Argon2 memory (KB) |
| `ARGON2_PARALLELISM` | No | 1 | Argon2 parallelism |
| `DEBUG` | No | False | Debug mode |
| `BASE_URL` | No | `http://localhost:8000` | Base URL for email links |

## Testing

### Running Tests

```bash
# Start MySQL
docker-compose up -d mysql

# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run only unit tests (no DB needed)
pytest tests/unit -v

# Run with coverage
pytest tests/unit -v --cov=app --cov-report=term-missing

# Run only integration tests
pytest tests/integration -v

# Type checking
mypy app/

# Security scanning
bandit -r app/ -c pyproject.toml
```

### Load Testing

```bash
# Create load test users
python -m tests.load.setup_users --count 1000

# Smoke run
locust -f tests/load/locustfile.py --headless --host http://localhost:8000 -u 10 -r 2 -t 10s

# Full load test
locust -f tests/load/locustfile.py --headless --host http://localhost:8000 -u 200 -r 20 -t 60s
```

## Development Notes

### Email Verification in Dev

SMTP is not configured by default. After registering a user, verify them manually:

```bash
docker compose exec mysql mysql -u auth_user -pauth_pass auth_db \
  -e "UPDATE users SET is_verified = 1 WHERE email = 'user@example.com';"
```

Without this step, login will fail with "Invalid credentials" because unverified accounts cannot authenticate.

## Deployment

```bash
# Build and run
make up  # or: docker-compose up --build

# Or run directly
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## External Dependencies

| Package | Purpose |
|---------|---------|
| fastapi | Web framework |
| uvicorn | ASGI server |
| aiomysql | Async MySQL driver |
| cryptography | MySQL 8 caching_sha2_password auth |
| argon2-cffi | Password hashing |
| PyJWT | JWT tokens |
| jinja2 | HTML templates |
| python-multipart | Form parsing |
| pydantic[email] | Data validation |
| aiosmtplib | Async email |
| pytest-cov | Test coverage reporting |
| mypy | Static type checking |
| bandit | Security linting |

## Security Features

- **Password hashing**: Argon2id with configurable cost parameters
- **Breached password detection**: Bloom filter with 100K common passwords
- **JWT tokens**: Short-lived (15 min) with opaque refresh tokens
- **JWT secret validation**: Blocks production startup with default/weak/short secrets
- **CSRF protection**: Double-submit cookies on form endpoints
- **Rate limiting**: Per-IP (20/min), per-email (10/min), per-IP+email (5/min) on login, register, forgot-password, and refresh endpoints
- **Configurable rate limit failure mode**: Fail-open (default) or fail-closed (503) when rate limiter DB is unavailable
- **Trusted proxy support**: X-Forwarded-For only trusted from configured proxy IPs/CIDRs; ignored by default
- **Security headers**: CSP, X-Frame-Options, MIME sniffing, XSS protection
- **Email enumeration prevention**: Silent failures on forgot-password
- **SQL injection prevention**: Parameterized queries throughout
- **Static analysis**: bandit security scanning in CI

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-08 | Initial project setup |
| 0.2 | 2026-02-08 | All 48 application files implemented |
| 0.3 | 2026-02-08 | Tests, breach check, load testing, documentation |
| 0.4 | 2026-02-08 | DX fixes: Docker DATABASE_URL, cryptography dep, email verification docs, SDK Python 3.9+ |
| 0.5 | 2026-02-08 | Security hardening: JWT validation, rate limit refresh, fail-open config, trusted proxies |
| 0.6 | 2026-02-08 | CI improvements: mypy type checking, pytest-cov coverage, bandit security scanning |

## Known Gaps

> Issues identified during self-review that haven't been addressed yet.
> Ordered by priority (high → low). Remove items as they're resolved.

- [ ] Coverage at ~54% — target 80%+ for auth-critical paths — severity: medium
- [ ] No structured logging (print-based) — severity: low
- [ ] No health check for external dependencies (SMTP) — severity: low

---

*This specification is maintained by Claude Code. Update it when completing features or making architectural decisions.*
