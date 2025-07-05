"""Decorator pattern analysis utilities for function signature inspection."""

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class SignatureReport:
    """Report containing function signature analysis results.

    Attributes:
        function_name: Name of the analyzed function
        parameters: Dictionary of parameter names to parameter info
        return_annotation: Return type annotation if present
        has_click_context: Whether function has Click context parameter
        is_compatible: Whether function is compatible with decorators
        error_message: Error message if analysis failed
    """

    function_name: str
    parameters: dict[str, dict[str, Any]]
    return_annotation: str | None
    has_click_context: bool
    is_compatible: bool
    error_message: str | None = None


class DecoratorAnalysisError(Exception):
    """Exception raised when decorator analysis fails."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize decorator analysis error.

        Args:
            message: Error description
            context: Additional context information
        """
        super().__init__(message)
        self.context = context or {}


def analyze_function_signature(func: Callable[..., Any]) -> SignatureReport:
    """Analyze function signature for decorator compatibility.

    Args:
        func: Function to analyze

    Returns:
        SignatureReport containing analysis results

    Raises:
        DecoratorAnalysisError: If function analysis fails

    Example:
        >>> def example_func(ctx, name: str) -> str:
        ...     return f"Hello {name}"
        >>> report = analyze_function_signature(example_func)
        >>> assert report.function_name == "example_func"
        >>> assert "name" in report.parameters
    """
    if not callable(func):
        raise DecoratorAnalysisError(f"Expected callable function, got {type(func)}")

    try:
        sig = inspect.signature(func)
        function_name = getattr(func, "__name__", repr(func))

        # Analyze parameters
        parameters = {}
        has_click_context = False

        for param_name, param in sig.parameters.items():
            param_info = {
                "annotation": str(param.annotation)
                if param.annotation != inspect.Parameter.empty
                else None,
                "default": param.default
                if param.default != inspect.Parameter.empty
                else None,
                "kind": param.kind.name,
            }
            parameters[param_name] = param_info

            # Check for Click context patterns
            if param_name in ("ctx", "context") or "context" in param_name.lower():
                has_click_context = True

        # Check return annotation
        return_annotation = None
        if sig.return_annotation != inspect.Signature.empty:
            return_annotation = str(sig.return_annotation)

        # Determine compatibility - functions with reasonable parameter counts are compatible
        is_compatible = len(parameters) <= 5  # McCabe complexity consideration

        return SignatureReport(
            function_name=function_name,
            parameters=parameters,
            return_annotation=return_annotation,
            has_click_context=has_click_context,
            is_compatible=is_compatible,
        )

    except Exception as e:
        error_context = {"function": repr(func), "error_type": type(e).__name__}
        raise DecoratorAnalysisError(
            f"Failed to analyze function signature: {e}", context=error_context
        ) from e


def _is_overly_generic_signature(parameters: dict[str, dict[str, Any]]) -> bool:
    """Check if function signature is overly generic (only *args/**kwargs)."""
    if not parameters:
        return False

    for param_info in parameters.values():
        if param_info["kind"] not in ("VAR_POSITIONAL", "VAR_KEYWORD"):
            return False

    return True


def validate_decorator_compatibility(func: Callable[..., Any]) -> bool:
    """Validate if function is compatible with decorator patterns.

    Args:
        func: Function to validate

    Returns:
        True if function is decorator-compatible, False otherwise

    Raises:
        DecoratorAnalysisError: If validation process fails

    Example:
        >>> def compatible_func(name: str) -> str:
        ...     return f"Hello {name}"
        >>> assert validate_decorator_compatibility(compatible_func) is True
        >>>
        >>> def incompatible_func(*args, **kwargs):
        ...     pass  # Too generic
        >>> assert validate_decorator_compatibility(incompatible_func) is False
    """
    try:
        report = analyze_function_signature(func)

        if not report.is_compatible:
            return False

        if _is_overly_generic_signature(report.parameters):
            return False

        return True

    except DecoratorAnalysisError:
        return False
    except Exception:
        return False
