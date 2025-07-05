"""Unit tests for Click context utilities."""

import click
import pytest

from spec_cli.utils.click_utils import (
    ClickIntegrationError,
    clear_context_data,
    retrieve_context_data,
    store_context_data,
    validate_click_context,
)

# Test constants
TEST_KEY = "test_key"
TEST_DATA = {"test": "data", "debug": True}
DEFAULT_VALUE = "default"
PREFIXED_KEY = f"spec_{TEST_KEY}"


class TestStoreContextData:
    """Test context data storage functionality."""

    def test_store_context_data_when_valid_click_context_then_stores_data_successfully(
        self,
    ):
        """Test context data storage in Click context object."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Execute
        store_context_data(ctx, TEST_KEY, TEST_DATA)

        # Verify
        assert ctx.obj is not None
        assert PREFIXED_KEY in ctx.obj
        assert ctx.obj[PREFIXED_KEY] == TEST_DATA

    def test_store_context_data_when_context_obj_none_then_initializes_obj(self):
        """Test context obj initialization when None."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = None

        # Execute
        store_context_data(ctx, TEST_KEY, TEST_DATA)

        # Verify
        assert ctx.obj is not None
        assert isinstance(ctx.obj, dict)
        assert ctx.obj[PREFIXED_KEY] == TEST_DATA

    def test_store_context_data_when_invalid_context_then_raises_type_error(self):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            store_context_data(invalid_ctx, TEST_KEY, TEST_DATA)

    def test_store_context_data_when_empty_key_then_raises_integration_error(self):
        """Test error handling for empty context key."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="non-empty string"):
            store_context_data(ctx, "", TEST_DATA)

        with pytest.raises(ClickIntegrationError, match="non-empty string"):
            store_context_data(ctx, "   ", TEST_DATA)

    def test_store_context_data_when_key_collision_same_data_then_allows_storage(self):
        """Test key collision handling with same data."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        store_context_data(ctx, TEST_KEY, TEST_DATA)

        # Execute (store same data again)
        store_context_data(ctx, TEST_KEY, TEST_DATA)

        # Verify no error and data preserved
        assert ctx.obj[PREFIXED_KEY] == TEST_DATA

    def test_store_context_data_when_key_collision_different_data_then_raises_error(
        self,
    ):
        """Test key collision prevention with different data."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        store_context_data(ctx, TEST_KEY, TEST_DATA)
        different_data = {"different": "data"}

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="collision detected"):
            store_context_data(ctx, TEST_KEY, different_data)


class TestRetrieveContextData:
    """Test context data retrieval functionality."""

    def test_retrieve_context_data_when_data_exists_then_returns_stored_data(self):
        """Test context data retrieval from Click context object."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {PREFIXED_KEY: TEST_DATA}

        # Execute
        result = retrieve_context_data(ctx, TEST_KEY)

        # Verify
        assert result == TEST_DATA

    def test_retrieve_context_data_when_data_missing_then_returns_none_or_default(self):
        """Test context data retrieval when key doesn't exist."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {}

        # Execute & Verify - returns None by default
        result = retrieve_context_data(ctx, TEST_KEY)
        assert result is None

        # Execute & Verify - returns provided default
        result = retrieve_context_data(ctx, TEST_KEY, DEFAULT_VALUE)
        assert result == DEFAULT_VALUE

    def test_retrieve_context_data_when_context_obj_none_then_returns_default(self):
        """Test retrieval when context obj is None."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = None

        # Execute & Verify
        result = retrieve_context_data(ctx, TEST_KEY, DEFAULT_VALUE)
        assert result == DEFAULT_VALUE

    def test_retrieve_context_data_when_invalid_context_then_raises_type_error(self):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            retrieve_context_data(invalid_ctx, TEST_KEY)

    def test_retrieve_context_data_when_empty_key_then_raises_integration_error(self):
        """Test error handling for empty context key."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="non-empty string"):
            retrieve_context_data(ctx, "")

        with pytest.raises(ClickIntegrationError, match="non-empty string"):
            retrieve_context_data(ctx, "   ")


class TestValidateClickContext:
    """Test Click context validation functionality."""

    def test_validate_click_context_when_valid_context_then_returns_true(self):
        """Test validation of valid Click context."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Execute
        result = validate_click_context(ctx)

        # Verify
        assert result is True

    def test_validate_click_context_when_context_with_dict_obj_then_validates_successfully(
        self,
    ):
        """Test validation with dict-like obj."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {"existing": "data"}

        # Execute
        result = validate_click_context(ctx)

        # Verify
        assert result is True

    def test_validate_click_context_when_context_with_none_obj_then_validates_successfully(
        self,
    ):
        """Test validation with None obj."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = None

        # Execute
        result = validate_click_context(ctx)

        # Verify
        assert result is True

    def test_validate_click_context_when_invalid_context_then_raises_type_error(self):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            validate_click_context(invalid_ctx)

    def test_validate_click_context_when_context_missing_info_then_raises_integration_error(
        self,
    ):
        """Test validation failure for context missing info."""

        # Setup - create minimal context-like object without info
        class MockContext:
            def __init__(self):
                self.params = {}
                self.obj = None

        mock_ctx = MockContext()

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            validate_click_context(mock_ctx)

    def test_validate_click_context_when_non_dict_obj_then_raises_integration_error(
        self,
    ):
        """Test validation failure for non-dict-like obj."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = "not_dict_like"  # String doesn't have __getitem__

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="dict-like"):
            validate_click_context(ctx)


class TestClearContextData:
    """Test context data clearing functionality."""

    def test_clear_context_data_when_specific_key_then_clears_only_that_key(self):
        """Test clearing specific context key."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {
            PREFIXED_KEY: TEST_DATA,
            "spec_other": "other_data",
            "non_spec": "preserved",
        }

        # Execute
        clear_context_data(ctx, TEST_KEY)

        # Verify
        assert PREFIXED_KEY not in ctx.obj
        assert "spec_other" in ctx.obj
        assert "non_spec" in ctx.obj

    def test_clear_context_data_when_no_key_specified_then_clears_all_spec_data(self):
        """Test clearing all spec-prefixed data."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {
            "spec_data1": "data1",
            "spec_data2": "data2",
            "non_spec": "preserved",
        }

        # Execute
        clear_context_data(ctx)

        # Verify
        assert "spec_data1" not in ctx.obj
        assert "spec_data2" not in ctx.obj
        assert "non_spec" in ctx.obj

    def test_clear_context_data_when_context_obj_none_then_handles_gracefully(self):
        """Test clearing when context obj is None."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = None

        # Execute (should not raise error)
        clear_context_data(ctx)

        # Verify no error occurs
        assert ctx.obj is None

    def test_clear_context_data_when_key_not_exists_then_handles_gracefully(self):
        """Test clearing non-existent key."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {"other": "data"}

        # Execute (should not raise error)
        clear_context_data(ctx, "non_existent")

        # Verify
        assert ctx.obj["other"] == "data"

    def test_clear_context_data_when_invalid_context_then_raises_type_error(self):
        """Test type error for invalid Click context."""
        # Setup
        invalid_ctx = "not_a_context"

        # Execute & Verify
        with pytest.raises(TypeError, match="Expected click.Context"):
            clear_context_data(invalid_ctx)

    def test_clear_context_data_when_empty_key_then_raises_integration_error(self):
        """Test error handling for empty context key."""
        # Setup
        cmd = click.Command("test")
        ctx = click.Context(cmd)
        ctx.obj = {"test": "data"}  # Ensure obj is not None for validation to occur

        # Execute & Verify
        with pytest.raises(ClickIntegrationError, match="non-empty string"):
            clear_context_data(ctx, "")

        with pytest.raises(ClickIntegrationError, match="non-empty string"):
            clear_context_data(ctx, "   ")


class TestClickIntegrationError:
    """Test ClickIntegrationError exception functionality."""

    def test_click_integration_error_when_basic_message_then_creates_error(self):
        """Test basic ClickIntegrationError creation."""
        # Setup
        message = "Integration failed"

        # Execute
        error = ClickIntegrationError(message)

        # Verify
        assert str(error) == message
        assert isinstance(error, ClickIntegrationError)

    def test_click_integration_error_when_with_click_context_then_adds_context(self):
        """Test ClickIntegrationError with Click context information."""
        # Setup
        cmd = click.Command("test_command")
        ctx = click.Context(cmd)
        ctx.params = {"param1": "value1"}
        message = "Integration failed"

        # Execute
        error = ClickIntegrationError(message, ctx)

        # Verify
        assert str(error) == message
        assert error.context["click_info_name"] == "test_command"
        assert error.context["click_params"] == {"param1": "value1"}
        assert error.context["click_parent"] is None

    def test_click_integration_error_when_with_parent_context_then_includes_parent(
        self,
    ):
        """Test ClickIntegrationError with parent context information."""
        # Setup
        parent_cmd = click.Command("parent")
        parent_ctx = click.Context(parent_cmd)
        child_cmd = click.Command("child")
        child_ctx = click.Context(child_cmd, parent=parent_ctx)
        message = "Child integration failed"

        # Execute
        error = ClickIntegrationError(message, child_ctx)

        # Verify
        assert error.context["click_info_name"] == "child"
        assert error.context["click_parent"] == "parent"
