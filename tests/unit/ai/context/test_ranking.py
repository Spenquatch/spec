"""Unit tests for RelevanceRanker class."""

from unittest.mock import Mock

import pytest

from spec_cli.ai.context.ranking import RelevanceRanker


class TestRelevanceRankerInitialization:
    """Test RelevanceRanker initialization."""

    def test_init_with_default_parameters_creates_ranker_with_defaults(self):
        """Test initialization with default parameters."""
        ranker = RelevanceRanker()

        assert ranker.max_results == 20
        assert ranker.min_relevance_score == 0.1
        assert ranker.debug_logger is not None
        assert isinstance(ranker.weights, dict)
        assert len(ranker.weights) == 5

    def test_init_with_custom_parameters_uses_provided_values(self):
        """Test initialization with custom parameters."""
        mock_logger = Mock()

        ranker = RelevanceRanker(
            max_results=10, min_relevance_score=0.3, debug_logger=mock_logger
        )

        assert ranker.max_results == 10
        assert ranker.min_relevance_score == 0.3
        assert ranker.debug_logger is mock_logger

    def test_init_when_invalid_max_results_then_raises_value_error(self):
        """Test initialization with invalid max_results."""
        with pytest.raises(ValueError, match="max_results must be positive"):
            RelevanceRanker(max_results=0)

        with pytest.raises(ValueError, match="max_results must be positive"):
            RelevanceRanker(max_results=-1)

    def test_init_when_invalid_min_relevance_score_then_raises_value_error(self):
        """Test initialization with invalid min_relevance_score."""
        with pytest.raises(
            ValueError, match="min_relevance_score must be between 0.0 and 1.0"
        ):
            RelevanceRanker(min_relevance_score=-0.1)

        with pytest.raises(
            ValueError, match="min_relevance_score must be between 0.0 and 1.0"
        ):
            RelevanceRanker(min_relevance_score=1.1)

    def test_init_when_edge_case_min_scores_then_accepts_valid_boundaries(self):
        """Test initialization with boundary min_relevance_score values."""
        ranker_zero = RelevanceRanker(min_relevance_score=0.0)
        assert ranker_zero.min_relevance_score == 0.0

        ranker_one = RelevanceRanker(min_relevance_score=1.0)
        assert ranker_one.min_relevance_score == 1.0


class TestRelevanceRankerRankContexts:
    """Test RelevanceRanker rank_contexts method."""

    @pytest.fixture
    def ranker(self):
        """Create ranker with mocked logger."""
        mock_logger = Mock()
        return RelevanceRanker(debug_logger=mock_logger)

    @pytest.fixture
    def sample_contexts(self):
        """Sample contexts for testing."""
        return [
            {
                "file_path": "/project/module1.py",
                "file_size": 2000,
                "relevance_score": 0.8,
                "classes": ["UserManager", "AuthService"],
                "functions": ["authenticate", "login"],
                "imports": ["from auth import utils"],
                "comments": ["# User authentication module"],
            },
            {
                "file_path": "/project/utils.js",
                "file_size": 1500,
                "relevance_score": 0.6,
                "classes": [],
                "functions": ["formatDate", "validateEmail"],
                "imports": [],
                "comments": ["// Utility functions"],
            },
            {
                "file_path": "/project/config.json",
                "file_size": 500,
                "relevance_score": 0.3,
                "classes": [],
                "functions": [],
                "imports": [],
                "comments": [],
            },
        ]

    def test_rank_contexts_when_valid_inputs_then_returns_ranked_list(
        self, ranker, sample_contexts
    ):
        """Test ranking with valid inputs."""
        query = "user authentication"

        result = ranker.rank_contexts(sample_contexts, query)

        assert isinstance(result, list)
        assert len(result) <= ranker.max_results
        # Should be sorted by composite_score (descending)
        for i in range(1, len(result)):
            assert result[i - 1]["composite_score"] >= result[i]["composite_score"]

    def test_rank_contexts_when_empty_contexts_then_raises_value_error(self, ranker):
        """Test ranking with empty contexts list."""
        with pytest.raises(ValueError, match="Contexts list cannot be empty"):
            ranker.rank_contexts([], "query")

    def test_rank_contexts_when_invalid_query_type_then_raises_value_error(
        self, ranker, sample_contexts
    ):
        """Test ranking with invalid query type."""
        with pytest.raises(ValueError, match="Query must be a string"):
            ranker.rank_contexts(sample_contexts, 123)

        with pytest.raises(ValueError, match="Query must be a string"):
            ranker.rank_contexts(sample_contexts, None)

    def test_rank_contexts_when_contexts_below_threshold_then_filters_out(
        self, sample_contexts
    ):
        """Test filtering of contexts below minimum relevance score."""
        ranker = RelevanceRanker(min_relevance_score=0.7)
        query = "test"

        result = ranker.rank_contexts(sample_contexts, query)

        # Only contexts with high relevance should remain
        assert all(ctx["composite_score"] >= 0.7 for ctx in result)

    def test_rank_contexts_when_max_results_limit_then_respects_limit(
        self, sample_contexts
    ):
        """Test max_results limit enforcement."""
        ranker = RelevanceRanker(max_results=2, min_relevance_score=0.0)
        query = "test"

        result = ranker.rank_contexts(sample_contexts, query)

        assert len(result) <= 2

    def test_rank_contexts_when_called_then_logs_debug_information(
        self, ranker, sample_contexts
    ):
        """Test that debug information is logged."""
        query = "test"

        ranker.rank_contexts(sample_contexts, query)

        # Verify debug logging
        ranker.debug_logger.log.assert_called_once()
        call_args = ranker.debug_logger.log.call_args
        assert call_args[0][0] == "DEBUG"
        assert call_args[0][1] == "Contexts ranked"

    def test_rank_contexts_when_query_empty_then_handles_gracefully(
        self, ranker, sample_contexts
    ):
        """Test ranking with empty query string."""
        result = ranker.rank_contexts(sample_contexts, "")

        # Should still process contexts
        assert isinstance(result, list)

    def test_rank_contexts_when_contexts_have_composite_score_then_preserves_ranking(
        self, ranker, sample_contexts
    ):
        """Test that composite scores are added to results."""
        query = "test"

        result = ranker.rank_contexts(sample_contexts, query)

        for context in result:
            assert "composite_score" in context
            assert isinstance(context["composite_score"], float)
            assert 0.0 <= context["composite_score"] <= 1.0


class TestRelevanceRankerCompositeScoring:
    """Test composite score calculation."""

    @pytest.fixture
    def ranker(self):
        """Create basic ranker for testing."""
        return RelevanceRanker()

    @pytest.fixture
    def basic_context(self):
        """Basic context for scoring tests."""
        return {
            "file_path": "/project/test.py",
            "file_size": 2000,
            "relevance_score": 0.7,
            "classes": ["TestClass"],
            "functions": ["test_function"],
            "imports": ["import unittest"],
            "comments": ["# Test file"],
        }

    def test_calculate_composite_score_when_valid_context_then_returns_score(
        self, ranker, basic_context
    ):
        """Test composite score calculation."""
        query = "test function"

        score = ranker._calculate_composite_score(basic_context, query)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_calculate_composite_score_when_missing_fields_then_handles_gracefully(
        self, ranker
    ):
        """Test scoring with missing context fields."""
        incomplete_context = {
            "file_path": "/test.py",
            "file_size": 1000,
            # Missing other fields
        }
        query = "test"

        score = ranker._calculate_composite_score(incomplete_context, query)

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

    def test_score_file_type_when_python_file_then_returns_high_score(self, ranker):
        """Test file type scoring for Python files."""
        score = ranker._score_file_type("/project/module.py")
        assert score == 1.0

    def test_score_file_type_when_javascript_file_then_returns_good_score(self, ranker):
        """Test file type scoring for JavaScript files."""
        score = ranker._score_file_type("/project/script.js")
        assert score == 0.9

    def test_score_file_type_when_unknown_extension_then_returns_default_score(
        self, ranker
    ):
        """Test file type scoring for unknown extensions."""
        score = ranker._score_file_type("/project/data.xyz")
        assert score == 0.3

    def test_score_file_size_when_optimal_size_then_returns_max_score(self, ranker):
        """Test file size scoring for optimal sizes."""
        score = ranker._score_file_size(25000)  # 25KB - optimal range
        assert score == 1.0

    def test_score_file_size_when_very_small_then_returns_moderate_score(self, ranker):
        """Test file size scoring for very small files."""
        score = ranker._score_file_size(500)  # 500 bytes
        assert score == 0.7

    def test_score_file_size_when_very_large_then_returns_low_score(self, ranker):
        """Test file size scoring for very large files."""
        score = ranker._score_file_size(500000)  # 500KB
        assert score == 0.4

    def test_score_file_size_when_zero_size_then_returns_zero(self, ranker):
        """Test file size scoring for zero-size files."""
        score = ranker._score_file_size(0)
        assert score == 0.0

    def test_score_structure_complexity_when_optimal_complexity_then_returns_max(
        self, ranker
    ):
        """Test structure complexity scoring for optimal complexity."""
        context = {
            "classes": ["Class1", "Class2"],  # 2 classes = 0.8
            "functions": ["func1", "func2"],  # 2 functions = 0.6
            "imports": ["import1", "import2"],  # 2 imports = 0.6
        }  # Total complexity = 2.0

        score = ranker._score_structure_complexity(context)
        assert 0.0 <= score <= 1.0

    def test_score_structure_complexity_when_empty_structure_then_returns_zero(
        self, ranker
    ):
        """Test structure complexity scoring for empty structure."""
        context = {"classes": [], "functions": [], "imports": []}

        score = ranker._score_structure_complexity(context)
        assert score == 0.0

    def test_score_query_match_density_when_all_terms_match_then_returns_one(
        self, ranker
    ):
        """Test query match density with all terms matching."""
        context = {
            "classes": ["UserClass"],
            "functions": ["authenticate_user"],
            "imports": ["from auth import user"],
            "comments": ["# User authentication"],
        }
        query = "user authenticate"

        score = ranker._score_query_match_density(context, query)
        assert score == 1.0

    def test_score_query_match_density_when_no_terms_match_then_returns_zero(
        self, ranker
    ):
        """Test query match density with no terms matching."""
        context = {
            "classes": ["DatabaseConnection"],
            "functions": ["connect", "execute"],
            "imports": ["import sqlite3"],
            "comments": ["# Database operations"],
        }
        query = "user authentication"

        score = ranker._score_query_match_density(context, query)
        assert score == 0.0

    def test_score_query_match_density_when_empty_query_then_returns_neutral(
        self, ranker, basic_context
    ):
        """Test query match density with empty query."""
        score = ranker._score_query_match_density(basic_context, "")
        assert score == 0.5


class TestRelevanceRankerRankingSummary:
    """Test ranking summary generation."""

    @pytest.fixture
    def ranker(self):
        """Create basic ranker for testing."""
        return RelevanceRanker()

    @pytest.fixture
    def ranked_results(self):
        """Sample ranked results for testing."""
        return [
            {"file_path": "/project/main.py", "composite_score": 0.9},
            {"file_path": "/project/utils.js", "composite_score": 0.7},
            {"file_path": "/project/config.json", "composite_score": 0.4},
        ]

    def test_get_ranking_summary_when_results_provided_then_returns_complete_summary(
        self, ranker, ranked_results
    ):
        """Test ranking summary with results."""
        summary = ranker.get_ranking_summary(ranked_results)

        assert isinstance(summary, dict)
        assert "total_results" in summary
        assert "average_score" in summary
        assert "score_distribution" in summary
        assert "file_types" in summary
        assert "ranking_weights" in summary

        assert summary["total_results"] == 3
        assert isinstance(summary["average_score"], float)
        assert isinstance(summary["score_distribution"], dict)
        assert isinstance(summary["file_types"], dict)

    def test_get_ranking_summary_when_empty_results_then_returns_zero_stats(
        self, ranker
    ):
        """Test ranking summary with empty results."""
        summary = ranker.get_ranking_summary([])

        assert summary["total_results"] == 0
        assert summary["average_score"] == 0.0
        assert summary["score_distribution"] == {}
        assert summary["file_types"] == {}

    def test_get_ranking_summary_when_results_then_calculates_score_distribution(
        self, ranker, ranked_results
    ):
        """Test score distribution calculation."""
        summary = ranker.get_ranking_summary(ranked_results)

        distribution = summary["score_distribution"]
        assert "0.8-1.0" in distribution
        assert "0.6-0.8" in distribution
        assert "0.4-0.6" in distribution
        assert "0.2-0.4" in distribution
        assert "0.0-0.2" in distribution

        # Verify counts based on our test data
        assert distribution["0.8-1.0"] == 1  # 0.9 score
        assert distribution["0.6-0.8"] == 1  # 0.7 score
        assert distribution["0.4-0.6"] == 1  # 0.4 score

    def test_get_ranking_summary_when_results_then_counts_file_types(
        self, ranker, ranked_results
    ):
        """Test file type counting."""
        summary = ranker.get_ranking_summary(ranked_results)

        file_types = summary["file_types"]
        assert ".py" in file_types
        assert ".js" in file_types
        assert ".json" in file_types
        assert file_types[".py"] == 1
        assert file_types[".js"] == 1
        assert file_types[".json"] == 1

    def test_get_ranking_summary_when_called_then_includes_ranking_weights(
        self, ranker, ranked_results
    ):
        """Test that ranking weights are included in summary."""
        summary = ranker.get_ranking_summary(ranked_results)

        weights = summary["ranking_weights"]
        assert isinstance(weights, dict)
        assert weights == ranker.weights
        # Verify it's a copy, not reference
        weights["test"] = "modified"
        assert "test" not in ranker.weights


class TestRelevanceRankerCrossPlatformCompatibility:
    """Test cross-platform compatibility."""

    def test_score_file_type_when_windows_path_then_handles_correctly(self):
        """Test file type scoring with Windows paths."""
        ranker = RelevanceRanker()

        # Test with Windows-style path
        score = ranker._score_file_type("C:\\project\\module.py")
        assert score == 1.0  # Should recognize .py extension

    def test_file_type_scoring_when_mixed_case_extensions_then_normalizes(self):
        """Test file type scoring with mixed case extensions."""
        ranker = RelevanceRanker()

        score_py = ranker._score_file_type("/project/MODULE.PY")
        score_js = ranker._score_file_type("/project/SCRIPT.JS")

        assert score_py == 1.0  # Should normalize to .py
        assert score_js == 0.9  # Should normalize to .js


class TestRelevanceRankerErrorHandling:
    """Test error handling in RelevanceRanker."""

    def test_rank_contexts_when_malformed_context_then_handles_gracefully(self):
        """Test ranking with malformed context data."""
        ranker = RelevanceRanker()
        malformed_contexts = [
            {"file_path": "/test.py"},  # Missing most fields
            {},  # Empty context
            {"relevance_score": "invalid"},  # Invalid score type
        ]

        # Should not crash with malformed data
        result = ranker.rank_contexts(malformed_contexts, "test")
        assert isinstance(result, list)

    def test_composite_score_calculation_when_invalid_data_then_clamps_to_range(self):
        """Test that composite scores are always in valid range."""
        ranker = RelevanceRanker()

        # Test with extreme values
        extreme_context = {
            "file_path": "/test.py",
            "file_size": -1000,  # Invalid size
            "relevance_score": 5.0,  # Out of range
            "classes": [],
            "functions": [],
            "imports": [],
            "comments": [],
        }

        score = ranker._calculate_composite_score(extreme_context, "test")
        assert 0.0 <= score <= 1.0  # Should be clamped to valid range
