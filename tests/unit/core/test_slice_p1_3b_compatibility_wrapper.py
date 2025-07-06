"""Unit tests for compatibility wrapper implementation - P1.3b slice.

This module tests the compatibility layer that bridges singleton patterns
with dependency injection, ensuring transparent access and backward compatibility.

Target Coverage: 100% line coverage for compatibility wrapper implementation
Test Types: unit compatibility
Priority: High
"""

import threading
from unittest.mock import Mock, patch

import pytest

# DEPRECATED: Compatibility layer was removed as part of singleton elimination (P3.2a)
# These tests need to be updated to test context-based patterns instead
# from spec_cli.core.compatibility import (
#     CompatibilityLayer,
#     ProgressManagerWrapper,
#     compatibility_layer,
#     get_progress_manager_compatibility,
# )
from spec_cli.exceptions import CompatibilityError
from spec_cli.utils.compatibility_utils import (
    SingletonCompatibilityWrapper,
    _get_default_context_key,
    create_singleton_wrapper,
    validate_wrapper_behavior,
)

# Test constants to avoid magic numbers
DEFAULT_CONTEXT_KEY = "test_context"
WRAPPER_KEY = "progress_manager"
MOCK_SINGLETON_NAME = "MockSingleton"
MOCK_ATTRIBUTE_NAME = "test_attribute"
MOCK_ATTRIBUTE_VALUE = "test_value"
MOCK_METHOD_RETURN = "method_result"
THREAD_COUNT = 5

class TestCompatibilityUtilsWrapperCreation:
    """Test compatibility utils wrapper creation functions."""

    def test_create_singleton_wrapper_when_valid_singleton_class_then_returns_working_wrapper(
        self,
    ):
        """Test wrapper creation for actual singleton classes."""

        # Create actual class for testing (not Mock)
        class TestSingleton:
            def __init__(self):
                pass

        wrapper = create_singleton_wrapper(
            singleton_class=TestSingleton,
            fallback_enabled=True,
            context_key=DEFAULT_CONTEXT_KEY,
        )

        assert wrapper is not None
        assert isinstance(wrapper, SingletonCompatibilityWrapper)
        assert wrapper._singleton_class == TestSingleton
        assert wrapper._fallback_enabled is True
        assert wrapper._context_key == DEFAULT_CONTEXT_KEY

    def test_create_singleton_wrapper_when_invalid_class_type_then_raises_type_error(
        self,
    ):
        """Test wrapper creation with invalid class type."""
        with pytest.raises(TypeError, match="Expected class type"):
            create_singleton_wrapper("not_a_class")

    def test_create_singleton_wrapper_when_singleton_creation_fails_then_raises_compatibility_error(
        self,
    ):
        """Test wrapper creation when singleton construction fails."""

        # Create class that raises exception on instantiation
        class FailingSingleton:
            def __init__(self):
                raise Exception("Singleton creation failed")

        # Wrapper creation itself should succeed, but accessing instance should fail
        wrapper = create_singleton_wrapper(FailingSingleton)
        with pytest.raises(
            CompatibilityError, match="Context unavailable and fallback disabled"
        ):
            # Disable fallback to force the error
            wrapper._fallback_enabled = False
            wrapper._get_instance()

class TestCompatibilityUtilsWrapperValidation:
    """Test compatibility utils wrapper validation functions."""

    def test_validate_wrapper_behavior_when_wrapper_created_then_matches_original(self):
        """Test wrapper behavior validation against original singleton."""
        # Create mock original with test methods
        mock_original = Mock()
        mock_original.test_method = Mock(return_value=MOCK_METHOD_RETURN)

        # Create wrapper with same interface
        mock_wrapper = Mock()
        mock_wrapper.test_method = Mock(return_value=MOCK_METHOD_RETURN)

        result = validate_wrapper_behavior(mock_wrapper, mock_original)

        assert result is True

    def test_validate_wrapper_behavior_when_wrapper_missing_methods_then_returns_false(
        self,
    ):
        """Test validation fails when wrapper missing methods."""
        # Original has method, wrapper doesn't
        mock_original = Mock()
        mock_original.important_method = Mock()

        mock_wrapper = Mock(spec=[])  # Empty spec, no methods

        result = validate_wrapper_behavior(mock_wrapper, mock_original)

        assert result is False

    def test_validate_wrapper_behavior_when_none_inputs_then_raises_type_error(self):
        """Test validation with None inputs."""
        with pytest.raises(TypeError, match="cannot be None"):
            validate_wrapper_behavior(None, Mock())

        with pytest.raises(TypeError, match="cannot be None"):
            validate_wrapper_behavior(Mock(), None)

    def test_validate_wrapper_behavior_when_validation_exception_then_returns_false(
        self,
    ):
        """Test validation handles exceptions gracefully."""
        # Create mock that raises exception during dir() call
        mock_original = Mock()
        mock_wrapper = Mock()

        with patch("builtins.dir", side_effect=Exception("Dir failed")):
            result = validate_wrapper_behavior(mock_wrapper, mock_original)

        assert result is False

class TestSingletonCompatibilityWrapper:
    """Test SingletonCompatibilityWrapper class behavior."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_singleton_class = Mock()
        self.mock_singleton_class.__name__ = MOCK_SINGLETON_NAME
        self.mock_instance = Mock()
        self.mock_singleton_class.return_value = self.mock_instance

    def test_singleton_wrapper_transparent_access_when_existing_methods_called_then_preserves_behavior(
        self,
    ):
        """Test wrapper preserves original singleton method behavior."""
        # Setup singleton instance with test method
        self.mock_instance.test_method = Mock(return_value=MOCK_METHOD_RETURN)

        wrapper = SingletonCompatibilityWrapper(
            singleton_class=self.mock_singleton_class, fallback_enabled=True
        )

        # Access method through wrapper
        result = wrapper.test_method()

        assert result == MOCK_METHOD_RETURN
        self.mock_instance.test_method.assert_called_once()

    def test_singleton_wrapper_attribute_access_when_non_callable_then_returns_value(
        self,
    ):
        """Test wrapper returns non-callable attributes directly."""
        # Setup singleton instance with test attribute
        self.mock_instance.test_attribute = MOCK_ATTRIBUTE_VALUE

        wrapper = SingletonCompatibilityWrapper(
            singleton_class=self.mock_singleton_class, fallback_enabled=True
        )

        # Access attribute through wrapper
        result = wrapper.test_attribute

        assert result == MOCK_ATTRIBUTE_VALUE

    def test_singleton_wrapper_when_attribute_missing_then_raises_attribute_error(self):
        """Test wrapper raises AttributeError for missing attributes."""

        # Use a real class without the attribute instead of Mock
        class MinimalSingleton:
            def __init__(self):
                pass

        wrapper = SingletonCompatibilityWrapper(
            singleton_class=MinimalSingleton, fallback_enabled=True
        )

        with pytest.raises(AttributeError, match="has no attribute 'nonexistent'"):
            _ = wrapper.nonexistent

    def test_wrapper_fallback_mechanism_when_context_unavailable_then_uses_singleton(
        self,
    ):
        """Test fallback to singleton when context system unavailable."""
        wrapper = SingletonCompatibilityWrapper(
            singleton_class=self.mock_singleton_class, fallback_enabled=True
        )

        # Access instance should use singleton fallback
        instance = wrapper._get_instance()

        assert instance == self.mock_instance
        self.mock_singleton_class.assert_called_once()

    def test_wrapper_when_fallback_disabled_and_no_context_then_raises_error(self):
        """Test error when fallback disabled and context unavailable."""
        wrapper = SingletonCompatibilityWrapper(
            singleton_class=self.mock_singleton_class, fallback_enabled=False
        )

        with pytest.raises(
            CompatibilityError, match="Context unavailable and fallback disabled"
        ):
            wrapper._get_instance()

    def test_wrapper_reset_when_called_then_clears_cached_instance(self):
        """Test wrapper reset clears cached state."""
        wrapper = SingletonCompatibilityWrapper(
            singleton_class=self.mock_singleton_class, fallback_enabled=True
        )

        # Access instance to cache it
        _ = wrapper._get_instance()
        assert wrapper._cached_instance is not None

        # Reset should clear cache
        wrapper.reset()
        assert wrapper._cached_instance is None

    def test_wrapper_thread_safety_when_concurrent_access_then_single_instance(self):
        """Test wrapper maintains thread safety during concurrent access."""
        wrapper = SingletonCompatibilityWrapper(
            singleton_class=self.mock_singleton_class, fallback_enabled=True
        )

        instances = []

        def get_instance():
            instances.append(wrapper._get_instance())

        # Create multiple threads accessing wrapper
        threads = []
        for _i in range(THREAD_COUNT):
            thread = threading.Thread(target=get_instance)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All instances should be the same (singleton behavior)
        assert len(instances) == THREAD_COUNT
        assert all(instance == instances[0] for instance in instances)
        # Singleton class should only be called once
        assert self.mock_singleton_class.call_count == 1

class TestGetDefaultContextKey:
    """Test context key generation utility."""

    def test_get_default_context_key_when_pascal_case_then_converts_to_snake_case(self):
        """Test PascalCase to snake_case conversion."""
        mock_class = Mock()
        mock_class.__name__ = "ProgressManagerSingleton"

        result = _get_default_context_key(mock_class)

        assert result == "progress_manager_singleton"

    def test_get_default_context_key_when_single_word_then_converts_to_lowercase(self):
        """Test single word conversion."""
        mock_class = Mock()
        mock_class.__name__ = "Manager"

        result = _get_default_context_key(mock_class)

        assert result == "manager"

    def test_get_default_context_key_when_numbers_in_name_then_preserves_numbers(self):
        """Test conversion preserves numbers."""
        mock_class = Mock()
        mock_class.__name__ = "Database2Connection"

        result = _get_default_context_key(mock_class)

        assert result == "database2_connection"

@pytest.mark.skip(reason="CompatibilityLayer removed in P3.2a - singleton elimination complete")
class TestCompatibilityLayer:
    """Test CompatibilityLayer central management."""

    def setup_method(self):
        """Setup test compatibility layer."""
        self.layer = CompatibilityLayer()

    def test_get_progress_manager_wrapper_when_first_call_then_creates_wrapper(self):
        """Test first call creates ProgressManager wrapper."""

        # Create a test class to use as the singleton
        class MockProgressManagerSingleton:
            def __init__(self):
                pass

        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton",
            MockProgressManagerSingleton,
        ):
            wrapper = self.layer.get_progress_manager_wrapper()

            assert wrapper is not None
            assert isinstance(wrapper, ProgressManagerWrapper)
            assert wrapper._singleton_class == MockProgressManagerSingleton

    def test_get_progress_manager_wrapper_when_subsequent_calls_then_returns_cached(
        self,
    ):
        """Test subsequent calls return cached wrapper."""
        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton"
        ) as mock_singleton:
            mock_singleton.__name__ = "ProgressManagerSingleton"

            wrapper1 = self.layer.get_progress_manager_wrapper()
            wrapper2 = self.layer.get_progress_manager_wrapper()

            assert wrapper1 is wrapper2

    def test_get_progress_manager_wrapper_when_import_fails_then_raises_error(self):
        """Test error handling when singleton import fails."""
        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton",
            side_effect=Exception("Import failed"),
        ):
            with pytest.raises(
                CompatibilityError, match="Failed to create ProgressManager wrapper"
            ):
                self.layer.get_progress_manager_wrapper()

    def test_validate_all_wrappers_when_no_wrappers_then_returns_true(self):
        """Test validation with no wrappers created."""
        result = self.layer.validate_all_wrappers()

        assert result is True

    def test_validate_all_wrappers_when_valid_wrappers_then_returns_true(self):
        """Test validation with valid wrappers."""
        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton"
        ) as mock_singleton:
            with patch(
                "spec_cli.core.compatibility.validate_wrapper_behavior",
                return_value=True,
            ) as mock_validate:
                mock_singleton.__name__ = "ProgressManagerSingleton"

                # Create wrapper
                self.layer.get_progress_manager_wrapper()

                # Validate all wrappers
                result = self.layer.validate_all_wrappers()

                assert result is True
                mock_validate.assert_called_once()

    def test_validate_all_wrappers_when_invalid_wrapper_then_returns_false(self):
        """Test validation fails with invalid wrapper."""
        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton"
        ) as mock_singleton:
            with patch(
                "spec_cli.core.compatibility.validate_wrapper_behavior",
                return_value=False,
            ):
                mock_singleton.__name__ = "ProgressManagerSingleton"

                # Create wrapper
                self.layer.get_progress_manager_wrapper()

                # Validate all wrappers
                result = self.layer.validate_all_wrappers()

                assert result is False

    def test_reset_all_wrappers_when_wrappers_exist_then_resets_state(self):
        """Test reset clears all wrapper states."""
        # Create mock wrapper with reset method
        mock_wrapper = Mock()
        mock_wrapper.reset = Mock()

        # Add wrapper to layer
        with self.layer._lock:
            self.layer._wrappers[WRAPPER_KEY] = mock_wrapper

        # Reset all wrappers
        self.layer.reset_all_wrappers()

        # Verify reset was called
        mock_wrapper.reset.assert_called_once()

@pytest.mark.skip(reason="ProgressManagerWrapper removed in P3.2a - singleton elimination complete")
class TestProgressManagerWrapper:
    """Test ProgressManagerWrapper specific functionality."""

    def setup_method(self):
        """Setup test fixtures."""
        self.mock_singleton_class = Mock()
        self.mock_singleton_class.__name__ = "ProgressManagerSingleton"
        self.mock_instance = Mock()
        self.mock_singleton_class.return_value = self.mock_instance
        self.wrapper = ProgressManagerWrapper(self.mock_singleton_class)

    def test_get_progress_manager_when_called_then_delegates_to_singleton(self):
        """Test get_progress_manager delegates to singleton."""
        mock_manager = Mock()
        self.mock_instance.get_progress_manager.return_value = mock_manager

        result = self.wrapper.get_progress_manager()

        assert result == mock_manager
        self.mock_instance.get_progress_manager.assert_called_once()

    def test_get_progress_manager_when_singleton_fails_then_raises_error(self):
        """Test error handling when singleton operation fails."""
        self.mock_instance.get_progress_manager.side_effect = Exception(
            "Singleton failed"
        )

        with pytest.raises(CompatibilityError, match="Failed to get progress manager"):
            self.wrapper.get_progress_manager()

    def test_set_progress_manager_when_called_then_delegates_to_singleton(self):
        """Test set_progress_manager delegates to singleton."""
        mock_manager = Mock()

        self.wrapper.set_progress_manager(mock_manager)

        self.mock_instance.set_progress_manager.assert_called_once_with(mock_manager)

    def test_set_progress_manager_when_singleton_fails_then_raises_error(self):
        """Test error handling when singleton set operation fails."""
        self.mock_instance.set_progress_manager.side_effect = Exception("Set failed")
        mock_manager = Mock()

        with pytest.raises(CompatibilityError, match="Failed to set progress manager"):
            self.wrapper.set_progress_manager(mock_manager)

    def test_reset_progress_manager_when_called_then_resets_singleton_and_cache(self):
        """Test reset clears both wrapper and singleton state."""
        # Setup instance with reset method
        self.mock_instance.reset = Mock()

        # Access instance to cache it
        _ = self.wrapper.get_progress_manager()
        assert self.wrapper._cached_instance is not None

        # Reset progress manager
        self.wrapper.reset_progress_manager()

        # Verify singleton reset was called
        self.mock_instance.reset.assert_called_once()
        mock_reset.assert_called_once_with(self.mock_singleton_class)

        # Verify cache was cleared
        assert self.wrapper._cached_instance is None

    def test_reset_progress_manager_when_reset_fails_then_raises_error(self):
        """Test error handling when reset operation fails."""
        # Setup instance with reset method that fails
        self.mock_instance.reset = Mock(side_effect=Exception("Reset failed"))

        # Access instance to cache it first
        _ = self.wrapper.get_progress_manager()

        with pytest.raises(
            CompatibilityError, match="Failed to reset progress manager"
        ):
            self.wrapper.reset_progress_manager()

    def test_wrapper_attribute_delegation_when_method_called_then_preserves_behavior(
        self,
    ):
        """Test wrapper delegates attribute access to singleton."""
        mock_method = Mock(return_value=MOCK_METHOD_RETURN)
        self.mock_instance.custom_method = mock_method

        # Call method through wrapper
        result = self.wrapper.custom_method()

        assert result == MOCK_METHOD_RETURN
        mock_method.assert_called_once()

    def test_wrapper_attribute_delegation_when_attribute_missing_then_raises_error(
        self,
    ):
        """Test wrapper raises AttributeError for missing attributes."""

        # Use a real singleton class without the missing attribute
        class MinimalSingleton:
            def __init__(self):
                pass

        wrapper = ProgressManagerWrapper(MinimalSingleton)

        with pytest.raises(AttributeError, match="has no attribute 'missing_attr'"):
            _ = wrapper.missing_attr

    def test_wrapper_attribute_delegation_when_access_fails_then_raises_compatibility_error(
        self,
    ):
        """Test wrapper converts exceptions to CompatibilityError."""
        # Make the singleton instance creation fail
        self.mock_singleton_class.side_effect = RuntimeError("Instance creation failed")

        with pytest.raises(CompatibilityError, match="Failed to access attribute"):
            _ = self.wrapper.some_attr

@pytest.mark.skip(reason="Global compatibility layer removed in P3.2a - singleton elimination complete")
class TestGlobalCompatibilityLayer:
    """Test global compatibility layer instance and utilities."""

    def test_global_compatibility_layer_exists(self):
        """Test global compatibility layer is available."""
        assert compatibility_layer is not None
        assert isinstance(compatibility_layer, CompatibilityLayer)

    def test_get_progress_manager_compatibility_when_called_then_returns_wrapper(self):
        """Test global helper function returns wrapper."""
        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton"
        ) as mock_singleton:
            mock_singleton.__name__ = "ProgressManagerSingleton"

            wrapper = get_progress_manager_compatibility()

            assert wrapper is not None
            assert isinstance(wrapper, ProgressManagerWrapper)

class TestErrorHandlingAndContexts:
    """Test error handling with proper context information."""

    def test_compatibility_error_when_wrapper_creation_fails_then_includes_context(
        self,
    ):
        """Test CompatibilityError includes relevant context."""

        # Create a real class that will fail during wrapper creation
        class FailingSingleton:
            def __init__(self):
                raise Exception("Creation failed")

        wrapper = create_singleton_wrapper(FailingSingleton)

        # Disable fallback to force the context error instead of instance creation error
        wrapper._fallback_enabled = False

        try:
            wrapper._get_instance()
        except CompatibilityError as e:
            assert "Context unavailable and fallback disabled" in str(e)

    def test_progress_manager_wrapper_error_when_operation_fails_then_includes_context(
        self,
    ):
        """Test ProgressManagerWrapper errors include operation context."""
        mock_singleton_class = Mock()
        mock_singleton_class.__name__ = MOCK_SINGLETON_NAME

        with patch.object(
            mock_singleton_class,
            "__call__",
            side_effect=Exception("Instantiation failed"),
        ):
            wrapper = ProgressManagerWrapper(mock_singleton_class)

            try:
                wrapper.get_progress_manager()
            except CompatibilityError as e:
                assert "Failed to get progress manager" in str(e)
                assert hasattr(e, "context")
                assert "operation" in e.context

class TestConcurrencyAndThreadSafety:
    """Test thread safety of compatibility wrappers."""

    def setup_method(self):
        """Setup thread safety test fixtures."""
        self.mock_singleton_class = Mock()
        self.mock_singleton_class.__name__ = MOCK_SINGLETON_NAME
        self.results = []
        self.errors = []

    def test_compatibility_layer_thread_safety_when_concurrent_wrapper_access_then_single_wrapper(
        self,
    ):
        """Test CompatibilityLayer thread safety with concurrent access."""
        layer = CompatibilityLayer()
        wrappers = []

        def get_wrapper():
            try:
                wrapper = layer.get_progress_manager_wrapper()
                wrappers.append(wrapper)
            except Exception as e:
                self.errors.append(e)

        # Patch the import outside of the thread function
        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton",
            self.mock_singleton_class,
        ):
            # Create multiple threads accessing wrapper
            threads = []
            for _i in range(THREAD_COUNT):
                thread = threading.Thread(target=get_wrapper)
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Check results
            assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
            assert len(wrappers) == THREAD_COUNT
            # All wrappers should be the same instance (cached)
            assert all(wrapper is wrappers[0] for wrapper in wrappers)

    def test_progress_manager_wrapper_thread_safety_when_concurrent_operations_then_thread_safe(
        self,
    ):
        """Test ProgressManagerWrapper thread safety during concurrent operations."""
        mock_instance = Mock()
        mock_manager = Mock()
        mock_instance.get_progress_manager.return_value = mock_manager
        self.mock_singleton_class.return_value = mock_instance

        wrapper = ProgressManagerWrapper(self.mock_singleton_class)

        def get_manager():
            try:
                manager = wrapper.get_progress_manager()
                self.results.append(manager)
            except Exception as e:
                self.errors.append(e)

        # Create multiple threads accessing wrapper
        threads = []
        for _i in range(THREAD_COUNT):
            thread = threading.Thread(target=get_manager)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check results
        assert len(self.errors) == 0, f"Errors occurred: {self.errors}"
        assert len(self.results) == THREAD_COUNT
        # All should return the same manager
        assert all(manager == mock_manager for manager in self.results)
        # Singleton should only be created once
        assert self.mock_singleton_class.call_count == 1
