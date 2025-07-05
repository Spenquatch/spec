"""Click framework utilities for context storage and retrieval."""

from typing import Any

import click

from ..exceptions import SpecError


class ClickIntegrationError(SpecError):
    """Error raised when Click context integration fails."""

    def __init__(self, message: str, click_ctx: click.Context | None = None) -> None:
        """Initialize Click integration error.

        Args:
            message: Error message describing the integration failure
            click_ctx: Optional Click context for additional context
        """
        super().__init__(message)
        if click_ctx is not None:
            self.add_context(
                "click_info_name",
                getattr(click_ctx.command, "name", None) if click_ctx.command else None,
            )
            self.add_context(
                "click_params", click_ctx.params if click_ctx.params else {}
            )
            self.add_context(
                "click_parent",
                getattr(click_ctx.parent.command, "name", None)
                if click_ctx.parent and click_ctx.parent.command
                else None,
            )


def store_context_data(click_ctx: click.Context, key: str, data: Any) -> None:
    """Store data in Click context with collision prevention.

    Args:
        click_ctx: Click context object to store data in
        key: String key to store data under (prefixed with 'spec_' for safety)
        data: Any data to store in the context

    Raises:
        ClickIntegrationError: If context storage fails or key collision detected
        TypeError: If click_ctx is not a Click Context

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> store_context_data(ctx, "user_config", {"debug": True})
        >>> # Data stored under 'spec_user_config' key
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    if not isinstance(key, str) or not key.strip():
        raise ClickIntegrationError("Context key must be a non-empty string")

    # Prefix key to avoid collisions with Click's internal context data
    prefixed_key = f"spec_{key}"

    try:
        # Initialize obj dict if it doesn't exist
        if click_ctx.obj is None:
            click_ctx.obj = {}

        # Check for existing data and warn about collision
        if prefixed_key in click_ctx.obj:
            existing_data = click_ctx.obj[prefixed_key]
            if existing_data != data:
                raise ClickIntegrationError(
                    f"Context key collision detected: '{key}' already exists with different data",
                    click_ctx,
                )

        # Store the data
        click_ctx.obj[prefixed_key] = data

    except (AttributeError, TypeError) as e:
        raise ClickIntegrationError(
            f"Failed to store context data for key '{key}': {e}", click_ctx
        ) from e


def retrieve_context_data(
    click_ctx: click.Context, key: str, default: Any = None
) -> Any:
    """Retrieve data from Click context with validation.

    Args:
        click_ctx: Click context object to retrieve data from
        key: String key to retrieve data for (will be prefixed with 'spec_')
        default: Default value to return if key not found

    Returns:
        Stored data or default value if key not found

    Raises:
        ClickIntegrationError: If context retrieval fails
        TypeError: If click_ctx is not a Click Context

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> ctx.obj = {"spec_user_config": {"debug": True}}
        >>> config = retrieve_context_data(ctx, "user_config")
        >>> print(config)  # {"debug": True}
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    if not isinstance(key, str) or not key.strip():
        raise ClickIntegrationError("Context key must be a non-empty string")

    # Prefix key to match storage format
    prefixed_key = f"spec_{key}"

    try:
        # Return default if obj is None or key doesn't exist
        if click_ctx.obj is None:
            return default

        return click_ctx.obj.get(prefixed_key, default)

    except (AttributeError, TypeError) as e:
        raise ClickIntegrationError(
            f"Failed to retrieve context data for key '{key}': {e}", click_ctx
        ) from e


def validate_click_context(click_ctx: click.Context) -> bool:
    """Validate Click context for safe operations.

    Args:
        click_ctx: Click context object to validate

    Returns:
        True if context is valid for operations

    Raises:
        TypeError: If click_ctx is not a Click Context
        ClickIntegrationError: If context validation fails

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> is_valid = validate_click_context(ctx)
        >>> print(is_valid)  # True
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    try:
        # Check that context has basic required attributes
        if not hasattr(click_ctx, "command"):
            raise ClickIntegrationError("Click context missing 'command' attribute")

        if not hasattr(click_ctx, "params"):
            raise ClickIntegrationError("Click context missing 'params' attribute")

        # Validate that obj can be used for storage (can be None or dict-like)
        if click_ctx.obj is not None and not (
            hasattr(click_ctx.obj, "__getitem__")
            and hasattr(click_ctx.obj, "__setitem__")
        ):
            raise ClickIntegrationError(
                "Click context 'obj' must be None or dict-like for data storage"
            )

        return True

    except Exception as e:
        if isinstance(e, ClickIntegrationError):
            raise
        raise ClickIntegrationError(f"Context validation failed: {e}") from e


def clear_context_data(click_ctx: click.Context, key: str | None = None) -> None:
    """Clear stored context data with optional key filtering.

    Args:
        click_ctx: Click context object to clear data from
        key: Optional specific key to clear (if None, clears all spec_ prefixed data)

    Raises:
        ClickIntegrationError: If context clearing fails
        TypeError: If click_ctx is not a Click Context

    Example:
        >>> import click
        >>> ctx = click.Context(click.Command("test"))
        >>> ctx.obj = {"spec_config": {}, "other": "data"}
        >>> clear_context_data(ctx, "config")  # Clears only spec_config
        >>> clear_context_data(ctx)  # Clears all spec_ prefixed data
    """
    if not isinstance(click_ctx, click.Context):
        raise TypeError(f"Expected click.Context, got {type(click_ctx)}")

    try:
        # Nothing to clear if obj is None
        if click_ctx.obj is None:
            return

        if key is not None:
            # Clear specific key
            if not isinstance(key, str) or not key.strip():
                raise ClickIntegrationError("Context key must be a non-empty string")

            prefixed_key = f"spec_{key}"
            click_ctx.obj.pop(prefixed_key, None)
        else:
            # Clear all spec_ prefixed keys
            spec_keys = [k for k in click_ctx.obj.keys() if k.startswith("spec_")]
            for spec_key in spec_keys:
                click_ctx.obj.pop(spec_key, None)

    except (AttributeError, TypeError) as e:
        raise ClickIntegrationError(f"Failed to clear context data: {e}") from e
