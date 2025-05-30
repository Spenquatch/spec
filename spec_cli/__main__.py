#!/usr/bin/env python3
import fnmatch
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml
from pydantic import BaseModel, Field

ROOT = Path.cwd()
SPEC_DIR = ROOT / ".spec"
INDEX_FILE = ROOT / ".spec-index"
SPECS_DIR = ROOT / ".specs"
IGNORE_FILE = ROOT / ".specignore"
GITIGNORE = ROOT / ".gitignore"
TEMPLATE_FILE = ROOT / ".spectemplate"

DEBUG = os.environ.get("SPEC_DEBUG", "").lower() in ["1", "true", "yes"]


class TemplateConfig(BaseModel):
    """Configuration for spec template generation."""

    index: str = Field(
        default="""# {{filename}}

**Location**: {{filepath}}

**Purpose**: {{purpose}}

**Responsibilities**:
{{responsibilities}}

**Requirements**:
{{requirements}}

**Example Usage**:
```{{file_extension}}
{{example_usage}}
```

**Notes**:
{{notes}}
""",
        description="Template for index.md file",
    )

    history: str = Field(
        default="""# History for {{filename}}

## {{date}} - Initial Creation

**Purpose**: Created initial specification for {{filename}}

**Context**: {{context}}

**Decisions**: {{decisions}}

**Lessons Learned**: {{lessons}}
""",
        description="Template for history.md file",
    )


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


def load_template() -> TemplateConfig:
    """Load template configuration from .spectemplate file or use defaults.

    Returns:
        TemplateConfig object with loaded or default templates

    Raises:
        yaml.YAMLError: If template file exists but contains invalid YAML
        ValueError: If template file contains invalid configuration
    """
    if not TEMPLATE_FILE.exists():
        if DEBUG:
            print("🔍 Debug: No .spectemplate file found, using default template")
        return TemplateConfig()

    try:
        with TEMPLATE_FILE.open("r", encoding="utf-8") as f:
            template_data = yaml.safe_load(f)

        if DEBUG:
            print(f"🔍 Debug: Loaded template from {TEMPLATE_FILE}")

        # Handle case where YAML file is empty or None
        if template_data is None:
            template_data = {}

        return TemplateConfig(**template_data)

    except yaml.YAMLError as e:
        raise yaml.YAMLError(
            f"Invalid YAML in template file {TEMPLATE_FILE}: {e}"
        ) from e
    except Exception as e:
        raise ValueError(
            f"Invalid template configuration in {TEMPLATE_FILE}: {e}"
        ) from e


def generate_spec_content(
    file_path: Path, spec_dir: Path, template: TemplateConfig
) -> None:
    """Generate spec content files using template substitution.

    Args:
        file_path: Path to the source file (relative to project root)
        spec_dir: Path to the spec directory where files will be written
        template: Template configuration with index and history templates

    Raises:
        OSError: If file writing fails due to permissions or other issues
    """
    # Prepare template substitution variables
    now = datetime.now()
    substitutions = {
        "filename": file_path.name,
        "filepath": str(file_path),
        "date": now.strftime("%Y-%m-%d"),
        "file_extension": file_path.suffix.lstrip(".") or "txt",
        # Placeholder values - these would be enhanced with AI integration later
        "purpose": "[Generated by spec-cli - to be filled]",
        "responsibilities": "[Generated by spec-cli - to be filled]",
        "requirements": "[Generated by spec-cli - to be filled]",
        "example_usage": "[Generated by spec-cli - to be filled]",
        "notes": "[Generated by spec-cli - to be filled]",
        "context": "[Generated by spec-cli - to be filled]",
        "decisions": "[Generated by spec-cli - to be filled]",
        "lessons": "[Generated by spec-cli - to be filled]",
    }

    try:
        # Generate index.md content
        index_content = _substitute_template(template.index, substitutions)
        index_file = spec_dir / "index.md"
        index_file.write_text(index_content, encoding="utf-8")

        # Generate history.md content
        history_content = _substitute_template(template.history, substitutions)
        history_file = spec_dir / "history.md"
        history_file.write_text(history_content, encoding="utf-8")

        if DEBUG:
            print(f"🔍 Debug: Generated index.md ({len(index_content)} chars)")
            print(f"🔍 Debug: Generated history.md ({len(history_content)} chars)")

    except OSError as e:
        raise OSError(f"Failed to write spec files to {spec_dir}: {e}") from e


def _substitute_template(template: str, substitutions: Dict[str, str]) -> str:
    """Substitute placeholders in template with provided values.

    Args:
        template: Template string with {{placeholder}} syntax
        substitutions: Dictionary mapping placeholder names to values

    Returns:
        Template string with placeholders replaced
    """
    result = template
    for key, value in substitutions.items():
        placeholder = f"{{{{{key}}}}}"
        result = result.replace(placeholder, value)
    return result


def get_file_type(file_path: Path) -> str:
    """Determine the file type category based on file extension.

    Args:
        file_path: Path to the file

    Returns:
        String representing the file type category
    """
    extension = file_path.suffix.lower()

    # Programming languages
    if extension in {".py", ".pyx", ".pyi"}:
        return "python"
    elif extension in {".js", ".jsx", ".ts", ".tsx"}:
        return "javascript"
    elif extension in {".java", ".class"}:
        return "java"
    elif extension in {".c", ".h"}:
        return "c"
    elif extension in {".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx"}:
        return "cpp"
    elif extension in {".rs"}:
        return "rust"
    elif extension in {".go"}:
        return "go"
    elif extension in {".rb"}:
        return "ruby"
    elif extension in {".php"}:
        return "php"
    elif extension in {".swift"}:
        return "swift"
    elif extension in {".kt", ".kts"}:
        return "kotlin"
    elif extension in {".scala"}:
        return "scala"
    elif extension in {".cs"}:
        return "csharp"
    elif extension in {".vb"}:
        return "visualbasic"

    # Web technologies
    elif extension in {".html", ".htm"}:
        return "html"
    elif extension in {".css", ".scss", ".sass", ".less"}:
        return "css"
    elif extension in {".xml", ".xsl", ".xsd"}:
        return "xml"

    # Data formats
    elif extension in {".json"}:
        return "json"
    elif extension in {".yaml", ".yml"}:
        return "yaml"
    elif extension in {".toml"}:
        return "toml"
    elif extension in {".csv"}:
        return "csv"
    elif extension in {".sql"}:
        return "sql"

    # Documentation
    elif extension in {".md", ".markdown"}:
        return "markdown"
    elif extension in {".rst"}:
        return "restructuredtext"
    elif extension in {".txt"}:
        return "text"

    # Configuration
    elif extension in {".conf", ".config", ".cfg", ".ini"}:
        return "config"
    elif extension in {".env"} or file_path.name.lower() == ".env":
        return "environment"

    # Build/Package files
    elif file_path.name.lower() in {
        "makefile",
        "dockerfile",
        "vagrantfile",
        "rakefile",
    }:
        return "build"
    elif extension in {".mk", ".make"}:
        return "build"

    # No extension or unknown
    elif not extension:
        return "no_extension"
    else:
        return "unknown"


def load_specignore_patterns() -> Set[str]:
    """Load ignore patterns from .specignore file.

    Returns:
        Set of ignore patterns
    """
    patterns = set()

    if IGNORE_FILE.exists():
        try:
            content = IGNORE_FILE.read_text(encoding="utf-8")
            for line in content.splitlines():
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith("#"):
                    patterns.add(line)
        except OSError as e:
            if DEBUG:
                print(f"🔍 Debug: Failed to read .specignore: {e}")

    # Add default patterns
    default_patterns = {
        "*.pyc",
        "*.pyo",
        "*.pyd",
        "__pycache__/*",
        ".git/*",
        ".svn/*",
        ".hg/*",
        "node_modules/*",
        ".venv/*",
        ".env/*",
        "venv/*",
        "env/*",
        "*.egg-info/*",
        "build/*",
        "dist/*",
        ".pytest_cache/*",
        ".coverage",
        "htmlcov/*",
        ".tox/*",
        ".mypy_cache/*",
        ".ruff_cache/*",
        "*.log",
        "*.tmp",
        "*.temp",
        "*.bak",
        "*.swp",
        "*.swo",
        "*~",
        ".DS_Store",
        "Thumbs.db",
    }
    patterns.update(default_patterns)

    if DEBUG:
        print(f"🔍 Debug: Loaded {len(patterns)} ignore patterns")

    return patterns


def should_generate_spec(
    file_path: Path, ignore_patterns: Optional[Set[str]] = None
) -> bool:
    """Determine if a spec should be generated for the given file.

    Args:
        file_path: Path to the file (relative to project root)
        ignore_patterns: Optional set of ignore patterns (loaded automatically if None)

    Returns:
        True if spec should be generated, False otherwise
    """
    if ignore_patterns is None:
        ignore_patterns = load_specignore_patterns()

    # Convert to string for pattern matching
    file_str = str(file_path)
    file_name = file_path.name

    # Check against ignore patterns
    for pattern in ignore_patterns:
        # Match against full path
        if fnmatch.fnmatch(file_str, pattern):
            if DEBUG:
                print(f"🔍 Debug: File {file_path} matches ignore pattern: {pattern}")
            return False

        # Match against filename only
        if fnmatch.fnmatch(file_name, pattern):
            if DEBUG:
                print(f"🔍 Debug: File {file_path} matches ignore pattern: {pattern}")
            return False

        # Handle directory patterns (ending with /*)
        if pattern.endswith("/*"):
            dir_pattern = pattern[:-2]  # Remove /*
            # Check if file is in the ignored directory
            for parent in file_path.parents:
                if fnmatch.fnmatch(str(parent), dir_pattern) or fnmatch.fnmatch(
                    parent.name, dir_pattern
                ):
                    if DEBUG:
                        print(
                            f"🔍 Debug: File {file_path} in ignored directory: {pattern}"
                        )
                    return False

    # Check file type - only generate for known file types
    file_type = get_file_type(file_path)
    if file_type in {"unknown"}:
        if DEBUG:
            print(f"🔍 Debug: Skipping unknown file type: {file_path}")
        return False

    # Skip binary files and images
    binary_extensions = {
        ".exe",
        ".dll",
        ".so",
        ".dylib",
        ".a",
        ".lib",
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".bmp",
        ".svg",
        ".ico",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".zip",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
        ".7z",
        ".rar",
        ".mp3",
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".wav",
        ".flac",
    }

    if file_path.suffix.lower() in binary_extensions:
        if DEBUG:
            print(f"🔍 Debug: Skipping binary file: {file_path}")
        return False

    # Skip very large files (>1MB)
    try:
        full_path = ROOT / file_path
        if full_path.exists() and full_path.stat().st_size > 1_048_576:  # 1MB
            if DEBUG:
                print(
                    f"🔍 Debug: Skipping large file: {file_path} ({full_path.stat().st_size} bytes)"
                )
            return False
    except OSError:
        # If we can't check size, assume it's okay
        pass

    if DEBUG:
        print(
            f"🔍 Debug: File {file_path} approved for spec generation (type: {file_type})"
        )

    return True


def check_existing_specs(spec_dir: Path) -> Dict[str, bool]:
    """Check if spec files already exist in the spec directory.

    Args:
        spec_dir: Path to the spec directory

    Returns:
        Dict with 'index' and 'history' keys indicating which files exist
    """
    index_file = spec_dir / "index.md"
    history_file = spec_dir / "history.md"

    result = {"index": index_file.exists(), "history": history_file.exists()}

    if DEBUG:
        print(f"🔍 Debug: Checking existing specs in {spec_dir}:")
        print(f"   index.md: {'exists' if result['index'] else 'not found'}")
        print(f"   history.md: {'exists' if result['history'] else 'not found'}")

    return result


def create_backup(file_path: Path) -> Optional[Path]:
    """Create a backup of an existing file.

    Args:
        file_path: Path to the file to backup

    Returns:
        Path to the backup file, or None if backup failed

    Raises:
        OSError: If backup creation fails
    """
    if not file_path.exists():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = file_path.with_suffix(f".{timestamp}.backup")

    try:
        shutil.copy2(file_path, backup_path)

        if DEBUG:
            print(f"🔍 Debug: Created backup: {backup_path}")

        return backup_path

    except OSError as e:
        raise OSError(f"Failed to create backup of {file_path}: {e}") from e


def handle_spec_conflict(
    spec_dir: Path, existing_specs: Dict[str, bool], force: bool = False
) -> str:
    """Handle conflicts when spec files already exist.

    Args:
        spec_dir: Path to the spec directory
        existing_specs: Dict indicating which spec files exist
        force: If True, overwrite without prompting

    Returns:
        Action to take: 'overwrite', 'backup', 'skip', or 'abort'

    Raises:
        KeyboardInterrupt: If user cancels operation
    """
    if not any(existing_specs.values()):
        return "proceed"  # No conflicts

    existing_files = [name for name, exists in existing_specs.items() if exists]

    if force:
        if DEBUG:
            print(
                f"🔍 Debug: Force mode - overwriting existing files: {existing_files}"
            )
        return "overwrite"

    print(f"⚠️  Existing spec files found in {spec_dir}:")
    for file_name in existing_files:
        file_path = spec_dir / f"{file_name}.md"
        # Show file info
        try:
            stat = file_path.stat()
            size = stat.st_size
            mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
            print(f"   📄 {file_name}.md ({size} bytes, modified {mtime})")
        except OSError:
            print(f"   📄 {file_name}.md")

    print("\nChoose an action:")
    print("  [o] Overwrite existing files")
    print("  [b] Backup existing files and create new ones")
    print("  [s] Skip generation for this file")
    print("  [q] Quit/abort operation")

    while True:
        try:
            choice = input("\nYour choice [o/b/s/q]: ").lower().strip()

            if choice in ["o", "overwrite"]:
                return "overwrite"
            elif choice in ["b", "backup"]:
                return "backup"
            elif choice in ["s", "skip"]:
                return "skip"
            elif choice in ["q", "quit", "abort"]:
                return "abort"
            else:
                print("Invalid choice. Please enter 'o', 'b', 's', or 'q'.")

        except (EOFError, KeyboardInterrupt) as e:
            print("\n\nOperation cancelled by user.")
            raise KeyboardInterrupt("User cancelled operation") from e


def process_spec_conflicts(spec_dir: Path, action: str) -> bool:
    """Process spec conflicts based on chosen action.

    Args:
        spec_dir: Path to the spec directory
        action: Action to take ('overwrite', 'backup', 'skip', 'abort')

    Returns:
        True if generation should proceed, False if it should be skipped

    Raises:
        KeyboardInterrupt: If user chose to abort
        OSError: If backup creation fails
    """
    if action == "abort":
        print("\n❌ Operation aborted by user.")
        raise KeyboardInterrupt("User aborted operation")

    if action == "skip":
        print(f"⏭️  Skipping spec generation for {spec_dir.parent.name}")
        return False

    if action == "overwrite":
        print("🔄 Overwriting existing spec files...")
        return True

    if action == "backup":
        print("💾 Creating backups of existing files...")

        backup_paths = []
        for file_name in ["index", "history"]:
            file_path = spec_dir / f"{file_name}.md"
            if file_path.exists():
                backup_path = create_backup(file_path)
                if backup_path:
                    backup_paths.append(backup_path)

        if backup_paths:
            print("✅ Backups created:")
            for backup_path in backup_paths:
                print(f"   📦 {backup_path}")

        return True

    # Default case
    return True


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

            # Check if file should be processed
            if not should_generate_spec(resolved_path):
                file_type = get_file_type(resolved_path)
                print(f"⏭️  Skipping {resolved_path} (type: {file_type})")
                return

            spec_dir = create_spec_directory(resolved_path)
            template = load_template()

            file_type = get_file_type(resolved_path)
            print(f"📝 Generating spec for file: {resolved_path} (type: {file_type})")
            print(f"📁 Spec directory: {spec_dir}")
            print(
                f"📋 Template loaded: {len(template.index)} chars index, {len(template.history)} chars history"
            )

            # Check for existing spec files and handle conflicts
            existing_specs = check_existing_specs(spec_dir)

            # Handle conflicts if any exist
            try:
                # For now, we'll add a --force flag support later
                # Currently using interactive mode
                action = handle_spec_conflict(spec_dir, existing_specs, force=False)

                # Process the chosen action
                should_proceed = process_spec_conflicts(spec_dir, action)

                if not should_proceed:
                    return

            except KeyboardInterrupt:
                return

            # Generate content files
            generate_spec_content(resolved_path, spec_dir, template)

            print("✅ Generated spec files:")
            print(f"   📄 {spec_dir / 'index.md'}")
            print(f"   📄 {spec_dir / 'history.md'}")
            return
        except (
            FileNotFoundError,
            IsADirectoryError,
            ValueError,
            OSError,
            yaml.YAMLError,
        ) as e:
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
