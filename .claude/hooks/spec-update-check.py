#!/usr/bin/env python3
"""
Stop hook to check if SPEC.md documentation update is needed.
Runs at the end of each Claude Code turn.

Triggers on:
- User says "/spec-update", "update spec", "update documentation", "feature complete"
- All todos are marked complete (feature implementation finished)
"""
import json
import subprocess
import sys
import os
from glob import glob


# Trigger phrases that activate the hook
TRIGGER_PHRASES = [
    "/spec-update",
    "update spec",
    "update documentation",
    "feature complete",
    "update the spec",
    "sync documentation",
]


def get_git_changes():
    """Get list of files changed (staged, unstaged, untracked)."""
    try:
        cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

        # Get all changes
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=cwd
        )

        if result.returncode != 0:
            return []

        changes = []
        for line in result.stdout.strip().split("\n"):
            if line:
                # Format: "XY filename" where X=staged, Y=unstaged
                status = line[:2]
                filename = line[3:]
                changes.append({"status": status.strip(), "file": filename})

        return changes
    except Exception:
        return []


def get_git_diff_summary():
    """Get a summary of what changed in the diff."""
    try:
        cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())

        result = subprocess.run(
            ["git", "diff", "--stat", "HEAD"],
            capture_output=True, text=True, cwd=cwd
        )

        return result.stdout.strip() if result.returncode == 0 else ""
    except Exception:
        return ""


def read_transcript_tail(transcript_path, lines=50):
    """Read the last N lines of the transcript to check for triggers."""
    try:
        if not transcript_path or not os.path.exists(transcript_path):
            return ""

        with open(transcript_path, "r") as f:
            content = f.readlines()

        # Get last N lines
        return "".join(content[-lines:])
    except Exception:
        return ""


def check_for_triggers(transcript_content):
    """Check if any trigger phrases appear in recent transcript."""
    content_lower = transcript_content.lower()

    for phrase in TRIGGER_PHRASES:
        if phrase.lower() in content_lower:
            return True, phrase

    return False, None


def check_todos_complete(transcript_content):
    """Check if all todos were just marked complete."""
    # Simple heuristic: if recent transcript has multiple completions
    # and no pending items, consider it complete
    completed_count = transcript_content.lower().count("completed")
    pending_count = transcript_content.lower().count("pending")
    in_progress_count = transcript_content.lower().count("in_progress")

    # If we see completions and no pending/in_progress recently, might be done
    if completed_count > 2 and pending_count == 0 and in_progress_count == 0:
        return True

    return False


def find_active_plan():
    """Find the most recent plan file."""
    try:
        cwd = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
        plans_dir = os.path.join(cwd, ".claude", "plans")

        if not os.path.exists(plans_dir):
            return None, None

        # Find most recent .md file
        plan_files = glob(os.path.join(plans_dir, "*.md"))
        if not plan_files:
            return None, None

        # Sort by modification time, get newest
        newest = max(plan_files, key=os.path.getmtime)

        with open(newest, "r") as f:
            content = f.read()

        return os.path.basename(newest), content
    except Exception:
        return None, None


def build_update_prompt(changes, transcript_excerpt, plan_name, plan_content, trigger_phrase):
    """Build a detailed prompt for Claude to update SPEC.md."""

    # Format changed files
    changed_files = "\n".join([f"  - [{c['status']}] {c['file']}" for c in changes[:20]])
    if len(changes) > 20:
        changed_files += f"\n  ... and {len(changes) - 20} more files"

    # Get diff summary
    diff_summary = get_git_diff_summary()

    prompt = f"""
---
## Documentation Update Requested

**Trigger**: "{trigger_phrase}"

### Context

**Changed Files** ({len(changes)} files):
{changed_files}

**Diff Summary**:
```
{diff_summary}
```
"""

    if plan_name and plan_content:
        # Include abbreviated plan
        plan_excerpt = plan_content[:2000] + "..." if len(plan_content) > 2000 else plan_content
        prompt += f"""
**Active Plan** ({plan_name}):
```markdown
{plan_excerpt}
```
"""

    prompt += """
### Instructions

Please update `docs/SPEC.md` to reflect the changes made:

1. **Read the changed files** to understand what was implemented
2. **Read docs/SPEC.md** current state
3. **Compare and update**:
   - Fix any sections that no longer match the actual code
   - Add new sections for features not yet documented
   - Update the project structure if files were added/removed
   - Update implementation status checkboxes
   - Add entry to Version History (if section exists)
   - Update document footer (version number and "Last Updated" date)

4. **Be thorough**: Check all relevant sections, not just obvious ones

---
"""

    return prompt


def main():
    # Read hook input from stdin
    try:
        hook_input = json.load(sys.stdin)
    except json.JSONDecodeError:
        hook_input = {}

    # Get transcript path
    transcript_path = hook_input.get("transcript_path", "")

    # Read recent transcript
    transcript_content = read_transcript_tail(transcript_path)

    # Check for trigger phrases
    triggered, trigger_phrase = check_for_triggers(transcript_content)

    # Also check if todos just completed
    if not triggered and check_todos_complete(transcript_content):
        triggered = True
        trigger_phrase = "All todos completed"

    # If not triggered, exit silently
    if not triggered:
        sys.exit(0)

    # Get context
    changes = get_git_changes()
    plan_name, plan_content = find_active_plan()

    # Build prompt
    prompt = build_update_prompt(
        changes,
        transcript_content[-1000:],  # Last 1000 chars for context
        plan_name,
        plan_content,
        trigger_phrase
    )

    # Output JSON response for Stop hook
    # Stop hooks use systemMessage at top level, not hookSpecificOutput
    response = {
        "continue": True,
        "systemMessage": prompt
    }

    print(json.dumps(response))
    sys.exit(0)


if __name__ == "__main__":
    main()
