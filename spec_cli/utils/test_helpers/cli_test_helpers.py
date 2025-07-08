"""CLI test infrastructure for comprehensive command testing.

This module provides comprehensive CLI test infrastructure to enable testing
of CLI commands without affecting the host system, including command execution
simulation, output capture, and user input mocking.
"""

import os
import sys
from contextlib import contextmanager
from io import StringIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

from click.testing import CliRunner

from ...core.context_bridge import debug_logger


class CLICommandRunner:
    """Execute CLI commands in isolated test environment.

    This class provides comprehensive CLI command execution simulation, allowing
    tests to verify command behavior without affecting the host system or
    requiring real file operations.
    """

    def __init__(self, isolated_filesystem: bool = True, mix_stderr: bool = True):
        """Initialize CLI command runner.

        Args:
            isolated_filesystem: Whether to run commands in isolated filesystem
            mix_stderr: Whether to mix stderr with stdout in output
        """
        self.runner = CliRunner()
        self.isolated_filesystem = isolated_filesystem
        self.mix_stderr = mix_stderr
        self.command_history: list[dict[str, Any]] = []
        self.mock_environment: dict[str, str] = {}

        debug_logger.log(
            "DEBUG",
            "CLI command runner initialized",
            extra={
                "isolated_filesystem": isolated_filesystem,
                "mix_stderr": mix_stderr,
            },
        )

    def run_command(
        self,
        command_func: Any,
        args: list[str] | None = None,
        input_data: str | None = None,
        env: dict[str, str] | None = None,
        catch_exceptions: bool = True,
    ) -> "CLITestResult":
        """Run CLI command and capture results.

        Args:
            command_func: Click command function to execute
            args: Command line arguments
            input_data: Simulated user input
            env: Environment variables for command
            catch_exceptions: Whether to catch exceptions

        Returns:
            CLITestResult with command execution details
        """
        args = args or []
        env = {**self.mock_environment, **(env or {})}

        debug_logger.log(
            "DEBUG",
            "Running CLI command",
            extra={
                "command": getattr(command_func, "name", str(command_func)),
                "args": args,
                "has_input": input_data is not None,
                "env_vars": list(env.keys()),
            },
        )

        if self.isolated_filesystem:
            with self.runner.isolated_filesystem():
                result = self.runner.invoke(
                    command_func,
                    args,
                    input=input_data,
                    env=env,
                    catch_exceptions=catch_exceptions,
                )
        else:
            result = self.runner.invoke(
                command_func,
                args,
                input=input_data,
                env=env,
                catch_exceptions=catch_exceptions,
            )

        cli_result = CLITestResult(
            exit_code=result.exit_code,
            output=result.output,
            exception=result.exception,
            command=getattr(command_func, "name", str(command_func)),
            args=args,
        )

        self.command_history.append(
            {
                "command": cli_result.command,
                "args": args,
                "exit_code": result.exit_code,
                "output_length": len(result.output),
                "success": result.exit_code == 0,
            }
        )

        return cli_result

    def set_environment_variable(self, key: str, value: str) -> None:
        """Set environment variable for subsequent command runs.

        Args:
            key: Environment variable name
            value: Environment variable value
        """
        self.mock_environment[key] = value
        debug_logger.log(
            "DEBUG",
            "Set environment variable",
            extra={"key": key, "value": value},
        )

    def clear_environment(self) -> None:
        """Clear all mock environment variables."""
        self.mock_environment.clear()
        debug_logger.log("DEBUG", "Cleared mock environment variables")

    def get_command_history(self) -> list[dict[str, Any]]:
        """Get history of executed commands.

        Returns:
            List of command execution records
        """
        return self.command_history.copy()

    def clear_history(self) -> None:
        """Clear command execution history."""
        self.command_history.clear()
        debug_logger.log("DEBUG", "Cleared command execution history")


class CLITestResult:
    """Result of CLI command execution in test environment."""

    def __init__(
        self,
        exit_code: int,
        output: str,
        exception: Exception | None,
        command: str,
        args: list[str],
    ):
        """Initialize CLI test result.

        Args:
            exit_code: Command exit code
            output: Command output (stdout + stderr if mixed)
            exception: Exception that occurred during execution
            command: Command name that was executed
            args: Arguments passed to command
        """
        self.exit_code = exit_code
        self.output = output
        self.exception = exception
        self.command = command
        self.args = args

    @property
    def success(self) -> bool:
        """Check if command executed successfully.

        Returns:
            True if exit code is 0
        """
        return self.exit_code == 0

    @property
    def failed(self) -> bool:
        """Check if command failed.

        Returns:
            True if exit code is not 0
        """
        return self.exit_code != 0

    def assert_success(self, message: str | None = None) -> None:
        """Assert that command executed successfully.

        Args:
            message: Optional assertion message

        Raises:
            AssertionError: If command failed
        """
        if self.failed:
            error_msg = (
                message
                or f"Command '{self.command}' failed with exit code {self.exit_code}"
            )
            if self.exception:
                error_msg += f"\nException: {self.exception}"
            if self.output:
                error_msg += f"\nOutput: {self.output}"
            raise AssertionError(error_msg)

    def assert_failure(self, expected_exit_code: int | None = None) -> None:
        """Assert that command failed.

        Args:
            expected_exit_code: Expected exit code (any non-zero if None)

        Raises:
            AssertionError: If command succeeded or exit code doesn't match
        """
        if self.success:
            raise AssertionError(
                f"Command '{self.command}' succeeded when failure was expected"
            )

        if expected_exit_code is not None and self.exit_code != expected_exit_code:
            raise AssertionError(
                f"Command '{self.command}' failed with exit code {self.exit_code}, "
                f"expected {expected_exit_code}"
            )

    def assert_output_contains(self, text: str) -> None:
        """Assert that output contains specific text.

        Args:
            text: Text that should be in output

        Raises:
            AssertionError: If text not found in output
        """
        if text not in self.output:
            raise AssertionError(
                f"Output does not contain '{text}'\nActual output: {self.output}"
            )

    def assert_output_not_contains(self, text: str) -> None:
        """Assert that output does not contain specific text.

        Args:
            text: Text that should not be in output

        Raises:
            AssertionError: If text found in output
        """
        if text in self.output:
            raise AssertionError(
                f"Output contains '{text}' when it shouldn't\nActual output: {self.output}"
            )


class CLIOutputCapture:
    """Capture stdout and stderr from CLI commands during testing."""

    def __init__(self, capture_stdout: bool = True, capture_stderr: bool = True):
        """Initialize output capture.

        Args:
            capture_stdout: Whether to capture stdout
            capture_stderr: Whether to capture stderr
        """
        self.capture_stdout = capture_stdout
        self.capture_stderr = capture_stderr
        self.stdout_buffer = StringIO()
        self.stderr_buffer = StringIO()
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr

    @contextmanager
    def capture(self) -> Any:
        """Context manager for capturing output.

        Yields:
            Dictionary with 'stdout' and 'stderr' keys
        """
        if self.capture_stdout:
            sys.stdout = self.stdout_buffer
        if self.capture_stderr:
            sys.stderr = self.stderr_buffer

        try:
            yield {
                "stdout": self.stdout_buffer,
                "stderr": self.stderr_buffer,
            }
        finally:
            sys.stdout = self._original_stdout
            sys.stderr = self._original_stderr

    def get_stdout(self) -> str:
        """Get captured stdout content.

        Returns:
            Stdout content as string
        """
        return self.stdout_buffer.getvalue()

    def get_stderr(self) -> str:
        """Get captured stderr content.

        Returns:
            Stderr content as string
        """
        return self.stderr_buffer.getvalue()

    def clear_buffers(self) -> None:
        """Clear both stdout and stderr buffers."""
        self.stdout_buffer = StringIO()
        self.stderr_buffer = StringIO()


class UserInputMocker:
    """Mock user input for interactive CLI commands."""

    def __init__(self) -> None:
        """Initialize user input mocker."""
        self.input_queue: list[str] = []
        self.input_history: list[str] = []
        self.mock_patch: Any | None = None

    def add_input(self, input_text: str) -> None:
        """Add input to the queue for subsequent prompts.

        Args:
            input_text: Text to provide when input is requested
        """
        self.input_queue.append(input_text)
        debug_logger.log(
            "DEBUG",
            "Added user input to queue",
            extra={"input": input_text, "queue_size": len(self.input_queue)},
        )

    def add_inputs(self, inputs: list[str]) -> None:
        """Add multiple inputs to the queue.

        Args:
            inputs: List of input strings
        """
        self.input_queue.extend(inputs)
        debug_logger.log(
            "DEBUG",
            "Added multiple user inputs to queue",
            extra={"count": len(inputs), "queue_size": len(self.input_queue)},
        )

    def mock_input(self, prompt: str = "") -> str:
        """Mock input function that returns queued inputs.

        Args:
            prompt: Input prompt (logged but not displayed)

        Returns:
            Next input from queue

        Raises:
            RuntimeError: If no more inputs are queued
        """
        if not self.input_queue:
            raise RuntimeError(f"No more inputs queued for prompt: {prompt}")

        input_text = self.input_queue.pop(0)
        self.input_history.append(input_text)

        debug_logger.log(
            "DEBUG",
            "Providing mocked user input",
            extra={
                "prompt": prompt,
                "input": input_text,
                "remaining_queue": len(self.input_queue),
            },
        )

        return input_text

    @contextmanager
    def mock_user_input(self) -> Any:
        """Context manager for mocking user input."""
        with patch("builtins.input", side_effect=self.mock_input):
            with patch("click.prompt", side_effect=self.mock_input):
                with patch(
                    "click.confirm",
                    side_effect=lambda msg, default=False: self.mock_input(msg).lower()
                    in ["y", "yes", "true"],
                ):
                    yield

    def clear_queue(self) -> None:
        """Clear the input queue."""
        self.input_queue.clear()
        debug_logger.log("DEBUG", "Cleared user input queue")

    def get_input_history(self) -> list[str]:
        """Get history of inputs that were consumed.

        Returns:
            List of input strings that were provided
        """
        return self.input_history.copy()

    def clear_history(self) -> None:
        """Clear input history."""
        self.input_history.clear()
        debug_logger.log("DEBUG", "Cleared user input history")


def create_cli_command_runner(
    isolated_filesystem: bool = True, mix_stderr: bool = True
) -> CLICommandRunner:
    """Create CLI command runner for testing.

    Args:
        isolated_filesystem: Whether to run commands in isolated filesystem
        mix_stderr: Whether to mix stderr with stdout in output

    Returns:
        CLICommandRunner instance
    """
    return CLICommandRunner(isolated_filesystem, mix_stderr)


def create_cli_output_capture(
    capture_stdout: bool = True, capture_stderr: bool = True
) -> CLIOutputCapture:
    """Create CLI output capture for testing.

    Args:
        capture_stdout: Whether to capture stdout
        capture_stderr: Whether to capture stderr

    Returns:
        CLIOutputCapture instance
    """
    return CLIOutputCapture(capture_stdout, capture_stderr)


def create_user_input_mocker() -> UserInputMocker:
    """Create user input mocker for testing interactive commands.

    Returns:
        UserInputMocker instance
    """
    return UserInputMocker()


@contextmanager
def isolated_cli_environment(
    temp_dir: Path | None = None,
    env_vars: dict[str, str] | None = None,
) -> Any:
    """Context manager for isolated CLI testing environment.

    Args:
        temp_dir: Temporary directory to use (creates one if None)
        env_vars: Environment variables to set

    Yields:
        Dictionary with 'runner', 'output_capture', and 'input_mocker' keys
    """
    runner = create_cli_command_runner()
    output_capture = create_cli_output_capture()
    input_mocker = create_user_input_mocker()

    if env_vars:
        for key, value in env_vars.items():
            runner.set_environment_variable(key, value)

    with runner.runner.isolated_filesystem():
        if temp_dir:
            os.chdir(temp_dir)

        yield {
            "runner": runner,
            "output_capture": output_capture,
            "input_mocker": input_mocker,
        }
