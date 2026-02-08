#!/usr/bin/env python3
"""After editing, remind to run related tests. Advisory only - doesn't block.

Language-agnostic: Provides generic test reminders based on file type.
"""
import json
import os


def get_test_reminder(file_path):
    """Generate a test reminder based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()

    # Skip test files themselves
    if "test" in file_path.lower() or "spec" in file_path.lower():
        return None

    reminders = {
        ".py": "pytest",
        ".js": "npm test",
        ".ts": "npm test",
        ".tsx": "npm test",
        ".jsx": "npm test",
        ".rs": "cargo test",
        ".go": "go test ./...",
    }

    return reminders.get(ext)


def main():
    file_path = os.environ.get("CLAUDE_FILE_PATH", "")
    test_cmd = get_test_reminder(file_path)

    if test_cmd:
        return {
            "continue": True,
            "message": f"Remember to verify changes: {test_cmd}",
        }

    return {"continue": True}


if __name__ == "__main__":
    print(json.dumps(main()))
