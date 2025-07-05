"""Compatibility layer for singleton to dependency injection migration.

This module provides compatibility wrappers that bridge existing singleton patterns
with the new dependency injection system, enabling gradual migration without
breaking existing code.
"""

import threading
from typing import Any, cast

from ..exceptions import CompatibilityError
from ..logging.debug import debug_logger
from ..utils.compatibility_utils import (
    validate_wrapper_behavior,
)

# Note: error_utils.create_error_context expects Path, so we'll create context dicts directly


class CompatibilityLayer:
    """Central compatibility layer managing singleton to DI migration.

    Provides transparent access to singletons while supporting gradual migration
    to dependency injection patterns without breaking existing functionality.
    """

    def __init__(self) -> None:
        """Initialize compatibility layer with singleton mappings."""
        self._wrappers: dict[str, Any] = {}
        self._lock = threading.Lock()
        self._initialized = False

        debug_logger.log("INFO", "CompatibilityLayer initialized")

    def get_progress_manager_wrapper(self) -> "ProgressManagerWrapper":
        """Get ProgressManager compatibility wrapper.

        Returns:
            ProgressManagerWrapper instance providing transparent access

        Raises:
            CompatibilityError: If wrapper creation or access fails

        Example:
            >>> layer = CompatibilityLayer()
            >>> wrapper = layer.get_progress_manager_wrapper()
            >>> manager = wrapper.get_progress_manager()
        """
        wrapper_key = "progress_manager"

        with self._lock:
            if wrapper_key not in self._wrappers:
                try:
                    # Import here to avoid circular imports
                    from ..ui.progress_manager import ProgressManagerSingleton

                    debug_logger.log(
                        "INFO",
                        "Creating ProgressManager compatibility wrapper",
                        wrapper_key=wrapper_key,
                    )

                    self._wrappers[wrapper_key] = ProgressManagerWrapper(
                        singleton_class=ProgressManagerSingleton
                    )

                except Exception as e:
                    error_context = {
                        "operation": "progress_manager_wrapper_creation",
                        "wrapper_key": wrapper_key,
                        "error": str(e),
                    }
                    debug_logger.log(
                        "ERROR",
                        "Failed to create ProgressManager wrapper",
                        **error_context,
                    )
                    raise CompatibilityError(
                        f"Failed to create ProgressManager wrapper: {e}", error_context
                    ) from e

            wrapper = cast(ProgressManagerWrapper, self._wrappers[wrapper_key])
            return wrapper

    def validate_all_wrappers(self) -> bool:
        """Validate all created wrappers maintain singleton behavior.

        Returns:
            True if all wrappers are valid, False otherwise

        Example:
            >>> layer = CompatibilityLayer()
            >>> wrapper = layer.get_progress_manager_wrapper()
            >>> is_valid = layer.validate_all_wrappers()
        """
        try:
            with self._lock:
                for wrapper_key, wrapper in self._wrappers.items():
                    debug_logger.log(
                        "INFO", "Validating wrapper behavior", wrapper_key=wrapper_key
                    )

                    # Get original singleton for comparison
                    original = wrapper._singleton_class()

                    if not validate_wrapper_behavior(wrapper, original):
                        debug_logger.log(
                            "ERROR",
                            "Wrapper validation failed",
                            wrapper_key=wrapper_key,
                        )
                        return False

                debug_logger.log("INFO", "All wrapper validations successful")
                return True

        except Exception as e:
            debug_logger.log("ERROR", "Wrapper validation process failed", error=str(e))
            return False

    def reset_all_wrappers(self) -> None:
        """Reset all wrapper states for testing.

        Clears cached instances and resets wrapper state to enable
        clean testing environments.
        """
        with self._lock:
            for wrapper_key, wrapper in self._wrappers.items():
                if hasattr(wrapper, "reset"):
                    wrapper.reset()
                    debug_logger.log(
                        "INFO", "Reset wrapper state", wrapper_key=wrapper_key
                    )

            debug_logger.log("INFO", "All wrapper states reset")


class ProgressManagerWrapper:
    """Compatibility wrapper for ProgressManagerSingleton.

    Provides transparent access to ProgressManager functionality while
    supporting migration to dependency injection patterns.
    """

    def __init__(self, singleton_class: type) -> None:
        """Initialize ProgressManager wrapper.

        Args:
            singleton_class: ProgressManagerSingleton class to wrap
        """
        self._singleton_class = singleton_class
        self._lock = threading.Lock()
        self._cached_instance: Any | None = None

        debug_logger.log(
            "INFO",
            "ProgressManagerWrapper initialized",
            singleton_class=singleton_class.__name__,
        )

    def get_progress_manager(self) -> Any:
        """Get progress manager instance with transparent access.

        Returns:
            ProgressManager instance from singleton or DI context

        Raises:
            CompatibilityError: If progress manager retrieval fails

        Example:
            >>> wrapper = ProgressManagerWrapper(ProgressManagerSingleton)
            >>> manager = wrapper.get_progress_manager()
        """
        try:
            with self._lock:
                # Use cached singleton instance for consistent behavior
                if self._cached_instance is None:
                    self._cached_instance = self._singleton_class()
                    debug_logger.log(
                        "INFO",
                        "Created ProgressManagerSingleton instance",
                        singleton_class=self._singleton_class.__name__,
                    )

                # Delegate to singleton's get_progress_manager method
                return self._cached_instance.get_progress_manager()

        except Exception as e:
            error_context = {
                "operation": "get_progress_manager",
                "singleton_class": self._singleton_class.__name__,
                "error": str(e),
            }
            debug_logger.log("ERROR", "Failed to get progress manager", **error_context)
            raise CompatibilityError(
                f"Failed to get progress manager: {e}", error_context
            ) from e

    def set_progress_manager(self, manager: Any) -> None:
        """Set progress manager with transparent delegation.

        Args:
            manager: ProgressManager instance to set

        Raises:
            CompatibilityError: If progress manager setting fails

        Example:
            >>> wrapper = ProgressManagerWrapper(ProgressManagerSingleton)
            >>> wrapper.set_progress_manager(custom_manager)
        """
        try:
            with self._lock:
                # Ensure singleton instance exists
                if self._cached_instance is None:
                    self._cached_instance = self._singleton_class()

                # Delegate to singleton's set_progress_manager method
                self._cached_instance.set_progress_manager(manager)

                debug_logger.log(
                    "INFO",
                    "Progress manager set successfully",
                    manager_type=type(manager).__name__,
                )

        except Exception as e:
            error_context = {
                "operation": "set_progress_manager",
                "manager_type": type(manager).__name__ if manager else "None",
                "error": str(e),
            }
            debug_logger.log("ERROR", "Failed to set progress manager", **error_context)
            raise CompatibilityError(
                f"Failed to set progress manager: {e}", error_context
            ) from e

    def reset_progress_manager(self) -> None:
        """Reset progress manager state for testing.

        Resets both the wrapper and underlying singleton state to enable
        clean test environments.

        Raises:
            CompatibilityError: If reset operation fails
        """
        try:
            with self._lock:
                # Reset singleton if it exists
                if self._cached_instance is not None:
                    if hasattr(self._cached_instance, "reset"):
                        self._cached_instance.reset()

                    # Reset singleton using singleton utility
                    from ..utils.singleton import reset_singleton

                    reset_singleton(self._singleton_class)

                # Clear cached instance
                self._cached_instance = None

                debug_logger.log(
                    "INFO",
                    "Progress manager state reset",
                    singleton_class=self._singleton_class.__name__,
                )

        except Exception as e:
            error_context = {
                "operation": "reset_progress_manager",
                "singleton_class": self._singleton_class.__name__,
                "error": str(e),
            }
            debug_logger.log(
                "ERROR", "Failed to reset progress manager", **error_context
            )
            raise CompatibilityError(
                f"Failed to reset progress manager: {e}", error_context
            ) from e

    def reset(self) -> None:
        """Reset wrapper state for testing compatibility."""
        self.reset_progress_manager()

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
            # Use object.__getattribute__ to avoid recursion
            lock = object.__getattribute__(self, "_lock")
            singleton_class = object.__getattribute__(self, "_singleton_class")

            with lock:
                # Ensure singleton instance exists using object.__getattribute__
                try:
                    cached_instance = object.__getattribute__(self, "_cached_instance")
                except AttributeError:
                    cached_instance = None

                if cached_instance is None:
                    cached_instance = singleton_class()
                    object.__setattr__(self, "_cached_instance", cached_instance)

                if hasattr(cached_instance, name):
                    attr = getattr(cached_instance, name)

                    # If it's a method, wrap it to maintain context
                    if callable(attr):

                        def wrapped_method(*args: Any, **kwargs: Any) -> Any:
                            return attr(*args, **kwargs)

                        return wrapped_method
                    else:
                        return attr
                else:
                    raise AttributeError(
                        f"'{singleton_class.__name__}' object has no attribute '{name}'"
                    )

        except AttributeError:
            # Re-raise AttributeError as-is
            raise
        except Exception as e:
            singleton_class = object.__getattribute__(self, "_singleton_class")
            error_context = {
                "operation": "attribute_access",
                "attribute_name": name,
                "singleton_class": singleton_class.__name__,
                "error": str(e),
            }
            debug_logger.log(
                "ERROR", "Failed to access wrapped attribute", **error_context
            )
            raise CompatibilityError(
                f"Failed to access attribute '{name}': {e}", error_context
            ) from e


# Global compatibility layer instance for application use
compatibility_layer = CompatibilityLayer()


def get_progress_manager_compatibility() -> ProgressManagerWrapper:
    """Get global ProgressManager compatibility wrapper.

    Returns:
        ProgressManagerWrapper instance for transparent access

    Raises:
        CompatibilityError: If wrapper access fails

    Example:
        >>> wrapper = get_progress_manager_compatibility()
        >>> manager = wrapper.get_progress_manager()
    """
    return compatibility_layer.get_progress_manager_wrapper()
