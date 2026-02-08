#!/usr/bin/env python3
"""
Warns about uncommitted changes at session start.
Runs on first user prompt to catch forgotten work from previous sessions.
Advisory only - doesn't block.
"""
import json
import os
import subprocess

# Track if we've already shown the warning this session
STATE_FILE = "/tmp/claude-uncommitted-warning-shown"


def get_uncommitted_changes():
    """Get list of uncommitted changes from git."""
    try:
        # Get modified files (staged and unstaged)
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=os.environ.get("CLAUDE_PROJECT_DIR", "."),
        )
        if result.returncode != 0:
            return []

        changes = []
        for line in result.stdout.strip().split("\n"):
            if line:
                status = line[:2]
                filepath = line[3:]
                # Skip untracked files and common noise
                if status.strip() == "??":
                    # Only warn about untracked files that look important
                    if any(
                        filepath.endswith(ext)
                        for ext in [".py", ".html", ".js", ".css", ".json"]
                    ):
                        if not any(
                            skip in filepath
                            for skip in ["__pycache__", ".pyc", "node_modules", ".bak"]
                        ):
                            changes.append(f"  ?? {filepath} (untracked)")
                else:
                    changes.append(f"  {status} {filepath}")
        return changes
    except Exception:
        return []


def main():
    # Only show once per session
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    state_file = f"{STATE_FILE}-{session_id}"

    if os.path.exists(state_file):
        return {"continue": True}

    changes = get_uncommitted_changes()

    if not changes:
        # Mark as shown even if no changes, so we don't check repeatedly
        with open(state_file, "w") as f:
            f.write("shown")
        return {"continue": True}

    # Mark as shown
    with open(state_file, "w") as f:
        f.write("shown")

    # Build warning message
    change_list = "\n".join(changes[:10])  # Limit to 10 files
    extra = f"\n  ... and {len(changes) - 10} more" if len(changes) > 10 else ""

    return {
        "continue": True,
        "message": f"""Uncommitted changes detected.

The following files have uncommitted changes from a previous session:
{change_list}{extra}

Consider:
- Committing these changes if they're ready
- Stashing them: git stash push -m "WIP: description"
- Discarding them: git restore <file>""",
    }


if __name__ == "__main__":
    print(json.dumps(main()))
