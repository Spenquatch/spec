"""Tests for status command (commands/status.py)."""

from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

from click.testing import CliRunner

from spec_cli.cli.commands.status import status_command
from spec_cli.exceptions import SpecRepositoryError


class TestStatusCommand:
    """Test cases for status command functionality."""

    @patch("spec_cli.cli.commands.status.get_spec_repository")
    @patch("spec_cli.cli.commands.status._get_repository_status")
    @patch("spec_cli.cli.commands.status._display_repository_status")
    def test_status_command_success(
        self, mock_display: Mock, mock_get_status: Mock, mock_get_repo: Mock
    ) -> None:
        """Test successful status command execution."""
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_status_data = {
            "repository": {"initialized": True},
            "files": {"total_spec_files": 5},
            "git": {"staged_files": 2},
        }
        mock_get_status.return_value = mock_status_data

        runner = CliRunner()
        result = runner.invoke(status_command, [])

        assert result.exit_code == 0
        assert "Checking repository status" in result.output
        mock_get_status.assert_called_once_with(mock_repo)
        mock_display.assert_called_once_with(mock_status_data)

    @patch("spec_cli.cli.commands.status.get_spec_repository")
    @patch("spec_cli.cli.commands.status._get_repository_health")
    @patch("spec_cli.cli.commands.status._display_health_check")
    def test_status_command_health_check(
        self, mock_display: Mock, mock_get_health: Mock, mock_get_repo: Mock
    ) -> None:
        """Test status command with health check option."""
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_health_data = {
            "repository_structure": {"status": "healthy", "details": []},
            "git_configuration": {"status": "healthy", "details": []},
        }
        mock_get_health.return_value = mock_health_data

        runner = CliRunner()
        result = runner.invoke(status_command, ["--health"])

        assert result.exit_code == 0
        assert "Running repository health check" in result.output
        mock_get_health.assert_called_once_with(mock_repo)
        mock_display.assert_called_once_with(mock_health_data)

    @patch("spec_cli.cli.commands.status.get_spec_repository")
    @patch("spec_cli.cli.commands.status._get_repository_status")
    @patch("spec_cli.cli.commands.status._display_repository_status")
    @patch("spec_cli.cli.commands.status._get_git_status_data")
    @patch("spec_cli.cli.commands.status._display_git_status")
    def test_status_command_with_git(
        self,
        mock_display_git: Mock,
        mock_get_git_status: Mock,
        mock_display: Mock,
        mock_get_status: Mock,
        mock_get_repo: Mock,
    ) -> None:
        """Test status command with git option."""
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_status_data: Dict[str, Any] = {"repository": {}, "files": {}, "git": {}}
        mock_get_status.return_value = mock_status_data
        mock_git_status: Dict[str, List[str]] = {
            "staged": [],
            "modified": [],
            "untracked": [],
        }
        mock_get_git_status.return_value = mock_git_status

        runner = CliRunner()
        result = runner.invoke(status_command, ["--git"])

        assert result.exit_code == 0
        mock_get_git_status.assert_called_once_with(mock_repo)
        mock_display_git.assert_called_once_with(mock_git_status)

    @patch("spec_cli.cli.commands.status.get_spec_repository")
    @patch("spec_cli.cli.commands.status._get_repository_status")
    @patch("spec_cli.cli.commands.status._display_repository_status")
    @patch("spec_cli.cli.commands.status._display_processing_summary")
    def test_status_command_with_summary(
        self,
        mock_display_summary: Mock,
        mock_display: Mock,
        mock_get_status: Mock,
        mock_get_repo: Mock,
    ) -> None:
        """Test status command with summary option."""
        mock_repo = MagicMock()
        mock_get_repo.return_value = mock_repo
        mock_status_data: Dict[str, Any] = {"repository": {}, "files": {}, "git": {}}
        mock_get_status.return_value = mock_status_data

        runner = CliRunner()
        result = runner.invoke(status_command, ["--summary"])

        assert result.exit_code == 0
        mock_display_summary.assert_called_once()

    @patch("spec_cli.cli.commands.status.get_spec_repository")
    def test_status_command_repository_error(self, mock_get_repo: Mock) -> None:
        """Test status command with repository error."""
        mock_get_repo.side_effect = SpecRepositoryError("Test error")

        runner = CliRunner()
        result = runner.invoke(status_command, [])

        assert result.exit_code != 0
        assert "Repository error" in result.output

    @patch("spec_cli.cli.commands.status.get_spec_repository")
    def test_status_command_unexpected_error(self, mock_get_repo: Mock) -> None:
        """Test status command with unexpected error."""
        mock_get_repo.side_effect = Exception("Unexpected error")

        runner = CliRunner()
        result = runner.invoke(status_command, [])

        assert result.exit_code != 0
        assert "Status check failed" in result.output

    def test_status_command_help(self) -> None:
        """Test status command help display."""
        runner = CliRunner()
        result = runner.invoke(status_command, ["--help"])

        assert result.exit_code == 0
        assert "Show repository status" in result.output
        assert "--health" in result.output
        assert "--git" in result.output
        assert "--summary" in result.output


class TestStatusHelperFunctions:
    """Test cases for status command helper functions."""

    @patch("spec_cli.cli.commands.status.Path")
    def test_get_repository_status(self, mock_path: Mock) -> None:
        """Test _get_repository_status function."""
        from spec_cli.cli.commands.status import _get_repository_status

        mock_repo = MagicMock()
        mock_repo.is_initialized.return_value = True
        mock_repo.get_git_status.return_value = {
            "staged": ["file1.md"],
            "modified": ["file2.md"],
            "untracked": [],
        }

        # Mock Path objects and their methods
        mock_path.cwd.return_value.return_value = "/test/dir"

        result = _get_repository_status(mock_repo)

        assert "repository" in result
        assert "files" in result
        assert "git" in result
        assert result["repository"]["initialized"] is True

    def test_get_processing_summary(self) -> None:
        """Test _get_processing_summary function."""
        from spec_cli.cli.commands.status import _get_processing_summary

        result = _get_processing_summary()

        assert "template_system" in result
        assert "file_processing" in result
        assert "ai_integration" in result

    def test_get_git_status_data_success(self) -> None:
        """Test _get_git_status_data function with successful repo operations."""
        from spec_cli.cli.commands.status import _get_git_status_data

        mock_repo = MagicMock()
        mock_repo.get_staged_files.return_value = ["staged.md"]
        mock_repo.get_unstaged_files.return_value = ["modified.md"]
        mock_repo.get_untracked_files.return_value = ["untracked.md"]

        result = _get_git_status_data(mock_repo)

        assert result == {
            "staged": ["staged.md"],
            "modified": ["modified.md"],
            "untracked": ["untracked.md"],
        }

    def test_get_git_status_data_exception(self) -> None:
        """Test _get_git_status_data function when repo operations fail."""
        from spec_cli.cli.commands.status import _get_git_status_data

        mock_repo = MagicMock()
        mock_repo.get_staged_files.side_effect = Exception("Git error")

        result = _get_git_status_data(mock_repo)

        assert result == {"staged": [], "modified": [], "untracked": []}

    @patch("spec_cli.cli.commands.status.Path")
    def test_get_repository_health_healthy(self, mock_path: Mock) -> None:
        """Test _get_repository_health function with healthy repo."""
        from spec_cli.cli.commands.status import _get_repository_health

        mock_repo = MagicMock()

        # Mock directories exist and are healthy
        mock_spec_dir = MagicMock()
        mock_spec_dir.exists.return_value = True
        mock_spec_dir.is_dir.return_value = True
        mock_specs_dir = MagicMock()
        mock_specs_dir.exists.return_value = True
        mock_specs_dir.is_dir.return_value = True

        def path_side_effect(path: str) -> Any:
            if path == ".spec":
                return mock_spec_dir
            elif path == ".specs":
                return mock_specs_dir
            else:
                return MagicMock()

        mock_path.side_effect = path_side_effect

        with patch("spec_cli.cli.commands.status._get_git_status_data") as mock_git:
            mock_git.return_value = {
                "staged": ["file.md"],
                "modified": [],
                "untracked": [],
            }

            health = _get_repository_health(mock_repo)

            assert health["repository_structure"]["status"] == "healthy"
            assert health["git_configuration"]["status"] == "healthy"
            assert health["file_permissions"]["status"] == "healthy"

    @patch("spec_cli.cli.commands.status.Path")
    def test_get_repository_health_errors(self, mock_path: Mock) -> None:
        """Test _get_repository_health function with various errors."""
        from spec_cli.cli.commands.status import _get_repository_health

        mock_repo = MagicMock()

        # Mock missing directories
        mock_spec_dir = MagicMock()
        mock_spec_dir.exists.return_value = False
        mock_specs_dir = MagicMock()
        mock_specs_dir.exists.return_value = False

        def path_side_effect(path: str) -> Any:
            if path == ".spec":
                return mock_spec_dir
            elif path == ".specs":
                return mock_specs_dir
            else:
                return MagicMock()

        mock_path.side_effect = path_side_effect

        with patch("spec_cli.cli.commands.status._get_git_status_data") as mock_git:
            mock_git.side_effect = Exception("Git error")

            health = _get_repository_health(mock_repo)

            # When both dirs are missing, .specs missing overwrites to "warning"
            assert health["repository_structure"]["status"] == "warning"
            assert (
                ".spec directory missing" in health["repository_structure"]["details"]
            )
            assert health["git_configuration"]["status"] == "error"

    @patch("spec_cli.cli.commands.status.get_console")
    def test_display_git_status_with_files(self, mock_get_console: Mock) -> None:
        """Test _display_git_status function with files."""
        from spec_cli.cli.commands.status import _display_git_status

        mock_console = MagicMock()
        mock_get_console.return_value = mock_console

        git_status: Dict[str, List[str]] = {
            "staged": ["staged.md"],
            "modified": ["modified.md"],
            "untracked": ["untracked.md"],
        }

        _display_git_status(git_status)

        # Verify console.print was called for each section
        assert mock_console.print.call_count >= 3

    @patch("spec_cli.cli.commands.status.get_console")
    def test_display_git_status_clean(self, mock_get_console: Mock) -> None:
        """Test _display_git_status function with clean directory."""
        from spec_cli.cli.commands.status import _display_git_status

        mock_console = MagicMock()
        mock_get_console.return_value = mock_console

        git_status: Dict[str, List[str]] = {
            "staged": [],
            "modified": [],
            "untracked": [],
        }

        _display_git_status(git_status)

        # Should print clean message
        mock_console.print.assert_called_with(
            "\n[green]Working directory clean[/green]"
        )

    def test_display_processing_summary(self) -> None:
        """Test _display_processing_summary function."""
        from spec_cli.cli.commands.status import _display_processing_summary

        summary_info = {"test": "data"}

        with patch("spec_cli.ui.error_display.format_data") as mock_format:
            _display_processing_summary(summary_info)
            mock_format.assert_called_once_with(summary_info, "Processing Capabilities")
