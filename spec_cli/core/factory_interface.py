"""Factory interface definition for context creation patterns.

This module defines the abstract factory interface for creating contexts
in different environments (CLI, testing) without depending on specific
SpecContext implementations.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, TypeVar

from typing_extensions import Protocol

from ..core.context_bridge import debug_logger


class FactoryInterfaceError(Exception):
    """Exception raised for factory interface related errors.

    This exception is raised when factory interface validation fails,
    required methods are not implemented, or factory creation encounters
    errors that prevent proper context instantiation.
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize factory interface error with context.

        Args:
            message: Error description
            context: Additional error context for debugging
        """
        super().__init__(message)
        self.context = context or {}
        debug_logger.log(
            "ERROR",
            "Factory interface error raised",
            error_message=message,
            context=self.context,
        )


# Type variable for context types created by factories
ContextType = TypeVar("ContextType")


@dataclass(frozen=True)
class FactoryConfig:
    """Configuration for factory creation and behavior.

    Encapsulates factory configuration parameters including environment
    settings, debugging options, and factory-specific configurations.
    """

    factory_type: str
    environment: str = "unknown"
    debug_mode: bool = False
    timeout: int = 30
    factory_config: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        """Validate factory configuration after initialization."""
        if self.factory_config is None:
            # Use object.__setattr__ because dataclass is frozen
            object.__setattr__(self, "factory_config", {})

        debug_logger.log(
            "DEBUG",
            "Factory config initialized",
            factory_type=self.factory_type,
            environment=self.environment,
            debug_mode=self.debug_mode,
            timeout=self.timeout,
            config_keys=list(self.factory_config.keys()) if self.factory_config else [],
        )


class ContextFactory(Protocol):
    """Protocol defining the interface for context factories.

    This protocol defines the contract that all context factory implementations
    must follow, enabling different factory types while maintaining consistent
    interfaces for context creation.
    """

    def create_context(self, config: FactoryConfig) -> Any:
        """Create a context instance with the given configuration.

        Args:
            config: Factory configuration for context creation

        Returns:
            Created context instance

        Raises:
            FactoryInterfaceError: If context creation fails
        """
        ...

    def validate_config(self, config: FactoryConfig) -> bool:
        """Validate factory configuration for context creation.

        Args:
            config: Factory configuration to validate

        Returns:
            True if configuration is valid for this factory

        Raises:
            FactoryInterfaceError: If configuration validation fails
        """
        ...

    def supports_environment(self, environment: str) -> bool:
        """Check if factory supports the specified environment.

        Args:
            environment: Environment type to check support for

        Returns:
            True if factory supports the environment
        """
        ...


class AbstractContextFactory(ABC):
    """Abstract base class for context factory implementations.

    Provides a concrete base implementation for the ContextFactory protocol
    with common functionality and enforced abstract methods for specific
    factory implementations.
    """

    def __init__(self, factory_type: str) -> None:
        """Initialize abstract context factory.

        Args:
            factory_type: Type identifier for this factory

        Raises:
            FactoryInterfaceError: If factory_type is invalid
        """
        if not isinstance(factory_type, str) or not factory_type.strip():
            raise FactoryInterfaceError(
                "Factory type must be non-empty string",
                {"provided_type": type(factory_type), "value": factory_type},
            )

        self.factory_type = factory_type.strip().lower()
        debug_logger.log(
            "DEBUG",
            "Abstract context factory initialized",
            factory_type=self.factory_type,
        )

    @abstractmethod
    def create_context(self, config: FactoryConfig) -> Any:
        """Create a context instance with the given configuration.

        Abstract method that must be implemented by concrete factory classes
        to define specific context creation logic.

        Args:
            config: Factory configuration for context creation

        Returns:
            Created context instance

        Raises:
            FactoryInterfaceError: If context creation fails
        """

    @abstractmethod
    def validate_config(self, config: FactoryConfig) -> bool:
        """Validate factory configuration for context creation.

        Abstract method that must be implemented by concrete factory classes
        to define configuration validation logic.

        Args:
            config: Factory configuration to validate

        Returns:
            True if configuration is valid for this factory

        Raises:
            FactoryInterfaceError: If configuration validation fails
        """

    def supports_environment(self, environment: str) -> bool:
        """Check if factory supports the specified environment.

        Default implementation supports all environments. Override in
        subclasses to restrict environment support.

        Args:
            environment: Environment type to check support for

        Returns:
            True if factory supports the environment
        """
        debug_logger.log(
            "DEBUG",
            "Environment support check",
            factory_type=self.factory_type,
            environment=environment,
            supports=True,
        )
        return True

    def _validate_common_config(self, config: FactoryConfig) -> None:
        """Validate common configuration parameters.

        Helper method for concrete implementations to validate standard
        configuration parameters before specific validation.

        Args:
            config: Factory configuration to validate

        Raises:
            FactoryInterfaceError: If common configuration is invalid
        """
        if not isinstance(config, FactoryConfig):
            raise FactoryInterfaceError(
                "Config must be FactoryConfig instance",
                {"provided_type": type(config)},
            )

        if config.timeout <= 0:
            raise FactoryInterfaceError(
                "Timeout must be positive",
                {"timeout": config.timeout},
            )

        if not isinstance(config.factory_config, dict):
            raise FactoryInterfaceError(
                "Factory config must be dict",
                {"config_type": type(config.factory_config)},
            )

        debug_logger.log(
            "DEBUG",
            "Common config validation passed",
            factory_type=self.factory_type,
            config_type=config.factory_type,
            environment=config.environment,
        )


class FactoryRegistry:
    """Registry for managing factory implementations by type and environment.

    Provides centralized factory registration and lookup functionality
    for different factory types and execution environments.
    """

    def __init__(self) -> None:
        """Initialize empty factory registry."""
        self._factories: dict[str, dict[str, ContextFactory]] = {}
        debug_logger.log("DEBUG", "Factory registry initialized")

    def register_factory(
        self,
        factory_type: str,
        environment: str,
        factory: ContextFactory,
    ) -> None:
        """Register a factory for specific type and environment.

        Args:
            factory_type: Type of factory (e.g., "context", "config")
            environment: Environment this factory supports
            factory: Factory implementation to register

        Raises:
            FactoryInterfaceError: If registration parameters are invalid
        """
        if not factory_type or not environment:
            raise FactoryInterfaceError(
                "Factory type and environment must be non-empty",
                {"factory_type": factory_type, "environment": environment},
            )

        if factory_type not in self._factories:
            self._factories[factory_type] = {}

        self._factories[factory_type][environment] = factory
        debug_logger.log(
            "DEBUG",
            "Factory registered",
            factory_type=factory_type,
            environment=environment,
            factory_class=type(factory).__name__,
        )

    def get_factory(self, factory_type: str, environment: str) -> ContextFactory:
        """Get registered factory for type and environment.

        Args:
            factory_type: Type of factory to retrieve
            environment: Environment the factory should support

        Returns:
            Registered factory instance

        Raises:
            FactoryInterfaceError: If no factory registered for type/environment
        """
        if factory_type not in self._factories:
            raise FactoryInterfaceError(
                f"No factories registered for type: {factory_type}",
                {"available_types": list(self._factories.keys())},
            )

        if environment not in self._factories[factory_type]:
            raise FactoryInterfaceError(
                f"No factory for environment: {environment}",
                {
                    "factory_type": factory_type,
                    "available_environments": list(
                        self._factories[factory_type].keys()
                    ),
                },
            )

        factory = self._factories[factory_type][environment]
        debug_logger.log(
            "DEBUG",
            "Factory retrieved",
            factory_type=factory_type,
            environment=environment,
            factory_class=type(factory).__name__,
        )
        return factory

    def list_available_factories(self) -> dict[str, list[str]]:
        """List all registered factories by type and environment.

        Returns:
            Dictionary mapping factory types to list of supported environments
        """
        available = {
            factory_type: list(environments.keys())
            for factory_type, environments in self._factories.items()
        }
        debug_logger.log(
            "DEBUG",
            "Listed available factories",
            factory_count=len(available),
            available_factories=available,
        )
        return available
