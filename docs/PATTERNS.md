# Architectural Patterns Reference

> Common patterns Claude can reference when architecting solutions. Not prescriptive - use what fits the project.

## Multi-Tenancy Pattern

For applications where data must be isolated between users/organizations.

### Session-Based Context

```python
# Store tenant context in session
def get_current_tenant_id():
    return session.get('tenant_id')

def set_current_tenant(tenant_id):
    session['tenant_id'] = tenant_id
```

### Query Filtering

**Every query** must include tenant filter:

```python
# CORRECT
Items.query.filter_by(tenant_id=get_current_tenant_id(), ...)

# WRONG - data leak!
Items.query.filter_by(...)
```

### Isolation Decorator

```python
@tenant_required
def protected_route():
    # tenant_id guaranteed to be set
    pass
```

## 3-Layer Architecture

Separation of concerns for maintainable code:

```
Routes/Controllers → Services → Data/Models
     (HTTP)          (Logic)    (Database)
```

- **Routes**: Handle HTTP, validation, auth
- **Services**: Business logic, calculations
- **Models**: Data access, schema

## Testing Patterns

### Fixtures for Test Data

```python
@pytest.fixture
def test_user(db):
    user = User(email="test@example.com")
    db.session.add(user)
    db.session.commit()
    return user
```

### Isolation Tests

Always test data isolation between tenants:

```python
def test_tenant_isolation(client, tenant_a, tenant_b):
    # Create item as tenant A
    # Try to access as tenant B
    # Should fail
```

### Test Organization

```
tests/
├── unit/           # Fast, no I/O
├── integration/    # Database, APIs
└── e2e/            # Full user flows
```

## Security Checklist

### Input Validation

- [ ] Validate all user inputs
- [ ] Sanitize before database queries
- [ ] Parameterized queries (no string concatenation)

### Authentication

- [ ] Secure password hashing (bcrypt, argon2)
- [ ] Session management (secure cookies, expiration)
- [ ] Rate limiting on auth endpoints

### Headers

```python
# Essential security headers
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'
```

### CSRF Protection

- Include CSRF tokens in all forms
- Validate on state-changing requests

## Configuration Patterns

### Environment-Based Config

```python
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key')

class ProductionConfig(Config):
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
```

### Secrets Management

- Never commit secrets to git
- Use `.env` files locally (gitignored)
- Use environment variables in production
- Document required variables in `.env.example`

## Design Systems

### Recommended Component Libraries

**React/Next.js:**
- **shadcn/ui** - Accessible, customizable components built on Radix
- **Radix Primitives** - Unstyled accessible components
- **Headless UI** - Unstyled, accessible components from Tailwind

**CSS:**
- **Tailwind CSS** - Utility-first CSS framework
- **Tailwind UI** - Production-ready Tailwind patterns

### Design Principles

1. **Avoid generic AI aesthetics** - No stock photos, lorem ipsum, or placeholder content
2. **Use real content** - Real data makes design issues visible
3. **Consistent spacing** - Use a spacing scale (4px, 8px, 16px, 24px, 32px...)
4. **Typography hierarchy** - Clear distinction between headings, body, captions
5. **Color with purpose** - Don't use color just for decoration

### Visual Verification

Use Playwright to verify UI changes:

```javascript
// Take screenshot for comparison
await page.screenshot({ path: 'screenshot.png' });

// Visual regression testing
expect(await page.screenshot()).toMatchSnapshot('page.png');
```

## Error Handling Patterns

### User-Facing Errors

```python
# Be helpful, not technical
"Please enter a valid email address"  # Good
"ValidationError: email field regex match failed"  # Bad
```

### Logging

```python
# Log for debugging, not for users
logger.error(f"Database connection failed: {e}", exc_info=True)

# Return user-friendly message
return {"error": "Something went wrong. Please try again."}
```

### Graceful Degradation

```python
try:
    rate = fetch_exchange_rate()
except ExternalAPIError:
    rate = get_cached_rate()  # Fallback
```

## API Design Patterns

### RESTful Conventions

| Action | Method | Path | Response |
|--------|--------|------|----------|
| List | GET | /items | 200 + array |
| Create | POST | /items | 201 + item |
| Read | GET | /items/:id | 200 + item |
| Update | PUT | /items/:id | 200 + item |
| Delete | DELETE | /items/:id | 204 |

### Error Responses

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human readable message",
    "details": { "field": "email", "issue": "invalid format" }
  }
}
```

### Pagination

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

## Database Patterns

### Migrations

- Always use migrations for schema changes
- Never modify production data directly
- Test migrations on a copy first

### Soft Deletes

```python
class Item(Model):
    deleted_at = Column(DateTime, nullable=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None
```

### Timestamps

```python
class TimestampMixin:
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
```

---

*Add new patterns as you learn them. This is a living reference.*
