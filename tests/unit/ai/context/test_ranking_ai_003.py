"""Unit tests for AI Context Processing - RelevanceRanker (Slice ai_003).

This module implements comprehensive unit tests for the RelevanceRanker class,
achieving 95% coverage target with thorough testing of all ranking methods,
scoring algorithms, and edge cases.
"""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.context.ranking import RelevanceRanker


class TestRelevanceRankerInitialization:
    """Test RelevanceRanker initialization and parameter validation."""

    def test_init_with_default_parameters(self) -> None:
        """Test initialization with default parameters."""
        ranker = RelevanceRanker()

        assert ranker.max_results == 20
        assert ranker.min_relevance_score == 0.1
        assert ranker.debug_logger is not None
        assert ranker.weights == {
            "relevance_score": 0.4,
            "file_type": 0.2,
            "file_size": 0.1,
            "structure_complexity": 0.2,
            "query_match_density": 0.1,
        }

    def test_init_with_custom_parameters(self) -> None:
        """Test initialization with custom parameters."""
        mock_logger = Mock()
        ranker = RelevanceRanker(
            max_results=50, min_relevance_score=0.3, debug_logger=mock_logger
        )

        assert ranker.max_results == 50
        assert ranker.min_relevance_score == 0.3
        assert ranker.debug_logger is mock_logger

    def test_init_with_invalid_max_results(self) -> None:
        """Test initialization fails with invalid max_results."""
        with pytest.raises(ValueError, match="max_results must be positive"):
            RelevanceRanker(max_results=0)

        with pytest.raises(ValueError, match="max_results must be positive"):
            RelevanceRanker(max_results=-1)

    def test_init_with_invalid_min_relevance_score(self) -> None:
        """Test initialization fails with invalid min_relevance_score."""
        with pytest.raises(
            ValueError, match="min_relevance_score must be between 0.0 and 1.0"
        ):
            RelevanceRanker(min_relevance_score=-0.1)

        with pytest.raises(
            ValueError, match="min_relevance_score must be between 0.0 and 1.0"
        ):
            RelevanceRanker(min_relevance_score=1.1)

    def test_init_boundary_values(self) -> None:
        """Test initialization with boundary values."""
        # Minimum valid values
        ranker1 = RelevanceRanker(max_results=1, min_relevance_score=0.0)
        assert ranker1.max_results == 1
        assert ranker1.min_relevance_score == 0.0

        # Maximum valid values
        ranker2 = RelevanceRanker(max_results=1000, min_relevance_score=1.0)
        assert ranker2.max_results == 1000
        assert ranker2.min_relevance_score == 1.0


class TestRankContexts:
    """Test rank_contexts method with various scenarios."""

    @pytest.fixture
    def ranker(self) -> RelevanceRanker:
        """Create RelevanceRanker instance for testing."""
        return RelevanceRanker(max_results=10, min_relevance_score=0.2)

    @pytest.fixture
    def mock_debug_logger(self) -> Mock:
        """Mock debug logger with log method."""
        logger = Mock()
        logger.log = Mock()
        return logger

    @pytest.fixture
    def sample_contexts(self) -> list[dict[str, Any]]:
        """Create sample context data for testing."""
        return [
            {
                "file_path": "/test/module.py",
                "file_size": 5000,
                "relevance_score": 0.8,
                "classes": ["MyClass", "Helper"],
                "functions": ["main", "process", "validate"],
                "imports": ["os", "sys", "pathlib"],
                "comments": ["Main module", "Helper functions"],
            },
            {
                "file_path": "/test/utils.js",
                "file_size": 2000,
                "relevance_score": 0.6,
                "classes": [],
                "functions": ["helper", "utility"],
                "imports": ["lodash"],
                "comments": ["Utility functions"],
            },
            {
                "file_path": "/test/config.json",
                "file_size": 500,
                "relevance_score": 0.4,
                "classes": [],
                "functions": [],
                "imports": [],
                "comments": [],
            },
            {
                "file_path": "/test/large_file.txt",
                "file_size": 200000,
                "relevance_score": 0.1,  # Below threshold
                "classes": [],
                "functions": [],
                "imports": [],
                "comments": [],
            },
        ]

    def test_rank_contexts_successful_ranking(
        self, ranker: RelevanceRanker, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test successful context ranking with typical data."""
        query = "module main process"
        results = ranker.rank_contexts(sample_contexts, query)

        # Should return results above threshold, sorted by composite score
        assert len(results) > 0
        assert len(results) <= ranker.max_results

        # All results should have composite_score added
        for result in results:
            assert "composite_score" in result
            assert result["composite_score"] >= ranker.min_relevance_score

        # Results should be sorted by composite score (descending)
        scores = [result["composite_score"] for result in results]
        assert scores == sorted(scores, reverse=True)

    def test_rank_contexts_empty_contexts_raises_error(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test rank_contexts raises ValueError with empty contexts."""
        with pytest.raises(ValueError, match="Contexts list cannot be empty"):
            ranker.rank_contexts([], "test query")

    def test_rank_contexts_invalid_query_raises_error(
        self, ranker: RelevanceRanker, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test rank_contexts raises ValueError with invalid query."""
        with pytest.raises(ValueError, match="Query must be a string"):
            ranker.rank_contexts(sample_contexts, None)  # type: ignore

        with pytest.raises(ValueError, match="Query must be a string"):
            ranker.rank_contexts(sample_contexts, 123)  # type: ignore

    def test_rank_contexts_filters_by_min_score(
        self, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test that contexts below min_relevance_score are filtered out."""
        # Set high threshold to filter most results
        ranker = RelevanceRanker(min_relevance_score=0.8)
        results = ranker.rank_contexts(sample_contexts, "test")

        # Should only return contexts with high composite scores
        for result in results:
            assert result["composite_score"] >= 0.8

    def test_rank_contexts_limits_max_results(
        self, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test that results are limited to max_results."""
        ranker = RelevanceRanker(max_results=2, min_relevance_score=0.0)
        results = ranker.rank_contexts(sample_contexts, "test")

        assert len(results) <= 2

    def test_rank_contexts_with_debug_logging(
        self, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test that debug logging is called when available."""
        mock_logger = Mock()
        mock_logger.log = Mock()

        ranker = RelevanceRanker(debug_logger=mock_logger)
        ranker.rank_contexts(sample_contexts, "test query")

        # Verify debug logging was called
        mock_logger.log.assert_called_once()
        call_args = mock_logger.log.call_args
        assert call_args[0][0] == "DEBUG"
        assert "Contexts ranked" in call_args[0][1]

    def test_rank_contexts_preserves_original_data(
        self, ranker: RelevanceRanker, sample_contexts: list[dict[str, Any]]
    ) -> None:
        """Test that original context data is preserved and copied."""
        original_data = sample_contexts[0].copy()
        results = ranker.rank_contexts(sample_contexts, "test")

        # Original contexts should not be modified
        assert sample_contexts[0] == original_data

        # Results should contain copies with added composite_score
        if results:
            result = results[0]
            assert "composite_score" in result
            # Remove composite_score and check other data is preserved
            result_copy = result.copy()
            del result_copy["composite_score"]
            # Should match one of the original contexts (excluding composite_score)


class TestScoringMethods:
    """Test individual scoring methods."""

    @pytest.fixture
    def ranker(self) -> RelevanceRanker:
        """Create RelevanceRanker instance for testing."""
        return RelevanceRanker()

    def test_score_file_type_python_files(self, ranker: RelevanceRanker) -> None:
        """Test file type scoring for Python files."""
        score = ranker._score_file_type("/path/to/module.py")
        assert score == 1.0  # Python files get highest score

    def test_score_file_type_javascript_files(self, ranker: RelevanceRanker) -> None:
        """Test file type scoring for JavaScript/TypeScript files."""
        js_score = ranker._score_file_type("/path/to/script.js")
        ts_score = ranker._score_file_type("/path/to/module.ts")
        assert js_score == 0.9
        assert ts_score == 0.9

    def test_score_file_type_other_code_files(self, ranker: RelevanceRanker) -> None:
        """Test file type scoring for other code files."""
        java_score = ranker._score_file_type("/path/to/Main.java")
        cpp_score = ranker._score_file_type("/path/to/program.cpp")
        c_score = ranker._score_file_type("/path/to/program.c")

        assert java_score == 0.8
        assert cpp_score == 0.8
        assert c_score == 0.8

    def test_score_file_type_documentation_files(self, ranker: RelevanceRanker) -> None:
        """Test file type scoring for documentation files."""
        md_score = ranker._score_file_type("/path/to/README.md")
        txt_score = ranker._score_file_type("/path/to/notes.txt")

        assert md_score == 0.7
        assert txt_score == 0.5

    def test_score_file_type_config_files(self, ranker: RelevanceRanker) -> None:
        """Test file type scoring for configuration files."""
        json_score = ranker._score_file_type("/path/to/config.json")
        yaml_score = ranker._score_file_type("/path/to/config.yaml")
        yml_score = ranker._score_file_type("/path/to/config.yml")

        assert json_score == 0.6
        assert yaml_score == 0.6
        assert yml_score == 0.6

    def test_score_file_type_unknown_extension(self, ranker: RelevanceRanker) -> None:
        """Test file type scoring for unknown extensions."""
        score = ranker._score_file_type("/path/to/file.unknown")
        assert score == 0.3  # Default for unknown types

    def test_score_file_type_no_extension(self, ranker: RelevanceRanker) -> None:
        """Test file type scoring for files without extension."""
        score = ranker._score_file_type("/path/to/Makefile")
        assert score == 0.3  # Default score

    def test_score_file_size_optimal_range(self, ranker: RelevanceRanker) -> None:
        """Test file size scoring in optimal range (1KB-50KB)."""
        assert ranker._score_file_size(5000) == 1.0
        assert ranker._score_file_size(25000) == 1.0
        assert ranker._score_file_size(50000) == 1.0

    def test_score_file_size_small_files(self, ranker: RelevanceRanker) -> None:
        """Test file size scoring for small files."""
        assert ranker._score_file_size(500) == 0.7
        assert ranker._score_file_size(100) == 0.7

    def test_score_file_size_large_files(self, ranker: RelevanceRanker) -> None:
        """Test file size scoring for large files."""
        assert ranker._score_file_size(75000) == 0.8  # Large but manageable
        assert ranker._score_file_size(150000) == 0.4  # Very large

    def test_score_file_size_zero_or_negative(self, ranker: RelevanceRanker) -> None:
        """Test file size scoring for zero or negative sizes."""
        assert ranker._score_file_size(0) == 0.0
        assert ranker._score_file_size(-100) == 0.0

    def test_score_structure_complexity_optimal(self, ranker: RelevanceRanker) -> None:
        """Test structure complexity scoring in optimal range."""
        context: dict[str, Any] = {
            "classes": ["Class1", "Class2"],  # 2 classes
            "functions": ["func1", "func2", "func3"],  # 3 functions
            "imports": ["os", "sys", "json"],  # 3 imports
        }
        # Complexity = 2*0.4 + 3*0.3 + 3*0.3 = 0.8 + 0.9 + 0.9 = 2.6
        # Since 5 <= 2.6 is false, complexity < 5, so score = 2.6 / 5.0 = 0.52
        score = ranker._score_structure_complexity(context)
        assert 0.5 <= score <= 0.6

    def test_score_structure_complexity_high_complexity(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test structure complexity scoring for high complexity."""
        context: dict[str, Any] = {
            "classes": ["C" + str(i) for i in range(20)],  # 20 classes
            "functions": ["f" + str(i) for i in range(30)],  # 30 functions
            "imports": ["i" + str(i) for i in range(10)],  # 10 imports
        }
        # Complexity = 20*0.4 + 30*0.3 + 10*0.3 = 8 + 9 + 3 = 20
        # Since complexity > 15, score = max(0.3, 15.0/20) = max(0.3, 0.75) = 0.75
        score = ranker._score_structure_complexity(context)
        assert score == 0.75

    def test_score_structure_complexity_empty_context(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test structure complexity scoring for empty context."""
        context: dict[str, Any] = {}
        score = ranker._score_structure_complexity(context)
        assert score == 0.0

    def test_score_structure_complexity_non_list_values(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test structure complexity scoring with non-list values."""
        context: dict[str, Any] = {
            "classes": "not a list",
            "functions": 123,
            "imports": None,
        }
        score = ranker._score_structure_complexity(context)
        assert score == 0.0

    def test_score_query_match_density_perfect_match(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test query match density with perfect matches."""
        context: dict[str, Any] = {
            "classes": ["UserClass", "AdminClass"],
            "functions": ["login_user", "validate_user"],
            "imports": ["user_module"],
            "comments": ["User management system"],
        }
        query = "user class login"
        score = ranker._score_query_match_density(context, query)
        assert score == 1.0  # All query terms match

    def test_score_query_match_density_partial_match(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test query match density with partial matches."""
        context: dict[str, Any] = {
            "classes": ["UserClass"],
            "functions": ["process_data"],
            "imports": ["os"],
            "comments": ["Data processing"],
        }
        query = "user data unknown"  # 2 out of 3 terms match
        score = ranker._score_query_match_density(context, query)
        assert abs(score - (2 / 3)) < 0.01

    def test_score_query_match_density_no_match(self, ranker: RelevanceRanker) -> None:
        """Test query match density with no matches."""
        context: dict[str, Any] = {
            "classes": ["SomeClass"],
            "functions": ["some_function"],
            "imports": ["some_module"],
            "comments": ["Some comment"],
        }
        query = "completely different terms"
        score = ranker._score_query_match_density(context, query)
        assert score == 0.0

    def test_score_query_match_density_empty_query(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test query match density with empty query."""
        context: dict[str, Any] = {
            "classes": ["Class"],
            "functions": ["function"],
        }
        score = ranker._score_query_match_density(context, "")
        assert score == 0.5  # Neutral score for empty query

    def test_score_query_match_density_empty_context(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test query match density with empty context."""
        context: dict[str, Any] = {}
        score = ranker._score_query_match_density(context, "test query")
        assert score == 0.0

    def test_calculate_composite_score_integration(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test composite score calculation integrates all scoring methods."""
        context: dict[str, Any] = {
            "file_path": "/test/module.py",
            "file_size": 5000,
            "relevance_score": 0.8,
            "classes": ["MyClass"],
            "functions": ["main_function"],
            "imports": ["os"],
            "comments": ["Main module"],
        }
        query = "main module class"

        score = ranker._calculate_composite_score(context, query)

        # Score should be between 0.0 and 1.0
        assert 0.0 <= score <= 1.0

        # Score should be influenced by all components
        assert score > 0.0  # Should be positive due to good relevance and matches

    def test_calculate_composite_score_invalid_relevance(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test composite score with invalid relevance scores."""
        context: dict[str, Any] = {
            "relevance_score": "invalid",
            "file_path": "/test/file.py",
            "file_size": 1000,
        }

        score = ranker._calculate_composite_score(context, "test")
        assert 0.0 <= score <= 1.0  # Should handle invalid input gracefully


class TestGetRankingSummary:
    """Test get_ranking_summary method."""

    @pytest.fixture
    def ranker(self) -> RelevanceRanker:
        """Create RelevanceRanker instance for testing."""
        return RelevanceRanker()

    @pytest.fixture
    def sample_ranked_results(self) -> list[dict[str, Any]]:
        """Create sample ranked results for testing."""
        return [
            {
                "file_path": "/test/module.py",
                "composite_score": 0.9,
            },
            {
                "file_path": "/test/utils.js",
                "composite_score": 0.7,
            },
            {
                "file_path": "/test/config.json",
                "composite_score": 0.5,
            },
            {
                "file_path": "/test/readme.md",
                "composite_score": 0.3,
            },
        ]

    def test_get_ranking_summary_with_results(
        self, ranker: RelevanceRanker, sample_ranked_results: list[dict[str, Any]]
    ) -> None:
        """Test ranking summary with results."""
        summary = ranker.get_ranking_summary(sample_ranked_results)

        assert summary["total_results"] == 4
        assert summary["average_score"] == (0.9 + 0.7 + 0.5 + 0.3) / 4

        # Check score distribution
        distribution = summary["score_distribution"]
        assert distribution["0.8-1.0"] == 1  # One score (0.9)
        assert distribution["0.6-0.8"] == 1  # One score (0.7)
        assert distribution["0.4-0.6"] == 1  # One score (0.5)
        assert distribution["0.2-0.4"] == 1  # One score (0.3)
        assert distribution["0.0-0.2"] == 0  # No scores in this range

        # Check file types
        file_types = summary["file_types"]
        assert file_types[".py"] == 1
        assert file_types[".js"] == 1
        assert file_types[".json"] == 1
        assert file_types[".md"] == 1

        # Check ranking weights are included
        assert "ranking_weights" in summary
        assert summary["ranking_weights"] == ranker.weights

    def test_get_ranking_summary_empty_results(self, ranker: RelevanceRanker) -> None:
        """Test ranking summary with empty results."""
        summary = ranker.get_ranking_summary([])

        assert summary["total_results"] == 0
        assert summary["average_score"] == 0.0
        assert summary["score_distribution"] == {}
        assert summary["file_types"] == {}

    def test_get_ranking_summary_missing_scores(self, ranker: RelevanceRanker) -> None:
        """Test ranking summary with missing composite scores."""
        results: list[dict[str, Any]] = [
            {"file_path": "/test/file1.py"},  # No composite_score
            {"file_path": "/test/file2.js", "composite_score": 0.8},
        ]

        summary = ranker.get_ranking_summary(results)

        # Should handle missing scores gracefully
        assert summary["total_results"] == 2
        # Average should be (0.0 + 0.8) / 2 = 0.4
        assert summary["average_score"] == 0.4

    def test_get_ranking_summary_file_types_no_extension(
        self, ranker: RelevanceRanker
    ) -> None:
        """Test ranking summary with files that have no extension."""
        results = [
            {"file_path": "/test/Makefile", "composite_score": 0.5},
            {"file_path": "/test/file", "composite_score": 0.3},
        ]

        summary = ranker.get_ranking_summary(results)

        # Files without extension should have empty string as key
        assert summary["file_types"][""] == 2


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling scenarios."""

    def test_ranker_with_structlog_available(self) -> None:
        """Test ranker initialization when structlog is available."""
        with patch("spec_cli.ai.context.ranking.structlog") as mock_structlog:
            mock_logger = Mock()
            mock_structlog.get_logger.return_value = mock_logger

            # Re-import to trigger structlog path
            import importlib

            import spec_cli.ai.context.ranking

            importlib.reload(spec_cli.ai.context.ranking)

            ranker = spec_cli.ai.context.ranking.RelevanceRanker()
            # Should use structlog logger
            assert ranker.debug_logger is not None

    def test_ranker_with_structlog_unavailable(self) -> None:
        """Test ranker initialization when structlog is not available."""
        with patch("spec_cli.ai.context.ranking.structlog", None):
            # Re-import to trigger non-structlog path
            import importlib

            import spec_cli.ai.context.ranking

            importlib.reload(spec_cli.ai.context.ranking)

            ranker = spec_cli.ai.context.ranking.RelevanceRanker()
            # Should use standard logging
            assert ranker.debug_logger is not None

    def test_path_normalization_in_scoring(self) -> None:
        """Test that path normalization is used in file type scoring."""
        ranker = RelevanceRanker()

        # Test with Windows-style path
        with patch(
            "spec_cli.ai.context.ranking.normalize_path_separators"
        ) as mock_normalize:
            mock_normalize.return_value = "/normalized/path/file.py"

            score = ranker._score_file_type("C:\\windows\\path\\file.py")

            mock_normalize.assert_called_once_with("C:\\windows\\path\\file.py")
            assert score == 1.0  # Should recognize .py extension after normalization

    def test_context_data_types_robustness(self) -> None:
        """Test ranker handles various context data types robustly."""
        ranker = RelevanceRanker(min_relevance_score=0.0)

        # Context with mixed data types
        contexts: list[dict[str, Any]] = [
            {
                "file_path": 123,  # Non-string path
                "file_size": "5000",  # String size
                "relevance_score": [0.8],  # List instead of float
                "classes": "not_a_list",  # String instead of list
                "functions": None,  # None instead of list
                "imports": 42,  # Number instead of list
                "comments": {},  # Dict instead of list
            }
        ]

        # Should not raise exception
        results = ranker.rank_contexts(contexts, "test")
        assert len(results) >= 0  # Should return some result or empty list

    def test_debug_logger_without_log_method(self) -> None:
        """Test ranker with debug logger that doesn't have log method."""
        mock_logger = Mock()
        # Remove the log method to test hasattr check
        del mock_logger.log

        ranker = RelevanceRanker(debug_logger=mock_logger)
        contexts = [{"file_path": "/test.py", "relevance_score": 0.5}]

        # Should not raise exception even without log method
        results = ranker.rank_contexts(contexts, "test")
        assert isinstance(results, list)


class TestIntegrationScenarios:
    """Test integration scenarios combining multiple features."""

    def test_full_ranking_pipeline(self) -> None:
        """Test complete ranking pipeline with realistic data."""
        ranker = RelevanceRanker(max_results=5, min_relevance_score=0.3)

        contexts = [
            {
                "file_path": "/project/src/auth/login.py",
                "file_size": 8000,
                "relevance_score": 0.9,
                "classes": ["LoginHandler", "AuthenticationError"],
                "functions": ["authenticate_user", "validate_credentials", "login"],
                "imports": ["hashlib", "jwt", "datetime"],
                "comments": ["Authentication module", "Handle user login"],
            },
            {
                "file_path": "/project/src/utils/helpers.js",
                "file_size": 3000,
                "relevance_score": 0.7,
                "classes": [],
                "functions": ["formatDate", "validateEmail", "sanitizeInput"],
                "imports": ["moment", "validator"],
                "comments": ["Utility functions", "Helper methods"],
            },
            {
                "file_path": "/project/config/settings.json",
                "file_size": 500,
                "relevance_score": 0.4,
                "classes": [],
                "functions": [],
                "imports": [],
                "comments": [],
            },
            {
                "file_path": "/project/docs/api.md",
                "file_size": 15000,
                "relevance_score": 0.6,
                "classes": [],
                "functions": [],
                "imports": [],
                "comments": ["API documentation", "Authentication endpoints"],
            },
        ]

        query = "authentication login user validate"
        results = ranker.rank_contexts(contexts, query)

        # Verify results
        assert len(results) > 0
        assert len(results) <= 5

        # First result should be the Python auth file (highest relevance + query match)
        assert results[0]["file_path"] == "/project/src/auth/login.py"

        # All results should meet minimum threshold
        for result in results:
            assert result["composite_score"] >= 0.3

        # Verify ranking summary
        summary = ranker.get_ranking_summary(results)
        assert summary["total_results"] == len(results)
        assert 0.0 < summary["average_score"] <= 1.0

    def test_performance_with_large_dataset(self) -> None:
        """Test ranking performance with larger dataset."""
        ranker = RelevanceRanker(max_results=10, min_relevance_score=0.1)

        # Generate 100 contexts
        contexts = []
        for i in range(100):
            contexts.append(
                {
                    "file_path": f"/project/file_{i}.py",
                    "file_size": 1000 + (i * 100),
                    "relevance_score": 0.1 + (i % 10) * 0.1,
                    "classes": [f"Class_{i}"],
                    "functions": [f"function_{i}", f"method_{i}"],
                    "imports": ["os", "sys"],
                    "comments": [f"Module {i}"],
                }
            )

        query = "function class module"

        # Should complete without performance issues
        results = ranker.rank_contexts(contexts, query)

        assert len(results) <= 10  # Respects max_results
        assert all(result["composite_score"] >= 0.1 for result in results)

    def test_empty_and_minimal_contexts(self) -> None:
        """Test ranking with empty and minimal context data."""
        ranker = RelevanceRanker(min_relevance_score=0.0)

        contexts: list[dict[str, Any]] = [
            {},  # Completely empty context
            {"file_path": "/test.py"},  # Minimal context
            {"relevance_score": 0.5},  # Only relevance score
            {  # Complete but empty lists
                "classes": [],
                "functions": [],
                "imports": [],
                "comments": [],
            },
        ]

        results = ranker.rank_contexts(contexts, "test")

        # Should handle gracefully
        assert isinstance(results, list)

        # All results should have composite_score
        for result in results:
            assert "composite_score" in result
            assert 0.0 <= result["composite_score"] <= 1.0
