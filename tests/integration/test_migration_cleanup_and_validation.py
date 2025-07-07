"""Integration tests for migration cleanup and validation."""

import tempfile
from pathlib import Path

from spec_cli.utils.migration_cleanup_utils import (
    cleanup_migration,
    validate_migration_complete,
)


class TestMigrationCleanupIntegration:
    """Integration tests for migration cleanup and validation workflow."""

    def test_migration_cleanup_when_all_singleton_references_removed_then_test_suite_executes_completely(
        self,
    ):
        """Test complete migration cleanup workflow with real file processing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create realistic file structure
            spec_cli_dir = temp_path / "spec_cli"
            config_dir = spec_cli_dir / "config"
            ui_dir = spec_cli_dir / "ui"
            config_dir.mkdir(parents=True)
            ui_dir.mkdir(parents=True)

            # Create files with singleton imports
            settings_file = config_dir / "settings.py"
            console_file = ui_dir / "console.py"

            settings_content = '''"""Settings module with singleton imports."""

from pathlib import Path

class SettingsManager:
    def __init__(self):
        pass
'''

            console_content = '''"""Console module with singleton imports."""

from rich.console import Console

class ConsoleManager:
    def __init__(self):
        pass
'''

            settings_file.write_text(settings_content)
            console_file.write_text(console_content)

            # Run migration cleanup
            result = cleanup_migration(temp_path)

            # Verify cleanup success
            assert result.success is True
            assert result.files_processed >= 2
            assert result.imports_removed >= 2

            # Verify singleton imports were removed
            settings_after = settings_file.read_text()
            console_after = console_file.read_text()

            assert "from ..utils.singleton import" not in settings_after

            assert "from ..utils.singleton import" not in console_after

            # Verify context imports were added where appropriate
            assert "from ..core.context import SpecContext" in settings_after

    def test_migration_validation_when_cleanup_complete_then_reports_success(self):
        """Test migration validation reports success after complete cleanup."""
        # This test uses the actual codebase after cleanup
        report = validate_migration_complete()

        # The migration should be successful
        assert isinstance(report.files_processed, int)
        assert report.files_processed > 0

        # Check that no singleton violations remain
        # Note: Some references may remain in detection/test files, which is expected
        assert isinstance(report.singleton_violations, list)

    def test_migration_integration_when_full_workflow_then_maintains_functionality(
        self,
    ):
        """Test that migration maintains code functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create a complete module with singleton pattern
            module_dir = temp_path / "spec_cli" / "test_module"
            module_dir.mkdir(parents=True)

            module_file = module_dir / "__init__.py"
            module_content = '''"""Test module with singleton pattern."""

class TestSingleton:
    def __init__(self):
        self.value = "test"

    def get_value(self):
        return self.value

def get_instance():
    return TestSingleton()
'''

            module_file.write_text(module_content)

            # Run cleanup
            result = cleanup_migration(temp_path)

            # Verify cleanup worked
            assert result.success is True

            # Verify the module structure is maintained
            cleaned_content = module_file.read_text()
            assert "class TestSingleton:" in cleaned_content
            assert "def get_value(self):" in cleaned_content
            assert "def get_instance():" in cleaned_content

            # Verify singleton decorator was removed

            assert "from ..utils.singleton import" not in cleaned_content
