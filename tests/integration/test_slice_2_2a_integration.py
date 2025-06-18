"""Integration tests for slice 2.2a - Agent Scope Command Core."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.cli.commands.agent_scope import AgentScopeCommand

# Test constants
DEFAULT_QUERY = "authentication module"
DEFAULT_CONTEXT_WINDOW = 8000
TEST_FILE_COUNT_MINIMUM = 3


class TestSlice22aAgentScopeIntegration:
    """Integration tests for agent scope command with file discovery."""

    @pytest.fixture
    def sample_project(self):
        """Create a temporary project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create realistic project structure
            (project_root / "src").mkdir()
            (project_root / "src" / "auth").mkdir()
            (project_root / "src" / "auth" / "__init__.py").write_text(
                '"""Authentication module."""\nfrom .login import authenticate\n'
            )
            (project_root / "src" / "auth" / "login.py").write_text(
                'def authenticate(username, password):\n    """Authenticate user."""\n    pass\n'
            )
            (project_root / "src" / "utils.py").write_text(
                'def helper_function():\n    """Helper utility."""\n    pass\n'
            )
            (project_root / "tests").mkdir()
            (project_root / "tests" / "test_auth.py").write_text(
                'def test_authenticate():\n    """Test authentication."""\n    pass\n'
            )
            (project_root / "README.md").write_text("# Project Documentation\n")
            (project_root / "pyproject.toml").write_text(
                '[tool.poetry]\nname = "test"\n'
            )

            # Create files that should be excluded
            (project_root / "__pycache__").mkdir()
            (project_root / "__pycache__" / "test.pyc").write_text("compiled")
            (project_root / ".git").mkdir()
            (project_root / ".git" / "config").write_text("git config")
            (project_root / "build.log").write_text("build output")

            yield project_root

    def test_integration_file_discovery_across_project_structures(self, sample_project):
        """Test file discovery works across different project structures."""
        command = AgentScopeCommand()

        with patch(
            "spec_cli.cli.commands.agent_scope.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = sample_project

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW, exclude=[]
            )

            assert result["success"] is True
            assert len(result["data"]["file_list"]) >= TEST_FILE_COUNT_MINIMUM

            # Verify expected files are discovered
            file_names = [f.name for f in result["data"]["file_list"]]
            assert "__init__.py" in file_names
            assert "login.py" in file_names
            assert "utils.py" in file_names
            assert "test_auth.py" in file_names
            assert "README.md" in file_names
            assert "pyproject.toml" in file_names

            # Verify excluded files are not discovered
            assert "test.pyc" not in file_names
            assert "config" not in file_names
            assert "build.log" not in file_names

    def test_integration_exclusion_patterns_work_correctly(self, sample_project):
        """Test that exclusion patterns effectively filter files."""
        command = AgentScopeCommand()
        exclude_patterns = ["*.md", "test_*", "pyproject.toml"]

        with patch(
            "spec_cli.cli.commands.agent_scope.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = sample_project

            result = command.execute(
                query=DEFAULT_QUERY,
                context_window=DEFAULT_CONTEXT_WINDOW,
                exclude=exclude_patterns,
            )

            assert result["success"] is True

            file_names = [f.name for f in result["data"]["file_list"]]

            # Should exclude files matching patterns
            assert "README.md" not in file_names
            assert "test_auth.py" not in file_names
            assert "pyproject.toml" not in file_names

            # Should still include non-matching files
            assert "__init__.py" in file_names
            assert "login.py" in file_names
            assert "utils.py" in file_names

    def test_integration_validated_params_structure_complete(self, sample_project):
        """Test that validated parameters contain all required fields."""
        command = AgentScopeCommand()
        test_exclude_patterns = ["*.log", "*.tmp"]

        with patch(
            "spec_cli.cli.commands.agent_scope.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = sample_project

            result = command.execute(
                query=DEFAULT_QUERY,
                context_window=DEFAULT_CONTEXT_WINDOW,
                exclude=test_exclude_patterns,
            )

            assert result["success"] is True

            validated_params = result["data"]["validated_params"]
            assert validated_params["query"] == DEFAULT_QUERY
            assert validated_params["context_window"] == DEFAULT_CONTEXT_WINDOW
            assert validated_params["exclude_patterns"] == test_exclude_patterns
            assert validated_params["project_root"] == sample_project

            project_metadata = result["data"]["project_metadata"]
            assert project_metadata["project_root"] == str(sample_project)
            assert project_metadata["total_files_discovered"] == len(
                result["data"]["file_list"]
            )
            assert "environment" in project_metadata

    def test_integration_handles_permission_errors_gracefully(self, sample_project):
        """Test that permission errors during file discovery are handled gracefully."""
        command = AgentScopeCommand()

        with (
            patch(
                "spec_cli.cli.commands.agent_scope.resolve_project_root"
            ) as mock_resolve,
            patch.object(Path, "rglob") as mock_rglob,
        ):
            mock_resolve.return_value = sample_project
            # Simulate permission error during file traversal
            mock_rglob.side_effect = PermissionError("Access denied")

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
            )

            # Should handle gracefully and return empty file list
            assert result["success"] is False
            assert "No relevant files found" in result["error"]

    def test_integration_performance_requirements_met(self, sample_project):
        """Test that file discovery completes within performance requirements."""
        import time

        command = AgentScopeCommand()

        with patch(
            "spec_cli.cli.commands.agent_scope.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = sample_project

            start_time = time.time()

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
            )

            end_time = time.time()
            execution_time = end_time - start_time

            assert result["success"] is True
            assert execution_time < 2.0  # Must complete within 2 seconds

    def test_integration_cross_platform_path_handling(self, sample_project):
        """Test that file discovery handles paths correctly across platforms."""
        command = AgentScopeCommand()

        with patch(
            "spec_cli.cli.commands.agent_scope.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = sample_project

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
            )

            assert result["success"] is True

            # Verify all file paths are Path objects and exist
            for file_path in result["data"]["file_list"]:
                assert isinstance(file_path, Path)
                assert file_path.exists()
                assert file_path.is_file()

    def test_integration_environment_info_included(self, sample_project):
        """Test that environment information is properly included."""
        command = AgentScopeCommand()

        with patch(
            "spec_cli.cli.commands.agent_scope.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = sample_project

            result = command.execute(
                query=DEFAULT_QUERY, context_window=DEFAULT_CONTEXT_WINDOW
            )

            assert result["success"] is True

            environment = result["data"]["project_metadata"]["environment"]
            assert isinstance(environment, dict)
            # Environment info should contain platform information
            assert len(environment) > 0

    def test_integration_query_whitespace_handling(self, sample_project):
        """Test that query whitespace is properly trimmed."""
        command = AgentScopeCommand()
        query_with_whitespace = "  test query with spaces  "

        with patch(
            "spec_cli.cli.commands.agent_scope.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = sample_project

            result = command.execute(
                query=query_with_whitespace, context_window=DEFAULT_CONTEXT_WINDOW
            )

            assert result["success"] is True
            assert (
                result["data"]["validated_params"]["query"]
                == query_with_whitespace.strip()
            )
            assert query_with_whitespace.strip() in result["message"]

    def test_integration_large_project_structure_handling(self):
        """Test handling of larger project structures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create larger project structure
            for i in range(10):
                module_dir = project_root / f"module_{i}"
                module_dir.mkdir()
                for j in range(5):
                    (module_dir / f"file_{j}.py").write_text(f"# Module {i} File {j}\n")

            # Add various file types
            (project_root / "config.json").write_text('{"key": "value"}')
            (project_root / "README.md").write_text("# Large Project")
            (project_root / "requirements.txt").write_text("dependency==1.0")

            command = AgentScopeCommand()

            with patch(
                "spec_cli.cli.commands.agent_scope.resolve_project_root"
            ) as mock_resolve:
                mock_resolve.return_value = project_root

                result = command.execute(
                    query="module configuration", context_window=DEFAULT_CONTEXT_WINDOW
                )

                assert result["success"] is True
                assert len(result["data"]["file_list"]) >= 50  # Should find many files

                # Verify expected file types are included
                file_extensions = {f.suffix for f in result["data"]["file_list"]}
                assert ".py" in file_extensions
                assert ".json" in file_extensions
                assert ".md" in file_extensions
                assert ".txt" in file_extensions
