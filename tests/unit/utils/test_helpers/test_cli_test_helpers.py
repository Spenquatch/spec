"""Unit tests for CLI test infrastructure helpers.

Tests CLI command execution simulation, output capture, and user input mocking
functionality to ensure reliable testing of CLI commands.
"""

import os
import sys
from pathlib import Path
from unittest.mock import patch

import click
import pytest

from spec_cli.utils.test_helpers.cli_test_helpers import (
    CLICommandRunner,
    CLIOutputCapture,
    CLITestResult,
    UserInputMocker,
    create_cli_command_runner,
    create_cli_output_capture,
    create_user_input_mocker,
    isolated_cli_environment,
)


class TestCLICommandRunner:
    """Test CLI command runner functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.runner = create_cli_command_runner()

    def test_initialization_with_defaults(self):
        """Test CLI runner initialization with default settings."""
        runner = CLICommandRunner()

        assert runner.isolated_filesystem is True
        assert runner.mix_stderr is True
        assert runner.command_history == []
        assert runner.mock_environment == {}

    def test_initialization_with_custom_settings(self):
        """Test CLI runner initialization with custom settings."""
        runner = CLICommandRunner(isolated_filesystem=False, mix_stderr=False)

        assert runner.isolated_filesystem is False
        assert runner.mix_stderr is False

    def test_run_simple_command_success(self):
        """Test running simple successful command."""

        @click.command()
        def test_cmd():
            click.echo("Hello, World!")

        result = self.runner.run_command(test_cmd)

        assert result.success
        assert result.exit_code == 0
        assert "Hello, World!" in result.output
        assert result.exception is None
        assert result.command == "test"  # Click uses function name without "_cmd"
        assert result.args == []

    def test_run_command_with_arguments(self):
        """Test running command with arguments."""

        @click.command()
        @click.argument("name")
        @click.option("--greeting", default="Hello")
        def greet_cmd(name, greeting):
            click.echo(f"{greeting}, {name}!")

        result = self.runner.run_command(greet_cmd, args=["Alice", "--greeting", "Hi"])

        assert result.success
        assert "Hi, Alice!" in result.output
        assert result.args == ["Alice", "--greeting", "Hi"]

    def test_run_command_with_failure(self):
        """Test running command that fails."""

        @click.command()
        def failing_cmd():
            click.echo("Error occurred")
            raise click.ClickException("Test error")

        result = self.runner.run_command(failing_cmd)

        assert result.failed
        assert result.exit_code != 0
        assert "Error occurred" in result.output

    def test_run_command_with_input(self):
        """Test running command with user input."""

        @click.command()
        def input_cmd():
            name = click.prompt("Enter name")
            click.echo(f"Hello, {name}!")

        result = self.runner.run_command(input_cmd, input_data="Bob\n")

        assert result.success
        assert "Hello, Bob!" in result.output

    def test_run_command_with_environment_variables(self):
        """Test running command with environment variables."""

        @click.command()
        def env_cmd():
            value = os.environ.get("TEST_VAR", "default")
            click.echo(f"Value: {value}")

        result = self.runner.run_command(env_cmd, env={"TEST_VAR": "test_value"})

        assert result.success
        assert "Value: test_value" in result.output

    def test_set_environment_variable(self):
        """Test setting environment variables for runner."""
        self.runner.set_environment_variable("GLOBAL_VAR", "global_value")

        @click.command()
        def env_cmd():
            value = os.environ.get("GLOBAL_VAR", "default")
            click.echo(f"Value: {value}")

        result = self.runner.run_command(env_cmd)

        assert result.success
        assert "Value: global_value" in result.output

    def test_clear_environment(self):
        """Test clearing environment variables."""
        self.runner.set_environment_variable("TEST_VAR", "value")
        assert "TEST_VAR" in self.runner.mock_environment

        self.runner.clear_environment()
        assert self.runner.mock_environment == {}

    def test_command_history_tracking(self):
        """Test command execution history tracking."""

        @click.command()
        def cmd1():
            click.echo("Command 1")

        @click.command()
        def cmd2():
            click.echo("Command 2")

        self.runner.run_command(cmd1)
        self.runner.run_command(cmd2, args=["--option"])

        history = self.runner.get_command_history()
        assert len(history) == 2
        assert history[0]["command"] == "cmd1"
        assert history[0]["success"] is True
        assert history[1]["command"] == "cmd2"
        assert history[1]["args"] == ["--option"]

    def test_clear_history(self):
        """Test clearing command execution history."""

        @click.command()
        def test_cmd():
            pass

        self.runner.run_command(test_cmd)
        assert len(self.runner.command_history) == 1

        self.runner.clear_history()
        assert len(self.runner.command_history) == 0

    def test_isolated_filesystem_mode(self):
        """Test running commands in isolated filesystem."""
        runner = CLICommandRunner(isolated_filesystem=True)

        @click.command()
        def file_cmd():
            Path("test_file.txt").write_text("test content")
            if Path("test_file.txt").exists():
                click.echo("File created")

        result = runner.run_command(file_cmd)

        assert result.success
        assert "File created" in result.output
        # File should not exist outside isolated environment
        assert not Path("test_file.txt").exists()


class TestCLITestResult:
    """Test CLI test result functionality."""

    def test_successful_result(self):
        """Test result properties for successful command."""
        result = CLITestResult(0, "Success output", None, "test", ["arg1"])

        assert result.success
        assert not result.failed
        assert result.exit_code == 0
        assert result.output == "Success output"
        assert result.exception is None
        assert result.command == "test"  # Click uses function name
        assert result.args == ["arg1"]

    def test_failed_result(self):
        """Test result properties for failed command."""
        exception = Exception("Test error")
        result = CLITestResult(1, "Error output", exception, "test_cmd", [])

        assert not result.success
        assert result.failed
        assert result.exit_code == 1
        assert result.exception is exception

    def test_assert_success_with_successful_result(self):
        """Test assert_success with successful result."""
        result = CLITestResult(0, "Success", None, "test_cmd", [])
        result.assert_success()  # Should not raise

    def test_assert_success_with_failed_result(self):
        """Test assert_success with failed result."""
        result = CLITestResult(1, "Error", None, "test_cmd", [])

        with pytest.raises(AssertionError, match="Command 'test_cmd' failed"):
            result.assert_success()

    def test_assert_success_with_custom_message(self):
        """Test assert_success with custom error message."""
        result = CLITestResult(1, "Error", None, "test_cmd", [])

        with pytest.raises(AssertionError, match="Custom error message"):
            result.assert_success("Custom error message")

    def test_assert_failure_with_failed_result(self):
        """Test assert_failure with failed result."""
        result = CLITestResult(1, "Error", None, "test_cmd", [])
        result.assert_failure()  # Should not raise

    def test_assert_failure_with_successful_result(self):
        """Test assert_failure with successful result."""
        result = CLITestResult(0, "Success", None, "test_cmd", [])

        with pytest.raises(AssertionError, match="succeeded when failure was expected"):
            result.assert_failure()

    def test_assert_failure_with_specific_exit_code(self):
        """Test assert_failure with specific expected exit code."""
        result = CLITestResult(2, "Error", None, "test_cmd", [])
        result.assert_failure(2)  # Should not raise

        with pytest.raises(AssertionError, match="failed with exit code 2, expected 1"):
            result.assert_failure(1)

    def test_assert_output_contains_success(self):
        """Test assert_output_contains with matching text."""
        result = CLITestResult(0, "Hello, World!", None, "test_cmd", [])
        result.assert_output_contains("Hello")  # Should not raise

    def test_assert_output_contains_failure(self):
        """Test assert_output_contains with non-matching text."""
        result = CLITestResult(0, "Hello, World!", None, "test_cmd", [])

        with pytest.raises(AssertionError, match="Output does not contain 'Goodbye'"):
            result.assert_output_contains("Goodbye")

    def test_assert_output_not_contains_success(self):
        """Test assert_output_not_contains with non-matching text."""
        result = CLITestResult(0, "Hello, World!", None, "test_cmd", [])
        result.assert_output_not_contains("Goodbye")  # Should not raise

    def test_assert_output_not_contains_failure(self):
        """Test assert_output_not_contains with matching text."""
        result = CLITestResult(0, "Hello, World!", None, "test_cmd", [])

        with pytest.raises(
            AssertionError, match="Output contains 'Hello' when it shouldn't"
        ):
            result.assert_output_not_contains("Hello")


class TestCLIOutputCapture:
    """Test CLI output capture functionality."""

    def test_initialization_with_defaults(self):
        """Test output capture initialization with defaults."""
        capture = CLIOutputCapture()

        assert capture.capture_stdout is True
        assert capture.capture_stderr is True

    def test_initialization_with_custom_settings(self):
        """Test output capture initialization with custom settings."""
        capture = CLIOutputCapture(capture_stdout=False, capture_stderr=True)

        assert capture.capture_stdout is False
        assert capture.capture_stderr is True

    def test_capture_stdout(self):
        """Test capturing stdout output."""
        capture = CLIOutputCapture(capture_stdout=True, capture_stderr=False)

        with capture.capture():
            print("Test stdout output")

        assert "Test stdout output" in capture.get_stdout()
        assert capture.get_stderr() == ""

    def test_capture_stderr(self):
        """Test capturing stderr output."""
        capture = CLIOutputCapture(capture_stdout=False, capture_stderr=True)

        with capture.capture():
            print("Test stderr output", file=sys.stderr)

        assert capture.get_stdout() == ""
        assert "Test stderr output" in capture.get_stderr()

    def test_capture_both_outputs(self):
        """Test capturing both stdout and stderr."""
        capture = CLIOutputCapture()

        with capture.capture():
            print("Stdout message")
            print("Stderr message", file=sys.stderr)

        assert "Stdout message" in capture.get_stdout()
        assert "Stderr message" in capture.get_stderr()

    def test_clear_buffers(self):
        """Test clearing output buffers."""
        capture = CLIOutputCapture()

        with capture.capture():
            print("Test output")

        assert capture.get_stdout() != ""

        capture.clear_buffers()
        assert capture.get_stdout() == ""
        assert capture.get_stderr() == ""

    def test_multiple_capture_sessions(self):
        """Test multiple capture sessions."""
        capture = CLIOutputCapture()

        with capture.capture():
            print("First session")

        capture.get_stdout()

        with capture.capture():
            print("Second session")

        # Should contain both sessions
        combined_output = capture.get_stdout()
        assert "First session" in combined_output
        assert "Second session" in combined_output


class TestUserInputMocker:
    """Test user input mocking functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.input_mocker = create_user_input_mocker()

    def test_initialization(self):
        """Test input mocker initialization."""
        mocker = UserInputMocker()

        assert mocker.input_queue == []
        assert mocker.input_history == []
        assert mocker.mock_patch is None

    def test_add_single_input(self):
        """Test adding single input to queue."""
        self.input_mocker.add_input("test input")

        assert len(self.input_mocker.input_queue) == 1
        assert self.input_mocker.input_queue[0] == "test input"

    def test_add_multiple_inputs(self):
        """Test adding multiple inputs to queue."""
        inputs = ["input1", "input2", "input3"]
        self.input_mocker.add_inputs(inputs)

        assert len(self.input_mocker.input_queue) == 3
        assert self.input_mocker.input_queue == inputs

    def test_mock_input_function(self):
        """Test mock input function behavior."""
        self.input_mocker.add_input("test response")

        response = self.input_mocker.mock_input("Enter something: ")

        assert response == "test response"
        assert len(self.input_mocker.input_queue) == 0
        assert "test response" in self.input_mocker.input_history

    def test_mock_input_with_empty_queue(self):
        """Test mock input function with empty queue."""
        with pytest.raises(RuntimeError, match="No more inputs queued"):
            self.input_mocker.mock_input("Enter something: ")

    def test_mock_input_sequence(self):
        """Test sequence of mock inputs."""
        inputs = ["first", "second", "third"]
        self.input_mocker.add_inputs(inputs)

        responses = []
        for i in range(3):
            responses.append(self.input_mocker.mock_input(f"Prompt {i}: "))

        assert responses == inputs
        assert self.input_mocker.input_history == inputs
        assert len(self.input_mocker.input_queue) == 0

    def test_clear_queue(self):
        """Test clearing input queue."""
        self.input_mocker.add_inputs(["input1", "input2"])
        assert len(self.input_mocker.input_queue) == 2

        self.input_mocker.clear_queue()
        assert len(self.input_mocker.input_queue) == 0

    def test_get_input_history(self):
        """Test getting input history."""
        self.input_mocker.add_inputs(["input1", "input2"])

        self.input_mocker.mock_input("Prompt 1")
        self.input_mocker.mock_input("Prompt 2")

        history = self.input_mocker.get_input_history()
        assert history == ["input1", "input2"]
        assert history is not self.input_mocker.input_history  # Should be copy

    def test_clear_history(self):
        """Test clearing input history."""
        self.input_mocker.add_input("test")
        self.input_mocker.mock_input("Prompt")

        assert len(self.input_mocker.input_history) == 1

        self.input_mocker.clear_history()
        assert len(self.input_mocker.input_history) == 0

    def test_mock_user_input_context_manager(self):
        """Test mock user input context manager."""
        self.input_mocker.add_inputs(["Alice", "y"])

        with self.input_mocker.mock_user_input():
            # Test builtin input
            with patch("builtins.input") as mock_input:
                mock_input.side_effect = self.input_mocker.mock_input
                name = input("Enter name: ")
                assert name == "Alice"


class TestFactoryFunctions:
    """Test factory functions for creating test helpers."""

    def test_create_cli_command_runner(self):
        """Test CLI command runner factory function."""
        runner = create_cli_command_runner()

        assert isinstance(runner, CLICommandRunner)
        assert runner.isolated_filesystem is True
        assert runner.mix_stderr is True

    def test_create_cli_command_runner_with_options(self):
        """Test CLI command runner factory with options."""
        runner = create_cli_command_runner(isolated_filesystem=False, mix_stderr=False)

        assert runner.isolated_filesystem is False
        assert runner.mix_stderr is False

    def test_create_cli_output_capture(self):
        """Test CLI output capture factory function."""
        capture = create_cli_output_capture()

        assert isinstance(capture, CLIOutputCapture)
        assert capture.capture_stdout is True
        assert capture.capture_stderr is True

    def test_create_cli_output_capture_with_options(self):
        """Test CLI output capture factory with options."""
        capture = create_cli_output_capture(capture_stdout=False, capture_stderr=True)

        assert capture.capture_stdout is False
        assert capture.capture_stderr is True

    def test_create_user_input_mocker(self):
        """Test user input mocker factory function."""
        mocker = create_user_input_mocker()

        assert isinstance(mocker, UserInputMocker)
        assert mocker.input_queue == []
        assert mocker.input_history == []


class TestIsolatedCLIEnvironment:
    """Test isolated CLI environment context manager."""

    def test_isolated_environment_basic(self):
        """Test basic isolated CLI environment."""
        with isolated_cli_environment() as env:
            assert "runner" in env
            assert "output_capture" in env
            assert "input_mocker" in env
            assert isinstance(env["runner"], CLICommandRunner)
            assert isinstance(env["output_capture"], CLIOutputCapture)
            assert isinstance(env["input_mocker"], UserInputMocker)

    def test_isolated_environment_with_env_vars(self):
        """Test isolated environment with environment variables."""
        env_vars = {"TEST_VAR": "test_value", "DEBUG": "true"}

        with isolated_cli_environment(env_vars=env_vars) as env:
            runner = env["runner"]
            assert "TEST_VAR" in runner.mock_environment
            assert runner.mock_environment["TEST_VAR"] == "test_value"
            assert runner.mock_environment["DEBUG"] == "true"

    def test_isolated_environment_integration(self):
        """Test integration of all components in isolated environment."""

        @click.command()
        @click.argument("name")
        def test_cmd(name):
            user_input = input("Enter age: ")
            click.echo(f"Hello {name}, age {user_input}")

        with isolated_cli_environment() as env:
            runner = env["runner"]
            input_mocker = env["input_mocker"]

            input_mocker.add_input("25")

            with input_mocker.mock_user_input():
                result = runner.run_command(test_cmd, args=["Alice"])

            assert result.success
            assert "Hello Alice" in result.output


class TestErrorHandling:
    """Test error handling in CLI test helpers."""

    def test_command_runner_exception_handling(self):
        """Test exception handling in command runner."""

        @click.command()
        def error_cmd():
            raise ValueError("Test error")

        runner = create_cli_command_runner()
        result = runner.run_command(error_cmd, catch_exceptions=True)

        assert result.failed
        assert result.exception is not None
        assert isinstance(result.exception, ValueError)

    def test_command_runner_uncaught_exceptions(self):
        """Test uncaught exceptions in command runner."""

        @click.command()
        def error_cmd():
            raise ValueError("Test error")

        runner = create_cli_command_runner()

        with pytest.raises(ValueError):
            runner.run_command(error_cmd, catch_exceptions=False)

    def test_output_capture_exception_safety(self):
        """Test output capture is exception-safe."""
        capture = create_cli_output_capture()

        try:
            with capture.capture():
                print("Before error")
                raise ValueError("Test error")
        except ValueError:
            pass

        # Output should still be captured
        assert "Before error" in capture.get_stdout()

    def test_input_mocker_error_conditions(self):
        """Test input mocker error conditions."""
        mocker = create_user_input_mocker()

        # Test empty queue error
        with pytest.raises(RuntimeError, match="No more inputs queued"):
            mocker.mock_input("Test prompt")

        # Test partial queue consumption
        mocker.add_inputs(["input1", "input2"])
        mocker.mock_input("Prompt 1")

        # Should still work for remaining input
        response = mocker.mock_input("Prompt 2")
        assert response == "input2"
