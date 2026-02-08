# Test and Commit

Run tests first, only commit if they pass.

## Steps

1. Detect test runner and run tests:
   - Python: `pytest tests/ -v --tb=short` or `python -m pytest`
   - Node.js: `npm test`
   - Rust: `cargo test`
   - Go: `go test ./...`
2. If any tests fail:
   - Report the failures clearly
   - Do NOT proceed with commit
   - Offer to fix the failures
3. If all tests pass:
   - Run `git status` to see changes
   - Run `git diff` to review what will be committed
   - Stage relevant files
   - Create commit with descriptive message
   - Include `Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>`

## Test Failure Response

If tests fail, output:
```
Tests failed - cannot commit. Failures:
- test_name: brief description of failure

Would you like me to fix these issues?
```

## Success Response

If tests pass and commit succeeds:
```
All tests passed. Committed: <commit hash>
<commit message summary>
```
