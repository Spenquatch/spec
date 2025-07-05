"""Unit tests for CLI context injection decorators."""

from unittest.mock import Mock, patch

import click
import pytest

from spec_cli.cli.decorators import (
    ContextInjectionError,
    _get_spec_context_from_click,
    context_injection,
    inject_context,
    with_context,
)
from spec_cli.core.context import SpecContext
from spec_cli.utils.click_utils import ClickIntegrationError
from spec_cli.utils.decorator_utils import DecoratorError

# Test constants
TEST_CONTEXT_DATA = {"config": "test_value", "debug": True}
TEST_FUNCTION_NAME = "test_function"
TEST_COMMAND_NAME = "test_command"
EXPECTED_CONTEXT_PARAM = "ctx"


class TestContextInjectionDecorator:
    """Test context_injection decorator functionality."""

    @pytest.fixture
    def mock_spec_context(self):
        """Mock SpecContext instance for testing."""
        context = Mock(spec=SpecContext)
        context.config = TEST_CONTEXT_DATA
        return context

    @pytest.fixture
    def mock_click_context(self):
        """Mock Click context for testing."""
        click_ctx = Mock(spec=click.Context)
        click_ctx.command = Mock()
        click_ctx.command.name = TEST_COMMAND_NAME
        click_ctx.params = {"debug": True}
        click_ctx.obj = {"spec_spec_context": Mock(spec=SpecContext)}
        return click_ctx

    @pytest.fixture
    def sample_command_function(self):
        """Sample function for decorator testing."""

        def sample_command(ctx, name="default"):
            """Test command function."""
            return f"name: {name}, config: {getattr(ctx, 'config', {})}"

        sample_command.__name__ = TEST_FUNCTION_NAME
        return sample_command

    def test_context_decorator_when_valid_function_then_injects_context_parameter(
        self, sample_command_function, mock_spec_context
    ):
        """Test decorator injects context into valid function."""
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            decorated_func = context_injection(sample_command_function)

            # Call without context - should be injected automatically
            result = decorated_func("test_name")

            assert "test_name" in result
            assert str(TEST_CONTEXT_DATA) in result

    def test_context_decorator_when_missing_context_then_raises_decorator_error(
        self, sample_command_function
    ):
        """Test decorator raises error when context retrieval fails."""
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            side_effect=ContextInjectionError("Context not found"),
        ):
            decorated_func = context_injection(sample_command_function)

            with pytest.raises(ContextInjectionError, match="Context not found"):
                decorated_func("test_name")

    def test_context_decorator_when_preserves_metadata_then_maintains_function_attributes(
        self, sample_command_function
    ):
        """Test decorator preserves function metadata."""
        original_name = sample_command_function.__name__
        original_doc = sample_command_function.__doc__

        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=Mock(spec=SpecContext),
        ):
            decorated_func = context_injection(sample_command_function)

            assert decorated_func.__name__ == original_name
            assert decorated_func.__doc__ == original_doc

    def test_context_decorator_when_click_command_then_maintains_click_compatibility(
        self, mock_spec_context
    ):
        """Test decorator maintains Click command compatibility."""

        @click.command()
        def click_command(ctx, name):
            return f"click: {name}"

        # Add Click-specific attributes
        click_command.__click_params__ = []
        click_command.callback = click_command

        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            decorated_func = context_injection(click_command)

            # Check Click attributes are preserved
            assert hasattr(decorated_func, "__click_params__")
            assert hasattr(decorated_func, "callback")

    def test_context_decorator_when_multiple_decorators_then_preserves_decorator_chain(
        self, sample_command_function, mock_spec_context
    ):
        """Test decorator works in decorator chain."""

        def other_decorator(func):
            func.__other_decorator_applied__ = True
            return func

        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            # Apply multiple decorators
            decorated_func = context_injection(other_decorator(sample_command_function))

            # Both decorators should be applied
            assert hasattr(decorated_func, "__other_decorator_applied__")
            result = decorated_func("test")
            assert "test" in result

    def test_context_decorator_when_invalid_signature_then_raises_signature_error(self):
        """Test decorator raises error for invalid function signature."""

        def invalid_function():
            """Function with no parameters."""
            return "invalid"

        with pytest.raises(
            ContextInjectionError, match="Function must accept at least one parameter"
        ):
            context_injection(invalid_function)

    def test_context_decorator_when_context_retrieval_fails_then_raises_context_error(
        self, sample_command_function
    ):
        """Test decorator handles context retrieval failure."""
        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            side_effect=Exception("Retrieval failed"),
        ):
            decorated_func = context_injection(sample_command_function)

            with pytest.raises(DecoratorError, match="Context injection failed"):
                decorated_func("test")


class TestInjectContextParametricDecorator:
    """Test inject_context parametric decorator."""

    @pytest.fixture
    def mock_spec_context(self):
        """Mock SpecContext for testing."""
        return Mock(spec=SpecContext)

    def test_inject_context_when_custom_param_name_then_accepts_parameter(
        self, mock_spec_context
    ):
        """Test inject_context accepts custom parameter name."""

        def test_function(context, name):
            return f"context: {context}, name: {name}"

        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            decorator = inject_context("context")
            decorated_func = decorator(test_function)

            result = decorated_func("test_name")
            assert "test_name" in result

    def test_inject_context_when_empty_param_name_then_raises_error(self):
        """Test inject_context raises error for empty parameter name."""
        with pytest.raises(
            ContextInjectionError, match="context_param must be a non-empty string"
        ):
            inject_context("")

    def test_inject_context_when_invalid_param_type_then_raises_error(self):
        """Test inject_context raises error for invalid parameter type."""
        with pytest.raises(
            ContextInjectionError, match="context_param must be a non-empty string"
        ):
            inject_context(123)  # type: ignore

    def test_inject_context_when_decoration_fails_then_raises_context_error(self):
        """Test inject_context handles decoration failure."""

        def invalid_function():
            return "invalid"

        decorator = inject_context(EXPECTED_CONTEXT_PARAM)

        with pytest.raises(ContextInjectionError):
            decorator(invalid_function)


class TestWithContextAlias:
    """Test with_context decorator alias."""

    @pytest.fixture
    def mock_spec_context(self):
        """Mock SpecContext for testing."""
        return Mock(spec=SpecContext)

    def test_with_context_when_valid_function_then_applies_context_injection(
        self, mock_spec_context
    ):
        """Test with_context alias works like context_injection."""

        def test_function(ctx, name):
            return f"ctx: {ctx}, name: {name}"

        with patch(
            "spec_cli.cli.decorators._get_spec_context_from_click",
            return_value=mock_spec_context,
        ):
            decorated_func = with_context(test_function)

            result = decorated_func("test_name")
            assert "test_name" in result

    def test_with_context_when_invalid_function_then_raises_error(self):
        """Test with_context raises error for invalid function."""

        def invalid_function():
            return "invalid"

        with pytest.raises(ContextInjectionError):
            with_context(invalid_function)


class TestGetSpecContextFromClick:
    """Test _get_spec_context_from_click helper function."""

    def test_get_context_when_valid_click_context_then_returns_spec_context(self):
        """Test context retrieval from valid Click context."""
        mock_spec_context = Mock(spec=SpecContext)
        mock_click_ctx = Mock(spec=click.Context)

        with (
            patch("click.get_current_context", return_value=mock_click_ctx),
            patch(
                "spec_cli.cli.decorators.retrieve_context_data",
                return_value=mock_spec_context,
            ),
        ):
            result = _get_spec_context_from_click()

            assert result is mock_spec_context

    def test_get_context_when_no_click_context_then_raises_error(self):
        """Test error when no Click context available."""
        with patch("click.get_current_context", return_value=None):
            with pytest.raises(
                ContextInjectionError, match="No active Click context found"
            ):
                _get_spec_context_from_click()

    def test_get_context_when_no_spec_context_then_creates_default(self):
        """Test default context creation when none found."""
        mock_click_ctx = Mock(spec=click.Context)

        with (
            patch("click.get_current_context", return_value=mock_click_ctx),
            patch("spec_cli.cli.decorators.retrieve_context_data", return_value=None),
        ):
            # Should create a default SpecContext
            result = _get_spec_context_from_click()

            # Should be a SpecContext instance
            from spec_cli.core.context import SpecContext

            assert isinstance(result, SpecContext)

    def test_get_context_when_invalid_context_type_then_raises_error(self):
        """Test error when retrieved context is wrong type."""
        mock_click_ctx = Mock(spec=click.Context)
        invalid_context = "not_a_context"

        with (
            patch("click.get_current_context", return_value=mock_click_ctx),
            patch(
                "spec_cli.cli.decorators.retrieve_context_data",
                return_value=invalid_context,
            ),
        ):
            with pytest.raises(ContextInjectionError, match="Invalid context type"):
                _get_spec_context_from_click()

    def test_get_context_when_click_integration_error_then_raises_context_error(self):
        """Test handling of Click integration errors."""
        mock_click_ctx = Mock(spec=click.Context)

        with (
            patch("click.get_current_context", return_value=mock_click_ctx),
            patch(
                "spec_cli.cli.decorators.retrieve_context_data",
                side_effect=ClickIntegrationError("Integration failed"),
            ),
        ):
            with pytest.raises(ContextInjectionError, match="Click integration failed"):
                _get_spec_context_from_click()

    def test_get_context_when_unexpected_error_then_raises_context_error(self):
        """Test handling of unexpected errors."""
        with patch(
            "click.get_current_context", side_effect=RuntimeError("Unexpected error")
        ):
            with pytest.raises(ContextInjectionError, match="Context retrieval failed"):
                _get_spec_context_from_click()


class TestContextInjectionError:
    """Test ContextInjectionError exception class."""

    def test_context_injection_error_when_click_context_provided_then_adds_context(
        self,
    ):
        """Test error adds Click context information."""
        mock_click_ctx = Mock(spec=click.Context)
        mock_click_ctx.command = Mock()
        mock_click_ctx.command.name = TEST_COMMAND_NAME
        mock_click_ctx.params = {"debug": True}

        error = ContextInjectionError("Test error", mock_click_ctx)

        assert error.context["click_command"] == TEST_COMMAND_NAME
        assert error.context["click_params"] == {"debug": True}

    def test_context_injection_error_when_no_click_context_then_basic_error(self):
        """Test error without Click context."""
        error = ContextInjectionError("Test error")

        assert str(error) == "Test error"
        assert "click_command" not in error.context
