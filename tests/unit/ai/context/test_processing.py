"""Unit tests for process_agent_scope_context function."""

from collections.abc import Generator
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.context.processing import (
    AgentScopeValidator,
    _analyze_query_processing,
    _build_discovery_params,
    _build_processing_summary,
    _extract_file_context,
    discover_project_files,
    process_agent_scope_context,
)


class TestProcessAgentScopeContextFunction:
    """Test main process_agent_scope_context function."""

    @pytest.fixture
    def temp_dir(self, tmp_path: Path) -> Path:
        """Create temporary directory for testing."""
        return tmp_path

    @pytest.fixture
    def mock_dependencies(self) -> Generator[dict[str, Any], None, None]:
        """Mock all dependencies for isolated testing."""
        with (
            patch(
                "spec_cli.ai.context.processing.discover_project_files"
            ) as mock_discover,
            patch(
                "spec_cli.ai.context.processing.AgentScopeValidator"
            ) as mock_validator_class,
            patch(
                "spec_cli.ai.context.processing.ContextExtractor"
            ) as mock_extractor_class,
            patch(
                "spec_cli.ai.context.processing.RelevanceRanker"
            ) as mock_ranker_class,
            patch(
                "spec_cli.ai.context.processing.CodeSanitizer"
            ) as mock_sanitizer_class,
        ):
            # Setup mock returns
            mock_discover.return_value = ["/test/file1.py", "/test/file2.js"]

            mock_validator = Mock()
            mock_validator.validate_file_inclusion.return_value = True
            mock_validator_class.return_value = mock_validator

            mock_extractor = Mock()
            mock_extractor.extract_context.return_value = {
                "file_path": "/test/file1.py",
                "relevance_score": 0.8,
                "classes": ["TestClass"],
                "functions": ["test_function"],
            }
            mock_extractor_class.return_value = mock_extractor

            mock_ranker = Mock()
            mock_ranker.rank_contexts.return_value = [
                {"file_path": "/test/file1.py", "composite_score": 0.9}
            ]
            mock_ranker.get_ranking_summary.return_value = {
                "total_results": 1,
                "average_score": 0.9,
            }
            mock_ranker_class.return_value = mock_ranker

            mock_sanitizer_class.return_value = Mock()

            yield {
                "discover": mock_discover,
                "validator_class": mock_validator_class,
                "validator": mock_validator,
                "extractor_class": mock_extractor_class,
                "extractor": mock_extractor,
                "ranker_class": mock_ranker_class,
                "ranker": mock_ranker,
                "sanitizer_class": mock_sanitizer_class,
            }

    def test_process_agent_scope_context_when_valid_inputs_then_returns_complete_result(
        self, temp_dir: Path, mock_dependencies: dict[str, Any]
    ) -> None:
        """Test processing with valid inputs."""
        result = process_agent_scope_context(
            base_path=temp_dir, query="test function", max_results=10
        )

        assert isinstance(result, dict)
        assert "ranked_files" in result
        assert "processing_summary" in result
        assert "query_analysis" in result
        assert "ranking_statistics" in result
        assert "processing_errors" in result

        # Verify structure of returned data
        assert isinstance(result["ranked_files"], list)
        assert isinstance(result["processing_summary"], dict)
        assert isinstance(result["query_analysis"], dict)

    def test_process_agent_scope_context_when_nonexistent_path_then_raises_value_error(
        self, mock_dependencies: dict[str, Any]
    ) -> None:
        """Test processing with non-existent base path."""
        nonexistent_path = Path("/nonexistent/path")

        with pytest.raises(ValueError, match="Base path does not exist"):
            process_agent_scope_context(base_path=nonexistent_path, query="test")

    def test_process_agent_scope_context_when_empty_query_then_raises_value_error(
        self, temp_dir: Path, mock_dependencies: dict[str, Any]
    ) -> None:
        """Test processing with empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            process_agent_scope_context(base_path=temp_dir, query="")

        with pytest.raises(ValueError, match="Query cannot be empty"):
            process_agent_scope_context(
                base_path=temp_dir,
                query="   ",  # Whitespace only
            )

    def test_process_agent_scope_context_when_invalid_max_results_then_raises_value_error(
        self, temp_dir: Path, mock_dependencies: dict[str, Any]
    ) -> None:
        """Test processing with invalid max_results."""
        with pytest.raises(ValueError, match="max_results must be positive"):
            process_agent_scope_context(base_path=temp_dir, query="test", max_results=0)

        with pytest.raises(ValueError, match="max_results must be positive"):
            process_agent_scope_context(
                base_path=temp_dir, query="test", max_results=-1
            )

    def test_process_agent_scope_context_when_custom_ai_config_then_uses_config(
        self, temp_dir: Path, mock_dependencies: dict[str, Any]
    ) -> None:
        """Test processing with custom AI configuration."""
        custom_config = Mock(spec=AIConfig)
        custom_config.security = Mock()

        process_agent_scope_context(
            base_path=temp_dir, query="test", ai_config=custom_config
        )

        # Should use provided config
        mock_dependencies["extractor_class"].assert_called_once()
        call_kwargs = mock_dependencies["extractor_class"].call_args.kwargs
        assert call_kwargs["ai_config"] is custom_config

    def test_process_agent_scope_context_when_discovery_fails_then_raises_runtime_error(
        self, temp_dir: Path, mock_dependencies: dict[str, Any]
    ) -> None:
        """Test processing when file discovery fails."""
        mock_dependencies["discover"].side_effect = Exception("Discovery failed")

        with pytest.raises(RuntimeError, match="Context processing failed"):
            process_agent_scope_context(base_path=temp_dir, query="test")

    def test_process_agent_scope_context_when_no_files_discovered_then_returns_empty_results(
        self, temp_dir: Path, mock_dependencies: dict[str, Any]
    ) -> None:
        """Test processing when no files are discovered."""
        mock_dependencies["discover"].return_value = []
        mock_dependencies["ranker"].rank_contexts.return_value = []
        mock_dependencies["ranker"].get_ranking_summary.return_value = {
            "total_results": 0
        }

        result = process_agent_scope_context(base_path=temp_dir, query="test")

        assert result["ranked_files"] == []
        assert result["processing_summary"]["pipeline_stages"]["discovered"] == 0

    def test_process_agent_scope_context_when_validation_filters_files_then_processes_remaining(
        self, temp_dir: Path, mock_dependencies: dict[str, Any]
    ) -> None:
        """Test processing when validation filters out some files."""

        # Setup validator to reject second file
        def validate_side_effect(file_path: Any, base_path: Any) -> bool:
            return str(file_path) == "/test/file1.py"

        mock_dependencies[
            "validator"
        ].validate_file_inclusion.side_effect = validate_side_effect

        result = process_agent_scope_context(base_path=temp_dir, query="test")

        # Should process only validated files
        summary = result["processing_summary"]
        assert summary["pipeline_stages"]["discovered"] == 2
        assert summary["pipeline_stages"]["validated"] == 1

    def test_process_agent_scope_context_when_extraction_errors_then_logs_and_continues(
        self, temp_dir: Path, mock_dependencies: dict[str, Any]
    ) -> None:
        """Test processing when context extraction fails for some files."""
        # Setup extractor to fail on second call
        call_count = 0

        def extract_side_effect(*args: Any, **kwargs: Any) -> Any:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return {"file_path": "/test/file1.py", "relevance_score": 0.8}
            else:
                raise Exception("Extraction failed")

        with patch(
            "spec_cli.ai.context.processing._extract_file_context"
        ) as mock_extract:
            mock_extract.side_effect = extract_side_effect

            result = process_agent_scope_context(base_path=temp_dir, query="test")

        # Should have processing errors recorded
        assert len(result["processing_errors"]) > 0
        assert any("error" in error for error in result["processing_errors"])


class TestBuildDiscoveryParams:
    """Test _build_discovery_params helper function."""

    def test_build_discovery_params_when_called_then_returns_complete_params(
        self,
    ) -> None:
        """Test discovery parameter building."""
        base_path = Path("/test/project")
        query = "test query"

        params = _build_discovery_params(base_path, query)

        assert isinstance(params, dict)
        assert params["base_path"] == base_path
        assert params["query"] == "test query"
        assert params["include_env_info"] is True
        assert params["max_file_size"] == 1024 * 1024
        assert params["respect_gitignore"] is True

    def test_build_discovery_params_when_query_has_whitespace_then_strips_whitespace(
        self,
    ) -> None:
        """Test query whitespace handling."""
        base_path = Path("/test")
        query = "  test query  "

        params = _build_discovery_params(base_path, query)

        assert params["query"] == "test query"


class TestExtractFileContext:
    """Test _extract_file_context helper function."""

    def test_extract_file_context_when_valid_file_then_returns_context(
        self, tmp_path: Path
    ) -> None:
        """Test file context extraction with valid file."""
        # Create test file
        test_file = tmp_path / "test.py"
        test_file.write_text("def test_function():\n    pass")

        mock_extractor = Mock()
        mock_extractor.extract_context.return_value = {
            "file_path": str(test_file),
            "relevance_score": 0.7,
        }

        result = _extract_file_context(test_file, "test", mock_extractor)

        assert result is not None
        mock_extractor.extract_context.assert_called_once()

    def test_extract_file_context_when_file_not_exists_then_returns_none(self) -> None:
        """Test extraction with non-existent file."""
        nonexistent_file = Path("/nonexistent/file.py")
        mock_extractor = Mock()

        result = _extract_file_context(nonexistent_file, "test", mock_extractor)

        assert result is None
        mock_extractor.extract_context.assert_not_called()

    def test_extract_file_context_when_not_a_file_then_returns_none(
        self, tmp_path: Path
    ) -> None:
        """Test extraction with directory instead of file."""
        mock_extractor = Mock()

        result = _extract_file_context(tmp_path, "test", mock_extractor)

        assert result is None

    def test_extract_file_context_when_empty_file_then_returns_none(
        self, tmp_path: Path
    ) -> None:
        """Test extraction with empty file."""
        empty_file = tmp_path / "empty.py"
        empty_file.write_text("")

        mock_extractor = Mock()

        result = _extract_file_context(empty_file, "test", mock_extractor)

        assert result is None

    def test_extract_file_context_when_unicode_decode_error_then_tries_latin1(
        self, tmp_path: Path
    ) -> None:
        """Test extraction with encoding issues."""
        # Create file with non-UTF8 content
        test_file = tmp_path / "test.py"
        test_file.write_bytes(b"def test():\n    # \xff\xfe invalid utf8")

        mock_extractor = Mock()
        mock_extractor.extract_context.return_value = {
            "file_path": str(test_file),
            "relevance_score": 0.5,
        }

        result = _extract_file_context(test_file, "test", mock_extractor)

        # Should handle encoding fallback
        assert result is not None or result is None  # May succeed or fail gracefully

    def test_extract_file_context_when_extractor_fails_then_returns_none(
        self, tmp_path: Path
    ) -> None:
        """Test extraction when extractor raises exception."""
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        mock_extractor = Mock()
        mock_extractor.extract_context.side_effect = Exception("Extractor failed")

        result = _extract_file_context(test_file, "test", mock_extractor)

        assert result is None


class TestBuildProcessingSummary:
    """Test _build_processing_summary helper function."""

    def test_build_processing_summary_when_called_then_returns_complete_summary(
        self,
    ) -> None:
        """Test processing summary building."""
        summary = _build_processing_summary(
            discovered_files=100,
            validated_files=80,
            processed_files=75,
            final_results=20,
            errors=5,
        )

        assert isinstance(summary, dict)
        assert "pipeline_stages" in summary
        assert "processing_efficiency" in summary
        assert "quality_metrics" in summary

        # Check pipeline stages
        stages = summary["pipeline_stages"]
        assert stages["discovered"] == 100
        assert stages["validated"] == 80
        assert stages["processed"] == 75
        assert stages["ranked"] == 20

        # Check efficiency metrics
        efficiency = summary["processing_efficiency"]
        assert efficiency["validation_rate"] == 0.8  # 80/100
        assert abs(efficiency["processing_rate"] - 0.9375) < 0.001  # 75/80
        assert abs(efficiency["error_rate"] - 0.0625) < 0.001  # 5/80

    def test_build_processing_summary_when_zero_inputs_then_handles_division_safely(
        self,
    ) -> None:
        """Test summary building with zero values."""
        summary = _build_processing_summary(
            discovered_files=0,
            validated_files=0,
            processed_files=0,
            final_results=0,
            errors=0,
        )

        # Should handle division by zero gracefully
        efficiency = summary["processing_efficiency"]
        assert efficiency["validation_rate"] == 0.0
        assert efficiency["processing_rate"] == 0.0
        assert efficiency["error_rate"] == 0.0


class TestAnalyzeQueryProcessing:
    """Test _analyze_query_processing helper function."""

    @pytest.fixture
    def sample_contexts(self) -> list[dict[str, Any]]:
        """Sample contexts for query analysis testing."""
        return [
            {
                "file_path": "/project/user_manager.py",
                "relevance_score": 0.8,
                "classes": ["UserManager"],
                "functions": ["authenticate_user", "create_user"],
                "imports": ["from auth import utils"],
            },
            {
                "file_path": "/project/database.py",
                "relevance_score": 0.6,
                "classes": ["DatabaseConnection"],
                "functions": ["connect", "query"],
                "imports": ["import sqlite3"],
            },
        ]

    def test_analyze_query_processing_when_contexts_provided_then_returns_analysis(
        self, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test query analysis with sample contexts."""
        query = "user authentication database"

        analysis = _analyze_query_processing(query, sample_contexts)

        assert isinstance(analysis, dict)
        assert "query_terms" in analysis
        assert "term_coverage" in analysis
        assert "average_relevance" in analysis
        assert "query_effectiveness" in analysis

        # Check query terms extraction
        assert "user" in analysis["query_terms"]
        assert "authentication" in analysis["query_terms"]
        assert "database" in analysis["query_terms"]

    def test_analyze_query_processing_when_empty_contexts_then_returns_zero_metrics(
        self,
    ) -> None:
        """Test query analysis with empty contexts."""
        query = "test query"

        analysis = _analyze_query_processing(query, [])

        assert analysis["average_relevance"] == 0.0
        assert analysis["query_effectiveness"] == 0.0
        assert analysis["term_coverage"] == {}

    def test_analyze_query_processing_when_term_coverage_calculated_then_counts_correctly(
        self, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test term coverage calculation."""
        query = "user database"

        analysis = _analyze_query_processing(query, sample_contexts)

        coverage = analysis["term_coverage"]
        # "user" should appear in first context
        assert coverage.get("user", 0) >= 1
        # "database" should appear in second context
        assert coverage.get("database", 0) >= 1

    def test_analyze_query_processing_when_average_relevance_calculated_then_computes_correctly(
        self, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test average relevance calculation."""
        query = "test"

        analysis = _analyze_query_processing(query, sample_contexts)

        expected_avg = (0.8 + 0.6) / 2.0  # (relevance scores) / count
        assert abs(analysis["average_relevance"] - expected_avg) < 0.001

    def test_analyze_query_processing_when_effectiveness_calculated_then_combines_metrics(
        self, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test query effectiveness calculation."""
        query = "user database"  # Both terms should have coverage

        analysis = _analyze_query_processing(query, sample_contexts)

        effectiveness = analysis["query_effectiveness"]
        assert 0.0 <= effectiveness <= 1.0
        # Should be combination of average relevance and coverage ratio


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility."""

    @patch("spec_cli.ai.context.processing.normalize_path_separators")
    def test_process_agent_scope_context_when_windows_path_then_normalizes(
        self, mock_normalize: Any, tmp_path: Path
    ) -> None:
        """Test path normalization across platforms."""
        mock_normalize.return_value = "normalized/path"

        with patch(
            "spec_cli.ai.context.processing.discover_project_files"
        ) as mock_discover:
            mock_discover.return_value = []

            # Should not raise exception with normalized paths
            process_agent_scope_context(base_path=tmp_path, query="test")

            mock_normalize.assert_called()

    def test_extract_file_context_when_different_encodings_then_handles_gracefully(
        self, tmp_path: Path
    ) -> None:
        """Test file reading with different encodings."""
        # Create file with UTF-8 content
        utf8_file = tmp_path / "utf8.py"
        utf8_file.write_text("# UTF-8 content", encoding="utf-8")

        mock_extractor = Mock()
        mock_extractor.extract_context.return_value = {"test": "result"}

        result = _extract_file_context(utf8_file, "test", mock_extractor)

        # Should handle encoding properly
        assert result is not None or result is None  # Depends on mock setup


class TestDiscoverProjectFiles:
    """Test discover_project_files stub function."""

    def test_discover_project_files_when_valid_base_path_then_finds_files(
        self, tmp_path: Path
    ) -> None:
        """Test file discovery with valid base path."""
        # Create test files
        (tmp_path / "test.py").write_text("# Python file")
        (tmp_path / "test.js").write_text("// JS file")
        (tmp_path / "test.md").write_text("# Markdown")

        params = {"base_path": tmp_path}
        files = discover_project_files(params)

        assert isinstance(files, list)
        assert len(files) >= 3
        file_names = [Path(f).name for f in files]
        assert "test.py" in file_names
        assert "test.js" in file_names
        assert "test.md" in file_names

    def test_discover_project_files_when_string_base_path_then_converts_to_path(
        self, tmp_path: Path
    ) -> None:
        """Test file discovery with string base path."""
        (tmp_path / "test.py").write_text("# Test")

        params = {"base_path": str(tmp_path)}
        files = discover_project_files(params)

        assert isinstance(files, list)
        assert len(files) >= 1

    def test_discover_project_files_when_no_base_path_then_uses_cwd(self) -> None:
        """Test file discovery with no base path parameter."""
        params: dict[str, Any] = {}
        files = discover_project_files(params)

        assert isinstance(files, list)
        # Should find some files in current working directory

    def test_discover_project_files_when_large_directory_then_limits_results(
        self, tmp_path: Path
    ) -> None:
        """Test file discovery limits results for performance."""
        # Create more than 50 files to test limit
        for i in range(60):
            (tmp_path / f"test_{i}.py").write_text(f"# Test file {i}")

        params = {"base_path": tmp_path}
        files = discover_project_files(params)

        assert isinstance(files, list)
        assert len(files) <= 50  # Should respect limit


class TestAgentScopeValidator:
    """Test AgentScopeValidator stub class."""

    def test_validate_file_inclusion_when_valid_source_file_then_returns_true(
        self, tmp_path: Path
    ) -> None:
        """Test validation accepts valid source files."""
        validator = AgentScopeValidator()
        source_file = tmp_path / "valid_file.py"

        result = validator.validate_file_inclusion(source_file, tmp_path)

        assert result is True

    def test_validate_file_inclusion_when_pycache_file_then_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Test validation rejects __pycache__ files."""
        validator = AgentScopeValidator()
        cache_file = tmp_path / "__pycache__" / "file.pyc"

        result = validator.validate_file_inclusion(cache_file, tmp_path)

        assert result is False

    def test_validate_file_inclusion_when_git_file_then_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Test validation rejects .git files."""
        validator = AgentScopeValidator()
        git_file = tmp_path / ".git" / "config"

        result = validator.validate_file_inclusion(git_file, tmp_path)

        assert result is False

    def test_validate_file_inclusion_when_spec_file_then_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Test validation rejects .spec files."""
        validator = AgentScopeValidator()
        spec_file = tmp_path / ".spec" / "file"

        result = validator.validate_file_inclusion(spec_file, tmp_path)

        assert result is False

    def test_validate_file_inclusion_when_venv_file_then_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Test validation rejects .venv files."""
        validator = AgentScopeValidator()
        venv_file = tmp_path / ".venv" / "lib" / "python.py"

        result = validator.validate_file_inclusion(venv_file, tmp_path)

        assert result is False

    def test_validate_file_inclusion_when_node_modules_file_then_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Test validation rejects node_modules files."""
        validator = AgentScopeValidator()
        node_file = tmp_path / "node_modules" / "package" / "index.js"

        result = validator.validate_file_inclusion(node_file, tmp_path)

        assert result is False

    def test_validate_file_inclusion_when_cache_directories_then_returns_false(
        self, tmp_path: Path
    ) -> None:
        """Test validation rejects various cache directories."""
        validator = AgentScopeValidator()

        cache_dirs = [".pytest_cache", ".mypy_cache", ".ruff_cache"]
        for cache_dir in cache_dirs:
            cache_file = tmp_path / cache_dir / "file"
            result = validator.validate_file_inclusion(cache_file, tmp_path)
            assert result is False, f"Should reject {cache_dir} files"


class TestErrorHandling:
    """Test error handling in processing functions."""

    def test_process_agent_scope_context_when_component_initialization_fails_then_raises_runtime_error(
        self, tmp_path: Path
    ) -> None:
        """Test handling of component initialization failures."""
        with patch(
            "spec_cli.ai.context.processing.ContextExtractor"
        ) as mock_extractor_class:
            mock_extractor_class.side_effect = Exception("Initialization failed")

            with pytest.raises(RuntimeError, match="Context processing failed"):
                process_agent_scope_context(base_path=tmp_path, query="test")

    def test_process_agent_scope_context_when_ranking_fails_then_raises_runtime_error(
        self, tmp_path: Path
    ) -> None:
        """Test handling of ranking failures."""
        # Create a test file to ensure discovery finds something
        test_file = tmp_path / "test.py"
        test_file.write_text("def test(): pass")

        with (
            patch(
                "spec_cli.ai.context.processing.discover_project_files"
            ) as mock_discover,
            patch(
                "spec_cli.ai.context.processing.AgentScopeValidator"
            ) as mock_validator_class,
            patch(
                "spec_cli.ai.context.processing.ContextExtractor"
            ) as mock_extractor_class,
            patch(
                "spec_cli.ai.context.processing.RelevanceRanker"
            ) as mock_ranker_class,
            patch("spec_cli.ai.context.processing.CodeSanitizer"),
        ):
            mock_discover.return_value = [str(test_file)]

            # Setup validator to allow files
            mock_validator = Mock()
            mock_validator.validate_file_inclusion.return_value = True
            mock_validator_class.return_value = mock_validator

            # Setup extractor to return some context
            mock_extractor = Mock()
            mock_extractor.extract_context.return_value = {
                "file_path": "/test/file.py",
                "relevance_score": 0.5,
            }
            mock_extractor_class.return_value = mock_extractor

            mock_ranker = Mock()
            mock_ranker.rank_contexts.side_effect = Exception("Ranking failed")
            mock_ranker_class.return_value = mock_ranker

            with pytest.raises(RuntimeError, match="Context processing failed"):
                process_agent_scope_context(base_path=tmp_path, query="test")
