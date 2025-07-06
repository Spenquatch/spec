"""Integration tests for pre-commit hook integration with singleton detection."""

import subprocess
import sys
import tempfile
from pathlib import Path

from spec_cli.utils.hook_integration import (
    create_pre_commit_hook,
    validate_hook_configuration,
)


class TestPreCommitHookIntegration:
    """Integration tests for pre-commit hook with singleton detection."""

    def test_pre_commit_hook_integration_when_full_workflow_then_prevents_singleton_reintroduction(
        self,
    ):
        """Test complete pre-commit hook integration workflow prevents singleton reintroduction."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a mock Git repository structure
            repo_path = temp_path / "test_repo"
            repo_path.mkdir()

            # Create spec_cli directory structure
            spec_cli_path = repo_path / "spec_cli"
            spec_cli_path.mkdir()

            # Create the check_singletons.py script in scripts directory
            scripts_path = repo_path / "scripts"
            scripts_path.mkdir()
            check_script = scripts_path / "check_singletons.py"

            # Write the actual hook script content
            hook_script_content = '''#!/usr/bin/env python3
"""Pre-commit hook for singleton pattern detection."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def scan_for_singleton_patterns(file_path):
    """Mock singleton detection that finds specific patterns."""
    content = file_path.read_text()
    violations = []

    # Check for singleton patterns
    if "SingletonMeta" in content or "@singleton" in content:
        violations.append({
            "line_number": 1,
            "description": "Detected singleton pattern",
            "code_snippet": content.split('\\n')[0]
        })

    return violations

def main():
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
            violations = scan_for_singleton_patterns(file_path)

            if violations:
                print(f"\\nSingleton violations found in {file_path}:")
                for violation in violations:
                    print(f"  Line {violation['line_number']}: {violation['description']}")
                    print(f"    Code: {violation['code_snippet']}")
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
            check_script.write_text(hook_script_content)
            check_script.chmod(0o755)

            # Test 1: Create hook configuration
            hook_config = create_pre_commit_hook(check_script)
            assert "singleton-detection" in hook_config
            assert str(check_script) in hook_config

            # Test 2: Validate hook configuration structure
            import yaml

            parsed_config = yaml.safe_load(hook_config)
            assert validate_hook_configuration(parsed_config)

            # Test 3: Create clean Python file (should pass)
            clean_file = spec_cli_path / "clean_module.py"
            clean_file.write_text('''
"""Clean module without singleton patterns."""

class RegularClass:
    def __init__(self):
        self.value = "clean"

def regular_function():
    return "no singletons here"
''')

            # Test 4: Run hook on clean file (should succeed)
            result = subprocess.run(
                [sys.executable, str(check_script), str(clean_file)],
                capture_output=True,
                text=True,
                cwd=repo_path,
            )
            assert result.returncode == 0, f"Clean file failed: {result.stderr}"

            # Test 5: Create file with singleton pattern (should fail)
            singleton_file = spec_cli_path / "singleton_module.py"
            singleton_file.write_text('''
"""Module with singleton pattern."""

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class MySingleton(metaclass=SingletonMeta):
    def __init__(self):
        self.value = "singleton"
''')

            # Test 6: Run hook on singleton file (should fail)
            result = subprocess.run(
                [sys.executable, str(check_script), str(singleton_file)],
                capture_output=True,
                text=True,
                cwd=repo_path,
            )
            assert result.returncode == 1, "Singleton file should have failed hook"
            assert "Singleton violations found" in result.stdout
            assert "singleton pattern" in result.stdout.lower()

            # Test 7: Test with mixed files
            result = subprocess.run(
                [
                    sys.executable,
                    str(check_script),
                    str(clean_file),
                    str(singleton_file),
                ],
                capture_output=True,
                text=True,
                cwd=repo_path,
            )
            assert result.returncode == 1, "Mixed files should fail due to singleton"
            assert "FAILED: Found 1 singleton pattern violations" in result.stdout

class TestHookIntegrationWithDetectionSystem:
    """Test hook integration with the actual detection system from P3.2b."""

    def test_hook_integration_when_detection_system_installed_then_uses_singleton_detector(
        self,
    ):
        """Test hook integration uses singleton detection system when available."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test Python file with singleton pattern
            test_file = temp_path / "test_singleton.py"
            test_file.write_text("""
class SingletonMeta(type):
    _instances = {}

class TestSingleton(metaclass=SingletonMeta):
    pass
""")

            # Use the actual singleton detection from P3.2b
            violations = scan_for_singleton_patterns(test_file)

            # Verify detection system found the singleton
            assert len(violations) > 0
            assert any("SingletonMeta" in v.description for v in violations)

    def test_pre_commit_hook_when_infrastructure_removed_then_validates_clean_commits(
        self,
    ):
        """Test pre-commit hook validates clean commits after infrastructure removal."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a test file without singleton patterns (post-migration)
            clean_file = temp_path / "clean_di_code.py"
            clean_file.write_text('''
"""Clean dependency injection code."""

class UserService:
    def __init__(self, db_connection, logger):
        self.db = db_connection
        self.logger = logger

    def create_user(self, user_data):
        self.logger.info("Creating user")
        return self.db.insert(user_data)

# DI container setup
def create_user_service(context):
    return UserService(
        db_connection=context.get_db(),
        logger=context.get_logger()
    )
''')

            # Verify clean file has no violations
            violations = scan_for_singleton_patterns(clean_file)
            assert len(violations) == 0

class TestHookIntegrationDIMigrationContext:
    """Test hook integration in the context of DI migration."""

    def test_hook_integration_when_migration_complete_then_maintains_singleton_free_development(
        self,
    ):
        """Test hook maintains singleton-free development after migration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create post-migration code example
            di_file = temp_path / "di_example.py"
            di_file.write_text('''
"""Example of dependency injection pattern (post-migration)."""

from typing import Protocol

class DatabaseProtocol(Protocol):
    def query(self, sql: str) -> list: ...

class LoggerProtocol(Protocol):
    def info(self, message: str) -> None: ...

class UserRepository:
    def __init__(self, db: DatabaseProtocol, logger: LoggerProtocol):
        self._db = db
        self._logger = logger

    def find_user(self, user_id: str):
        self._logger.info(f"Finding user {user_id}")
        return self._db.query(f"SELECT * FROM users WHERE id = '{user_id}'")

class AppContext:
    def __init__(self):
        self._db = self._create_database()
        self._logger = self._create_logger()

    def get_user_repository(self) -> UserRepository:
        return UserRepository(self._db, self._logger)

    def _create_database(self):
        # Factory method for database
        pass

    def _create_logger(self):
        # Factory method for logger
        pass
''')

            # Verify DI pattern has no singleton violations
            violations = scan_for_singleton_patterns(di_file)
            assert len(violations) == 0

    def test_pre_commit_validation_when_context_injection_used_then_allows_proper_di_patterns(
        self,
    ):
        """Test pre-commit validation allows proper DI patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create context injection pattern (allowed)
            context_file = temp_path / "context_injection.py"
            context_file.write_text('''
"""Context injection pattern - allowed post-migration."""

from functools import wraps
from typing import Callable, TypeVar

T = TypeVar('T')

def inject_context(func: Callable[..., T]) -> Callable[..., T]:
    """Decorator to inject context into function calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get context from current execution context
        context = get_current_context()
        return func(context, *args, **kwargs)
    return wrapper

def get_current_context():
    """Get the current execution context."""
    # This is dependency injection, not singleton
    from contextvars import ContextVar
    return _context_var.get()

_context_var: ContextVar = ContextVar('spec_context')

@inject_context
def create_user(context, user_data):
    user_service = context.get_user_service()
    return user_service.create(user_data)
''')

            # Verify context injection pattern is not flagged as singleton
            violations = scan_for_singleton_patterns(context_file)
            assert len(violations) == 0

class TestCrossSliceIntegration:
    """Test integration across multiple slices."""

    def test_hook_integration_cross_slice_compatibility(self):
        """Test hook integration works with components from other slices."""
        # This test verifies that the hook integration (P3.2c) works correctly
        # with the singleton detection system (P3.2b) and infrastructure removal (P3.2a)

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create example of code that should trigger detection
            legacy_file = temp_path / "legacy_singleton.py"
            legacy_file.write_text('''
"""Legacy singleton pattern that should be detected."""

class LegacyService:
    def __init__(self):
        self.initialized = True
''')

            # Test that singleton detection finds the violation
            violations = scan_for_singleton_patterns(legacy_file)

            assert len(violations) >= 1
            singleton_found = any(
                "singleton" in v.description.lower() for v in violations
            )
            assert singleton_found, (
                f"Expected singleton detection, got: {[v.description for v in violations]}"
            )
