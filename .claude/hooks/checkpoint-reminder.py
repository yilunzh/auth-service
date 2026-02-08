#!/usr/bin/env python3
"""PostToolUse hook: Remind to checkpoint every 3-5 major steps.

Tracks edits via a simple counter file. Advisory only - doesn't block.
"""
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta


def get_counter_path():
    """Get path to step counter file."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    return Path(project_dir) / ".claude" / ".step-counter"


def read_counter():
    """Read current step count and last checkpoint time."""
    counter_path = get_counter_path()
    if not counter_path.exists():
        return {"count": 0, "last_checkpoint": None, "last_update": None}

    try:
        with open(counter_path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {"count": 0, "last_checkpoint": None, "last_update": None}


def write_counter(data):
    """Write step counter data."""
    counter_path = get_counter_path()
    counter_path.parent.mkdir(parents=True, exist_ok=True)

    with open(counter_path, "w") as f:
        json.dump(data, f)


def checkpoint_exists_and_recent():
    """Check if session-context.md exists and was updated recently."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    checkpoint_path = Path(project_dir) / ".claude" / "session-context.md"

    if not checkpoint_path.exists():
        return False

    mtime = datetime.fromtimestamp(checkpoint_path.stat().st_mtime)
    # Consider "recent" if updated within last 10 minutes
    return datetime.now() - mtime < timedelta(minutes=10)


def is_major_step(tool_input):
    """Determine if this edit constitutes a major step."""
    file_path = tool_input.get("file_path", "")

    # Skip test files, config files, and checkpoint files themselves
    skip_patterns = [
        "test_",
        ".spec.",
        ".claude/",
        "requirements",
        "package.json",
        "package-lock.json",
        ".env",
        "session-context.md",
        "handoff.md",
        ".step-counter",
        ".gitignore",
        "pytest.ini",
        "conftest.py",
        "tsconfig.json",
        "vite.config",
        "jest.config",
    ]

    for pattern in skip_patterns:
        if pattern in file_path:
            return False

    # Count edits to source files as major steps
    major_extensions = [".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".go", ".rs"]
    return any(file_path.endswith(ext) for ext in major_extensions)


def main():
    # Read hook input
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        input_data = {}

    tool_input = input_data.get("tool_input", {})

    # Only count major steps
    if not is_major_step(tool_input):
        return {"continue": True}

    # Read and increment counter
    counter = read_counter()
    counter["count"] = counter.get("count", 0) + 1
    counter["last_update"] = datetime.now().isoformat()

    # Check if checkpoint was recently written
    if checkpoint_exists_and_recent():
        # Reset counter after checkpoint
        counter["count"] = 0
        counter["last_checkpoint"] = datetime.now().isoformat()
        write_counter(counter)
        return {"continue": True}

    write_counter(counter)

    # Remind at 3, 5, and every 3 thereafter
    step_count = counter["count"]

    if step_count == 3:
        return {
            "continue": True,
            "message": (
                "Checkpoint reminder: 3 major edits since last checkpoint. "
                "Consider updating .claude/session-context.md with current goal, "
                "decisions made, files modified, and next steps."
            ),
        }
    elif step_count == 5:
        return {
            "continue": True,
            "message": (
                "Checkpoint due: 5 major edits without a checkpoint. "
                "Please update .claude/session-context.md before continuing. "
                "Required sections: Current goal, Decisions made, Files modified, What's next."
            ),
        }
    elif step_count > 5 and step_count % 3 == 0:
        return {
            "continue": True,
            "message": f"Checkpoint overdue ({step_count} steps). Update .claude/session-context.md.",
        }

    return {"continue": True}


if __name__ == "__main__":
    print(json.dumps(main()))
