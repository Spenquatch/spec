"""Unit tests for test fixture migration utilities.

Tests the test_migration_utils module that provides utilities for migrating
test fixtures from singleton-dependent patterns to context-based dependency
injection patterns.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from spec_cli.core.context import SpecContext
from spec_cli.utils.test_migration_utils import (
    FixtureMigrationError,
    create_context_fixture,
    create_mock_context_fixture,
    migrate_singleton_fixture,
    validate_test_isolation,
)


class TestCreateContextFixture:
    """Test create_context_fixture functionality."""

    def test_create_context_fixture_when_factory_method_provided_then_creates_valid_fixture(
        self,
    ):
        """Test creating context fixture from valid factory method."""

        def test_factory():
            return SpecContext.create_for_testing()

        fixture_func = create_context_fixture(test_factory)

        # Verify fixture function was created
        assert callable(fixture_func)
        assert hasattr(fixture_func, "_pytestfixturefunction")
        assert fixture_func.__name__ == "test_factory_fixture"

        # Verify fixture returns proper context
        context = fixture_func()
        assert isinstance(context, SpecContext)
        assert context.settings is not None
        assert context.console is not None
        assert context.progress is not None

    def test_create_context_fixture_when_factory_with_args_then_handles_parameters(
        self,
    ):
        """Test creating context fixture from factory that expects arguments."""

        def factory_with_args(debug_mode=False):
            return SpecContext.create_for_testing({"debug_enabled": debug_mode})

        fixture_func = create_context_fixture(factory_with_args)

        # Verify fixture works with arguments
        context = fixture_func(debug_mode=True)
        assert isinstance(context, SpecContext)
        assert context.settings.debug_enabled is True

    def test_create_context_fixture_when_invalid_factory_then_raises_migration_error(
        self,
    ):
        """Test error handling for invalid factory method."""
        with pytest.raises(
            FixtureMigrationError, match="Factory method must be callable"
        ):
            create_context_fixture("not_callable")

    def test_create_context_fixture_when_factory_returns_wrong_type_then_raises_error(
        self,
    ):
        """Test error handling when factory returns non-SpecContext."""

        def bad_factory():
            return "not_a_context"

        fixture_func = create_context_fixture(bad_factory)

        with pytest.raises(
            FixtureMigrationError, match="Factory method must return SpecContext"
        ):
            fixture_func()

    def test_create_context_fixture_when_factory_throws_exception_then_propagates_error(
        self,
    ):
        """Test error handling when factory method throws exception."""

        def failing_factory():
            raise ValueError("Factory failed")

        fixture_func = create_context_fixture(failing_factory)

        with pytest.raises(
            FixtureMigrationError, match="Failed to create context from factory"
        ):
            fixture_func()

class TestValidateTestIsolation:
    """Test validate_test_isolation functionality."""

    def test_validate_test_isolation_when_isolated_test_then_returns_true(self):
        """Test validation passes for properly isolated test."""

        def test_with_context(spec_context):
            """Test function using context injection."""
            result = spec_context.settings.debug_enabled
            return result

        is_isolated = validate_test_isolation(test_with_context)
        assert is_isolated is True

    def test_validate_test_isolation_when_state_contamination_then_returns_false(self):
        """Test validation fails for test with state contamination patterns."""

        def test_with_singleton():
            """Test function using singleton patterns."""
            from spec_cli.config.settings import get_settings

            settings = get_settings()
            return settings.debug_enabled

        is_isolated = validate_test_isolation(test_with_singleton)
        assert is_isolated is False

    def test_validate_test_isolation_when_environment_access_then_returns_false(self):
        """Test validation fails for test with environment variable access."""

        def test_with_env_access():
            """Test function accessing environment variables."""
            import os

            value = os.environ["SOME_VAR"]
            return value

        is_isolated = validate_test_isolation(test_with_env_access)
        assert is_isolated is False

    def test_validate_test_isolation_when_invalid_function_then_raises_error(self):
        """Test error handling for invalid test function."""
        with pytest.raises(
            FixtureMigrationError, match="Test function must be callable"
        ):
            validate_test_isolation("not_callable")

    def test_validate_test_isolation_when_no_context_param_then_returns_false(self):
        """Test validation fails for test without context parameter."""

        def test_without_context():
            """Test function without context parameter."""
            return True

        is_isolated = validate_test_isolation(test_without_context)
        assert is_isolated is False

    def test_validate_test_isolation_when_source_unavailable_then_returns_false(self):
        """Test validation handles case where source code is unavailable."""
        # Create a function where source can't be retrieved
        mock_func = Mock()
        mock_func.__name__ = "mock_test"
        mock_func.__module__ = "unknown"

        # Mock inspect.signature to return context parameter
        with pytest.mock.patch("inspect.signature") as mock_sig:
            mock_param = Mock()
            mock_param.lower.return_value = "spec_context"
            mock_sig.return_value.parameters.keys.return_value = ["spec_context"]

            # Mock inspect.getsource to raise OSError
            with pytest.mock.patch("inspect.getsource", side_effect=OSError):
                is_isolated = validate_test_isolation(mock_func)
                assert is_isolated is False

class TestCreateMockContextFixture:
    """Test create_mock_context_fixture functionality."""

    def test_create_mock_context_fixture_when_no_overrides_then_creates_default_fixture(
        self,
    ):
        """Test creating mock context fixture with default settings."""
        fixture_func = create_mock_context_fixture()

        # Verify fixture function was created
        assert callable(fixture_func)
        assert hasattr(fixture_func, "_pytestfixturefunction")

        # Verify fixture returns proper mock context
        context = fixture_func()
        assert isinstance(context, SpecContext)
        assert context.settings is not None
        assert context.console is not None
        assert context.progress is not None

    def test_create_mock_context_fixture_when_settings_overrides_then_applies_settings(
        self,
    ):
        """Test creating mock context fixture with settings overrides."""
        settings_overrides = {"debug_enabled": True, "console_width": 120}
        fixture_func = create_mock_context_fixture(
            settings_overrides=settings_overrides
        )

        context = fixture_func()
        assert context.settings.debug_enabled is True
        assert context.settings.console_width == 120

    def test_create_mock_context_fixture_when_console_overrides_then_applies_console_behavior(
        self,
    ):
        """Test creating mock context fixture with console overrides."""
        console_overrides = {"supports_color": True, "get_width": 100}
        fixture_func = create_mock_context_fixture(console_overrides=console_overrides)

        context = fixture_func()
        # Check that overrides were applied to mock
        assert hasattr(context.console, "supports_color")
        assert hasattr(context.console, "get_width")

    def test_create_mock_context_fixture_when_progress_overrides_then_applies_progress_behavior(
        self,
    ):
        """Test creating mock context fixture with progress overrides."""
        progress_overrides = {"start_operation": "custom_op_123"}
        fixture_func = create_mock_context_fixture(
            progress_overrides=progress_overrides
        )

        context = fixture_func()
        # Check that overrides were applied to mock
        assert hasattr(context.progress, "start_operation")

    def test_create_mock_context_fixture_when_all_overrides_then_applies_all_configurations(
        self,
    ):
        """Test creating mock context fixture with all types of overrides."""
        settings_overrides = {"debug_enabled": True}
        console_overrides = {"supports_color": False}
        progress_overrides = {"start_operation": "test_op"}

        fixture_func = create_mock_context_fixture(
            settings_overrides=settings_overrides,
            console_overrides=console_overrides,
            progress_overrides=progress_overrides,
        )

        context = fixture_func()
        assert context.settings.debug_enabled is True
        assert hasattr(context.console, "supports_color")
        assert hasattr(context.progress, "start_operation")

class TestMigrateSingletonFixture:
    """Test migrate_singleton_fixture functionality."""

    def test_migrate_singleton_fixture_when_settings_fixture_then_returns_context_settings(
        self,
    ):
        """Test migrating settings fixture to context-based pattern."""

        @pytest.fixture
        def legacy_settings():
            # This would have been: return get_settings()
            return Mock()

        migrated_fixture = migrate_singleton_fixture(legacy_settings)

        # Verify migrated fixture function
        assert callable(migrated_fixture)
        assert hasattr(migrated_fixture, "_pytestfixturefunction")
        assert migrated_fixture.__name__ == "legacy_settings_migrated"

        # Test the fixture with a mock context
        mock_context = SpecContext.create_for_testing()
        result = migrated_fixture(mock_context)
        assert result == mock_context.settings

    def test_migrate_singleton_fixture_when_console_fixture_then_returns_context_console(
        self,
    ):
        """Test migrating console fixture to context-based pattern."""

        @pytest.fixture
        def legacy_console():
            # This would have been: return get_console()
            return Mock()

        migrated_fixture = migrate_singleton_fixture(legacy_console)

        # Test the fixture with a mock context
        mock_context = SpecContext.create_for_testing()
        result = migrated_fixture(mock_context)
        assert result == mock_context.console

    def test_migrate_singleton_fixture_when_progress_fixture_then_returns_context_progress(
        self,
    ):
        """Test migrating progress fixture to context-based pattern."""

        @pytest.fixture
        def legacy_progress():
            # This would have been: return get_progress()
            return Mock()

        migrated_fixture = migrate_singleton_fixture(legacy_progress)

        # Test the fixture with a mock context
        mock_context = SpecContext.create_for_testing()
        result = migrated_fixture(mock_context)
        assert result == mock_context.progress

    def test_migrate_singleton_fixture_when_unknown_fixture_then_returns_full_context(
        self,
    ):
        """Test migrating unknown fixture type returns full context."""

        @pytest.fixture
        def legacy_unknown():
            return Mock()

        migrated_fixture = migrate_singleton_fixture(legacy_unknown)

        # Test the fixture with a mock context
        mock_context = SpecContext.create_for_testing()
        result = migrated_fixture(mock_context)
        assert result == mock_context

    def test_migrate_singleton_fixture_when_invalid_fixture_then_raises_error(self):
        """Test error handling for invalid fixture function."""
        with pytest.raises(
            FixtureMigrationError, match="Legacy fixture must be callable"
        ):
            migrate_singleton_fixture("not_callable")

    def test_migrate_singleton_fixture_when_fixture_execution_fails_then_raises_error(
        self,
    ):
        """Test error handling when migrated fixture execution fails."""

        @pytest.fixture
        def legacy_settings():
            return Mock()

        migrated_fixture = migrate_singleton_fixture(legacy_settings)

        # Test with invalid context (None)
        with pytest.raises(FixtureMigrationError, match="Failed to migrate fixture"):
            migrated_fixture(None)

class TestContextFixtureMigration:
    """Test context fixture migration integration."""

    def test_context_fixture_migration_when_singleton_fixtures_replaced_then_no_shared_state(
        self,
    ):
        """Test that migrated fixtures don't share state between invocations."""

        def test_factory():
            return SpecContext.create_for_testing({"debug_enabled": False})

        fixture_func = create_context_fixture(test_factory)

        # Get two contexts from the fixture
        context1 = fixture_func()
        context2 = fixture_func()

        # Verify they are separate instances
        assert context1 is not context2
        assert context1.get_context_hash() != context2.get_context_hash()

        # Modify one context and verify the other is unaffected
        context1.settings.debug_enabled = True
        assert context2.settings.debug_enabled is False

    def test_test_migration_when_context_integration_then_uses_spec_context_factory(
        self,
    ):
        """Test that migration integrates with SpecContext factory methods."""

        def factory_using_testing():
            return SpecContext.create_for_testing()

        def factory_using_cli():
            # This would normally use create_for_cli but we'll mock it
            return SpecContext.create_for_testing({"root_path": Path("/test")})

        # Test both factory patterns
        testing_fixture = create_context_fixture(factory_using_testing)
        cli_fixture = create_context_fixture(factory_using_cli)

        testing_context = testing_fixture()
        cli_context = cli_fixture()

        assert isinstance(testing_context, SpecContext)
        assert isinstance(cli_context, SpecContext)
        assert testing_context.settings.root_path != cli_context.settings.root_path

    def test_fixture_migration_when_isolation_validation_then_prevents_state_contamination(
        self,
    ):
        """Test that migration validation prevents state contamination."""

        def good_test_function(spec_context):
            """Well-isolated test using context injection."""
            return spec_context.settings.debug_enabled

        def bad_test_function():
            """Poorly isolated test with singleton access."""
            from spec_cli.config.settings import get_settings

            return get_settings().debug_enabled

        # Validate isolation
        assert validate_test_isolation(good_test_function) is True
        assert validate_test_isolation(bad_test_function) is False

        # Create fixtures for both patterns
        def good_factory():
            return SpecContext.create_for_testing()

        good_fixture = create_context_fixture(good_factory)

        # Verify good fixture provides isolation
        context1 = good_fixture()
        context2 = good_fixture()
        assert context1 is not context2

# Test constants for magic number elimination
DEFAULT_TEST_CONSOLE_WIDTH = 80
DEFAULT_DEBUG_ENABLED = False
CUSTOM_CONSOLE_WIDTH = 120
CUSTOM_DEBUG_ENABLED = True
EXPECTED_ISOLATION_ISSUES_COUNT = 0
