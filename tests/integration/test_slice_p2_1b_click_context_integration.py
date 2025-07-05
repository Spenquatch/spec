"""Integration tests for Click context integration with real CLI commands."""

import click
import pytest
from click.testing import CliRunner

from spec_cli.cli.context_integration import (
    get_context_keys,
    integrate_spec_context,
    retrieve_spec_context,
    retrieve_typed_context_data,
    setup_dependency_injection_context,
    store_typed_context_data,
    teardown_dependency_injection_context,
)
from spec_cli.core.context import (
    SpecConsoleInterface,
    SpecContext,
    SpecProgressInterface,
    SpecSettingsInterface,
)
from spec_cli.utils.click_utils import retrieve_context_data, store_context_data

# Test constants
INTEGRATION_CONFIG = {"integration_test": True, "environment": "testing", "debug": True}


@pytest.fixture
def mock_spec_context():
    """Create a mock SpecContext for integration testing."""
    settings = SpecSettingsInterface()
    console = SpecConsoleInterface()
    progress = SpecProgressInterface()
    return SpecContext(settings=settings, console=console, progress=progress)


class TestClickContextIntegrationEndToEnd:
    """Test Click context integration with real CLI command scenarios."""

    def test_click_context_integration_when_real_cli_commands_then_stores_retrieves_successfully(
        self, mock_spec_context
    ):
        """End-to-end test with actual CLI commands storing and retrieving context data."""

        # Create a test CLI command that uses context integration
        @click.command()
        @click.pass_context
        def test_command(ctx: click.Context) -> None:
            """Test command for context integration."""
            # Setup dependency injection context
            setup_dependency_injection_context(ctx)

            # Store various types of data
            store_context_data(ctx, "config", INTEGRATION_CONFIG)
            store_typed_context_data(ctx, "debug_mode", True, bool)
            store_typed_context_data(ctx, "max_retries", 5, int)

            # Integrate SpecContext
            integrate_spec_context(ctx, mock_spec_context)

            # Verify storage worked
            retrieved_config = retrieve_context_data(ctx, "config")
            assert retrieved_config == INTEGRATION_CONFIG

            debug_mode = retrieve_typed_context_data(ctx, "debug_mode", bool)
            assert debug_mode is True

            max_retries = retrieve_typed_context_data(ctx, "max_retries", int)
            assert max_retries == 5

            # Verify SpecContext integration
            retrieved_spec_context = retrieve_spec_context(ctx)
            assert retrieved_spec_context is mock_spec_context

            # Verify context keys
            keys = get_context_keys(ctx)
            expected_keys = {
                "config",
                "debug_mode",
                "max_retries",
                "spec_context",
                "di_metadata",
            }
            assert set(keys) == expected_keys

            # Cleanup
            teardown_dependency_injection_context(ctx)

        # Execute the command
        runner = CliRunner()
        result = runner.invoke(test_command, [])

        # Verify command executed successfully
        assert result.exit_code == 0

    def test_click_context_integration_when_parent_child_commands_then_context_inheritance_works(
        self,
    ):
        """Test context integration with parent-child command structure."""

        @click.group()
        @click.pass_context
        def parent_group(ctx: click.Context) -> None:
            """Parent command group."""
            setup_dependency_injection_context(ctx)
            store_context_data(ctx, "parent_config", {"parent": True})

        @parent_group.command()
        @click.pass_context
        def child_command(ctx: click.Context) -> None:
            """Child command that accesses parent context."""
            # Child can access parent context data
            parent_config = retrieve_context_data(ctx.parent, "parent_config")
            assert parent_config == {"parent": True}

            # Child can setup its own context
            store_context_data(ctx, "child_config", {"child": True})

            # Verify child context
            child_config = retrieve_context_data(ctx, "child_config")
            assert child_config == {"child": True}

            # Verify context keys for both parent and child
            parent_keys = get_context_keys(ctx.parent)
            assert "parent_config" in parent_keys
            assert "di_metadata" in parent_keys

            child_keys = get_context_keys(ctx)
            assert "child_config" in child_keys

        # Execute the command hierarchy
        runner = click.testing.CliRunner()
        result = runner.invoke(parent_group, ["child-command"])

        # Verify command executed successfully
        assert result.exit_code == 0

    def test_click_context_integration_when_error_handling_then_maintains_context_safety(
        self,
    ):
        """Test error handling maintains context safety and integrity."""

        @click.command()
        @click.pass_context
        def error_prone_command(ctx: click.Context) -> None:
            """Command that tests error handling with context."""
            setup_dependency_injection_context(ctx)

            # Store some initial data
            store_context_data(ctx, "initial_data", {"status": "started"})

            # Attempt operation that might fail
            try:
                # This should fail due to type mismatch
                store_typed_context_data(ctx, "bad_data", "string", int)
                raise AssertionError("Should have raised ClickIntegrationError")
            except Exception:
                # Error occurred, but context should still be accessible
                initial_data = retrieve_context_data(ctx, "initial_data")
                assert initial_data == {"status": "started"}

                # Store recovery data
                store_context_data(ctx, "recovery_data", {"status": "recovered"})

            # Verify both initial and recovery data exist
            keys = get_context_keys(ctx)
            assert "initial_data" in keys
            assert "recovery_data" in keys
            assert "bad_data" not in keys  # Failed storage shouldn't persist

        # Execute the command
        runner = click.testing.CliRunner()
        result = runner.invoke(error_prone_command, [])

        # Verify command executed successfully despite internal error handling
        assert result.exit_code == 0

    def test_click_context_integration_when_multiple_spec_contexts_then_isolation_maintained(
        self,
    ):
        """Test multiple SpecContext instances maintain proper isolation."""

        @click.command()
        @click.option("--context-id", required=True)
        @click.pass_context
        def multi_context_command(ctx: click.Context, context_id: str) -> None:
            """Command that manages multiple contexts."""
            setup_dependency_injection_context(ctx)

            # Create and integrate first SpecContext
            spec_context1 = SpecContext()
            integrate_spec_context(ctx, spec_context1)

            # Store context-specific data
            store_context_data(
                ctx,
                f"context_{context_id}_data",
                {"id": context_id, "type": "spec_context"},
            )

            # Verify retrieval
            retrieved_context = retrieve_spec_context(ctx)
            assert retrieved_context is spec_context1

            context_data = retrieve_context_data(ctx, f"context_{context_id}_data")
            assert context_data["id"] == context_id

        # Test with multiple context IDs
        runner = click.testing.CliRunner()

        # Execute with first context ID
        result1 = runner.invoke(multi_context_command, ["--context-id", "test1"])
        assert result1.exit_code == 0

        # Execute with second context ID
        result2 = runner.invoke(multi_context_command, ["--context-id", "test2"])
        assert result2.exit_code == 0

    def test_click_context_integration_when_concurrent_operations_then_thread_safety_maintained(
        self,
    ):
        """Test context integration maintains thread safety during concurrent operations."""

        import threading
        import time

        results = []
        errors = []

        def worker(worker_id: int) -> None:
            """Worker function for concurrent testing."""
            try:

                @click.command()
                @click.pass_context
                def worker_command(ctx: click.Context) -> None:
                    """Worker command for concurrent testing."""
                    setup_dependency_injection_context(ctx)

                    # Store worker-specific data
                    worker_data = {
                        "worker_id": worker_id,
                        "timestamp": time.time(),
                        "thread_id": threading.current_thread().ident,
                    }
                    store_context_data(ctx, f"worker_{worker_id}", worker_data)

                    # Brief delay to increase chance of race conditions
                    time.sleep(0.01)

                    # Verify data integrity
                    retrieved_data = retrieve_context_data(ctx, f"worker_{worker_id}")
                    assert retrieved_data["worker_id"] == worker_id

                    results.append(worker_id)

                # Execute worker command
                runner = click.testing.CliRunner()
                result = runner.invoke(worker_command, [])
                assert result.exit_code == 0

            except Exception as e:
                errors.append(f"Worker {worker_id}: {e}")

        # Create and start multiple worker threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert set(results) == {0, 1, 2, 3, 4}


class TestCrossSliceIntegration:
    """Test integration requirements for future slices."""

    def test_p2_1b_to_p2_2a_click_decorator_compatibility(self):
        """Validates Click context integration supports P2.2a decorator requirements."""

        # Simulate what P2.2a decorators will need
        @click.command()
        @click.pass_context
        def future_decorated_command(ctx: click.Context) -> None:
            """Command that simulates P2.2a decorator usage."""
            # P2.2a will need to setup dependency injection
            setup_dependency_injection_context(ctx)

            # P2.2a will need to store dependency configuration
            dependency_config = {
                "auto_inject": True,
                "factory_type": "cli",
                "dependencies": ["spec_context", "config", "logger"],
            }
            store_typed_context_data(ctx, "dependency_config", dependency_config, dict)

            # P2.2a will need to integrate SpecContext
            spec_context = SpecContext()
            integrate_spec_context(ctx, spec_context)

            # Verify P2.2a requirements are met
            retrieved_config = retrieve_typed_context_data(
                ctx, "dependency_config", dict
            )
            assert retrieved_config["auto_inject"] is True
            assert retrieved_config["factory_type"] == "cli"

            retrieved_context = retrieve_spec_context(ctx)
            assert retrieved_context is spec_context

            # Verify context keys available for P2.2a
            keys = get_context_keys(ctx)
            assert "dependency_config" in keys
            assert "spec_context" in keys
            assert "di_metadata" in keys

        # Execute to verify compatibility
        runner = click.testing.CliRunner()
        result = runner.invoke(future_decorated_command, [])
        assert result.exit_code == 0

    def test_click_integration_implements_p2_1a_requirements(self):
        """Validates integration implementation satisfies P2.1a analysis requirements."""

        # Test requirement: Context storage and retrieval
        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Requirement: Safe context storage
        setup_dependency_injection_context(ctx)
        store_context_data(ctx, "test_data", {"safe": True})

        # Requirement: Type-safe retrieval
        retrieved = retrieve_context_data(ctx, "test_data")
        assert retrieved == {"safe": True}

        # Requirement: Error handling
        with pytest.raises(Exception):  # Should handle invalid operations safely
            store_typed_context_data(ctx, "bad_data", "string", int)

        # Requirement: Context validation
        from spec_cli.utils.click_utils import validate_click_context

        assert validate_click_context(ctx) is True

        # Requirement: Context cleanup
        teardown_dependency_injection_context(ctx)
        keys = get_context_keys(ctx)
        assert len(keys) == 0  # All spec data should be cleared


class TestDependencyInjectionMigrationContext:
    """Test Click integration supports dependency injection migration patterns."""

    def test_click_context_integration_spec_context_storage(self):
        """Validates Click context can store and retrieve SpecContext objects."""

        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Create SpecContext as would be done in DI migration
        spec_context = SpecContext()

        # Integrate with Click context
        integrate_spec_context(ctx, spec_context)

        # Verify storage and retrieval
        retrieved = retrieve_spec_context(ctx)
        assert retrieved is spec_context

        # Verify context metadata
        keys = get_context_keys(ctx)
        assert "spec_context" in keys

    def test_click_integration_dependency_injection_readiness(self):
        """Validates Click integration supports dependency injection patterns."""

        cmd = click.Command("test")
        ctx = click.Context(cmd)

        # Setup DI context
        setup_dependency_injection_context(ctx)

        # Store DI configuration
        di_config = {
            "pattern": "dependency_injection",
            "factory_type": "cli",
            "singleton_migration": True,
        }
        store_typed_context_data(ctx, "di_config", di_config, dict)

        # Store SpecContext for DI
        spec_context = SpecContext()
        integrate_spec_context(ctx, spec_context)

        # Verify DI readiness
        retrieved_config = retrieve_typed_context_data(ctx, "di_config", dict)
        assert retrieved_config["pattern"] == "dependency_injection"
        assert retrieved_config["singleton_migration"] is True

        retrieved_context = retrieve_spec_context(ctx)
        assert retrieved_context is spec_context

        # Verify metadata indicates DI setup
        metadata = retrieve_context_data(ctx, "di_metadata")
        assert metadata["initialized"] is True
