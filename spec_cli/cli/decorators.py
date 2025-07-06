"""Context injection decorators for CLI commands."""

from collections.abc import Callable
from typing import Any, TypeVar

import click

from ..core.context import SpecContext
from ..logging.debug import debug_logger
from ..utils.click_utils import ClickIntegrationError, retrieve_context_data
from ..utils.decorator_utils import (
    DecoratorError,
    create_context_injector,
    preserve_function_metadata,
    validate_decorator_target,
)

F = TypeVar("F", bound=Callable[..., Any])


class ContextInjectionError(DecoratorError):
    """Error raised when context injection fails."""

    def __init__(self, message: str, click_ctx: click.Context | None = None) -> None:
        """Initialize context injection error.

        Args:
            message: Error message describing the injection failure
            click_ctx: Optional Click context for additional debugging
        """
        super().__init__(message)
        if click_ctx is not None:
            self.add_context("click_command", getattr(click_ctx.command, "name", None))
            self.add_context(
                "click_params", click_ctx.params if click_ctx.params else {}
            )


def _get_spec_context_from_click() -> SpecContext:
    """Retrieve SpecContext from current Click context.

    Returns:
        SpecContext instance from Click context

    Raises:
        ContextInjectionError: If context retrieval fails or context not found
    """
    try:
        # Get current Click context
        click_ctx = click.get_current_context(silent=True)
        if click_ctx is None:
            raise ContextInjectionError("No active Click context found")

        # Retrieve SpecContext from Click context storage
        spec_context = retrieve_context_data(click_ctx, "spec_context")
        debug_logger.log(
            "DEBUG",
            "Context retrieval status",
            spec_context_found=spec_context is not None,
            spec_context_type=type(spec_context).__name__ if spec_context else None,
        )
        if spec_context is None:
            # Create default context if not found with real implementations
            from ..config.settings import get_settings
            from ..ui.console import get_console
            from ..ui.progress_manager import ProgressManager

            settings = get_settings()
            rich_console = get_console()
            progress = ProgressManager()

            debug_logger.log(
                "DEBUG",
                "Created default dependencies",
                settings_type=type(settings).__name__,
                console_type=type(rich_console).__name__,
                progress_type=type(progress).__name__,
            )

            # Create adapter to bridge SpecConsole to SpecConsoleInterface
            class ConsoleAdapter:
                def __init__(self, spec_console):
                    self._console = spec_console
                    # Detect non-interactive mode to prevent hanging
                    import sys

                    self._is_interactive = sys.stdout.isatty() and sys.stderr.isatty()

                def print_message(self, text: str, style: str | None = None) -> None:
                    if not self._is_interactive:
                        # In non-interactive mode, use simple print to avoid Rich hanging
                        print(text)
                        return
                    if style:
                        self._console.print_status(text, style)
                    else:
                        self._console.print(text)

                def print_error(self, text: str) -> None:
                    if not self._is_interactive:
                        print(f"Error: {text}")
                        return
                    self._console.print_status(text, "error")

                def print_success(self, text: str) -> None:
                    if not self._is_interactive:
                        print(f"Success: {text}")
                        return
                    self._console.print_status(text, "success")

                def print_warning(self, text: str) -> None:
                    if not self._is_interactive:
                        print(f"Warning: {text}")
                        return
                    self._console.print_status(text, "warning")

                def get_width(self) -> int:
                    return getattr(self._console, "width", 80)

                def supports_color(self) -> bool:
                    return self._is_interactive and not getattr(
                        self._console, "no_color", False
                    )

                def capture_output(self):
                    # Return the capture_output from the underlying console if available
                    return getattr(self._console, "capture_output", lambda: None)()

            console = ConsoleAdapter(rich_console)

            # For migration period, pass concrete settings directly
            # even though SpecContext expects interface types
            spec_context = SpecContext(
                settings=settings, console=console, progress=progress
            )

            debug_logger.log(
                "DEBUG",
                "Created default SpecContext",
                final_settings_type=type(spec_context.settings).__name__,
                final_console_type=type(spec_context.console).__name__,
                final_progress_type=type(spec_context.progress).__name__,
            )

        if not isinstance(spec_context, SpecContext):
            raise ContextInjectionError(
                f"Invalid context type: expected SpecContext, got {type(spec_context)}"
            )

        return spec_context

    except ClickIntegrationError as e:
        raise ContextInjectionError(f"Click integration failed: {e}") from e
    except Exception as e:
        raise ContextInjectionError(f"Context retrieval failed: {e}") from e


def context_injection(func: F) -> F:
    """Decorator to automatically inject SpecContext into CLI commands.

    This decorator automatically provides a SpecContext instance as the first
    parameter to decorated functions. The context is retrieved from the Click
    context storage and injected seamlessly.

    Args:
        func: Function to decorate with context injection

    Returns:
        Decorated function with automatic context injection

    Raises:
        ContextInjectionError: If function is not suitable for decoration
        DecoratorError: If decorator application fails

    Example:
        >>> @context_injection
        ... @click.command()
        ... def my_command(ctx: SpecContext, name: str) -> None:
        ...     # ctx is automatically injected
        ...     print(f"Config: {ctx.config}")

    Note:
        - Function must accept at least one parameter for context
        - Context is injected as the first parameter
        - Compatible with Click command decorators
        - Preserves function metadata and Click attributes
    """
    # Validate function is suitable for decoration
    try:
        validate_decorator_target(func)
    except (DecoratorError, TypeError) as e:
        raise ContextInjectionError(f"Function validation failed: {e}") from e

    # Create context injector using Click context retrieval
    injector = create_context_injector(_get_spec_context_from_click)

    # Apply context injection decorator
    try:
        wrapped_func = injector(func)
    except (DecoratorError, TypeError) as e:
        raise ContextInjectionError(f"Context injection failed: {e}") from e

    # Preserve function metadata for Click compatibility
    try:
        enhanced_func = preserve_function_metadata(wrapped_func, func)
    except DecoratorError as e:
        raise ContextInjectionError(f"Metadata preservation failed: {e}") from e

    return enhanced_func  # type: ignore[return-value]


def inject_context(context_param: str = "ctx") -> Callable[[F], F]:
    """Parametric decorator for context injection with custom parameter name.

    Args:
        context_param: Name hint for the context parameter (for documentation)

    Returns:
        Decorator function that injects context into target functions

    Raises:
        ContextInjectionError: If decorator creation fails

    Example:
        >>> @inject_context("context")
        ... @click.command()
        ... def my_command(context: SpecContext, name: str) -> None:
        ...     # context is automatically injected
        ...     print(f"Config: {context.config}")

    Note:
        - The context_param is currently used for documentation only
        - Context is always injected as the first parameter
        - Future versions may support parameter name matching
    """
    if not isinstance(context_param, str) or not context_param.strip():
        raise ContextInjectionError("context_param must be a non-empty string")

    def decorator(func: F) -> F:
        try:
            return context_injection(func)
        except ContextInjectionError:
            raise
        except Exception as e:
            raise ContextInjectionError(
                f"Failed to create context injection decorator: {e}"
            ) from e

    return decorator


def with_context(func: F) -> F:
    """Simple alias for context_injection decorator.

    Provides a shorter decorator name for common usage patterns.

    Args:
        func: Function to decorate with context injection

    Returns:
        Decorated function with automatic context injection

    Example:
        >>> @with_context
        ... @click.command()
        ... def my_command(ctx: SpecContext, name: str) -> None:
        ...     print(f"Using context: {ctx}")
    """
    return context_injection(func)
