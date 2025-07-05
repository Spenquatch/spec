"""Command migration utilities for dependency injection transitions."""

import inspect
from collections.abc import Callable
from typing import Any, TypeVar

from ..exceptions import SpecError

F = TypeVar("F", bound=Callable[..., Any])


class MigrationError(SpecError):
    """Error raised during command migration operations."""

    def __init__(self, message: str, command_name: str | None = None) -> None:
        """Initialize migration error.

        Args:
            message: Error message describing the migration failure
            command_name: Optional command name for context
        """
        super().__init__(message)
        if command_name:
            self.add_context("command_name", command_name)


def migrate_command_signature(
    func: Callable[..., Any], context_param: str
) -> Callable[..., Any]:
    """Migrate command signature to accept context parameter.

    Args:
        func: Original function to migrate
        context_param: Name of the context parameter to add

    Returns:
        Function with migrated signature

    Raises:
        MigrationError: If migration fails
        TypeError: If func is not callable or context_param is invalid

    Example:
        >>> def original_cmd(debug: bool, verbose: bool) -> None:
        ...     pass
        >>> migrated = migrate_command_signature(original_cmd, "context")
        >>> # migrated now expects (context, debug, verbose)
    """
    if not callable(func):
        raise TypeError(f"Expected callable, got {type(func)}")

    if not isinstance(context_param, str) or not context_param.strip():
        raise TypeError("context_param must be a non-empty string")

    try:
        # Get original signature
        original_sig = inspect.signature(func)
        func_name = getattr(func, "__name__", "unknown")

        # Create new parameter for context injection
        context_parameter = inspect.Parameter(
            context_param,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation="SpecContext",
        )

        # Build new parameter list with context first
        new_params = [context_parameter]
        new_params.extend(original_sig.parameters.values())

        # Create new signature with context parameter
        new_signature = original_sig.replace(parameters=new_params)

        # Create wrapper function that accepts context parameter
        def migrated_function(*args: Any, **kwargs: Any) -> Any:
            # Extract context from first argument
            if not args:
                raise MigrationError(
                    "Context parameter required as first argument", func_name
                )

            # Skip context parameter when calling original function
            original_args = args[1:]
            return func(*original_args, **kwargs)

        # Apply new signature to wrapper
        migrated_function.__signature__ = new_signature  # type: ignore[attr-defined]
        migrated_function.__name__ = func_name
        migrated_function.__doc__ = func.__doc__
        migrated_function.__module__ = getattr(func, "__module__", func.__module__)

        # Preserve Click attributes if present
        for attr in ["__click_params__", "__click_group__", "__click_command__"]:
            if hasattr(func, attr):
                setattr(migrated_function, attr, getattr(func, attr))

        return migrated_function

    except Exception as e:
        raise MigrationError(
            f"Failed to migrate command signature: {e}", getattr(func, "__name__", None)
        ) from e


def validate_migration_behavior(
    original: Callable[..., Any], migrated: Callable[..., Any]
) -> bool:
    """Validate that migrated command maintains behavior compatibility.

    Args:
        original: Original function before migration
        migrated: Migrated function after migration

    Returns:
        True if migration preserves behavior compatibility

    Raises:
        MigrationError: If validation fails
        TypeError: If functions are not callable

    Example:
        >>> def original_cmd(debug: bool) -> str:
        ...     return "result"
        >>> migrated = migrate_command_signature(original_cmd, "ctx")
        >>> validate_migration_behavior(original_cmd, migrated)
        True
    """
    if not callable(original):
        raise TypeError(f"Expected callable original, got {type(original)}")

    if not callable(migrated):
        raise TypeError(f"Expected callable migrated, got {type(migrated)}")

    try:
        # Validate signatures
        original_sig = inspect.signature(original)
        migrated_sig = inspect.signature(migrated)

        # Migrated should have one additional parameter (context)
        original_param_count = len(original_sig.parameters)
        migrated_param_count = len(migrated_sig.parameters)

        if migrated_param_count != original_param_count + 1:
            raise MigrationError(
                f"Parameter count mismatch: original={original_param_count}, "
                f"migrated={migrated_param_count}, expected difference=1"
            )

        # Validate parameter names (excluding context parameter)
        original_params = list(original_sig.parameters.keys())
        migrated_params = list(migrated_sig.parameters.keys())[1:]  # Skip context

        if original_params != migrated_params:
            raise MigrationError(
                f"Parameter names mismatch: original={original_params}, "
                f"migrated={migrated_params}"
            )

        # Validate function attributes are preserved
        for attr in ["__doc__", "__module__"]:
            original_val = getattr(original, attr, None)
            migrated_val = getattr(migrated, attr, None)
            if original_val != migrated_val:
                raise MigrationError(
                    f"Attribute {attr} not preserved: "
                    f"original={original_val}, migrated={migrated_val}"
                )

        # Validate Click attributes are preserved
        for click_attr in ["__click_params__", "__click_group__", "__click_command__"]:
            if hasattr(original, click_attr):
                if not hasattr(migrated, click_attr):
                    raise MigrationError(f"Click attribute {click_attr} not preserved")

                original_val = getattr(original, click_attr)
                migrated_val = getattr(migrated, click_attr)
                if original_val != migrated_val:
                    raise MigrationError(
                        f"Click attribute {click_attr} value changed: "
                        f"original={original_val}, migrated={migrated_val}"
                    )

        return True

    except MigrationError:
        raise
    except Exception as e:
        raise MigrationError(f"Behavior validation failed: {e}") from e


def get_migration_requirements(func: Callable[..., Any]) -> dict[str, Any]:
    """Analyze function to determine migration requirements.

    Args:
        func: Function to analyze for migration

    Returns:
        Dictionary containing migration requirements and recommendations

    Raises:
        TypeError: If func is not callable

    Example:
        >>> def cmd(debug: bool, verbose: bool) -> None:
        ...     pass
        >>> reqs = get_migration_requirements(cmd)
        >>> print(reqs["parameter_count"])  # 2
        >>> print(reqs["has_click_decorators"])  # True/False
    """
    if not callable(func):
        raise TypeError(f"Expected callable, got {type(func)}")

    try:
        # Analyze function signature
        sig = inspect.signature(func)
        func_name = getattr(func, "__name__", "unknown")

        requirements = {
            "function_name": func_name,
            "parameter_count": len(sig.parameters),
            "parameters": list(sig.parameters.keys()),
            "has_click_decorators": any(
                hasattr(func, attr)
                for attr in ["__click_params__", "__click_group__", "__click_command__"]
            ),
            "has_docstring": bool(func.__doc__),
            "module": getattr(func, "__module__", None),
            "migration_complexity": "low",  # Default complexity
        }

        # Determine migration complexity
        param_count = len(sig.parameters)
        if param_count > 5:
            requirements["migration_complexity"] = "high"
        elif param_count > 2:
            requirements["migration_complexity"] = "medium"

        # Check for special parameter types
        has_special_params = any(
            param.kind
            in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD)
            for param in sig.parameters.values()
        )
        if has_special_params:
            requirements["migration_complexity"] = "high"
            requirements["has_var_args"] = True

        return requirements

    except Exception as e:
        raise MigrationError(f"Failed to analyze migration requirements: {e}") from e
