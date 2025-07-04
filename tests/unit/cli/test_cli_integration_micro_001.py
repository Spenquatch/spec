"""Integration tests for CLI command interactions and flow.

This module tests the integration between CLI app components and command flow.
"""

from spec_cli.cli.app import app
from spec_cli.utils.test_helpers.cli_test_helpers import create_cli_command_runner


class TestCLIIntegrationMicro001:
    """Integration tests for CLI app - Micro-Agent Implementation."""

    def setup_method(self):
        """Setup using discovered CLI test helpers."""
        self.cli_runner = create_cli_command_runner()

    def test_app_help_command_integration(self):
        """Test integration between app and help command."""
        result = self.cli_runner.run_command(app, ["help"])

        result.assert_success()
        # Should show general help information
        result.assert_output_contains("Spec CLI")

    def test_app_version_command_integration(self):
        """Test version display integrates properly with app."""
        result = self.cli_runner.run_command(app, ["--version"])

        result.assert_success()
        result.assert_output_contains("Spec CLI v0.1.0")

    def test_app_help_for_specific_command_integration(self):
        """Test help for specific commands integrates properly."""
        result = self.cli_runner.run_command(app, ["help", "init"])

        result.assert_success()
        # Should show init-specific help
        result.assert_output_contains("init")

    def test_app_error_handling_flow_integration(self):
        """Test error handling flow integration across CLI components."""
        # Test invalid command flows through proper error handling
        result = self.cli_runner.run_command(app, ["nonexistent-command"])

        result.assert_failure()
        result.assert_output_contains("No such command")

    def test_app_command_routing_integration(self):
        """Test command routing integrates properly across the CLI system."""
        # Test that commands are properly registered and accessible
        expected_commands = ["init", "status", "help", "gen", "add", "commit"]

        for command in expected_commands:
            result = self.cli_runner.run_command(app, [command, "--help"])
            result.assert_success()
            # Should show help for the specific command
            result.assert_output_contains(command)

    def test_cli_context_preservation_integration(self):
        """Test that CLI context is preserved across command invocations."""
        # Test help flag consistency
        help_result = self.cli_runner.run_command(app, ["--help"])
        help_short_result = self.cli_runner.run_command(app, ["-h"])

        help_result.assert_success()
        help_short_result.assert_success()

        # Both should contain similar help content
        assert "Spec CLI" in help_result.output
        assert "Spec CLI" in help_short_result.output
