# Auth Service Client SDK

Python client library for the Auth Service API. Provides both synchronous and asynchronous clients with typed responses and automatic error mapping.

## Installation

```bash
pip install -e path/to/auth-service/sdk
```

Or for development (includes test dependencies):

```bash
pip install -e "path/to/auth-service/sdk[dev]"
```

## Quick Start

### Synchronous Client

```python
from auth_client import AuthClient

with AuthClient("http://localhost:8000") as client:
    # Register & login
    client.register("user@example.com", "securepassword")
    tokens = client.login("user@example.com", "securepassword")
    # access token is auto-stored on the client

    # Authenticated requests
    me = client.get_me()
    print(f"Logged in as {me.email}")

    # Logout
    client.logout(tokens.refresh_token)
```

### Asynchronous Client

```python
from auth_client import AsyncAuthClient

async with AsyncAuthClient("http://localhost:8000") as client:
    tokens = await client.login("user@example.com", "securepassword")
    me = await client.get_me()
    print(f"Logged in as {me.email}")
```

## Features

- **Auto-token management**: `login()` and `refresh()` automatically store the access token on the client instance for subsequent authenticated requests.
- **Typed exceptions**: All non-2xx responses raise specific exceptions (`AuthenticationError`, `AuthorizationError`, `ValidationError`, `NotFoundError`, `ServerError`).
- **Dataclass models**: All responses are stdlib dataclasses — no pydantic dependency.
- **Connection reuse**: Both clients use persistent `httpx` connections, closed via context manager.

## Available Methods

### Public
- `register(email, password)` → `Message`
- `login(email, password)` → `TokenPair` *(auto-stores access token)*
- `refresh(refresh_token)` → `TokenPair` *(auto-stores access token)*
- `forgot_password(email)` → `Message`
- `reset_password(token, new_password)` → `Message`
- `verify_email(token)` → `Message`

### Authenticated
- `get_me()` → `User`
- `update_me(display_name=..., phone=..., metadata=...)` → `User`
- `change_password(old_password, new_password)` → `Message`
- `delete_me()` → `Message`
- `logout(refresh_token)` → `Message`
- `logout_all()` → `Message`
- `list_sessions()` → `list[Session]`

### Admin
- `list_users(page=1, per_page=20)` → `UserList`
- `change_user_role(user_id, role)` → `User`
- `change_user_active(user_id, is_active)` → `User`
- `get_audit_log(user_id=..., event=..., start_date=..., end_date=..., page=1, per_page=20)` → `AuditLog`

### API Keys
- `create_api_key(name, expires_at=..., rate_limit=...)` → `ApiKeyCreated`
- `list_api_keys()` → `ApiKeyList`
- `get_api_key(key_id)` → `ApiKey`
- `rotate_api_key(key_id, grace_hours=24)` → `ApiKeyCreated`
- `revoke_api_key(key_id)` → `Message`

### Health
- `health()` → `HealthStatus`

## Error Handling

```python
from auth_client import AuthClient, AuthenticationError, ValidationError

with AuthClient() as client:
    try:
        client.login("user@example.com", "wrongpassword")
    except AuthenticationError as e:
        print(f"Login failed ({e.status_code}): {e.detail}")
    except ValidationError as e:
        print(f"Bad request ({e.status_code}): {e.detail}")
```

### Exception Hierarchy

| Status Code | Exception |
|------------|-----------|
| 400, 422 | `ValidationError` |
| 401 | `AuthenticationError` |
| 403 | `AuthorizationError` |
| 404 | `NotFoundError` |
| 5xx | `ServerError` |

All exceptions inherit from `AuthServiceError`.

## Running Tests

```bash
cd sdk
pip install -e ".[dev]"
pytest tests/ -v
```
