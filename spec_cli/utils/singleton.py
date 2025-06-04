"""Thread-safe singleton implementation utilities.

This module provides reusable singleton patterns for consistent instance management
across the application with proper thread safety and testing support.
"""

import threading
from functools import wraps
from typing import Any, Dict, Type, TypeVar, cast

from ..logging.debug import debug_logger

T = TypeVar("T")

# Thread-safe singleton instances storage
_instances: Dict[Type[Any], Any] = {}
_instance_locks: Dict[Type[Any], threading.Lock] = {}
_global_lock = threading.Lock()


def singleton_decorator(cls: Type[T]) -> Type[T]:
    """Thread-safe singleton decorator.

    Args:
        cls: Class to make singleton

    Returns:
        Decorated class with singleton behavior

    Raises:
        TypeError: If cls is not a class

    Example:
        @singleton_decorator
        class MyService:
            def __init__(self):
                self.initialized = True
    """
    if not isinstance(cls, type):
        raise TypeError("singleton_decorator can only be applied to classes")

    @wraps(cls)
    def get_instance(*args: Any, **kwargs: Any) -> T:
        """Get or create singleton instance with thread safety."""
        if cls not in _instances:
            with _global_lock:
                if cls not in _instances:
                    debug_logger.log(
                        "DEBUG",
                        "Creating new singleton instance",
                        class_name=cls.__name__,
                        module=cls.__module__,
                    )
                    _instance_locks[cls] = threading.Lock()
                    instance = cls(*args, **kwargs)
                    _instances[cls] = instance
                else:
                    debug_logger.log(
                        "DEBUG",
                        "Using existing singleton instance",
                        class_name=cls.__name__,
                    )

        return cast(T, _instances[cls])

    # Preserve class metadata
    get_instance.__name__ = cls.__name__
    get_instance.__doc__ = cls.__doc__
    get_instance.__module__ = cls.__module__
    get_instance.__qualname__ = cls.__qualname__

    # Add class attributes for introspection
    get_instance._original_class = cls  # type: ignore
    get_instance._is_singleton = True  # type: ignore

    return cast(Type[T], get_instance)


class SingletonMeta(type):
    """Metaclass-based singleton implementation with thread safety.

    Provides an alternative to the decorator approach for classes that need
    to use metaclass-based singleton behavior.

    Example:
        class MyService(metaclass=SingletonMeta):
            def __init__(self):
                self.initialized = True
    """

    _instances: Dict[Type[Any], Any] = {}
    _locks: Dict[Type[Any], threading.Lock] = {}
    _global_lock = threading.Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Thread-safe instance creation."""
        if cls not in cls._instances:
            with cls._global_lock:
                if cls not in cls._instances:
                    debug_logger.log(
                        "DEBUG",
                        "Creating new singleton instance via metaclass",
                        class_name=cls.__name__,
                        module=cls.__module__,
                    )
                    cls._locks[cls] = threading.Lock()
                    instance = super().__call__(*args, **kwargs)
                    cls._instances[cls] = instance
                else:
                    debug_logger.log(
                        "DEBUG",
                        "Using existing singleton instance via metaclass",
                        class_name=cls.__name__,
                    )

        return cls._instances[cls]


def reset_singleton(cls: Type[Any]) -> None:
    """Reset singleton instance for testing purposes.

    Args:
        cls: Class to reset singleton instance for

    Example:
        reset_singleton(MyService)
        # Next call to MyService() will create new instance
    """
    with _global_lock:
        # For decorator-based singletons, use the original class
        original_cls = cls
        if hasattr(cls, "_original_class"):
            original_cls = cls._original_class

        # Reset decorator-based singleton
        if original_cls in _instances:
            debug_logger.log(
                "DEBUG", "Resetting decorator-based singleton", class_name=cls.__name__
            )
            del _instances[original_cls]
            if original_cls in _instance_locks:
                del _instance_locks[original_cls]

        # Reset metaclass-based singleton
        if hasattr(cls, "_instances") and cls in cls._instances:
            debug_logger.log(
                "DEBUG", "Resetting metaclass-based singleton", class_name=cls.__name__
            )
            del cls._instances[cls]
            if cls in cls._locks:
                del cls._locks[cls]
