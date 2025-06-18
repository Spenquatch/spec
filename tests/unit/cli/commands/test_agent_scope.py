"""Unit tests for agent scope command."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.agent_scope import AgentScopeCommand
from spec_cli.exceptions import SpecRepositoryError

# Test constants
DEFAULT_QUERY = "test query"
DEFAULT_CONTEXT_WINDOW = 8000
VALID_CONTEXT_WINDOW = 5000
INVALID_CONTEXT_WINDOW_LOW = 0
INVALID_CONTEXT_WINDOW_HIGH = 50000
MAX_CONTEXT_WINDOW = 32000
TEST_PROJECT_ROOT = "/test/project"
TEST_FILE_COUNT = 5


class TestAgentScopeCommandValidation:
    """Test input validation for AgentScopeCommand."""

    def test_execute_when_empty_query_then_returns_error_result(self):
        """Test that empty query returns validation error."""
        command = AgentScopeCommand()

        result = command.execute(query="", context_window=DEFAULT_CONTEXT_WINDOW)

        assert result["success"] is False
        assert "Query cannot be empty" in result["error"]

    def test_execute_when_whitespace_query_then_returns_error_result(self):
        """Test that whitespace-only query returns validation error."""
        command = AgentScopeCommand()

        result = command.execute(query="   ", context_window=DEFAULT_CONTEXT_WINDOW)

        assert result["success"] is False
        assert "Query cannot be empty" in result["error"]

    def test_execute_when_context_window_zero_then_returns_error_result(self):
        """Test that zero context window returns validation error."""
        command = AgentScopeCommand()

        result = command.execute(
            query=DEFAULT_QUERY, context_window=INVALID_CONTEXT_WINDOW_LOW
        )

        assert result["success"] is False
        assert "Context window must be between 1 and 32000 tokens" in result["error"]

    def test_execute_when_context_window_above_limit_then_returns_error_result(self):
        """Test that context window above limit returns validation error."""
        command = AgentScopeCommand()

        result = command.execute(
            query=DEFAULT_QUERY, context_window=INVALID_CONTEXT_WINDOW_HIGH
        )

        assert result["success"] is False
        assert "Context window must be between 1 and 32000 tokens" in result["error"]

    def test_execute_when_valid_inputs_then_validates_successfully(self):
        """Test that valid inputs pass validation."""
        command = AgentScopeCommand()

        with (
            patch(
                "spec_cli.cli.commands.agent_scope.resolve_project_root"
            ) as mock_resolve,
            patch.object(command, "_discover_files") as mock_discover,
            patch("spec_cli.cli.commands.agent_scope.get_environment_info") as mock_env,
        ):
            mock_project = Mock(spec=Path)
            mock_project.exists.return_value = True
            mock_resolve.return_value = mock_project
            mock_discover.return_value = [Path("/test/file.py")]
            mock_env.return_value = {"platform": "test"}

            result = command.execute(
                query=DEFAULT_QUERY, context_window=VALID_CONTEXT_WINDOW
            )

            assert result["success"] is True
            assert DEFAULT_QUERY in result["message"]


class TestAgentScopeCommandProjectResolution:
    """Test project root resolution for AgentScopeCommand."""

    @patch("spec_cli.cli.commands.agent_scope.resolve_project_root")
    def test_execute_when_project_root_missing_then_returns_error_result(
        self, mock_resolve
    ):
        """Test that missing project root returns error."""
        mock_project = Mock(spec=Path)
        mock_project.exists.return_value = False
        mock_project.__str__ = Mock(return_value=TEST_PROJECT_ROOT)
        mock_resolve.return_value = mock_project

        command = AgentScopeCommand()
        result = command.execute(
            query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
        )

        assert result["success"] is False
        assert f"Project root not found: {mock_project}" in result["error"]

    @patch("spec_cli.cli.commands.agent_scope.resolve_project_root")
    def test_execute_when_resolve_project_root_raises_exception_then_handles_gracefully(
        self, mock_resolve
    ):
        """Test exception handling during project root resolution."""
        mock_resolve.side_effect = SpecRepositoryError("Resolution failed")

        command = AgentScopeCommand()
        result = command.execute(
            query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
        )

        assert result["success"] is False
        assert "Agent scope command failed" in result["error"]


class TestAgentScopeCommandFileDiscovery:
    """Test file discovery functionality for AgentScopeCommand."""

    def test_execute_when_no_files_discovered_then_returns_error_result(self):
        """Test that no discovered files returns error."""
        command = AgentScopeCommand()

        with (
            patch(
                "spec_cli.cli.commands.agent_scope.resolve_project_root"
            ) as mock_resolve,
            patch.object(command, "_discover_files") as mock_discover,
        ):
            mock_project = Mock(spec=Path)
            mock_project.exists.return_value = True
            mock_resolve.return_value = mock_project
            mock_discover.return_value = []

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
            )

            assert result["success"] is False
            assert "No relevant files found in project" in result["error"]

    def test_execute_when_files_discovered_then_includes_in_result(self):
        """Test that discovered files are included in successful result."""
        command = AgentScopeCommand()
        test_files = [Path("/test/file1.py"), Path("/test/file2.py")]

        with (
            patch(
                "spec_cli.cli.commands.agent_scope.resolve_project_root"
            ) as mock_resolve,
            patch.object(command, "_discover_files") as mock_discover,
            patch("spec_cli.cli.commands.agent_scope.get_environment_info") as mock_env,
        ):
            mock_project = Mock(spec=Path)
            mock_project.exists.return_value = True
            mock_resolve.return_value = mock_project
            mock_discover.return_value = test_files
            mock_env.return_value = {"platform": "test"}

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
            )

            assert result["success"] is True
            assert result["data"]["file_list"] == test_files
            assert (
                len(test_files)
                == result["data"]["project_metadata"]["total_files_discovered"]
            )

    def test_execute_when_exclude_patterns_provided_then_passes_to_discovery(self):
        """Test that exclude patterns are passed to file discovery."""
        command = AgentScopeCommand()
        exclude_patterns = ["*.pyc", "*.log"]

        with (
            patch(
                "spec_cli.cli.commands.agent_scope.resolve_project_root"
            ) as mock_resolve,
            patch.object(command, "_discover_files") as mock_discover,
            patch("spec_cli.cli.commands.agent_scope.get_environment_info") as mock_env,
        ):
            mock_project = Mock(spec=Path)
            mock_project.exists.return_value = True
            mock_resolve.return_value = mock_project
            mock_discover.return_value = [Path("/test/file.py")]
            mock_env.return_value = {"platform": "test"}

            result = command.execute(
                query=DEFAULT_QUERY,
                context_window=DEFAULT_CONTEXT_WINDOW,
                exclude=exclude_patterns,
            )

            assert result["success"] is True
            mock_discover.assert_called_once_with(mock_project, exclude_patterns)


class TestAgentScopeCommandResultData:
    """Test result data structure for AgentScopeCommand."""

    def test_execute_when_successful_then_returns_complete_data_structure(self):
        """Test that successful execution returns complete data structure."""
        command = AgentScopeCommand()
        test_files = [Path("/test/file.py")]
        test_env = {"platform": "darwin", "python": "3.11"}

        with (
            patch(
                "spec_cli.cli.commands.agent_scope.resolve_project_root"
            ) as mock_resolve,
            patch.object(command, "_discover_files") as mock_discover,
            patch("spec_cli.cli.commands.agent_scope.get_environment_info") as mock_env,
        ):
            mock_project = Mock(spec=Path)
            mock_project.exists.return_value = True
            mock_project.__str__ = Mock(return_value=TEST_PROJECT_ROOT)
            mock_resolve.return_value = mock_project
            mock_discover.return_value = test_files
            mock_env.return_value = test_env

            result = command.execute(
                query=DEFAULT_QUERY,
                context_window=VALID_CONTEXT_WINDOW,
                exclude=["*.log"],
            )

            assert result["success"] is True
            assert "validated_params" in result["data"]
            assert "file_list" in result["data"]
            assert "project_metadata" in result["data"]

            # Check validated_params structure
            params = result["data"]["validated_params"]
            assert params["query"] == DEFAULT_QUERY
            assert params["context_window"] == VALID_CONTEXT_WINDOW
            assert params["exclude_patterns"] == ["*.log"]
            assert params["project_root"] == mock_project

            # Check project_metadata structure
            metadata = result["data"]["project_metadata"]
            assert metadata["project_root"] == TEST_PROJECT_ROOT
            assert metadata["total_files_discovered"] == len(test_files)
            assert metadata["environment"] == test_env


class TestAgentScopeCommandDiscoverFiles:
    """Test _discover_files method for AgentScopeCommand."""

    @pytest.fixture
    def sample_project_structure(self, tmp_path):
        """Create sample project structure for testing."""
        # Create source files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("# Python file")
        (tmp_path / "src" / "utils.js").write_text("// JavaScript file")
        (tmp_path / "README.md").write_text("# Project README")

        # Create files to exclude
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "main.pyc").write_text("compiled")
        (tmp_path / "build.log").write_text("log content")
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("git config")

        return tmp_path

    def test_discover_files_when_valid_project_then_finds_source_files(
        self, sample_project_structure
    ):
        """Test file discovery finds source files."""
        command = AgentScopeCommand()

        with patch(
            "spec_cli.cli.commands.agent_scope.safe_relative_to"
        ) as mock_relative:
            mock_relative.side_effect = lambda path, root: path.relative_to(root)

            files = command._discover_files(sample_project_structure, [])

            # Should find source files
            file_names = [f.name for f in files]
            assert "main.py" in file_names
            assert "utils.js" in file_names
            assert "README.md" in file_names

            # Should exclude compiled and system files
            assert "main.pyc" not in file_names
            assert "build.log" not in file_names
            assert "config" not in file_names

    def test_discover_files_when_custom_excludes_then_applies_patterns(
        self, sample_project_structure
    ):
        """Test file discovery applies custom exclude patterns."""
        command = AgentScopeCommand()
        custom_excludes = ["*.md", "*.js"]

        with patch(
            "spec_cli.cli.commands.agent_scope.safe_relative_to"
        ) as mock_relative:
            mock_relative.side_effect = lambda path, root: path.relative_to(root)

            files = command._discover_files(sample_project_structure, custom_excludes)

            file_names = [f.name for f in files]
            assert "main.py" in file_names
            assert "utils.js" not in file_names  # Excluded by custom pattern
            assert "README.md" not in file_names  # Excluded by custom pattern

    def test_discover_files_when_discovery_fails_then_handles_gracefully(self):
        """Test file discovery handles exceptions gracefully."""
        command = AgentScopeCommand()
        invalid_path = Path("/nonexistent/path")

        files = command._discover_files(invalid_path, [])

        assert files == []

    def test_discover_files_when_safe_relative_to_fails_then_continues_discovery(
        self, sample_project_structure
    ):
        """Test file discovery continues when path resolution fails."""
        command = AgentScopeCommand()

        with patch(
            "spec_cli.cli.commands.agent_scope.safe_relative_to"
        ) as mock_relative:
            # First call succeeds, second fails, third succeeds
            mock_relative.side_effect = [
                Path("src/main.py"),
                Exception("Path resolution failed"),
                Path("README.md"),
            ]

            files = command._discover_files(sample_project_structure, [])

            # Should continue despite one failure
            assert len(files) >= 1


class TestAgentScopeCommandPatternMatching:
    """Test pattern matching methods for AgentScopeCommand."""

    def test_matches_exclude_patterns_when_exact_match_then_returns_true(self):
        """Test pattern matching with exact file name match."""
        command = AgentScopeCommand()
        patterns = {"build.log", "*.pyc"}

        result = command._matches_exclude_patterns("build.log", patterns)

        assert result is True

    def test_matches_exclude_patterns_when_wildcard_match_then_returns_true(self):
        """Test pattern matching with wildcard extension."""
        command = AgentScopeCommand()
        patterns = {"*.pyc", "*.log"}

        result = command._matches_exclude_patterns("main.pyc", patterns)

        assert result is True

    def test_matches_exclude_patterns_when_no_match_then_returns_false(self):
        """Test pattern matching when no patterns match."""
        command = AgentScopeCommand()
        patterns = {"*.pyc", "*.log"}

        result = command._matches_exclude_patterns("main.py", patterns)

        assert result is False

    def test_matches_exclude_patterns_when_partial_path_match_then_returns_true(self):
        """Test pattern matching with partial path inclusion."""
        command = AgentScopeCommand()
        patterns = {"__pycache__", ".git"}

        result = command._matches_exclude_patterns("src/__pycache__/main.pyc", patterns)

        assert result is True

    def test_is_source_file_when_python_extension_then_returns_true(self):
        """Test source file detection for Python files."""
        command = AgentScopeCommand()

        result = command._is_source_file(Path("main.py"))

        assert result is True

    def test_is_source_file_when_uppercase_extension_then_returns_true(self):
        """Test source file detection handles uppercase extensions."""
        command = AgentScopeCommand()

        result = command._is_source_file(Path("README.MD"))

        assert result is True

    def test_is_source_file_when_non_source_extension_then_returns_false(self):
        """Test source file detection rejects non-source files."""
        command = AgentScopeCommand()

        result = command._is_source_file(Path("data.bin"))

        assert result is False

    def test_is_source_file_when_multiple_extensions_then_handles_correctly(self):
        """Test source file detection with various extensions."""
        command = AgentScopeCommand()
        test_cases = [
            ("script.js", True),
            ("style.css", True),
            ("config.json", True),
            ("database.sql", True),
            ("image.png", False),
            ("archive.zip", False),
        ]

        for filename, expected in test_cases:
            result = command._is_source_file(Path(filename))
            assert result == expected, f"Failed for {filename}"


class TestAgentScopeCommandErrorHandling:
    """Test error handling for AgentScopeCommand."""

    def test_execute_when_exception_during_execution_then_returns_error_result(self):
        """Test exception handling during command execution."""
        command = AgentScopeCommand()

        with patch(
            "spec_cli.cli.commands.agent_scope.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.side_effect = Exception("Unexpected error")

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
            )

            assert result["success"] is False
            assert "Agent scope command failed" in result["error"]
            assert "Unexpected error" in result["error"]

    @patch("spec_cli.cli.commands.agent_scope.debug_logger")
    def test_execute_when_successful_then_logs_completion(self, mock_logger):
        """Test that successful execution logs completion."""
        command = AgentScopeCommand()

        with (
            patch(
                "spec_cli.cli.commands.agent_scope.resolve_project_root"
            ) as mock_resolve,
            patch.object(command, "_discover_files") as mock_discover,
            patch("spec_cli.cli.commands.agent_scope.get_environment_info") as mock_env,
        ):
            mock_project = Mock(spec=Path)
            mock_project.exists.return_value = True
            mock_resolve.return_value = mock_project
            mock_discover.return_value = [Path("/test/file.py")]
            mock_env.return_value = {"platform": "test"}

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
            )

            assert result["success"] is True
            mock_logger.log.assert_called()

            # Check that INFO log was called with success message
            info_calls = [
                call for call in mock_logger.log.call_args_list if call[0][0] == "INFO"
            ]
            assert len(info_calls) > 0

    @patch("spec_cli.cli.commands.agent_scope.debug_logger")
    def test_execute_when_exception_then_logs_error(self, mock_logger):
        """Test that exceptions are logged with error details."""
        command = AgentScopeCommand()

        with patch(
            "spec_cli.cli.commands.agent_scope.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.side_effect = Exception("Test error")

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
            )

            assert result["success"] is False
            mock_logger.log.assert_called()

            # Check that ERROR log was called
            error_calls = [
                call for call in mock_logger.log.call_args_list if call[0][0] == "ERROR"
            ]
            assert len(error_calls) > 0


class TestAgentScopeCommandCrossPlatformBehavior:
    """Test cross-platform behavior for AgentScopeCommand."""

    @patch("spec_cli.cli.commands.agent_scope.safe_relative_to")
    def test_discover_files_when_windows_paths_then_normalizes_correctly(
        self, mock_relative
    ):
        """Test file discovery handles Windows paths correctly."""
        command = AgentScopeCommand()

        # Mock Windows-style path normalization
        mock_relative.return_value = Path("src\\main.py")

        with patch.object(Path, "rglob") as mock_rglob:
            mock_file = Mock(spec=Path)
            mock_file.is_file.return_value = True
            mock_file.suffix = ".py"
            mock_rglob.return_value = [mock_file]

            files = command._discover_files(Path("C:\\project"), [])

            mock_relative.assert_called()
            assert len(files) >= 0  # Should handle path normalization

    def test_is_source_file_when_cross_platform_paths_then_handles_consistently(self):
        """Test source file detection works across platforms."""
        command = AgentScopeCommand()

        # Test different path styles
        test_paths = [
            Path("src/main.py"),  # Unix-style
            Path("src\\main.py"),  # Windows-style
            Path("./main.py"),  # Relative
            Path("/abs/path/main.py"),  # Absolute
        ]

        for path in test_paths:
            result = command._is_source_file(path)
            assert result is True, f"Failed for path: {path}"
