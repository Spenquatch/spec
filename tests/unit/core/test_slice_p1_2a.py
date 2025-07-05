"""Unit tests for slice P1.2a factory interface definition."""

from unittest.mock import MagicMock

import pytest

from spec_cli.core.factory_interface import (
    AbstractContextFactory,
    ContextFactory,
    FactoryConfig,
    FactoryInterfaceError,
    FactoryRegistry,
)


class TestFactoryInterfaceError:
    """Test factory interface error handling."""

    def test_factory_interface_error_when_invalid_interface_then_raises_specific_error(
        self,
    ):
        """Test error handling for invalid factory interface usage."""
        context = {"factory_type": "invalid", "reason": "missing_method"}
        error = FactoryInterfaceError("Factory interface validation failed", context)

        assert str(error) == "Factory interface validation failed"
        assert error.context == context
        assert error.context["factory_type"] == "invalid"

    def test_factory_interface_error_when_no_context_then_uses_empty_dict(self):
        """Test error handling with no context uses empty dict."""
        error = FactoryInterfaceError("Simple error message")
        assert error.context == {}


class TestFactoryConfig:
    """Test factory configuration data class."""

    def test_factory_config_when_minimal_args_then_creates_with_defaults(self):
        """Test factory config creation with minimal arguments."""
        config = FactoryConfig(factory_type="context")

        assert config.factory_type == "context"
        assert config.environment == "unknown"
        assert config.debug_mode is False
        assert config.timeout == 30
        assert config.factory_config == {}

    def test_factory_config_when_all_args_then_creates_correctly(self):
        """Test factory config creation with all arguments."""
        factory_config = {"key": "value", "nested": {"inner": "data"}}
        config = FactoryConfig(
            factory_type="test_context",
            environment="testing",
            debug_mode=True,
            timeout=60,
            factory_config=factory_config,
        )

        assert config.factory_type == "test_context"
        assert config.environment == "testing"
        assert config.debug_mode is True
        assert config.timeout == 60
        assert config.factory_config == factory_config

    def test_factory_config_when_none_factory_config_then_initializes_empty_dict(self):
        """Test factory config with None factory_config initializes empty dict."""
        config = FactoryConfig(factory_type="context", factory_config=None)
        assert config.factory_config == {}

    def test_factory_config_when_frozen_dataclass_then_immutable(self):
        """Test factory config is immutable due to frozen=True."""
        config = FactoryConfig(factory_type="context")

        with pytest.raises(AttributeError):
            config.factory_type = "modified"

        with pytest.raises(AttributeError):
            config.timeout = 100


class TestAbstractContextFactory:
    """Test abstract context factory base class."""

    def test_abstract_context_factory_when_valid_type_then_initializes(self):
        """Test abstract factory initialization with valid type."""

        # Create concrete implementation for testing
        class TestFactory(AbstractContextFactory):
            def create_context(self, config):
                return {"context": "test"}

            def validate_config(self, config):
                return True

        factory = TestFactory("test_factory")
        assert factory.factory_type == "test_factory"

    def test_abstract_context_factory_when_type_normalization_then_strips_and_lowers(
        self,
    ):
        """Test factory type normalization strips whitespace and converts to lowercase."""

        class TestFactory(AbstractContextFactory):
            def create_context(self, config):
                return {"context": "test"}

            def validate_config(self, config):
                return True

        factory = TestFactory("  TEST_FACTORY  ")
        assert factory.factory_type == "test_factory"

    def test_abstract_context_factory_when_invalid_type_then_raises_error(self):
        """Test abstract factory raises error for invalid factory type."""

        class TestFactory(AbstractContextFactory):
            def create_context(self, config):
                return {"context": "test"}

            def validate_config(self, config):
                return True

        with pytest.raises(
            FactoryInterfaceError, match="Factory type must be non-empty string"
        ):
            TestFactory("")

        with pytest.raises(
            FactoryInterfaceError, match="Factory type must be non-empty string"
        ):
            TestFactory("   ")

        with pytest.raises(
            FactoryInterfaceError, match="Factory type must be non-empty string"
        ):
            TestFactory(123)

    def test_abstract_context_factory_when_environment_support_then_returns_true_by_default(
        self,
    ):
        """Test default environment support returns True."""

        class TestFactory(AbstractContextFactory):
            def create_context(self, config):
                return {"context": "test"}

            def validate_config(self, config):
                return True

        factory = TestFactory("test")
        assert factory.supports_environment("cli") is True
        assert factory.supports_environment("testing") is True
        assert factory.supports_environment("unknown") is True

    def test_abstract_context_factory_when_common_config_validation_then_validates_correctly(
        self,
    ):
        """Test common configuration validation helper."""

        class TestFactory(AbstractContextFactory):
            def create_context(self, config):
                return {"context": "test"}

            def validate_config(self, config):
                self._validate_common_config(config)
                return True

        factory = TestFactory("test")
        valid_config = FactoryConfig(factory_type="test", timeout=30)

        # Should not raise exception
        assert factory.validate_config(valid_config) is True

    def test_abstract_context_factory_when_invalid_common_config_then_raises_error(
        self,
    ):
        """Test common configuration validation with invalid config."""

        class TestFactory(AbstractContextFactory):
            def create_context(self, config):
                return {"context": "test"}

            def validate_config(self, config):
                self._validate_common_config(config)
                return True

        factory = TestFactory("test")

        # Test invalid config type
        with pytest.raises(
            FactoryInterfaceError, match="Config must be FactoryConfig instance"
        ):
            factory.validate_config({"not": "config"})

        # Test invalid timeout
        invalid_config = FactoryConfig(factory_type="test", timeout=0)
        with pytest.raises(FactoryInterfaceError, match="Timeout must be positive"):
            factory.validate_config(invalid_config)

        # Test invalid factory_config type
        config = FactoryConfig(factory_type="test")
        # Modify the factory_config to invalid type using object.__setattr__
        object.__setattr__(config, "factory_config", "not_a_dict")
        with pytest.raises(FactoryInterfaceError, match="Factory config must be dict"):
            factory.validate_config(config)

    def test_abstract_context_factory_when_abstract_methods_then_defines_complete_contract(
        self,
    ):
        """Test abstract factory interface defines all required methods."""
        # Test that abstract methods are properly defined
        assert hasattr(AbstractContextFactory, "create_context")
        assert hasattr(AbstractContextFactory, "validate_config")

        # Test that incomplete implementation raises TypeError
        with pytest.raises(TypeError):

            class IncompleteFactory(AbstractContextFactory):
                pass  # Missing abstract method implementations

            IncompleteFactory("incomplete")


class TestFactoryRegistry:
    """Test factory registry functionality."""

    def test_factory_registry_when_initialized_then_empty(self):
        """Test factory registry initializes empty."""
        registry = FactoryRegistry()
        available = registry.list_available_factories()
        assert available == {}

    def test_factory_registry_when_register_factory_then_stores_correctly(self):
        """Test factory registration stores factory correctly."""
        registry = FactoryRegistry()
        mock_factory = MagicMock(spec=ContextFactory)

        registry.register_factory("context", "cli", mock_factory)

        retrieved = registry.get_factory("context", "cli")
        assert retrieved is mock_factory

    def test_factory_registry_when_multiple_factories_then_manages_independently(self):
        """Test registry manages multiple factories independently."""
        registry = FactoryRegistry()
        cli_factory = MagicMock(spec=ContextFactory)
        test_factory = MagicMock(spec=ContextFactory)

        registry.register_factory("context", "cli", cli_factory)
        registry.register_factory("context", "testing", test_factory)

        assert registry.get_factory("context", "cli") is cli_factory
        assert registry.get_factory("context", "testing") is test_factory

    def test_factory_registry_when_register_invalid_params_then_raises_error(self):
        """Test factory registration with invalid parameters raises error."""
        registry = FactoryRegistry()
        mock_factory = MagicMock(spec=ContextFactory)

        with pytest.raises(
            FactoryInterfaceError,
            match="Factory type and environment must be non-empty",
        ):
            registry.register_factory("", "cli", mock_factory)

        with pytest.raises(
            FactoryInterfaceError,
            match="Factory type and environment must be non-empty",
        ):
            registry.register_factory("context", "", mock_factory)

    def test_factory_registry_when_get_nonexistent_type_then_raises_error(self):
        """Test getting non-existent factory type raises error."""
        registry = FactoryRegistry()

        with pytest.raises(
            FactoryInterfaceError, match="No factories registered for type: nonexistent"
        ):
            registry.get_factory("nonexistent", "cli")

    def test_factory_registry_when_get_nonexistent_environment_then_raises_error(self):
        """Test getting non-existent environment raises error."""
        registry = FactoryRegistry()
        mock_factory = MagicMock(spec=ContextFactory)
        registry.register_factory("context", "cli", mock_factory)

        with pytest.raises(
            FactoryInterfaceError, match="No factory for environment: nonexistent"
        ):
            registry.get_factory("context", "nonexistent")

    def test_factory_registry_when_list_available_then_returns_complete_mapping(self):
        """Test listing available factories returns complete mapping."""
        registry = FactoryRegistry()
        cli_factory = MagicMock(spec=ContextFactory)
        test_factory = MagicMock(spec=ContextFactory)
        config_factory = MagicMock(spec=ContextFactory)

        registry.register_factory("context", "cli", cli_factory)
        registry.register_factory("context", "testing", test_factory)
        registry.register_factory("config", "cli", config_factory)

        available = registry.list_available_factories()

        expected = {"context": ["cli", "testing"], "config": ["cli"]}

        assert available == expected

    def test_factory_registry_when_overwrite_registration_then_replaces_factory(self):
        """Test overwriting factory registration replaces previous factory."""
        registry = FactoryRegistry()
        old_factory = MagicMock(spec=ContextFactory)
        new_factory = MagicMock(spec=ContextFactory)

        registry.register_factory("context", "cli", old_factory)
        registry.register_factory("context", "cli", new_factory)

        retrieved = registry.get_factory("context", "cli")
        assert retrieved is new_factory
        assert retrieved is not old_factory
