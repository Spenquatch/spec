"""Unit tests for WorkflowValidator class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.core.repository_state import RepositoryStateChecker
from spec_cli.core.validators.workflow_validator import WorkflowValidator
from spec_cli.exceptions import SpecWorkflowError


class TestWorkflowValidator:
    """Tests for WorkflowValidator class."""

    @pytest.fixture
    def mock_settings(self, tmp_path: Path) -> SpecSettings:
        """Create mock settings."""
        settings = Mock(spec=SpecSettings)
        settings.project_root = tmp_path
        settings.spec_dir = tmp_path / ".spec"
        settings.specs_dir = tmp_path / ".specs"
        return settings

    @pytest.fixture
    def mock_state_checker(self) -> Mock:
        """Create mock repository state checker."""
        return Mock(spec=RepositoryStateChecker)

    @pytest.fixture
    def validator(
        self, mock_settings: SpecSettings, mock_state_checker: Mock
    ) -> WorkflowValidator:
        """Create WorkflowValidator instance."""
        return WorkflowValidator(mock_settings, mock_state_checker)

    @pytest.fixture
    def test_file(self, tmp_path: Path) -> Path:
        """Create a test file."""
        test_file = tmp_path / "test.py"
        test_file.write_text("# Test file")
        return test_file

    def test_init_when_valid_inputs_then_initializes_correctly(
        self, mock_settings: SpecSettings, mock_state_checker: Mock
    ) -> None:
        """Test WorkflowValidator initialization."""
        validator = WorkflowValidator(mock_settings, mock_state_checker)

        assert validator.settings == mock_settings
        assert validator.state_checker == mock_state_checker
        assert validator.error_handler is not None

    def test_validate_workflow_preconditions_when_all_valid_then_returns_valid(
        self, validator: WorkflowValidator, mock_state_checker: Mock, test_file: Path
    ) -> None:
        """Test successful validation of all preconditions."""
        # Arrange
        mock_state_checker.is_safe_for_spec_operations.return_value = True
        mock_state_checker.validate_pre_operation_state.return_value = []

        # Act
        result = validator.validate_workflow_preconditions(test_file, "generate")

        # Assert
        assert result["valid"] is True
        assert result["issues"] == []
        mock_state_checker.is_safe_for_spec_operations.assert_called_once()
        mock_state_checker.validate_pre_operation_state.assert_called_once_with(
            "generate"
        )

    def test_validate_workflow_preconditions_when_repo_unhealthy_then_returns_invalid(
        self, validator: WorkflowValidator, mock_state_checker: Mock, test_file: Path
    ) -> None:
        """Test validation when repository is unhealthy."""
        # Arrange
        mock_state_checker.is_safe_for_spec_operations.return_value = False
        mock_state_checker.validate_pre_operation_state.return_value = []

        # Act
        result = validator.validate_workflow_preconditions(test_file, "generate")

        # Assert
        assert result["valid"] is False
        assert "Repository is not safe for spec operations" in result["issues"]

    def test_validate_workflow_preconditions_when_file_missing_then_returns_invalid(
        self, validator: WorkflowValidator, mock_state_checker: Mock, tmp_path: Path
    ) -> None:
        """Test validation when file doesn't exist."""
        # Arrange
        missing_file = tmp_path / "missing.py"
        mock_state_checker.is_safe_for_spec_operations.return_value = True
        mock_state_checker.validate_pre_operation_state.return_value = []

        # Act
        result = validator.validate_workflow_preconditions(missing_file, "generate")

        # Assert
        assert result["valid"] is False
        assert any("does not exist" in issue for issue in result["issues"])

    def test_validate_workflow_preconditions_when_path_is_directory_then_returns_invalid(
        self, validator: WorkflowValidator, mock_state_checker: Mock, tmp_path: Path
    ) -> None:
        """Test validation when path is a directory."""
        # Arrange
        test_dir = tmp_path / "test_dir"
        test_dir.mkdir()
        mock_state_checker.is_safe_for_spec_operations.return_value = True
        mock_state_checker.validate_pre_operation_state.return_value = []

        # Act
        result = validator.validate_workflow_preconditions(test_dir, "generate")

        # Assert
        assert result["valid"] is False
        assert any("not a file" in issue for issue in result["issues"])

    def test_validate_workflow_preconditions_when_pre_operation_fails_then_returns_invalid(
        self, validator: WorkflowValidator, mock_state_checker: Mock, test_file: Path
    ) -> None:
        """Test validation when pre-operation check fails."""
        # Arrange
        mock_state_checker.is_safe_for_spec_operations.return_value = True
        mock_state_checker.validate_pre_operation_state.return_value = [
            "Git repository not initialized",
            "Work tree not configured",
        ]

        # Act
        result = validator.validate_workflow_preconditions(test_file, "generate")

        # Assert
        assert result["valid"] is False
        assert "Git repository not initialized" in result["issues"]
        assert "Work tree not configured" in result["issues"]

    def test_validate_workflow_preconditions_when_exception_then_raises_workflow_error(
        self, validator: WorkflowValidator, mock_state_checker: Mock, test_file: Path
    ) -> None:
        """Test validation when an exception occurs."""
        # Arrange
        mock_state_checker.is_safe_for_spec_operations.side_effect = Exception(
            "Test error"
        )

        # Act & Assert
        with pytest.raises(SpecWorkflowError, match="Workflow validation error"):
            validator.validate_workflow_preconditions(test_file, "generate")

    @patch("spec_cli.core.validators.workflow_validator.ensure_path_permissions")
    def test_validate_file_path_when_no_permissions_then_returns_issue(
        self,
        mock_ensure_permissions: Mock,
        validator: WorkflowValidator,
        test_file: Path,
    ) -> None:
        """Test file validation when permissions check fails."""
        # Arrange
        mock_ensure_permissions.side_effect = PermissionError("Access denied")

        # Act
        issues = validator._validate_file_path(test_file)

        # Assert
        assert len(issues) == 1
        assert "not readable" in issues[0]
        mock_ensure_permissions.assert_called_once_with(test_file, require_write=False)

    def test_validate_batch_operation_when_all_valid_then_returns_valid(
        self, validator: WorkflowValidator, mock_state_checker: Mock, tmp_path: Path
    ) -> None:
        """Test batch validation with all valid files."""
        # Arrange
        files = []
        for i in range(3):
            file_path = tmp_path / f"test{i}.py"
            file_path.write_text(f"# Test file {i}")
            files.append(file_path)

        mock_state_checker.is_safe_for_spec_operations.return_value = True
        mock_state_checker.validate_pre_operation_state.return_value = []

        # Act
        result = validator.validate_batch_operation(files, "generate")

        # Assert
        assert result["valid"] is True
        assert result["total_files"] == 3
        assert len(result["valid_files"]) == 3
        assert len(result["invalid_files"]) == 0
        assert len(result["global_issues"]) == 0

    def test_validate_batch_operation_when_repo_unhealthy_then_returns_invalid(
        self, validator: WorkflowValidator, mock_state_checker: Mock, tmp_path: Path
    ) -> None:
        """Test batch validation when repository is unhealthy."""
        # Arrange
        files = [tmp_path / "test.py"]
        mock_state_checker.is_safe_for_spec_operations.return_value = False
        mock_state_checker.validate_pre_operation_state.return_value = []

        # Act
        result = validator.validate_batch_operation(files, "generate")

        # Assert
        assert result["valid"] is False
        assert "Repository is not safe for spec operations" in result["global_issues"]
        assert len(result["valid_files"]) == 0

    def test_validate_batch_operation_when_mixed_validity_then_returns_partial_results(
        self, validator: WorkflowValidator, mock_state_checker: Mock, tmp_path: Path
    ) -> None:
        """Test batch validation with mixed valid/invalid files."""
        # Arrange
        valid_file = tmp_path / "valid.py"
        valid_file.write_text("# Valid file")

        missing_file = tmp_path / "missing.py"

        directory = tmp_path / "test_dir"
        directory.mkdir()

        files = [valid_file, missing_file, directory]

        mock_state_checker.is_safe_for_spec_operations.return_value = True
        mock_state_checker.validate_pre_operation_state.return_value = []

        # Act
        result = validator.validate_batch_operation(files, "generate")

        # Assert
        assert result["valid"] is False
        assert result["total_files"] == 3
        assert len(result["valid_files"]) == 1
        assert valid_file in result["valid_files"]
        assert len(result["invalid_files"]) == 2
        assert missing_file in result["invalid_files"]
        assert directory in result["invalid_files"]

    def test_validate_repository_health_when_checker_fails_then_returns_false(
        self, validator: WorkflowValidator, mock_state_checker: Mock
    ) -> None:
        """Test repository health check when checker throws exception."""
        # Arrange
        mock_state_checker.is_safe_for_spec_operations.side_effect = Exception(
            "Check failed"
        )

        # Act
        result = validator._validate_repository_health()

        # Assert
        assert result is False

    def test_validate_pre_operation_state_when_checker_fails_then_returns_error_issue(
        self, validator: WorkflowValidator, mock_state_checker: Mock
    ) -> None:
        """Test pre-operation validation when checker throws exception."""
        # Arrange
        mock_state_checker.validate_pre_operation_state.side_effect = Exception(
            "Validation failed"
        )

        # Act
        issues = validator._validate_pre_operation_state("generate")

        # Assert
        assert len(issues) == 1
        assert "Pre-operation validation error" in issues[0]
