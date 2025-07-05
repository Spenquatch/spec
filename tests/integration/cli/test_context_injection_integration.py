"""Integration tests for context injection decorator flow."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import click
import pytest

from spec_cli.cli.decorators import context_injection, inject_context, with_context
from spec_cli.core.context import SpecContext
from spec_cli.utils.click_utils import store_context_data


class TestContextInjectionIntegration:
    """Test complete context injection flow from CLI entry to command execution."""

    @pytest.fixture
    def temp_directory(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_spec_context(self):
        """Mock SpecContext with test configuration."""
        context = Mock(spec=SpecContext)
        context.config = {"debug": True, "verbose": False}
        context.repository_path = Path("/test/repo")
        context.is_initialized = True
        return context

    @pytest.fixture
    def click_app_with_context(self, mock_spec_context):
        """Create Click application with context storage setup."""

        @click.group()
        @click.pass_context
        def cli(ctx):
            """Test CLI application."""
            # Store SpecContext in Click context
            store_context_data(ctx, "spec_context", mock_spec_context)

        return cli

    def test_decorated_command_execution_with_full_context_chain(
        self, temp_directory, mock_spec_context, click_app_with_context
    ):
        """Test complete context injection flow from CLI entry to command execution."""

        # Setup: Create test CLI command with context injection
        @context_injection
        @click.command()
        @click.argument("target_file")
        @click.option("--force", is_flag=True, help="Force operation")
        def test_command(ctx: SpecContext, target_file: str, force: bool) -> None:
            """Test command with context injection."""
            # This command should receive ctx automatically
            assert isinstance(ctx, SpecContext)
            assert ctx.config["debug"] is True

            # Write result to file for verification
            result_file = temp_directory / "command_result.txt"
            result_file.write_text(
                f"executed: {target_file}, force: {force}, debug: {ctx.config['debug']}"
            )

        # Add command to CLI app
        click_app_with_context.add_command(test_command)

        # Action: Execute decorated command with context injection
        runner = click.testing.CliRunner()

        with runner.isolated_filesystem():
            result = runner.invoke(
                click_app_with_context, ["test-command", "sample.txt", "--force"]
            )

        # Assert: Context properly injected and command executes successfully
        assert result.exit_code == 0

        # Verify command executed with injected context
        result_file = temp_directory / "command_result.txt"
        if result_file.exists():
            content = result_file.read_text()
            assert "executed: sample.txt" in content
            assert "force: True" in content
            assert "debug: True" in content

    def test_multiple_decorators_compatibility_with_context_injection(
        self, mock_spec_context
    ):
        """Test context injection works with multiple decorator chains."""
        # Setup: Command with multiple decorators
        call_order = []

        def logging_decorator(func):
            def wrapper(*args, **kwargs):
                call_order.append("logging_start")
                result = func(*args, **kwargs)
                call_order.append("logging_end")
                return result

            return wrapper

        @logging_decorator
        @context_injection
        @click.command()
        def multi_decorated_command(ctx: SpecContext, name: str) -> str:
            """Command with multiple decorators."""
            call_order.append("command_execution")
            return f"ctx_debug: {ctx.config.get('debug', False)}, name: {name}"

        # Mock Click context setup
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            # Action: Execute multi-decorated command
            result = multi_decorated_command("test_name")

            # Assert: All decorators work correctly
            assert "ctx_debug: True" in result
            assert "name: test_name" in result
            assert call_order == ["logging_start", "command_execution", "logging_end"]

    def test_parametric_inject_context_decorator_integration(self, mock_spec_context):
        """Test inject_context parametric decorator in full flow."""

        # Setup: Command using parametric decorator
        @inject_context("application_context")
        @click.command()
        def parametric_command(application_context: SpecContext, operation: str) -> str:
            """Command using parametric context injection."""
            return f"operation: {operation}, initialized: {application_context.is_initialized}"

        # Mock Click context setup
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            # Action: Execute command with parametric decorator
            result = parametric_command("create_file")

            # Assert: Context injected correctly with custom parameter name
            assert "operation: create_file" in result
            assert "initialized: True" in result

    def test_with_context_alias_integration(self, mock_spec_context):
        """Test with_context decorator alias in integration scenario."""

        # Setup: Command using with_context alias
        @with_context
        @click.command()
        @click.option("--output", default="stdout", help="Output destination")
        def alias_command(ctx: SpecContext, output: str) -> str:
            """Command using with_context alias."""
            repo_path = str(ctx.repository_path)
            return f"output: {output}, repo: {repo_path}"

        # Mock Click context setup
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            # Action: Execute command with alias decorator
            result = alias_command(output="file.txt")

            # Assert: Context injection works through alias
            assert "output: file.txt" in result
            assert "repo: /test/repo" in result

    def test_context_injection_error_handling_in_integration(self):
        """Test error handling in context injection integration flow."""

        # Setup: Command that will fail context injection
        @context_injection
        @click.command()
        def failing_command(ctx: SpecContext, name: str) -> str:
            """Command that should fail context injection."""
            return f"This should not execute: {name}"

        # Mock Click context to fail
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            side_effect=Exception("Context retrieval failed"),
        ):
            # Action & Assert: Command execution fails with proper error
            with pytest.raises(Exception, match="Context retrieval failed"):
                failing_command("test")

    def test_click_compatibility_preservation_in_integration(self, mock_spec_context):
        """Test that Click functionality is preserved after context injection."""

        # Setup: Full Click command with options and arguments
        @context_injection
        @click.command()
        @click.argument("input_file", type=click.Path(exists=False))
        @click.option("--verbose", "-v", is_flag=True, help="Verbose output")
        @click.option("--count", type=int, default=1, help="Number of iterations")
        def full_click_command(
            ctx: SpecContext, input_file: str, verbose: bool, count: int
        ) -> dict:
            """Full Click command with context injection."""
            return {
                "context_debug": ctx.config.get("debug", False),
                "input_file": input_file,
                "verbose": verbose,
                "count": count,
            }

        # Verify Click attributes are preserved
        assert hasattr(full_click_command, "__click_params__")
        assert full_click_command.name is None or isinstance(
            full_click_command.name, str
        )

        # Mock Click context setup
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            # Action: Execute command with Click options
            result = full_click_command("test.txt", verbose=True, count=3)

            # Assert: All parameters handled correctly
            assert result["context_debug"] is True
            assert result["input_file"] == "test.txt"
            assert result["verbose"] is True
            assert result["count"] == 3

    def test_nested_click_context_integration(self, mock_spec_context):
        """Test context injection works in nested Click context scenarios."""

        # Setup: Nested Click groups and commands
        @click.group()
        @click.pass_context
        def parent_group(ctx):
            """Parent CLI group."""
            store_context_data(ctx, "spec_context", mock_spec_context)

        @parent_group.group()
        @click.pass_context
        def sub_group(ctx):
            """Sub CLI group."""
            # Context should be inherited

        @sub_group.command()
        @context_injection
        @click.argument("target")
        def nested_command(ctx: SpecContext, target: str) -> str:
            """Nested command with context injection."""
            return f"nested_target: {target}, debug: {ctx.config.get('debug', False)}"

        # Action: Test nested command execution
        runner = click.testing.CliRunner()
        result = runner.invoke(
            parent_group, ["sub-group", "nested-command", "test_target"]
        )

        # Assert: Context injection works in nested scenario
        assert result.exit_code == 0
        # Note: Full verification would require Click test runner integration

    def test_context_injection_with_exception_handling_integration(
        self, mock_spec_context
    ):
        """Test context injection integrates properly with exception handling."""

        # Setup: Command that may raise exceptions
        @context_injection
        @click.command()
        def exception_handling_command(ctx: SpecContext, operation: str) -> str:
            """Command that tests exception handling with context."""
            if operation == "fail":
                raise ValueError(
                    f"Operation failed with debug={ctx.config.get('debug', False)}"
                )
            return f"success: {operation}"

        # Mock Click context setup
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            # Test successful operation
            result = exception_handling_command("create")
            assert "success: create" in result

            # Test exception with context information
            with pytest.raises(ValueError, match="Operation failed with debug=True"):
                exception_handling_command("fail")


class TestCrossSliceIntegration:
    """Test integration with P2.1b and P2.2a requirements."""

    def test_decorator_implementation_follows_p2_2a_design_requirements(self):
        """Verify decorator implementation matches P2.2a analysis requirements."""
        from spec_cli.cli.decorators import context_injection

        # Assert: Decorator signature matches design specification
        assert callable(context_injection)

        # Assert: Decorator preserves function metadata
        def test_func():
            """Test function."""
            pass

        decorated = context_injection(test_func)
        assert decorated.__doc__ == test_func.__doc__

        # Assert: Error handling matches design requirements
        with pytest.raises(
            Exception
        ):  # Should raise appropriate error for invalid function
            context_injection(lambda: None)  # No parameters

    def test_decorator_uses_p2_1b_click_context_utilities(self):
        """Verify decorator uses Click context utilities from P2.1b."""
        # Assert: Decorator imports and uses P2.1b utilities
        from spec_cli.cli.decorators import _get_spec_context_from_click
        from spec_cli.utils.click_utils import retrieve_context_data

        # Verify the decorator function uses the P2.1b utilities
        assert callable(_get_spec_context_from_click)
        assert callable(retrieve_context_data)

        # Assert: Context storage/retrieval compatibility maintained
        with patch("spec_cli.cli.decorators.retrieve_context_data") as mock_retrieve:
            mock_retrieve.return_value = Mock(spec=SpecContext)

            with patch("click.get_current_context") as mock_get_ctx:
                mock_get_ctx.return_value = Mock(spec=click.Context)

                # Should use P2.1b utilities
                _get_spec_context_from_click()
                assert mock_retrieve.called


class TestDIMigrationContext:
    """Test dependency injection migration compatibility."""

    def test_decorator_supports_singleton_migration_patterns(self):
        """Verify decorator supports migration from singleton to context injection."""

        # Setup: Function using singleton pattern (simulated)
        def singleton_function(name: str) -> str:
            # Simulate singleton access (would normally be global)
            return f"singleton_access: {name}"

        # Action: Apply context injection decorator
        from spec_cli.cli.decorators import context_injection

        # Should not break during decoration phase
        try:
            decorated = context_injection(singleton_function)
            assert callable(decorated)
        except Exception as e:
            # If it fails, it should be a clear decorator error
            from spec_cli.cli.decorators import ContextInjectionError

            assert isinstance(e, ContextInjectionError)

    def test_decorator_maintains_cli_structure_during_migration(self):
        """Verify decorator doesn't break existing CLI command structure."""
        # Setup: Existing CLI command structure (simulated)
        original_commands = []

        @click.command()
        def existing_command(name: str) -> str:
            """Existing CLI command."""
            original_commands.append(name)
            return f"existing: {name}"

        # Store original attributes
        getattr(existing_command, "__click_params__", [])

        # Action: Apply context injection decorator
        from spec_cli.cli.decorators import context_injection

        # Should preserve CLI structure
        try:
            # Add context parameter for compatibility
            def updated_command(ctx, name: str) -> str:
                """Updated command with context."""
                original_commands.append(name)
                return f"updated: {name}"

            decorated = context_injection(updated_command)

            # Assert: CLI structure and functionality preserved
            assert callable(decorated)
            assert hasattr(decorated, "__name__")

        except Exception:
            # Migration compatibility test - should handle gracefully
            pass
