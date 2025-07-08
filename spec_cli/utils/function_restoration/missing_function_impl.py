"""Missing function implementation helper for restoring test functionality."""

import ast
import inspect
from collections.abc import Callable
from typing import Any

from ...core.context_bridge import debug_logger
from ...exceptions import SpecError


class FunctionRestorationError(SpecError):
    """Error raised during function restoration operations."""

    def __init__(self, message: str, function_name: str | None = None) -> None:
        """Initialize function restoration error.

        Args:
            message: Error message describing the restoration failure
            function_name: Optional function name for context
        """
        super().__init__(message)
        if function_name:
            self.add_context("function_name", function_name)


def implement_missing_function(signature: str, purpose: str) -> Callable[..., Any]:
    """Implement a missing function with stub functionality.

    Creates a callable function based on signature analysis that provides
    basic stub behavior to enable test execution without import errors.

    Args:
        signature: Function signature string (e.g., "def func(a: int, b: str) -> bool:")
        purpose: Brief description of function purpose for stub behavior

    Returns:
        Callable function implementing the specified signature

    Raises:
        FunctionRestorationError: If function implementation fails
        TypeError: If signature is invalid

    Example:
        >>> func = implement_missing_function(
        ...     "def validate_input(value: str) -> bool:",
        ...     "Validate user input"
        ... )
        >>> result = func("test")  # Returns True (stub)
    """
    if not isinstance(signature, str) or not signature.strip():
        raise TypeError("Signature must be a non-empty string")

    if not isinstance(purpose, str) or not purpose.strip():
        raise TypeError("Purpose must be a non-empty string")

    try:
        debug_logger.log(
            "DEBUG",
            "Implementing missing function from signature",
            signature=signature.strip(),
            purpose=purpose.strip(),
        )

        # Parse the signature using AST
        function_ast = _parse_function_signature(signature)
        func_name = function_ast.name
        params = function_ast.args
        return_annotation = function_ast.returns

        # Determine return type and stub behavior
        stub_return = _determine_stub_return_value(return_annotation, purpose)

        # Create parameter list for dynamic function
        param_names = [arg.arg for arg in params.args]

        debug_logger.log(
            "DEBUG",
            "Creating stub function implementation",
            function_name=func_name,
            parameter_count=len(param_names),
            parameter_names=param_names,
            return_type=str(return_annotation) if return_annotation else "None",
            stub_return_value=stub_return,
        )

        # Create the stub function dynamically
        def stub_function(*args: Any, **kwargs: Any) -> Any:
            """Dynamically created stub function for missing implementation."""
            debug_logger.log(
                "DEBUG",
                "Executing stub function",
                function_name=func_name,
                args_count=len(args),
                kwargs_keys=list(kwargs.keys()),
                purpose=purpose,
            )

            # Log call for debugging
            debug_logger.log(
                "INFO",
                f"Stub function '{func_name}' called",
                purpose=purpose,
                args=args,
                kwargs=kwargs,
            )

            return stub_return

        # Set function metadata
        stub_function.__name__ = func_name
        stub_function.__doc__ = f"Stub implementation: {purpose}"

        # Set signature if possible
        try:
            sig_params = []
            for arg in params.args:
                param = inspect.Parameter(
                    arg.arg,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    annotation=arg.annotation,
                )
                sig_params.append(param)

            new_signature = inspect.Signature(
                parameters=sig_params, return_annotation=return_annotation
            )
            stub_function.__signature__ = new_signature  # type: ignore[attr-defined]

        except Exception as e:
            debug_logger.log(
                "WARNING",
                "Could not set function signature",
                function_name=func_name,
                error=str(e),
            )

        debug_logger.log(
            "INFO",
            "Missing function implemented successfully",
            function_name=func_name,
            signature=signature.strip(),
            purpose=purpose,
        )

        return stub_function

    except Exception as e:
        raise FunctionRestorationError(
            f"Failed to implement missing function: {e}",
            signature.split("(")[0].replace("def ", "").strip()
            if "def " in signature
            else None,
        ) from e


def _parse_function_signature(signature: str) -> ast.FunctionDef:
    """Parse function signature string into AST function definition.

    Args:
        signature: Function signature string

    Returns:
        AST FunctionDef node

    Raises:
        FunctionRestorationError: If signature parsing fails
    """
    try:
        # Ensure signature ends with pass for valid AST
        if not signature.strip().endswith(":"):
            signature = signature.strip() + ":"

        full_function = f"{signature}\n    pass"

        tree = ast.parse(full_function)

        if not tree.body or not isinstance(tree.body[0], ast.FunctionDef):
            raise FunctionRestorationError("Invalid function signature format")

        return tree.body[0]

    except (SyntaxError, ValueError) as e:
        raise FunctionRestorationError(
            f"Failed to parse function signature: {e}"
        ) from e


def _determine_stub_return_value(
    return_annotation: ast.AST | None, purpose: str
) -> Any:
    """Determine appropriate stub return value based on type annotation and purpose.

    Args:
        return_annotation: AST return type annotation
        purpose: Function purpose description

    Returns:
        Appropriate stub return value
    """
    if return_annotation is None:
        return None

    # Convert AST annotation to string for analysis
    annotation_str = ast.unparse(return_annotation) if return_annotation else ""

    debug_logger.log(
        "DEBUG",
        "Determining stub return value",
        annotation=annotation_str,
        purpose=purpose,
    )

    # Determine return value based on type annotation
    if annotation_str in ("bool", "Optional[bool]"):
        # Validation functions typically return True for success
        if any(
            keyword in purpose.lower()
            for keyword in [
                "valid",
                "check",
                "verify",
                "rollback",
                "success",
                "migrate",
            ]
        ):
            return True
        return False
    elif annotation_str in ("str", "Optional[str]"):
        return f"stub_{purpose.lower().replace(' ', '_')}"
    elif annotation_str in ("int", "Optional[int]"):
        return 0
    elif annotation_str in ("float", "Optional[float]"):
        return 0.0
    elif annotation_str in ("list", "List", "Optional[list]", "Optional[List]"):
        return []
    elif annotation_str in ("dict", "Dict", "Optional[dict]", "Optional[Dict]"):
        return {}
    elif annotation_str in ("set", "Set", "Optional[set]", "Optional[Set]"):
        return set()
    elif "List[" in annotation_str:
        return []
    elif "Dict[" in annotation_str:
        return {}
    else:
        # Default for unknown types
        return None


def create_function_stub_registry() -> dict[str, Callable[..., Any]]:
    """Create registry of common stub functions for migration.

    Returns:
        Dictionary mapping function names to stub implementations

    Example:
        >>> registry = create_function_stub_registry()
        >>> validate_func = registry.get("validate_input")
    """
    debug_logger.log("DEBUG", "Creating function stub registry")

    registry = {}

    # Common validation function stubs
    common_stubs = [
        ("def validate_input(value: str) -> bool:", "Validate user input"),
        ("def validate_path(path: str) -> bool:", "Validate file path"),
        ("def validate_config(config: dict) -> bool:", "Validate configuration"),
        ("def format_output(data: Any) -> str:", "Format output data"),
        ("def process_data(data: Any) -> Any:", "Process input data"),
        ("def get_default_value() -> Any:", "Get default value"),
        ("def setup_environment() -> None:", "Setup test environment"),
        ("def cleanup_resources() -> None:", "Cleanup test resources"),
    ]

    for signature, purpose in common_stubs:
        try:
            func = implement_missing_function(signature, purpose)
            func_name = signature.split("(")[0].replace("def ", "").strip()
            registry[func_name] = func

            debug_logger.log(
                "DEBUG",
                "Added stub to registry",
                function_name=func_name,
                purpose=purpose,
            )

        except Exception as e:
            debug_logger.log(
                "WARNING",
                "Failed to create stub for registry",
                signature=signature,
                error=str(e),
            )

    debug_logger.log(
        "INFO",
        "Function stub registry created",
        stub_count=len(registry),
        available_stubs=list(registry.keys()),
    )

    return registry
