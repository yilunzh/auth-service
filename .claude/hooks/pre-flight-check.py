#!/usr/bin/env python3
"""
Advisory UserPromptSubmit hook: validates environment setup on first prompt.
Auto-detects project type (Python/Node) and checks for common setup issues.
Runs once per session via marker file. Never blocks.
"""
import json
import os
import subprocess

STATE_FILE = "/tmp/claude-pre-flight-done"


def detect_project_type(project_dir):
    """Detect project type from config files."""
    types = []
    if os.path.exists(os.path.join(project_dir, "pyproject.toml")) or \
       os.path.exists(os.path.join(project_dir, "setup.py")) or \
       os.path.exists(os.path.join(project_dir, "requirements.txt")):
        types.append("python")
    if os.path.exists(os.path.join(project_dir, "package.json")):
        types.append("node")
    return types


def check_python(project_dir):
    """Check Python environment setup."""
    issues = []

    # Check for virtual environment
    venv_paths = [
        os.path.join(project_dir, ".venv"),
        os.path.join(project_dir, "venv"),
    ]
    venv_found = any(os.path.isdir(p) for p in venv_paths)
    if not venv_found:
        issues.append("No virtual environment found (.venv/ or venv/). Create one with: python -m venv .venv")
        return issues  # Can't check further without venv

    # Find the active venv
    venv_dir = next(p for p in venv_paths if os.path.isdir(p))
    python_bin = os.path.join(venv_dir, "bin", "python")

    if not os.path.exists(python_bin):
        issues.append(f"Virtual environment at {os.path.basename(venv_dir)}/ exists but has no python binary")
        return issues

    # Check Python version against requires-python in pyproject.toml
    pyproject_path = os.path.join(project_dir, "pyproject.toml")
    if os.path.exists(pyproject_path):
        try:
            with open(pyproject_path) as f:
                content = f.read()
            # Simple parse for requires-python
            for line in content.split("\n"):
                if "requires-python" in line:
                    required = line.split("=", 1)[-1].strip().strip('"').strip("'")
                    result = subprocess.run(
                        [python_bin, "--version"],
                        capture_output=True, text=True,
                    )
                    if result.returncode == 0:
                        version = result.stdout.strip().replace("Python ", "")
                        # Just inform, don't try to parse version constraints
                        issues.append(
                            f"Python version: {version} (requires-python: {required}). "
                            "Verify compatibility if you see import errors."
                        ) if ">=" not in required or version < required.replace(">=", "").strip() else None
                    break
        except Exception:
            pass

    # Check if key dependencies are installed
    req_files = ["requirements.txt", "requirements-dev.txt"]
    for req_file in req_files:
        req_path = os.path.join(project_dir, req_file)
        if os.path.exists(req_path):
            result = subprocess.run(
                [python_bin, "-m", "pip", "list", "--format=columns"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                installed = result.stdout.lower()
                with open(req_path) as f:
                    for line in f:
                        pkg = line.strip().split("==")[0].split(">=")[0].split("~=")[0].strip().lower()
                        if pkg and not pkg.startswith("#") and not pkg.startswith("-"):
                            if pkg.replace("-", "_") not in installed.replace("-", "_"):
                                issues.append(
                                    f"Package '{pkg}' from {req_file} may not be installed. "
                                    f"Run: {venv_dir}/bin/pip install -r {req_file}"
                                )
                                break  # One warning is enough
            break

    return issues


def check_node(project_dir):
    """Check Node.js environment setup."""
    issues = []

    # Check for node_modules
    if not os.path.isdir(os.path.join(project_dir, "node_modules")):
        issues.append("node_modules/ not found. Run: npm install")
        return issues

    # Check Node version against engines in package.json
    pkg_path = os.path.join(project_dir, "package.json")
    if os.path.exists(pkg_path):
        try:
            with open(pkg_path) as f:
                import json as j
                pkg = j.load(f)
            engines = pkg.get("engines", {})
            if "node" in engines:
                result = subprocess.run(
                    ["node", "--version"],
                    capture_output=True, text=True,
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    required = engines["node"]
                    # Informational only
                    issues.append(
                        f"Node version: {version} (engines.node: {required}). "
                        "Verify compatibility if you see module errors."
                    ) if version else None
        except Exception:
            pass

    return issues


def main():
    session_id = os.environ.get("CLAUDE_SESSION_ID", "default")
    state_file = f"{STATE_FILE}-{session_id}"

    # Only run once per session
    if os.path.exists(state_file):
        return {"continue": True}

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")

    # Mark as done regardless of result
    try:
        with open(state_file, "w") as f:
            f.write("done")
    except Exception:
        pass

    project_types = detect_project_type(project_dir)

    if not project_types:
        return {"continue": True}  # Can't detect project type, skip silently

    all_issues = []

    if "python" in project_types:
        all_issues.extend(check_python(project_dir))
    if "node" in project_types:
        all_issues.extend(check_node(project_dir))

    if not all_issues:
        return {"continue": True}

    issue_list = "\n".join(f"  - {issue}" for issue in all_issues)
    return {
        "continue": True,
        "message": f"Environment check ({', '.join(project_types)} project):\n{issue_list}",
    }


if __name__ == "__main__":
    print(json.dumps(main()))
