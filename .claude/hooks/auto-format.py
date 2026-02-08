#!/usr/bin/env python3
"""Auto-format Python files after Edit/Write. Advisory - doesn't block on failure."""
import json
import os
import subprocess
import shutil


def format_file(file_path):
    """Run black and isort on the file if available."""
    messages = []

    # Check if black is available
    if shutil.which("black"):
        try:
            result = subprocess.run(
                ["black", "--quiet", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                messages.append("black")
        except (subprocess.TimeoutExpired, Exception):
            pass

    # Check if isort is available
    if shutil.which("isort"):
        try:
            result = subprocess.run(
                ["isort", "--quiet", file_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                messages.append("isort")
        except (subprocess.TimeoutExpired, Exception):
            pass

    return messages


def main():
    file_path = os.environ.get("CLAUDE_FILE_PATH", "")

    # Only format Python files (not test files to avoid disrupting test structure)
    if not file_path.endswith(".py"):
        return {"continue": True}

    # Skip hook files themselves to avoid recursion issues
    if ".claude/hooks/" in file_path:
        return {"continue": True}

    # Skip if file doesn't exist (might have been deleted)
    if not os.path.exists(file_path):
        return {"continue": True}

    formatted_with = format_file(file_path)

    if formatted_with:
        return {
            "continue": True,
            "message": f"Auto-formatted with {', '.join(formatted_with)}"
        }

    return {"continue": True}


if __name__ == "__main__":
    print(json.dumps(main()))
