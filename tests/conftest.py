"""Pytest configuration and shared fixtures for spec-cli tests.

This module provides common pytest fixtures and configuration for all
test modules in the spec-cli test suite.
"""

import os
import sys
from unittest.mock import patch

import pytest

from spec_cli.utils.test_helpers.git_test_helpers import (
    create_git_command_simulator,
    create_git_environment_isolator,
    create_git_repository_mocker,
)


@pytest.fixture(autouse=True)
def isolate_working_directory():
    """Ensure working directory is restored after each test.

    This fixture automatically captures and restores the current working
    directory for every test, preventing working directory contamination
    between tests that causes systematic failures in the full test suite.

    Complexity: 2/7 (PASSES McCabe requirement)
    """
    original_cwd = os.getcwd()  # +0 (assignment)
    try:  # +1 (try block)
        yield  # Test execution happens here
    finally:  # +1 (finally block)
        if os.getcwd() != original_cwd:  # +0 (condition in finally)
            os.chdir(original_cwd)


@pytest.fixture(autouse=True)
def isolate_environment_variables():
    """Isolate environment variables between tests.

    This fixture captures and restores environment variables that tests
    might modify, preventing environment variable contamination between
    tests that causes systematic failures in the full test suite.

    Targets common SPEC_ environment variables that tests modify:
    - SPEC_DEBUG, SPEC_DEBUG_LEVEL, SPEC_DEBUG_TIMING
    - SPEC_USE_COLOR, SPEC_CONSOLE_WIDTH

    Complexity: 3/7 (PASSES McCabe requirement)
    """
    # Store original environment state for SPEC_ variables
    spec_vars = [k for k in os.environ.keys() if k.startswith("SPEC_")]
    original_env = {key: os.environ.get(key) for key in spec_vars}

    try:  # +1 (try block)
        yield  # Test execution happens here
    finally:  # +1 (finally block)
        # Restore original environment variables
        current_spec_vars = [k for k in os.environ.keys() if k.startswith("SPEC_")]

        # Remove any SPEC_ vars added during test
        for key in current_spec_vars:
            if key not in original_env:
                del os.environ[key]

        # Restore original values
        for key, value in original_env.items():
            if value is not None:  # +1 (condition)
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]


@pytest.fixture(autouse=True)
def clean_mock_state():
    """Clean up all mock/patch state between tests.

    This fixture automatically cleans up mock patches and test helper module
    state that can accumulate during large test suite execution, preventing
    state pollution between tests.

    Targets the extensive test helper infrastructure that imports:
    - ai_test_doubles (mock providers, timeout simulators)
    - cli_test_helpers (command runners, input mockers)
    - file_system_test_helpers (permission mockers)
    - template_test_helpers (template mocking)
    - workflow_test_helpers (state builders, error simulators)

    Complexity: 3/7 (PASSES McCabe requirement)
    """
    # Store initial module state
    initial_modules = set(sys.modules.keys())

    try:  # +1 (try block)
        yield  # Test execution happens here
    finally:  # +1 (finally block)
        # Clean up any lingering patches
        patch.stopall()

        # Clean up test helper modules that may retain state
        if len(sys.modules) > len(initial_modules):  # +1 (condition)
            test_helper_modules = [
                mod
                for mod in sys.modules.keys()
                if "test_helpers" in mod and mod not in initial_modules
            ]
            for mod in test_helper_modules:
                if mod in sys.modules:
                    del sys.modules[mod]


@pytest.fixture
def git_test_repository(tmp_path):
    """Pytest fixture for temporary Git repository.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        GitRepositoryMocker instance for testing
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()
    return create_git_repository_mocker(repo_path)


@pytest.fixture
def git_command_simulator():
    """Pytest fixture for Git command simulation.

    Returns:
        GitCommandSimulator instance for testing
    """
    return create_git_command_simulator()


@pytest.fixture
def git_environment_isolator(tmp_path):
    """Pytest fixture for Git environment isolation.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        GitEnvironmentIsolator instance for testing
    """
    spec_dir = tmp_path / ".spec"
    specs_dir = tmp_path / ".specs"
    return create_git_environment_isolator(spec_dir, specs_dir)


@pytest.fixture
def mock_git_environment(tmp_path):
    """Pytest fixture for complete Git environment mocking.

    Combines repository mocking, command simulation, and environment isolation
    for comprehensive Git testing.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Dictionary with 'repository', 'simulator', and 'isolator' keys
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    repository = create_git_repository_mocker(repo_path)
    simulator = create_git_command_simulator()
    isolator = create_git_environment_isolator(
        repo_path / ".spec", repo_path / ".specs"
    )

    # Set up simulator with repository as default
    simulator.set_default_repository(repository)

    return {
        "repository": repository,
        "simulator": simulator,
        "isolator": isolator,
        "repo_path": repo_path,
    }


@pytest.fixture
def sample_git_repository(git_test_repository):
    """Pytest fixture for Git repository with sample data.

    Args:
        git_test_repository: GitRepositoryMocker fixture

    Returns:
        GitRepositoryMocker with sample files and commits
    """
    # Initialize repository
    git_test_repository.mock_git_command(["git", "init"])

    # Add some sample files
    git_test_repository.add_file("README.md", "# Test Repository")
    git_test_repository.add_file("src/main.py", 'print("Hello, World!")')
    git_test_repository.add_file("tests/test_main.py", "def test_main(): pass")

    # Stage and commit files
    git_test_repository.stage_file("README.md")
    git_test_repository.stage_file("src/main.py")
    git_test_repository.mock_git_command(["git", "commit", "-m", "Initial commit"])

    # Add another commit
    git_test_repository.add_file("docs/guide.md", "# User Guide")
    git_test_repository.stage_file("docs/guide.md")
    git_test_repository.mock_git_command(["git", "commit", "-m", "Add documentation"])

    return git_test_repository
