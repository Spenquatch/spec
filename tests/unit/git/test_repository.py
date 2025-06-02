from pathlib import Path
from unittest.mock import Mock, call, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.git.repository import GitRepository, SpecGitRepository


class TestSpecGitRepository:
    """Tests for SpecGitRepository class."""

    @pytest.fixture
    def mock_settings(self, tmp_path: Path) -> Mock:
        """Create mock settings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.spec_dir = tmp_path / ".spec"
        settings.specs_dir = tmp_path / ".specs"
        settings.index_file = tmp_path / ".spec-index"
        return settings

    @pytest.fixture
    def repository(self, mock_settings: Mock) -> SpecGitRepository:
        """Create SpecGitRepository instance for testing."""
        with patch("spec_cli.git.repository.get_settings", return_value=mock_settings):
            repo = SpecGitRepository(mock_settings)
            return repo

    def test_spec_git_repository_initialization(
        self, repository: SpecGitRepository, mock_settings: Mock
    ) -> None:
        """Test SpecGitRepository initializes correctly."""
        assert repository.settings == mock_settings
        assert repository.operations is not None
        assert repository.path_converter is not None

    def test_spec_git_repository_is_git_repository_interface(
        self, repository: SpecGitRepository
    ) -> None:
        """Test that SpecGitRepository implements GitRepository interface."""
        assert isinstance(repository, GitRepository)

    @patch("spec_cli.git.repository.GitOperations")
    def test_spec_git_repository_adds_files_with_force_flag(
        self, mock_git_ops_class: Mock, repository: SpecGitRepository
    ) -> None:
        """Test that files are added with force flag to bypass ignore rules."""
        # Setup mocks
        mock_operations = Mock()
        repository.operations = mock_operations

        paths = [".specs/src/main.py", ".specs/docs/README.md"]

        # Execute add
        repository.add(paths)

        # Verify run_git_command was called with force flag
        mock_operations.run_git_command.assert_called_once()
        call_args = mock_operations.run_git_command.call_args[0][0]

        assert call_args[0] == "add"
        assert call_args[1] == "-f"
        assert "src/main.py" in call_args
        assert "docs/README.md" in call_args

    def test_spec_git_repository_converts_paths_for_add(
        self, repository: SpecGitRepository
    ) -> None:
        """Test that paths are converted to Git context before adding."""
        with patch.object(repository.operations, "run_git_command") as mock_run:
            paths = [".specs/src/main.py", "docs/README.md"]

            repository.add(paths)

            # Check converted paths in the call
            call_args = mock_run.call_args[0][0]
            assert "src/main.py" in call_args
            assert "docs/README.md" in call_args

    def test_spec_git_repository_creates_commits(
        self, repository: SpecGitRepository
    ) -> None:
        """Test commit creation."""
        with patch.object(repository.operations, "run_git_command") as mock_run:
            # Mock the second call to return a commit hash
            mock_run.return_value.stdout = "abc123def456"

            message = "Test commit message"

            repository.commit(message)

            # Should be called twice: once for commit, once for rev-parse HEAD
            assert mock_run.call_count == 2
            expected_calls = [
                call(["commit", "-m", message], capture_output=False),
                call(["rev-parse", "HEAD"]),
            ]
            mock_run.assert_has_calls(expected_calls)

    def test_spec_git_repository_shows_status(
        self, repository: SpecGitRepository
    ) -> None:
        """Test status display."""
        with patch.object(repository.operations, "run_git_command") as mock_run:
            repository.status()

            mock_run.assert_called_once_with(["status"], capture_output=False)

    def test_spec_git_repository_shows_log_without_path_filter(
        self, repository: SpecGitRepository
    ) -> None:
        """Test log display without path filter."""
        with patch.object(repository.operations, "run_git_command") as mock_run:
            repository.log()

            expected_args = ["log", "--oneline", "--graph"]
            mock_run.assert_called_once_with(expected_args, capture_output=False)

    def test_spec_git_repository_shows_log_with_path_filter(
        self, repository: SpecGitRepository
    ) -> None:
        """Test log display with path filter."""
        with patch.object(repository.operations, "run_git_command") as mock_run:
            paths = [".specs/src/main.py", "docs/README.md"]

            repository.log(paths)

            call_args = mock_run.call_args[0][0]
            assert call_args[:3] == ["log", "--oneline", "--graph"]
            assert "--" in call_args

            # Check converted paths are included
            separator_index = call_args.index("--")
            filtered_paths = call_args[separator_index + 1 :]
            assert "src/main.py" in filtered_paths
            assert "docs/README.md" in filtered_paths

    def test_spec_git_repository_shows_diff_without_path_filter(
        self, repository: SpecGitRepository
    ) -> None:
        """Test diff display without path filter."""
        with patch.object(repository.operations, "run_git_command") as mock_run:
            repository.diff()

            mock_run.assert_called_once_with(["diff"], capture_output=False)

    def test_spec_git_repository_shows_diff_with_path_filter(
        self, repository: SpecGitRepository
    ) -> None:
        """Test diff display with path filter."""
        with patch.object(repository.operations, "run_git_command") as mock_run:
            paths = [".specs/src/main.py", "docs/README.md"]

            repository.diff(paths)

            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "diff"
            assert "--" in call_args

            # Check converted paths are included
            separator_index = call_args.index("--")
            filtered_paths = call_args[separator_index + 1 :]
            assert "src/main.py" in filtered_paths
            assert "docs/README.md" in filtered_paths

    def test_spec_git_repository_detects_uninitialized_repository(
        self, repository: SpecGitRepository, tmp_path: Path
    ) -> None:
        """Test detection of uninitialized repository."""
        # Ensure .spec directory doesn't exist
        spec_dir = tmp_path / ".spec"
        if spec_dir.exists():
            spec_dir.rmdir()

        assert repository.is_initialized() is False

    def test_spec_git_repository_detects_initialized_repository(
        self, repository: SpecGitRepository, tmp_path: Path
    ) -> None:
        """Test detection of initialized repository."""
        # Create .spec directory and objects subdirectory
        spec_dir = tmp_path / ".spec"
        spec_dir.mkdir(exist_ok=True)
        objects_dir = spec_dir / "objects"
        objects_dir.mkdir(exist_ok=True)

        assert repository.is_initialized() is True

    def test_spec_git_repository_detects_spec_dir_as_file(
        self, repository: SpecGitRepository, tmp_path: Path
    ) -> None:
        """Test handling when .spec exists but is a file, not directory."""
        # Create .spec as a file instead of directory
        spec_file = tmp_path / ".spec"
        spec_file.write_text("not a directory")

        assert repository.is_initialized() is False

    def test_spec_git_repository_initializes_repository(
        self, repository: SpecGitRepository, tmp_path: Path
    ) -> None:
        """Test repository initialization."""
        with patch.object(repository.operations, "initialize_repository") as mock_init:
            repository.initialize_repository()

            # Verify directories are created
            assert repository.settings.spec_dir.exists()
            assert repository.settings.specs_dir.exists()

            # Verify Git initialization was called
            mock_init.assert_called_once()

    def test_spec_git_repository_skips_initialization_if_already_initialized(
        self, repository: SpecGitRepository, tmp_path: Path
    ) -> None:
        """Test that initialization is skipped if repository already exists."""
        # Setup repository as already initialized
        spec_dir = tmp_path / ".spec"
        spec_dir.mkdir(exist_ok=True)
        objects_dir = spec_dir / "objects"
        objects_dir.mkdir(exist_ok=True)

        with patch.object(repository.operations, "initialize_repository") as mock_init:
            repository.initialize_repository()

            # Should not call Git initialization
            mock_init.assert_not_called()

    def test_spec_git_repository_gets_repository_info(
        self, repository: SpecGitRepository, tmp_path: Path
    ) -> None:
        """Test getting repository information."""
        info = repository.get_repository_info()

        # Check basic information is present
        assert "is_initialized" in info
        assert "spec_dir" in info
        assert "specs_dir" in info
        assert "index_file" in info

        # Check values
        assert info["spec_dir"] == str(repository.settings.spec_dir)
        assert info["specs_dir"] == str(repository.settings.specs_dir)
        assert info["index_file"] == str(repository.settings.index_file)

    def test_spec_git_repository_info_includes_file_existence_when_initialized(
        self, repository: SpecGitRepository, tmp_path: Path
    ) -> None:
        """Test that repository info includes file existence when initialized."""
        # Setup repository as initialized
        spec_dir = tmp_path / ".spec"
        spec_dir.mkdir(exist_ok=True)
        objects_dir = spec_dir / "objects"
        objects_dir.mkdir(exist_ok=True)

        info = repository.get_repository_info()

        # Check that additional info is included for initialized repository
        assert info["is_initialized"] is True
        assert "spec_dir_exists" in info
        assert "specs_dir_exists" in info
        assert "index_file_exists" in info

    def test_spec_git_repository_info_handles_errors(
        self, repository: SpecGitRepository
    ) -> None:
        """Test that repository info handles errors gracefully."""
        # Force is_initialized to return True and make get_repository_info raise an error
        with patch.object(repository, "is_initialized", return_value=True):
            with patch("pathlib.Path.exists", side_effect=Exception("Test error")):
                info = repository.get_repository_info()

                assert "error" in info
                assert "Test error" in info["error"]

    def test_spec_git_repository_uses_provided_settings(
        self, mock_settings: Mock
    ) -> None:
        """Test that repository uses provided settings instead of defaults."""
        repo = SpecGitRepository(mock_settings)

        assert repo.settings == mock_settings

    def test_spec_git_repository_uses_default_settings_when_none_provided(self) -> None:
        """Test that repository gets default settings when none provided."""
        with patch("spec_cli.git.repository.get_settings") as mock_get_settings:
            mock_settings = Mock()
            mock_get_settings.return_value = mock_settings

            repo = SpecGitRepository()

            assert repo.settings == mock_settings
            mock_get_settings.assert_called_once()

    def test_spec_git_repository_handles_long_commit_messages(
        self, repository: SpecGitRepository
    ) -> None:
        """Test handling of long commit messages in logging."""
        with patch.object(repository.operations, "run_git_command") as mock_run:
            # Mock the second call to return a commit hash
            mock_run.return_value.stdout = "abc123def456"

            long_message = "A" * 100  # Create message longer than 50 characters

            repository.commit(long_message)

            # Should be called twice: once for commit, once for rev-parse HEAD
            assert mock_run.call_count == 2
            expected_calls = [
                call(["commit", "-m", long_message], capture_output=False),
                call(["rev-parse", "HEAD"]),
            ]
            mock_run.assert_has_calls(expected_calls)

    def test_spec_git_repository_path_converter_integration(
        self, repository: SpecGitRepository
    ) -> None:
        """Test integration with GitPathConverter."""
        # Test that path converter is properly initialized and used
        test_path = ".specs/src/main.py"
        expected_git_path = "src/main.py"

        actual_git_path = repository.path_converter.convert_to_git_path(test_path)
        assert actual_git_path == expected_git_path
