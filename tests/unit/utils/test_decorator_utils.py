"""Unit tests for decorator utilities."""

from unittest.mock import Mock, patch

import pytest

from spec_cli.utils.decorator_utils import (
    DecoratorError,
    create_context_injector,
    preserve_function_metadata,
    validate_decorator_target,
)

# Test constants
TEST_CONTEXT_DATA = {"config": "test_value", "debug": True}
TEST_FUNCTION_NAME = "test_function"
TEST_DOCSTRING = "Test function docstring"
MOCK_QUALNAME = "module.test_function"
MOCK_MODULE = "test_module"


class TestCreateContextInjector:
    """Test create_context_injector function."""

    @pytest.fixture
    def mock_context_retriever(self):
        """Mock context retriever function."""
        return Mock(return_value=TEST_CONTEXT_DATA)

    @pytest.fixture
    def sample_function(self):
        """Sample function for testing."""

        def test_function(ctx, name="default"):
            """Test function."""
            return f"ctx: {ctx}, name: {name}"

        test_function.__name__ = TEST_FUNCTION_NAME
        return test_function

    def test_create_context_injector_when_valid_retriever_then_returns_decorator(
        self, mock_context_retriever
    ):
        """Test create_context_injector returns working decorator."""
        injector = create_context_injector(mock_context_retriever)

        assert callable(injector)

    def test_create_context_injector_when_invalid_retriever_then_raises_type_error(
        self,
    ):
        """Test create_context_injector raises TypeError for non-callable."""
        with pytest.raises(TypeError, match="context_retriever must be callable"):
            create_context_injector("not_callable")  # type: ignore

    def test_context_injector_when_applied_to_function_then_injects_context(
        self, mock_context_retriever, sample_function
    ):
        """Test context injector injects context into function."""
        injector = create_context_injector(mock_context_retriever)
        decorated_func = injector(sample_function)

        # Call without context - should be injected
        result = decorated_func("test_name")

        assert "test_name" in result
        assert str(TEST_CONTEXT_DATA) in result
        mock_context_retriever.assert_called_once()

    def test_context_injector_when_context_already_provided_then_uses_provided_context(
        self, mock_context_retriever, sample_function
    ):
        """Test context injector handles pre-provided context."""
        injector = create_context_injector(mock_context_retriever)
        decorated_func = injector(sample_function)

        custom_context = {"custom": "context"}

        # Call with context provided
        result = decorated_func(custom_context, "test_name")

        assert "test_name" in result
        assert "custom" in result

    def test_context_injector_when_non_callable_function_then_raises_decorator_error(
        self, mock_context_retriever
    ):
        """Test context injector raises error for non-callable."""
        injector = create_context_injector(mock_context_retriever)

        with pytest.raises(DecoratorError, match="Can only decorate callable objects"):
            injector("not_callable")  # type: ignore

    def test_context_injector_when_function_no_params_then_raises_decorator_error(
        self, mock_context_retriever
    ):
        """Test context injector raises error for parameterless function."""
        injector = create_context_injector(mock_context_retriever)

        def no_params_function():
            return "no params"

        with pytest.raises(
            DecoratorError, match="Function must accept at least one parameter"
        ):
            injector(no_params_function)

    def test_context_injector_when_signature_inspection_fails_then_raises_decorator_error(
        self, mock_context_retriever
    ):
        """Test context injector handles signature inspection failure."""
        injector = create_context_injector(mock_context_retriever)

        # Create a mock function that fails signature inspection
        mock_func = Mock()
        mock_func.__name__ = "mock_func"

        with patch("inspect.signature", side_effect=ValueError("Cannot inspect")):
            with pytest.raises(
                DecoratorError, match="Cannot inspect function signature"
            ):
                injector(mock_func)

    def test_context_injector_when_retriever_fails_then_raises_decorator_error(
        self, sample_function
    ):
        """Test context injector handles retriever failure."""
        failing_retriever = Mock(side_effect=RuntimeError("Retrieval failed"))
        injector = create_context_injector(failing_retriever)
        decorated_func = injector(sample_function)

        with pytest.raises(DecoratorError, match="Context injection failed"):
            decorated_func("test")

    def test_context_injector_when_proper_arg_count_then_inserts_context(
        self, mock_context_retriever
    ):
        """Test context injector inserts context when argument count matches."""

        def two_param_function(ctx, name):
            return f"ctx: {ctx}, name: {name}"

        injector = create_context_injector(mock_context_retriever)
        decorated_func = injector(two_param_function)

        # Call with one argument (expecting context insertion)
        result = decorated_func("test_name")

        assert "test_name" in result
        assert str(TEST_CONTEXT_DATA) in result


class TestPreserveFunctionMetadata:
    """Test preserve_function_metadata function."""

    @pytest.fixture
    def original_function(self):
        """Original function with metadata."""

        def original_function(x, y):
            """Original function docstring."""
            return x + y

        original_function.__name__ = TEST_FUNCTION_NAME
        original_function.__doc__ = TEST_DOCSTRING
        original_function.__module__ = MOCK_MODULE
        original_function.__qualname__ = MOCK_QUALNAME
        original_function.__annotations__ = {"x": int, "y": int, "return": int}
        original_function.__click_params__ = ["param1", "param2"]
        original_function.callback = original_function
        original_function.name = "cli_name"
        original_function.help = "CLI help text"

        return original_function

    @pytest.fixture
    def wrapper_function(self):
        """Wrapper function for testing."""

        def wrapper_function(*args, **kwargs):
            """Wrapper function."""
            return "wrapped"

        return wrapper_function

    def test_preserve_function_metadata_when_valid_functions_then_copies_attributes(
        self, wrapper_function, original_function
    ):
        """Test preserve_function_metadata copies all attributes."""
        enhanced = preserve_function_metadata(wrapper_function, original_function)

        assert enhanced.__name__ == TEST_FUNCTION_NAME
        assert enhanced.__doc__ == TEST_DOCSTRING
        assert enhanced.__module__ == MOCK_MODULE
        assert enhanced.__qualname__ == MOCK_QUALNAME
        assert enhanced.__annotations__ == {"x": int, "y": int, "return": int}

    def test_preserve_function_metadata_when_click_attributes_then_preserves_click_attrs(
        self, wrapper_function, original_function
    ):
        """Test preserve_function_metadata preserves Click-specific attributes."""
        enhanced = preserve_function_metadata(wrapper_function, original_function)

        assert hasattr(enhanced, "__click_params__")
        assert enhanced.__click_params__ == ["param1", "param2"]
        assert enhanced.callback is original_function
        assert enhanced.name == "cli_name"
        assert enhanced.help == "CLI help text"

    def test_preserve_function_metadata_when_missing_attributes_then_handles_gracefully(
        self, wrapper_function
    ):
        """Test preserve_function_metadata handles missing attributes."""

        def minimal_function():
            pass

        enhanced = preserve_function_metadata(wrapper_function, minimal_function)

        # Should preserve what exists
        assert enhanced.__name__ == minimal_function.__name__

    def test_preserve_function_metadata_when_non_callable_wrapper_then_raises_type_error(
        self, original_function
    ):
        """Test preserve_function_metadata raises TypeError for non-callable wrapper."""
        with pytest.raises(TypeError, match="wrapper must be callable"):
            preserve_function_metadata("not_callable", original_function)  # type: ignore

    def test_preserve_function_metadata_when_non_callable_original_then_raises_type_error(
        self, wrapper_function
    ):
        """Test preserve_function_metadata raises TypeError for non-callable original."""
        with pytest.raises(TypeError, match="original must be callable"):
            preserve_function_metadata(wrapper_function, "not_callable")  # type: ignore

    def test_preserve_function_metadata_when_attribute_error_then_raises_decorator_error(
        self, wrapper_function, original_function
    ):
        """Test preserve_function_metadata handles attribute setting errors."""

        # Create a wrapper that can't have attributes set
        class ReadOnlyWrapper:
            def __call__(self):
                pass

            def __setattr__(self, name, value):
                raise AttributeError("Cannot set attributes")

        readonly_wrapper = ReadOnlyWrapper()

        with pytest.raises(
            DecoratorError, match="Failed to preserve function metadata"
        ):
            preserve_function_metadata(readonly_wrapper, original_function)


class TestValidateDecoratorTarget:
    """Test validate_decorator_target function."""

    def test_validate_decorator_target_when_valid_function_then_returns_true(self):
        """Test validate_decorator_target returns True for valid function."""

        def valid_function(ctx, name):
            return f"ctx: {ctx}, name: {name}"

        result = validate_decorator_target(valid_function)

        assert result is True

    def test_validate_decorator_target_when_non_callable_then_raises_type_error(self):
        """Test validate_decorator_target raises TypeError for non-callable."""
        with pytest.raises(TypeError, match="Expected callable function"):
            validate_decorator_target("not_callable")  # type: ignore

    def test_validate_decorator_target_when_no_parameters_then_raises_decorator_error(
        self,
    ):
        """Test validate_decorator_target raises error for parameterless function."""

        def no_params():
            return "no params"

        with pytest.raises(
            DecoratorError, match="Function must accept at least one parameter"
        ):
            validate_decorator_target(no_params)

    def test_validate_decorator_target_when_var_keyword_first_param_then_raises_decorator_error(
        self,
    ):
        """Test validate_decorator_target raises error for **kwargs as first param."""

        def invalid_function(**kwargs):
            return "invalid"

        with pytest.raises(
            DecoratorError, match="First parameter cannot be \\*\\*kwargs"
        ):
            validate_decorator_target(invalid_function)

    def test_validate_decorator_target_when_wrapped_function_then_validates_chain(self):
        """Test validate_decorator_target handles wrapped functions."""

        def original_function(ctx, name):
            return f"ctx: {ctx}, name: {name}"

        def wrapper(*args, **kwargs):
            return original_function(*args, **kwargs)

        wrapper.__wrapped__ = original_function
        wrapper.__name__ = "wrapper"

        result = validate_decorator_target(wrapper)

        assert result is True

    def test_validate_decorator_target_when_wrapped_missing_name_then_raises_decorator_error(
        self,
    ):
        """Test validate_decorator_target raises error for wrapped function missing __name__."""

        # Create a mock object that has __wrapped__ but no __name__
        class NamelessWrapper:
            def __call__(self, *args, **kwargs):
                return "wrapped"

            def __init__(self):
                self.__wrapped__ = lambda ctx, name: f"ctx: {ctx}, name: {name}"
                # Intentionally no __name__ attribute

        nameless_wrapper = NamelessWrapper()

        with pytest.raises(
            DecoratorError, match="Wrapped function missing __name__ attribute"
        ):
            validate_decorator_target(nameless_wrapper)

    def test_validate_decorator_target_when_signature_error_then_raises_decorator_error(
        self,
    ):
        """Test validate_decorator_target handles signature inspection errors."""
        mock_func = Mock()
        mock_func.__name__ = "mock_func"

        with patch("inspect.signature", side_effect=ValueError("Cannot inspect")):
            with pytest.raises(DecoratorError, match="Function validation failed"):
                validate_decorator_target(mock_func)


class TestDecoratorError:
    """Test DecoratorError exception class."""

    def test_decorator_error_when_function_provided_then_adds_context(self):
        """Test DecoratorError adds function context information."""

        def test_function(x, y):
            return x + y

        test_function.__name__ = TEST_FUNCTION_NAME
        test_function.__module__ = MOCK_MODULE

        error = DecoratorError("Test error", test_function)

        assert error.context["function_name"] == TEST_FUNCTION_NAME
        assert error.context["function_module"] == MOCK_MODULE
        assert "function_signature" in error.context

    def test_decorator_error_when_no_function_then_basic_error(self):
        """Test DecoratorError without function context."""
        error = DecoratorError("Test error")

        assert str(error) == "Test error"
        assert "function_name" not in error.context

    def test_decorator_error_when_non_callable_function_then_handles_gracefully(self):
        """Test DecoratorError handles non-callable function object."""
        non_callable = "not_a_function"

        error = DecoratorError("Test error", non_callable)  # type: ignore

        # Should not crash, just use repr
        assert "function_name" in error.context
        assert error.context["function_name"] == repr(non_callable)
