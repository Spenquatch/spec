#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

ROOT = Path.cwd()
SPEC_DIR = ROOT / ".spec"
INDEX_FILE = ROOT / ".spec-index"
SPECS_DIR = ROOT / ".specs"
IGNORE_FILE = ROOT / ".specignore"
GITIGNORE = ROOT / ".gitignore"

DEBUG = os.environ.get("SPEC_DEBUG", "").lower() in ["1", "true", "yes"]


def run_git(args: List[str]) -> None:
    env = os.environ.copy()
    env.update(
        {
            "GIT_DIR": str(SPEC_DIR),
            "GIT_WORK_TREE": str(SPECS_DIR),
            "GIT_INDEX_FILE": str(INDEX_FILE),
        }
    )
    # Convert paths to be relative to SPECS_DIR for add commands
    if args and args[0] in ["add", "rm"]:
        processed_args = [args[0]]
        if args[0] == "add" and "-f" not in args[1:]:
            processed_args.append("-f")
        for arg in args[1:]:
            if arg.startswith("-"):
                processed_args.append(arg)
            else:
                # Convert .specs/file.md to file.md
                path = Path(arg)
                if path.is_absolute():
                    path = path.relative_to(SPECS_DIR)
                elif str(path).startswith(".specs/"):
                    path = Path(str(path).replace(".specs/", "", 1))
                processed_args.append(str(path))
        args = processed_args

    cmd = ["git", "-c", "core.excludesFile=", "-c", "core.ignoresCase=false", *args]

    if DEBUG:
        print(f"🔍 Debug: Running command: {' '.join(cmd)}")
        print("🔍 Debug: Environment:")
        for k, v in env.items():
            if k.startswith("GIT_"):
                print(f"   {k}={v}")

    subprocess.check_call(cmd, env=env)


def cmd_init(_: List[str]) -> None:
    # 1. Create .spec/ as bare Git repo
    if not SPEC_DIR.exists():
        SPEC_DIR.mkdir()
        subprocess.check_call(["git", "init", "--bare", str(SPEC_DIR)])
        print("✅ .spec/ initialized")
    else:
        print("ℹ️ .spec/ already exists, skipping init")

    # 2. Create .specignore
    if not IGNORE_FILE.exists():
        IGNORE_FILE.write_text("*\n!/.specs/**\n!/.specs/**/*.md\n")
        print("✅ .specignore created")
    else:
        print("ℹ️ .specignore already exists")

    # 3. Copy into Git exclude
    (SPEC_DIR / "info").mkdir(parents=True, exist_ok=True)
    (SPEC_DIR / "info" / "exclude").write_text(IGNORE_FILE.read_text())
    print("✅ .spec/info/exclude synced")

    # 4. Create .specs/ mirror
    SPECS_DIR.mkdir(exist_ok=True)
    print("✅ .specs/ directory ready")

    # 5. Append to .gitignore (if .git exists)
    if (ROOT / ".git").exists():
        GITIGNORE.touch()
        lines = GITIGNORE.read_text().splitlines()
        added = False
        for entry in [".spec/", ".specs/", ".spec-index"]:
            if entry not in lines:
                lines.append(entry)
                added = True
        if added:
            GITIGNORE.write_text("\n".join(lines) + "\n")
            print("✅ .gitignore updated")
        else:
            print("ℹ️ .gitignore already configured")


def cmd_add(paths: List[str]) -> None:
    run_git(["add", *paths])
    print("✅ Staged specs:", *paths)


def cmd_commit(args: List[str]) -> None:
    msg = " ".join(args) or "spec update"
    run_git(["commit", "-m", msg])
    print("✅ Commit written:", msg)


def cmd_log(args: List[str]) -> None:
    run_git(["log", "--", *args] if args else ["log"])


def cmd_diff(args: List[str]) -> None:
    run_git(["diff", "--", *args] if args else ["diff"])


def cmd_status(_: List[str]) -> None:
    run_git(["status"])


def cmd_gen(args: List[str]) -> None:
    """Generate spec documentation for file(s) or directory."""
    if not args:
        print("❌ Please specify a file or directory to generate specs for")
        return

    path_str = args[0]
    path = Path(path_str)

    # Handle "." for current directory
    if path_str == ".":
        path = Path.cwd()

    # Check if path exists
    if not path.exists():
        print(f"❌ Path not found: {path}")
        return

    # Handle single file
    if path.is_file():
        print(f"📝 Generating spec for file: {path}")
        # TODO: Implement file spec generation
        return

    # Handle directory
    if path.is_dir():
        print(f"📁 Generating specs for directory: {path}")
        # TODO: Implement directory spec generation
        return

    print(f"❌ Path is neither a file nor directory: {path}")


COMMANDS = {
    "init": cmd_init,
    "add": cmd_add,
    "commit": cmd_commit,
    "log": cmd_log,
    "diff": cmd_diff,
    "status": cmd_status,
    "gen": cmd_gen,
}


def main(argv: Optional[List[str]] = None) -> None:
    argv = argv or sys.argv[1:]
    if not argv or argv[0] not in COMMANDS:
        print("Usage: spec [init|add|commit|log|diff|status|gen]")
        sys.exit(1)
    COMMANDS[argv[0]](argv[1:])


if __name__ == "__main__":
    main()
