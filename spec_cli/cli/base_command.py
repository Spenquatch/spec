"""Base command class for CLI commands with common functionality."""

from abc import ABC, abstractmethod
from typing import Any

from ..config.settings import SpecSettings, get_settings
from ..exceptions import SpecError
from ..logging.debug import debug_logger
from ..utils.error_handler import ErrorHandler


class BaseCommand(ABC):
    """Base class for all spec CLI commands with common functionality.

    Provides standard initialization, error handling, validation, and logging
    patterns that all commands should follow.
    """

    def __init__(self, settings: SpecSettings | None = None):
        """Initialize base command with settings and error handling.

        Args:
            settings: Optional settings override (defaults to global settings)
        """
        self.settings = settings or get_settings()
        self.error_handler = ErrorHandler(
            {"module": "cli", "component": self.get_command_name()}
        )

        debug_logger.log(
            "INFO",
            f"Initialized {self.__class__.__name__}",
            command=self.get_command_name(),
            root_path=str(self.settings.root_path),
        )

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the command with given arguments.

        Args:
            **kwargs: Command-specific arguments

        Returns:
            Dictionary containing execution results with:
            - success: bool indicating if command succeeded
            - message: str with result message
            - data: Any additional result data (optional)

        Raises:
            SpecError: If command execution fails
        """
        pass

    def validate_arguments(self, **kwargs: Any) -> None:  # noqa: B027
        """Validate command arguments before execution.

        Args:
            **kwargs: Command arguments to validate

        Raises:
            SpecError: If validation fails

        Note:
            Base implementation does minimal validation.
            Subclasses can override for specific validation.
        """
        # Base implementation does minimal validation
        # Subclasses can override for specific validation
        pass

    def validate_repository_state(self, require_initialized: bool = True) -> None:
        """Validate repository state before command execution.

        Args:
            require_initialized: Whether command requires initialized repository

        Raises:
            SpecError: If repository state is invalid
        """
        if require_initialized and not self.settings.is_initialized():
            raise SpecError(
                "Spec repository not initialized. Run 'spec init' first.",
                {"command": self.get_command_name(), "initialized": False},
            )

        # Validate permissions if repository exists
        if self.settings.is_initialized():
            try:
                self.settings.validate_permissions()
            except Exception as e:
                self.error_handler.log_and_raise(
                    e, "repository permission validation", reraise_as=SpecError
                )
                # This should never be reached due to exception being raised
                raise  # pragma: no cover

    def safe_execute(self, **kwargs: Any) -> dict[str, Any]:
        """Safely execute command with error handling and validation.

        Args:
            **kwargs: Command arguments

        Returns:
            Dictionary with execution results

        Raises:
            SpecError: If execution fails
        """
        try:
            # Validate arguments first
            self.validate_arguments(**kwargs)

            # Execute the command
            with debug_logger.timer(f"{self.get_command_name()}_execution"):
                result = self.execute(**kwargs)

            debug_logger.log(
                "INFO",
                f"{self.__class__.__name__} completed successfully",
                success=result.get("success", False),
                command=self.get_command_name(),
            )

            return result

        except SpecError:
            # Re-raise spec errors as-is
            raise
        except Exception as e:
            # Wrap other exceptions as SpecError
            self.error_handler.log_and_raise(
                e,
                f"{self.get_command_name()} execution",
                reraise_as=SpecError,
                command=self.get_command_name(),
            )
            # This should never be reached due to exception being raised
            raise  # pragma: no cover

    def get_command_name(self) -> str:
        """Get the command name for logging and error reporting.

        Returns:
            Command name in lowercase
        """
        return self.__class__.__name__.lower().replace("command", "")

    def create_result(
        self,
        success: bool,
        message: str,
        data: Any | None = None,
        **additional_fields: Any,
    ) -> dict[str, Any]:
        """Create standardized result dictionary.

        Args:
            success: Whether operation succeeded
            message: Result message
            data: Optional result data
            **additional_fields: Additional fields to include

        Returns:
            Standardized result dictionary
        """
        result = {
            "success": success,
            "message": message,
            "command": self.get_command_name(),
        }

        if data is not None:
            result["data"] = data

        result.update(additional_fields)
        return result
