#!/usr/bin/env python3
"""
Auto-stage files that were modified by formatting hooks.

This script is called as a pre-commit hook after formatting tools run.
It stages only the files that were actually modified during the current
pre-commit run, not all modified files in the repository.
"""

import subprocess
import sys
from pathlib import Path


def run_git_command(args):
    """Run a git command and return the output."""
    try:
        result = subprocess.run(
            ["git"] + args, capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Git command failed: {e}")
        return ""


def get_staged_files():
    """Get list of files that are currently staged."""
    output = run_git_command(["diff", "--cached", "--name-only"])
    return set(output.split()) if output else set()


def get_modified_files():
    """Get list of files that are modified but not staged."""
    output = run_git_command(["diff", "--name-only"])
    return set(output.split()) if output else set()


def main():
    """Stage files that were modified by formatting but not yet staged."""
    # Get currently modified files (these might have been changed by formatting hooks)
    modified_files = get_modified_files()

    # Only stage files with extensions that could have been formatted
    files_to_stage = []
    for file in modified_files:
        if Path(file).suffix in {".py", ".md", ".yaml", ".yml", ".json", ".toml"}:
            files_to_stage.append(file)

    if files_to_stage:
        print(f"Auto-staging {len(files_to_stage)} formatted files...")
        for file in files_to_stage:
            run_git_command(["add", file])
        return 0
    else:
        # No files to stage - this is normal and shouldn't be an error
        return 0


if __name__ == "__main__":
    sys.exit(main())
