"""Tests for singleton implementation utilities."""

import threading
import time
from unittest.mock import patch

import pytest

from spec_cli.utils.singleton import (
    SingletonMeta,
    _instance_locks,
    _instances,
    reset_singleton,
    singleton_decorator,
)


class TestSingletonDecorator:
    """Test decorator-based singleton implementation."""

    def test_singleton_decorator_when_applied_to_class_then_creates_singleton_behavior(
        self,
    ):
        """Test basic singleton behavior with decorator."""

        @singleton_decorator
        class TestService:
            def __init__(self):
                self.initialized = True

        instance1 = TestService()
        instance2 = TestService()

        assert instance1 is instance2
        assert instance1.initialized is True

    def test_singleton_decorator_when_applied_to_non_class_then_raises_type_error(self):
        """Test decorator rejects non-class arguments."""
        with pytest.raises(
            TypeError, match="singleton_decorator can only be applied to classes"
        ):

            @singleton_decorator
            def not_a_class():
                pass

    def test_singleton_decorator_when_multiple_threads_then_creates_single_instance(
        self,
    ):
        """Test thread safety of decorator."""

        @singleton_decorator
        class ThreadTestService:
            def __init__(self):
                time.sleep(0.01)  # Simulate initialization time
                self.thread_id = threading.current_thread().ident

        instances = []

        def create_instance():
            instances.append(ThreadTestService())

        threads = [threading.Thread(target=create_instance) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All instances should be the same
        for instance in instances[1:]:
            assert instance is instances[0]

    def test_singleton_decorator_when_preserves_class_metadata_then_maintains_attributes(
        self,
    ):
        """Test decorator preserves class metadata."""

        @singleton_decorator
        class DocumentedService:
            """A documented service class."""

            pass

        assert DocumentedService.__name__ == "DocumentedService"
        assert DocumentedService.__doc__ == "A documented service class."
        assert hasattr(DocumentedService, "_original_class")
        assert hasattr(DocumentedService, "_is_singleton")
        assert DocumentedService._is_singleton is True

    @patch("spec_cli.utils.singleton.debug_logger")
    def test_singleton_decorator_when_creates_instance_then_logs_creation(
        self, mock_logger
    ):
        """Test singleton creation is logged."""

        @singleton_decorator
        class LogTestService:
            pass

        LogTestService()

        mock_logger.log.assert_called_with(
            "DEBUG",
            "Creating new singleton instance",
            class_name="LogTestService",
            module="tests.unit.utils.test_singleton",
        )


class TestSingletonMeta:
    """Test metaclass-based singleton implementation."""

    def test_singleton_meta_when_creates_class_then_provides_singleton_behavior(self):
        """Test basic singleton behavior with metaclass."""

        class MetaTestService(metaclass=SingletonMeta):
            def __init__(self):
                self.initialized = True

        instance1 = MetaTestService()
        instance2 = MetaTestService()

        assert instance1 is instance2
        assert instance1.initialized is True

    def test_singleton_meta_when_multiple_threads_then_creates_single_instance(self):
        """Test thread safety of metaclass."""

        class MetaThreadService(metaclass=SingletonMeta):
            def __init__(self):
                time.sleep(0.01)  # Simulate initialization time
                self.thread_id = threading.current_thread().ident

        instances = []

        def create_instance():
            instances.append(MetaThreadService())

        threads = [threading.Thread(target=create_instance) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # All instances should be the same
        for instance in instances[1:]:
            assert instance is instances[0]

    @patch("spec_cli.utils.singleton.debug_logger")
    def test_singleton_meta_when_creates_instance_then_logs_creation(self, mock_logger):
        """Test metaclass singleton creation is logged."""

        class MetaLogService(metaclass=SingletonMeta):
            pass

        MetaLogService()

        mock_logger.log.assert_called_with(
            "DEBUG",
            "Creating new singleton instance via metaclass",
            class_name="MetaLogService",
            module="tests.unit.utils.test_singleton",
        )


class TestResetSingleton:
    """Test singleton reset functionality."""

    def test_reset_singleton_when_decorator_singleton_then_clears_instance(self):
        """Test resetting decorator-based singleton."""

        @singleton_decorator
        class ResetTestService:
            def __init__(self):
                self.value = "original"

        # Create first instance
        instance1 = ResetTestService()
        instance1.value = "modified"

        # Reset and create new instance
        reset_singleton(ResetTestService)
        instance2 = ResetTestService()

        assert instance2.value == "original"
        assert instance1 is not instance2

    def test_reset_singleton_when_metaclass_singleton_then_clears_instance(self):
        """Test resetting metaclass-based singleton."""

        class MetaResetService(metaclass=SingletonMeta):
            def __init__(self):
                self.value = "original"

        # Create first instance
        instance1 = MetaResetService()
        instance1.value = "modified"

        # Reset and create new instance
        reset_singleton(MetaResetService)
        instance2 = MetaResetService()

        assert instance2.value == "original"
        assert instance1 is not instance2

    def test_reset_singleton_when_no_instance_exists_then_no_error(self):
        """Test resetting non-existent singleton."""

        @singleton_decorator
        class NeverCreatedService:
            pass

        # Should not raise error
        reset_singleton(NeverCreatedService)

    @patch("spec_cli.utils.singleton.debug_logger")
    def test_reset_singleton_when_resets_then_logs_action(self, mock_logger):
        """Test reset action is logged."""

        @singleton_decorator
        class LogResetService:
            pass

        # Create instance first
        LogResetService()

        # Reset it
        reset_singleton(LogResetService)

        mock_logger.log.assert_any_call(
            "DEBUG", "Resetting decorator-based singleton", class_name="LogResetService"
        )


class TestSingletonComparison:
    """Test comparison between decorator and metaclass approaches."""

    def test_decorator_vs_metaclass_when_both_used_then_independent_instances(self):
        """Test decorator and metaclass singletons are independent."""

        @singleton_decorator
        class DecoratorService:
            def __init__(self):
                self.approach = "decorator"

        class MetaclassService(metaclass=SingletonMeta):
            def __init__(self):
                self.approach = "metaclass"

        dec_instance1 = DecoratorService()
        dec_instance2 = DecoratorService()
        meta_instance1 = MetaclassService()
        meta_instance2 = MetaclassService()

        # Decorator instances should be same
        assert dec_instance1 is dec_instance2
        assert dec_instance1.approach == "decorator"

        # Metaclass instances should be same
        assert meta_instance1 is meta_instance2
        assert meta_instance1.approach == "metaclass"

        # Different approaches should be different instances
        assert dec_instance1 is not meta_instance1


class TestConcurrencyEdgeCases:
    """Test edge cases for concurrent access."""

    def test_concurrent_reset_and_creation_when_racing_then_handles_gracefully(self):
        """Test concurrent reset and instance creation."""

        @singleton_decorator
        class ConcurrencyService:
            def __init__(self):
                time.sleep(0.01)
                self.created_at = time.time()

        # Create initial instance
        ConcurrencyService()

        results = []
        errors = []

        def reset_service():
            try:
                reset_singleton(ConcurrencyService)
                results.append("reset")
            except Exception as e:
                errors.append(e)

        def create_service():
            try:
                instance = ConcurrencyService()
                results.append(instance)
            except Exception as e:
                errors.append(e)

        # Run concurrent reset and creation
        threads = [
            threading.Thread(target=reset_service),
            threading.Thread(target=create_service),
            threading.Thread(target=create_service),
        ]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # Should handle gracefully without errors
        assert len(errors) == 0
        assert len(results) == 3  # 1 reset + 2 instances

    def setUp(self):
        """Clear singletons before each test."""
        _instances.clear()
        _instance_locks.clear()
        if hasattr(SingletonMeta, "_instances"):
            SingletonMeta._instances.clear()
            SingletonMeta._locks.clear()

    def tearDown(self):
        """Clear singletons after each test."""
        _instances.clear()
        _instance_locks.clear()
        if hasattr(SingletonMeta, "_instances"):
            SingletonMeta._instances.clear()
            SingletonMeta._locks.clear()
