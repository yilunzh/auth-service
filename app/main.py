"""FastAPI application entry point.

Creates the app, configures middleware, mounts static files, sets up
Jinja2 templates, and wires up routers.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import settings
from app.db.pool import close_pool, init_pool
from app.middleware.csrf import CSRFMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.security import SecurityHeadersMiddleware
from app.services.breach_check import init_bloom_filter

_DEFAULT_JWT_SECRET = "CHANGE-ME-IN-PRODUCTION"

logger = logging.getLogger(__name__)


def _validate_jwt_secret() -> None:
    """Validate the JWT secret key at startup.

    Raises RuntimeError in production (DEBUG=False) if the secret is still the
    default value, empty, or shorter than 16 characters.
    """
    secret = settings.JWT_SECRET_KEY
    is_default = secret == _DEFAULT_JWT_SECRET

    if is_default and settings.DEBUG:
        logger.warning(
            "JWT_SECRET_KEY is set to the default value — acceptable for development only"
        )
        return

    if is_default:
        raise RuntimeError(
            "JWT_SECRET_KEY is still the default value. "
            "Set a strong, unique secret before running in production."
        )

    if not secret or len(secret) < 16:
        raise RuntimeError("JWT_SECRET_KEY must be at least 16 characters long.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle."""
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("aiomysql").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    # Validate JWT secret before anything else
    _validate_jwt_secret()

    # Startup
    await init_pool(settings)
    init_bloom_filter()
    yield
    # Shutdown
    await close_pool()


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Middleware (order matters: outermost middleware runs first)
# ---------------------------------------------------------------------------
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(CSRFMiddleware, secure_cookies=not settings.DEBUG)

# ---------------------------------------------------------------------------
# Static files & templates
# ---------------------------------------------------------------------------
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_static_dir = os.path.join(_base_dir, "static")
_templates_dir = os.path.join(_base_dir, "templates")

if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir), name="static")

templates = Jinja2Templates(directory=_templates_dir)
app.state.templates = templates

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
# Import routers with graceful fallback so the app boots even when
# route modules haven't been implemented yet.

try:
    from app.api.health import router as health_router

    app.include_router(health_router)
except ImportError:
    pass

try:
    from app.api.auth import router as auth_router

    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
except ImportError:
    pass

try:
    from app.api.keys import router as keys_router

    app.include_router(keys_router, prefix="/api/keys", tags=["api-keys"])
except ImportError:
    pass

try:
    from app.api.admin import router as admin_router

    app.include_router(admin_router, tags=["admin"])
except ImportError:
    pass

try:
    from app.pages.auth import router as pages_router

    app.include_router(pages_router, tags=["pages"])
except ImportError:
    pass
