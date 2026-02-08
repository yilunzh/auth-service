#!/usr/bin/env python3
"""Block Edit/Write on main branch for project files.

Enforces feature branch workflow. Allows editing plan files and handoffs.
"""
import json
import subprocess
import sys
import os


def get_current_branch():
    """Get the current git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=os.environ.get("CLAUDE_PROJECT_DIR", "."),
        )
        return result.stdout.strip()
    except Exception:
        return ""


def is_exempt_path(file_path):
    """Check if file path is exempt from branch protection."""
    if not file_path:
        return True

    exempt_patterns = [
        "/.claude/plans/",
        "/.claude/handoff.md",
        "/.claude/session-context.md",
        ".claude/CLAUDE.md",
    ]

    for pattern in exempt_patterns:
        if pattern in file_path:
            return True

    # Also exempt user's global claude config
    home = os.path.expanduser("~")
    if file_path.startswith(f"{home}/.claude/"):
        return True

    return False


def main():
    # Read hook input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {"decision": "allow"}

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Allow exempt paths (plans, handoffs, global config)
    if is_exempt_path(file_path):
        return {"decision": "allow"}

    # Check branch
    branch = get_current_branch()

    if branch == "main":
        return {
            "decision": "block",
            "reason": (
                f"Cannot edit '{file_path}' on main branch.\n"
                f"Create a feature branch first:\n"
                f"  git checkout -b feature/<name>\n"
                f"Then retry your edit."
            ),
        }

    return {"decision": "allow"}


if __name__ == "__main__":
    print(json.dumps(main()))
