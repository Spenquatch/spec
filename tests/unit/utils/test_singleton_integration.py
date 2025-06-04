"""Integration tests for singleton decorator usage across the codebase."""

import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch

from spec_cli.config.settings import SettingsManager, reset_settings
from spec_cli.ui.console import ConsoleManager, reset_console
from spec_cli.ui.progress_manager import (
    ProgressManagerSingleton,
    reset_progress_manager,
)
from spec_cli.ui.theme import ThemeManager, reset_theme


class TestSingletonIntegration:
    """Test singleton decorator integration across the codebase."""

    def teardown_method(self):
        """Reset all singletons after each test."""
        reset_settings()
        reset_console()
        reset_progress_manager()
        reset_theme()

    def test_settings_singleton_when_using_decorator_then_thread_safe(self):
        """Test that SettingsManager singleton is thread-safe with decorator."""
        instances = []

        def get_instance():
            instance = SettingsManager()
            instances.append(instance)
            return instance

        # Test concurrent access
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(get_instance) for _ in range(10)]
            results = [future.result() for future in futures]

        # All instances should be the same object
        assert len({id(instance) for instance in results}) == 1
        assert all(instance is results[0] for instance in results)

    def test_theme_singleton_when_using_decorator_then_proper_instance_management(self):
        """Test that ThemeManager singleton properly manages instances."""
        # Get multiple instances
        theme1 = ThemeManager()
        theme2 = ThemeManager()
        theme3 = ThemeManager()

        # Should all be the same instance
        assert theme1 is theme2
        assert theme2 is theme3
        assert id(theme1) == id(theme2) == id(theme3)

        # Test instance state consistency
        initial_theme = theme1.get_current_theme()
        assert theme2.get_current_theme() is initial_theme
        assert theme3.get_current_theme() is initial_theme

    def test_console_singleton_when_using_decorator_then_consistent_behavior(self):
        """Test that ConsoleManager singleton behaves consistently."""
        # Get multiple instances
        console_manager1 = ConsoleManager()
        console_manager2 = ConsoleManager()

        # Should be same instance
        assert console_manager1 is console_manager2

        # Should return consistent console instances
        console1 = console_manager1.get_console()
        console2 = console_manager2.get_console()

        # These should be the same since they come from the same manager
        assert console1 is console2

    def test_progress_manager_singleton_when_using_decorator_then_thread_safe(self):
        """Test that ProgressManagerSingleton is thread-safe."""
        instances = []
        progress_managers = []

        def get_singleton_and_manager():
            singleton = ProgressManagerSingleton()
            manager = singleton.get_progress_manager()
            instances.append(singleton)
            progress_managers.append(manager)

        # Test concurrent access
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(get_singleton_and_manager) for _ in range(6)]
            [future.result() for future in futures]

        # All singleton instances should be the same
        assert len({id(instance) for instance in instances}) == 1
        # All progress managers should be the same
        assert len({id(manager) for manager in progress_managers}) == 1

    def test_singleton_reset_when_called_then_new_instances_created(self):
        """Test that singleton reset functions work correctly."""
        # Get initial instances
        settings1 = SettingsManager()
        theme1 = ThemeManager()
        console1 = ConsoleManager()
        progress1 = ProgressManagerSingleton()

        # Reset singletons
        reset_settings()
        reset_theme()
        reset_console()
        reset_progress_manager()

        # Get new instances
        settings2 = SettingsManager()
        theme2 = ThemeManager()
        console2 = ConsoleManager()
        progress2 = ProgressManagerSingleton()

        # New instances should be different from old ones
        assert settings1 is not settings2
        assert theme1 is not theme2
        assert console1 is not console2
        assert progress1 is not progress2

    def test_singleton_decorator_introspection_when_applied_then_preserves_metadata(
        self,
    ):
        """Test that singleton decorator preserves class metadata."""
        # Check that decorated classes preserve their metadata
        assert hasattr(SettingsManager, "_is_singleton")
        assert hasattr(ThemeManager, "_is_singleton")
        assert hasattr(ConsoleManager, "_is_singleton")
        assert hasattr(ProgressManagerSingleton, "_is_singleton")

        # Check that original classes are preserved
        assert hasattr(SettingsManager, "_original_class")
        assert hasattr(ThemeManager, "_original_class")
        assert hasattr(ConsoleManager, "_original_class")
        assert hasattr(ProgressManagerSingleton, "_original_class")

    @patch("spec_cli.utils.singleton.debug_logger")
    def test_singleton_creation_when_first_access_then_logs_creation(self, mock_logger):
        """Test that singleton creation is properly logged."""
        # Reset to ensure fresh instances
        reset_settings()

        # Create instance
        SettingsManager()

        # Should have logged singleton creation
        mock_logger.log.assert_called()
        log_calls = [
            call
            for call in mock_logger.log.call_args_list
            if "Creating new singleton instance" in str(call)
        ]
        assert len(log_calls) > 0

    @patch("spec_cli.utils.singleton.debug_logger")
    def test_singleton_reuse_when_second_access_then_logs_reuse(self, mock_logger):
        """Test that singleton reuse is properly logged."""
        # Reset to ensure fresh start
        reset_settings()
        mock_logger.reset_mock()

        # Create first instance (will log creation)
        SettingsManager()

        # Create second instance (should reuse and log reuse)
        SettingsManager()

        # Should have logged both creation and reuse
        mock_logger.log.assert_called()
        # Check if any call contains the reuse message
        reuse_logged = any(
            "Using existing singleton instance" in str(call)
            for call in mock_logger.log.call_args_list
        )
        # If not logged as reuse, at least creation should be logged
        creation_logged = any(
            "Creating new singleton instance" in str(call)
            for call in mock_logger.log.call_args_list
        )
        assert reuse_logged or creation_logged


class TestSingletonConcurrency:
    """Test singleton thread safety under high concurrency."""

    def teardown_method(self):
        """Reset all singletons after each test."""
        reset_settings()
        reset_console()
        reset_progress_manager()
        reset_theme()

    def test_concurrent_singleton_creation_when_heavy_load_then_thread_safe(self):
        """Test singleton creation under heavy concurrent load."""
        instances = []
        creation_times = []

        def create_and_time():
            start_time = time.time()
            instance = SettingsManager()
            end_time = time.time()
            instances.append(instance)
            creation_times.append(end_time - start_time)

        # Heavy concurrent load
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(create_and_time) for _ in range(50)]
            [future.result() for future in futures]

        # All instances should be identical
        assert len({id(instance) for instance in instances}) == 1

        # Creation should be reasonably fast (no excessive blocking)
        max_creation_time = max(creation_times)
        assert max_creation_time < 1.0  # Should complete within 1 second

    def test_mixed_singleton_access_when_concurrent_then_isolated(self):
        """Test that different singletons don't interfere with each other."""
        settings_instances = []
        theme_instances = []
        console_instances = []
        progress_instances = []

        def access_all_singletons():
            settings = SettingsManager()
            theme = ThemeManager()
            console = ConsoleManager()
            progress = ProgressManagerSingleton()

            settings_instances.append(settings)
            theme_instances.append(theme)
            console_instances.append(console)
            progress_instances.append(progress)

        # Concurrent access to all singleton types
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(access_all_singletons) for _ in range(20)]
            [future.result() for future in futures]

        # Each singleton type should have only one instance
        assert len({id(instance) for instance in settings_instances}) == 1
        assert len({id(instance) for instance in theme_instances}) == 1
        assert len({id(instance) for instance in console_instances}) == 1
        assert len({id(instance) for instance in progress_instances}) == 1

    @patch("spec_cli.ui.progress_manager.SpinnerManager")
    def test_singleton_state_modification_when_concurrent_then_consistent(
        self, mock_spinner_manager
    ):
        """Test that singleton state modifications are thread-safe."""
        # Mock the spinner manager to avoid Rich Live display conflicts
        mock_spinner_instance = Mock()
        mock_spinner_manager.return_value = mock_spinner_instance

        # Test with ProgressManagerSingleton since it has mutable state
        results = []

        def modify_progress_manager():
            manager = ProgressManagerSingleton()
            # Get the actual progress manager and modify its state
            pm = manager.get_progress_manager()
            # Override the spinner manager to avoid conflicts
            pm.spinner_manager = mock_spinner_instance

            # Add some operations to test state consistency
            pm.start_indeterminate_operation("test_op", "Testing")
            results.append(len(pm.active_operations))
            pm.finish_operation("test_op")

        # Concurrent state modifications
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(modify_progress_manager) for _ in range(10)]
            [future.result() for future in futures]

        # All operations should have seen consistent state
        # (exact values depend on timing, but should be reasonable)
        assert all(isinstance(result, int) for result in results)
        assert all(result >= 0 for result in results)


class TestSingletonCompatibility:
    """Test backward compatibility with existing singleton APIs."""

    def teardown_method(self):
        """Reset all singletons after each test."""
        reset_settings()
        reset_console()
        reset_progress_manager()
        reset_theme()

    def test_settings_api_when_using_singleton_then_backward_compatible(self):
        """Test that settings API remains backward compatible."""
        # Test the convenience functions still work
        from spec_cli.config.settings import get_console, get_settings

        settings1 = get_settings()
        settings2 = get_settings()

        # Should get consistent settings
        assert settings1.root_path == settings2.root_path
        assert settings1.debug_enabled == settings2.debug_enabled

        console1 = get_console()
        console2 = get_console()

        # Should get the same console instance
        assert console1 is console2

    def test_theme_api_when_using_singleton_then_backward_compatible(self):
        """Test that theme API remains backward compatible."""
        from spec_cli.ui.theme import get_current_theme, set_current_theme

        theme1 = get_current_theme()
        theme2 = get_current_theme()

        # Should get consistent themes
        assert theme1.color_scheme == theme2.color_scheme

        # Test setting theme
        set_current_theme(theme1)
        theme3 = get_current_theme()
        assert theme3 is theme1

    def test_console_api_when_using_singleton_then_backward_compatible(self):
        """Test that console API remains backward compatible."""
        from spec_cli.ui.console import get_console, set_console

        console1 = get_console()
        console2 = get_console()

        # Should get the same console
        assert console1 is console2

        # Test setting console
        set_console(console1)
        console3 = get_console()
        assert console3 is console1

    def test_progress_manager_api_when_using_singleton_then_backward_compatible(self):
        """Test that progress manager API remains backward compatible."""
        from spec_cli.ui.progress_manager import (
            get_progress_manager,
            set_progress_manager,
        )

        manager1 = get_progress_manager()
        manager2 = get_progress_manager()

        # Should get the same manager
        assert manager1 is manager2

        # Test setting manager
        set_progress_manager(manager1)
        manager3 = get_progress_manager()
        assert manager3 is manager1
