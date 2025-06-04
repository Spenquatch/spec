"""Tests for GenCommand class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.gen_command import GenCommand
from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecError
from spec_cli.file_processing.conflict_resolver import ConflictResolutionStrategy


class TestGenCommand:
    """Test GenCommand class functionality."""

    @pytest.fixture
    def mock_settings(self, tmp_path: Path) -> Mock:
        """Create mock settings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.root_path = tmp_path
        settings.spec_dir = tmp_path / ".spec"
        settings.specs_dir = tmp_path / ".specs"
        settings.is_initialized.return_value = True
        settings.validate_permissions.return_value = None
        return settings

    @pytest.fixture
    def command(self, mock_settings: Mock) -> GenCommand:
        """Create GenCommand instance for testing."""
        return GenCommand(settings=mock_settings)

    def test_gen_command_when_initialized_then_validates_repository(
        self, command: GenCommand, mock_settings: Mock
    ):
        """Test that GenCommand validates repository state."""
        mock_settings.is_initialized.return_value = False

        with pytest.raises(SpecError, match="not initialized"):
            command.execute(files=[])

    def test_gen_command_when_no_files_provided_then_validates_arguments(
        self, command: GenCommand
    ):
        """Test argument validation with no files."""
        with pytest.raises(SpecError, match="No source files provided"):
            command.validate_arguments(files=[])

    def test_gen_command_when_invalid_template_type_then_raises_error(
        self, command: GenCommand
    ):
        """Test argument validation with invalid template type."""
        with pytest.raises(SpecError, match="Invalid template type"):
            command.validate_arguments(files=[Path("test.py")], template=123)  # type: ignore

    def test_gen_command_when_invalid_conflict_strategy_then_raises_error(
        self, command: GenCommand
    ):
        """Test argument validation with invalid conflict strategy."""
        with pytest.raises(SpecError, match="Invalid conflict strategy"):
            command.validate_arguments(
                files=[Path("test.py")], conflict_strategy="invalid"
            )

    @patch("spec_cli.cli.commands.generation.validation.GenerationValidator")
    def test_expand_source_files_when_single_file_then_validates_and_returns_if_processable(
        self, mock_validator_class: Mock, command: GenCommand, tmp_path: Path
    ):
        """Test expanding single file that is processable."""
        # Setup
        test_file = tmp_path / "test.py"
        test_file.touch()

        mock_validator = Mock()
        mock_validator._is_processable_file.return_value = True
        mock_validator_class.return_value = mock_validator

        # Execute
        result = command._expand_source_files([test_file])

        # Verify
        assert result == [test_file]
        mock_validator._is_processable_file.assert_called_once_with(test_file)

    @patch("spec_cli.cli.commands.generation.validation.GenerationValidator")
    def test_expand_source_files_when_single_file_not_processable_then_returns_empty(
        self, mock_validator_class: Mock, command: GenCommand, tmp_path: Path
    ):
        """Test expanding single file that is not processable."""
        # Setup
        test_file = tmp_path / "test.bin"
        test_file.touch()

        mock_validator = Mock()
        mock_validator._is_processable_file.return_value = False
        mock_validator_class.return_value = mock_validator

        # Execute
        result = command._expand_source_files([test_file])

        # Verify
        assert result == []

    @patch("spec_cli.cli.commands.generation.validation.GenerationValidator")
    def test_expand_source_files_when_directory_then_expands_to_processable_files(
        self, mock_validator_class: Mock, command: GenCommand, tmp_path: Path
    ):
        """Test expanding directory to processable files."""
        # Setup
        test_dir = tmp_path / "src"
        test_dir.mkdir()

        mock_validator = Mock()
        mock_validator._get_processable_files_in_directory.return_value = [
            test_dir / "file1.py",
            test_dir / "file2.py",
        ]
        mock_validator_class.return_value = mock_validator

        # Execute
        result = command._expand_source_files([test_dir])

        # Verify
        assert len(result) == 2
        mock_validator._get_processable_files_in_directory.assert_called_once_with(
            test_dir
        )

    @patch("spec_cli.file_system.path_resolver.PathResolver")
    @patch("spec_cli.cli.commands.gen_command.show_message")
    def test_show_dry_run_preview_when_called_then_displays_preview_info(
        self,
        mock_show_message: Mock,
        mock_resolver_class: Mock,
        command: GenCommand,
        tmp_path: Path,
    ):
        """Test dry run preview display."""
        # Setup
        test_file = tmp_path / "test.py"
        test_file.touch()

        mock_resolver = Mock()
        mock_resolver.get_spec_files_for_source.return_value = {
            "index": tmp_path / ".specs" / "test.py" / "index.md",
            "history": tmp_path / ".specs" / "test.py" / "history.md",
        }
        mock_resolver_class.return_value = mock_resolver

        # Execute
        command._show_dry_run_preview(
            [test_file], "default", ConflictResolutionStrategy.BACKUP_AND_REPLACE
        )

        # Verify
        mock_show_message.assert_called_with(
            "This is a dry run. No files would be modified.", "info"
        )

    @patch("spec_cli.cli.commands.gen_command.create_generation_workflow")
    @patch("spec_cli.cli.commands.gen_command.validate_generation_input")
    @patch("spec_cli.cli.commands.gen_command.show_message")
    def test_execute_when_dry_run_then_does_not_generate(
        self,
        mock_show_message: Mock,
        mock_validate: Mock,
        mock_create_workflow: Mock,
        command: GenCommand,
        tmp_path: Path,
    ):
        """Test dry run mode doesn't generate files."""
        # Setup
        test_file = tmp_path / "test.py"
        test_file.touch()

        mock_validate.return_value = {"valid": True, "errors": [], "warnings": []}

        with patch.object(command, "_expand_source_files", return_value=[test_file]):
            # Execute
            result = command.execute(files=[test_file], dry_run=True)

            # Verify
            assert result["success"] is True
            assert "Dry run completed" in result["message"]
            mock_create_workflow.assert_not_called()

    @patch("spec_cli.cli.commands.gen_command.create_generation_workflow")
    @patch("spec_cli.cli.commands.gen_command.validate_generation_input")
    @patch("spec_cli.cli.commands.gen_command.show_message")
    def test_execute_when_validation_fails_then_raises_error(
        self,
        mock_show_message: Mock,
        mock_validate: Mock,
        mock_create_workflow: Mock,
        command: GenCommand,
        tmp_path: Path,
    ):
        """Test execution fails when validation fails."""
        # Setup
        test_file = tmp_path / "test.py"
        test_file.touch()

        mock_validate.return_value = {
            "valid": False,
            "errors": ["Template not found"],
            "warnings": [],
        }

        with patch.object(command, "_expand_source_files", return_value=[test_file]):
            # Execute & Verify
            with pytest.raises(SpecError, match="Validation failed"):
                command.execute(files=[test_file])

    @patch("spec_cli.cli.commands.gen_command.create_generation_workflow")
    @patch("spec_cli.cli.commands.gen_command.validate_generation_input")
    @patch("spec_cli.cli.commands.gen_command.get_user_confirmation")
    @patch("spec_cli.cli.commands.gen_command.show_message")
    def test_execute_when_warnings_and_not_forced_then_prompts_user(
        self,
        mock_show_message: Mock,
        mock_confirm: Mock,
        mock_validate: Mock,
        mock_create_workflow: Mock,
        command: GenCommand,
        tmp_path: Path,
    ):
        """Test execution prompts user when warnings exist and not forced."""
        # Setup
        test_file = tmp_path / "test.py"
        test_file.touch()

        mock_validate.return_value = {
            "valid": True,
            "errors": [],
            "warnings": ["Large file detected"],
        }
        mock_confirm.return_value = False  # User cancels

        with patch.object(command, "_expand_source_files", return_value=[test_file]):
            # Execute
            result = command.execute(files=[test_file], force=False)

            # Verify
            assert result["success"] is False
            assert "cancelled due to warnings" in result["message"]
            mock_confirm.assert_called_once()

    @patch("spec_cli.cli.commands.gen_command.create_generation_workflow")
    @patch("spec_cli.cli.commands.gen_command.validate_generation_input")
    @patch("spec_cli.cli.commands.gen_command.show_message")
    def test_execute_when_successful_then_returns_success_result(
        self,
        mock_show_message: Mock,
        mock_validate: Mock,
        mock_create_workflow: Mock,
        command: GenCommand,
        tmp_path: Path,
    ):
        """Test successful generation execution."""
        # Setup
        test_file = tmp_path / "test.py"
        test_file.touch()

        mock_validate.return_value = {"valid": True, "errors": [], "warnings": []}

        mock_result = Mock()
        mock_result.success = True
        mock_result.generated_files = ["file1.md", "file2.md"]
        mock_result.skipped_files = []
        mock_result.failed_files = []
        mock_result.conflicts_resolved = []
        mock_result.total_processing_time = 1.5

        mock_workflow = Mock()
        mock_workflow.generate.return_value = mock_result
        mock_create_workflow.return_value = mock_workflow

        with patch.object(command, "_expand_source_files", return_value=[test_file]):
            # Execute
            result = command.execute(files=[test_file])

            # Verify
            assert result["success"] is True
            assert "Generated documentation for 2 files" in result["message"]
            assert result["data"]["generated"] == ["file1.md", "file2.md"]
            assert result["data"]["processing_time"] == 1.5

    def test_safe_execute_integration_when_valid_files_then_succeeds(
        self, mock_settings: Mock, tmp_path: Path
    ):
        """Test full safe_execute integration."""
        # Setup
        test_file = tmp_path / "test.py"
        test_file.touch()

        with patch(
            "spec_cli.cli.commands.gen_command.create_generation_workflow"
        ) as mock_create:
            with patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input"
            ) as mock_validate:
                mock_validate.return_value = {
                    "valid": True,
                    "errors": [],
                    "warnings": [],
                }

                mock_result = Mock()
                mock_result.success = True
                mock_result.generated_files = ["file1.md"]
                mock_result.skipped_files = []
                mock_result.failed_files = []
                mock_result.conflicts_resolved = []
                mock_result.total_processing_time = 1.0

                mock_workflow = Mock()
                mock_workflow.generate.return_value = mock_result
                mock_create.return_value = mock_workflow

                command = GenCommand(settings=mock_settings)

                with patch.object(
                    command, "_expand_source_files", return_value=[test_file]
                ):
                    result = command.safe_execute(files=[test_file])

                    assert result["success"] is True
                    assert result["command"] == "gen"
