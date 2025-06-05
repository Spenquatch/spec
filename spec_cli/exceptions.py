"""Custom exception classes for the spec CLI package.

This module defines the exception hierarchy used throughout the spec CLI to
provide structured error handling with context information and user-friendly
error messages.
"""

from typing import Any


class SpecError(Exception):
    """Base exception for all spec-related errors.

    Provides structured error handling with context information
    for debugging and user-friendly error messages.
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None):
        """Initialize the SpecError.

        Args:
            message: Error message
            context: Optional context information for debugging
        """
        self.message = message
        self.context = context or {}
        self.details: str | None = None
        super().__init__(self.message)

    def get_user_message(self) -> str:
        """Get user-friendly error message."""
        return self.message

    def get_context(self) -> dict[str, Any]:
        """Get error context for debugging."""
        return self.context

    def add_context(self, key: str, value: Any) -> None:
        """Add additional context to the error."""
        self.context[key] = value


class SpecNotInitializedError(SpecError):
    """Raised when spec operations are attempted in uninitialized directory."""

    def __init__(
        self,
        message: str = "Spec repository not initialized",
        context: dict[str, Any] | None = None,
    ):
        """Initialize the SpecNotInitializedError.

        Args:
            message: Error message
            context: Optional context information for debugging
        """
        super().__init__(message, context)

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecNotInitializedError."""
        return f"{self.message}. Run 'spec init' to initialize."


class SpecPermissionError(SpecError):
    """Raised when permission is denied for spec operations."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecPermissionError."""
        return (
            f"Permission denied: {self.message}. Check file permissions and try again."
        )


class SpecGitError(SpecError):
    """Raised when Git operations fail."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecGitError."""
        return f"Git operation failed: {self.message}"


class SpecConfigurationError(SpecError):
    """Raised when configuration is invalid."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecConfigurationError."""
        return f"Configuration error: {self.message}"


class SpecTemplateError(SpecError):
    """Raised when template processing fails."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecTemplateError."""
        return f"Template error: {self.message}"


class SpecFileError(SpecError):
    """Raised when file operations fail."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecFileError."""
        return f"File operation failed: {self.message}"


class SpecRepositoryError(SpecError):
    """Raised when repository operations fail."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecRepositoryError."""
        return f"Repository operation failed: {self.message}"


class SpecWorkflowError(SpecError):
    """Raised when workflow operations fail."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecWorkflowError."""
        return f"Workflow operation failed: {self.message}"


class SpecValidationError(SpecError):
    """Raised when validation fails."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecValidationError."""
        return f"Validation failed: {self.message}"


class SpecConflictError(SpecError):
    """Raised when file conflicts occur during processing."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecConflictError."""
        return f"Conflict resolution failed: {self.message}"


class SpecProcessingError(SpecError):
    """Raised when file processing operations fail."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecProcessingError."""
        return f"Processing failed: {self.message}"


class SpecBatchProcessingError(SpecError):
    """Raised when batch processing operations fail."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecBatchProcessingError."""
        return f"Batch processing failed: {self.message}"


class SpecGenerationError(SpecError):
    """Raised when documentation generation fails."""

    def get_user_message(self) -> str:
        """Get user-friendly error message for SpecGenerationError."""
        return f"Generation failed: {self.message}"


# Convenience function for creating errors with context
def create_spec_error(
    error_type: type, message: str, **context_kwargs: Any
) -> SpecError:
    """Create a spec error with context information."""
    if not issubclass(error_type, SpecError):
        raise ValueError(
            f"error_type must be a subclass of SpecError, got {error_type}"
        )

    return error_type(message, context=context_kwargs)
