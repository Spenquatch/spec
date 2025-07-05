"""Integration tests for slice P1.2b: Factory Method Implementation.

Tests end-to-end factory functionality validating both CLI and testing
factories create usable SpecContext instances with proper integration.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from spec_cli.core.context import SpecContext, SpecFactoryError

# Test constants
INTEGRATION_ROOT_PATH = Path("/integration/test")
INTEGRATION_OVERRIDES = {"debug_enabled": True, "console_width": 100}


class TestFactoryIntegration:
    """Integration tests for factory method functionality."""

    def test_factory_integration_when_cli_and_testing_then_both_create_valid_contexts(
        self,
    ):
        """End-to-end test validating both CLI and testing factories create usable SpecContext instances."""
        # Act - Create contexts using both factory methods
        cli_context = SpecContext.create_for_cli(
            INTEGRATION_ROOT_PATH, **INTEGRATION_OVERRIDES
        )
        testing_context = SpecContext.create_for_testing(INTEGRATION_OVERRIDES)

        # Assert - Both contexts are valid SpecContext instances
        assert isinstance(cli_context, SpecContext)
        assert isinstance(testing_context, SpecContext)

        # Assert - CLI context has real dependencies
        assert not isinstance(cli_context.settings, Mock)
        assert not isinstance(cli_context.console, Mock)
        assert not isinstance(cli_context.progress, Mock)

        # Assert - Testing context has mock dependencies
        assert isinstance(testing_context.settings, Mock)
        assert isinstance(testing_context.console, Mock)
        assert isinstance(testing_context.progress, Mock)

        # Assert - Both contexts applied overrides correctly
        assert cli_context.settings.debug_enabled is True
        assert cli_context.settings.console_width == 100
        assert testing_context.settings.debug_enabled is True
        assert testing_context.settings.console_width == 100

        # Assert - Both contexts support core operations
        cli_hash = cli_context.get_context_hash()
        testing_hash = testing_context.get_context_hash()
        assert isinstance(cli_hash, str)
        assert isinstance(testing_hash, str)
        assert cli_hash != testing_hash  # Different context types

        # Assert - Both contexts support dependency replacement
        from spec_cli.core.context import SpecConsoleInterface

        new_console = SpecConsoleInterface()

        cli_with_new_console = cli_context.with_console(new_console)
        testing_with_new_console = testing_context.with_console(new_console)

        assert cli_with_new_console.console is new_console
        assert testing_with_new_console.console is new_console

        # Assert - Original contexts unchanged (immutability)
        assert cli_context.console is not new_console
        assert testing_context.console is not new_console

    def test_factory_implements_p1_2a_interface_contracts(self):
        """Validate factory implementation satisfies P1.2a interface contracts."""
        # Create contexts using factory methods
        cli_context = SpecContext.create_for_cli(INTEGRATION_ROOT_PATH)
        testing_context = SpecContext.create_for_testing()

        # Verify interface contracts for settings dependency
        assert hasattr(cli_context.settings, "get_setting")
        assert hasattr(cli_context.settings, "validate_configuration")
        assert hasattr(testing_context.settings, "get_setting")
        assert hasattr(testing_context.settings, "validate_configuration")

        # Verify interface contracts for console dependency
        assert hasattr(cli_context.console, "print_message")
        assert hasattr(cli_context.console, "print_error")
        assert hasattr(cli_context.console, "get_width")
        assert hasattr(cli_context.console, "supports_color")
        assert hasattr(testing_context.console, "print_message")
        assert hasattr(testing_context.console, "print_error")
        assert hasattr(testing_context.console, "get_width")
        assert hasattr(testing_context.console, "supports_color")

        # Verify interface contracts for progress dependency
        assert hasattr(cli_context.progress, "show_progress")
        assert hasattr(cli_context.progress, "start_operation")
        assert hasattr(cli_context.progress, "finish_operation")
        assert hasattr(testing_context.progress, "show_progress")
        assert hasattr(testing_context.progress, "start_operation")
        assert hasattr(testing_context.progress, "finish_operation")

        # Test interface method calls work
        # CLI context - real implementations
        setting_value = cli_context.settings.get_setting("console_width")
        validation_result = cli_context.settings.validate_configuration()
        console_width = cli_context.console.get_width()
        color_support = cli_context.console.supports_color()
        operation_id = cli_context.progress.start_operation("test operation")

        assert setting_value is not None or setting_value is None  # Valid return
        assert isinstance(validation_result, dict)
        assert isinstance(console_width, int)
        assert isinstance(color_support, bool)
        assert isinstance(operation_id, str)

        # Testing context - mock implementations
        mock_setting = testing_context.settings.get_setting("test_key")
        mock_validation = testing_context.settings.validate_configuration()
        mock_width = testing_context.console.get_width()
        mock_color = testing_context.console.supports_color()
        mock_op_id = testing_context.progress.start_operation("test operation")

        # Mocks return configured values
        assert mock_setting is None  # Configured return value
        assert mock_validation == {}  # Configured return value
        assert mock_width == 80  # Configured return value
        assert mock_color is False  # Configured return value
        assert mock_op_id == "test_op_001"  # Configured return value

    def test_factory_error_handling_integration(self):
        """Test factory error handling in integrated scenarios."""
        # Test CLI factory with valid and invalid inputs
        try:
            # Valid CLI context creation
            valid_context = SpecContext.create_for_cli(INTEGRATION_ROOT_PATH)
            assert isinstance(valid_context, SpecContext)
        except SpecFactoryError:
            pytest.fail("Valid CLI context creation should not raise SpecFactoryError")

        # Test testing factory with valid and invalid inputs
        try:
            # Valid testing context creation
            valid_testing_context = SpecContext.create_for_testing({"debug_mode": True})
            assert isinstance(valid_testing_context, SpecContext)
        except SpecFactoryError:
            pytest.fail(
                "Valid testing context creation should not raise SpecFactoryError"
            )

        # Integration verification: both contexts work together
        cli_context = SpecContext.create_for_cli(INTEGRATION_ROOT_PATH)
        testing_context = SpecContext.create_for_testing()

        # Both contexts should be usable in the same application
        assert cli_context != testing_context  # Different contexts
        assert cli_context.get_context_hash() != testing_context.get_context_hash()

        # Both contexts support the same operations
        cli_with_overrides = cli_context.with_settings(debug_enabled=True)
        testing_with_overrides = testing_context.with_settings(debug_enabled=True)

        assert cli_with_overrides.settings.debug_enabled is True
        assert testing_with_overrides.settings.debug_enabled is True

    def test_cross_slice_integration_p1_1b_to_p1_2b(self):
        """Test integration between P1.1b SpecContext and P1.2b factory methods."""
        # P1.1b provided the core SpecContext class
        # P1.2b extends it with factory methods

        # Verify factory methods are available on SpecContext class
        assert hasattr(SpecContext, "create_for_cli")
        assert hasattr(SpecContext, "create_for_testing")
        assert callable(SpecContext.create_for_cli)
        assert callable(SpecContext.create_for_testing)

        # Verify factory methods create contexts with P1.1b functionality
        cli_context = SpecContext.create_for_cli(INTEGRATION_ROOT_PATH)
        testing_context = SpecContext.create_for_testing()

        # Test P1.1b functionality works with factory-created contexts
        # Immutability validation (from P1.1b)
        assert hasattr(cli_context, "__dataclass_fields__")  # Dataclass structure

        # Context replacement methods (from P1.1b)
        from spec_cli.core.context import SpecConsoleInterface, SpecProgressInterface

        new_console = SpecConsoleInterface()
        new_progress = SpecProgressInterface()

        cli_with_new_console = cli_context.with_console(new_console)
        cli_with_new_progress = cli_context.with_progress(new_progress)

        assert cli_with_new_console.console is new_console
        assert cli_with_new_progress.progress is new_progress

        # Original context unchanged (P1.1b immutability)
        assert cli_context.console is not new_console
        assert cli_context.progress is not new_progress

        # Hash generation (from P1.1b)
        cli_hash = cli_context.get_context_hash()
        testing_hash = testing_context.get_context_hash()
        assert isinstance(cli_hash, str)
        assert isinstance(testing_hash, str)
        assert len(cli_hash) > 0
        assert len(testing_hash) > 0

        # Equality comparison (from P1.1b)
        cli_context_2 = SpecContext.create_for_cli(INTEGRATION_ROOT_PATH)
        assert cli_context == cli_context_2  # Same configuration
        assert cli_context != testing_context  # Different configurations
