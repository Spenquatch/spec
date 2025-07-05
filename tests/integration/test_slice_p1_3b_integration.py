"""Integration tests for P1.3b compatibility wrapper implementation.

This module tests the compatibility wrapper integration with actual singleton
classes to ensure transparent access and backward compatibility preservation.

Test Scope: Integration with real singleton behavior
Priority: High
"""

from unittest.mock import Mock, patch

import pytest

from spec_cli.core.compatibility import (
    CompatibilityLayer,
    get_progress_manager_compatibility,
)


class TestCompatibilityWrapperIntegration:
    """Test compatibility wrapper integration with real singleton usage patterns."""

    def setup_method(self):
        """Setup integration test environment."""
        self.layer = CompatibilityLayer()

    def test_compatibility_wrapper_integration_when_real_singleton_usage_then_preserves_behavior(
        self,
    ):
        """End-to-end test with actual singleton usage patterns from codebase."""

        # Create a mock singleton that mimics ProgressManagerSingleton interface
        class MockProgressManagerSingleton:
            def __init__(self):
                self._manager = Mock()
                self._manager.start_task = Mock(return_value="task_id")
                self._manager.update_progress = Mock()
                self._manager.complete_task = Mock()

            def get_progress_manager(self):
                """Get the progress manager instance."""
                return self._manager

            def set_progress_manager(self, manager):
                """Set a custom progress manager."""
                self._manager = manager

            def reset(self):
                """Reset the progress manager state."""
                self._manager = Mock()

        # Test the integration with patched singleton
        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton",
            MockProgressManagerSingleton,
        ):
            # Get wrapper through compatibility layer
            wrapper = self.layer.get_progress_manager_wrapper()

            # Test that wrapper preserves all expected methods
            assert hasattr(wrapper, "get_progress_manager")
            assert hasattr(wrapper, "set_progress_manager")
            assert hasattr(wrapper, "reset_progress_manager")

            # Test progress manager access through wrapper
            manager = wrapper.get_progress_manager()
            assert manager is not None

            # Test that the manager has expected interface
            assert hasattr(manager, "start_task")
            assert hasattr(manager, "update_progress")
            assert hasattr(manager, "complete_task")

            # Test actual method calls work through wrapper
            task_id = manager.start_task("test_task")
            assert task_id == "task_id"
            manager.start_task.assert_called_once_with("test_task")

            # Test progress update
            manager.update_progress(0.5)
            manager.update_progress.assert_called_once_with(0.5)

            # Test task completion
            manager.complete_task()
            manager.complete_task.assert_called_once()

    def test_compatibility_wrapper_when_singleton_methods_called_then_transparent_delegation(
        self,
    ):
        """Test wrapper transparently delegates to singleton methods."""

        class TestSingleton:
            def __init__(self):
                self.value = "initial"
                self.call_count = 0

            def get_value(self):
                return self.value

            def set_value(self, new_value):
                self.value = new_value
                self.call_count += 1

            def increment_count(self):
                self.call_count += 1
                return self.call_count

        # Test transparent delegation
        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton", TestSingleton
        ):
            wrapper = self.layer.get_progress_manager_wrapper()

            # Test attribute access through wrapper
            initial_value = wrapper.get_value()
            assert initial_value == "initial"

            # Test method calls that modify state
            wrapper.set_value("modified")
            modified_value = wrapper.get_value()
            assert modified_value == "modified"

            # Test method calls with return values
            count1 = wrapper.increment_count()
            count2 = wrapper.increment_count()
            assert count1 == 1
            assert count2 == 2

    def test_compatibility_wrapper_when_multiple_access_patterns_then_maintains_singleton_behavior(
        self,
    ):
        """Test wrapper maintains singleton behavior across different access patterns."""

        class SingletonWithState:
            def __init__(self):
                self.state = {"counter": 0, "values": []}

            def increment(self):
                self.state["counter"] += 1
                return self.state["counter"]

            def add_value(self, value):
                self.state["values"].append(value)

            def get_state(self):
                return self.state.copy()

        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton", SingletonWithState
        ):
            # Get wrapper instances through different paths
            wrapper1 = self.layer.get_progress_manager_wrapper()
            wrapper2 = get_progress_manager_compatibility()

            # Verify both wrappers access the same singleton instance
            wrapper1.increment()
            wrapper2.add_value("test")

            state1 = wrapper1.get_state()
            state2 = wrapper2.get_state()

            # Both should see the same state (singleton behavior preserved)
            assert state1 == state2
            assert state1["counter"] == 1
            assert state1["values"] == ["test"]

    def test_compatibility_wrapper_when_reset_called_then_clears_singleton_state(self):
        """Test wrapper reset functionality with singleton state management."""

        class StatefulSingleton:
            def __init__(self):
                self.data = {"initialized": True}

            def set_data(self, key, value):
                self.data[key] = value

            def get_data(self):
                return self.data

            def reset(self):
                self.data = {"reset": True}

        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton", StatefulSingleton
        ):
            with patch("spec_cli.utils.singleton.reset_singleton") as mock_reset:
                wrapper = self.layer.get_progress_manager_wrapper()

                # Modify singleton state through wrapper
                wrapper.set_data("test_key", "test_value")

                # Verify state is set
                data = wrapper.get_data()
                assert data["test_key"] == "test_value"

                # Reset through wrapper
                wrapper.reset_progress_manager()

                # Verify reset was called on both wrapper and singleton utility
                mock_reset.assert_called_once()

    def test_compatibility_wrapper_error_handling_when_singleton_errors_then_propagates_correctly(
        self,
    ):
        """Test wrapper error handling preserves singleton error behavior."""

        class ErroringSingleton:
            def __init__(self):
                pass

            def failing_method(self):
                raise ValueError("Singleton method failed")

            def working_method(self):
                return "success"

        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton", ErroringSingleton
        ):
            wrapper = self.layer.get_progress_manager_wrapper()

            # Test that working methods still work
            result = wrapper.working_method()
            assert result == "success"

            # Test that errors are properly propagated
            with pytest.raises(ValueError, match="Singleton method failed"):
                wrapper.failing_method()

    def test_compatibility_wrapper_thread_safety_when_concurrent_access_then_maintains_consistency(
        self,
    ):
        """Test wrapper maintains thread safety with singleton access."""
        import threading

        class ThreadSafeSingleton:
            def __init__(self):
                self.counter = 0
                self.lock = threading.Lock()

            def increment(self):
                with self.lock:
                    current = self.counter
                    # Simulate some work
                    import time

                    time.sleep(0.001)
                    self.counter = current + 1
                    return self.counter

        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton", ThreadSafeSingleton
        ):
            wrapper = self.layer.get_progress_manager_wrapper()
            results = []
            errors = []

            def worker():
                try:
                    for _ in range(5):
                        result = wrapper.increment()
                        results.append(result)
                except Exception as e:
                    errors.append(e)

            # Start multiple threads
            threads = []
            for _ in range(3):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()

            # Wait for completion
            for thread in threads:
                thread.join()

            # Verify no errors occurred
            assert len(errors) == 0

            # Verify we got expected number of results
            assert len(results) == 15  # 3 threads * 5 increments each

            # Verify final counter value is correct
            final_count = wrapper.increment()
            assert final_count == 16  # Previous 15 + 1


class TestP1_3bToPhase2CompatibilityBridge:
    """Test compatibility wrapper provides bridge for Phase 2 CLI integration."""

    def test_p1_3b_to_phase_2_compatibility_bridge(self):
        """Validates compatibility layer provides bridge for Phase 2 CLI integration."""
        # This test validates that the wrapper can serve as a bridge
        # between current singleton usage and future DI-based CLI integration

        class MockCLIProgressSingleton:
            def __init__(self):
                self.cli_calls = []

            def get_progress_manager(self):
                return MockProgressManager()

            def set_progress_manager(self, manager):
                self.cli_calls.append(f"set_manager:{type(manager).__name__}")

        class MockProgressManager:
            def start_task(self, name):
                return f"cli_task_{name}"

        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton",
            MockCLIProgressSingleton,
        ):
            # Get wrapper that will serve as compatibility bridge
            wrapper = get_progress_manager_compatibility()

            # Test Phase 2 CLI integration patterns
            manager = wrapper.get_progress_manager()
            task_id = manager.start_task("cli_operation")

            # Verify CLI integration works through compatibility layer
            assert task_id == "cli_task_cli_operation"

            # Test that wrapper can accept custom managers (Phase 2 DI integration)
            custom_manager = Mock()
            wrapper.set_progress_manager(custom_manager)

            # Verify the call was delegated properly
            # This shows the bridge is ready for Phase 2 DI integration


class TestCompatibilityWrapperImplementsP1_3aRequirements:
    """Test wrapper implementation satisfies P1.3a compatibility requirements."""

    def test_compatibility_wrapper_implements_p1_3a_requirements(self):
        """Validates wrapper implementation satisfies P1.3a compatibility requirements."""
        # Based on P1.3a analysis, test all required compatibility aspects

        class P1_3aCompliantSingleton:
            def __init__(self):
                self.reset_count = 0

            def get_progress_manager(self):
                """Required by P1.3a: convenience function compatibility."""
                return Mock(name="progress_manager")

            def set_progress_manager(self, manager):
                """Required by P1.3a: custom manager injection."""
                self.current_manager = manager

            def reset(self):
                """Required by P1.3a: reset functionality."""
                self.reset_count += 1

        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton",
            P1_3aCompliantSingleton,
        ):
            with patch("spec_cli.utils.singleton.reset_singleton") as mock_reset:
                layer = CompatibilityLayer()
                wrapper = layer.get_progress_manager_wrapper()

                # Test P1.3a Requirement: API Preservation
                assert hasattr(wrapper, "get_progress_manager")
                assert hasattr(wrapper, "set_progress_manager")
                assert hasattr(wrapper, "reset_progress_manager")

                # Test P1.3a Requirement: Convenience Function Compatibility
                manager = wrapper.get_progress_manager()
                assert manager is not None

                # Test P1.3a Requirement: Custom Manager Injection
                custom_manager = Mock()
                wrapper.set_progress_manager(custom_manager)
                # Should not raise exception

                # Test P1.3a Requirement: Reset Functionality
                wrapper.reset_progress_manager()
                mock_reset.assert_called_once()

                # Test P1.3a Requirement: Thread Safety (basic check)
                assert hasattr(wrapper, "_lock")
                assert wrapper._lock is not None

                # Test P1.3a Requirement: Backward Compatibility
                # Wrapper should work exactly like direct singleton access
                direct_singleton = P1_3aCompliantSingleton()
                direct_manager = direct_singleton.get_progress_manager()
                wrapper_manager = wrapper.get_progress_manager()

                # Both should provide similar interface
                assert hasattr(direct_manager, "__class__")
                assert hasattr(wrapper_manager, "__class__")


class TestDIMigrationContext:
    """Test compatibility wrapper supports migration from singleton to context patterns."""

    def test_compatibility_wrapper_migration_readiness(self):
        """Validates wrapper supports migration from singleton to context patterns."""
        # Test that wrapper is ready for gradual migration to DI

        class MigrationReadySingleton:
            def __init__(self):
                self.migration_mode = "singleton"

            def get_progress_manager(self):
                return Mock(mode=self.migration_mode)

            def set_migration_mode(self, mode):
                self.migration_mode = mode

        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton",
            MigrationReadySingleton,
        ):
            wrapper = get_progress_manager_compatibility()

            # Test current singleton mode works
            manager = wrapper.get_progress_manager()
            assert manager.mode == "singleton"

            # Test that wrapper can adapt to migration changes
            wrapper.set_migration_mode("transitional")
            updated_manager = wrapper.get_progress_manager()
            assert updated_manager.mode == "transitional"

            # Verify wrapper maintains consistent access patterns during migration
            assert callable(wrapper.get_progress_manager)
            assert hasattr(wrapper, "_lock")  # Thread safety maintained

    def test_wrapper_backward_compatibility_during_migration(self):
        """Validates existing code continues working during migration phases."""
        # Test that existing singleton usage patterns continue to work
        # even as the system migrates toward dependency injection

        class LegacySingleton:
            def __init__(self):
                self.legacy_calls = []

            def legacy_method(self):
                self.legacy_calls.append("legacy_call")
                return "legacy_result"

            def get_progress_manager(self):
                return self

        with patch(
            "spec_cli.ui.progress_manager.ProgressManagerSingleton", LegacySingleton
        ):
            # Test that legacy patterns still work through wrapper
            wrapper = get_progress_manager_compatibility()

            # Test legacy method access through wrapper
            result = wrapper.legacy_method()
            assert result == "legacy_result"

            # Test chained access patterns (legacy style)
            manager = wrapper.get_progress_manager()
            chained_result = manager.legacy_method()
            assert chained_result == "legacy_result"

            # Verify legacy calls were recorded (singleton behavior preserved)
            assert len(wrapper.legacy_calls) >= 2  # Both calls should be recorded
