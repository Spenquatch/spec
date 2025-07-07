"""Pre-commit hook integration utilities for singleton detection.

This module provides utilities to integrate singleton detection into pre-commit hooks
for continuous validation during development workflow.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..exceptions import SpecError

class HookIntegrationError(SpecError):
    """Exception raised when hook integration fails."""

    def __init__(self, message: str, hook_config: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.hook_config = hook_config

@dataclass
class HookIntegration:
    """Represents a pre-commit hook integration configuration."""

    hook_name: str
    hook_command: str
    hook_files: str
    hook_language: str
    hook_entry: str

def create_pre_commit_hook(detection_tool: Path) -> str:
    """Create pre-commit hook configuration for singleton detection.

    Args:
        detection_tool: Path to the singleton detection tool script

    Returns:
        YAML configuration string for pre-commit hook

    Raises:
        HookIntegrationError: If detection tool path is invalid or hook creation fails

    Example:
        >>> from pathlib import Path
        >>> tool_path = Path("scripts/check_singletons.py")
        >>> config = create_pre_commit_hook(tool_path)
        >>> print("singleton-check" in config)  # True
    """
    if not isinstance(detection_tool, Path):
        raise HookIntegrationError(f"Expected Path object, got {type(detection_tool)}")

    if not detection_tool.exists():
        raise HookIntegrationError(
            f"Detection tool not found: {detection_tool}",
            {"tool_path": str(detection_tool)},
        )

    hook_config = f"""repos:
  - repo: local
    hooks:
      - id: singleton-detection
        name: Singleton Pattern Detection
        entry: python {detection_tool}
        language: system
        files: ^spec_cli/.*\\.py$
        description: 'Detect singleton patterns in Python code'
        pass_filenames: true
        require_serial: false
        additional_dependencies: []
"""

    return hook_config

def validate_hook_configuration(hook_config: dict[str, Any]) -> bool:
    """Validate pre-commit hook configuration structure.

    Args:
        hook_config: Dictionary containing hook configuration

    Returns:
        True if configuration is valid, False otherwise

    Raises:
        HookIntegrationError: If hook_config is not a dictionary

    Example:
        >>> config = {
        ...     "repos": [{"repo": "local", "hooks": [{"id": "test"}]}]
        ... }
        >>> result = validate_hook_configuration(config)
        >>> print(result)  # True or False
    """
    if not isinstance(hook_config, dict):
        raise HookIntegrationError(f"Expected dictionary, got {type(hook_config)}")

    # Check required top-level structure
    if "repos" not in hook_config:
        return False

    repos = hook_config["repos"]
    if not isinstance(repos, list) or not repos:
        return False

    # Validate each repository configuration
    for repo in repos:
        if not isinstance(repo, dict):
            return False

        # Check required repository fields
        if "repo" not in repo or "hooks" not in repo:
            return False

        hooks = repo["hooks"]
        if not isinstance(hooks, list):
            return False

        # Validate each hook in the repository
        for hook in hooks:
            if not isinstance(hook, dict):
                return False

            # Check required hook fields
            required_fields = ["id", "name", "entry"]
            if not all(field in hook for field in required_fields):
                return False

            # Validate hook field types
            if not all(isinstance(hook[field], str) for field in required_fields):
                return False

    return True

def get_singleton_detection_hook() -> HookIntegration:
    """Get the singleton detection hook integration configuration.

    Returns:
        HookIntegration object with singleton detection configuration

    Example:
        >>> hook = get_singleton_detection_hook()
        >>> print(hook.hook_name)  # 'singleton-detection'
    """
    return HookIntegration(
        hook_name="singleton-detection",
        hook_command="python scripts/check_singletons.py",
        hook_files="^spec_cli/.*\\.py$",
        hook_language="system",
        hook_entry="python scripts/check_singletons.py",
    )

def create_hook_script(detection_module_path: Path) -> str:
    """Create executable hook script for singleton detection.

    Args:
        detection_module_path: Path to singleton detection module

    Returns:
        Python script content for hook execution

    Raises:
        HookIntegrationError: If detection module path is invalid

    Example:
        >>> from pathlib import Path
        >>> module_path = Path("spec_cli/utils/singleton_detection.py")
        >>> script = create_hook_script(module_path)
        >>> print("sys.exit" in script)  # True
    """
    if not isinstance(detection_module_path, Path):
        raise HookIntegrationError(
            f"Expected Path object, got {type(detection_module_path)}"
        )

    script_content = '''#!/usr/bin/env python3
"""Pre-commit hook for singleton pattern detection."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from spec_cli.utils.singleton_detection import SingletonPatternDetector
except ImportError as e:
    print(f"ERROR: Cannot
    sys.exit(1)

def main() -> int:
    """Run singleton detection on provided files."""
    if len(sys.argv) < 2:
        print("Usage: check_singletons.py <file1> [file2] ...")
        return 1

    violation_count = 0

    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)

        # Only check Python files
        if not file_path.suffix == ".py":
            continue

        if not file_path.exists():
            print(f"WARNING: File not found: {file_path}")
            continue

        try:
            detector = SingletonPatternDetector()
            violations = detector.detect_violations(file_path)

            if violations:
                print(f"\\nSingleton violations found in {file_path}:")
                for violation in violations:
                    print(f"  Line {violation.line_number}: {violation.pattern_type}")
                    print(f"    Code: {violation.code_snippet}")
                violation_count += len(violations)

        except Exception as e:
            print(f"ERROR checking {file_path}: {e}")
            return 1

    if violation_count > 0:
        print(f"\\nFAILED: Found {violation_count} singleton pattern violations")
        print("Please remove singleton patterns before committing.")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

    return script_content
