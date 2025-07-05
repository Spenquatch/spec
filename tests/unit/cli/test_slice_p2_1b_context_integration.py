"""Unit tests for Click context integration utilities."""

from unittest.mock import patch

import click
import pytest

from spec_cli.cli.context_integration import (
    get_context_keys,
    integrate_spec_context,
    retrieve_spec_context,
    retrieve_typed_context_data,
    setup_dependency_injection_context,
    store_typed_context_data,
    teardown_dependency_injection_context,
)
from spec_cli.core.context import (
    SpecConsoleInterface,
    SpecContext,
    SpecProgressInterface,
    SpecSettingsInterface,
)
from spec_cli.utils.click_utils import ClickIntegrationError

# Test constants
TEST_CONFIG = {"debug": True, "verbose": False}
TEST_STRING = "test_string"
TEST_INT = 42


@pytest.fixture
def mock_spec_context():
    """Create a mock SpecContext for testing."""
    settings = SpecSettingsInterface()
    console = SpecConsoleInterface()
    progress = SpecProgressInterface()
    return SpecContext(settings=settings, console=console, progress=progress)


class TestIntegrateSpecContext:
    """Test SpecContext integration functionality."""

    def test_integrate_spec_context_when_valid_inputs_then_stores_context_successfully(
        self, mock_spec_context
    ):
        """Test SpecContext integration with Click context."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Execute
        integrate_spec_context(ctx, mock_spec_context)

        # Verify
        assert ctx.obj is not None
        assert "spec_spec_context" in ctx.obj
        assert ctx.obj["spec_spec_context"] is mock_spec_context

    def test_integrate_spec_context_when_invalid_click_context_then_raises_type_error(
        self, mock_spec_context
    ):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            integrate_spec_context(invalid_ctx, mock_spec_context)

    def test_integrate_spec_context_when_invalid_spec_context_then_raises_type_error(
        self,
    ):
        """Test type error for invalid SpecContext."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        invalid_spec_ctx = "not_a_spec_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected SpecContext"):
            integrate_spec_context(ctx, invalid_spec_ctx)

    @patch("spec_cli.cli.context_integration.debug_logger")
    def test_integrate_spec_context_when_successful_then_logs_debug_info(
        self, mock_logger, mock_spec_context
    ):
        """Test debug logging on successful integration."""
        # Setup
        cmd = click.Command("test_cmd")
        ctx = click.Context(cmd)

        # Execute
        integrate_spec_context(ctx, mock_spec_context)

        # Verify
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == "DEBUG"
        assert "SpecContext integrated" in call_args[0][1]
        assert call_args[1]["click_command"] == "test_cmd"


class TestRetrieveSpecContext:
    """Test SpecContext retrieval functionality."""

    def test_retrieve_spec_context_when_context_exists_then_returns_spec_context(self, mock_spec_context):
        """Test SpecContext retrieval when it exists."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {"spec_spec_context": mock_spec_context}

        # Execute
        result = retrieve_spec_context(ctx)

        # Verify
        assert result is mock_spec_context

    def test_retrieve_spec_context_when_context_missing_then_returns_none(self):
        """Test SpecContext retrieval when missing."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {}

        # Execute
        result = retrieve_spec_context(ctx)

        # Verify
        assert result is None

    def test_retrieve_spec_context_when_context_obj_none_then_returns_none(self):
        """Test retrieval when context obj is None."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = None

        # Execute
        result = retrieve_spec_context(ctx)

        # Verify
        assert result is None

    def test_retrieve_spec_context_when_invalid_context_then_raises_type_error(self):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            retrieve_spec_context(invalid_ctx)

    def test_retrieve_spec_context_when_wrong_type_stored_then_raises_integration_error(
        self,
    ):
        """Test error handling when wrong type is stored."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {"spec_spec_context": "not_a_spec_context"}

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="Invalid SpecContext type"):
            retrieve_spec_context(ctx)


class TestStoreTypedContextData:
    """Test typed context data storage functionality."""

    def test_store_typed_context_data_when_valid_type_then_stores_successfully(self):
        """Test typed data storage with valid type."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Execute
        store_typed_context_data(ctx, "config", TEST_CONFIG, dict)

        # Verify
        assert ctx.obj["spec_config"] == TEST_CONFIG

    def test_store_typed_context_data_when_type_mismatch_then_raises_integration_error(
        self,
    ):
        """Test type validation failure."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="Type validation failed"):
            store_typed_context_data(ctx, "config", TEST_STRING, dict)

    def test_store_typed_context_data_when_invalid_context_then_raises_type_error(self):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            store_typed_context_data(invalid_ctx, "config", TEST_CONFIG, dict)

    def test_store_typed_context_data_when_empty_key_then_raises_integration_error(
        self,
    ):
        """Test error handling for empty key."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="non-empty string"):
            store_typed_context_data(ctx, "", TEST_CONFIG, dict)

    @patch("spec_cli.cli.context_integration.debug_logger")
    def test_store_typed_context_data_when_successful_then_logs_debug_info(
        self, mock_logger
    ):
        """Test debug logging on successful storage."""
        # Setup
        cmd = click.Command("test_cmd")
        ctx = click.Context(cmd)

        # Execute
        store_typed_context_data(ctx, "config", TEST_CONFIG, dict)

        # Verify
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == "DEBUG"
        assert "Typed context data stored" in call_args[0][1]
        assert call_args[1]["key"] == "config"
        assert call_args[1]["data_type"] == "dict"


class TestRetrieveTypedContextData:
    """Test typed context data retrieval functionality."""

    def test_retrieve_typed_context_data_when_valid_type_then_returns_data(self):
        """Test typed data retrieval with valid type."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {"spec_config": TEST_CONFIG}

        # Execute
        result = retrieve_typed_context_data(ctx, "config", dict)

        # Verify
        assert result == TEST_CONFIG

    def test_retrieve_typed_context_data_when_missing_key_then_returns_default(self):
        """Test retrieval with missing key returns default."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {}
        default = {"default": True}

        # Execute
        result = retrieve_typed_context_data(ctx, "config", dict, default)

        # Verify
        assert result == default

    def test_retrieve_typed_context_data_when_type_mismatch_then_raises_integration_error(
        self,
    ):
        """Test type validation failure on retrieval."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {"spec_config": TEST_STRING}  # Wrong type

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="Type validation failed"):
            retrieve_typed_context_data(ctx, "config", dict)

    def test_retrieve_typed_context_data_when_default_returned_then_no_type_validation(
        self,
    ):
        """Test no type validation when default is returned."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {}
        default = "string_default"  # Different type than expected

        # Execute (should not raise type error)
        result = retrieve_typed_context_data(ctx, "config", dict, default)

        # Verify
        assert result == default

    def test_retrieve_typed_context_data_when_invalid_context_then_raises_type_error(
        self,
    ):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            retrieve_typed_context_data(invalid_ctx, "config", dict)

    def test_retrieve_typed_context_data_when_empty_key_then_raises_integration_error(
        self,
    ):
        """Test error handling for empty key."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="non-empty string"):
            retrieve_typed_context_data(ctx, "", dict)


class TestSetupDependencyInjectionContext:
    """Test dependency injection context setup functionality."""

    def test_setup_dependency_injection_context_when_valid_context_then_initializes_successfully(
        self,
    ):
        """Test dependency injection setup."""
        # Setup
        cmd = click.Command("test_cmd")
        ctx = click.Context(cmd)

        # Execute
        setup_dependency_injection_context(ctx)

        # Verify
        assert ctx.obj is not None
        assert "spec_di_metadata" in ctx.obj
        metadata = ctx.obj["spec_di_metadata"]
        assert metadata["initialized"] is True
        assert metadata["command"] == "test_cmd"
        assert metadata["parent_command"] is None

    def test_setup_dependency_injection_context_when_existing_obj_then_preserves_data(
        self,
    ):
        """Test setup preserves existing context data."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {"existing": "data"}

        # Execute
        setup_dependency_injection_context(ctx)

        # Verify
        assert ctx.obj["existing"] == "data"
        assert "spec_di_metadata" in ctx.obj

    def test_setup_dependency_injection_context_when_parent_context_then_includes_parent(
        self,
    ):
        """Test setup with parent context."""
        # Setup
        parent_cmd = click.Command("parent")
        parent_ctx = click.Context(parent_cmd)
        child_cmd = click.Command("child")
        child_ctx = click.Context(child_cmd, parent=parent_ctx)

        # Execute
        setup_dependency_injection_context(child_ctx)

        # Verify
        metadata = child_ctx.obj["spec_di_metadata"]
        assert metadata["command"] == "child"
        assert metadata["parent_command"] == "parent"

    @patch("spec_cli.cli.context_integration.debug_logger")
    def test_setup_dependency_injection_context_when_successful_then_logs_debug_info(
        self, mock_logger
    ):
        """Test debug logging on successful setup."""
        # Setup
        cmd = click.Command("test_cmd")
        ctx = click.Context(cmd)

        # Execute
        setup_dependency_injection_context(ctx)

        # Verify
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == "DEBUG"
        assert "setup complete" in call_args[0][1]

    def test_setup_dependency_injection_context_when_invalid_context_then_raises_type_error(
        self,
    ):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            setup_dependency_injection_context(invalid_ctx)


class TestTeardownDependencyInjectionContext:
    """Test dependency injection context teardown functionality."""

    def test_teardown_dependency_injection_context_when_spec_data_exists_then_clears_data(
        self, mock_spec_context
    ):
        """Test teardown clears spec data."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {
            "spec_config": TEST_CONFIG,
            "spec_context": mock_spec_context,
            "other": "preserved",
        }

        # Execute
        teardown_dependency_injection_context(ctx)

        # Verify
        assert "spec_config" not in ctx.obj
        assert "spec_context" not in ctx.obj
        assert "other" in ctx.obj

    def test_teardown_dependency_injection_context_when_no_obj_then_handles_gracefully(
        self,
    ):
        """Test teardown when context obj is None."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = None

        # Execute (should not raise error)
        teardown_dependency_injection_context(ctx)

        # Verify no error occurs
        assert ctx.obj is None

    @patch("spec_cli.cli.context_integration.debug_logger")
    def test_teardown_dependency_injection_context_when_successful_then_logs_debug_info(
        self, mock_logger
    ):
        """Test debug logging on successful teardown."""
        # Setup
        cmd = click.Command("test_cmd")
        ctx = click.Context(cmd)

        # Execute
        teardown_dependency_injection_context(ctx)

        # Verify
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == "DEBUG"
        assert "teardown complete" in call_args[0][1]

    def test_teardown_dependency_injection_context_when_invalid_context_then_raises_type_error(
        self,
    ):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            teardown_dependency_injection_context(invalid_ctx)


class TestGetContextKeys:
    """Test context keys retrieval functionality."""

    def test_get_context_keys_when_spec_keys_exist_then_returns_unprefixed_keys(self, mock_spec_context):
        """Test getting spec-related context keys."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {
            "spec_config": TEST_CONFIG,
            "spec_context": mock_spec_context,
            "spec_metadata": {"info": "data"},
            "other": "not_spec",
        }

        # Execute
        keys = get_context_keys(ctx)

        # Verify
        assert set(keys) == {"config", "context", "metadata"}
        assert "other" not in keys

    def test_get_context_keys_when_no_spec_keys_then_returns_empty_list(self):
        """Test getting keys when no spec keys exist."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {"other": "data", "another": "value"}

        # Execute
        keys = get_context_keys(ctx)

        # Verify
        assert keys == []

    def test_get_context_keys_when_context_obj_none_then_returns_empty_list(self):
        """Test getting keys when context obj is None."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = None

        # Execute
        keys = get_context_keys(ctx)

        # Verify
        assert keys == []

    def test_get_context_keys_when_invalid_context_then_raises_type_error(self):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            get_context_keys(invalid_ctx)
