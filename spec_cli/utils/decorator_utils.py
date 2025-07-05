"""Decorator implementation utilities for context injection."""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, TypeVar

from ..exceptions import SpecError

F = TypeVar("F", bound=Callable[..., Any])


class DecoratorError(SpecError):
    """Error raised when decorator operations fail."""

    def __init__(self, message: str, func: Callable[..., Any] | None = None) -> None:
        """Initialize decorator error.

        Args:
            message: Error message describing the decorator failure
            func: Optional function that caused the error for context
        """
        super().__init__(message)
        if func is not None:
            self.add_context("function_name", getattr(func, "__name__", repr(func)))
            self.add_context("function_module", getattr(func, "__module__", None))
            # Try to get signature, but don't fail if inspect fails
            try:
                sig_str = str(inspect.signature(func)) if callable(func) else None
                self.add_context("function_signature", sig_str)
            except (ValueError, TypeError):
                self.add_context("function_signature", "Unable to inspect")


def create_context_injector(context_retriever: Callable[[], Any]) -> Callable[[F], F]:
    """Create context injection decorator with custom retrieval strategy.

    Args:
        context_retriever: Function that retrieves context data when called

    Returns:
        Decorator function that injects context into target functions

    Raises:
        DecoratorError: If context_retriever is not callable
        TypeError: If context_retriever is not a callable

    Example:
        >>> def get_context():
        ...     return {"config": "test"}
        >>> injector = create_context_injector(get_context)
        >>> @injector
        ... def my_func(ctx, name):
        ...     return f"{name}: {ctx}"
        >>> result = my_func("test")  # ctx automatically injected
    """
    if not callable(context_retriever):
        raise TypeError(f"context_retriever must be callable, got {type(context_retriever)}")

    def decorator(func: F) -> F:
        if not callable(func):
            raise DecoratorError("Can only decorate callable objects", func)

        # Analyze function signature for context parameter
        try:
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
        except (ValueError, TypeError) as e:
            raise DecoratorError(f"Cannot inspect function signature: {e}", func) from e

        # Check if function expects context parameter
        if not param_names:
            raise DecoratorError("Function must accept at least one parameter for context", func)

        # First parameter will be used for context injection

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                # Retrieve context using provided strategy
                context = context_retriever()

                # Inject context as first argument if not already provided
                if not args:
                    args = (context,)
                elif len(args) == len(param_names) - 1:
                    # Insert context as first argument
                    args = (context,) + args

                return func(*args, **kwargs)

            except Exception as e:
                if isinstance(e, DecoratorError):
                    raise
                raise DecoratorError(f"Context injection failed: {e}", func) from e

        return wrapper  # type: ignore[return-value]

    return decorator


def preserve_function_metadata(wrapper: Callable[..., Any], original: Callable[..., Any]) -> Callable[..., Any]:
    """Preserve function metadata for decorator compatibility.

    Args:
        wrapper: Wrapper function to enhance with metadata
        original: Original function to copy metadata from

    Returns:
        Wrapper function with preserved metadata

    Raises:
        DecoratorError: If metadata preservation fails
        TypeError: If wrapper or original are not callable

    Example:
        >>> def original_func():
        ...     '''Original docstring'''
        ...     pass
        >>> def wrapper_func():
        ...     pass
        >>> enhanced = preserve_function_metadata(wrapper_func, original_func)
        >>> print(enhanced.__doc__)  # 'Original docstring'
    """
    if not callable(wrapper):
        raise TypeError(f"wrapper must be callable, got {type(wrapper)}")
    if not callable(original):
        raise TypeError(f"original must be callable, got {type(original)}")

    try:
        # Apply functools.wraps behavior manually for explicit control
        wrapper.__name__ = getattr(original, "__name__", wrapper.__name__)
        wrapper.__doc__ = getattr(original, "__doc__", wrapper.__doc__)
        wrapper.__module__ = getattr(original, "__module__", wrapper.__module__)
        wrapper.__qualname__ = getattr(original, "__qualname__", wrapper.__qualname__)
        wrapper.__annotations__ = getattr(original, "__annotations__", {})

        # Preserve Click-specific attributes if they exist
        click_attrs = ["__click_params__", "__click_group__", "__click_command__", "callback", "name", "help"]
        for attr in click_attrs:
            if hasattr(original, attr):
                setattr(wrapper, attr, getattr(original, attr))

        return wrapper

    except Exception as e:
        raise DecoratorError(f"Failed to preserve function metadata: {e}", original) from e


def validate_decorator_target(func: Callable[..., Any]) -> bool:
    """Validate that function is suitable for context injection decoration.

    Args:
        func: Function to validate for decorator compatibility

    Returns:
        True if function is suitable for context injection

    Raises:
        DecoratorError: If function is not suitable for decoration
        TypeError: If func is not callable

    Example:
        >>> def valid_func(ctx, name):
        ...     return name
        >>> is_valid = validate_decorator_target(valid_func)
        >>> print(is_valid)  # True
    """
    if not callable(func):
        raise TypeError(f"Expected callable function, got {type(func)}")

    try:
        # Check function signature
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        if not params:
            raise DecoratorError("Function must accept at least one parameter for context", func)

        # Validate first parameter can accept context
        first_param = params[0]
        if first_param.kind == inspect.Parameter.VAR_KEYWORD:
            raise DecoratorError("First parameter cannot be **kwargs for context injection", func)

        # Check for conflicting decorators or attributes
        if hasattr(func, "__wrapped__"):
            # Function is already wrapped, validate chain compatibility
            if not hasattr(func, "__name__"):
                raise DecoratorError("Wrapped function missing __name__ attribute", func)

        return True

    except Exception as e:
        if isinstance(e, DecoratorError):
            raise
        raise DecoratorError(f"Function validation failed: {e}", func) from e

