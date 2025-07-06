"""Integration tests for gen command migration to context injection pattern."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.gen import gen_command
from spec_cli.config.settings import SpecSettings
from spec_cli.core.context import SpecContext

class TestGenCommandMigrationIntegration:
    """Integration tests for gen command migration with full context chain."""

    @pytest.fixture
    def test_context(self):
        """Create test SpecContext with real-like dependencies."""
        # Create mock settings that behave like real SpecSettings
        mock_settings = Mock(spec=SpecSettings)
        mock_settings.root_path = Path.cwd()
        mock_settings.spec_dir = Path(".spec")
        mock_settings.specs_dir = Path(".specs")

        # Create mock console interface
        mock_console = Mock()
        mock_console.print_message = Mock()
        mock_console.print_error = Mock()
        mock_console.print_success = Mock()
        mock_console.print_warning = Mock()

        # Create mock progress interface
        mock_progress = Mock()

        # Create SpecContext with mocked dependencies
        context = SpecContext(
            settings=mock_settings, console=mock_console, progress=mock_progress
        )
        return context

    @pytest.fixture
    def temp_source_file(self):
        """Create temporary Python source file for testing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write('''"""Test module for documentation generation."""

def hello_world():
    """Print hello world message."""
    print("Hello, World!")

class TestClass:
    """Test class for demonstration."""

    def __init__(self, name: str):
        """Initialize with name."""
        self.name = name

    def greet(self) -> str:
        """Return greeting message."""
        return f"Hello, {self.name}!"
''')
            yield Path(temp_file.name)
        Path(temp_file.name).unlink(missing_ok=True)

    def test_gen_command_migration_when_full_workflow_then_consistent_with_all_migrated_commands(
        self, test_context, temp_source_file
    ):
        """Test that gen command migration maintains consistency with other migrated commands."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks for successful generation
            mock_validate.return_value = [temp_source_file]

            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Documentation generated successfully",
                "data": {
                    "generated_files": [
                        str(
                            temp_source_file.parent
                            / ".specs"
                            / temp_source_file.name
                            / "index.md"
                        ),
                        str(
                            temp_source_file.parent
                            / ".specs"
                            / temp_source_file.name
                            / "history.md"
                        ),
                    ],
                    "generation_method": "ai_enhanced_template",
                    "files_generated": 2,
                },
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = test_context

            # Import and test gen command using the Click testing framework
            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(
                gen_command,
                [
                    str(temp_source_file),
                    "--template",
                    "comprehensive",
                    "--conflict-strategy",
                    "backup",
                    "--force",
                ],
            )

            # Verify successful execution
            assert result.exit_code == 0, f"Command failed with output: {result.output}"

            # Verify context injection pattern consistency
            mock_get_ctx.assert_called()  # Context should be retrieved

            # Verify settings passed from context (consistent with add/commit commands)
            mock_gen_class.assert_called_once_with(settings=test_context.settings)

            # Verify command execution with proper parameters
            mock_gen_instance.safe_execute.assert_called_once()
            call_kwargs = mock_gen_instance.safe_execute.call_args.kwargs

            # Verify parameters match expected migration pattern
            assert call_kwargs["files"] == [temp_source_file]
            assert call_kwargs["template"] == "comprehensive"
            assert call_kwargs["conflict_strategy"] == "backup"
            assert call_kwargs["force"] is True
            assert call_kwargs["dry_run"] is False  # Default value
            assert call_kwargs["interactive"] is False  # Default value

    def test_gen_command_when_used_with_migrated_add_then_context_consistent(
        self, test_context, temp_source_file
    ):
        """Test context consistency between gen and add commands."""
        # This test verifies that the context injection pattern
        # works consistently across different commands

        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = [temp_source_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Context consistency verified",
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = test_context

            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(gen_command, [str(temp_source_file)])

            # Verify same context pattern as other migrated commands
            assert result.exit_code == 0

            # Verify context injection occurred
            mock_get_ctx.assert_called()

            # Verify settings from context were used (same pattern as add command)
            mock_gen_class.assert_called_once()
            call_args = mock_gen_class.call_args
            assert call_args.kwargs["settings"] == test_context.settings

    def test_gen_command_when_used_with_migrated_commit_then_dependency_injection_works(
        self, test_context, temp_source_file
    ):
        """Test dependency injection compatibility with commit workflow."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks for gen + commit workflow
            mock_validate.return_value = [temp_source_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Ready for commit workflow",
                "data": {"generated_files": ["index.md", "history.md"]},
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = test_context

            from click.testing import CliRunner

            runner = CliRunner()

            # Test gen command with commit flag (simulating workflow)
            result = runner.invoke(
                gen_command,
                [str(temp_source_file), "--commit", "--message", "Add documentation"],
            )

            # Verify dependency injection pattern works for workflows
            assert result.exit_code == 0
            mock_gen_instance.safe_execute.assert_called_once()

            # Verify commit parameters are passed through correctly
            call_kwargs = mock_gen_instance.safe_execute.call_args.kwargs
            assert call_kwargs["commit"] is True
            assert call_kwargs["message"] == "Add documentation"

    def test_gen_command_when_context_factory_provides_dependencies_then_uses_injected_instances(
        self, test_context, temp_source_file
    ):
        """Test that gen command uses dependencies provided by context factory."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup specific mock settings with identifiable properties
            test_context.settings.debug_mode = True
            test_context.settings.verbose_output = True

            mock_validate.return_value = [temp_source_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Dependencies injected correctly",
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = test_context

            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(gen_command, [str(temp_source_file)])

            # Verify context factory pattern works
            assert result.exit_code == 0

            # Verify specific settings instance was injected
            mock_gen_class.assert_called_once_with(settings=test_context.settings)
            injected_settings = mock_gen_class.call_args.kwargs["settings"]
            assert hasattr(injected_settings, "debug_mode")
            assert injected_settings.debug_mode is True
            assert injected_settings.verbose_output is True

    def test_gen_command_when_singleton_elimination_complete_then_no_global_state_access(
        self, test_context, temp_source_file
    ):
        """Test that singleton elimination is complete and no global state is accessed."""
        # Verify that gen command function doesn't access global singletons
        import inspect

        import spec_cli.cli.commands.gen as gen_module

        # Get source code of the gen_command function
        source = inspect.getsource(gen_module.gen_command)

        # Verify no singleton access patterns
        forbidden_singleton_patterns = [
            "get_settings()",
            "get_console()",
            "get_progress()",
            "Settings()",  # Direct instantiation
            "Console()",  # Direct instantiation
        ]

        for pattern in forbidden_singleton_patterns:
            assert pattern not in source, (
                f"Found singleton pattern '{pattern}' in gen_command"
            )

        # Verify context injection pattern is present
        assert "context: SpecContext" in source
        assert "@context_injection" in source

        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Execute command to verify runtime behavior
            mock_validate.return_value = [temp_source_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "No global state accessed",
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = test_context

            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(gen_command, [str(temp_source_file)])

            # Verify successful execution without singleton access
            assert result.exit_code == 0

    def test_gen_command_when_error_during_context_injection_then_proper_error_handling(
        self, temp_source_file
    ):
        """Test proper error handling when context injection fails."""
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click"
        ) as mock_get_ctx:
            # Simulate context injection failure
            from spec_cli.cli.decorators import ContextInjectionError

            mock_get_ctx.side_effect = ContextInjectionError(
                "Test context injection failure"
            )

            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(gen_command, [str(temp_source_file)])

            # Verify error is properly handled
            assert result.exit_code != 0
            # Error message should be present (either in output or exception)
            error_present = "context injection failure" in result.output.lower() or (
                result.exception
                and "context injection failure" in str(result.exception).lower()
            )
            assert error_present, (
                f"Expected error message not found in output: {result.output}"
            )

    def test_gen_command_when_interactive_mode_then_context_supports_user_interaction(
        self, test_context, temp_source_file
    ):
        """Test that interactive mode works with context injection pattern."""
        with (
            patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate,
            patch("spec_cli.cli.commands.gen.GenCommand") as mock_gen_class,
            patch(
                "spec_cli.cli.decorators._get_spec_context_from_click"
            ) as mock_get_ctx,
        ):
            # Setup mocks
            mock_validate.return_value = [temp_source_file]
            mock_gen_instance = Mock()
            mock_gen_instance.safe_execute.return_value = {
                "success": True,
                "message": "Interactive mode completed",
                "data": {"user_interactions": 3},
            }
            mock_gen_class.return_value = mock_gen_instance
            mock_get_ctx.return_value = test_context

            from click.testing import CliRunner

            runner = CliRunner()
            result = runner.invoke(
                gen_command, [str(temp_source_file), "--interactive"]
            )

            # Verify interactive mode parameters are passed
            assert result.exit_code == 0
            call_kwargs = mock_gen_instance.safe_execute.call_args.kwargs
            assert call_kwargs["interactive"] is True

            # Verify context console is available for user interaction
            assert test_context.console is not None
            assert hasattr(test_context.console, "print_message")
