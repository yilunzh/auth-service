#!/usr/bin/env python3
"""Prompt agent to verify work before ending session.

This hook runs at Stop and checks if tests were run during the session.
If no test execution is detected, it blocks completion.
"""
import json
import os


def main():
    # Get transcript from environment (if available)
    transcript = os.environ.get("CLAUDE_TRANSCRIPT", "")

    # If no transcript available, allow but remind
    if not transcript:
        return {
            "continue": True,
            "message": "Reminder: Ensure you ran tests before finishing.",
        }

    transcript_lower = transcript.lower()

    # Check for common test runner patterns
    test_patterns = [
        "pytest",
        "npm test",
        "npx vitest",
        "npx jest",
        "cargo test",
        "go test",
        "unittest",
    ]

    test_ran = any(pattern in transcript_lower for pattern in test_patterns)

    if not test_ran:
        return {
            "continue": False,
            "stopReason": "Tests haven't been run this session. "
            "Run your project's test suite before finishing.",
        }

    # Check for unresolved test failures
    if "failed" in transcript_lower or "error" in transcript_lower:
        # Find the last occurrence of test results
        last_failed_idx = max(
            transcript_lower.rfind("failed"),
            transcript_lower.rfind("error")
        )
        remaining = transcript_lower[last_failed_idx:]
        # If there's no "passed" or "0 failed" after, tests might still be failing
        if "passed" not in remaining and "0 failed" not in remaining and "ok" not in remaining:
            return {
                "continue": False,
                "stopReason": "Tests appear to be failing. "
                "Fix failing tests before finishing.",
            }

    return {"continue": True}


if __name__ == "__main__":
    print(json.dumps(main()))
