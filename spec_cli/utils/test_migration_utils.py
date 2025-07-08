"""Test fixture migration utilities for context-based dependency injection.

This module provides utilities for migrating test fixtures from singleton-dependent
patterns to context-based dependency injection patterns, ensuring test isolation
and eliminating state contamination.
"""

import inspect
from collections.abc import Callable
from typing import Any

import pytest

from ..core.context import SpecContext
from ..core.context_bridge import debug_logger
from .error_utils import SpecAnalysisError


class FixtureMigrationError(SpecAnalysisError):
    """Error during test fixture migration to context-based patterns."""


def create_context_fixture(factory_method: Callable) -> Callable:
    """Create context-based pytest fixture from factory method.

    Converts a factory method into a pytest fixture that creates isolated
    SpecContext instances for testing, eliminating singleton dependencies
    and ensuring test isolation.

    Args:
        factory_method: Factory method that returns a SpecContext instance

    Returns:
        Pytest fixture function that provides isolated context

    Raises:
        FixtureMigrationError: If context fixture creation fails

    Example:
        def create_test_context():
            return SpecContext.create_for_testing()

        test_context_fixture = create_context_fixture(create_test_context)
    """
    if not callable(factory_method):
        raise FixtureMigrationError(
            f"Factory method must be callable, got {type(factory_method)}"
        )

    try:
        debug_logger.log(
            "DEBUG",
            "Creating context fixture from factory method",
            factory_name=factory_method.__name__,
            factory_module=getattr(factory_method, "__module__", "unknown"),
        )

        # Inspect factory method signature to handle dependencies
        sig = inspect.signature(factory_method)
        factory_params = list(sig.parameters.keys())

        @pytest.fixture
        def context_fixture(*args: Any, **kwargs: Any) -> SpecContext:
            """Pytest fixture providing isolated SpecContext for testing.

            Returns:
                SpecContext instance created by factory method
            """
            try:
                debug_logger.log(
                    "DEBUG",
                    "Creating context instance via factory",
                    factory_name=factory_method.__name__,
                    args_count=len(args),
                    kwargs_keys=list(kwargs.keys()),
                )

                # Call factory method with appropriate arguments
                if factory_params:
                    # Factory expects arguments - pass what we received
                    context = factory_method(*args, **kwargs)
                else:
                    # Factory expects no arguments
                    context = factory_method()

                if not isinstance(context, SpecContext):
                    raise FixtureMigrationError(
                        f"Factory method must return SpecContext, got {type(context)}"
                    )

                debug_logger.log(
                    "DEBUG",
                    "Context fixture created successfully",
                    context_hash=context.get_context_hash()[:8],
                    settings_type=type(context.settings).__name__,
                    console_type=type(context.console).__name__,
                    progress_type=type(context.progress).__name__,
                )

                return context

            except Exception as e:
                debug_logger.log(
                    "ERROR",
                    "Context fixture creation failed",
                    factory_name=factory_method.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise FixtureMigrationError(
                    f"Failed to create context from factory {factory_method.__name__}: {e}"
                ) from e

        # Preserve factory method metadata
        context_fixture.__name__ = f"{factory_method.__name__}_fixture"
        context_fixture.__doc__ = (
            f"Context fixture created from {factory_method.__name__}"
        )

        return context_fixture

    except Exception as e:
        raise FixtureMigrationError(
            f"Failed to create context fixture from factory method: {e}"
        ) from e


def validate_test_isolation(test_func: Callable) -> bool:
    """Validate that test function provides proper isolation.

    Analyzes test function for patterns that could cause state contamination
    between test executions, ensuring proper context-based isolation.

    Args:
        test_func: Test function to validate for isolation

    Returns:
        True if test provides proper isolation, False otherwise

    Raises:
        FixtureMigrationError: If isolation validation fails

    Example:
        def test_with_context(spec_context):
            # Uses context injection - good isolation
            pass

        is_isolated = validate_test_isolation(test_with_context)  # Returns True
    """
    if not callable(test_func):
        raise FixtureMigrationError(
            f"Test function must be callable, got {type(test_func)}"
        )

    try:
        debug_logger.log(
            "DEBUG",
            "Validating test isolation",
            test_name=test_func.__name__,
            test_module=getattr(test_func, "__module__", "unknown"),
        )

        # Get test function signature
        sig = inspect.signature(test_func)
        param_names = list(sig.parameters.keys())

        # Check for context-based parameters
        has_context_param = any("context" in param.lower() for param in param_names)

        # Get test source code for pattern analysis
        isolation_issues = []

        try:
            source = inspect.getsource(test_func)

            # Patterns that indicate poor isolation
            contamination_patterns = [
                "get_settings()",
                "get_console()",
                "reset_console()",
                "spec_console.",
                "SpecSettings()",
                "SpecConsole()",
                "singleton",
                "os.environ[",
                "os.chdir(",
                "sys.modules[",
                "global ",
            ]

            for pattern in contamination_patterns:
                if pattern in source:
                    isolation_issues.append(pattern)

        except (OSError, TypeError):
            # Can't get source code - assume isolation issues
            debug_logger.log(
                "WARNING",
                "Could not get test source for analysis",
                test_name=test_func.__name__,
            )
            isolation_issues.append("source_unavailable")

        # Determine isolation quality
        is_isolated = has_context_param and len(isolation_issues) == 0

        debug_logger.log(
            "DEBUG",
            "Test isolation validation complete",
            test_name=test_func.__name__,
            has_context_param=has_context_param,
            isolation_issues_count=len(isolation_issues),
            isolation_issues=isolation_issues,
            is_isolated=is_isolated,
        )

        return is_isolated

    except Exception as e:
        raise FixtureMigrationError(
            f"Failed to validate test isolation for {test_func.__name__}: {e}"
        ) from e


def create_mock_context_fixture(
    settings_overrides: dict[str, Any] | None = None,
    console_overrides: dict[str, Any] | None = None,
    progress_overrides: dict[str, Any] | None = None,
) -> Callable:
    """Create mock context fixture with configurable overrides.

    Creates a pytest fixture that provides a SpecContext with mock dependencies,
    allowing for fine-grained control over mock behavior in tests.

    Args:
        settings_overrides: Optional settings attribute overrides
        console_overrides: Optional console behavior overrides
        progress_overrides: Optional progress behavior overrides

    Returns:
        Pytest fixture that provides mock SpecContext

    Raises:
        FixtureMigrationError: If mock context fixture creation fails

    Example:
        mock_fixture = create_mock_context_fixture(
            settings_overrides={"debug_enabled": True},
            console_overrides={"supports_color": True}
        )
    """
    try:
        debug_logger.log(
            "DEBUG",
            "Creating mock context fixture",
            settings_overrides=settings_overrides or {},
            console_overrides=console_overrides or {},
            progress_overrides=progress_overrides or {},
        )

        @pytest.fixture
        def mock_context_fixture() -> SpecContext:
            """Pytest fixture providing mock SpecContext for testing."""
            try:
                # Create base context using testing factory
                context = SpecContext.create_for_testing()

                # Apply settings overrides
                if settings_overrides:
                    for key, value in settings_overrides.items():
                        if hasattr(context.settings, key):
                            setattr(context.settings, key, value)

                # Apply console overrides
                if console_overrides:
                    for key, value in console_overrides.items():
                        if hasattr(context.console, key):
                            if callable(getattr(context.console, key)):
                                getattr(context.console, key).return_value = value
                            else:
                                setattr(context.console, key, value)

                # Apply progress overrides
                if progress_overrides:
                    for key, value in progress_overrides.items():
                        if hasattr(context.progress, key):
                            if callable(getattr(context.progress, key)):
                                getattr(context.progress, key).return_value = value
                            else:
                                setattr(context.progress, key, value)

                debug_logger.log(
                    "DEBUG",
                    "Mock context fixture created",
                    context_hash=context.get_context_hash()[:8],
                    applied_overrides={
                        "settings": len(settings_overrides or {}),
                        "console": len(console_overrides or {}),
                        "progress": len(progress_overrides or {}),
                    },
                )

                return context

            except Exception as e:
                debug_logger.log(
                    "ERROR",
                    "Mock context fixture creation failed",
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise FixtureMigrationError(
                    f"Failed to create mock context fixture: {e}"
                ) from e

        return mock_context_fixture

    except Exception as e:
        raise FixtureMigrationError(
            f"Failed to create mock context fixture: {e}"
        ) from e


def migrate_singleton_fixture(legacy_fixture_func: Callable) -> Callable:
    """Migrate legacy singleton fixture to context-based pattern.

    Converts an existing fixture that depends on singleton infrastructure
    to use context-based dependency injection instead.

    Args:
        legacy_fixture_func: Existing fixture function to migrate

    Returns:
        New context-based fixture function

    Raises:
        FixtureMigrationError: If fixture migration fails

    Example:
        @pytest.fixture
        def legacy_settings():
            return get_settings()  # Singleton access

        # Migrate to context-based
        new_settings = migrate_singleton_fixture(legacy_settings)
    """
    if not callable(legacy_fixture_func):
        raise FixtureMigrationError(
            f"Legacy fixture must be callable, got {type(legacy_fixture_func)}"
        )

    try:
        debug_logger.log(
            "DEBUG",
            "Migrating singleton fixture to context-based",
            legacy_name=legacy_fixture_func.__name__,
            legacy_module=getattr(legacy_fixture_func, "__module__", "unknown"),
        )

        @pytest.fixture
        def migrated_fixture(spec_context: SpecContext) -> Any:
            """Context-based fixture migrated from singleton pattern."""
            try:
                # Determine what type of dependency this fixture provided
                fixture_name = legacy_fixture_func.__name__.lower()

                if "setting" in fixture_name:
                    result = spec_context.settings
                elif "console" in fixture_name:
                    result = spec_context.console
                elif "progress" in fixture_name:
                    result = spec_context.progress
                else:
                    # Default to providing the full context
                    result = spec_context

                debug_logger.log(
                    "DEBUG",
                    "Singleton fixture migrated successfully",
                    legacy_name=legacy_fixture_func.__name__,
                    migrated_type=type(result).__name__,
                    context_hash=spec_context.get_context_hash()[:8],
                )

                return result

            except Exception as e:
                debug_logger.log(
                    "ERROR",
                    "Singleton fixture migration failed",
                    legacy_name=legacy_fixture_func.__name__,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise FixtureMigrationError(
                    f"Failed to migrate fixture {legacy_fixture_func.__name__}: {e}"
                ) from e

        # Preserve original fixture metadata
        migrated_fixture.__name__ = f"{legacy_fixture_func.__name__}_migrated"
        migrated_fixture.__doc__ = (
            f"Context-based fixture migrated from {legacy_fixture_func.__name__}"
        )

        return migrated_fixture

    except Exception as e:
        raise FixtureMigrationError(f"Failed to migrate singleton fixture: {e}") from e
