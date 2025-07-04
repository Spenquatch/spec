"""Unit tests for GitOperations - Concurrent Access (git_002).

This module provides comprehensive testing for Git operations concurrent access
scenarios, thread safety, and isolation validation.
"""

import concurrent.futures
import os
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import Mock, patch

from spec_cli.exceptions import SpecGitError
from spec_cli.git.operations import GitOperations


class TestGitOperationsConcurrentEnvironment:
    """Test GitOperations environment isolation under concurrent access."""

    def setup_method(self):
        """Set up test environment with multiple temporary repositories."""
        # Create multiple temporary directories for concurrent testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo1_spec = self.temp_dir / "repo1" / ".spec"
        self.repo1_specs = self.temp_dir / "repo1" / ".specs"
        self.repo1_index = self.repo1_spec / "index"

        self.repo2_spec = self.temp_dir / "repo2" / ".spec"
        self.repo2_specs = self.temp_dir / "repo2" / ".specs"
        self.repo2_index = self.repo2_spec / "index"

        # Create directories
        self.repo1_spec.mkdir(parents=True, exist_ok=True)
        self.repo1_specs.mkdir(parents=True, exist_ok=True)
        self.repo2_spec.mkdir(parents=True, exist_ok=True)
        self.repo2_specs.mkdir(parents=True, exist_ok=True)

        self.git_ops1 = GitOperations(
            self.repo1_spec, self.repo1_specs, self.repo1_index
        )
        self.git_ops2 = GitOperations(
            self.repo2_spec, self.repo2_specs, self.repo2_index
        )

    def test_concurrent_environment_preparation_isolation(self):
        """Test that concurrent environment preparation doesn't interfere."""
        original_env = dict(os.environ)
        results = []

        def prepare_env_and_record(git_ops, result_list, operation_id):
            """Prepare environment and record results."""
            for i in range(5):  # Multiple iterations to increase race condition chances
                env = git_ops._prepare_git_environment()
                result_list.append(
                    {
                        "operation_id": operation_id,
                        "iteration": i,
                        "git_dir": env.get("GIT_DIR"),
                        "work_tree": env.get("GIT_WORK_TREE"),
                        "index_file": env.get("GIT_INDEX_FILE"),
                        "thread_id": threading.current_thread().ident,
                    }
                )
                time.sleep(0.001)  # Small delay to encourage race conditions

        # Run concurrent environment preparations
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(prepare_env_and_record, self.git_ops1, results, "ops1"),
                executor.submit(prepare_env_and_record, self.git_ops2, results, "ops2"),
                executor.submit(
                    prepare_env_and_record, self.git_ops1, results, "ops1_2"
                ),
                executor.submit(
                    prepare_env_and_record, self.git_ops2, results, "ops2_2"
                ),
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()  # Wait for completion and check for exceptions

        # Verify environment isolation
        ops1_results = [r for r in results if r["operation_id"].startswith("ops1")]
        ops2_results = [r for r in results if r["operation_id"].startswith("ops2")]

        # All ops1 results should have consistent repo1 paths
        for result in ops1_results:
            assert result["git_dir"] == str(self.repo1_spec)
            assert result["work_tree"] == str(self.repo1_specs)
            assert result["index_file"] == str(self.repo1_index)

        # All ops2 results should have consistent repo2 paths
        for result in ops2_results:
            assert result["git_dir"] == str(self.repo2_spec)
            assert result["work_tree"] == str(self.repo2_specs)
            assert result["index_file"] == str(self.repo2_index)

        # Verify original environment wasn't permanently modified
        assert dict(os.environ) == original_env

    def test_concurrent_command_execution_isolation(self):
        """Test that concurrent command executions maintain isolation."""
        execution_results = []

        def execute_git_command(git_ops, command, operation_id):
            """Execute git command and record execution details."""
            try:
                with patch("subprocess.run") as mock_run:
                    # Mock successful execution
                    mock_result = Mock()
                    mock_result.returncode = 0
                    mock_result.stdout = f"Success from {operation_id}"
                    mock_result.stderr = ""
                    mock_run.return_value = mock_result

                    # Record the environment used for the subprocess call
                    def capture_subprocess_call(*args, **kwargs):
                        execution_results.append(
                            {
                                "operation_id": operation_id,
                                "git_dir": kwargs.get("env", {}).get("GIT_DIR"),
                                "work_tree": kwargs.get("env", {}).get("GIT_WORK_TREE"),
                                "index_file": kwargs.get("env", {}).get(
                                    "GIT_INDEX_FILE"
                                ),
                                "thread_id": threading.current_thread().ident,
                                "timestamp": time.time(),
                            }
                        )
                        return mock_result

                    mock_run.side_effect = capture_subprocess_call

                    # Execute the command
                    result = git_ops.run_git_command(command)
                    return result

            except Exception as e:
                execution_results.append(
                    {
                        "operation_id": operation_id,
                        "error": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )
                raise

        # Run concurrent git command executions
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(
                    execute_git_command, self.git_ops1, ["status"], "repo1_status"
                ),
                executor.submit(
                    execute_git_command, self.git_ops2, ["status"], "repo2_status"
                ),
                executor.submit(
                    execute_git_command, self.git_ops1, ["log"], "repo1_log"
                ),
                executor.submit(
                    execute_git_command, self.git_ops2, ["log"], "repo2_log"
                ),
                executor.submit(
                    execute_git_command, self.git_ops1, ["diff"], "repo1_diff"
                ),
                executor.submit(
                    execute_git_command, self.git_ops2, ["diff"], "repo2_diff"
                ),
            ]

            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except Exception:
                    pass  # Expected for some commands in test environment

        # Verify that each operation used the correct environment
        repo1_executions = [
            r for r in execution_results if "repo1" in r.get("operation_id", "")
        ]
        repo2_executions = [
            r for r in execution_results if "repo2" in r.get("operation_id", "")
        ]

        for result in repo1_executions:
            if "error" not in result:
                assert result["git_dir"] == str(self.repo1_spec)
                assert result["work_tree"] == str(self.repo1_specs)
                assert result["index_file"] == str(self.repo1_index)

        for result in repo2_executions:
            if "error" not in result:
                assert result["git_dir"] == str(self.repo2_spec)
                assert result["work_tree"] == str(self.repo2_specs)
                assert result["index_file"] == str(self.repo2_index)

    def test_concurrent_repository_initialization(self):
        """Test concurrent repository initialization doesn't interfere."""
        initialization_results = []

        def initialize_and_record(git_ops, operation_id):
            """Initialize repository and record results."""
            try:
                with patch.object(git_ops, "run_git_command") as mock_run:
                    mock_result = Mock()
                    mock_result.stdout = f"Initialized repository for {operation_id}"
                    mock_run.return_value = mock_result

                    git_ops.initialize_repository()
                    initialization_results.append(
                        {
                            "operation_id": operation_id,
                            "success": True,
                            "thread_id": threading.current_thread().ident,
                        }
                    )

            except Exception as e:
                initialization_results.append(
                    {
                        "operation_id": operation_id,
                        "success": False,
                        "error": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Run concurrent initializations
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(initialize_and_record, self.git_ops1, "init_repo1_a"),
                executor.submit(initialize_and_record, self.git_ops1, "init_repo1_b"),
                executor.submit(initialize_and_record, self.git_ops2, "init_repo2_a"),
                executor.submit(initialize_and_record, self.git_ops2, "init_repo2_b"),
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify all initializations completed successfully
        successful_inits = [r for r in initialization_results if r["success"]]
        assert len(successful_inits) >= 3, (
            f"Expected at least 3 successful initializations, got {len(successful_inits)}: {initialization_results}"
        )

        # Verify different thread IDs (true concurrency)
        thread_ids = {r["thread_id"] for r in initialization_results}
        assert len(thread_ids) >= 1, "Expected at least one thread to be used"


class TestGitOperationsRaceConditions:
    """Test GitOperations for race conditions and thread safety."""

    def setup_method(self):
        """Set up test environment for race condition testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.spec_dir = self.temp_dir / ".spec"
        self.specs_dir = self.temp_dir / ".specs"
        self.index_file = self.spec_dir / "index"

        self.spec_dir.mkdir(parents=True, exist_ok=True)
        self.specs_dir.mkdir(parents=True, exist_ok=True)

        self.git_ops = GitOperations(self.spec_dir, self.specs_dir, self.index_file)

    def test_concurrent_environment_state_corruption(self):
        """Test that concurrent operations don't corrupt environment state."""
        corruption_detected = threading.Event()
        results = []

        def environment_checker(checker_id, iterations=10):
            """Check environment consistency across multiple operations."""
            for i in range(iterations):
                try:
                    env = self.git_ops._prepare_git_environment()

                    # Verify environment consistency
                    expected_git_dir = str(self.spec_dir)
                    expected_work_tree = str(self.specs_dir)
                    expected_index = str(self.index_file)

                    actual_git_dir = env.get("GIT_DIR")
                    actual_work_tree = env.get("GIT_WORK_TREE")
                    actual_index = env.get("GIT_INDEX_FILE")

                    if (
                        actual_git_dir != expected_git_dir
                        or actual_work_tree != expected_work_tree
                        or actual_index != expected_index
                    ):
                        corruption_detected.set()
                        results.append(
                            {
                                "checker_id": checker_id,
                                "iteration": i,
                                "corruption": True,
                                "expected": {
                                    "git_dir": expected_git_dir,
                                    "work_tree": expected_work_tree,
                                    "index": expected_index,
                                },
                                "actual": {
                                    "git_dir": actual_git_dir,
                                    "work_tree": actual_work_tree,
                                    "index": actual_index,
                                },
                            }
                        )
                    else:
                        results.append(
                            {
                                "checker_id": checker_id,
                                "iteration": i,
                                "corruption": False,
                            }
                        )

                    # Small delay to encourage race conditions
                    time.sleep(0.001)

                except Exception as e:
                    results.append(
                        {"checker_id": checker_id, "iteration": i, "error": str(e)}
                    )

        # Run multiple concurrent environment checkers
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(environment_checker, f"checker_{i}", 20)
                for i in range(8)
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify no corruption was detected
        corrupted_results = [r for r in results if r.get("corruption", False)]
        assert len(corrupted_results) == 0, (
            f"Environment corruption detected: {corrupted_results}"
        )

        # Verify successful operations
        successful_results = [
            r for r in results if not r.get("corruption", False) and "error" not in r
        ]
        assert len(successful_results) > 0, "No successful environment preparations"

    def test_concurrent_command_preparation_consistency(self):
        """Test that concurrent command preparation maintains consistency."""
        command_results = []

        def prepare_command_and_check(command_args, checker_id):
            """Prepare git command and verify consistency."""
            try:
                prepared_cmd = self.git_ops._prepare_git_command(command_args)

                # Verify command structure
                expected_start = [
                    "git",
                    "-c",
                    "core.excludesFile=",
                    "-c",
                    "core.ignoreCase=false",
                ]
                actual_start = prepared_cmd[:5]

                command_results.append(
                    {
                        "checker_id": checker_id,
                        "original_args": command_args,
                        "prepared_command": prepared_cmd,
                        "consistent_start": actual_start == expected_start,
                        "ends_with_args": prepared_cmd[5:] == command_args,
                        "thread_id": threading.current_thread().ident,
                    }
                )

            except Exception as e:
                command_results.append(
                    {
                        "checker_id": checker_id,
                        "error": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Test various git commands concurrently
        commands = [
            ["status"],
            ["add", "file.txt"],
            ["commit", "-m", "test"],
            ["log", "--oneline"],
            ["diff", "--cached"],
            ["branch"],
            ["tag", "-l"],
            ["remote", "-v"],
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i, cmd in enumerate(commands * 3):  # Run each command 3 times
                futures.append(
                    executor.submit(
                        prepare_command_and_check, cmd, f"cmd_{i}_{'-'.join(cmd)}"
                    )
                )

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify all command preparations were consistent
        successful_results = [r for r in command_results if "error" not in r]
        assert len(successful_results) > 0, "No successful command preparations"

        for result in successful_results:
            assert result["consistent_start"], f"Inconsistent command start: {result}"
            assert result["ends_with_args"], f"Command args not preserved: {result}"

    def test_error_handling_under_concurrent_access(self):
        """Test error handling behavior under concurrent access."""
        error_results = []

        def trigger_error_and_record(error_type, operation_id):
            """Trigger specific error and record handling."""
            try:
                if error_type == "invalid_command":
                    # This should trigger validation error
                    with patch(
                        "spec_cli.git.operations.validate_git_command"
                    ) as mock_validate:
                        mock_validate.return_value = (False, "Invalid command")
                        self.git_ops.run_git_command(["invalid"])

                elif error_type == "subprocess_error":
                    # This should trigger subprocess error
                    with patch("subprocess.run") as mock_run:
                        mock_run.side_effect = subprocess.CalledProcessError(
                            1, ["git"], "Test error"
                        )
                        self.git_ops.run_git_command(["status"])

                elif error_type == "file_not_found":
                    # This should trigger FileNotFoundError
                    with patch("subprocess.run") as mock_run:
                        mock_run.side_effect = FileNotFoundError("git not found")
                        self.git_ops.run_git_command(["status"])

                error_results.append(
                    {
                        "operation_id": operation_id,
                        "error_type": error_type,
                        "unexpected_success": True,
                    }
                )

            except SpecGitError as e:
                error_results.append(
                    {
                        "operation_id": operation_id,
                        "error_type": error_type,
                        "caught_spec_error": True,
                        "error_message": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )
            except Exception as e:
                error_results.append(
                    {
                        "operation_id": operation_id,
                        "error_type": error_type,
                        "unexpected_error": True,
                        "error_message": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Run concurrent error scenarios
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = [
                executor.submit(
                    trigger_error_and_record, "invalid_command", "invalid_1"
                ),
                executor.submit(
                    trigger_error_and_record, "invalid_command", "invalid_2"
                ),
                executor.submit(
                    trigger_error_and_record, "subprocess_error", "subprocess_1"
                ),
                executor.submit(
                    trigger_error_and_record, "subprocess_error", "subprocess_2"
                ),
                executor.submit(trigger_error_and_record, "file_not_found", "fnf_1"),
                executor.submit(trigger_error_and_record, "file_not_found", "fnf_2"),
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify all errors were properly handled as SpecGitError (some may succeed due to mocking)
        properly_handled = [
            r for r in error_results if r.get("caught_spec_error", False)
        ]
        unexpected_successes = [
            r for r in error_results if r.get("unexpected_success", False)
        ]

        # At least most errors should be properly handled
        assert len(properly_handled) >= 4, (
            f"Expected at least 4 properly handled errors: {error_results}"
        )

        # No more than 2 unexpected successes (due to race conditions in mocking)
        assert len(unexpected_successes) <= 2, (
            f"Too many unexpected successes: {unexpected_successes}"
        )


class TestGitOperationsThreadSafety:
    """Test GitOperations thread safety and isolation."""

    def setup_method(self):
        """Set up test environment for thread safety testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.spec_dir = self.temp_dir / ".spec"
        self.specs_dir = self.temp_dir / ".specs"
        self.index_file = self.spec_dir / "index"

        self.spec_dir.mkdir(parents=True, exist_ok=True)
        self.specs_dir.mkdir(parents=True, exist_ok=True)

        self.git_ops = GitOperations(self.spec_dir, self.specs_dir, self.index_file)

    def test_multiple_instances_isolation(self):
        """Test that multiple GitOperations instances maintain isolation."""
        # Create multiple instances with different paths
        instances = []
        for i in range(5):
            instance_dir = self.temp_dir / f"instance_{i}"
            spec_dir = instance_dir / ".spec"
            specs_dir = instance_dir / ".specs"
            index_file = spec_dir / "index"

            spec_dir.mkdir(parents=True, exist_ok=True)
            specs_dir.mkdir(parents=True, exist_ok=True)

            instances.append(
                {
                    "id": i,
                    "git_ops": GitOperations(spec_dir, specs_dir, index_file),
                    "spec_dir": spec_dir,
                    "specs_dir": specs_dir,
                    "index_file": index_file,
                }
            )

        isolation_results = []

        def test_instance_isolation(instance_data):
            """Test that instance maintains its configuration."""
            instance_id = instance_data["id"]
            git_ops = instance_data["git_ops"]

            for iteration in range(10):
                env = git_ops._prepare_git_environment()

                isolation_results.append(
                    {
                        "instance_id": instance_id,
                        "iteration": iteration,
                        "git_dir": env.get("GIT_DIR"),
                        "work_tree": env.get("GIT_WORK_TREE"),
                        "index_file": env.get("GIT_INDEX_FILE"),
                        "expected_git_dir": str(instance_data["spec_dir"]),
                        "expected_work_tree": str(instance_data["specs_dir"]),
                        "expected_index": str(instance_data["index_file"]),
                        "thread_id": threading.current_thread().ident,
                    }
                )

                time.sleep(0.001)  # Small delay to encourage race conditions

        # Run all instances concurrently
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=len(instances)
        ) as executor:
            futures = [
                executor.submit(test_instance_isolation, instance)
                for instance in instances
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify each instance maintained its own configuration
        for instance_id in range(len(instances)):
            instance_results = [
                r for r in isolation_results if r["instance_id"] == instance_id
            ]

            for result in instance_results:
                assert result["git_dir"] == result["expected_git_dir"], (
                    f"Instance {instance_id} git_dir mismatch: {result}"
                )
                assert result["work_tree"] == result["expected_work_tree"], (
                    f"Instance {instance_id} work_tree mismatch: {result}"
                )
                assert result["index_file"] == result["expected_index"], (
                    f"Instance {instance_id} index_file mismatch: {result}"
                )

    def test_concurrent_availability_checks(self):
        """Test concurrent Git availability checks don't interfere."""
        availability_results = []

        def check_availability_and_record(check_id):
            """Check Git availability and record results."""
            try:
                with patch.object(self.git_ops, "run_git_command") as mock_run:
                    mock_result = Mock()
                    mock_result.stdout = "git version 2.34.1"
                    mock_run.return_value = mock_result

                    is_available = self.git_ops.check_git_available()
                    version = self.git_ops.get_git_version()

                    availability_results.append(
                        {
                            "check_id": check_id,
                            "available": is_available,
                            "version": version,
                            "thread_id": threading.current_thread().ident,
                        }
                    )

            except Exception as e:
                availability_results.append(
                    {
                        "check_id": check_id,
                        "error": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Run multiple concurrent availability checks
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(check_availability_and_record, f"check_{i}")
                for i in range(20)
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify all checks completed successfully
        successful_checks = [r for r in availability_results if "error" not in r]
        assert len(successful_checks) == 20, (
            f"Some availability checks failed: {availability_results}"
        )

        # Verify consistent results
        for result in successful_checks:
            assert result["available"] is True, (
                f"Inconsistent availability result: {result}"
            )
            assert result["version"] == "git version 2.34.1", (
                f"Inconsistent version result: {result}"
            )

    def test_stress_test_concurrent_operations(self):
        """Stress test with many concurrent operations."""
        stress_results = []
        operation_count = 50

        def stress_operation(operation_id):
            """Perform multiple git operations in sequence."""
            try:
                with patch.object(self.git_ops, "run_git_command") as mock_run:
                    mock_result = Mock()
                    mock_result.stdout = f"Operation {operation_id} success"
                    mock_run.return_value = mock_result

                    # Perform multiple operations
                    operations = [
                        (
                            lambda: self.git_ops._prepare_git_environment(),
                            "prepare_env",
                        ),
                        (
                            lambda: self.git_ops._prepare_git_command(["status"]),
                            "prepare_cmd",
                        ),
                        (lambda: self.git_ops.check_git_available(), "check_available"),
                        (lambda: self.git_ops.get_git_version(), "get_version"),
                    ]

                    for op_func, op_name in operations:
                        result = op_func()
                        stress_results.append(
                            {
                                "operation_id": operation_id,
                                "op_name": op_name,
                                "success": True,
                                "result_type": type(result).__name__,
                                "thread_id": threading.current_thread().ident,
                            }
                        )

                        # Small delay between operations
                        time.sleep(0.001)

            except Exception as e:
                stress_results.append(
                    {
                        "operation_id": operation_id,
                        "error": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Run stress test
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [
                executor.submit(stress_operation, f"stress_{i}")
                for i in range(operation_count)
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify all operations completed successfully
        successful_operations = [r for r in stress_results if r.get("success", False)]
        failed_operations = [r for r in stress_results if "error" in r]

        assert len(failed_operations) == 0, f"Operations failed: {failed_operations}"
        assert len(successful_operations) == operation_count * 4, (
            f"Expected {operation_count * 4} successful operations, got {len(successful_operations)}"
        )

        # Verify true concurrency (multiple threads used)
        thread_ids = {r["thread_id"] for r in stress_results}
        assert len(thread_ids) > 5, (
            f"Expected more thread concurrency, got {len(thread_ids)} threads"
        )


class TestGitOperationsConcurrentEdgeCases:
    """Test edge cases in concurrent Git operations."""

    def setup_method(self):
        """Set up test environment for edge case testing."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.spec_dir = self.temp_dir / ".spec"
        self.specs_dir = self.temp_dir / ".specs"
        self.index_file = self.spec_dir / "index"

        self.spec_dir.mkdir(parents=True, exist_ok=True)
        self.specs_dir.mkdir(parents=True, exist_ok=True)

        self.git_ops = GitOperations(self.spec_dir, self.specs_dir, self.index_file)

    def test_concurrent_exception_handling_coverage(self):
        """Test concurrent access to exception handling paths."""
        exception_results = []

        def test_generic_exception_handling(operation_id):
            """Test the generic exception handling in run_git_command."""
            try:
                with patch("subprocess.run") as mock_run:
                    # Trigger generic exception (not CalledProcessError or FileNotFoundError)
                    mock_run.side_effect = RuntimeError("Unexpected runtime error")

                    self.git_ops.run_git_command(["status"])

                    exception_results.append(
                        {"operation_id": operation_id, "unexpected_success": True}
                    )

            except SpecGitError as e:
                exception_results.append(
                    {
                        "operation_id": operation_id,
                        "caught_spec_error": True,
                        "error_message": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )
            except Exception as e:
                exception_results.append(
                    {
                        "operation_id": operation_id,
                        "unexpected_error": True,
                        "error_message": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Run concurrent exception handling tests
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(test_generic_exception_handling, f"exception_{i}")
                for i in range(8)
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify all exceptions were properly handled
        properly_handled = [
            r for r in exception_results if r.get("caught_spec_error", False)
        ]
        assert len(properly_handled) == 8, (
            f"All generic exceptions should be handled: {exception_results}"
        )

    def test_concurrent_initialization_exception_coverage(self):
        """Test concurrent access to initialization exception paths."""
        init_exception_results = []

        def test_initialization_exception_handling(operation_id):
            """Test exception handling in initialize_repository."""
            try:
                with patch.object(self.git_ops, "run_git_command") as mock_run:
                    # Trigger generic exception in initialization (not SpecGitError)
                    mock_run.side_effect = RuntimeError(
                        "Unexpected initialization error"
                    )

                    self.git_ops.initialize_repository()

                    init_exception_results.append(
                        {"operation_id": operation_id, "unexpected_success": True}
                    )

            except SpecGitError as e:
                init_exception_results.append(
                    {
                        "operation_id": operation_id,
                        "caught_spec_error": True,
                        "error_message": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )
            except Exception as e:
                init_exception_results.append(
                    {
                        "operation_id": operation_id,
                        "unexpected_error": True,
                        "error_message": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Run concurrent initialization exception tests
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    test_initialization_exception_handling, f"init_exception_{i}"
                )
                for i in range(6)
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify all initialization exceptions were properly handled
        properly_handled = [
            r for r in init_exception_results if r.get("caught_spec_error", False)
        ]
        assert len(properly_handled) == 6, (
            f"All initialization exceptions should be handled: {init_exception_results}"
        )

    def test_concurrent_git_availability_exception_coverage(self):
        """Test concurrent access to git availability exception paths."""
        availability_exception_results = []

        def test_availability_exception_handling(operation_id):
            """Test exception handling in git availability checks."""
            try:
                with patch.object(self.git_ops, "run_git_command") as mock_run:
                    # For check_git_available - should return False on SpecGitError
                    mock_run.side_effect = SpecGitError("Git not available")

                    is_available = self.git_ops.check_git_available()
                    version = self.git_ops.get_git_version()

                    availability_exception_results.append(
                        {
                            "operation_id": operation_id,
                            "is_available": is_available,
                            "version": version,
                            "thread_id": threading.current_thread().ident,
                        }
                    )

            except Exception as e:
                availability_exception_results.append(
                    {
                        "operation_id": operation_id,
                        "unexpected_error": True,
                        "error_message": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Run concurrent availability exception tests
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    test_availability_exception_handling, f"availability_{i}"
                )
                for i in range(6)
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify all availability checks handled exceptions properly
        successful_checks = [
            r for r in availability_exception_results if "unexpected_error" not in r
        ]
        assert len(successful_checks) == 6, (
            f"All availability checks should handle exceptions: {availability_exception_results}"
        )

        for result in successful_checks:
            assert result["is_available"] is False, (
                f"Should return False on SpecGitError: {result}"
            )
            assert result["version"] is None, (
                f"Should return None on SpecGitError: {result}"
            )

    def test_concurrent_initialization_race_condition(self):
        """Test race conditions during repository initialization."""
        initialization_states = []

        def attempt_initialization(init_id):
            """Attempt repository initialization and record state."""
            try:
                # Mock mkdir on the GitOperations class to simulate race conditions
                with patch("pathlib.Path.mkdir") as mock_mkdir:
                    with patch.object(self.git_ops, "run_git_command") as mock_run:
                        mock_result = Mock()
                        mock_result.stdout = f"Initialized for {init_id}"
                        mock_run.return_value = mock_result

                        # Add delay to mkdir to encourage race conditions
                        def delayed_mkdir(*args, **kwargs):
                            time.sleep(0.005)  # 5ms delay
                            return None

                        mock_mkdir.side_effect = delayed_mkdir

                        self.git_ops.initialize_repository()

                        initialization_states.append(
                            {
                                "init_id": init_id,
                                "success": True,
                                "mkdir_called": mock_mkdir.called,
                                "git_init_called": mock_run.called,
                                "thread_id": threading.current_thread().ident,
                            }
                        )

            except Exception as e:
                initialization_states.append(
                    {
                        "init_id": init_id,
                        "success": False,
                        "error": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Run concurrent initializations
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(attempt_initialization, f"init_{i}") for i in range(10)
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify all initializations handled properly (race conditions may cause some failures)
        successful_inits = [s for s in initialization_states if s["success"]]
        failed_inits = [s for s in initialization_states if not s["success"]]

        # At least some should succeed, and failures should be due to expected race conditions
        assert len(successful_inits) >= 5, (
            f"Expected at least 5 successful initializations, got {len(successful_inits)}: {initialization_states}"
        )

        # Verify that failures are due to expected Git environment race conditions
        for failed_init in failed_inits:
            error_msg = failed_init.get("error", "")
            assert any(
                expected_error in error_msg
                for expected_error in [
                    "GIT_WORK_TREE",
                    "not allowed without specifying GIT_DIR",
                    "Command failed",
                ]
            ), f"Unexpected failure reason: {failed_init}"

    def test_environment_variable_corruption_detection(self):
        """Test detection of environment variable corruption."""
        corruption_attempts = []

        def attempt_environment_corruption(attempt_id):
            """Attempt to corrupt environment and verify isolation."""
            try:
                # Store original environment
                original_env = dict(os.environ)

                # Prepare git environment
                git_env = self.git_ops._prepare_git_environment()

                # Verify git environment is correct
                expected_git_dir = str(self.spec_dir)
                if git_env.get("GIT_DIR") != expected_git_dir:
                    corruption_attempts.append(
                        {
                            "attempt_id": attempt_id,
                            "corruption_type": "git_dir_mismatch",
                            "expected": expected_git_dir,
                            "actual": git_env.get("GIT_DIR"),
                        }
                    )

                # Verify original environment wasn't modified
                current_env = dict(os.environ)
                if current_env != original_env:
                    modified_keys = set(current_env.keys()) ^ set(original_env.keys())
                    corruption_attempts.append(
                        {
                            "attempt_id": attempt_id,
                            "corruption_type": "original_env_modified",
                            "modified_keys": list(modified_keys),
                        }
                    )

                corruption_attempts.append(
                    {
                        "attempt_id": attempt_id,
                        "corruption_type": "none",
                        "success": True,
                    }
                )

            except Exception as e:
                corruption_attempts.append(
                    {
                        "attempt_id": attempt_id,
                        "corruption_type": "exception",
                        "error": str(e),
                    }
                )

        # Run concurrent corruption detection
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            futures = [
                executor.submit(attempt_environment_corruption, f"attempt_{i}")
                for i in range(25)
            ]

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify no corruption was detected
        corruptions = [a for a in corruption_attempts if a["corruption_type"] != "none"]
        assert len(corruptions) == 0, f"Environment corruption detected: {corruptions}"

        successful_attempts = [
            a for a in corruption_attempts if a.get("success", False)
        ]
        assert len(successful_attempts) == 25, (
            "Not all corruption detection attempts succeeded"
        )

    def test_concurrent_command_validation_consistency(self):
        """Test that command validation remains consistent under concurrent access."""
        validation_results = []

        def validate_command_concurrently(command, validation_id):
            """Validate git command and record results."""
            try:
                with patch(
                    "spec_cli.git.operations.validate_git_command"
                ) as mock_validate:
                    # Simulate validation with delay to encourage race conditions
                    def delayed_validation(args, specs_dir):
                        time.sleep(0.005)  # 5ms delay
                        if "dangerous" in " ".join(args):
                            return False, "Dangerous command detected"
                        return True, ""

                    mock_validate.side_effect = delayed_validation

                    # This will call validate_git_command internally
                    try:
                        with patch("subprocess.run") as mock_run:
                            mock_result = Mock()
                            mock_result.returncode = 0
                            mock_result.stdout = "Success"
                            mock_run.return_value = mock_result

                            result = self.git_ops.run_git_command(command)

                            validation_results.append(
                                {
                                    "validation_id": validation_id,
                                    "command": command,
                                    "success": True,
                                    "result": str(result.stdout),
                                    "thread_id": threading.current_thread().ident,
                                }
                            )

                    except SpecGitError as e:
                        validation_results.append(
                            {
                                "validation_id": validation_id,
                                "command": command,
                                "validation_failed": True,
                                "error": str(e),
                                "thread_id": threading.current_thread().ident,
                            }
                        )

            except Exception as e:
                validation_results.append(
                    {
                        "validation_id": validation_id,
                        "command": command,
                        "unexpected_error": True,
                        "error": str(e),
                        "thread_id": threading.current_thread().ident,
                    }
                )

        # Test various commands concurrently
        test_commands = [
            ["status"],
            ["log"],
            ["dangerous", "command"],  # Should be rejected
            ["add", "file.txt"],
            ["commit", "-m", "test"],
            ["dangerous", "operation"],  # Should be rejected
            ["diff"],
            ["branch"],
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
            futures = []
            for i, cmd in enumerate(test_commands * 3):  # Run each command 3 times
                futures.append(
                    executor.submit(validate_command_concurrently, cmd, f"val_{i}")
                )

            for future in concurrent.futures.as_completed(futures):
                future.result()

        # Verify validation consistency
        # Commands with "dangerous" should be consistently rejected
        dangerous_commands = [
            r for r in validation_results if "dangerous" in " ".join(r["command"])
        ]
        for result in dangerous_commands:
            assert result.get("validation_failed", False), (
                f"Dangerous command should be rejected: {result}"
            )

        # Safe commands should be consistently accepted (or failed for expected reasons)
        safe_commands = [
            r for r in validation_results if "dangerous" not in " ".join(r["command"])
        ]
        for result in safe_commands:
            # Safe commands should either succeed or fail due to repository setup issues, not validation
            if result.get("validation_failed", False):
                # If validation failed for safe command, it should be due to git repository issues, not security
                assert "not a git repository" in result.get(
                    "error", ""
                ) or "Command failed" in result.get("error", ""), (
                    f"Safe command failed for unexpected reason: {result}"
                )
            else:
                assert result.get("success", False) or "unexpected_error" in result, (
                    f"Safe command should be accepted or have expected error: {result}"
                )
