"""Integration tests for singleton infrastructure removal."""

import tempfile
from pathlib import Path

from spec_cli.utils.cleanup_utils import (
    cleanup_compatibility_layer,
    cleanup_singleton_infrastructure,
    validate_no_references,
)

# Test constants
SINGLETON_INFRASTRUCTURE_CODE = '''
"""Thread-safe singleton implementation utilities."""

import threading
from functools import wraps
from typing import Any, TypeVar, cast

T = TypeVar("T")

# Thread-safe singleton instances storage
_instances: dict[type[Any], Any] = {}
_instance_locks: dict[type[Any], threading.Lock] = {}
_global_lock = threading.Lock()

class SingletonMeta(type):
    """Metaclass-based singleton implementation."""
    pass

def singleton_decorator(cls: type[T]) -> type[T]:
    """Thread-safe singleton decorator."""
    pass
'''

COMPATIBILITY_LAYER_CODE = '''
"""Compatibility layer for singleton to dependency injection migration."""

import threading
from typing import Any, cast

class CompatibilityLayer:
    """Central compatibility layer managing singleton to DI migration."""
    
    def __init__(self) -> None:
        self._wrappers: dict[str, Any] = {}
        self._lock = threading.Lock()

    def get_progress_manager_wrapper(self):
        """Get ProgressManager compatibility wrapper."""
        pass

class ProgressManagerWrapper:
    """Compatibility wrapper for ProgressManagerSingleton."""
    pass
'''

REFERENCING_CODE = '''
"""File that references removed modules."""

from spec_cli.utils.singleton import SingletonMeta, singleton_decorator
from spec_cli.core.compatibility import CompatibilityLayer

def test_function():
    """Function that uses singleton infrastructure."""
    pass
'''

CLEAN_CODE = '''
"""Clean file with no references to removed modules."""

import os
from pathlib import Path
from typing import Any

def test_function():
    """Function that doesn't use singleton infrastructure."""
    pass
'''


class TestSingletonInfrastructureRemoval:
    """Integration test for complete singleton infrastructure removal."""

    def test_singleton_infrastructure_removal_when_complete_workflow_then_codebase_clean_and_functional(self):
        """Test complete singleton infrastructure removal workflow."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create realistic project structure
            spec_cli_dir = temp_path / "spec_cli"
            utils_dir = spec_cli_dir / "utils"
            core_dir = spec_cli_dir / "core"

            utils_dir.mkdir(parents=True)
            core_dir.mkdir(parents=True)

            # Create infrastructure files to be removed
            singleton_file = utils_dir / "singleton.py"
            singleton_file.write_text(SINGLETON_INFRASTRUCTURE_CODE)

            compatibility_file = core_dir / "compatibility.py"
            compatibility_file.write_text(COMPATIBILITY_LAYER_CODE)

            # Create files with references (will remain after cleanup)
            referencing_file = temp_path / "referencing_module.py"
            referencing_file.write_text(REFERENCING_CODE)

            # Create clean files (should remain untouched)
            clean_file = temp_path / "clean_module.py"
            clean_file.write_text(CLEAN_CODE)

            # Verify initial state
            assert singleton_file.exists()
            assert compatibility_file.exists()
            assert referencing_file.exists()
            assert clean_file.exists()

            # Phase 1: Remove singleton infrastructure
            singleton_removed = cleanup_singleton_infrastructure(temp_path)

            # Verify singleton infrastructure removed
            assert len(singleton_removed) == 1
            assert str(singleton_file) in singleton_removed
            assert not singleton_file.exists()

            # Phase 2: Remove compatibility layer
            compatibility_removed = cleanup_compatibility_layer(temp_path)

            # Verify compatibility layer removed
            assert len(compatibility_removed) == 1
            assert str(compatibility_file) in compatibility_removed
            assert not compatibility_file.exists()

            # Phase 3: Validate reference detection
            violations = validate_no_references(
                temp_path, ["singleton", "compatibility"]
            )

            # Should detect references in referencing_file but not clean_file
            assert len(violations) == 1
            assert str(referencing_file) in violations

            # Clean file should remain untouched
            assert clean_file.exists()
            assert clean_file.read_text() == CLEAN_CODE

            # Phase 4: Verify infrastructure files are completely gone
            remaining_singleton_files = list(temp_path.rglob("**/singleton.py"))
            remaining_compatibility_files = list(temp_path.rglob("**/compatibility.py"))

            assert len(remaining_singleton_files) == 0
            assert len(remaining_compatibility_files) == 0

    def test_infrastructure_removal_when_partial_structure_then_handles_missing_files_gracefully(self):
        """Test graceful handling when some infrastructure files don't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create only partial structure (missing some expected files)
            spec_cli_dir = temp_path / "spec_cli"
            utils_dir = spec_cli_dir / "utils"
            utils_dir.mkdir(parents=True)

            # Only create singleton file, no compatibility file
            singleton_file = utils_dir / "singleton.py"
            singleton_file.write_text(SINGLETON_INFRASTRUCTURE_CODE)

            # Remove singleton infrastructure
            singleton_removed = cleanup_singleton_infrastructure(temp_path)
            assert len(singleton_removed) == 1
            assert not singleton_file.exists()

            # Remove compatibility layer (files don't exist)
            compatibility_removed = cleanup_compatibility_layer(temp_path)
            assert len(compatibility_removed) == 0  # No files to remove

            # Validate no references remain
            violations = validate_no_references(
                temp_path, ["singleton", "compatibility"]
            )
            assert len(violations) == 0  # No files with references

    def test_infrastructure_removal_when_empty_codebase_then_handles_gracefully(self):
        """Test infrastructure removal on empty codebase."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Empty codebase - just create directory structure
            spec_cli_dir = temp_path / "spec_cli"
            spec_cli_dir.mkdir(parents=True)

            # Attempt to remove infrastructure from empty codebase
            singleton_removed = cleanup_singleton_infrastructure(temp_path)
            compatibility_removed = cleanup_compatibility_layer(temp_path)

            # Should handle gracefully with no files to remove
            assert len(singleton_removed) == 0
            assert len(compatibility_removed) == 0

            # Validate no references (should be clean)
            violations = validate_no_references(
                temp_path, ["singleton", "compatibility"]
            )
            assert len(violations) == 0

    def test_infrastructure_removal_when_complex_references_then_detects_all_patterns(self):
        """Test reference detection with complex import patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create files with various reference patterns
            complex_refs_code = '''
            # Various import patterns
            from spec_cli.utils.singleton import SingletonMeta
            import spec_cli.core.compatibility as compat
            from ..core.compatibility import CompatibilityLayer
            
            # Usage patterns
            class MyClass(metaclass=SingletonMeta):
                pass
                
            layer = compat.CompatibilityLayer()
            '''

            complex_file = temp_path / "complex_refs.py"
            complex_file.write_text(complex_refs_code)

            # Create infrastructure files and remove them
            spec_cli_dir = temp_path / "spec_cli"
            utils_dir = spec_cli_dir / "utils"
            core_dir = spec_cli_dir / "core"

            utils_dir.mkdir(parents=True)
            core_dir.mkdir(parents=True)

            singleton_file = utils_dir / "singleton.py"
            singleton_file.write_text(SINGLETON_INFRASTRUCTURE_CODE)

            compatibility_file = core_dir / "compatibility.py"
            compatibility_file.write_text(COMPATIBILITY_LAYER_CODE)

            # Remove infrastructure
            cleanup_singleton_infrastructure(temp_path)
            cleanup_compatibility_layer(temp_path)

            # Validate reference detection finds complex patterns
            violations = validate_no_references(
                temp_path, ["singleton", "compatibility"]
            )

            assert len(violations) == 1
            assert str(complex_file) in violations

    def test_infrastructure_removal_when_large_codebase_then_performs_efficiently(self):
        """Test infrastructure removal scales well with larger codebases."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create larger codebase structure
            spec_cli_dir = temp_path / "spec_cli"
            utils_dir = spec_cli_dir / "utils"
            core_dir = spec_cli_dir / "core"

            utils_dir.mkdir(parents=True)
            core_dir.mkdir(parents=True)

            # Create infrastructure files
            singleton_file = utils_dir / "singleton.py"
            singleton_file.write_text(SINGLETON_INFRASTRUCTURE_CODE)

            compatibility_file = core_dir / "compatibility.py"
            compatibility_file.write_text(COMPATIBILITY_LAYER_CODE)

            # Create many files to test performance
            num_files = 50
            for i in range(num_files):
                test_file = temp_path / f"module_{i}.py"
                if i % 10 == 0:  # Every 10th file has references
                    test_file.write_text(REFERENCING_CODE)
                else:
                    test_file.write_text(CLEAN_CODE)

            # Perform infrastructure removal
            singleton_removed = cleanup_singleton_infrastructure(temp_path)
            compatibility_removed = cleanup_compatibility_layer(temp_path)

            # Verify removal
            assert len(singleton_removed) == 1
            assert len(compatibility_removed) == 1
            assert not singleton_file.exists()
            assert not compatibility_file.exists()

            # Validate reference detection
            violations = validate_no_references(
                temp_path, ["singleton", "compatibility"]
            )

            # Should find references in every 10th file (5 total)
            expected_violations = num_files // 10
            assert len(violations) == expected_violations

            # Verify correct files were identified
            for violation in violations:
                violation_file = Path(violation)
                assert violation_file.exists()
                content = violation_file.read_text()
                assert "singleton" in content or "compatibility" in content

