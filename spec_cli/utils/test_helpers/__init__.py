"""Test helper utilities for spec-cli testing infrastructure.

This module provides comprehensive test helpers for mocking and testing
Git operations, subprocess calls, and environment isolation.
"""

from .git_test_helpers import (
    GitCommandSimulator,
    GitEnvironmentIsolator,
    GitRepositoryMocker,
    create_git_command_simulator,
    create_git_environment_isolator,
    create_git_repository_mocker,
    git_command_simulator,
    git_test_repository,
)
from .test_failure_categorizer import (
    FailureCategory,
    FailureInfo,
    FailurePriority,
    FailureType,
    categorize_test_failure,
)

__all__ = [
    "GitRepositoryMocker",
    "GitCommandSimulator",
    "GitEnvironmentIsolator",
    "create_git_repository_mocker",
    "create_git_command_simulator",
    "create_git_environment_isolator",
    "git_test_repository",
    "git_command_simulator",
    "FailureType",
    "FailurePriority",
    "FailureInfo",
    "FailureCategory",
    "categorize_test_failure",
]
