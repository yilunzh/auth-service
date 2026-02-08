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

### 1. Register a user (directly against the auth service)

```bash
curl -s -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "password": "password123"}'
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

### 5. Try without a token

```bash
curl -s http://localhost:9000/protected
# → 422 (missing Authorization header)

curl -s http://localhost:9000/protected \
  -H "Authorization: Bearer invalid-token"
# → 401 Invalid or expired token
```

## How It Works

The key pattern is the `get_current_user` dependency:

```python
def get_current_user(authorization: str = Header(...)):
    token = authorization.removeprefix("Bearer ")
    with AuthClient(AUTH_SERVICE_URL) as c:
        c.set_token(token)
        return c.get_me()  # validates the token against the auth service
```

This creates an `AuthClient`, sets the Bearer token, and calls `get_me()`. If the token is valid, the auth service returns the user profile. If not, the SDK raises `AuthenticationError`, which the dependency converts to a 401 response.
