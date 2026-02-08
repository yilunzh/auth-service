"""Demo FastAPI app showing Auth Service SDK integration.

Run the auth service first:
    cd auth-service && make up

Then start this example:
    cd examples/fastapi-app
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    uvicorn main:app --port 9000
"""

from __future__ import annotations

from auth_client import AuthClient, AuthenticationError, AuthServiceError
from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

AUTH_SERVICE_URL = "http://localhost:8000"

app = FastAPI(title="Example App")

client = AuthClient(AUTH_SERVICE_URL)


# ---------------------------------------------------------------------------
# Dependencies
# ---------------------------------------------------------------------------


def get_current_user(authorization: str = Header(...)):
    """Validate a Bearer token against the auth service."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization.removeprefix("Bearer ")
    try:
        # Create a temporary client with this token to validate it
        with AuthClient(AUTH_SERVICE_URL) as c:
            c.set_token(token)
            return c.get_me()
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    except AuthServiceError as e:
        raise HTTPException(status_code=502, detail=f"Auth service error: {e.detail}")


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class LoginBody(BaseModel):
    email: str
    password: str


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.post("/login")
def login(body: LoginBody):
    """Proxy login through the auth service and return tokens."""
    try:
        with AuthClient(AUTH_SERVICE_URL) as c:
            tokens = c.login(body.email, body.password)
            return {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
            }
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/protected")
def protected(user=Depends(get_current_user)):
    """Example protected endpoint — requires a valid Bearer token."""
    return {"message": f"Hello, {user.email}!", "user_id": user.id}


@app.post("/logout")
def logout(user=Depends(get_current_user)):
    """Log out the current session (requires refresh_token in body)."""
    return {"message": "To fully log out, revoke your refresh token via the auth service."}
