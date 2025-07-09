"""Click context integration utilities for dependency injection support."""

from typing import TypeVar

import click

from ..core.context import SpecContext
from ..logging.debug import debug_logger
from ..utils.click_utils import (
    ClickIntegrationError,
    clear_context_data,
    retrieve_context_data,
    store_context_data,
    validate_click_context,
)

T = TypeVar("T")


def integrate_spec_context(click_ctx: click.Context, spec_context: SpecContext) -> None:
    """Integrate SpecContext with Click context for dependency injection.

    Args:
        click_ctx: Click context object to store SpecContext in
        spec_context: SpecContext instance to integrate

    Raises:
        ClickIntegrationError: If context integration fails
        TypeError: If arguments are not correct types

    Example:
        >>> import click
        >>> from spec_cli.core.context import SpecContext
        >>> ctx = click.Context(click.Command("test"))
        >>> spec_ctx = SpecContext()
        >>> integrate_spec_context(ctx, spec_ctx)
        >>> # SpecContext now accessible via Click context
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    if not isinstance(spec_context, SpecContext):
        raise TypeError(f"Expected SpecContext, got {type(spec_context)}")

    try:
        # Validate Click context first
        validate_click_context(click_ctx)

        # Store the SpecContext with a standard key
        store_context_data(click_ctx, "spec_context", spec_context)

        debug_logger.log(
            "DEBUG",
            "SpecContext integrated with Click context",
            context_id=id(spec_context),
            click_command=getattr(click_ctx.command, "name", "unknown")
            if click_ctx.command
            else "unknown",
        )

    except Exception as e:
        if isinstance(e, ClickIntegrationError | TypeError):
            raise
        raise ClickIntegrationError(
            f"Failed to integrate SpecContext: {e}", click_ctx
        ) from e


def retrieve_spec_context(click_ctx: click.Context) -> SpecContext | None:
    """Retrieve SpecContext from Click context.

    Args:
        click_ctx: Click context object to retrieve SpecContext from

    Returns:
        SpecContext instance if found, None otherwise

    Raises:
        ClickIntegrationError: If context retrieval fails
        TypeError: If click_ctx is not a Click Context

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> spec_ctx = retrieve_spec_context(ctx)
        >>> if spec_ctx:
        ...     print(f"Found SpecContext: {spec_ctx}")
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    try:
        spec_context = retrieve_context_data(click_ctx, "spec_context")

        if spec_context is not None and not isinstance(spec_context, SpecContext):
            raise ClickIntegrationError(
                f"Invalid SpecContext type in Click context: {type(spec_context)}",
                click_ctx,
            )

        return spec_context

    except Exception as e:
        if isinstance(e, ClickIntegrationError | TypeError):
            raise
        raise ClickIntegrationError(
            f"Failed to retrieve SpecContext: {e}", click_ctx
        ) from e


def store_typed_context_data(
    click_ctx: click.Context, key: str, data: T, expected_type: type[T]
) -> None:
    """Store typed data in Click context with type validation.

    Args:
        click_ctx: Click context object to store data in
        key: String key to store data under
        data: Data to store with type validation
        expected_type: Expected type for validation

    Raises:
        ClickIntegrationError: If context storage fails or type validation fails
        TypeError: If arguments are not correct types

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> store_typed_context_data(ctx, "config", {"debug": True}, dict)
        >>> # Data stored with type validation
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    if not isinstance(key, str) or not key.strip():
        raise ClickIntegrationError("Context key must be a non-empty string")

    if not isinstance(data, expected_type):
        raise ClickIntegrationError(
            f"Type validation failed: expected {expected_type.__name__}, "
            f"got {type(data).__name__}",
            click_ctx,
        )

    try:
        store_context_data(click_ctx, key, data)

        debug_logger.log(
            "DEBUG",
            "Typed context data stored",
            key=key,
            data_type=type(data).__name__,
            click_command=getattr(click_ctx.command, "name", "unknown")
            if click_ctx.command
            else "unknown",
        )

    except Exception as e:
        if isinstance(e, ClickIntegrationError | TypeError):
            raise
        raise ClickIntegrationError(
            f"Failed to store typed context data for key '{key}': {e}", click_ctx
        ) from e


def retrieve_typed_context_data(
    click_ctx: click.Context, key: str, expected_type: type[T], default: T | None = None
) -> T | None:
    """Retrieve typed data from Click context with type validation.

    Args:
        click_ctx: Click context object to retrieve data from
        key: String key to retrieve data for
        expected_type: Expected type for validation
        default: Default value to return if key not found

    Returns:
        Stored data of expected type or default value

    Raises:
        ClickIntegrationError: If context retrieval fails or type validation fails
        TypeError: If click_ctx is not a Click Context

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> config = retrieve_typed_context_data(ctx, "config", dict, {})
        >>> print(type(config))  # <class 'dict'>
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    if not isinstance(key, str) or not key.strip():
        raise ClickIntegrationError("Context key must be a non-empty string")

    try:
        data = retrieve_context_data(click_ctx, key, default)

        # Validate type if data is not None and not the default
        if data is not None and data != default:
            if not isinstance(data, expected_type):
                raise ClickIntegrationError(
                    f"Type validation failed: expected {expected_type.__name__}, "
                    f"got {type(data).__name__}",
                    click_ctx,
                )

        return data  # type: ignore[no-any-return]

    except Exception as e:
        if isinstance(e, ClickIntegrationError | TypeError):
            raise
        raise ClickIntegrationError(
            f"Failed to retrieve typed context data for key '{key}': {e}", click_ctx
        ) from e


def setup_dependency_injection_context(click_ctx: click.Context) -> None:
    """Initialize Click context for dependency injection patterns.

    Args:
        click_ctx: Click context object to setup for dependency injection

    Raises:
        ClickIntegrationError: If context setup fails
        TypeError: If click_ctx is not a Click Context

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> setup_dependency_injection_context(ctx)
        >>> # Context ready for dependency injection
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    try:
        # Validate Click context first
        validate_click_context(click_ctx)

        # Initialize context object if needed
        if click_ctx.obj is None:
            click_ctx.obj = {}

        # Store dependency injection metadata
        store_context_data(
            click_ctx,
            "di_metadata",
            {
                "initialized": True,
                "command": getattr(click_ctx.command, "name", "unknown")
                if click_ctx.command
                else "unknown",
                "parent_command": (
                    getattr(click_ctx.parent.command, "name", None)
                    if click_ctx.parent and click_ctx.parent.command
                    else None
                ),
            },
        )

        debug_logger.log(
            "DEBUG",
            "Dependency injection context setup complete",
            click_command=getattr(click_ctx.command, "name", "unknown")
            if click_ctx.command
            else "unknown",
        )

    except Exception as e:
        if isinstance(e, ClickIntegrationError | TypeError):
            raise
        raise ClickIntegrationError(
            f"Failed to setup dependency injection context: {e}", click_ctx
        ) from e


def teardown_dependency_injection_context(click_ctx: click.Context) -> None:
    """Teardown Click context dependency injection data.

    Args:
        click_ctx: Click context object to teardown

    Raises:
        ClickIntegrationError: If context teardown fails
        TypeError: If click_ctx is not a Click Context

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> teardown_dependency_injection_context(ctx)
        >>> # Context cleaned up
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    try:
        # Clear all spec-related context data
        clear_context_data(click_ctx)

        debug_logger.log(
            "DEBUG",
            "Dependency injection context teardown complete",
            click_command=getattr(click_ctx.command, "name", "unknown")
            if click_ctx.command
            else "unknown",
        )

    except Exception as e:
        if isinstance(e, ClickIntegrationError | TypeError):
            raise
        raise ClickIntegrationError(
            f"Failed to teardown dependency injection context: {e}", click_ctx
        ) from e


def get_context_keys(click_ctx: click.Context) -> list[str]:
    """Get list of all spec-related context keys.

    Args:
        click_ctx: Click context object to examine

    Returns:
        List of spec-related context keys (without 'spec_' prefix)

    Raises:
        ClickIntegrationError: If context examination fails
        TypeError: If click_ctx is not a Click Context

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> ctx.obj = {"spec_config": {}, "spec_context": None}
        >>> keys = get_context_keys(ctx)
        >>> print(keys)  # ['config', 'context']
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    try:
        if click_ctx.obj is None:
            return []

        # Extract spec-related keys and remove prefix
        spec_keys = [
            key[5:]  # Remove 'spec_' prefix
            for key in click_ctx.obj.keys()
            if key.startswith("spec_")
        ]

        return spec_keys

    except Exception as e:
        raise ClickIntegrationError(
            f"Failed to get context keys: {e}", click_ctx
        ) from e
