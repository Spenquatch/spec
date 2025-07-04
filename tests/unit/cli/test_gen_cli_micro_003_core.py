"""Core unit tests for CLI Gen Command - Micro-Agent cli_003 Implementation.

Focused test suite covering the essential CLI interface and core functionality
without deep AI integration dependencies.

Tests cover:
- CLI interface (gen.py) with click options and argument validation
- Core GenCommand class methods without AI dependencies
- Essential validation and error handling
- CLI argument passing and option handling
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from spec_cli.cli.commands.gen import gen_command
from spec_cli.exceptions import SpecError


class TestGenCommandCLICore:
    """Test the CLI interface for gen command - core functionality."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()

    def test_gen_command_when_valid_file_then_executes_successfully(self):
        """Test gen command with valid file path executes successfully."""
        with self.runner.isolated_filesystem():
            # Create test file
            test_file = Path("test.py")
            test_file.write_text("print('hello')")

            # Mock the GenCommand.safe_execute to return success
            with patch(
                "spec_cli.cli.commands.gen.GenCommand.safe_execute"
            ) as mock_execute:
                mock_execute.return_value = {
                    "success": True,
                    "message": "Generation completed",
                }

                # Mock validate_file_paths
                with patch(
                    "spec_cli.cli.commands.gen.validate_file_paths"
                ) as mock_validate:
                    mock_validate.return_value = [test_file]

                    result = self.runner.invoke(gen_command, ["test.py"])

                    assert result.exit_code == 0
                    mock_execute.assert_called_once()

    def test_gen_command_when_no_files_then_raises_bad_parameter(self):
        """Test gen command with no files raises BadParameter."""
        with patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate:
            mock_validate.return_value = []

            result = self.runner.invoke(gen_command, ["dummy_file"])

            assert result.exit_code != 0
            assert "No valid source files provided" in result.output

    def test_gen_command_when_command_fails_then_exits_with_error(self):
        """Test gen command exits with error when command execution fails."""
        with self.runner.isolated_filesystem():
            test_file = Path("test.py")
            test_file.write_text("print('hello')")

            with patch(
                "spec_cli.cli.commands.gen.GenCommand.safe_execute"
            ) as mock_execute:
                mock_execute.return_value = {
                    "success": False,
                    "message": "Generation failed",
                }

                with patch(
                    "spec_cli.cli.commands.gen.validate_file_paths"
                ) as mock_validate:
                    mock_validate.return_value = [test_file]

                    result = self.runner.invoke(gen_command, ["test.py"])

                    assert result.exit_code != 0
                    assert "Generation failed" in result.output

    def test_gen_command_when_all_options_provided_then_passes_to_command(self):
        """Test gen command passes all options correctly to GenCommand."""
        with self.runner.isolated_filesystem():
            test_file = Path("test.py")
            test_file.write_text("print('hello')")

            with patch(
                "spec_cli.cli.commands.gen.GenCommand.safe_execute"
            ) as mock_execute:
                mock_execute.return_value = {
                    "success": True,
                    "message": "Generation completed",
                }

                with patch(
                    "spec_cli.cli.commands.gen.validate_file_paths"
                ) as mock_validate:
                    mock_validate.return_value = [test_file]

                    result = self.runner.invoke(
                        gen_command,
                        [
                            "test.py",
                            "--template",
                            "custom",
                            "--conflict-strategy",
                            "overwrite",
                            "--commit",
                            "--message",
                            "Test commit",
                            "--interactive",
                            "--force",
                            "--dry-run",
                        ],
                    )

                    assert result.exit_code == 0

                    # Verify all options were passed
                    call_args = mock_execute.call_args[1]
                    assert call_args["template"] == "custom"
                    assert call_args["conflict_strategy"] == "overwrite"
                    assert call_args["commit"] is True
                    assert call_args["message"] == "Test commit"
                    assert call_args["interactive"] is True
                    assert call_args["force"] is True
                    assert call_args["dry_run"] is True

    def test_gen_command_when_exception_raised_then_converts_to_click_exception(self):
        """Test gen command converts exceptions to ClickException."""
        with self.runner.isolated_filesystem():
            test_file = Path("test.py")
            test_file.write_text("print('hello')")

            with patch(
                "spec_cli.cli.commands.gen.GenCommand.safe_execute"
            ) as mock_execute:
                mock_execute.side_effect = Exception("Unexpected error")

                with patch(
                    "spec_cli.cli.commands.gen.validate_file_paths"
                ) as mock_validate:
                    mock_validate.return_value = [test_file]

                    result = self.runner.invoke(gen_command, ["test.py"])

                    assert result.exit_code != 0
                    assert "Generation failed: Unexpected error" in result.output

    def test_gen_command_when_click_parameter_error_then_re_raises(self):
        """Test gen command re-raises click parameter errors."""
        import click

        with patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate:
            mock_validate.side_effect = click.BadParameter("Invalid file parameter")

            result = self.runner.invoke(gen_command, ["test.py"])

            assert result.exit_code != 0
            assert "Invalid file parameter" in result.output

    def test_gen_command_when_click_exception_then_re_raises(self):
        """Test gen command re-raises click exceptions."""
        import click

        with patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate:
            mock_validate.side_effect = click.ClickException("Click error")

            result = self.runner.invoke(gen_command, ["test.py"])

            assert result.exit_code != 0
            assert "Click error" in result.output


class TestGenCommandCoreValidation:
    """Test core validation functionality without AI dependencies."""

    def setup_method(self):
        """Set up test environment for each test."""
        # Mock GenCommand without importing the actual class with AI dependencies
        self.mock_command = Mock()

    def test_validate_arguments_when_valid_inputs_then_succeeds(self):
        """Test validate_arguments with valid inputs."""
        # Import only what's needed for validation testing
        from spec_cli.cli.commands.gen_command import GenCommand
        from spec_cli.config.settings import SpecSettings

        mock_settings = Mock(spec=SpecSettings)
        mock_settings.root_path = Path("/test")
        mock_settings.spec_dir = Path("/test/.spec")
        mock_settings.specs_dir = Path("/test/.specs")

        # Use dependency injection to avoid AI imports
        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(mock_settings)

            kwargs = {
                "files": [Path("test.py")],
                "template": "default",
                "conflict_strategy": "backup",
                "no_ai": False,
                "doc_type": "standard",
            }

            # Should not raise any exception
            command.validate_arguments(**kwargs)

    def test_validate_arguments_when_no_files_then_raises_spec_error(self):
        """Test validate_arguments raises SpecError when no files provided."""
        from spec_cli.cli.commands.gen_command import GenCommand
        from spec_cli.config.settings import SpecSettings

        mock_settings = Mock(spec=SpecSettings)
        mock_settings.root_path = Path("/test")
        mock_settings.spec_dir = Path("/test/.spec")
        mock_settings.specs_dir = Path("/test/.specs")

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(mock_settings)

            kwargs = {"files": []}

            with pytest.raises(SpecError, match="No source files provided"):
                command.validate_arguments(**kwargs)

    def test_validate_arguments_when_invalid_conflict_strategy_then_raises_spec_error(
        self,
    ):
        """Test validate_arguments raises SpecError for invalid conflict strategy."""
        from spec_cli.cli.commands.gen_command import GenCommand
        from spec_cli.config.settings import SpecSettings

        mock_settings = Mock(spec=SpecSettings)
        mock_settings.root_path = Path("/test")
        mock_settings.spec_dir = Path("/test/.spec")
        mock_settings.specs_dir = Path("/test/.specs")

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(mock_settings)

            kwargs = {
                "files": [Path("test.py")],
                "template": "default",
                "conflict_strategy": "invalid_strategy",
                "no_ai": False,
                "doc_type": "standard",
            }

            with pytest.raises(SpecError, match="Invalid conflict strategy"):
                command.validate_arguments(**kwargs)

    def test_validate_arguments_when_invalid_doc_type_then_raises_spec_error(self):
        """Test validate_arguments raises SpecError for invalid doc_type."""
        from spec_cli.cli.commands.gen_command import GenCommand
        from spec_cli.config.settings import SpecSettings

        mock_settings = Mock(spec=SpecSettings)
        mock_settings.root_path = Path("/test")
        mock_settings.spec_dir = Path("/test/.spec")
        mock_settings.specs_dir = Path("/test/.specs")

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(mock_settings)

            kwargs = {
                "files": [Path("test.py")],
                "template": "default",
                "conflict_strategy": "backup",
                "no_ai": False,
                "doc_type": "invalid_type",
            }

            with pytest.raises(SpecError, match="Invalid doc_type"):
                command.validate_arguments(**kwargs)

    def test_validate_arguments_when_invalid_file_type_then_raises_spec_error(self):
        """Test validate_arguments raises SpecError for invalid file types."""
        from spec_cli.cli.commands.gen_command import GenCommand
        from spec_cli.config.settings import SpecSettings

        mock_settings = Mock(spec=SpecSettings)
        mock_settings.root_path = Path("/test")
        mock_settings.spec_dir = Path("/test/.spec")
        mock_settings.specs_dir = Path("/test/.specs")

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(mock_settings)

            kwargs = {
                "files": [123],  # Invalid type
                "template": "default",
                "conflict_strategy": "backup",
                "no_ai": False,
                "doc_type": "standard",
            }

            with pytest.raises(SpecError, match="Invalid file path type"):
                command.validate_arguments(**kwargs)

    def test_validate_arguments_when_invalid_template_type_then_raises_spec_error(self):
        """Test validate_arguments raises SpecError for invalid template type."""
        from spec_cli.cli.commands.gen_command import GenCommand
        from spec_cli.config.settings import SpecSettings

        mock_settings = Mock(spec=SpecSettings)
        mock_settings.root_path = Path("/test")
        mock_settings.spec_dir = Path("/test/.spec")
        mock_settings.specs_dir = Path("/test/.specs")

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(mock_settings)

            kwargs = {
                "files": [Path("test.py")],
                "template": 123,  # Invalid type
                "conflict_strategy": "backup",
                "no_ai": False,
                "doc_type": "standard",
            }

            with pytest.raises(SpecError, match="Invalid template type"):
                command.validate_arguments(**kwargs)

    def test_validate_arguments_when_invalid_no_ai_type_then_raises_spec_error(self):
        """Test validate_arguments raises SpecError for invalid no_ai flag type."""
        from spec_cli.cli.commands.gen_command import GenCommand
        from spec_cli.config.settings import SpecSettings

        mock_settings = Mock(spec=SpecSettings)
        mock_settings.root_path = Path("/test")
        mock_settings.spec_dir = Path("/test/.spec")
        mock_settings.specs_dir = Path("/test/.specs")

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(mock_settings)

            kwargs = {
                "files": [Path("test.py")],
                "template": "default",
                "conflict_strategy": "backup",
                "no_ai": "invalid",  # Invalid type
                "doc_type": "standard",
            }

            with pytest.raises(SpecError, match="Invalid no_ai flag type"):
                command.validate_arguments(**kwargs)


class TestGenCommandCoreUtilities:
    """Test core utility methods without AI dependencies."""

    def setup_method(self):
        """Set up test environment for each test."""
        from spec_cli.config.settings import SpecSettings

        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test")
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/.specs")

    def test_create_template_variables_when_valid_path_then_returns_variables(self):
        """Test _create_template_variables returns correct variable dictionary."""
        from spec_cli.cli.commands.gen_command import GenCommand

        test_path = Path("/test/dir/example.py")

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            with patch(
                "spec_cli.cli.commands.gen_command.normalize_path",
                return_value=test_path,
            ):
                with patch(
                    "spec_cli.cli.commands.gen_command.datetime"
                ) as mock_datetime:
                    mock_datetime.now.return_value.isoformat.return_value = (
                        "2023-01-01T00:00:00"
                    )

                    command = GenCommand(self.mock_settings)
                    variables = command._create_template_variables(test_path)

                    assert variables["filename"] == "example.py"
                    assert variables["filepath"] == str(test_path)
                    assert variables["parent_dir"] == "dir"
                    assert variables["file_ext"] == ".py"
                    assert variables["timestamp"] == "2023-01-01T00:00:00"

    def test_init_when_no_settings_then_uses_default(self):
        """Test GenCommand initialization without settings."""
        from spec_cli.cli.commands.gen_command import GenCommand

        with patch("spec_cli.cli.commands.gen_command.get_console") as mock_console:
            command = GenCommand()
            assert command.settings is not None
            mock_console.assert_called_once()

    def test_init_when_provided_settings_then_uses_settings(self):
        """Test GenCommand initialization with provided settings."""
        from spec_cli.cli.commands.gen_command import GenCommand

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(self.mock_settings)
            assert command.settings == self.mock_settings


class TestGenCommandEdgeCasesCore:
    """Test edge cases and boundary conditions without AI dependencies."""

    def setup_method(self):
        """Set up test environment for each test."""
        from spec_cli.config.settings import SpecSettings

        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test")
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/.specs")

    def test_validate_arguments_with_all_valid_doc_types(self):
        """Test validate_arguments accepts all valid doc_types."""
        from spec_cli.cli.commands.gen_command import GenCommand

        valid_doc_types = ["standard", "comprehensive", "minimal", "api", "tutorial"]

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(self.mock_settings)

            for doc_type in valid_doc_types:
                kwargs = {
                    "files": [Path("test.py")],
                    "template": "default",
                    "conflict_strategy": "backup",
                    "no_ai": False,
                    "doc_type": doc_type,
                }

                # Should not raise any exception
                command.validate_arguments(**kwargs)

    def test_validate_arguments_with_all_valid_conflict_strategies(self):
        """Test validate_arguments accepts all valid conflict strategies."""
        from spec_cli.cli.commands.gen_command import GenCommand

        valid_strategies = ["backup", "overwrite", "skip", "fail"]

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(self.mock_settings)

            for strategy in valid_strategies:
                kwargs = {
                    "files": [Path("test.py")],
                    "template": "default",
                    "conflict_strategy": strategy,
                    "no_ai": False,
                    "doc_type": "standard",
                }

                # Should not raise any exception
                command.validate_arguments(**kwargs)

    def test_validate_arguments_when_path_objects_then_succeeds(self):
        """Test validate_arguments accepts Path objects."""
        from spec_cli.cli.commands.gen_command import GenCommand

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(self.mock_settings)

            kwargs = {
                "files": [Path("test.py"), Path("other.py")],
                "template": "default",
                "conflict_strategy": "backup",
                "no_ai": False,
                "doc_type": "standard",
            }

            # Should not raise any exception
            command.validate_arguments(**kwargs)

    def test_validate_arguments_when_string_paths_then_succeeds(self):
        """Test validate_arguments accepts string paths."""
        from spec_cli.cli.commands.gen_command import GenCommand

        with patch("spec_cli.cli.commands.gen_command.get_console"):
            command = GenCommand(self.mock_settings)

            kwargs = {
                "files": ["test.py", "other.py"],
                "template": "default",
                "conflict_strategy": "backup",
                "no_ai": False,
                "doc_type": "standard",
            }

            # Should not raise any exception
            command.validate_arguments(**kwargs)


class TestGenerateWithAIFunction:
    """Test the standalone generate_with_ai function."""

    def test_generate_with_ai_when_called_then_returns_not_implemented(self):
        """Test generate_with_ai function returns not implemented error."""
        from spec_cli.cli.commands.gen_command import generate_with_ai

        result = generate_with_ai(Path("/test/file.py"), "standard", None)

        assert result["success"] is False
        assert "AI generation not yet implemented" in result["error"]
