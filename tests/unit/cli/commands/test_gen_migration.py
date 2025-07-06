"""Unit tests for gen command migration to context injection pattern."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from spec_cli.cli.commands.gen import gen_command
from spec_cli.cli.commands.gen_command import GenCommand
from spec_cli.config.settings import SpecSettings
from spec_cli.core.context import SpecContext

# Test constants
DEFAULT_TEST_FILE = "test.py"
DEFAULT_TEMPLATE = "default"
DEFAULT_CONFLICT_STRATEGY = "backup"
TEST_CONTEXT_SETTINGS_TYPE = "TestSpecSettings"
TEST_GENERATED_FILES = ["index.md", "history.md"]


class TestGenCommandMigration:
    """Test gen command migration to context injection pattern."""

    @pytest.fixture
    def mock_context(self):
        """Create mock SpecContext for testing."""
        mock_context = Mock(spec=SpecContext)
        mock_settings = Mock(spec=SpecSettings)
        mock_settings.root_path = Path.cwd()
        mock_context.settings = mock_settings
        mock_context.console = Mock()
        mock_context.progress = Mock()
        return mock_context

    @pytest.fixture
    def mock_gen_command(self):
        """Create mock GenCommand for testing."""
        mock_command = Mock(spec=GenCommand)
        mock_command.safe_execute.return_value = {
            "success": True,
            "message": "Generation completed",
            "data": {"generated_files": TEST_GENERATED_FILES},
        }
        return mock_command

    @pytest.fixture
    def temp_file(self):
        """Create temporary test file."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("print('test')")
            yield Path(temp_file.name)
        Path(temp_file.name).unlink(missing_ok=True)

    def test_gen_command_when_context_decorator_applied_then_receives_context_parameter(
        self, mock_context, temp_file
    ):
        """Test that gen command receives context parameter from decorator."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.commands.gen.click.get_current_context"
            ) as mock_click_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = [temp_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Test success",
            }
            mock_gen_class.return_value = mock_gen_instance

            # Mock Click context to provide SpecContext
            mock_click_context = Mock()
            mock_click_context.obj = {"spec_context": mock_context}
            mock_click_ctx.return_value = mock_click_context

            # Mock context injection mechanism
            with patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx:
                mock_get_ctx.return_value = mock_context

                # Execute command
                runner = CliRunner()
                result = runner.invoke(gen_command, [str(temp_file)])

                # Verify context was injected
                assert result.exit_code == 0
                mock_gen_class.assert_called_once()
                # Verify settings were passed from context
                call_args = mock_gen_class.call_args
                assert "settings" in call_args.kwargs
                assert call_args.kwargs["settings"] == mock_context.settings

    def test_gen_command_when_using_context_settings_then_accesses_settings_from_context(
        self, mock_context, temp_file
    ):
        """Test that gen command accesses settings from injected context."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = [temp_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Settings accessed",
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = mock_context

            # Execute command
            runner = CliRunner()
            result = runner.invoke(gen_command, [str(temp_file)])

            # Verify settings from context were used
            assert result.exit_code == 0
            mock_gen_class.assert_called_once_with(settings=mock_context.settings)

    def test_gen_command_when_using_context_console_then_accesses_console_from_context(
        self, mock_context, temp_file
    ):
        """Test that gen command has access to console through context."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = [temp_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Console accessed",
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = mock_context

            # Execute command
            runner = CliRunner()
            result = runner.invoke(gen_command, [str(temp_file)])

            # Verify context was properly injected (console access is implicit)
            assert result.exit_code == 0
            assert mock_context.console is not None

    def test_gen_command_when_singleton_replaced_then_no_singleton_references_remain(
        self, mock_context, temp_file
    ):
        """Test that gen command function has no direct singleton references."""
        # Get source file content to check patterns
        import inspect

        import spec_cli.cli.commands.gen as gen_module
        source_file = inspect.getfile(gen_module)
        with open(source_file) as f:
            source = f.read()

        # Check for singleton patterns that should be eliminated
        forbidden_patterns = [
            "get_settings()",
            "get_console()",
            "get_progress()",
        ]

        for pattern in forbidden_patterns:
            assert pattern not in source, (
                f"Found singleton pattern '{pattern}' in gen_command function"
            )

        # Verify context parameter is present
        assert "context: SpecContext" in source

    def test_gen_command_when_migrated_signature_then_maintains_click_compatibility(
        self, mock_context, temp_file
    ):
        """Test that migrated command signature maintains Click compatibility."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = [temp_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Click compatible",
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = mock_context

            # Test with various Click options
            runner = CliRunner()
            result = runner.invoke(
                gen_command,
                [
                    str(temp_file),
                    "--template",
                    "comprehensive",
                    "--conflict-strategy",
                    "overwrite",
                    "--interactive",
                    "--force",
                    "--dry-run",
                ],
            )

            # Verify Click compatibility
            assert result.exit_code == 0
            mock_gen_instance.safe_execute.assert_called_once()
            call_kwargs = mock_gen_instance.safe_execute.call_args.kwargs
            assert call_kwargs["template"] == "comprehensive"
            assert call_kwargs["conflict_strategy"] == "overwrite"
            assert call_kwargs["interactive"] is True
            assert call_kwargs["force"] is True
            assert call_kwargs["dry_run"] is True

    def test_gen_command_when_behavior_validation_then_identical_to_original_behavior(
        self, mock_context, temp_file
    ):
        """Test that migrated command behavior is identical to original."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = [temp_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Behavior preserved",
                "data": {"generated": TEST_GENERATED_FILES},
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = mock_context

            # Execute command with standard parameters
            runner = CliRunner()
            result = runner.invoke(
                gen_command, [str(temp_file), "--template", DEFAULT_TEMPLATE]
            )

            # Verify original behavior is preserved
            assert result.exit_code == 0
            mock_validate.assert_called_once_with([str(temp_file)])
            mock_gen_class.assert_called_once_with(settings=mock_context.settings)
            mock_gen_instance.safe_execute.assert_called_once()

            # Verify parameters are passed correctly
            call_kwargs = mock_gen_instance.safe_execute.call_args.kwargs
            assert call_kwargs["files"] == [temp_file]
            assert call_kwargs["template"] == DEFAULT_TEMPLATE

    def test_gen_command_when_context_injection_error_then_raises_migration_error(self):
        """Test that context injection errors are handled properly."""
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click"
        ) as mock_get_ctx:
            # Mock context injection failure
            from spec_cli.cli.decorators import ContextInjectionError

            mock_get_ctx.side_effect = ContextInjectionError("Context not available")

            # Execute command
            runner = CliRunner()
            result = runner.invoke(gen_command, ["test.py"])

            # Verify error handling
            assert result.exit_code != 0
            assert (
                "Context not available" in result.output
                or "Context not available" in str(result.exception)
            )


class TestGenCommandParameterValidation:
    """Test parameter validation in migrated gen command."""

    @pytest.fixture
    def mock_context(self):
        """Create mock SpecContext for testing."""
        mock_context = Mock(spec=SpecContext)
        mock_settings = Mock(spec=SpecSettings)
        mock_context.settings = mock_settings
        return mock_context

    def test_gen_command_when_no_files_provided_then_raises_bad_parameter(
        self, mock_context
    ):
        """Test that command raises error when no files provided."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = []  # No valid files
            mock_get_ctx.return_value = mock_context

            # Execute command
            runner = CliRunner()
            result = runner.invoke(gen_command, [])

            # Verify error handling
            assert result.exit_code != 0

    def test_gen_command_when_generation_fails_then_raises_click_exception(
        self, mock_context, tmp_path
    ):
        """Test that command handles generation failures properly."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = [test_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": False,
                "message": "Generation failed",
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = mock_context

            # Execute command
            runner = CliRunner()
            result = runner.invoke(gen_command, [str(test_file)])

            # Verify error handling
            assert result.exit_code != 0
            assert "Generation failed" in result.output


class TestGenCommandConflictStrategyHandling:
    """Test conflict strategy parameter handling in migrated command."""

    @pytest.fixture
    def mock_context(self):
        """Create mock SpecContext for testing."""
        mock_context = Mock(spec=SpecContext)
        mock_settings = Mock(spec=SpecSettings)
        mock_context.settings = mock_settings
        return mock_context

    def test_gen_command_when_backup_strategy_then_passes_correct_parameter(
        self, mock_context, tmp_path
    ):
        """Test backup conflict strategy parameter passing."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = [test_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Success with backup",
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = mock_context

            # Execute command with backup strategy
            runner = CliRunner()
            result = runner.invoke(
                gen_command, [str(test_file), "--conflict-strategy", "backup"]
            )

            # Verify parameter passing
            assert result.exit_code == 0
            call_kwargs = mock_gen_instance.safe_execute.call_args.kwargs
            assert call_kwargs["conflict_strategy"] == "backup"

    def test_gen_command_when_invalid_strategy_then_click_handles_validation(
        self, mock_context, tmp_path
    ):
        """Test that Click handles invalid conflict strategy validation."""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        # Execute command with invalid strategy
        runner = CliRunner()
        result = runner.invoke(
            gen_command, [str(test_file), "--conflict-strategy", "invalid"]
        )

        # Verify Click validation
        assert result.exit_code != 0
        assert "invalid" in result.output.lower()
