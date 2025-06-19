"""Integration tests for Slice 4.1b: Semantic Embeddings & Search end-to-end workflow."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.context.semantic_search import SemanticSearchEngine

# Test constants
TEST_QUERY_AUTH = "user authentication and login"
TEST_QUERY_DATABASE = "database connections and queries"
TEST_QUERY_IRRELEVANT = "quantum physics and relativity"
SIMILARITY_THRESHOLD_HIGH = 0.8
SIMILARITY_THRESHOLD_LOW = 0.3
MAX_RESULTS_SMALL = 3
MAX_RESULTS_LARGE = 10

# Mock embedding vectors for consistent testing
MOCK_EMBEDDINGS = {
    "auth": [0.8, 0.1, 0.2, 0.3, 0.4, 0.5] + [0.0] * 762,  # 768-dim vector
    "database": [0.1, 0.8, 0.3, 0.2, 0.4, 0.5] + [0.0] * 762,
    "utils": [0.2, 0.3, 0.8, 0.1, 0.4, 0.5] + [0.0] * 762,
    "config": [0.3, 0.2, 0.1, 0.8, 0.4, 0.5] + [0.0] * 762,
    "irrelevant": [0.1, 0.1, 0.1, 0.1, 0.1, 0.1] + [0.0] * 762,
}

# Sample documentation content for testing
SAMPLE_DOCS = {
    "src/auth/login.py": """
User authentication module providing login and logout functionality.
Handles user credentials, session management, and security validation.
Supports OAuth, JWT tokens, and traditional username/password authentication.
""",
    "src/database/connection.py": """
Database connection manager for handling SQL and NoSQL database connections.
Provides connection pooling, query execution, and transaction management.
Supports PostgreSQL, MySQL, MongoDB, and Redis databases.
""",
    "src/utils/helpers.py": """
General utility functions for string manipulation, date formatting, and file operations.
Helper functions for common programming tasks and data validation.
""",
    "src/config/settings.py": """
Application configuration management and environment variable handling.
Manages development, staging, and production environment configurations.
""",
    "docs/physics.md": """
Documentation about quantum physics principles and Einstein's theory of relativity.
Mathematical formulations and scientific explanations of physical phenomena.
""",
}


@pytest.fixture
def mock_ai_config_enabled():
    """Create mock AI configuration with embeddings enabled."""
    config = Mock(spec=AIConfig)
    config.enabled = True
    return config


@pytest.fixture
def mock_ai_config_disabled():
    """Create mock AI configuration with embeddings disabled."""
    config = Mock(spec=AIConfig)
    config.enabled = False
    return config


@pytest.fixture
def temp_project_structure():
    """Create temporary project structure with sample files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)

        # Create directory structure
        (project_root / "src" / "auth").mkdir(parents=True)
        (project_root / "src" / "database").mkdir(parents=True)
        (project_root / "src" / "utils").mkdir(parents=True)
        (project_root / "src" / "config").mkdir(parents=True)
        (project_root / "docs").mkdir(parents=True)
        (project_root / ".spec").mkdir(parents=True)

        # Write sample files
        for file_path, content in SAMPLE_DOCS.items():
            full_path = project_root / file_path
            full_path.write_text(content)

        yield project_root


@pytest.fixture
def sample_file_index_with_embeddings():
    """Create sample file index data with pre-computed embeddings."""
    return {
        "files": {
            "src/auth/login.py": {
                "size": 256,
                "modified": "2023-01-01T00:00:00",
                "type": "python",
                "embeddings": MOCK_EMBEDDINGS["auth"],
            },
            "src/database/connection.py": {
                "size": 512,
                "modified": "2023-01-01T00:00:00",
                "type": "python",
                "embeddings": MOCK_EMBEDDINGS["database"],
            },
            "src/utils/helpers.py": {
                "size": 128,
                "modified": "2023-01-01T00:00:00",
                "type": "python",
                "embeddings": MOCK_EMBEDDINGS["utils"],
            },
            "src/config/settings.py": {
                "size": 64,
                "modified": "2023-01-01T00:00:00",
                "type": "python",
                "embeddings": MOCK_EMBEDDINGS["config"],
            },
            "docs/physics.md": {
                "size": 1024,
                "modified": "2023-01-01T00:00:00",
                "type": "markdown",
                "embeddings": MOCK_EMBEDDINGS["irrelevant"],
            },
        },
        "metadata": {"total_files": 5, "index_created": "2023-01-01T00:00:00"},
    }


class TestSlice4_1bSemanticSearchIntegration:
    """Integration tests for end-to-end semantic search functionality."""

    def test_integration_end_to_end_semantic_search_produces_ranked_results(
        self, mock_ai_config_enabled, sample_file_index_with_embeddings
    ):
        """Test complete semantic search workflow produces properly ranked results."""

        # Mock the embedding generation to return consistent vectors
        def mock_generate_embeddings(text):
            if "authentication" in text.lower() or "login" in text.lower():
                return {
                    "success": True,
                    "data": {"embeddings": MOCK_EMBEDDINGS["auth"]},
                }
            elif "database" in text.lower():
                return {
                    "success": True,
                    "data": {"embeddings": MOCK_EMBEDDINGS["database"]},
                }
            else:
                return {
                    "success": True,
                    "data": {"embeddings": MOCK_EMBEDDINGS["irrelevant"]},
                }

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)
            result = search_engine.search(
                TEST_QUERY_AUTH,
                sample_file_index_with_embeddings,
                max_results=MAX_RESULTS_SMALL,
                similarity_threshold=SIMILARITY_THRESHOLD_LOW,
            )

            assert result["success"] is True
            assert len(result["data"]["search_results"]) > 0

            # Verify auth-related file is ranked highest for auth query
            top_result = result["data"]["search_results"][0]
            assert "auth" in top_result["file_path"]
            assert top_result["similarity"] > SIMILARITY_THRESHOLD_HIGH

            # Verify results are sorted by similarity (descending)
            similarities = result["data"]["similarity_scores"]
            assert similarities == sorted(similarities, reverse=True)

    def test_integration_semantic_search_outperforms_keyword_matching(
        self, mock_ai_config_enabled, sample_file_index_with_embeddings
    ):
        """Test semantic search finds relevant results beyond simple keyword matching."""
        # Use a query that doesn't have exact keywords but semantic meaning
        semantic_query = (
            "user login and session management"  # Related to auth but different words
        )

        def mock_generate_embeddings(text):
            # Query should be semantically similar to auth content
            if "user login" in text or "authentication" in text.lower():
                return {
                    "success": True,
                    "data": {"embeddings": MOCK_EMBEDDINGS["auth"]},
                }
            return {
                "success": True,
                "data": {"embeddings": MOCK_EMBEDDINGS["irrelevant"]},
            }

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)
            result = search_engine.search(
                semantic_query,
                sample_file_index_with_embeddings,
                similarity_threshold=SIMILARITY_THRESHOLD_LOW,
            )

            assert result["success"] is True
            assert len(result["data"]["search_results"]) > 0

            # Auth file should be found even without exact keyword matches
            auth_found = any(
                "auth" in r["file_path"] for r in result["data"]["search_results"]
            )
            assert auth_found, "Semantic search should find auth-related content"

    def test_integration_similarity_threshold_filtering_works_correctly(
        self, mock_ai_config_enabled, sample_file_index_with_embeddings
    ):
        """Test similarity threshold effectively filters low-relevance results."""

        def mock_generate_embeddings(text):
            return {
                "success": True,
                "data": {"embeddings": MOCK_EMBEDDINGS["irrelevant"]},
            }

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)

            # High threshold should filter out most results
            result_high = search_engine.search(
                TEST_QUERY_IRRELEVANT,
                sample_file_index_with_embeddings,
                similarity_threshold=SIMILARITY_THRESHOLD_HIGH,
            )

            # Low threshold should include more results
            result_low = search_engine.search(
                TEST_QUERY_IRRELEVANT,
                sample_file_index_with_embeddings,
                similarity_threshold=SIMILARITY_THRESHOLD_LOW,
            )

            assert result_high["success"] is True
            assert result_low["success"] is True
            assert len(result_low["data"]["search_results"]) >= len(
                result_high["data"]["search_results"]
            )

    def test_integration_max_results_limit_is_respected(
        self, mock_ai_config_enabled, sample_file_index_with_embeddings
    ):
        """Test max_results parameter correctly limits returned results."""

        def mock_generate_embeddings(text):
            return {"success": True, "data": {"embeddings": MOCK_EMBEDDINGS["auth"]}}

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)

            result = search_engine.search(
                TEST_QUERY_AUTH,
                sample_file_index_with_embeddings,
                max_results=MAX_RESULTS_SMALL,
                similarity_threshold=SIMILARITY_THRESHOLD_LOW,
            )

            assert result["success"] is True
            assert len(result["data"]["search_results"]) <= MAX_RESULTS_SMALL

            # Metadata should reflect the limiting
            metadata = result["data"]["metadata"]
            assert metadata["results_returned"] <= MAX_RESULTS_SMALL

    def test_integration_embedding_caching_improves_performance(
        self, mock_ai_config_enabled, sample_file_index_with_embeddings
    ):
        """Test embedding caching reduces redundant generation calls."""
        generation_calls = []

        def mock_generate_embeddings(text):
            generation_calls.append(text)
            return {"success": True, "data": {"embeddings": MOCK_EMBEDDINGS["auth"]}}

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)

            # First search
            search_engine.search(TEST_QUERY_AUTH, sample_file_index_with_embeddings)
            first_call_count = len(generation_calls)

            # Second search with same query - should use cached embeddings
            search_engine.search(TEST_QUERY_AUTH, sample_file_index_with_embeddings)
            second_call_count = len(generation_calls)

            # Only one new call should be made (for the query), document embeddings should be cached
            assert second_call_count == first_call_count + 1, (
                "Document embeddings should be cached"
            )

    def test_integration_when_ai_disabled_then_returns_clear_error(
        self, mock_ai_config_disabled, sample_file_index_with_embeddings
    ):
        """Test semantic search provides clear error when AI is disabled."""
        search_engine = SemanticSearchEngine(mock_ai_config_disabled)

        result = search_engine.search(
            TEST_QUERY_AUTH, sample_file_index_with_embeddings
        )

        assert result["success"] is False
        assert "AI embeddings disabled" in result["error"]

    def test_integration_handles_missing_files_gracefully(self, mock_ai_config_enabled):
        """Test semantic search handles missing files without crashing."""
        file_index_with_missing = {
            "files": {
                "/nonexistent/file1.py": {
                    "size": 256,
                    "modified": "2023-01-01T00:00:00",
                    "type": "python",
                    # No embeddings - will try to generate from file
                },
                "/another/missing.py": {
                    "size": 512,
                    "modified": "2023-01-01T00:00:00",
                    "type": "python",
                },
            }
        }

        def mock_generate_embeddings(text):
            return {"success": True, "data": {"embeddings": MOCK_EMBEDDINGS["auth"]}}

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)
            result = search_engine.search(TEST_QUERY_AUTH, file_index_with_missing)

            # Should complete successfully even with missing files
            assert result["success"] is True
            # Should not include results for missing files
            assert len(result["data"]["search_results"]) == 0

    def test_integration_cross_platform_path_handling(self, mock_ai_config_enabled):
        """Test semantic search handles different path formats correctly."""
        mixed_path_index = {
            "files": {
                "C:\\Windows\\path\\file.py": {
                    "size": 256,
                    "type": "python",
                    "embeddings": MOCK_EMBEDDINGS["auth"],
                },
                "/unix/style/path.py": {
                    "size": 512,
                    "type": "python",
                    "embeddings": MOCK_EMBEDDINGS["database"],
                },
            }
        }

        def mock_generate_embeddings(text):
            return {"success": True, "data": {"embeddings": MOCK_EMBEDDINGS["auth"]}}

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)
            result = search_engine.search(
                TEST_QUERY_AUTH, mixed_path_index, similarity_threshold=0.0
            )

            assert result["success"] is True
            # Should handle both path formats without errors
            assert len(result["data"]["search_results"]) == 2

    def test_integration_performance_requirements_met(
        self, mock_ai_config_enabled, sample_file_index_with_embeddings
    ):
        """Test semantic search completes within performance requirements."""
        import time

        def mock_generate_embeddings(text):
            return {"success": True, "data": {"embeddings": MOCK_EMBEDDINGS["auth"]}}

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)

            start_time = time.time()
            result = search_engine.search(
                TEST_QUERY_AUTH, sample_file_index_with_embeddings
            )
            end_time = time.time()

            search_duration = end_time - start_time

            assert result["success"] is True
            # Should complete within 5 seconds for typical documentation sets (mocked)
            assert search_duration < 5.0, (
                f"Search took {search_duration:.2f}s, should be < 5s"
            )

    def test_integration_error_handling_with_embedding_failures(
        self, mock_ai_config_enabled, sample_file_index_with_embeddings
    ):
        """Test semantic search handles embedding generation failures gracefully."""

        def mock_generate_embeddings_failing(text):
            return {"success": False, "error": "Model loading failed"}

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings_failing
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)
            result = search_engine.search(
                TEST_QUERY_AUTH, sample_file_index_with_embeddings
            )

            assert result["success"] is False
            assert "Query embedding failed" in result["error"]
            assert "Model loading failed" in result["error"]

    def test_integration_metadata_provides_meaningful_insights(
        self, mock_ai_config_enabled, sample_file_index_with_embeddings
    ):
        """Test search results include comprehensive metadata for analysis."""

        def mock_generate_embeddings(text):
            return {"success": True, "data": {"embeddings": MOCK_EMBEDDINGS["auth"]}}

        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings = Mock(
                side_effect=mock_generate_embeddings
            )
            mock_embedder_class.return_value = mock_embedder

            search_engine = SemanticSearchEngine(mock_ai_config_enabled)
            result = search_engine.search(
                TEST_QUERY_AUTH,
                sample_file_index_with_embeddings,
                max_results=MAX_RESULTS_SMALL,
                similarity_threshold=SIMILARITY_THRESHOLD_HIGH,
            )

            assert result["success"] is True
            metadata = result["data"]["metadata"]

            # Verify comprehensive metadata
            assert metadata["query"] == TEST_QUERY_AUTH
            assert metadata["total_documents"] == 5
            assert "documents_with_embeddings" in metadata
            assert "matches_found" in metadata
            assert "results_returned" in metadata
            assert metadata["similarity_threshold"] == SIMILARITY_THRESHOLD_HIGH
            assert "search_time" in metadata

            # Verify metadata consistency
            assert metadata["results_returned"] <= metadata["matches_found"]
            assert metadata["matches_found"] <= metadata["total_documents"]
