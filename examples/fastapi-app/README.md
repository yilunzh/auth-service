# Example: FastAPI App with Auth Service SDK

A minimal FastAPI application demonstrating how to integrate the Auth Service client SDK for authentication.

## Setup

1. **Start the auth service** (from the repo root):

```bash
cd auth-service
cp .env.example .env              # create local config (defaults work for Docker)
make up
```

> **Note:** `.env.example` defaults to `mysql` as the database host, which resolves
> to the MySQL container inside Docker networking. If you're running the auth service
> outside Docker, change the host to `localhost` in your `.env`.

2. **Create a virtual environment and install dependencies**:

```bash
cd examples/fastapi-app
python -m venv .venv
source .venv/bin/activate           # on Windows: .venv\Scripts\activate
pip install -e ../../sdk            # install the SDK
pip install -r requirements.txt     # install fastapi + uvicorn
```

3. **Start the example app**:

```bash
uvicorn main:app --port 9000
```

## Walkthrough

### 1. Register a user

```bash
curl -s -X POST http://localhost:9000/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "password123"}'
```

Response:
```json
{
  "message": "Check your email to verify your account"
}
```

### 2. Verify the user (dev shortcut)

SMTP isn't configured in the default dev setup, so the verification email won't send.
Mark the user as verified directly in MySQL:

```bash
docker compose exec mysql mysql -u auth_user -pauth_pass auth_db \
  -e "UPDATE users SET is_verified = 1 WHERE email = 'demo@example.com';"
```

### 3. Login via the example app

```bash
curl -s -X POST http://localhost:9000/login \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "password123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "a1b2c3d4..."
}
```

### 4. Access a protected endpoint

```bash
curl -s http://localhost:9000/protected \
  -H "Authorization: Bearer <access_token>"
```

Response:
```json
{
  "message": "Hello, demo@example.com!",
  "user_id": "some-uuid"
}
```

### 5. Refresh the token

```bash
curl -s -X POST http://localhost:9000/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOi...(new)...",
  "refresh_token": "e5f6g7h8...(new)..."
}
```

### 6. Logout

```bash
curl -s -X POST http://localhost:9000/logout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <access_token>" \
  -d '{"refresh_token": "<refresh_token>"}'
```

Response:
```json
{
  "message": "Logged out successfully."
}
```

### 7. Verify logout worked

Try refreshing with the revoked token — expect a 401:

```bash
curl -s -X POST http://localhost:9000/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
# → 401 Invalid or expired refresh token
```

## How It Works

The example app proxies all auth operations through its own endpoints, so your frontend only ever talks to one server.

**Token validation** — The `get_current_user` dependency extracts the Bearer token, calls `client.get_me()` against the auth service, and returns the user profile (or 401):

```python
def get_current_user(authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    with AuthClient(AUTH_SERVICE_URL) as c:
        c.set_token(token)
        return c.get_me()  # validates the token against the auth service
```

**Registration** — `POST /register` calls `client.register(email, password)` to create a new account. In production the user would receive a verification email; in dev you verify manually via MySQL.

**Token refresh** — `POST /refresh` calls `client.refresh(refresh_token)` to exchange a refresh token for a new access/refresh pair without re-entering credentials.

**Logout** — `POST /logout` requires a valid Bearer token (to prove identity) plus the refresh token to revoke. It calls `client.logout(refresh_token)` to revoke the token server-side, preventing further use.
