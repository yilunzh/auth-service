# Project Brief

## What am I building?

A backend authentication service built with Python and FastAPI. It will handle user authentication — registration, login, token management, and related auth flows — exposed as a REST API.

## Why?

To provide a standalone, reusable authentication layer that can be integrated with other services and frontends.

## For whom?

Other services and applications that need user authentication capabilities.

## Key Requirements

- User registration and login
- Token-based authentication (JWT)
- Secure password handling
- RESTful API endpoints

## Non-Functional Requirements (optional)

> These shape how Claude builds, not just what it builds. Skip any that don't apply.

- **Security**: [e.g., "all auth endpoints rate-limited", "secrets validated at startup", "no raw SQL"]
- **CI/Quality**: [e.g., "type checking required", "80%+ coverage", "security scanning"]
- **Performance**: [e.g., "< 200ms p95 latency", "handle 1000 concurrent users"]
- **Observability**: [e.g., "structured logging", "audit trail for admin actions"]
- **Deployment**: [e.g., "Docker required", "must run on ARM", "12-factor app"]

## Constraints (optional)

- **Tech stack**: Python / FastAPI

## Out of Scope

- Frontend / UI
- Authorization / permissions (for now — auth only)

---

*After completing this brief, start Claude Code and say: "I'm starting a new project. Read BRIEF.md and help me plan the implementation."*
