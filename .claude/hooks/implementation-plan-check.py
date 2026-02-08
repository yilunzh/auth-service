#!/usr/bin/env python3
"""
Check if implementation plan needs updating when working on features with ideation docs.

Triggers:
- Pre-commit: Advisory reminder if code changed but no plan updated
- Stop: Advisory reminder to update plan before ending session

Advisory only - doesn't block commits.

NOTE: Only applies to features that went through /ideate and have implementation plans.
"""
import json
import os
import subprocess
from pathlib import Path


def get_current_branch():
    """Get current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        cwd=os.environ.get("CLAUDE_PROJECT_DIR", "."),
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def get_matching_feature(branch, features_with_plans):
    """Find ideation feature that matches current branch.

    Matches if the feature name appears anywhere in the branch name.
    Example: "bank-import" matches "feature/bank-import"
    """
    for feature in features_with_plans:
        if feature in branch:
            return feature
    return None


def get_all_ideation_features(project_dir):
    """Get all features that have implementation plans in ideation folders."""
    ideation_dir = Path(project_dir) / ".claude" / "ideation"
    if not ideation_dir.exists():
        return []

    features = []
    for folder in ideation_dir.iterdir():
        if folder.is_dir() and (folder / "implementation-plan.md").exists():
            features.append(folder.name)
    return features


def get_staged_files():
    """Get list of staged files."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            cwd=os.environ.get("CLAUDE_PROJECT_DIR", "."),
        )
        return result.stdout.strip().split("\n") if result.stdout.strip() else []
    except Exception:
        return []


def get_modified_files():
    """Get list of all modified files (staged + unstaged)."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=os.environ.get("CLAUDE_PROJECT_DIR", "."),
        )
        files = []
        for line in result.stdout.strip().split("\n"):
            if line:
                # Format: XY filename (XY is status, filename starts at position 3)
                files.append(line[3:].strip())
        return files
    except Exception:
        return []


def is_code_file(file_path):
    """Check if file is a code file (not docs, not ideation)."""
    # Skip ideation docs
    if ".claude/ideation" in file_path:
        return False
    # Skip markdown docs (but not CLAUDE.md)
    if file_path.endswith(".md") and "CLAUDE" not in file_path:
        return False

    code_extensions = [".py", ".swift", ".ts", ".js", ".tsx", ".jsx", ".yaml", ".yml", ".json", ".html", ".css"]
    return any(file_path.endswith(ext) for ext in code_extensions)


def get_updated_plans(files):
    """Get list of implementation plans that were updated."""
    updated = []
    for f in files:
        if ".claude/ideation/" in f and "implementation-plan.md" in f:
            # Extract feature name from path
            parts = f.split("/")
            try:
                idx = parts.index("ideation")
                if idx + 1 < len(parts):
                    updated.append(parts[idx + 1])
            except ValueError:
                pass
    return updated


def main():
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    hook_type = os.environ.get("CLAUDE_HOOK_TYPE", "")

    # Get all features with implementation plans
    features_with_plans = get_all_ideation_features(project_dir)

    if not features_with_plans:
        return {"continue": True}

    # Determine which files to check based on hook type
    if hook_type == "PreToolUse":
        files = get_staged_files()
    else:
        files = get_modified_files()

    if not files:
        return {"continue": True}

    # Check if any code files are being changed
    has_code_changes = any(is_code_file(f) for f in files)
    if not has_code_changes:
        return {"continue": True}

    # Check which plans were updated
    updated_plans = get_updated_plans(files)

    # Only remind about the feature matching the current branch
    current_branch = get_current_branch()
    current_feature = get_matching_feature(current_branch, features_with_plans)

    # If no matching feature or the plan was already updated, no reminder needed
    if current_feature and current_feature not in updated_plans:
        plans_needing_update = [current_feature]
    else:
        plans_needing_update = []

    if plans_needing_update:
        plan_list = "\n".join(
            f"  - .claude/ideation/{f}/implementation-plan.md"
            for f in plans_needing_update
        )
        return {
            "continue": True,  # Advisory - don't block
            "message": f"ACTION REQUIRED: Update the implementation plan before committing.\n\n"
                       f"Plan to update:\n{plan_list}\n\n"
                       f"You MUST:\n"
                       f"1. Read the implementation plan\n"
                       f"2. Mark completed stories/tasks with [x]\n"
                       f"3. Update the Progress Summary table status\n"
                       f"4. Update the 'Last Updated' date to today\n"
                       f"5. Stage the updated plan file with the commit"
        }

    return {"continue": True}


if __name__ == "__main__":
    print(json.dumps(main()))
