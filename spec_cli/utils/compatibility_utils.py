"""Compatibility utilities for bridging singleton and dependency injection patterns.

This module provides utility functions for creating compatibility wrappers that
enable transparent access to singleton instances while supporting migration to
context-based dependency injection.
"""

import re
import threading
from typing import Any

from ..core.context_bridge import debug_logger
from ..exceptions import CompatibilityError


def create_singleton_wrapper(
    singleton_class: type[Any],
    fallback_enabled: bool = True,
    context_key: str | None = None,
) -> Any:
    """Create a compatibility wrapper for singleton class with DI support.

    Args:
        singleton_class: The singleton class to wrap
        fallback_enabled: Whether to fall back to singleton when context unavailable
        context_key: Optional key for DI container registration

    Returns:
        Wrapper instance that provides transparent access

    Raises:
        CompatibilityError: If wrapper creation fails
        TypeError: If singleton_class is not a valid class

    Example:
        >>> from spec_cli.ui.progress_manager import ProgressManagerSingleton
        >>> wrapper = create_singleton_wrapper(ProgressManagerSingleton)
        >>> manager = wrapper.get_progress_manager()
    """
    if not isinstance(singleton_class, type):
        raise TypeError(f"Expected class type, got {type(singleton_class)}")

    debug_logger.log(
        "INFO",
        "Creating singleton wrapper",
        singleton_class=singleton_class.__name__,
        fallback_enabled=fallback_enabled,
        context_key=context_key,
    )

    try:
        wrapper = SingletonCompatibilityWrapper(
            singleton_class=singleton_class,
            fallback_enabled=fallback_enabled,
            context_key=context_key or _get_default_context_key(singleton_class),
        )

        debug_logger.log(
            "INFO",
            "Singleton wrapper created successfully",
            singleton_class=singleton_class.__name__,
        )

        return wrapper

    except Exception as e:
        debug_logger.log(
            "ERROR",
            "Failed to create singleton wrapper",
            singleton_class=singleton_class.__name__,
            error=str(e),
        )
        raise CompatibilityError(
            f"Failed to create wrapper for {singleton_class.__name__}: {e}"
        ) from e


def validate_wrapper_behavior(wrapper: Any, original: Any) -> bool:
    """Validate that wrapper behavior matches original singleton behavior.

    Args:
        wrapper: The compatibility wrapper instance
        original: The original singleton instance

    Returns:
        True if behavior matches, False otherwise

    Raises:
        TypeError: If wrapper or original are invalid types

    Example:
        >>> wrapper = create_singleton_wrapper(ProgressManagerSingleton)
        >>> original = ProgressManagerSingleton()
        >>> is_valid = validate_wrapper_behavior(wrapper, original)
    """
    if wrapper is None or original is None:
        raise TypeError("Wrapper and original instances cannot be None")

    debug_logger.log(
        "INFO",
        "Validating wrapper behavior",
        wrapper_type=type(wrapper).__name__,
        original_type=type(original).__name__,
    )

    try:
        # Check if wrapper has same methods as original
        original_methods = [
            method for method in dir(original) if not method.startswith("_")
        ]
        wrapper_methods = [
            method for method in dir(wrapper) if not method.startswith("_")
        ]

        missing_methods = set(original_methods) - set(wrapper_methods)
        if missing_methods:
            debug_logger.log(
                "ERROR",
                "Wrapper missing methods from original",
                missing_methods=list(missing_methods),
            )
            return False

        # Validate callable methods exist and are callable
        for method_name in original_methods:
            original_method = getattr(original, method_name)
            if callable(original_method):
                wrapper_method = getattr(wrapper, method_name, None)
                if not callable(wrapper_method):
                    debug_logger.log(
                        "ERROR", "Wrapper method not callable", method_name=method_name
                    )
                    return False

        debug_logger.log("INFO", "Wrapper behavior validation successful")
        return True

    except Exception as e:
        debug_logger.log("ERROR", "Wrapper behavior validation failed", error=str(e))
        return False


class SingletonCompatibilityWrapper:
    """Compatibility wrapper that bridges singleton and dependency injection patterns."""

    def __init__(
        self,
        singleton_class: type[Any],
        fallback_enabled: bool = True,
        context_key: str = "default",
    ) -> None:
        """Initialize compatibility wrapper.

        Args:
            singleton_class: The singleton class to wrap
            fallback_enabled: Whether to fall back to singleton access
            context_key: Key for DI container registration
        """
        self._singleton_class = singleton_class
        self._fallback_enabled = fallback_enabled
        self._context_key = context_key
        self._lock = threading.Lock()
        self._cached_instance: Any | None = None

        debug_logger.log(
            "INFO",
            "Initialized singleton compatibility wrapper",
            singleton_class=singleton_class.__name__,
            context_key=context_key,
        )

    def __getattr__(self, name: str) -> Any:
        """Delegate attribute access to wrapped singleton instance.

        Args:
            name: Attribute name to access

        Returns:
            Attribute value from singleton instance

        Raises:
            AttributeError: If attribute doesn't exist
            CompatibilityError: If instance access fails
        """
        try:
            instance = self._get_instance()
            if hasattr(instance, name):
                attr = getattr(instance, name)

                # If it's a method, wrap it to maintain singleton context
                if callable(attr):

                    def wrapped_method(*args: Any, **kwargs: Any) -> Any:
                        return attr(*args, **kwargs)

                    return wrapped_method
                else:
                    return attr
            else:
                raise AttributeError(
                    f"'{self._singleton_class.__name__}' object has no attribute '{name}'"
                )

        except AttributeError:
            # Re-raise AttributeError as-is for proper error propagation
            raise
        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Failed to access wrapped attribute",
                attribute_name=name,
                error=str(e),
            )
            raise CompatibilityError(f"Failed to access attribute '{name}': {e}") from e

    def _get_instance(self) -> Any:
        """Get singleton instance with context-aware fallback.

        Returns:
            Singleton instance from context or direct access

        Raises:
            CompatibilityError: If instance retrieval fails
        """
        with self._lock:
            # Future: Try context-based access first when DI system is ready
            # For P1.3b, we focus on fallback mechanism to support existing singleton usage
            debug_logger.log(
                "DEBUG",
                "Context-based access not yet implemented, using fallback",
                context_key=self._context_key,
            )

            # Fallback to direct singleton access
            if self._fallback_enabled:
                if self._cached_instance is None:
                    self._cached_instance = self._singleton_class()
                    debug_logger.log(
                        "INFO",
                        "Created singleton instance as fallback",
                        singleton_class=self._singleton_class.__name__,
                    )
                return self._cached_instance
            else:
                raise CompatibilityError(
                    f"Context unavailable and fallback disabled for {self._singleton_class.__name__}"
                )

    def reset(self) -> None:
        """Reset wrapper state and cached instances."""
        with self._lock:
            self._cached_instance = None
            debug_logger.log(
                "INFO",
                "Reset compatibility wrapper state",
                singleton_class=self._singleton_class.__name__,
            )


def _get_default_context_key(singleton_class: type[Any]) -> str:
    """Get default context key for singleton class.

    Args:
        singleton_class: The singleton class

    Returns:
        Default context key based on class name
    """
    class_name = singleton_class.__name__
    # Convert from PascalCase to snake_case for context key
    snake_case = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", class_name)
    snake_case = re.sub("([a-z0-9])([A-Z])", r"\1_\2", snake_case).lower()
    return snake_case
