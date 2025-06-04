"""Tests for AddCommand class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.add_command import AddCommand
from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecError


class TestAddCommand:
    """Test AddCommand class functionality."""

    @pytest.fixture
    def mock_settings(self, tmp_path: Path) -> Mock:
        """Create mock settings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.root_path = tmp_path
        settings.spec_dir = tmp_path / ".spec"
        settings.specs_dir = tmp_path / ".specs"
        settings.index_file = tmp_path / ".spec-index"
        settings.is_initialized.return_value = True
        settings.validate_permissions.return_value = None
        return settings

    @pytest.fixture
    def command(self, mock_settings: Mock) -> AddCommand:
        """Create AddCommand instance for testing."""
        return AddCommand(settings=mock_settings)

    def test_add_command_when_initialized_then_validates_repository(
        self, command: AddCommand, mock_settings: Mock
    ):
        """Test that AddCommand validates repository state."""
        mock_settings.is_initialized.return_value = False

        with pytest.raises(SpecError, match="not initialized"):
            command.execute(files=[])

    def test_add_command_when_no_files_provided_then_validates_arguments(
        self, command: AddCommand
    ):
        """Test argument validation with no files."""
        with pytest.raises(SpecError, match="No file paths provided"):
            command.validate_arguments(files=[])

    def test_add_command_when_invalid_file_type_then_raises_error(
        self, command: AddCommand
    ):
        """Test argument validation with invalid file type."""
        with pytest.raises(SpecError, match="Invalid file path type"):
            command.validate_arguments(files=[123])  # type: ignore

    def test_expand_spec_files_when_single_file_then_returns_file(
        self, command: AddCommand, tmp_path: Path
    ):
        """Test that single file is returned as-is."""
        test_file = tmp_path / "test.md"
        test_file.touch()

        result = command._expand_spec_files([test_file])

        assert result == [test_file]

    def test_expand_spec_files_when_directory_then_returns_all_files(
        self, command: AddCommand, tmp_path: Path
    ):
        """Test that directory is expanded to all contained files."""
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()

        # Create test files
        file1 = test_dir / "file1.md"
        file2 = test_dir / "file2.md"
        subdir = test_dir / "subdir"
        subdir.mkdir()
        file3 = subdir / "file3.md"

        file1.touch()
        file2.touch()
        file3.touch()

        result = command._expand_spec_files([test_dir])

        # Should contain all files
        assert len(result) == 3
        assert file1 in result
        assert file2 in result
        assert file3 in result

    def test_filter_spec_files_when_file_in_specs_directory_then_included(
        self, command: AddCommand, mock_settings: Mock
    ):
        """Test that files in .specs directory are included."""
        specs_dir = mock_settings.specs_dir
        test_file = specs_dir / "test.md"

        result = command._filter_spec_files([test_file])

        assert result == [test_file]

    def test_filter_spec_files_when_file_outside_specs_directory_then_excluded(
        self, command: AddCommand, tmp_path: Path
    ):
        """Test that files outside .specs directory are excluded."""
        other_file = tmp_path / "other" / "file.md"

        result = command._filter_spec_files([other_file])

        assert result == []

    def test_analyze_git_status_when_repo_status_succeeds_then_returns_status_dict(
        self, command: AddCommand, tmp_path: Path
    ):
        """Test git status analysis when repository status succeeds."""
        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo.status.return_value = None
            mock_repo_class.return_value = mock_repo

            test_files = [tmp_path / "file1.md", tmp_path / "file2.md"]

            result = command._analyze_git_status(test_files, mock_repo)

            assert "untracked" in result
            assert "modified" in result
            assert "staged" in result
            assert "up_to_date" in result
            # In the simplified implementation, all files are assumed untracked
            assert len(result["untracked"]) == 2

    def test_analyze_git_status_when_repo_status_fails_then_assumes_untracked(
        self, command: AddCommand, tmp_path: Path
    ):
        """Test git status analysis when repository status fails."""
        with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
            mock_repo = Mock()
            mock_repo.status.side_effect = Exception("Git error")
            mock_repo_class.return_value = mock_repo

            test_files = [tmp_path / "file1.md"]

            result = command._analyze_git_status(test_files, mock_repo)

            # Should still return all files as untracked
            assert len(result["untracked"]) == 1

    def test_execute_when_dry_run_then_does_not_add_files(
        self,
        command: AddCommand,
        mock_settings: Mock,
        tmp_path: Path,
    ):
        """Test dry run mode doesn't actually add files."""
        # Setup
        specs_dir = mock_settings.specs_dir
        specs_dir.mkdir(parents=True)
        test_file = specs_dir / "test.md"
        test_file.touch()

        with patch("spec_cli.cli.commands.add_command.show_message"):
            with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
                with patch(
                    "spec_cli.cli.commands.add_command.create_add_workflow"
                ) as mock_create_workflow:
                    mock_repo = Mock()
                    mock_repo.status.return_value = None
                    mock_repo_class.return_value = mock_repo

                    # Execute
                    result = command.execute(files=[test_file], dry_run=True)

                    # Verify
                    assert result["success"] is True
                    assert "Dry run completed" in result["message"]
                    mock_create_workflow.assert_not_called()

    def test_execute_when_files_to_add_then_adds_successfully(
        self,
        command: AddCommand,
        mock_settings: Mock,
        tmp_path: Path,
    ):
        """Test successful file addition."""
        # Setup
        specs_dir = mock_settings.specs_dir
        specs_dir.mkdir(parents=True)
        test_file = specs_dir / "test.md"
        test_file.touch()

        with patch("spec_cli.cli.commands.add_command.show_message"):
            with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
                with patch(
                    "spec_cli.cli.commands.add_command.create_add_workflow"
                ) as mock_create_workflow:
                    mock_repo = Mock()
                    mock_repo.status.return_value = None
                    mock_repo_class.return_value = mock_repo

                    mock_workflow = Mock()
                    mock_workflow.add_files.return_value = {
                        "success": True,
                        "added": [str(test_file)],
                        "skipped": [],
                        "failed": [],
                    }
                    mock_create_workflow.return_value = mock_workflow

                    # Execute
                    result = command.execute(files=[test_file], force=False)

                    # Verify
                    assert result["success"] is True
                    assert "Added 1 files" in result["message"]
                    mock_workflow.add_files.assert_called_once()

    def test_execute_when_no_spec_files_then_returns_warning(
        self,
        command: AddCommand,
        tmp_path: Path,
    ):
        """Test when no files are in specs directory."""
        # Setup - file outside specs directory
        other_file = tmp_path / "other.md"
        other_file.touch()

        with patch("spec_cli.cli.commands.add_command.show_message"):
            with patch("spec_cli.git.repository.SpecGitRepository"):
                with patch(
                    "spec_cli.cli.commands.add_command.create_add_workflow"
                ) as mock_create_workflow:
                    # Execute
                    result = command.execute(files=[other_file])

                    # Verify
                    assert result["success"] is True
                    assert "No spec files found" in result["message"]
                    mock_create_workflow.assert_not_called()

    def test_safe_execute_integration_when_valid_files_then_succeeds(
        self, mock_settings: Mock, tmp_path: Path
    ):
        """Test full safe_execute integration."""
        # Setup
        specs_dir = mock_settings.specs_dir
        specs_dir.mkdir(parents=True)
        test_file = specs_dir / "test.md"
        test_file.touch()

        with patch(
            "spec_cli.cli.commands.add_command.create_add_workflow"
        ) as mock_create:
            with patch("spec_cli.git.repository.SpecGitRepository"):
                mock_workflow = Mock()
                mock_workflow.add_files.return_value = {
                    "success": True,
                    "added": [str(test_file)],
                    "skipped": [],
                    "failed": [],
                }
                mock_create.return_value = mock_workflow

                command = AddCommand(settings=mock_settings)
                result = command.safe_execute(files=[test_file])

                assert result["success"] is True
                assert result["command"] == "add"
