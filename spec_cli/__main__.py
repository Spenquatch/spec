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


def resolve_file_path(path: str) -> Path:
    """Resolve and validate a file path for spec generation.

    Args:
        path: Input path string (can be absolute or relative)

    Returns:
        Path object relative to project root

    Raises:
        FileNotFoundError: If the file doesn't exist
        IsADirectoryError: If the path is a directory
        ValueError: If the path is not a regular file
    """
    # Convert string to Path object
    input_path = Path(path)

    # Handle absolute paths - convert to relative to ROOT
    if input_path.is_absolute():
        try:
            resolved_path = input_path.relative_to(ROOT)
        except ValueError as e:
            # Path is outside the project root
            raise ValueError(f"Path is outside project root: {input_path}") from e
    else:
        # Relative path - resolve relative to current working directory
        resolved_path = input_path.resolve().relative_to(ROOT)

    # Check if file exists
    full_path = ROOT / resolved_path
    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {full_path}")

    # Check if it's a directory
    if full_path.is_dir():
        raise IsADirectoryError(f"Path is a directory, not a file: {full_path}")

    # Check if it's a regular file
    if not full_path.is_file():
        raise ValueError(f"Path is not a regular file: {full_path}")

    return resolved_path


def create_spec_directory(file_path: Path) -> Path:
    """Create the spec directory structure for a given file path.

    Args:
        file_path: Path to the source file (relative to project root)

    Returns:
        Path to the created spec directory

    Raises:
        OSError: If directory creation fails due to permissions or other issues
    """
    # Convert file path to spec directory path
    # e.g., src/models.py -> .specs/src/models/
    spec_dir_path = SPECS_DIR / file_path.parent / file_path.stem

    try:
        # Create directory structure with parents=True
        spec_dir_path.mkdir(parents=True, exist_ok=True)

        if DEBUG:
            print(f"🔍 Debug: Created spec directory: {spec_dir_path}")

        return spec_dir_path

    except OSError as e:
        raise OSError(f"Failed to create spec directory {spec_dir_path}: {e}") from e


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
        try:
            resolved_path = resolve_file_path(path_str)
            spec_dir = create_spec_directory(resolved_path)
            print(f"📝 Generating spec for file: {resolved_path}")
            print(f"📁 Spec directory: {spec_dir}")
            # TODO: Implement file spec generation (template + content)
            return
        except (FileNotFoundError, IsADirectoryError, ValueError, OSError) as e:
            print(f"❌ {e}")
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
