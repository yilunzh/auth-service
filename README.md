# Auth Service

A production-grade authentication service built with FastAPI and MySQL. Provides user registration, login, JWT-based authentication, API key management, and admin operations via a REST API — plus hosted HTML auth pages you can point users to directly.

## Features

- **JWT authentication** — short-lived access tokens (15 min) + revocable refresh tokens (30 days)
- **User registration** with email verification
- **Password reset** flow via email
- **Breached password detection** — Bloom filter checks against 100K common passwords
- **API key management** — create, rotate (with grace period), and revoke service-to-service keys
- **Admin operations** — user listing, role management, account activation, audit log
- **Hosted auth pages** — server-rendered login, register, forgot/reset password forms
- **Rate limiting** — 3-tier (per-IP, per-email, per-IP+email)
- **Security headers** — CSP, X-Frame-Options, MIME sniffing protection
- **CSRF protection** — double-submit cookies on form endpoints
- **GDPR account deletion** — users can hard-delete their own accounts
- **Session management** — list active sessions, logout single or all devices

## Quick Start

### Docker (recommended)

```bash
# Clone and start everything
git clone <repo-url> && cd auth-service
cp .env.example .env  # edit JWT_SECRET_KEY at minimum
make up               # or: docker-compose up --build
```

This starts the API on `http://localhost:8000` and MySQL on port 3306. The database schema is applied automatically on first boot.

> **Dev tip — email verification:** SMTP isn't configured by default, so verification emails won't send. After registering a user, verify them manually:
> ```bash
> docker compose exec mysql mysql -u auth_user -pauth_pass auth_db \
>   -e "UPDATE users SET is_verified = 1 WHERE email = 'alice@example.com';"
> ```

### Manual Setup

```bash
# 1. Start MySQL 8.0 (or use an existing instance)
docker-compose up -d mysql

# 2. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3. Set required env vars (or create .env)
export JWT_SECRET_KEY="your-secure-random-secret"
export DATABASE_URL="mysql://auth_user:auth_pass@localhost:3306/auth_db"

# 4. Run the server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Verify it's running:

```bash
curl http://localhost:8000/health
```

## Configuration

All settings are loaded from environment variables (or a `.env` file).

| Variable | Default | Description |
|----------|---------|-------------|
| `JWT_SECRET_KEY` | `CHANGE-ME-IN-PRODUCTION` | **Change this.** JWT signing secret |
| `DATABASE_URL` | `mysql://auth_user:auth_pass@localhost:3306/auth_db` | MySQL connection URL |
| `DB_POOL_MIN` / `DB_POOL_MAX` | 5 / 20 | Connection pool bounds |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15 | Access token TTL |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 30 | Refresh token TTL |
| `SMTP_HOST` | `localhost` | SMTP server for outbound email |
| `SMTP_PORT` | 587 | SMTP port |
| `SMTP_USER` / `SMTP_PASSWORD` | — | SMTP credentials |
| `SMTP_FROM_EMAIL` | `noreply@example.com` | Sender address |
| `CORS_ORIGINS` | — | Comma-separated allowed origins |
| `ARGON2_TIME_COST` | 2 | Argon2 iterations |
| `ARGON2_MEMORY_COST` | 32768 | Argon2 memory in KB |
| `ARGON2_PARALLELISM` | 1 | Argon2 parallelism |
| `BASE_URL` | `http://localhost:8000` | Base URL for email links |
| `DEBUG` | `false` | Debug mode |

## API Usage

All examples assume the service is running at `http://localhost:8000`.

### Register a User

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cureP@ss!"}'
# → {"message": "Check your email to verify your account"}
```

### Verify Email

Use the token from the verification email:

```bash
curl -X POST http://localhost:8000/api/auth/verify-email \
  -H "Content-Type: application/json" \
  -d '{"token": "<token-from-email>"}'
# → {"message": "Email verified successfully."}
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "s3cureP@ss!"}'
# → {"access_token": "eyJ...", "refresh_token": "abc123...", "token_type": "bearer"}
```

### Use the Access Token

Pass the `access_token` as a Bearer token:

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
# → {"id": "...", "email": "alice@example.com", "role": "user", ...}
```

### Refresh Tokens

When the access token expires, exchange the refresh token for a new pair:

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
# → {"access_token": "eyJ...", "refresh_token": "new-abc...", "token_type": "bearer"}
```

The old refresh token is invalidated (rotation).

### Logout

Revoke a single session:

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

Or revoke all sessions:

```bash
curl -X POST http://localhost:8000/api/auth/logout-all \
  -H "Authorization: Bearer <access_token>"
```

### Password Reset

```bash
# Request reset email
curl -X POST http://localhost:8000/api/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com"}'

# Reset with token from email
curl -X POST http://localhost:8000/api/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token": "<reset-token>", "new_password": "n3wS3cure!"}'
```

### Admin: List Users

```bash
curl "http://localhost:8000/api/auth/users?page=1&per_page=20" \
  -H "Authorization: Bearer <admin_access_token>"
```

### Admin: Manage API Keys

```bash
# Create a key
curl -X POST http://localhost:8000/api/keys/ \
  -H "Authorization: Bearer <admin_access_token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "my-service", "rate_limit": 1000}'
# → {"id": "...", "key": "ak_...", "name": "my-service", ...}

# List keys
curl http://localhost:8000/api/keys/ \
  -H "Authorization: Bearer <admin_access_token>"

# Rotate (24h grace period by default)
curl -X POST "http://localhost:8000/api/keys/<key_id>/rotate?grace_hours=24" \
  -H "Authorization: Bearer <admin_access_token>"

# Revoke
curl -X DELETE http://localhost:8000/api/keys/<key_id> \
  -H "Authorization: Bearer <admin_access_token>"
```

## Hosted Pages

Browser-accessible auth forms are served at:

| URL | Description |
|-----|-------------|
| `/auth/login` | Login form |
| `/auth/register` | Registration form |
| `/auth/forgot-password` | Forgot password form |
| `/auth/reset-password` | Reset password form (with token) |
| `/auth/verify-email` | Email verification (with token) |

These pages include CSRF protection and can be used as a standalone auth UI or embedded via iframe/redirect.

## Authentication Guide

### Token Lifecycle

1. User logs in → receives `access_token` (15 min) + `refresh_token` (30 days)
2. Client stores both tokens (e.g., `access_token` in memory, `refresh_token` in secure storage)
3. Client sends `Authorization: Bearer <access_token>` with every API request
4. When the access token expires (HTTP 401), client calls `/api/auth/refresh` with the refresh token
5. Server returns a new token pair and invalidates the old refresh token (rotation)
6. On logout, client calls `/api/auth/logout` to revoke the refresh token server-side

### Recommended Refresh Strategy

```
Request → 401 Unauthorized?
  ├── Yes → POST /api/auth/refresh
  │         ├── Success → Retry original request with new access_token
  │         └── Failure → Redirect to login
  └── No  → Continue normally
```

Keep the refresh token out of JavaScript-accessible storage (e.g., use `httpOnly` cookies or a secure native store) to mitigate XSS.

## API Reference

### Health

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | — | Service health + DB connectivity |

### Auth (Public)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create account, send verification email |
| POST | `/api/auth/login` | Authenticate, return JWT + refresh token |
| POST | `/api/auth/refresh` | Exchange refresh token for new pair |
| POST | `/api/auth/forgot-password` | Send password reset email |
| POST | `/api/auth/reset-password` | Reset password with token |
| POST | `/api/auth/verify-email` | Verify email with token |

### Auth (Authenticated — Bearer token)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/me` | Get current user profile |
| PUT | `/api/auth/me` | Update profile (display_name, phone, metadata) |
| PUT | `/api/auth/password` | Change password |
| DELETE | `/api/auth/me` | Delete account (GDPR) |
| POST | `/api/auth/logout` | Revoke single refresh token |
| POST | `/api/auth/logout-all` | Revoke all refresh tokens |
| GET | `/api/auth/sessions` | List active sessions |

### Admin (Bearer token, admin role)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/auth/users` | List users (paginated) |
| PUT | `/api/auth/users/{id}/role` | Change user role (user/admin) |
| PUT | `/api/auth/users/{id}/active` | Activate/deactivate user |
| GET | `/api/admin/audit-log` | Query audit log (filterable) |

### API Keys (Bearer token, admin role)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/keys/` | Create API key (full key returned once) |
| GET | `/api/keys/` | List API keys |
| GET | `/api/keys/{id}` | Get key details |
| POST | `/api/keys/{id}/rotate` | Rotate key (configurable grace period) |
| DELETE | `/api/keys/{id}` | Revoke key |

## Database

### Schema

7 tables managed via SQL migration (`app/db/migrations/001_initial.sql`), auto-applied by Docker on first boot:

| Table | Purpose |
|-------|---------|
| `users` | Accounts (email, password hash, role, profile) |
| `refresh_tokens` | Opaque refresh tokens (hashed, per-session) |
| `api_keys` | Service-to-service API keys (hashed) |
| `rate_limits` | Per-key rate limit counters |
| `email_verification_tokens` | Email verification tokens |
| `password_reset_tokens` | Password reset tokens |
| `audit_log` | Admin-visible audit trail |

### Migrations

The initial migration runs automatically when the MySQL container starts. For manual setup, apply it directly:

```bash
mysql -u auth_user -p auth_db < app/db/migrations/001_initial.sql
```

## Security

- **Argon2id** password hashing with configurable cost parameters
- **Breached password detection** via Bloom filter (~170KB, 0.1% false positive rate)
- **Short-lived JWTs** (15 min) — limits exposure window if a token leaks
- **Refresh token rotation** — old tokens are invalidated on use
- **Token hashing** — refresh tokens and API keys stored as SHA-256 hashes, never in plaintext
- **Rate limiting** — per-IP (20/min), per-email (10/min), per-IP+email (5/min)
- **CSRF** — double-submit cookies on hosted form pages
- **Security headers** — CSP, X-Frame-Options, X-Content-Type-Options, X-XSS-Protection
- **Email enumeration prevention** — forgot-password always returns the same response
- **SQL injection prevention** — parameterized queries throughout

## Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Unit tests only (no DB required)
pytest tests/unit -v

# Integration tests only (needs MySQL running)
docker-compose up -d mysql
pytest tests/integration -v
```

### Load Testing

```bash
# Create test users
python -m tests.load.setup_users --count 1000

# Quick smoke test
locust -f tests/load/locustfile.py --headless --host http://localhost:8000 -u 10 -r 2 -t 10s

# Full load test
locust -f tests/load/locustfile.py --headless --host http://localhost:8000 -u 200 -r 20 -t 60s
```

## Project Structure

```
auth-service/
├── app/
│   ├── main.py              # FastAPI app, lifespan, middleware
│   ├── config.py            # Settings from env vars
│   ├── dependencies.py      # FastAPI dependency injection
│   ├── api/
│   │   ├── health.py        # GET /health
│   │   ├── auth.py          # /api/auth/* endpoints
│   │   ├── keys.py          # /api/keys/* endpoints
│   │   └── admin.py         # Admin endpoints
│   ├── db/
│   │   ├── pool.py          # aiomysql connection pool
│   │   ├── users.py         # User CRUD
│   │   ├── tokens.py        # Token CRUD
│   │   ├── api_keys.py      # API key CRUD
│   │   ├── audit.py         # Audit log queries
│   │   └── migrations/
│   │       └── 001_initial.sql
│   ├── middleware/
│   │   ├── csrf.py          # Double-submit cookie CSRF
│   │   ├── rate_limit.py    # 3-tier rate limiting
│   │   └── security.py      # Security headers
│   ├── models/              # Pydantic request/response schemas
│   ├── pages/               # Hosted HTML form routes
│   └── services/            # Business logic layer
├── data/
│   └── breached_passwords.txt
├── tests/
│   ├── unit/                # ~40 unit tests
│   ├── integration/         # ~45 integration tests
│   └── load/                # Locust load tests
├── static/                  # CSS + JS for hosted pages
├── templates/               # Jinja2 HTML templates
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt
```

## Tech Stack

- **Python 3.11+** / **FastAPI** (async)
- **MySQL 8.0** via aiomysql
- **Argon2id** (argon2-cffi) for password hashing
- **PyJWT** for token signing
- **Jinja2** for HTML templates
- **aiosmtplib** for async email
- **pytest** + httpx for testing
- **Locust** for load testing
- **Docker** + docker-compose for deployment

## License

MIT
