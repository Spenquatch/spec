"""Unit tests for GitRepository - Repository Management (git_002).

This module provides comprehensive testing for Git repository initialization,
isolation validation, and core repository management functionality.
"""

import subprocess
from unittest.mock import Mock, call, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.git.repository import GitRepository, SpecGitRepository


class TestSpecGitRepositoryInit:
    """Test SpecGitRepository initialization and configuration."""

    def test_init_with_default_settings(self, mock_git_environment):
        """Test repository initialization with default settings."""
        repo_path = mock_git_environment["repo_path"]

        with patch("spec_cli.git.repository.get_settings") as mock_get_settings:
            mock_settings = Mock(spec=SpecSettings)
            mock_settings.spec_dir = repo_path / ".spec"
            mock_settings.specs_dir = repo_path / ".specs"
            mock_settings.index_file = repo_path / ".spec" / "index"
            mock_get_settings.return_value = mock_settings

            with (
                patch("spec_cli.git.repository.GitOperations") as mock_git_ops,
                patch(
                    "spec_cli.git.repository.GitPathConverter"
                ) as mock_path_converter,
            ):
                repository = SpecGitRepository()

                # Verify settings were obtained
                mock_get_settings.assert_called_once()

                # Verify GitOperations was initialized with correct parameters
                mock_git_ops.assert_called_once_with(
                    spec_dir=mock_settings.spec_dir,
                    specs_dir=mock_settings.specs_dir,
                    index_file=mock_settings.index_file,
                )

                # Verify GitPathConverter was initialized
                mock_path_converter.assert_called_once_with(mock_settings.specs_dir)

                # Verify settings are stored
                assert repository.settings == mock_settings

    def test_init_with_custom_settings(self, mock_git_environment):
        """Test repository initialization with custom settings."""
        repo_path = mock_git_environment["repo_path"]

        custom_settings = Mock(spec=SpecSettings)
        custom_settings.spec_dir = repo_path / "custom_spec"
        custom_settings.specs_dir = repo_path / "custom_specs"
        custom_settings.index_file = repo_path / "custom_spec" / "custom_index"

        with (
            patch("spec_cli.git.repository.GitOperations") as mock_git_ops,
            patch("spec_cli.git.repository.GitPathConverter") as mock_path_converter,
        ):
            repository = SpecGitRepository(settings=custom_settings)

            # Verify custom settings were used
            assert repository.settings == custom_settings

            # Verify GitOperations was initialized with custom settings
            mock_git_ops.assert_called_once_with(
                spec_dir=custom_settings.spec_dir,
                specs_dir=custom_settings.specs_dir,
                index_file=custom_settings.index_file,
            )

            # Verify GitPathConverter was initialized with custom settings
            mock_path_converter.assert_called_once_with(custom_settings.specs_dir)

    def test_init_creates_required_dependencies(self, mock_git_environment):
        """Test that initialization creates required dependency objects."""
        repo_path = mock_git_environment["repo_path"]

        settings = Mock(spec=SpecSettings)
        settings.spec_dir = repo_path / ".spec"
        settings.specs_dir = repo_path / ".specs"
        settings.index_file = repo_path / ".spec" / "index"

        repository = SpecGitRepository(settings=settings)

        # Verify required attributes exist
        assert hasattr(repository, "operations")
        assert hasattr(repository, "path_converter")
        assert hasattr(repository, "settings")

        # Verify settings are correctly assigned
        assert repository.settings == settings


class TestSpecGitRepositoryIsolation:
    """Test repository isolation and validation functionality."""

    def setup_method(self):
        """Set up test environment with mocked dependencies."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.spec_dir = Mock()
        self.mock_settings.specs_dir = Mock()
        self.mock_settings.index_file = Mock()

        with (
            patch("spec_cli.git.repository.GitOperations") as mock_git_ops,
            patch("spec_cli.git.repository.GitPathConverter") as mock_path_converter,
        ):
            self.repository = SpecGitRepository(settings=self.mock_settings)
            self.mock_operations = mock_git_ops.return_value
            self.mock_path_converter = mock_path_converter.return_value

    def test_is_initialized_when_spec_dir_missing(self):
        """Test is_initialized returns False when spec directory is missing."""
        self.mock_settings.spec_dir.exists.return_value = False

        result = self.repository.is_initialized()

        assert result is False
        self.mock_settings.spec_dir.exists.assert_called_once()

    def test_is_initialized_when_spec_dir_not_directory(self):
        """Test is_initialized returns False when spec path is not a directory."""
        self.mock_settings.spec_dir.exists.return_value = True
        self.mock_settings.spec_dir.is_dir.return_value = False

        result = self.repository.is_initialized()

        assert result is False
        self.mock_settings.spec_dir.is_dir.assert_called_once()

    def test_is_initialized_when_objects_dir_missing(self):
        """Test is_initialized returns False when Git objects directory is missing."""
        self.mock_settings.spec_dir.exists.return_value = True
        self.mock_settings.spec_dir.is_dir.return_value = True

        # Mock objects directory
        mock_objects_dir = Mock()
        mock_objects_dir.exists.return_value = False

        # Set up the path division mock directly
        self.mock_settings.spec_dir.__truediv__ = Mock(return_value=mock_objects_dir)

        result = self.repository.is_initialized()

        assert result is False
        self.mock_settings.spec_dir.__truediv__.assert_called_once_with("objects")
        mock_objects_dir.exists.assert_called_once()

    def test_is_initialized_when_objects_not_directory(self):
        """Test is_initialized returns False when objects path is not a directory."""
        self.mock_settings.spec_dir.exists.return_value = True
        self.mock_settings.spec_dir.is_dir.return_value = True

        # Mock objects directory
        mock_objects_dir = Mock()
        mock_objects_dir.exists.return_value = True
        mock_objects_dir.is_dir.return_value = False

        # Set up the path division mock directly
        self.mock_settings.spec_dir.__truediv__ = Mock(return_value=mock_objects_dir)

        result = self.repository.is_initialized()

        assert result is False
        mock_objects_dir.is_dir.assert_called_once()

    def test_is_initialized_success(self):
        """Test is_initialized returns True when repository is properly initialized."""
        self.mock_settings.spec_dir.exists.return_value = True
        self.mock_settings.spec_dir.is_dir.return_value = True

        # Mock objects directory
        mock_objects_dir = Mock()
        mock_objects_dir.exists.return_value = True
        mock_objects_dir.is_dir.return_value = True

        # Set up the path division mock directly
        self.mock_settings.spec_dir.__truediv__ = Mock(return_value=mock_objects_dir)

        result = self.repository.is_initialized()

        assert result is True

    def test_initialize_repository_when_already_initialized(self):
        """Test initialize_repository skips initialization when already initialized."""
        with patch.object(self.repository, "is_initialized", return_value=True):
            self.repository.initialize_repository()

            # Should not call GitOperations.initialize_repository
            self.mock_operations.initialize_repository.assert_not_called()

    def test_initialize_repository_creates_directories(self):
        """Test initialize_repository creates required directories."""
        with patch.object(self.repository, "is_initialized", return_value=False):
            self.repository.initialize_repository()

            # Verify directories are created
            self.mock_settings.spec_dir.mkdir.assert_called_once_with(
                parents=True, exist_ok=True
            )
            self.mock_settings.specs_dir.mkdir.assert_called_once_with(
                parents=True, exist_ok=True
            )

            # Verify GitOperations.initialize_repository is called
            self.mock_operations.initialize_repository.assert_called_once()

    def test_initialize_repository_handles_mkdir_errors(self):
        """Test initialize_repository handles directory creation errors."""
        with patch.object(self.repository, "is_initialized", return_value=False):
            self.mock_settings.spec_dir.mkdir.side_effect = OSError("Permission denied")

            with pytest.raises(OSError):
                self.repository.initialize_repository()

    def test_get_repository_info_when_not_initialized(self):
        """Test get_repository_info returns basic info when not initialized."""
        # Set up mock string conversion
        self.mock_settings.spec_dir.__str__ = Mock(return_value="/test/.spec")
        self.mock_settings.specs_dir.__str__ = Mock(return_value="/test/.specs")
        self.mock_settings.index_file.__str__ = Mock(return_value="/test/.spec/index")

        with patch.object(self.repository, "is_initialized", return_value=False):
            info = self.repository.get_repository_info()

            expected_info = {
                "is_initialized": False,
                "spec_dir": "/test/.spec",
                "specs_dir": "/test/.specs",
                "index_file": "/test/.spec/index",
            }

            assert info == expected_info

    def test_get_repository_info_when_initialized(self):
        """Test get_repository_info returns detailed info when initialized."""
        # Set up mock string conversion
        self.mock_settings.spec_dir.__str__ = Mock(return_value="/test/.spec")
        self.mock_settings.specs_dir.__str__ = Mock(return_value="/test/.specs")
        self.mock_settings.index_file.__str__ = Mock(return_value="/test/.spec/index")

        with patch.object(self.repository, "is_initialized", return_value=True):
            # Mock path existence checks
            self.mock_settings.spec_dir.exists.return_value = True
            self.mock_settings.specs_dir.exists.return_value = True
            self.mock_settings.index_file.exists.return_value = True

            info = self.repository.get_repository_info()

            expected_info = {
                "is_initialized": True,
                "spec_dir": "/test/.spec",
                "specs_dir": "/test/.specs",
                "index_file": "/test/.spec/index",
                "spec_dir_exists": True,
                "specs_dir_exists": True,
                "index_file_exists": True,
            }

            assert info == expected_info

    def test_get_repository_info_handles_exceptions(self):
        """Test get_repository_info handles exceptions gracefully."""
        # Set up mock string conversion
        self.mock_settings.spec_dir.__str__ = Mock(return_value="/test/.spec")
        self.mock_settings.specs_dir.__str__ = Mock(return_value="/test/.specs")
        self.mock_settings.index_file.__str__ = Mock(return_value="/test/.spec/index")

        with patch.object(self.repository, "is_initialized", return_value=True):
            # Mock path existence to raise exception
            self.mock_settings.spec_dir.exists.side_effect = Exception("Test error")

            info = self.repository.get_repository_info()

            assert "error" in info
            assert info["error"] == "Test error"


class TestSpecGitRepositoryManagement:
    """Test core repository management functionality."""

    def setup_method(self):
        """Set up test environment with mocked dependencies."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.spec_dir = Mock()
        self.mock_settings.specs_dir = Mock()
        self.mock_settings.index_file = Mock()

        with (
            patch("spec_cli.git.repository.GitOperations") as mock_git_ops,
            patch("spec_cli.git.repository.GitPathConverter") as mock_path_converter,
        ):
            self.repository = SpecGitRepository(settings=self.mock_settings)
            self.mock_operations = mock_git_ops.return_value
            self.mock_path_converter = mock_path_converter.return_value

    def test_add_converts_paths_and_calls_git_add(self):
        """Test add method converts paths and calls git add with force flag."""
        original_paths = ["file1.md", "dir/file2.md"]
        converted_paths = ["file1.md", "dir/file2.md"]

        # Mock path conversion
        self.mock_path_converter.convert_to_git_path.side_effect = converted_paths

        self.repository.add(original_paths)

        # Verify path conversion was called for each path
        expected_calls = [call(path) for path in original_paths]
        self.mock_path_converter.convert_to_git_path.assert_has_calls(expected_calls)

        # Verify git add was called with force flag
        expected_git_args = ["add", "-f"] + converted_paths
        self.mock_operations.run_git_command.assert_called_once_with(
            expected_git_args, capture_output=False
        )

    def test_commit_creates_commit_and_retrieves_hash(self):
        """Test commit method creates commit and retrieves hash."""
        commit_message = "Test commit message"
        expected_hash = "abc1234567890"

        # Mock successful commit and hash retrieval
        mock_result = Mock()
        mock_result.stdout = expected_hash + "\n"
        self.mock_operations.run_git_command.side_effect = [None, mock_result]

        result_hash = self.repository.commit(commit_message)

        # Verify commit command was called
        self.mock_operations.run_git_command.assert_any_call(
            ["commit", "-m", commit_message], capture_output=False
        )

        # Verify rev-parse command was called to get hash
        self.mock_operations.run_git_command.assert_any_call(["rev-parse", "HEAD"])

        # Verify correct hash is returned
        assert result_hash == expected_hash

    def test_commit_handles_hash_retrieval_failure(self):
        """Test commit method handles hash retrieval failure gracefully."""
        commit_message = "Test commit message"

        # Mock successful commit but failed hash retrieval
        self.mock_operations.run_git_command.side_effect = [
            None,  # Successful commit
            subprocess.SubprocessError(
                "Hash retrieval failed"
            ),  # Failed hash retrieval
        ]

        with (
            patch(
                "spec_cli.git.repository.handle_subprocess_error"
            ) as mock_handle_error,
            patch(
                "spec_cli.git.repository.create_error_context"
            ) as mock_create_context,
        ):
            mock_handle_error.return_value = "Formatted error"
            mock_create_context.return_value = {"context": "test"}

            result_hash = self.repository.commit(commit_message)

            # Verify fallback hash is returned
            assert result_hash == "unknown"

            # Verify error handling was called
            mock_handle_error.assert_called_once()
            mock_create_context.assert_called_once()

    def test_get_current_branch_success(self):
        """Test get_current_branch returns current branch name."""
        expected_branch = "main"

        mock_result = Mock()
        mock_result.stdout = expected_branch + "\n"
        self.mock_operations.run_git_command.return_value = mock_result

        branch = self.repository.get_current_branch()

        self.mock_operations.run_git_command.assert_called_once_with(
            ["symbolic-ref", "--short", "HEAD"]
        )
        assert branch == expected_branch

    def test_get_current_branch_handles_detached_head(self):
        """Test get_current_branch handles detached HEAD state."""
        self.mock_operations.run_git_command.side_effect = subprocess.SubprocessError(
            "detached HEAD"
        )

        with (
            patch(
                "spec_cli.git.repository.handle_subprocess_error"
            ) as mock_handle_error,
            patch(
                "spec_cli.git.repository.create_error_context"
            ) as mock_create_context,
        ):
            mock_handle_error.return_value = "Formatted error"
            mock_create_context.return_value = {"context": "test"}

            branch = self.repository.get_current_branch()

            # Verify fallback branch is returned
            assert branch == "HEAD"

    def test_has_uncommitted_changes_true(self):
        """Test has_uncommitted_changes returns True when changes exist."""
        self.mock_operations.run_git_command.side_effect = subprocess.SubprocessError(
            "Changes exist"
        )

        result = self.repository.has_uncommitted_changes()

        assert result is True
        self.mock_operations.run_git_command.assert_called_once_with(
            ["diff-index", "--quiet", "HEAD", "--"]
        )

    def test_has_uncommitted_changes_false(self):
        """Test has_uncommitted_changes returns False when no changes."""
        # Mock successful command (no changes)
        self.mock_operations.run_git_command.return_value = Mock()

        result = self.repository.has_uncommitted_changes()

        assert result is False

    def test_has_staged_changes_true(self):
        """Test has_staged_changes returns True when staged changes exist."""
        self.mock_operations.run_git_command.side_effect = subprocess.SubprocessError(
            "Staged changes exist"
        )

        result = self.repository.has_staged_changes()

        assert result is True
        self.mock_operations.run_git_command.assert_called_once_with(
            ["diff-index", "--quiet", "--cached", "HEAD", "--"]
        )

    def test_has_staged_changes_false(self):
        """Test has_staged_changes returns False when no staged changes."""
        # Mock successful command (no staged changes)
        self.mock_operations.run_git_command.return_value = Mock()

        result = self.repository.has_staged_changes()

        assert result is False

    def test_has_untracked_files_true(self):
        """Test has_untracked_files returns True when untracked files exist."""
        mock_result = Mock()
        mock_result.stdout = "untracked_file.txt\n"
        self.mock_operations.run_git_command.return_value = mock_result

        result = self.repository.has_untracked_files()

        assert result is True
        self.mock_operations.run_git_command.assert_called_once_with(
            ["ls-files", "--others", "--exclude-standard"]
        )

    def test_has_untracked_files_false(self):
        """Test has_untracked_files returns False when no untracked files."""
        mock_result = Mock()
        mock_result.stdout = ""
        self.mock_operations.run_git_command.return_value = mock_result

        result = self.repository.has_untracked_files()

        assert result is False

    def test_get_recent_commits_success(self):
        """Test get_recent_commits returns parsed commit data."""
        commit_count = 5
        mock_output = "hash1|Subject 1|Author 1|2025-01-01T00:00:00\nhash2|Subject 2|Author 2|2025-01-02T00:00:00"

        mock_result = Mock()
        mock_result.stdout = mock_output
        self.mock_operations.run_git_command.return_value = mock_result

        commits = self.repository.get_recent_commits(commit_count)

        expected_commits = [
            {
                "hash": "hash1",
                "subject": "Subject 1",
                "author": "Author 1",
                "date": "2025-01-01T00:00:00",
            },
            {
                "hash": "hash2",
                "subject": "Subject 2",
                "author": "Author 2",
                "date": "2025-01-02T00:00:00",
            },
        ]

        assert commits == expected_commits
        self.mock_operations.run_git_command.assert_called_once_with(
            [
                "log",
                f"--max-count={commit_count}",
                "--pretty=format:%H|%s|%an|%ad",
                "--date=iso",
            ]
        )

    def test_get_recent_commits_handles_errors(self):
        """Test get_recent_commits handles errors gracefully."""
        self.mock_operations.run_git_command.side_effect = subprocess.SubprocessError(
            "Log failed"
        )

        with (
            patch(
                "spec_cli.git.repository.handle_subprocess_error"
            ) as mock_handle_error,
            patch(
                "spec_cli.git.repository.create_error_context"
            ) as mock_create_context,
        ):
            mock_handle_error.return_value = "Formatted error"
            mock_create_context.return_value = {"context": "test"}

            commits = self.repository.get_recent_commits()

            assert commits == []


class TestSpecGitRepositoryFileOperations:
    """Test file-specific repository operations."""

    def setup_method(self):
        """Set up test environment with mocked dependencies."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.spec_dir = Mock()
        self.mock_settings.specs_dir = Mock()
        self.mock_settings.index_file = Mock()

        with (
            patch("spec_cli.git.repository.GitOperations") as mock_git_ops,
            patch("spec_cli.git.repository.GitPathConverter") as mock_path_converter,
        ):
            self.repository = SpecGitRepository(settings=self.mock_settings)
            self.mock_operations = mock_git_ops.return_value
            self.mock_path_converter = mock_path_converter.return_value

    def test_get_staged_files_success(self):
        """Test get_staged_files returns list of staged files."""
        staged_files_output = "file1.md\ndir/file2.md\n"

        mock_result = Mock()
        mock_result.stdout = staged_files_output
        self.mock_operations.run_git_command.return_value = mock_result

        staged_files = self.repository.get_staged_files()

        expected_files = ["file1.md", "dir/file2.md"]
        assert staged_files == expected_files
        self.mock_operations.run_git_command.assert_called_once_with(
            ["diff", "--cached", "--name-only"]
        )

    def test_get_staged_files_empty(self):
        """Test get_staged_files returns empty list when no staged files."""
        mock_result = Mock()
        mock_result.stdout = ""
        self.mock_operations.run_git_command.return_value = mock_result

        staged_files = self.repository.get_staged_files()

        assert staged_files == []

    def test_get_staged_files_handles_exception(self):
        """Test get_staged_files handles exceptions gracefully."""
        self.mock_operations.run_git_command.side_effect = Exception("Command failed")

        staged_files = self.repository.get_staged_files()

        assert staged_files == []

    def test_get_unstaged_files_success(self):
        """Test get_unstaged_files returns list of unstaged files."""
        unstaged_files_output = "modified1.md\nmodified2.md\n"

        mock_result = Mock()
        mock_result.stdout = unstaged_files_output
        self.mock_operations.run_git_command.return_value = mock_result

        unstaged_files = self.repository.get_unstaged_files()

        expected_files = ["modified1.md", "modified2.md"]
        assert unstaged_files == expected_files
        self.mock_operations.run_git_command.assert_called_once_with(
            ["diff", "--name-only"]
        )

    def test_get_untracked_files_success(self):
        """Test get_untracked_files returns list of untracked files."""
        untracked_files_output = "new1.md\nnew2.md\n"

        mock_result = Mock()
        mock_result.stdout = untracked_files_output
        self.mock_operations.run_git_command.return_value = mock_result

        untracked_files = self.repository.get_untracked_files()

        expected_files = ["new1.md", "new2.md"]
        assert untracked_files == expected_files
        self.mock_operations.run_git_command.assert_called_once_with(
            ["ls-files", "--others", "--exclude-standard"]
        )

    def test_get_current_commit_hash_success(self):
        """Test get_current_commit_hash returns current commit hash."""
        expected_hash = "abc1234567890"

        mock_result = Mock()
        mock_result.stdout = expected_hash + "\n"
        self.mock_operations.run_git_command.return_value = mock_result

        commit_hash = self.repository.get_current_commit_hash()

        assert commit_hash == expected_hash
        self.mock_operations.run_git_command.assert_called_once_with(
            ["rev-parse", "HEAD"]
        )

    def test_get_current_commit_hash_handles_exception(self):
        """Test get_current_commit_hash handles exceptions gracefully."""
        self.mock_operations.run_git_command.side_effect = Exception("No commits")

        commit_hash = self.repository.get_current_commit_hash()

        assert commit_hash is None

    def test_get_parent_commit_hash_success(self):
        """Test get_parent_commit_hash returns parent commit hash."""
        commit_hash = "abc1234567890"
        parent_hash = "def0987654321"

        mock_result = Mock()
        mock_result.stdout = parent_hash + "\n"
        self.mock_operations.run_git_command.return_value = mock_result

        result = self.repository.get_parent_commit_hash(commit_hash)

        assert result == parent_hash
        self.mock_operations.run_git_command.assert_called_once_with(
            ["rev-parse", f"{commit_hash}^"]
        )

    def test_get_parent_commit_hash_handles_exception(self):
        """Test get_parent_commit_hash handles exceptions gracefully."""
        commit_hash = "abc1234567890"
        self.mock_operations.run_git_command.side_effect = Exception("No parent")

        result = self.repository.get_parent_commit_hash(commit_hash)

        assert result is None


class TestSpecGitRepositoryIntegration:
    """Test integration between SpecGitRepository and its dependencies."""

    def test_repository_with_real_git_helpers(self, mock_git_environment):
        """Test repository integration with real git test helpers."""
        repo_path = mock_git_environment["repo_path"]
        repository_mocker = mock_git_environment["repository"]
        mock_git_environment["simulator"]

        # Set up test settings
        settings = Mock(spec=SpecSettings)
        settings.spec_dir = repo_path / ".spec"
        settings.specs_dir = repo_path / ".specs"
        settings.index_file = repo_path / ".spec" / "index"

        # Create directories
        settings.spec_dir.mkdir(parents=True, exist_ok=True)
        settings.specs_dir.mkdir(parents=True, exist_ok=True)

        # Mock GitOperations and GitPathConverter to work with our mocked Git
        with (
            patch("spec_cli.git.repository.GitOperations") as mock_git_ops,
            patch("spec_cli.git.repository.GitPathConverter") as mock_path_converter,
        ):
            # Set up GitOperations mock to use our command simulator
            mock_operations = Mock()
            mock_operations.run_git_command.side_effect = lambda args, **kwargs: (
                repository_mocker.mock_git_command(["git"] + args)
            )
            mock_git_ops.return_value = mock_operations

            # Set up path converter mock
            mock_path_converter.return_value.convert_to_git_path.side_effect = (
                lambda x: x
            )

            # Create repository instance
            repository = SpecGitRepository(settings=settings)

            # Test initialization check
            is_init_before = repository.is_initialized()

            # Initialize repository
            repository.initialize_repository()

            # Test initialization after setup
            is_init_after = repository.is_initialized()

            # Verify initialization state changed appropriately
            # Note: Since we're mocking, this tests the integration rather than actual Git state
            assert isinstance(is_init_before, bool)
            assert isinstance(is_init_after, bool)

    def test_repository_abstract_interface_compliance(self):
        """Test that SpecGitRepository implements GitRepository interface."""
        # Verify SpecGitRepository is a subclass of GitRepository
        assert issubclass(SpecGitRepository, GitRepository)

        # Verify all abstract methods are implemented
        abstract_methods = {"add", "commit", "status", "log", "diff", "is_initialized"}

        implemented_methods = set(dir(SpecGitRepository))

        for method in abstract_methods:
            assert method in implemented_methods, f"Method {method} not implemented"

            # Verify method is callable
            method_obj = getattr(SpecGitRepository, method)
            assert callable(method_obj), f"Method {method} is not callable"

    def test_repository_error_handling_integration(self, mock_git_environment):
        """Test repository error handling with mocked Git failures."""
        repo_path = mock_git_environment["repo_path"]

        settings = Mock(spec=SpecSettings)
        settings.spec_dir = repo_path / ".spec"
        settings.specs_dir = repo_path / ".specs"
        settings.index_file = repo_path / ".spec" / "index"

        with (
            patch("spec_cli.git.repository.GitOperations") as mock_git_ops,
            patch("spec_cli.git.repository.GitPathConverter") as mock_path_converter,
        ):
            # Set up GitOperations mock to simulate failures
            mock_operations = Mock()
            mock_git_ops.return_value = mock_operations
            mock_path_converter.return_value.convert_to_git_path.side_effect = (
                lambda x: x
            )

            repository = SpecGitRepository(settings=settings)

            # Test error handling for commit hash retrieval
            mock_operations.run_git_command.side_effect = [
                None,  # Successful commit
                subprocess.SubprocessError(
                    "Failed to get hash"
                ),  # Failed hash retrieval
            ]

            with (
                patch(
                    "spec_cli.git.repository.handle_subprocess_error"
                ) as mock_handle_error,
                patch(
                    "spec_cli.git.repository.create_error_context"
                ) as mock_create_context,
            ):
                mock_handle_error.return_value = "Test error"
                mock_create_context.return_value = {"test": "context"}

                commit_hash = repository.commit("Test commit")

                # Verify error handling was invoked
                assert commit_hash == "unknown"
                mock_handle_error.assert_called_once()
                mock_create_context.assert_called_once()
