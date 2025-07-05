"""Cross-slice compatibility test for P1.1b SpecContext with P1.2a factory patterns.

Tests validate that SpecContext implementation is compatible with factory interface
requirements and dependency injection patterns.
"""

from pathlib import Path
from typing import Protocol

import pytest

from spec_cli.core.context import (
    SpecConsoleInterface,
    SpecContext,
    SpecProgressInterface,
    SpecSettingsInterface,
)


# Factory interface pattern (simulating P1.2a requirements)
class FactoryInterface(Protocol):
    """Factory interface for creating SpecContext instances."""

    def create_context(self, **kwargs) -> SpecContext:
        """Create context instance with dependency injection."""
        ...

    def create_dev_context(self) -> SpecContext:
        """Create development context with debug settings."""
        ...

    def create_test_context(self) -> SpecContext:
        """Create test context with mock dependencies."""
        ...


# Mock factory implementation to test compatibility
class MockSpecContextFactory:
    """Mock factory implementation for testing SpecContext compatibility."""

    def create_context(self, **kwargs) -> SpecContext:
        """Create context instance with dependency injection."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        # Apply overrides from kwargs
        for key, value in kwargs.items():
            if hasattr(settings, key):
                setattr(settings, key, value)

        return SpecContext(
            settings=settings,
            console=console,
            progress=progress
        )

    def create_dev_context(self) -> SpecContext:
        """Create development context with debug settings."""
        settings = SpecSettingsInterface()
        settings.debug_enabled = True
        settings.console_width = 120

        return SpecContext(
            settings=settings,
            console=SpecConsoleInterface(),
            progress=SpecProgressInterface()
        )

    def create_test_context(self) -> SpecContext:
        """Create test context with mock dependencies."""
        settings = SpecSettingsInterface()
        settings.debug_enabled = False
        settings.root_path = Path("/test")

        return SpecContext(
            settings=settings,
            console=SpecConsoleInterface(),
            progress=SpecProgressInterface()
        )


class TestSpecContextFactoryCompatibility:
    """Test SpecContext compatibility with factory patterns."""

    def test_spec_context_factory_interface_when_compatible_then_creates_contexts(self):
        """Test SpecContext works with factory interface patterns."""
        factory = MockSpecContextFactory()

        # Test factory interface compliance
        assert hasattr(factory, "create_context")
        assert hasattr(factory, "create_dev_context")
        assert hasattr(factory, "create_test_context")

        # Test basic context creation
        context = factory.create_context()
        assert isinstance(context, SpecContext)
        assert context.settings is not None
        assert context.console is not None
        assert context.progress is not None

    def test_spec_context_factory_when_dependency_injection_then_applies_overrides(self):
        """Test SpecContext supports dependency injection via factory."""
        factory = MockSpecContextFactory()

        # Test dependency injection with overrides
        context = factory.create_context(
            debug_enabled=True,
            console_width=100,
            use_color=False
        )

        assert context.settings.debug_enabled is True
        assert context.settings.console_width == 100
        assert context.settings.use_color is False

    def test_spec_context_factory_when_dev_environment_then_creates_dev_context(self):
        """Test SpecContext factory creates development contexts."""
        factory = MockSpecContextFactory()

        dev_context = factory.create_dev_context()

        assert isinstance(dev_context, SpecContext)
        assert dev_context.settings.debug_enabled is True
        assert dev_context.settings.console_width == 120

    def test_spec_context_factory_when_test_environment_then_creates_test_context(self):
        """Test SpecContext factory creates test contexts."""
        factory = MockSpecContextFactory()

        test_context = factory.create_test_context()

        assert isinstance(test_context, SpecContext)
        assert test_context.settings.debug_enabled is False
        assert test_context.settings.root_path == Path("/test")

    def test_spec_context_factory_when_immutability_then_preserves_frozen_behavior(self):
        """Test factory-created SpecContext maintains immutability."""
        factory = MockSpecContextFactory()

        context = factory.create_context()

        # Verify immutability is preserved
        with pytest.raises(AttributeError):
            context.settings = SpecSettingsInterface()  # type: ignore

        with pytest.raises(AttributeError):
            context.console = SpecConsoleInterface()  # type: ignore

    def test_spec_context_factory_when_modification_methods_then_works_with_factory_patterns(self):
        """Test SpecContext modification methods work with factory patterns."""
        factory = MockSpecContextFactory()

        base_context = factory.create_dev_context()

        # Test modification methods preserve factory compatibility
        modified_context = base_context.with_settings(debug_enabled=False)

        assert modified_context.settings.debug_enabled is False
        assert base_context.settings.debug_enabled is True  # Original preserved

        # Test that modified context maintains all required attributes
        assert hasattr(modified_context, "settings")
        assert hasattr(modified_context, "console")
        assert hasattr(modified_context, "progress")

    def test_spec_context_factory_when_hash_equality_then_supports_comparison(self):
        """Test factory-created SpecContext supports hash/equality for caching."""
        factory = MockSpecContextFactory()

        # Create contexts with shared dependencies for equality testing
        shared_settings = SpecSettingsInterface()
        shared_settings.debug_enabled = False
        shared_settings.root_path = Path("/test")

        shared_console = SpecConsoleInterface()
        shared_progress = SpecProgressInterface()

        context1 = SpecContext(
            settings=shared_settings,
            console=shared_console,
            progress=shared_progress
        )

        context2 = SpecContext(
            settings=shared_settings,
            console=shared_console,
            progress=shared_progress
        )

        # Test equality for identical shared dependencies
        assert context1 == context2

        # Test hash consistency for caching
        hash1 = context1.get_context_hash()
        hash2 = context2.get_context_hash()
        assert hash1 == hash2

        # Test different contexts have different hashes
        dev_context = factory.create_dev_context()
        dev_hash = dev_context.get_context_hash()
        assert hash1 != dev_hash
