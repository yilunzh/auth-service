#!/usr/bin/env python3
"""PostToolUse hook: Validate checkpoint file has required sections.

Triggers after Write to .claude/session-context.md.
Validates required sections exist.
"""
import json
import os
import sys
from pathlib import Path


REQUIRED_SECTIONS = [
    ("current goal", ["current goal", "## current goal", "**current goal**", "# current goal"]),
    (
        "decisions made",
        ["decisions made", "## decisions", "**decisions made**", "key decisions", "# decisions"],
    ),
    (
        "files modified",
        ["files modified", "## files", "**files modified**", "files touched", "# files"],
    ),
    (
        "what's next",
        ["what's next", "## next", "**what's next**", "next steps", "remaining", "# next"],
    ),
]


def validate_checkpoint(content):
    """Check if checkpoint has all required sections."""
    content_lower = content.lower()

    missing = []
    for section_name, patterns in REQUIRED_SECTIONS:
        found = any(pattern in content_lower for pattern in patterns)
        if not found:
            missing.append(section_name)

    return missing


def reset_step_counter():
    """Reset the step counter after a valid checkpoint."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    counter_path = Path(project_dir) / ".claude" / ".step-counter"

    try:
        with open(counter_path, "w") as f:
            json.dump(
                {"count": 0, "last_checkpoint": "session-context.md", "reset_reason": "valid checkpoint written"},
                f,
            )
    except IOError:
        pass


def main():
    # Read hook input
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return {"continue": True}

    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    # Only validate session-context.md
    if "session-context.md" not in file_path:
        return {"continue": True}

    # Read the file that was just written
    try:
        with open(file_path, "r") as f:
            content = f.read()
    except IOError:
        return {"continue": True}

    # Validate sections
    missing = validate_checkpoint(content)

    if missing:
        return {
            "continue": True,  # Advisory, don't block
            "message": (
                f"Checkpoint incomplete. Missing sections: {', '.join(missing)}. "
                "Required: Current goal, Decisions made, Files modified, What's next."
            ),
        }

    # Reset step counter on valid checkpoint
    reset_step_counter()

    return {"continue": True, "message": "Checkpoint validated. Step counter reset."}


if __name__ == "__main__":
    print(json.dumps(main()))
