---
description: Run a structured self-review of recent work
---

# Self-Review Checklist

Review the code changes in the current branch (or recent commits if on main) against this checklist. For each category, identify specific gaps with file:line references.

## Generic Checklist

### Security
- [ ] All user-facing endpoints have appropriate authentication
- [ ] All auth/sensitive endpoints are rate-limited
- [ ] Secrets are not hardcoded; validated at startup
- [ ] Input validation on all external boundaries
- [ ] No raw SQL construction with user input
- [ ] X-Forwarded-For / proxy headers handled safely
- [ ] CSRF protection on state-changing form endpoints
- [ ] Error messages don't leak internal details

### Architecture
- [ ] No duplicate logic across files (DRY)
- [ ] Consistent error handling patterns
- [ ] Type safety: no untyped public interfaces, minimal `type: ignore`
- [ ] Dependencies flow one direction (no circular imports)
- [ ] Shared logic extracted to appropriate layer

### CI/Quality
- [ ] Linter configured and passing
- [ ] Type checker configured and passing (if applicable to language)
- [ ] Test coverage tracked with reasonable threshold
- [ ] Security scanner configured (if applicable)
- [ ] CI installs dependencies consistently (no inline dep lists diverging from lockfile)

### Testing
- [ ] New code has corresponding tests
- [ ] Edge cases covered (empty input, auth failures, concurrent access)
- [ ] Tests are isolated (no shared state between test cases)
- [ ] Mocking is at the right layer (not too deep, not too shallow)

### Production Readiness
- [ ] Logging at appropriate levels (not too verbose, not too silent)
- [ ] Graceful degradation for external dependencies
- [ ] Configuration is environment-driven (no hardcoded URLs, ports, etc.)
- [ ] Health check endpoint exists and checks real dependencies

## Project-Specific Checklist

Check `docs/SPEC.md` "Non-Functional Requirements" section for project-specific standards. If the section doesn't exist, note this as a gap.

## Output Format

Present findings as:

### Self-Review Results

**Gaps Found: N** (X high, Y medium, Z low)

| Priority | Category | Gap | Location |
|----------|----------|-----|----------|
| High | Security | Endpoint X not rate-limited | `app/api/foo.py:42` |
| Medium | CI | No type checker configured | `pyproject.toml` |
| Low | Testing | Missing edge case test for empty input | `tests/unit/test_bar.py` |

**Recommendation**: [Which gaps to fix now vs. defer]
