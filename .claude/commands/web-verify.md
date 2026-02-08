# Web Route Verification

Verify web routes and templates work correctly using Playwright.

## Prerequisites

- App must be running on the configured port
- Check with: `lsof -i :<port>`

## Steps

1. Check if app is running
2. For each affected route:
   - Use `browser_navigate` to visit the page
   - Use `browser_snapshot` to capture accessibility tree
   - Verify page loads without errors
   - Check key elements are present

3. After successful verification:
   ```bash
   touch .playwright-verified
   ```

## Common Routes to Verify

| Route | What to Check |
|-------|---------------|
| `/` | Home/index page loads |
| `/login` | Login form renders |
| `/register` | Registration form renders |
| `/dashboard` | Dashboard content loads |

## For Route Changes

When modifying routes:
1. Identify all affected URLs
2. Navigate to each one
3. Verify no 500 errors
4. Check key content is present

## Verification Marker

The pre-commit hook checks for `.playwright-verified` when committing route/template changes. Run this command to create the marker:
```bash
touch .playwright-verified
```
