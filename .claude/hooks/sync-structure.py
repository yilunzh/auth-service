#!/usr/bin/env python3
"""
Generate project structure tree for SPEC.md documentation.
Excludes: venv, __pycache__, .git, instance/, node_modules, etc.

Usage:
    python3 .claude/hooks/sync-structure.py

Output can be copied into SPEC.md Section 7 (Project Structure).
"""
import os
from pathlib import Path

# Directories to exclude
EXCLUDE_DIRS = {
    "venv",
    "__pycache__",
    ".git",
    "node_modules",
    ".pytest_cache",
    ".mypy_cache",
    "instance",
    ".venv",
    "env",
    ".env",
    "dist",
    "build",
    "*.egg-info",
}

# Files to exclude
EXCLUDE_FILES = {
    ".DS_Store",
    "*.pyc",
    "*.pyo",
    "*.so",
    "*.db",
    "Thumbs.db",
}

# Known file annotations
ANNOTATIONS = {
    "app.py": "# Main Flask application",
    "models.py": "# SQLAlchemy models",
    "auth.py": "# Flask-Login configuration",
    "decorators.py": "# Custom decorators",
    "household_context.py": "# Household session helpers",
    "email_service.py": "# Flask-Mail integration",
    "utils.py": "# Helper functions",
    "requirements.txt": "# Python dependencies",
    "requirements-dev.txt": "# Dev dependencies",
    "Procfile": "# Production server config",
    "CLAUDE.md": "# Claude Code guidance",
    ".env.example": "# Environment variable template",
    ".gitignore": "# Git ignore rules",
}


def should_exclude_dir(name):
    """Check if directory should be excluded."""
    if name in EXCLUDE_DIRS:
        return True
    if name.startswith(".") and name not in {".claude", ".github"}:
        return True
    return False


def should_exclude_file(name):
    """Check if file should be excluded."""
    if name in EXCLUDE_FILES:
        return True
    for pattern in EXCLUDE_FILES:
        if pattern.startswith("*") and name.endswith(pattern[1:]):
            return True
    return False


def get_annotation(name):
    """Get annotation for known files."""
    return ANNOTATIONS.get(name, "")


def generate_tree(root_path, prefix="", is_last=True):
    """Generate tree structure recursively."""
    lines = []
    root = Path(root_path)

    # Get and sort entries (directories first, then files)
    try:
        entries = sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
    except PermissionError:
        return lines

    # Filter out excluded entries
    entries = [
        e for e in entries
        if not (e.is_dir() and should_exclude_dir(e.name))
        and not (e.is_file() and should_exclude_file(e.name))
    ]

    for i, entry in enumerate(entries):
        is_entry_last = i == len(entries) - 1

        # Choose connector
        connector = "└── " if is_entry_last else "├── "

        # Get annotation
        annotation = get_annotation(entry.name)
        annotation_str = f"  {annotation}" if annotation else ""

        # Add line
        if entry.is_dir():
            lines.append(f"{prefix}{connector}{entry.name}/")
            # Recurse into directory
            extension = "    " if is_entry_last else "│   "
            lines.extend(generate_tree(entry, prefix + extension, is_entry_last))
        else:
            lines.append(f"{prefix}{connector}{entry.name}{annotation_str}")

    return lines


def main():
    """Generate and print project structure."""
    # Get project root
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", os.getcwd())
    root = Path(project_dir)

    print(f"{root.name}/")
    for line in generate_tree(root):
        print(line)

    print("\n---")
    print("Copy the above structure into docs/SPEC.md Section 7 (Project Structure)")


if __name__ == "__main__":
    main()
