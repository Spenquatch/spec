#!/usr/bin/env python3
import fnmatch
import logging
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

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
DEBUG_LEVEL = os.environ.get("SPEC_DEBUG_LEVEL", "INFO").upper()
DEBUG_TIMING = os.environ.get("SPEC_DEBUG_TIMING", "").lower() in ["1", "true", "yes"]

# Configure debug logger
logger = logging.getLogger("spec_cli")
if DEBUG:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("🔍 Debug [%(levelname)s]: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, DEBUG_LEVEL, logging.INFO))
else:
    logger.addHandler(logging.NullHandler())


def debug_log(level: str, message: str, **kwargs: Any) -> None:
    """Enhanced debug logging with structured output.

    Args:
        level: Log level (INFO, DEBUG, WARNING, ERROR)
        message: Log message
        **kwargs: Additional structured data to include
    """
    if not DEBUG:
        return

    # Format structured data
    extra_data = ""
    if kwargs:
        extra_parts = []
        for key, value in kwargs.items():
            extra_parts.append(f"{key}={value}")
        extra_data = f" ({', '.join(extra_parts)})"

    full_message = f"{message}{extra_data}"

    level_method = getattr(logger, level.lower(), logger.info)
    level_method(full_message)


class DebugTimer:
    """Context manager for timing operations in debug mode."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.start_time: Optional[float] = None

    def __enter__(self) -> "DebugTimer":
        if DEBUG_TIMING:
            self.start_time = time.perf_counter()
            debug_log("INFO", f"Starting {self.name}")
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if DEBUG_TIMING and self.start_time is not None:
            elapsed = time.perf_counter() - self.start_time
            debug_log(
                "INFO", f"Completed {self.name}", duration_ms=f"{elapsed * 1000:.2f}ms"
            )
        # Return None to let any exception propagate


def debug_timer(operation_name: str) -> DebugTimer:
    """Context manager for timing operations in debug mode.

    Args:
        operation_name: Name of the operation being timed

    Usage:
        with debug_timer("file_processing"):
            # ... operation code ...
    """
    return DebugTimer(operation_name)


def debug_operation_summary(operation: str, **metrics: Any) -> None:
    """Log a summary of an operation with metrics.

    Args:
        operation: Name of the operation
        **metrics: Key-value pairs of metrics to include
    """
    if not DEBUG:
        return

    debug_log("INFO", f"Operation summary: {operation}", **metrics)


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
        debug_log("INFO", "Running git command", command=" ".join(cmd))
        git_env = {k: v for k, v in env.items() if k.startswith("GIT_")}
        debug_log("DEBUG", "Git environment variables", **git_env)

    subprocess.check_call(cmd, env=env)


def cmd_init(_: List[str]) -> None:
    # 1. Create .spec/ as bare Git repo
    if not SPEC_DIR.exists():
        SPEC_DIR.mkdir()
        subprocess.check_call(["git", "init", "--bare", str(SPEC_DIR)])
        print("✅ .spec/ initialized")
    else:
        print("ℹ️ .spec/ already exists, skipping init")

    # 2. Create .specignore with proper patterns for source files
    if not IGNORE_FILE.exists():
        # Create a reasonable default .specignore that doesn't block all files
        ignore_content = """# Default ignore patterns for spec generation
# Build artifacts
*.pyc
*.pyo
*.pyd
__pycache__/*
*.egg-info/*
build/*
dist/*

# Version control
.git/*
.svn/*
.hg/*

# IDE files
.vscode/*
.idea/*
*.swp
*.swo
*~

# OS files
.DS_Store
Thumbs.db

# Logs and temporary files
*.log
*.tmp
*.temp

# Dependencies
node_modules/*
.venv/*
venv/*

# Spec directory itself
.spec/*
.spec-index
"""
        IGNORE_FILE.write_text(ignore_content)
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
            debug_log("INFO", "Created spec directory", path=str(spec_dir_path))

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
            debug_log("INFO", "No .spectemplate file found, using default template")
        return TemplateConfig()

    try:
        with TEMPLATE_FILE.open("r", encoding="utf-8") as f:
            template_data = yaml.safe_load(f)

        if DEBUG:
            debug_log(
                "INFO", "Loaded template from file", template_file=str(TEMPLATE_FILE)
            )

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
            debug_log(
                "INFO",
                "Generated spec content files",
                index_chars=len(index_content),
                history_chars=len(history_content),
            )

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
                debug_log("WARNING", "Failed to read .specignore file", error=str(e))

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
        debug_log("INFO", "Loaded ignore patterns", pattern_count=len(patterns))

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
                debug_log(
                    "DEBUG",
                    "File matches ignore pattern",
                    file_path=str(file_path),
                    pattern=pattern,
                )
            return False

        # Match against filename only
        if fnmatch.fnmatch(file_name, pattern):
            if DEBUG:
                debug_log(
                    "DEBUG",
                    "File matches ignore pattern",
                    file_path=str(file_path),
                    pattern=pattern,
                )
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
                        debug_log(
                            "DEBUG",
                            "File in ignored directory",
                            file_path=str(file_path),
                            pattern=pattern,
                        )
                    return False

    # Check file type - only generate for known file types
    file_type = get_file_type(file_path)
    if file_type in {"unknown"}:
        if DEBUG:
            debug_log(
                "DEBUG",
                "Skipping unknown file type",
                file_path=str(file_path),
                file_type=file_type,
            )
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
            debug_log(
                "DEBUG",
                "Skipping binary file",
                file_path=str(file_path),
                extension=file_path.suffix.lower(),
            )
        return False

    # Skip very large files (>1MB)
    try:
        full_path = ROOT / file_path
        if full_path.exists() and full_path.stat().st_size > 1_048_576:  # 1MB
            if DEBUG:
                debug_log(
                    "DEBUG",
                    "Skipping large file",
                    file_path=str(file_path),
                    size_bytes=full_path.stat().st_size,
                )
            return False
    except OSError:
        # If we can't check size, assume it's okay
        pass

    if DEBUG:
        debug_log(
            "INFO",
            "File approved for spec generation",
            file_path=str(file_path),
            file_type=file_type,
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
        debug_log(
            "INFO",
            "Checking existing specs",
            spec_dir=str(spec_dir),
            index_exists=result["index"],
            history_exists=result["history"],
        )

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
            debug_log(
                "INFO",
                "Created backup file",
                original=str(file_path),
                backup=str(backup_path),
            )

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
            debug_log(
                "INFO",
                "Force mode - overwriting existing files",
                existing_files=existing_files,
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


def find_source_files(directory: Path) -> List[Path]:
    """Find all source files in a directory recursively.

    Args:
        directory: Directory to search for source files

    Returns:
        List of Path objects for source files found

    Raises:
        OSError: If directory traversal fails
    """
    source_files = []
    ignore_patterns = load_specignore_patterns()

    try:
        # Walk through directory recursively
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                # Convert to relative path from ROOT for consistent checking
                try:
                    relative_path = (
                        file_path.relative_to(ROOT)
                        if file_path.is_absolute()
                        else file_path
                    )
                except ValueError:
                    # File is outside project root, skip it
                    continue

                # Check if file should be included
                if should_generate_spec(relative_path, ignore_patterns):
                    source_files.append(file_path)

        # Sort files for consistent ordering
        source_files.sort()

        debug_log(
            "INFO",
            "Completed source file discovery",
            directory=str(directory),
            total_files_found=len(source_files),
        )

        return source_files

    except OSError as e:
        raise OSError(f"Failed to traverse directory {directory}: {e}") from e


def cmd_gen(args: List[str]) -> None:
    """Generate spec documentation for file(s) or directory."""
    with debug_timer("cmd_gen_total"):
        debug_log("INFO", "Starting spec generation command", args=args)

        if not args:
            debug_log("WARNING", "No arguments provided to cmd_gen")
            print("❌ Please specify a file or directory to generate specs for")
            return

        path_str = args[0]
        path = Path(path_str)

        debug_log(
            "INFO",
            "Processing path argument",
            input_path=path_str,
            resolved_path=str(path),
        )

        # Handle "." for current directory
        if path_str == ".":
            path = Path.cwd()
            debug_log("DEBUG", "Resolved current directory", path=str(path))

        # Check if path exists
        if not path.exists():
            debug_log("ERROR", "Path not found", path=str(path))
            print(f"❌ Path not found: {path}")
            return

        # Handle single file
        if path.is_file():
            debug_log("INFO", "Processing single file", file_path=str(path))

            try:
                with debug_timer("file_processing"):
                    with debug_timer("resolve_file_path"):
                        resolved_path = resolve_file_path(path_str)

                    debug_log(
                        "INFO",
                        "File path resolved",
                        original=path_str,
                        resolved=str(resolved_path),
                    )

                    # Check if file should be processed
                    with debug_timer("should_generate_spec"):
                        should_process = should_generate_spec(resolved_path)

                    if not should_process:
                        file_type = get_file_type(resolved_path)
                        debug_log(
                            "INFO",
                            "File skipped by filtering",
                            file_path=str(resolved_path),
                            file_type=file_type,
                        )
                        print(f"⏭️  Skipping {resolved_path} (type: {file_type})")
                        return

                    with debug_timer("create_spec_directory"):
                        spec_dir = create_spec_directory(resolved_path)

                    with debug_timer("load_template"):
                        template = load_template()

                    file_type = get_file_type(resolved_path)
                    debug_log(
                        "INFO",
                        "File processing setup complete",
                        file_path=str(resolved_path),
                        file_type=file_type,
                        spec_dir=str(spec_dir),
                        template_index_chars=len(template.index),
                        template_history_chars=len(template.history),
                    )

                    print(
                        f"📝 Generating spec for file: {resolved_path} (type: {file_type})"
                    )
                    print(f"📁 Spec directory: {spec_dir}")
                    print(
                        f"📋 Template loaded: {len(template.index)} chars index, {len(template.history)} chars history"
                    )

                    # Check for existing spec files and handle conflicts
                    with debug_timer("check_existing_specs"):
                        existing_specs = check_existing_specs(spec_dir)

                    debug_log(
                        "INFO", "Conflict check complete", existing_specs=existing_specs
                    )

                    # Handle conflicts if any exist
                    try:
                        with debug_timer("handle_conflicts"):
                            # For now, we'll add a --force flag support later
                            # Currently using interactive mode
                            action = handle_spec_conflict(
                                spec_dir, existing_specs, force=False
                            )
                            debug_log(
                                "INFO",
                                "Conflict resolution action chosen",
                                action=action,
                            )

                            # Process the chosen action
                            should_proceed = process_spec_conflicts(spec_dir, action)
                            debug_log(
                                "INFO",
                                "Conflict processing result",
                                should_proceed=should_proceed,
                            )

                            if not should_proceed:
                                return

                    except KeyboardInterrupt:
                        debug_log("INFO", "Operation cancelled by user")
                        return

                    # Generate content files
                    with debug_timer("generate_spec_content"):
                        generate_spec_content(resolved_path, spec_dir, template)

                    debug_operation_summary(
                        "file_spec_generation",
                        file_path=str(resolved_path),
                        file_type=file_type,
                        spec_dir=str(spec_dir),
                        action_taken=action if "action" in locals() else "proceed",
                    )

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
                debug_log(
                    "ERROR",
                    "Error during file processing",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                print(f"❌ {e}")
                return

        # Handle directory
        elif path.is_dir():
            debug_log("INFO", "Processing directory", directory=str(path))
            print(f"📁 Generating specs for directory: {path}")

            try:
                with debug_timer("directory_processing"):
                    with debug_timer("find_source_files"):
                        source_files = find_source_files(path)

                    debug_log(
                        "INFO",
                        "Found source files in directory",
                        directory=str(path),
                        file_count=len(source_files),
                    )

                    if not source_files:
                        print("ℹ️  No source files found in directory")
                        debug_operation_summary(
                            "directory_spec_generation",
                            directory=str(path),
                            file_count=0,
                            status="no_files_found",
                        )
                        return

                    print(f"📋 Found {len(source_files)} source files to process")

                    # Load template once for all files
                    with debug_timer("load_template_for_directory"):
                        template = load_template()

                    debug_log(
                        "INFO",
                        "Template loaded for directory processing",
                        template_index_chars=len(template.index),
                        template_history_chars=len(template.history),
                    )

                    # Track progress
                    processed_count = 0
                    skipped_count = 0
                    error_count = 0

                    print(
                        f"🚀 Starting spec generation for {len(source_files)} files..."
                    )

                    for i, file_path in enumerate(source_files, 1):
                        try:
                            print(
                                f"\n[{i}/{len(source_files)}] Processing: {file_path}"
                            )

                            with debug_timer(f"process_file_{i}"):
                                # Convert to relative path from project root
                                relative_path = (
                                    file_path.relative_to(ROOT)
                                    if file_path.is_absolute()
                                    else file_path
                                )

                                # Check if file should be processed
                                with debug_timer("should_generate_check"):
                                    should_process = should_generate_spec(relative_path)

                                if not should_process:
                                    file_type = get_file_type(relative_path)
                                    print(f"   ⏭️  Skipped (type: {file_type})")
                                    skipped_count += 1
                                    continue

                                # Create spec directory
                                with debug_timer("create_spec_dir"):
                                    spec_dir = create_spec_directory(relative_path)

                                # Check for existing specs and handle conflicts
                                with debug_timer("check_conflicts"):
                                    existing_specs = check_existing_specs(spec_dir)

                                if any(existing_specs.values()):
                                    print(
                                        "   ⚠️  Existing specs found, using overwrite mode for batch processing"
                                    )
                                    action = "overwrite"
                                    should_proceed = process_spec_conflicts(
                                        spec_dir, action
                                    )
                                    if not should_proceed:
                                        skipped_count += 1
                                        continue

                                # Generate content
                                with debug_timer("generate_content"):
                                    generate_spec_content(
                                        relative_path, spec_dir, template
                                    )

                                file_type = get_file_type(relative_path)
                                print(f"   ✅ Generated specs (type: {file_type})")
                                processed_count += 1

                        except Exception as e:
                            error_count += 1
                            debug_log(
                                "ERROR",
                                "Error processing file in directory",
                                file_path=str(file_path),
                                error=str(e),
                            )
                            print(f"   ❌ Error: {e}")
                            continue

                    # Final summary
                    print("\n🎉 Directory processing complete!")
                    print(f"   ✅ Processed: {processed_count} files")
                    print(f"   ⏭️  Skipped: {skipped_count} files")
                    if error_count > 0:
                        print(f"   ❌ Errors: {error_count} files")

                    debug_operation_summary(
                        "directory_spec_generation",
                        directory=str(path),
                        total_files=len(source_files),
                        processed_count=processed_count,
                        skipped_count=skipped_count,
                        error_count=error_count,
                        status="completed",
                    )
                    return

            except Exception as e:
                debug_log(
                    "ERROR",
                    "Error during directory processing",
                    directory=str(path),
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                print(f"❌ Error processing directory: {e}")
                return
        else:
            debug_log(
                "ERROR",
                "Path is neither file nor directory",
                path=str(path),
                path_type=type(path).__name__,
            )
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
