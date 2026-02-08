#!/usr/bin/env python3
"""Stop hook: Detect incomplete work and require handoff.

Uses multiple signals:
1. Git status (uncommitted changes)
2. Step counter (edits without checkpoint)
3. Transcript patterns (in_progress todos)

Blocks if 2+ signals detected, advisory warning if 1 signal.
"""
import json
import os
import subprocess
from pathlib import Path
from datetime import datetime, timedelta


def get_uncommitted_changes():
    """Check git for uncommitted changes to tracked files."""
    try:
        cwd = os.environ.get("CLAUDE_PROJECT_DIR", ".")

        # Check for staged changes
        staged = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=cwd
        )

        # Check for unstaged changes to tracked files
        unstaged = subprocess.run(
            ["git", "diff", "--name-only"],
            capture_output=True,
            text=True,
            cwd=cwd
        )

        staged_files = [f for f in staged.stdout.strip().split("\n") if f]
        unstaged_files = [f for f in unstaged.stdout.strip().split("\n") if f]

        # Filter to code files only (ignore .claude/ files and config)
        code_extensions = [".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".go", ".rs"]
        skip_patterns = [".claude/", "requirements", ".env", ".gitignore", "package-lock.json"]

        def is_code_file(f):
            is_code = any(f.endswith(ext) for ext in code_extensions)
            is_skipped = any(pattern in f for pattern in skip_patterns)
            return is_code and not is_skipped

        code_changes = list(set(f for f in staged_files + unstaged_files if is_code_file(f)))

        return code_changes
    except Exception:
        return []


def get_step_count():
    """Read step counter to see edit activity."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    counter_path = Path(project_dir) / ".claude" / ".step-counter"

    if not counter_path.exists():
        return 0

    try:
        with open(counter_path, "r") as f:
            data = json.load(f)
            return data.get("count", 0)
    except (json.JSONDecodeError, IOError):
        return 0


def check_transcript_for_incomplete_todos():
    """Check transcript for in_progress todo items."""
    transcript = os.environ.get("CLAUDE_TRANSCRIPT", "")

    if not transcript:
        return False

    # Look for TodoWrite with in_progress items
    if '"status": "in_progress"' in transcript or "'status': 'in_progress'" in transcript:
        last_in_progress = transcript.rfind("in_progress")
        remaining = transcript[last_in_progress:]
        return "completed" not in remaining[:500].lower()

    return False


def handoff_exists_and_recent():
    """Check if handoff.md exists and is recent."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    handoff_path = Path(project_dir) / ".claude" / "handoff.md"

    if not handoff_path.exists():
        return False

    mtime = datetime.fromtimestamp(handoff_path.stat().st_mtime)
    return datetime.now() - mtime < timedelta(minutes=5)


def main():
    # Skip if handoff already written
    if handoff_exists_and_recent():
        return {"continue": True}

    # Collect signals
    signals = []

    # Signal 1: Uncommitted code changes
    uncommitted = get_uncommitted_changes()
    if uncommitted:
        file_list = ", ".join(uncommitted[:5])
        if len(uncommitted) > 5:
            file_list += f" (+{len(uncommitted) - 5} more)"
        signals.append(f"Uncommitted changes: {file_list}")

    # Signal 2: High step count without recent checkpoint
    step_count = get_step_count()
    if step_count >= 3:
        signals.append(f"{step_count} edits since last checkpoint")

    # Signal 3: In-progress todos
    if check_transcript_for_incomplete_todos():
        signals.append("Active in_progress todo items")

    # Require 2+ signals to block (reduces false positives)
    if len(signals) >= 2:
        return {
            "continue": False,
            "stopReason": (
                "Incomplete work detected:\n"
                + "\n".join(f"  - {s}" for s in signals)
                + "\n\nWrite .claude/handoff.md before ending session with:\n"
                "  - What we were doing\n"
                "  - Where we stopped\n"
                "  - Key decisions\n"
                "  - Next steps"
            ),
        }

    # Single signal: advisory warning only
    if len(signals) == 1:
        return {
            "continue": True,
            "message": f"Note: {signals[0]}. Consider writing .claude/handoff.md if work is incomplete.",
        }

    return {"continue": True}


if __name__ == "__main__":
    print(json.dumps(main()))
