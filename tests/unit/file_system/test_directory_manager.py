import tempfile
from pathlib import Path
from typing import Any, Generator
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecFileError, SpecPermissionError
from spec_cli.file_system.directory_manager import DirectoryManager


class TestDirectoryManager:
    """Test suite for DirectoryManager class."""

    @pytest.fixture
    def temp_dir(self) -> Generator[Path, None, None]:
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_settings(self, temp_dir: Path) -> Mock:
        """Create mock settings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.specs_dir = temp_dir / ".specs"
        settings.ignore_file = temp_dir / ".specignore"
        settings.gitignore_file = temp_dir / ".gitignore"
        return settings

    @pytest.fixture
    def manager(self, mock_settings: Mock) -> DirectoryManager:
        """Create a DirectoryManager instance for testing."""
        return DirectoryManager(settings=mock_settings)

    def test_directory_manager_ensures_specs_directory(
        self, manager: DirectoryManager, mock_settings: Mock
    ) -> None:
        """Test ensuring .specs directory exists."""
        specs_dir = mock_settings.specs_dir

        # Initially should not exist
        assert not specs_dir.exists()

        # Ensure directory
        manager.ensure_specs_directory()

        # Should now exist
        assert specs_dir.exists()
        assert specs_dir.is_dir()

        # Should have created .specignore
        specignore_in_specs = specs_dir / ".specignore"
        assert specignore_in_specs.exists()

    def test_directory_manager_creates_spec_directories(
        self, manager: DirectoryManager, mock_settings: Mock
    ) -> None:
        """Test creating spec directories for files."""
        # Ensure specs directory exists first
        manager.ensure_specs_directory()

        # Test creating directory for a file
        file_path = Path("src/models/user.py")
        spec_dir = manager.create_spec_directory(file_path)

        # Should have created the directory
        assert spec_dir.exists()
        assert spec_dir.is_dir()

        # Directory should be writable
        assert spec_dir.stat().st_mode & 0o200  # Write permission

    def test_directory_manager_checks_existing_specs(
        self, manager: DirectoryManager, mock_settings: Mock, temp_dir: Path
    ) -> None:
        """Test checking existing spec files."""
        # Create a test spec directory
        spec_dir = temp_dir / "test_spec"
        spec_dir.mkdir()

        # Initially no files exist
        existing = manager.check_existing_specs(spec_dir)
        assert existing["directory"] is True
        assert existing["index.md"] is False
        assert existing["history.md"] is False

        # Create some files
        (spec_dir / "index.md").write_text("# Index")
        (spec_dir / "history.md").write_text("# History")

        # Check again
        existing = manager.check_existing_specs(spec_dir)
        assert existing["index.md"] is True
        assert existing["history.md"] is True

    def test_directory_manager_creates_backups(
        self, manager: DirectoryManager, temp_dir: Path
    ) -> None:
        """Test creating backup files."""
        # Create a spec directory with files
        spec_dir = temp_dir / "test_spec"
        spec_dir.mkdir()

        index_file = spec_dir / "index.md"
        history_file = spec_dir / "history.md"
        index_file.write_text("# Index content")
        history_file.write_text("# History content")

        # Create backups
        backup_files = manager.backup_existing_files(spec_dir, ".test_backup")

        # Should have created backup files
        assert len(backup_files) == 2

        for backup_file in backup_files:
            assert backup_file.exists()
            assert ".test_backup" in backup_file.name

    def test_directory_manager_removes_directories_safely(
        self, manager: DirectoryManager, temp_dir: Path
    ) -> None:
        """Test removing spec directories with backup option."""
        # Create a spec directory with files
        spec_dir = temp_dir / "test_spec"
        spec_dir.mkdir()

        (spec_dir / "index.md").write_text("# Index")
        (spec_dir / "history.md").write_text("# History")

        # Remove with backup
        backup_files = manager.remove_spec_directory(spec_dir, backup_first=True)

        # Directory should be gone
        assert not spec_dir.exists()

        # Backup files should have been created (but they're in the removed directory)
        assert backup_files is not None
        assert len(backup_files) == 2

        # Check that backup files were created in the correct location (parent directory)
        for backup_file in backup_files:
            assert ".backup_" in backup_file.name

    def test_directory_manager_sets_up_ignore_files(
        self, manager: DirectoryManager, mock_settings: Mock
    ) -> None:
        """Test setting up ignore files."""
        ignore_file = mock_settings.ignore_file

        # Initially should not exist
        assert not ignore_file.exists()

        # Setup ignore files
        manager.setup_ignore_files()

        # Should now exist with content
        assert ignore_file.exists()
        content = ignore_file.read_text()
        assert "*.pyc" in content
        assert "__pycache__/" in content
        assert ".vscode/" in content

    def test_directory_manager_updates_gitignore(
        self, manager: DirectoryManager, mock_settings: Mock
    ) -> None:
        """Test updating .gitignore file."""
        gitignore_file = mock_settings.gitignore_file

        # Create initial .gitignore
        gitignore_file.write_text("node_modules/\n*.log\n")

        # Update with spec patterns
        manager.update_main_gitignore()

        # Should have added spec patterns
        content = gitignore_file.read_text()
        assert ".spec/" in content
        assert ".spec-index" in content
        assert "node_modules/" in content  # Should preserve existing content

    def test_directory_manager_handles_permission_errors(
        self, manager: DirectoryManager, mock_settings: Mock
    ) -> None:
        """Test handling of permission errors."""
        # Mock os.access to return False (no write permission)
        with patch("os.access", return_value=False):
            # Create the directory first
            mock_settings.specs_dir.mkdir(parents=True, exist_ok=True)

            # Should raise permission error
            with pytest.raises(SpecPermissionError):
                manager.ensure_specs_directory()

    def test_directory_manager_handles_directory_stats(
        self, manager: DirectoryManager, temp_dir: Path
    ) -> None:
        """Test getting directory statistics."""
        # Test with non-existent directory
        non_existent = temp_dir / "non_existent"
        stats = manager.get_directory_stats(non_existent)
        assert stats["exists"] is False

        # Create test directory with files
        test_dir = temp_dir / "test_dir"
        test_dir.mkdir()

        # Create some files
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "file2.py").write_text("print('hello')")

        subdir = test_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.md").write_text("# Markdown")

        # Get stats
        stats = manager.get_directory_stats(test_dir)

        assert stats["exists"] is True
        assert stats["files"] >= 3
        assert stats["directories"] >= 1
        assert stats["total_size"] > 0

    @patch("spec_cli.file_system.directory_manager.debug_logger")
    def test_directory_manager_logs_operations(
        self, mock_logger: Any, manager: DirectoryManager, mock_settings: Mock
    ) -> None:
        """Test that directory operations are logged."""
        manager.ensure_specs_directory()

        # Should have logged operations
        mock_logger.log.assert_called()

        # Check for specific log levels
        calls = mock_logger.log.call_args_list
        info_calls = [call for call in calls if call[0][0] == "INFO"]
        assert len(info_calls) > 0

    def test_directory_manager_handles_os_errors(
        self, manager: DirectoryManager, mock_settings: Mock
    ) -> None:
        """Test handling of OS errors during directory operations."""
        # Mock mkdir to raise OSError
        with patch.object(Path, "mkdir", side_effect=OSError("Permission denied")):
            with pytest.raises(SpecFileError) as exc_info:
                manager.ensure_specs_directory()

            assert "Failed to create .specs directory" in str(exc_info.value)

    def test_directory_manager_backup_empty_directory(
        self, manager: DirectoryManager, temp_dir: Path
    ) -> None:
        """Test backing up empty or non-existent directories."""
        # Test with non-existent directory
        non_existent = temp_dir / "non_existent"
        backup_files = manager.backup_existing_files(non_existent)
        assert backup_files == []

        # Test with empty directory
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        backup_files = manager.backup_existing_files(empty_dir)
        assert backup_files == []

    def test_directory_manager_removes_non_existent_directory(
        self, manager: DirectoryManager, temp_dir: Path
    ) -> None:
        """Test removing non-existent directory."""
        non_existent = temp_dir / "non_existent"

        # Should handle gracefully
        backup_files = manager.remove_spec_directory(non_existent)
        assert backup_files is None

    def test_directory_manager_gitignore_already_updated(
        self, manager: DirectoryManager, mock_settings: Mock
    ) -> None:
        """Test updating .gitignore when spec patterns already exist."""
        gitignore_file = mock_settings.gitignore_file

        # Create .gitignore with spec patterns already present
        initial_content = """node_modules/
*.log
# Spec CLI files
.spec/
.spec-index
"""
        gitignore_file.write_text(initial_content)

        # Update should not duplicate patterns
        manager.update_main_gitignore()

        final_content = gitignore_file.read_text()
        # Should still contain patterns but not duplicated
        assert final_content.count(".spec/") == 1
