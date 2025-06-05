"""CLI-specific exception handling."""

import click

from ..exceptions import SpecError


class CLIError(SpecError):
    """Base exception for CLI-specific errors."""

    pass


class CLIValidationError(CLIError):
    """CLI input validation error."""

    def __init__(
        self,
        message: str,
        parameter: str | None = None,
        suggestions: list[str] | None = None,
    ):
        """Initialize CLI validation error.

        Args:
            message: Error message
            parameter: Parameter name that caused the error
            suggestions: Optional list of suggestions for fixing the error
        """
        super().__init__(message)
        self.parameter = parameter
        self.suggestions = suggestions or []


class CLIConfigurationError(CLIError):
    """CLI configuration error."""

    pass


class CLIOperationError(CLIError):
    """CLI operation error."""

    pass


def convert_to_click_exception(error: Exception) -> click.ClickException:
    """Convert various exceptions to Click exceptions.

    Args:
        error: Exception to convert

    Returns:
        ClickException with appropriate message
    """
    if isinstance(error, click.ClickException):
        return error
    elif isinstance(error, CLIError):
        return click.ClickException(str(error))
    elif isinstance(error, SpecError):
        return click.ClickException(f"Spec error: {error}")
    else:
        return click.ClickException(f"Unexpected error: {error}")


def handle_validation_error(
    parameter: str, message: str, suggestions: list[str] | None = None
) -> None:
    """Handle validation errors with suggestions.

    Args:
        parameter: Parameter name that failed validation
        message: Error message
        suggestions: Optional list of suggestions

    Raises:
        click.BadParameter: With formatted message
    """
    error_msg = message
    if suggestions:
        error_msg += "\n\nSuggestions:"
        for suggestion in suggestions:
            error_msg += f"\n  • {suggestion}"

    raise click.BadParameter(error_msg)
