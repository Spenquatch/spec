"""Pytest configuration for test helpers tests.

This module provides pytest fixtures and configuration for testing
the test helper infrastructure itself.
"""

import pytest

# Import AI test double fixtures
from spec_cli.utils.test_helpers.ai_test_doubles import (
    ai_response_fixtures,
    ai_timeout_simulator,
    mock_generation_provider,
    mock_huggingface_model,
    mock_llamacpp_provider,
)

# Import CLI test helpers for fixtures
from spec_cli.utils.test_helpers.cli_test_helpers import (
    create_cli_command_runner,
    create_cli_output_capture,
    create_user_input_mocker,
    isolated_cli_environment,
)

# Import file system test helpers for fixtures
from spec_cli.utils.test_helpers.file_system_test_helpers import (
    create_cross_platform_path_validator,
    create_file_permission_mocker,
    create_temp_file_structure,
)

# Import template test helper fixtures
from spec_cli.utils.test_helpers.template_test_helpers import (
    ai_template_mocker,
    mock_template_environment,
    temp_template_dir,
    template_fixture_generator,
    variable_substitution_mocker,
)

# Import fixtures from the workflow test helpers module
from spec_cli.utils.test_helpers.workflow_test_helpers import (
    backup_rollback_fixtures,
    sample_failed_workflow,
    sample_pending_workflow,
    sample_running_workflow,
    state_transition_mocker,
    workflow_error_simulator,
    workflow_state_builder,
)


@pytest.fixture
def temp_file_structure_builder(tmp_path):
    """Pytest fixture for temporary file structure builder.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        TempFileStructureBuilder instance for testing
    """
    return create_temp_file_structure(tmp_path)


@pytest.fixture
def file_permission_mocker():
    """Pytest fixture for file permission mocker.

    Returns:
        FilePermissionMocker instance for testing
    """
    return create_file_permission_mocker()


@pytest.fixture
def cross_platform_path_validator():
    """Pytest fixture for cross-platform path validator.

    Returns:
        CrossPlatformPathValidator instance for testing
    """
    return create_cross_platform_path_validator()


@pytest.fixture
def cli_command_runner():
    """Pytest fixture for CLI command runner.

    Returns:
        CLICommandRunner instance for testing
    """
    return create_cli_command_runner()


@pytest.fixture
def cli_output_capture():
    """Pytest fixture for CLI output capture.

    Returns:
        CLIOutputCapture instance for testing
    """
    return create_cli_output_capture()


@pytest.fixture
def user_input_mocker():
    """Pytest fixture for user input mocker.

    Returns:
        UserInputMocker instance for testing
    """
    return create_user_input_mocker()


@pytest.fixture
def isolated_cli_test_environment(tmp_path):
    """Pytest fixture for isolated CLI testing environment.

    Args:
        tmp_path: pytest tmp_path fixture

    Returns:
        Context manager for isolated CLI environment
    """
    return isolated_cli_environment(temp_dir=tmp_path)


# Re-export fixtures so they're available in test files
__all__ = [
    "workflow_state_builder",
    "state_transition_mocker",
    "backup_rollback_fixtures",
    "workflow_error_simulator",
    "sample_pending_workflow",
    "sample_running_workflow",
    "sample_failed_workflow",
    "temp_file_structure_builder",
    "file_permission_mocker",
    "cross_platform_path_validator",
    "cli_command_runner",
    "cli_output_capture",
    "user_input_mocker",
    "isolated_cli_test_environment",
    "mock_llamacpp_provider",
    "mock_generation_provider",
    "ai_response_fixtures",
    "ai_timeout_simulator",
    "mock_huggingface_model",
    "template_fixture_generator",
    "variable_substitution_mocker",
    "ai_template_mocker",
    "temp_template_dir",
    "mock_template_environment",
]
