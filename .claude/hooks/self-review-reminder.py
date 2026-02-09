#!/usr/bin/env python3
"""
Advisory Stop hook: reminds to run /self-review after large changes.
Triggers when 5+ non-test/non-config source files changed in session.
Always advisory — never blocks.
"""
import json
import os
import subprocess


def get_changed_source_files():
    """Get source files changed relative to main (or recent commits)."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")

    # Try diff against main first (feature branch workflow)
    for base in ["main", "master"]:
        result = subprocess.run(
            ["git", "diff", base, "--name-only"],
            capture_output=True,
            text=True,
            cwd=project_dir,
        )
        if result.returncode == 0 and result.stdout.strip():
            return filter_source_files(result.stdout.strip().split("\n"))

    # Fallback: check uncommitted + last 5 commits
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD~5"],
        capture_output=True,
        text=True,
        cwd=project_dir,
    )
    if result.returncode == 0 and result.stdout.strip():
        return filter_source_files(result.stdout.strip().split("\n"))

    return []


def filter_source_files(files):
    """Filter to source files only (exclude tests, config, .claude/)."""
    skip_patterns = [
        "test_",
        "_test.",
        ".test.",
        "tests/",
        "__pycache__",
        ".claude/",
        ".gitignore",
        "README",
        "BRIEF.md",
        "CLAUDE.md",
        "SPEC.md",
        "PATTERNS.md",
        ".json",
        ".toml",
        ".cfg",
        ".ini",
        ".yml",
        ".yaml",
        ".lock",
        ".md",
    ]

    source_files = []
    for f in files:
        if not any(pattern in f for pattern in skip_patterns):
            source_files.append(f)
    return source_files


def self_review_already_run():
    """Check transcript for evidence that /self-review was already run."""
    transcript = os.environ.get("CLAUDE_TRANSCRIPT", "")
    if not transcript:
        return False
    return "/self-review" in transcript or "self-review" in transcript.lower()


def main():
    # Always advisory
    if self_review_already_run():
        return {"continue": True}

    source_files = get_changed_source_files()

    if len(source_files) < 5:
        return {"continue": True}

    file_list = "\n".join(f"  - {f}" for f in source_files[:10])
    extra = f"\n  ... and {len(source_files) - 10} more" if len(source_files) > 10 else ""

    return {
        "continue": True,
        "message": f"This session modified {len(source_files)} source files:\n"
        f"{file_list}{extra}\n\n"
        "Consider running `/self-review` to check for security, architecture, "
        "and CI gaps before finishing.",
    }


if __name__ == "__main__":
    print(json.dumps(main()))
