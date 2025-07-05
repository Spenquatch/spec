"""Integration tests for slice P1.2a factory interface definition."""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from spec_cli.core.factory_interface import (
    AbstractContextFactory,
    FactoryConfig,
    FactoryInterfaceError,
    FactoryRegistry,
)
from spec_cli.utils.factory_utils import (
    detect_environment_type,
    validate_factory_inputs,
)


class TestFactoryInterfaceIntegration:
    """Integration tests for factory interface with environment detection."""

    def test_factory_interface_integration_when_environment_detection_then_supports_context_creation_patterns(self):
        """End-to-end test validating factory interface supports both CLI and testing context creation."""
        # Test 1: Environment detection integration
        with patch.dict(os.environ, {"SPEC_ENV": "testing"}):
            env_type = detect_environment_type()
            assert env_type == "testing"

        # Test 2: Factory input validation integration
        factory_inputs = {
            "factory_type": "context",
            "timeout": 45,
            "debug_mode": True,
            "factory_config": {"environment": env_type}
        }
        validated_inputs = validate_factory_inputs(**factory_inputs)

        assert validated_inputs["factory_type"] == "context"
        assert validated_inputs["timeout"] == 45
        assert validated_inputs["debug_mode"] is True
        assert validated_inputs["factory_config"]["environment"] == "testing"

        # Test 3: Factory config creation integration
        config = FactoryConfig(
            factory_type=validated_inputs["factory_type"],
            environment=env_type,
            debug_mode=validated_inputs["debug_mode"],
            timeout=validated_inputs["timeout"],
            factory_config=validated_inputs["factory_config"]
        )

        assert config.factory_type == "context"
        assert config.environment == "testing"
        assert config.debug_mode is True
        assert config.timeout == 45

        # Test 4: Factory interface implementation integration
        class TestContextFactory(AbstractContextFactory):
            def create_context(self, config: FactoryConfig):
                return {
                    "context_type": "test",
                    "environment": config.environment,
                    "factory_type": config.factory_type,
                    "debug": config.debug_mode
                }

            def validate_config(self, config: FactoryConfig) -> bool:
                self._validate_common_config(config)
                return config.factory_type == "context"

        factory = TestContextFactory("test_context")
        assert factory.supports_environment("testing") is True
        assert factory.validate_config(config) is True

        # Test 5: Context creation integration
        context = factory.create_context(config)
        assert context["context_type"] == "test"
        assert context["environment"] == "testing"
        assert context["factory_type"] == "context"
        assert context["debug"] is True

        # Test 6: Factory registry integration
        registry = FactoryRegistry()
        registry.register_factory("context", "testing", factory)

        retrieved_factory = registry.get_factory("context", "testing")
        assert retrieved_factory is factory

        # Test 7: End-to-end workflow integration
        new_config = FactoryConfig(
            factory_type="context",
            environment="testing",
            debug_mode=False,
            timeout=30
        )

        retrieved_factory = registry.get_factory("context", "testing")
        assert retrieved_factory.validate_config(new_config) is True

        new_context = retrieved_factory.create_context(new_config)
        assert new_context["context_type"] == "test"
        assert new_context["environment"] == "testing"
        assert new_context["debug"] is False

    def test_factory_interface_cli_environment_integration_when_cli_detection_then_creates_cli_context(self):
        """Test factory interface with CLI environment detection."""
        # Simulate CLI environment
        mock_frame = MagicMock()
        mock_frame.f_code.co_filename = "/path/to/spec_cli/cli.py"
        mock_frame.f_back = None

        with (
            patch("spec_cli.utils.factory_utils.inspect.currentframe", return_value=mock_frame),
            patch.dict(os.environ, {}, clear=True),
            patch.object(sys, "argv", ["spec", "init"]),
        ):
            # Remove pytest from modules temporarily if present
            pytest_module = sys.modules.pop("pytest", None)
            try:
                env_type = detect_environment_type()
                assert env_type == "cli"

                # Create factory config for CLI environment
                factory_inputs = validate_factory_inputs(
                    factory_type="context",
                    timeout=30,
                    debug_mode=False,
                    factory_config={"cli_mode": True}
                )

                config = FactoryConfig(
                    factory_type=factory_inputs["factory_type"],
                    environment=env_type,
                    debug_mode=factory_inputs["debug_mode"],
                    timeout=factory_inputs["timeout"],
                    factory_config=factory_inputs["factory_config"]
                )

                # Create CLI-specific factory
                class CLIContextFactory(AbstractContextFactory):
                    def create_context(self, config: FactoryConfig):
                        return {
                            "context_type": "cli",
                            "environment": config.environment,
                            "cli_mode": config.factory_config.get("cli_mode", False)
                        }

                    def validate_config(self, config: FactoryConfig) -> bool:
                        self._validate_common_config(config)
                        return config.environment == "cli"

                    def supports_environment(self, environment: str) -> bool:
                        return environment == "cli"

                factory = CLIContextFactory("cli_context")
                assert factory.supports_environment("cli") is True
                assert factory.supports_environment("testing") is False
                assert factory.validate_config(config) is True

                context = factory.create_context(config)
                assert context["context_type"] == "cli"
                assert context["environment"] == "cli"
                assert context["cli_mode"] is True

            finally:
                if pytest_module:
                    sys.modules["pytest"] = pytest_module

    def test_factory_interface_error_handling_integration_when_invalid_flow_then_raises_appropriate_errors(self):
        """Test integrated error handling across factory interface components."""
        # Test 1: Invalid factory input validation
        with pytest.raises(ValueError, match="factory_type cannot be empty"):
            validate_factory_inputs(factory_type="")

        with pytest.raises(ValueError, match="timeout must be positive"):
            validate_factory_inputs(timeout=-1)

        # Test 2: Invalid factory config
        with pytest.raises(FactoryInterfaceError, match="Factory type must be non-empty string"):
            class TestFactory(AbstractContextFactory):
                def create_context(self, config):
                    return {}
                def validate_config(self, config):
                    return True
            TestFactory("")

        # Test 3: Invalid common config validation
        class ValidatingFactory(AbstractContextFactory):
            def create_context(self, config):
                return {}
            def validate_config(self, config):
                self._validate_common_config(config)
                return True

        factory = ValidatingFactory("test")
        invalid_config = FactoryConfig(factory_type="test", timeout=0)

        with pytest.raises(FactoryInterfaceError, match="Timeout must be positive"):
            factory.validate_config(invalid_config)

        # Test 4: Registry error handling
        registry = FactoryRegistry()

        with pytest.raises(FactoryInterfaceError, match="No factories registered for type"):
            registry.get_factory("nonexistent", "cli")

        # Register a factory and test environment error
        mock_factory = MagicMock()
        registry.register_factory("context", "cli", mock_factory)

        with pytest.raises(FactoryInterfaceError, match="No factory for environment"):
            registry.get_factory("context", "nonexistent")

    def test_factory_interface_cross_environment_integration_when_multiple_environments_then_manages_correctly(self):
        """Test factory interface managing multiple environments simultaneously."""
        registry = FactoryRegistry()

        # Create different factories for different environments
        class TestingFactory(AbstractContextFactory):
            def create_context(self, config):
                return {"type": "testing", "env": config.environment}
            def validate_config(self, config):
                self._validate_common_config(config)
                return True
            def supports_environment(self, environment):
                return environment == "testing"

        class CLIFactory(AbstractContextFactory):
            def create_context(self, config):
                return {"type": "cli", "env": config.environment}
            def validate_config(self, config):
                self._validate_common_config(config)
                return True
            def supports_environment(self, environment):
                return environment == "cli"

        testing_factory = TestingFactory("testing_context")
        cli_factory = CLIFactory("cli_context")

        # Register both factories
        registry.register_factory("context", "testing", testing_factory)
        registry.register_factory("context", "cli", cli_factory)

        # Test environment-specific retrieval
        retrieved_testing = registry.get_factory("context", "testing")
        retrieved_cli = registry.get_factory("context", "cli")

        assert retrieved_testing is testing_factory
        assert retrieved_cli is cli_factory

        # Test environment-specific behavior
        testing_config = FactoryConfig(factory_type="context", environment="testing")
        cli_config = FactoryConfig(factory_type="context", environment="cli")

        testing_context = retrieved_testing.create_context(testing_config)
        cli_context = retrieved_cli.create_context(cli_config)

        assert testing_context["type"] == "testing"
        assert testing_context["env"] == "testing"
        assert cli_context["type"] == "cli"
        assert cli_context["env"] == "cli"

        # Test environment support checks
        assert testing_factory.supports_environment("testing") is True
        assert testing_factory.supports_environment("cli") is False
        assert cli_factory.supports_environment("cli") is True
        assert cli_factory.supports_environment("testing") is False

        # Test registry listing
        available = registry.list_available_factories()
        assert "context" in available
        assert set(available["context"]) == {"testing", "cli"}

    def test_factory_interface_p1_1b_compatibility_when_spec_context_requirements_then_validates_interface_support(self):
        """Test factory interface supports SpecContext from P1.1b requirements."""
        # This test validates that the factory interface can support the creation
        # of SpecContext objects as defined in P1.1b, ensuring cross-slice compatibility

        # Test 1: Factory config supports SpecContext creation parameters
        spec_context_inputs = validate_factory_inputs(
            factory_type="spec_context",
            timeout=30,
            debug_mode=True,
            factory_config={
                "project_root": "/path/to/project",
                "config_file": "spec.config",
                "git_integration": True
            }
        )

        assert spec_context_inputs["factory_type"] == "spec_context"
        assert spec_context_inputs["factory_config"]["project_root"] == "/path/to/project"
        assert spec_context_inputs["factory_config"]["git_integration"] is True

        # Test 2: Factory config creation for SpecContext
        config = FactoryConfig(
            factory_type="spec_context",
            environment="testing",
            debug_mode=True,
            timeout=30,
            factory_config=spec_context_inputs["factory_config"]
        )

        assert config.factory_type == "spec_context"
        assert config.factory_config["project_root"] == "/path/to/project"

        # Test 3: Mock SpecContext factory interface compatibility
        class MockSpecContextFactory(AbstractContextFactory):
            def create_context(self, config: FactoryConfig):
                # Mock SpecContext creation compatible with P1.1b
                return {
                    "context_id": "mock_spec_context",
                    "project_root": config.factory_config.get("project_root"),
                    "environment": config.environment,
                    "git_integration": config.factory_config.get("git_integration", False),
                    "debug_mode": config.debug_mode
                }

            def validate_config(self, config: FactoryConfig) -> bool:
                self._validate_common_config(config)
                required_keys = ["project_root"]
                return all(
                    key in config.factory_config
                    for key in required_keys
                )

        factory = MockSpecContextFactory("spec_context")
        assert factory.validate_config(config) is True

        # Test 4: Context creation compatible with P1.1b patterns
        mock_spec_context = factory.create_context(config)

        assert mock_spec_context["context_id"] == "mock_spec_context"
        assert mock_spec_context["project_root"] == "/path/to/project"
        assert mock_spec_context["environment"] == "testing"
        assert mock_spec_context["git_integration"] is True
        assert mock_spec_context["debug_mode"] is True

        # Test 5: Registry supports SpecContext factory patterns
        registry = FactoryRegistry()
        registry.register_factory("spec_context", "testing", factory)
        registry.register_factory("spec_context", "cli", factory)

        available = registry.list_available_factories()
        assert "spec_context" in available
        assert set(available["spec_context"]) == {"testing", "cli"}

        # Verify retrieval and usage
        retrieved_factory = registry.get_factory("spec_context", "testing")
        test_context = retrieved_factory.create_context(config)
        assert test_context["context_id"] == "mock_spec_context"
