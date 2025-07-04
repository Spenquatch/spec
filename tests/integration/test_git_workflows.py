"""Git Integration Tests - Repository Workflows.

Integration tests for end-to-end Git workflow validation, testing the complete
interaction between Git operations, repository management, path conversion,
and workflow orchestration components.

Test Coverage:
- End-to-end repository initialization workflows
- Git operations coordination and integration
- Path conversion integration
- Error handling across Git operation boundaries
- Component integration validation
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.exceptions import SpecGitError
from spec_cli.git.operations import GitOperations
from spec_cli.git.path_converter import GitPathConverter
from spec_cli.utils.test_helpers.git_test_helpers import GitRepositoryMocker


class TestGitWorkflowIntegration:
    """Integration tests for Git workflow coordination."""

    def setup_method(self):
        """Set up test environment with mocked Git infrastructure."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_path = self.temp_dir / ".spec"
        self.work_tree = self.temp_dir / ".specs"
        self.index_file = self.repo_path / ".spec-index"

        # Create directories
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.work_tree.mkdir(parents=True, exist_ok=True)

        # Initialize core components with proper constructor arguments
        self.git_ops = GitOperations(
            spec_dir=self.repo_path,
            specs_dir=self.work_tree,
            index_file=self.index_file,
        )
        self.path_converter = GitPathConverter(specs_dir=self.work_tree)

        # Set up test helpers
        self.git_mocker = GitRepositoryMocker(self.repo_path)

    def test_git_operations_environment_integration(self):
        """Test Git operations integration with proper environment setup.

        Integration Test Coverage:
        - Git operations with environment configuration
        - Command execution with proper Git environment
        - Environment variable setup and validation
        - Integration of Git directory configuration
        """
        with patch("subprocess.run") as mock_subprocess:
            # Configure mock for successful Git operations
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = b"git status output"
            mock_subprocess.return_value.stderr = b""

            # Act: Execute basic Git command
            result = self.git_ops.run_git_command(["status", "--porcelain"])

            # Assert: Verify Git operation success
            assert result.returncode == 0
            assert mock_subprocess.called

            # Verify Git environment was configured properly
            call_args = mock_subprocess.call_args
            assert call_args is not None

            # Verify environment variables
            env = call_args[1].get("env", {})
            assert "GIT_DIR" in env
            assert "GIT_WORK_TREE" in env
            assert "GIT_INDEX_FILE" in env
            assert str(self.repo_path) in env["GIT_DIR"]
            assert str(self.work_tree) in env["GIT_WORK_TREE"]

    def test_path_conversion_integration(self):
        """Test path conversion integration with Git context.

        Integration Test Coverage:
        - Path conversion for Git-relative paths
        - Cross-platform path handling in Git context
        - Path consistency across operations
        - Work tree relative path processing
        """
        # Arrange: Set up test paths for conversion
        test_files = [
            self.work_tree / "docs" / "readme.md",
            self.work_tree / "src" / "main.py",
            self.work_tree / "tests" / "test_main.py",
        ]

        for file_path in test_files:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(f"Content for {file_path.name}")

        # Act & Assert: Test path conversion for each file
        for file_path in test_files:
            # Convert absolute path to Git-relative path
            git_path = self.path_converter.convert_to_git_path(str(file_path))

            # Verify path conversion results
            assert not Path(git_path).is_absolute()
            expected_relative = file_path.relative_to(self.work_tree)
            assert Path(git_path) == expected_relative

            # Test conversion info
            conversion_info = self.path_converter.get_conversion_info(str(file_path))
            assert conversion_info["is_under_specs_dir"]
            assert conversion_info["git_path"] == git_path

    def test_git_operations_error_handling_integration(self):
        """Test error handling integration across Git operations.

        Integration Test Coverage:
        - Error propagation from subprocess to Git operations
        - Exception handling with proper error context
        - Error message preservation through component stack
        - Security validation error handling
        """
        with patch("subprocess.run") as mock_subprocess:
            # Configure mock for Git operation failure
            from subprocess import CalledProcessError

            mock_subprocess.side_effect = CalledProcessError(
                returncode=1,
                cmd=["git", "status"],
                stderr="fatal: not a git repository",
            )

            # Act & Assert: Verify error handling
            with pytest.raises(SpecGitError) as exc_info:
                self.git_ops.run_git_command(["status"])

            # Verify error context preservation
            error_message = str(exc_info.value)
            assert "not a git repository" in error_message.lower()

    def test_multiple_git_operations_state_consistency(self):
        """Test state consistency across multiple Git operations.

        Integration Test Coverage:
        - Sequential Git operations with consistent state
        - Environment preservation across operations
        - Operation result consistency
        - State tracking through operation sequence
        """
        with patch("subprocess.run") as mock_subprocess:
            # Configure mock for successful operations
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = b"Files processed"
            mock_subprocess.return_value.stderr = b""

            # Act: Execute sequence of Git operations

            # Operation 1: Check status
            result1 = self.git_ops.run_git_command(["status", "--porcelain"])

            # Operation 2: Check Git version
            result2 = self.git_ops.run_git_command(["--version"])

            # Operation 3: Check log
            result3 = self.git_ops.run_git_command(["log", "--oneline", "-n", "1"])

            # Assert: Verify all operations succeeded
            assert result1.returncode == 0
            assert result2.returncode == 0
            assert result3.returncode == 0

            # Verify consistent environment across all operations
            assert mock_subprocess.call_count == 3

            # Check that each call used consistent Git environment
            for call in mock_subprocess.call_args_list:
                env = call[1].get("env", {})
                assert "GIT_DIR" in env
                assert "GIT_WORK_TREE" in env
                assert str(self.repo_path) in env["GIT_DIR"]

    def test_git_repository_initialization_integration(self):
        """Test Git repository initialization integration.

        Integration Test Coverage:
        - Repository initialization with proper Git environment
        - Directory structure creation and validation
        - Initial repository setup and configuration
        - Environment variable configuration for isolated repository
        """
        with patch("subprocess.run") as mock_subprocess:
            # Configure mock for successful repository initialization
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = b"Initialized empty Git repository"
            mock_subprocess.return_value.stderr = b""

            # Act: Initialize Git repository
            self.git_ops.initialize_repository()

            # Assert: Verify initialization success
            assert mock_subprocess.called

            # Verify Git init command was called
            call_args = mock_subprocess.call_args
            command = call_args[0][0]
            assert "git" in command
            assert "init" in command

            # Verify proper Git environment configuration
            env = call_args[1].get("env", {})
            assert "GIT_DIR" in env
            assert "GIT_WORK_TREE" in env

    def test_git_availability_integration(self):
        """Test Git availability checking integration.

        Integration Test Coverage:
        - Git availability detection
        - Version checking integration
        - Command validation
        - Environment setup validation
        """
        with patch("subprocess.run") as mock_subprocess:
            # Configure mock for Git availability check
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = (
                "git version 2.34.1"  # String, not bytes
            )
            mock_subprocess.return_value.stderr = ""

            # Act: Check Git availability
            is_available = self.git_ops.check_git_available()
            version = self.git_ops.get_git_version()

            # Assert: Verify Git detection
            assert is_available
            assert version is not None
            assert "2.34.1" in version

    def test_git_environment_preparation_integration(self):
        """Test Git environment preparation integration.

        Integration Test Coverage:
        - Environment variable preparation
        - Directory path configuration
        - Index file configuration
        - Environment consistency validation
        """
        # Act: Execute operation that requires environment preparation
        with patch("subprocess.run") as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            mock_subprocess.return_value.stdout = b"status output"

            result = self.git_ops.run_git_command(["status"])

            # Assert: Verify environment was prepared correctly
            assert result.returncode == 0

            # Check environment variables were set
            env = mock_subprocess.call_args[1]["env"]
            assert env["GIT_DIR"] == str(self.repo_path)
            assert env["GIT_WORK_TREE"] == str(self.work_tree)
            assert env["GIT_INDEX_FILE"] == str(self.index_file)


class TestGitPathIntegration:
    """Integration tests for Git path handling across components."""

    def setup_method(self):
        """Set up path integration test environment."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.repo_path = self.temp_dir / ".spec"
        self.work_tree = self.temp_dir / ".specs"
        self.index_file = self.repo_path / ".spec-index"

        # Create directories
        self.repo_path.mkdir(parents=True, exist_ok=True)
        self.work_tree.mkdir(parents=True, exist_ok=True)

        self.path_converter = GitPathConverter(specs_dir=self.work_tree)
        self.git_ops = GitOperations(
            spec_dir=self.repo_path,
            specs_dir=self.work_tree,
            index_file=self.index_file,
        )

    def test_cross_platform_path_handling_integration(self):
        """Test cross-platform path handling across Git operations.

        Integration Test Coverage:
        - Path conversion consistency across platforms
        - Path normalization validation
        - Work tree relative path processing
        - Path validation and checking
        """
        # Arrange: Set up cross-platform path scenarios
        test_paths = [
            self.work_tree / "docs" / "readme.md",
            self.work_tree / "src" / "module" / "code.py",
            self.work_tree / "tests" / "integration" / "test.py",
        ]

        # Act & Assert: Test path conversion integration
        for path in test_paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("test content")

            # Convert path for Git operations
            git_path = self.path_converter.convert_to_git_path(str(path))

            # Verify path conversion consistency
            expected_relative = path.relative_to(self.work_tree)
            assert Path(git_path) == expected_relative

            # Test path validation
            assert self.path_converter.is_under_specs_dir(str(path))

            # Test path normalization
            normalized = self.path_converter.normalize_path_separators(str(path))
            assert isinstance(normalized, str)

    def test_path_conversion_round_trip_integration(self):
        """Test path conversion round-trip integration.

        Integration Test Coverage:
        - Bidirectional path conversion
        - Absolute to relative conversion
        - Relative to absolute conversion
        - Path consistency validation
        """
        # Arrange: Set up test file
        test_file = self.work_tree / "round_trip" / "test.md"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        test_file.write_text("test content")

        # Act: Perform round-trip conversion

        # Convert to Git path
        git_path = self.path_converter.convert_to_git_path(str(test_file))

        # Convert back to absolute path
        abs_path = self.path_converter.convert_from_git_path(git_path)

        # Convert to absolute specs path
        specs_path = self.path_converter.convert_to_absolute_specs_path(git_path)

        # Assert: Verify round-trip consistency
        # abs_path should be .specs/ prefixed path (relative)
        assert abs_path == Path(".specs/round_trip/test.md")
        # specs_path should be absolute path
        assert specs_path == test_file

        # Verify Git path is relative
        assert not Path(git_path).is_absolute()
        assert git_path == "round_trip/test.md"

    def test_path_info_integration(self):
        """Test path information integration across components.

        Integration Test Coverage:
        - Path information extraction
        - Conversion metadata
        - Path validation results
        - Integration data consistency
        """
        # Arrange: Set up various path scenarios
        test_paths = {
            "under_specs": self.work_tree / "under" / "test.md",
            "outside_specs": self.temp_dir / "outside" / "test.md",
            "specs_root": self.work_tree / "root.md",
        }

        for name, path in test_paths.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"Content for {name}")

        # Act & Assert: Test path information for each scenario
        for name, path in test_paths.items():
            info = self.path_converter.get_conversion_info(str(path))

            # Verify information structure
            assert "is_under_specs_dir" in info
            assert "git_path" in info
            assert "normalized_separators" in info

            if name == "under_specs" or name == "specs_root":
                assert info["is_under_specs_dir"]
                assert not Path(info["git_path"]).is_absolute()
            else:
                assert not info["is_under_specs_dir"]
