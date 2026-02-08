#!/usr/bin/env python3
"""Block commits if tests/lint fail or committing to main.

Language-agnostic: Auto-detects test runner and linter based on project files.
"""
import subprocess
import json
import os
from pathlib import Path


def get_current_branch():
    """Get the current git branch name."""
    result = subprocess.run(
        ["git", "branch", "--show-current"], capture_output=True, text=True
    )
    return result.stdout.strip()


def get_staged_file_count():
    """Count total staged files."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True
    )
    files = [f for f in result.stdout.strip().split("\n") if f]
    return len(files)


def detect_test_runner():
    """Detect test runner based on project files."""
    # Node.js projects
    if os.path.exists("package.json"):
        try:
            with open("package.json") as f:
                pkg = json.load(f)
                if "test" in pkg.get("scripts", {}):
                    return ["npm", "test"]
        except (json.JSONDecodeError, IOError):
            pass
        # Check for specific test frameworks
        if os.path.exists("vitest.config.ts") or os.path.exists("vitest.config.js"):
            return ["npx", "vitest", "run"]
        if os.path.exists("jest.config.js") or os.path.exists("jest.config.ts"):
            return ["npx", "jest"]

    # Python projects
    if os.path.exists("requirements.txt") or os.path.exists("pyproject.toml"):
        if os.path.exists("pytest.ini") or os.path.exists("conftest.py"):
            return ["pytest", "-v", "--tb=short", "-q"]
        if os.path.exists("pyproject.toml"):
            try:
                with open("pyproject.toml") as f:
                    if "pytest" in f.read():
                        return ["pytest", "-v", "--tb=short", "-q"]
            except IOError:
                pass
        return ["python", "-m", "unittest", "discover"]

    # Rust projects
    if os.path.exists("Cargo.toml"):
        return ["cargo", "test"]

    # Go projects
    if os.path.exists("go.mod"):
        return ["go", "test", "./..."]

    return None


def detect_linter():
    """Detect linter based on project files."""
    # Node.js linters
    if os.path.exists(".eslintrc.js") or os.path.exists(".eslintrc.json") or os.path.exists("eslint.config.js"):
        return ["npx", "eslint", "."]

    # Python linters
    if os.path.exists("pyproject.toml"):
        try:
            with open("pyproject.toml") as f:
                content = f.read()
                if "ruff" in content:
                    return ["ruff", "check", "."]
        except IOError:
            pass
    if os.path.exists(".flake8") or os.path.exists("setup.cfg"):
        return ["flake8"]

    # Rust linter
    if os.path.exists("Cargo.toml"):
        return ["cargo", "clippy"]

    # Go linter
    if os.path.exists("go.mod"):
        return ["go", "vet", "./..."]

    return None


def run_command(cmd, name):
    """Run a command and return result."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    return {
        "name": name,
        "passed": result.returncode == 0,
        "output": (result.stdout + result.stderr)[-1500:],
    }


def main():
    checks = []

    # Check branch policy: block ALL commits to main
    branch = get_current_branch()
    file_count = get_staged_file_count()
    if branch == "main" and file_count > 0:
        return {
            "decision": "block",
            "reason": "Cannot commit directly to main.\n"
            "Create a feature branch: git checkout -b feature/<name>\n"
            "Then open a PR to merge into main.",
        }

    # Detect and run linter
    linter_cmd = detect_linter()
    if linter_cmd:
        checks.append(run_command(linter_cmd, f"Lint ({linter_cmd[0]})"))

    # Detect and run tests
    test_cmd = detect_test_runner()
    if test_cmd:
        checks.append(run_command(test_cmd, f"Tests ({test_cmd[0]})"))
    else:
        # No test runner detected - advisory only
        return {
            "decision": "allow",
            "message": "No test runner detected. Consider adding tests."
        }

    failed = [c for c in checks if not c["passed"]]
    if failed:
        reasons = [f"{c['name']}:\n{c['output']}" for c in failed]
        return {
            "decision": "block",
            "reason": "Pre-commit checks failed:\n\n" + "\n---\n".join(reasons),
        }
    return {"decision": "allow"}


if __name__ == "__main__":
    print(json.dumps(main()))
