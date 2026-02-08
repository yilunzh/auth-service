# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

See `BRIEF.md` for the project description and `docs/SPEC.md` for the technical specification.

## Development Workflow

### Phase 0: BRANCH FIRST (Feature Branches Required)

Before making ANY changes:

1. **Check current branch**: `git branch --show-current`
2. **For new features**: Create feature branch
   ```bash
   git checkout -b feature/<feature-name>
   ```
3. **For bug fixes**: Create fix branch
   ```bash
   git checkout -b fix/<bug-description>
   ```
4. **NEVER commit directly to main** - All changes go through branches → PR

Only small, trivial changes (typo fixes, config tweaks) can go directly to main.

### Merge Requirements

Before merging any PR:
1. All CI checks must pass
2. Wait for checks to complete — do NOT merge while checks are "in progress"
3. If CI fails — fix issues in the branch, push, wait for CI again

### Phase 1: CLARIFY FIRST (Ask Questions Before Coding)

Before writing ANY implementation code, you MUST:

1. **Read related code** - Understand existing patterns
2. **Ask clarifying questions** about:
   - Ambiguous requirements ("Should X also handle Y?")
   - User-facing text (error messages, labels)
   - Edge cases ("What happens if Z?")
   - Scope boundaries ("Does this include W?")
3. **Wait for answers** - Do NOT assume. Wrong assumptions = rework.

**For features with UI**, also clarify:
- Design inspiration (sites/apps to emulate)
- Visual style (modern, minimal, playful, etc.)
- Component library preference (if any)
- Key screens/interactions to get right

### Phase 2: PLAN (Create Todo List)

After clarification, create a todo list with:
- Implementation steps
- Test steps (which tests to update/add)
- Verification step ("Run tests, confirm passing")

### Phase 3: IMPLEMENT (Autonomous Execution)

Now proceed WITHOUT asking for confirmation:
1. Make incremental changes
2. Run related tests after each change
3. Fix failures immediately
4. Continue to next step

### Context Checkpoints (IMPORTANT)

**Every 3-5 major code edits**, update `.claude/session-context.md` with:

```markdown
## Current Goal
What we're trying to accomplish

## Decisions Made
- Key choice 1 and rationale
- Key choice 2 and rationale

## Files Modified
- file1.py - what changed
- file2.html - what changed

## What's Next
- Remaining step 1
- Remaining step 2
```

**Why this matters:**
- Prevents context loss during long sessions
- Hooks will remind you at 3 edits, insist at 5 edits
- Session end is blocked if incomplete work detected without handoff

**For multi-session work**, write `.claude/handoff.md` before ending with the same sections.

### Phase 4: VERIFY (Before Claiming Done)

Before saying "done":
1. Run tests - all must pass
2. If user-facing changes: present options for review
3. Mark todo items completed

**Verification Efficiency:**
- **Define "done" upfront**: Before starting, identify what verification is needed. Once met, stop.
- **Trust existing tests**: If a relevant test passes, that's sufficient. Don't duplicate.
- **One verification path**: Choose either existing test OR manual check. Not both.
- **Don't over-verify**: More verification does not equal better. Sufficient verification = done.

**For UI changes**, use Playwright to verify:
1. Use `browser_navigate` to visit affected pages
2. Use `browser_snapshot` to verify pages load correctly
3. Compare against design inspiration/expectations

## Decision Guidelines

### ESCALATE (Ask User)
- User-facing changes (UI, messages, outputs)
- API contracts and data formats
- Error messages and notifications
- Visual design decisions
- Security-sensitive changes
- Breaking changes

### AUTONOMOUS (Just Do It)
- Internal refactoring
- Bug fixes with clear solutions
- Test improvements
- Performance optimizations
- Code organization

## CI & Quality Guidelines

1. **Don't add CI checks the codebase doesn't pass** - Verify existing code passes before adding new checks
2. **Test hooks locally before committing** - Run hook scripts directly to verify they work
3. **Align local hooks with CI** - Pre-commit hook and CI should run the same checks
4. **Keep PRs small and focused** - One logical change per PR when possible

## Reference Documentation

- `BRIEF.md` - Initial project description (non-technical)
- `docs/SPEC.md` - Technical specification (grows with project)
- `docs/PATTERNS.md` - Architectural patterns reference

## Hooks

Custom hooks are in `.claude/hooks/`:
- `pre-commit-check.py` - **Blocking**: Runs tests + lint; blocks direct commits to main
- `branch-check.py` - **Blocking**: Prevents edits on main branch
- `uncommitted-changes-check.py` - **Advisory**: Warns about uncommitted changes at session start (runs on first user prompt)
- `post-edit-verify.py` - **Advisory**: Reminds to run tests after editing files
- `checkpoint-reminder.py` - **Advisory**: Reminds to checkpoint every 3-5 edits
- `checkpoint-validator.py` - **Advisory**: Validates checkpoint has required sections, resets step counter
- `completion-checklist.py` - **Blocking**: Ensures tests were run before session ends
- `session-handoff.py` - **Blocking**: Detects incomplete work, requires handoff
- `spec-update-check.py` - Triggers SPEC.md updates on key phrases

## Custom Skills

Custom slash commands are in `.claude/commands/`. See `example.md` for the format.

## SPEC.md Updates

After completing a feature, trigger docs updates by saying:
- `/spec-update`, "feature complete", "update spec", "update documentation"

The Stop hook gathers context (git changes, plan) and prompts for documentation updates.

You can also manually update `docs/SPEC.md`:
- Add feature to "Implemented" section
- Document key architectural decisions
- Update "Current State" as needed
