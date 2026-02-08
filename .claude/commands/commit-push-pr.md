# Commit, Push, and Create PR

Complete workflow from staged changes to PR creation.

## Steps

1. Run `git status` to see all untracked and modified files
2. Run `git diff` to review staged and unstaged changes
3. Run `git log -5 --oneline` to see recent commit style
4. Stage relevant files (avoid .env, credentials, large binaries)
5. Create commit with descriptive message following repo conventions
6. Check if branch tracks remote: `git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || echo "no upstream"`
7. Push to remote with `-u` flag if new branch
8. Create PR using `gh pr create` with:
   - Clear title summarizing the change
   - Body with Summary bullets and Test Plan
   - Link to related issues if applicable

## Commit Message Format

```
<type>: <short description>

<optional body explaining why>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

Types: feat, fix, refactor, test, docs, chore

## PR Body Template

```markdown
## Summary
- <1-3 bullet points describing what changed>

## Test plan
- [ ] Tests pass locally
- [ ] Verified in browser/simulator (if UI)
```
