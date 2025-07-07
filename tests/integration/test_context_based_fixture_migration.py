"""Integration test for context-based fixture migration.

Tests the complete migration of test fixtures from singleton-dependent patterns
to context-based dependency injection, ensuring the entire test suite can run
with isolated, context-based testing patterns.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from spec_cli.core.context import SpecContext
from spec_cli.utils.test_migration_utils import (
    create_context_fixture,
    create_mock_context_fixture,
    validate_test_isolation,
)


class TestContextBasedFixtureMigration:
    """Integration test for complete context-based fixture migration."""

    def test_context_based_fixture_migration_when_full_test_suite_then_isolated_reliable_testing(
        self, isolated_test_context
    ):
        """Test complete fixture migration provides isolated, reliable testing.

        This integration test validates that the migrated context-based fixtures
        provide proper test isolation, eliminate singleton dependencies, and
        enable reliable test execution without state contamination.

        Args:
            isolated_test_context: Isolated SpecContext fixture
        """
        # Verify isolated context provides proper dependency injection
        assert isinstance(isolated_test_context, SpecContext)
        assert isolated_test_context.settings is not None
        assert isolated_test_context.console is not None
        assert isolated_test_context.progress is not None

        # Verify settings are properly isolated
        settings = isolated_test_context.settings
        assert settings.root_path is not None
        assert isinstance(settings.root_path, Path)
        assert settings.spec_dir is not None
        assert settings.specs_dir is not None

        # Verify console mock provides expected interface
        console = isolated_test_context.console
        assert hasattr(console, "print_message")
        assert hasattr(console, "print_error")
        assert hasattr(console, "print_success")
        assert hasattr(console, "print_warning")
        assert hasattr(console, "get_width")
        assert hasattr(console, "supports_color")

        # Verify progress mock provides expected interface
        progress = isolated_test_context.progress
        assert hasattr(progress, "show_progress")
        assert hasattr(progress, "update_status")
        assert hasattr(progress, "start_operation")
        assert hasattr(progress, "finish_operation")

        # Test that context modifications don't affect other instances
        original_debug = isolated_test_context.settings.debug_enabled
        isolated_test_context.settings.debug_enabled = not original_debug

        # Create another context and verify it's independent
        new_context = SpecContext.create_for_testing()
        assert (
            new_context.settings.debug_enabled
            != isolated_test_context.settings.debug_enabled
        )

        # Verify context immutability works correctly
        context_hash = isolated_test_context.get_context_hash()
        assert isinstance(context_hash, str)
        assert len(context_hash) > MINIMUM_HASH_LENGTH

    def test_fixture_migration_when_analysis_requirements_implemented_then_meets_migration_specs(
        self, spec_context
    ):
        """Test fixture migration meets requirements from P3.3a analysis.

        Validates that the migrated fixtures address all the singleton dependency
        issues and test isolation problems identified in the fixture analysis.

        Args:
            spec_context: Primary SpecContext fixture
        """
        # Verify primary context fixture provides all required dependencies
        assert isinstance(spec_context, SpecContext)

        # Test that fixture eliminates singleton access patterns
        # (These patterns were identified in P3.3a analysis)
        # Verify context provides alternatives to singleton patterns
        assert spec_context.settings is not None  # Alternative to get_settings()
        assert spec_context.console is not None  # Alternative to get_console()
        assert spec_context.progress is not None  # New unified interface

        # Test context-based dependency access patterns
        settings_value = spec_context.settings.debug_enabled
        console_width = spec_context.console.get_width()
        progress_op = spec_context.progress.start_operation("test")

        assert isinstance(settings_value, bool)
        assert isinstance(console_width, int)
        assert isinstance(progress_op, str)

        # Verify no singleton state contamination
        context_1 = SpecContext.create_for_testing()
        context_2 = SpecContext.create_for_testing()

        # Modify one context
        context_1.settings.debug_enabled = True
        context_2.settings.debug_enabled = False

        # Verify they remain independent
        assert context_1.settings.debug_enabled != context_2.settings.debug_enabled

    def test_context_fixtures_when_used_with_migrated_commands_then_provides_consistent_context(
        self, mock_git_environment
    ):
        """Test context fixtures work properly with command execution patterns.

        Validates that migrated fixtures integrate properly with CLI command
        patterns and provide consistent context throughout command execution.

        Args:
            mock_git_environment: Mock Git environment with context integration
        """
        # Verify mock Git environment includes context
        assert "context" in mock_git_environment
        assert "repository" in mock_git_environment
        assert "simulator" in mock_git_environment
        assert "isolator" in mock_git_environment

        context = mock_git_environment["context"]
        repo_path = mock_git_environment["repo_path"]

        # Verify context configuration aligns with Git environment
        assert isinstance(context, SpecContext)
        assert context.settings.root_path in repo_path.parents

        # Test that Git helpers work with context-based paths
        git_repo = mock_git_environment["repository"]
        git_simulator = mock_git_environment["simulator"]
        git_isolator = mock_git_environment["isolator"]

        # Verify Git components are properly configured
        assert git_repo is not None
        assert git_simulator is not None
        assert git_isolator is not None

        # Test command execution patterns with context
        # Simulate command execution that would use context
        command_context = {
            "settings": context.settings,
            "console": context.console,
            "progress": context.progress,
            "git_repo": git_repo,
        }

        # Verify all command dependencies are available
        assert command_context["settings"] is not None
        assert command_context["console"] is not None
        assert command_context["progress"] is not None
        assert command_context["git_repo"] is not None

    def test_context_fixtures_when_spec_context_factory_used_then_creates_isolated_test_contexts(
        self,
    ):
        """Test context fixtures integrate with SpecContext factory methods.

        Validates that the fixture migration properly integrates with SpecContext
        factory methods from P1.2b, ensuring consistent context creation patterns.
        """
        # Test create_for_testing factory method
        testing_context = SpecContext.create_for_testing()
        assert isinstance(testing_context, SpecContext)
        assert testing_context.settings is not None
        assert testing_context.console is not None
        assert testing_context.progress is not None

        # Test create_for_testing with overrides
        debug_context = SpecContext.create_for_testing({"debug_enabled": True})
        assert debug_context.settings.debug_enabled is True

        # Test context factory integration with test migration utils
        def testing_factory():
            return SpecContext.create_for_testing()

        def debug_factory():
            return SpecContext.create_for_testing({"debug_enabled": True})

        # Create fixtures from factories
        testing_fixture = create_context_fixture(testing_factory)
        debug_fixture = create_context_fixture(debug_factory)

        # Verify fixtures work correctly
        test_ctx = testing_fixture()
        debug_ctx = debug_fixture()

        assert isinstance(test_ctx, SpecContext)
        assert isinstance(debug_ctx, SpecContext)
        assert test_ctx.settings.debug_enabled != debug_ctx.settings.debug_enabled

    def test_fixture_migration_when_singleton_elimination_complete_then_no_shared_state_between_tests(
        self,
    ):
        """Test complete singleton elimination ensures no shared state.

        Validates that the migration completely eliminates singleton dependencies
        and shared state that could cause test contamination between executions.
        """
        # Test multiple context creations for state isolation
        contexts = []
        for i in range(TEST_CONTEXT_COUNT):
            context = SpecContext.create_for_testing(
                {
                    "debug_enabled": i % 2 == 0,  # Alternate debug setting
                    "console_width": BASE_CONSOLE_WIDTH + i * WIDTH_INCREMENT,
                }
            )
            contexts.append(context)

        # Verify all contexts are independent
        for i, context in enumerate(contexts):
            expected_debug = i % 2 == 0
            expected_width = BASE_CONSOLE_WIDTH + i * WIDTH_INCREMENT

            assert context.settings.debug_enabled == expected_debug
            assert context.settings.console_width == expected_width

            # Verify context hashes are unique
            context_hash = context.get_context_hash()
            other_hashes = [
                ctx.get_context_hash() for j, ctx in enumerate(contexts) if j != i
            ]
            assert context_hash not in other_hashes

        # Test fixture-created contexts for isolation
        mock_fixture = create_mock_context_fixture(
            settings_overrides={"debug_enabled": True},
            console_overrides={"supports_color": False},
        )

        # Create multiple fixture instances
        fixture_contexts = [mock_fixture() for _ in range(FIXTURE_INSTANCE_COUNT)]

        # Verify all fixture contexts are independent
        for i, ctx in enumerate(fixture_contexts):
            for j, other_ctx in enumerate(fixture_contexts):
                if i != j:
                    assert ctx is not other_ctx
                    # Settings should be the same (same overrides) but different instances
                    assert ctx.settings is not other_ctx.settings

    def test_migration_validation_when_test_isolation_patterns_then_detects_contamination_risks(
        self,
    ):
        """Test migration validation detects and prevents contamination risks.

        Validates that the migration utilities can detect test isolation issues
        and prevent state contamination patterns in the migrated test suite.
        """

        # Define test functions with different isolation characteristics
        def well_isolated_test(spec_context):
            """Test with proper context injection."""
            return spec_context.settings.debug_enabled

        def poorly_isolated_test():
            """Test with singleton access patterns."""
            # Simulated singleton access (commented to avoid import errors)
            # from spec_cli.config.settings import get_settings
            # return get_settings().debug_enabled
            import os

            return os.environ.get("SPEC_DEBUG", False)

        def mixed_isolation_test(spec_context):
            """Test with context injection but also environment access."""
            import os

            env_debug = os.environ.get("SPEC_DEBUG", False)
            ctx_debug = spec_context.settings.debug_enabled
            return env_debug or ctx_debug

        # Validate isolation for each test pattern
        well_isolated_result = validate_test_isolation(well_isolated_test)
        poorly_isolated_result = validate_test_isolation(poorly_isolated_test)
        mixed_isolation_result = validate_test_isolation(mixed_isolation_test)

        # Verify isolation validation results
        assert well_isolated_result is True
        assert poorly_isolated_result is False
        assert mixed_isolation_result is False

        # Test with mock functions that simulate various patterns
        mock_context_test = Mock()
        mock_context_test.__name__ = "mock_context_test"
        mock_context_test.__module__ = "test_module"

        # Mock function signature and source code analysis
        with (
            pytest.mock.patch("inspect.signature") as mock_sig,
            pytest.mock.patch("inspect.getsource") as mock_source,
        ):
            # Simulate function with context parameter and clean source
            mock_sig.return_value.parameters.keys.return_value = ["spec_context"]
            mock_source.return_value = (
                "def test_func(spec_context): return spec_context.settings"
            )

            result = validate_test_isolation(mock_context_test)
            assert result is True

            # Simulate function with singleton patterns in source
            mock_source.return_value = "def test_func(): return get_settings().debug"
            result = validate_test_isolation(mock_context_test)
            assert result is False

# Test constants for magic number elimination
MINIMUM_HASH_LENGTH = 8
TEST_CONTEXT_COUNT = 5
BASE_CONSOLE_WIDTH = 80
WIDTH_INCREMENT = 10
FIXTURE_INSTANCE_COUNT = 3
