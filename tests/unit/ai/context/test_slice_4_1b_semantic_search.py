"""Unit tests for Slice 4.1b: Semantic search using vector embeddings."""

import json
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.context.semantic_search import (
    SemanticSearchEngine,
    perform_semantic_search,
)

# Test constants
TEST_QUERY = "authentication and user management"
TEST_SIMILARITY_THRESHOLD = 0.7
TEST_MAX_RESULTS = 5
MOCK_QUERY_EMBEDDING = [0.1, 0.2, 0.3, 0.4, 0.5]
MOCK_DOC_EMBEDDING_1 = [0.15, 0.25, 0.35, 0.45, 0.55]  # High similarity
MOCK_DOC_EMBEDDING_2 = [0.9, 0.8, 0.7, 0.6, 0.5]  # Low similarity
HIGH_SIMILARITY_SCORE = 0.95
LOW_SIMILARITY_SCORE = 0.3
TEST_FILE_PATH_1 = "/project/src/auth.py"
TEST_FILE_PATH_2 = "/project/src/utils.py"
TEST_FILE_CONTENT = "User authentication module with login and logout functionality"


@pytest.fixture
def mock_ai_config():
    """Create mock AI configuration for testing."""
    config = Mock(spec=AIConfig)
    config.enabled = True
    return config


@pytest.fixture
def mock_embedding_generator():
    """Create mock embedding generator."""
    generator = Mock()
    generator.generate_embeddings.return_value = {
        "success": True,
        "data": {"embeddings": MOCK_QUERY_EMBEDDING},
    }
    return generator


@pytest.fixture
def sample_file_index_data():
    """Create sample file index data for testing."""
    return {
        "files": {
            TEST_FILE_PATH_1: {
                "size": 1024,
                "modified": "2023-01-01T00:00:00",
                "type": "python",
                "embeddings": MOCK_DOC_EMBEDDING_1,
            },
            TEST_FILE_PATH_2: {
                "size": 512,
                "modified": "2023-01-01T00:00:00",
                "type": "python",
                # No embeddings - will need to generate
            },
        },
        "metadata": {"total_files": 2, "index_created": "2023-01-01T00:00:00"},
    }


@pytest.fixture
def empty_file_index_data():
    """Create empty file index data for testing."""
    return {
        "files": {},
        "metadata": {"total_files": 0, "index_created": "2023-01-01T00:00:00"},
    }


class TestSemanticSearchEngineInitialization:
    """Test SemanticSearchEngine initialization."""

    def test_init_with_ai_config_creates_engine_with_embedder(self, mock_ai_config):
        """Test initialization creates search engine with embedding generator."""
        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder_class.return_value = mock_embedder

            engine = SemanticSearchEngine(mock_ai_config)

            assert engine.ai_config == mock_ai_config
            assert engine.embedder == mock_embedder
            assert engine.embeddings_cache == {}
            mock_embedder_class.assert_called_once_with(mock_ai_config)


class TestSemanticSearchValidation:
    """Test search input validation."""

    def test_search_when_empty_query_then_returns_error(
        self, mock_ai_config, sample_file_index_data
    ):
        """Test search with empty query returns error."""
        engine = SemanticSearchEngine(mock_ai_config)

        result = engine.search("", sample_file_index_data)

        assert result["success"] is False
        assert "Empty query provided" in result["error"]

    def test_search_when_whitespace_only_query_then_returns_error(
        self, mock_ai_config, sample_file_index_data
    ):
        """Test search with whitespace-only query returns error."""
        engine = SemanticSearchEngine(mock_ai_config)

        result = engine.search("   ", sample_file_index_data)

        assert result["success"] is False
        assert "Empty query provided" in result["error"]

    def test_search_when_invalid_file_index_data_then_returns_error(
        self, mock_ai_config
    ):
        """Test search with invalid file index data returns error."""
        engine = SemanticSearchEngine(mock_ai_config)
        invalid_data = {"invalid": "structure"}

        result = engine.search(TEST_QUERY, invalid_data)

        assert result["success"] is False
        assert "Invalid file index data" in result["error"]


class TestSemanticSearchQueryEmbedding:
    """Test query embedding generation during search."""

    def test_search_when_query_embedding_fails_then_returns_error(
        self, mock_ai_config, sample_file_index_data
    ):
        """Test search when query embedding generation fails."""
        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings.return_value = {
                "success": False,
                "error": "Model loading failed",
            }
            mock_embedder_class.return_value = mock_embedder

            engine = SemanticSearchEngine(mock_ai_config)
            result = engine.search(TEST_QUERY, sample_file_index_data)

            assert result["success"] is False
            assert "Query embedding failed" in result["error"]
            assert "Model loading failed" in result["error"]

    def test_search_when_query_embedding_succeeds_then_processes_documents(
        self, mock_ai_config, sample_file_index_data
    ):
        """Test search proceeds with document processing after successful query embedding."""
        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings.return_value = {
                "success": True,
                "data": {"embeddings": MOCK_QUERY_EMBEDDING},
            }
            mock_embedder_class.return_value = mock_embedder

            engine = SemanticSearchEngine(mock_ai_config)

            # Mock document embedding retrieval to avoid file I/O
            engine._get_document_embedding = Mock(return_value=MOCK_DOC_EMBEDDING_1)

            result = engine.search(TEST_QUERY, sample_file_index_data)

            assert result["success"] is True
            mock_embedder.generate_embeddings.assert_called_once_with(TEST_QUERY)


class TestDocumentEmbeddingRetrieval:
    """Test document embedding retrieval and caching."""

    def test_get_document_embedding_when_embeddings_in_file_info_then_returns_cached(
        self, mock_ai_config
    ):
        """Test retrieval of embeddings from file index data."""
        engine = SemanticSearchEngine(mock_ai_config)
        file_info = {"embeddings": MOCK_DOC_EMBEDDING_1}

        result = engine._get_document_embedding(TEST_FILE_PATH_1, file_info)

        assert result == MOCK_DOC_EMBEDDING_1

    def test_get_document_embedding_when_in_runtime_cache_then_returns_cached(
        self, mock_ai_config
    ):
        """Test retrieval of embeddings from runtime cache."""
        engine = SemanticSearchEngine(mock_ai_config)
        engine.embeddings_cache[TEST_FILE_PATH_1] = MOCK_DOC_EMBEDDING_1
        file_info = {}

        result = engine._get_document_embedding(TEST_FILE_PATH_1, file_info)

        assert result == MOCK_DOC_EMBEDDING_1

    def test_get_document_embedding_when_file_not_exists_then_returns_none(
        self, mock_ai_config
    ):
        """Test retrieval when file does not exist returns None."""
        engine = SemanticSearchEngine(mock_ai_config)
        file_info = {}

        result = engine._get_document_embedding("/nonexistent/file.py", file_info)

        assert result is None

    def test_get_document_embedding_when_generating_new_then_caches_result(
        self, mock_ai_config, mock_embedding_generator
    ):
        """Test generation and caching of new document embeddings."""
        engine = SemanticSearchEngine(mock_ai_config)
        engine.embedder = mock_embedding_generator
        file_info = {}

        # Mock file reading
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=TEST_FILE_CONTENT),
        ):
            mock_embedding_generator.generate_embeddings.return_value = {
                "success": True,
                "data": {"embeddings": MOCK_DOC_EMBEDDING_2},
            }

            result = engine._get_document_embedding(TEST_FILE_PATH_2, file_info)

            assert result == MOCK_DOC_EMBEDDING_2
            assert engine.embeddings_cache[TEST_FILE_PATH_2] == MOCK_DOC_EMBEDDING_2
            mock_embedding_generator.generate_embeddings.assert_called_once_with(
                TEST_FILE_CONTENT
            )

    def test_get_document_embedding_when_generation_fails_then_returns_none(
        self, mock_ai_config, mock_embedding_generator
    ):
        """Test returns None when embedding generation fails."""
        engine = SemanticSearchEngine(mock_ai_config)
        engine.embedder = mock_embedding_generator
        file_info = {}

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.read_text", return_value=TEST_FILE_CONTENT),
        ):
            mock_embedding_generator.generate_embeddings.return_value = {
                "success": False,
                "error": "Generation failed",
            }

            result = engine._get_document_embedding(TEST_FILE_PATH_2, file_info)

            assert result is None
            assert TEST_FILE_PATH_2 not in engine.embeddings_cache


class TestCosineSimilarityCalculation:
    """Test cosine similarity calculation."""

    def test_calculate_cosine_similarity_when_identical_vectors_then_returns_one(
        self, mock_ai_config
    ):
        """Test cosine similarity returns 1.0 for identical vectors."""
        engine = SemanticSearchEngine(mock_ai_config)
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [1.0, 2.0, 3.0]

        similarity = engine._calculate_cosine_similarity(vec1, vec2)

        assert abs(similarity - 1.0) < 1e-7

    def test_calculate_cosine_similarity_when_orthogonal_vectors_then_returns_zero(
        self, mock_ai_config
    ):
        """Test cosine similarity returns 0.0 for orthogonal vectors."""
        engine = SemanticSearchEngine(mock_ai_config)
        vec1 = [1.0, 0.0]
        vec2 = [0.0, 1.0]

        similarity = engine._calculate_cosine_similarity(vec1, vec2)

        assert abs(similarity - 0.0) < 1e-7

    def test_calculate_cosine_similarity_when_zero_vector_then_returns_zero(
        self, mock_ai_config
    ):
        """Test cosine similarity returns 0.0 when one vector is zero."""
        engine = SemanticSearchEngine(mock_ai_config)
        vec1 = [1.0, 2.0, 3.0]
        vec2 = [0.0, 0.0, 0.0]

        similarity = engine._calculate_cosine_similarity(vec1, vec2)

        assert similarity == 0.0

    def test_calculate_cosine_similarity_when_opposite_vectors_then_returns_negative_one(
        self, mock_ai_config
    ):
        """Test cosine similarity returns -1.0 for opposite vectors."""
        engine = SemanticSearchEngine(mock_ai_config)
        vec1 = [1.0, 0.0]
        vec2 = [-1.0, 0.0]

        similarity = engine._calculate_cosine_similarity(vec1, vec2)

        assert abs(similarity - (-1.0)) < 1e-7


class TestSemanticSearchResultFiltering:
    """Test search result filtering and ranking."""

    def test_search_when_no_documents_meet_threshold_then_returns_empty_results(
        self, mock_ai_config
    ):
        """Test search returns empty results when no documents meet similarity threshold."""
        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings.return_value = {
                "success": True,
                "data": {"embeddings": MOCK_QUERY_EMBEDDING},
            }
            mock_embedder_class.return_value = mock_embedder

            engine = SemanticSearchEngine(mock_ai_config)

            # Mock low similarity scores
            engine._get_document_embedding = Mock(return_value=MOCK_DOC_EMBEDDING_2)
            engine._calculate_cosine_similarity = Mock(
                return_value=LOW_SIMILARITY_SCORE
            )

            file_index_data = {"files": {TEST_FILE_PATH_1: {"type": "python"}}}

            result = engine.search(
                TEST_QUERY,
                file_index_data,
                similarity_threshold=TEST_SIMILARITY_THRESHOLD,
            )

            assert result["success"] is True
            assert len(result["data"]["search_results"]) == 0
            assert result["data"]["metadata"]["matches_found"] == 0

    def test_search_when_documents_meet_threshold_then_returns_ranked_results(
        self, mock_ai_config
    ):
        """Test search returns properly ranked results for documents meeting threshold."""
        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings.return_value = {
                "success": True,
                "data": {"embeddings": MOCK_QUERY_EMBEDDING},
            }
            mock_embedder_class.return_value = mock_embedder

            engine = SemanticSearchEngine(mock_ai_config)

            # Mock different similarity scores for ranking test
            similarities = {
                TEST_FILE_PATH_1: HIGH_SIMILARITY_SCORE,
                TEST_FILE_PATH_2: 0.8,
            }

            def mock_get_embedding(file_path, file_info):
                return (
                    MOCK_DOC_EMBEDDING_1
                    if file_path == TEST_FILE_PATH_1
                    else MOCK_DOC_EMBEDDING_2
                )

            def mock_calculate_similarity(query_emb, doc_emb):
                if doc_emb == MOCK_DOC_EMBEDDING_1:
                    return similarities[TEST_FILE_PATH_1]
                return similarities[TEST_FILE_PATH_2]

            engine._get_document_embedding = Mock(side_effect=mock_get_embedding)
            engine._calculate_cosine_similarity = Mock(
                side_effect=mock_calculate_similarity
            )

            file_index_data = {
                "files": {
                    TEST_FILE_PATH_1: {"type": "python"},
                    TEST_FILE_PATH_2: {"type": "python"},
                }
            }

            result = engine.search(
                TEST_QUERY,
                file_index_data,
                similarity_threshold=TEST_SIMILARITY_THRESHOLD,
            )

            assert result["success"] is True
            assert len(result["data"]["search_results"]) == 2
            # Verify results are sorted by similarity (highest first)
            assert (
                result["data"]["search_results"][0]["similarity"]
                == HIGH_SIMILARITY_SCORE
            )
            assert result["data"]["search_results"][1]["similarity"] == 0.8
            assert result["data"]["search_results"][0]["file_path"] == TEST_FILE_PATH_1

    def test_search_when_max_results_limit_then_respects_limit(self, mock_ai_config):
        """Test search respects max_results parameter."""
        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings.return_value = {
                "success": True,
                "data": {"embeddings": MOCK_QUERY_EMBEDDING},
            }
            mock_embedder_class.return_value = mock_embedder

            engine = SemanticSearchEngine(mock_ai_config)
            engine._get_document_embedding = Mock(return_value=MOCK_DOC_EMBEDDING_1)
            engine._calculate_cosine_similarity = Mock(
                return_value=HIGH_SIMILARITY_SCORE
            )

            # Create index with 3 files but limit to 2 results
            file_index_data = {
                "files": {
                    "/file1.py": {"type": "python"},
                    "/file2.py": {"type": "python"},
                    "/file3.py": {"type": "python"},
                }
            }

            result = engine.search(TEST_QUERY, file_index_data, max_results=2)

            assert result["success"] is True
            assert len(result["data"]["search_results"]) == 2
            assert (
                result["data"]["metadata"]["matches_found"] == 3
            )  # Total matches found
            assert (
                result["data"]["metadata"]["results_returned"] == 2
            )  # Results returned


class TestSemanticSearchMetadata:
    """Test search result metadata generation."""

    def test_search_when_successful_then_includes_complete_metadata(
        self, mock_ai_config, sample_file_index_data
    ):
        """Test search includes complete metadata in results."""
        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings.return_value = {
                "success": True,
                "data": {"embeddings": MOCK_QUERY_EMBEDDING},
            }
            mock_embedder_class.return_value = mock_embedder

            engine = SemanticSearchEngine(mock_ai_config)
            engine._get_document_embedding = Mock(return_value=MOCK_DOC_EMBEDDING_1)
            engine._calculate_cosine_similarity = Mock(
                return_value=HIGH_SIMILARITY_SCORE
            )

            result = engine.search(TEST_QUERY, sample_file_index_data)

            assert result["success"] is True
            metadata = result["data"]["metadata"]
            assert metadata["query"] == TEST_QUERY
            assert metadata["total_documents"] == 2
            assert metadata["documents_with_embeddings"] == 2
            assert metadata["matches_found"] == 2
            assert metadata["results_returned"] == 2
            assert metadata["similarity_threshold"] == 0.7  # Default threshold
            assert "search_time" in metadata


class TestPerformSemanticSearchFunction:
    """Test the main perform_semantic_search function."""

    @patch("spec_cli.ai.context.semantic_search.AIConfigLoader")
    @patch("spec_cli.ai.context.semantic_search.DocumentationDiscovery")
    @patch("spec_cli.ai.context.semantic_search.FileIndexManager")
    @patch("spec_cli.ai.context.semantic_search.SemanticSearchEngine")
    def test_perform_semantic_search_when_successful_then_returns_search_results(
        self,
        mock_search_engine_class,
        mock_file_index_class,
        mock_discovery_class,
        mock_config_loader_class,
    ):
        """Test perform_semantic_search coordinates all components successfully."""
        # Mock AI config loading
        mock_config_loader = Mock()
        mock_ai_config = Mock()
        mock_config_loader.load_ai_config.return_value = mock_ai_config
        mock_config_loader_class.return_value = mock_config_loader

        # Mock file discovery
        mock_discovery = Mock()
        mock_discovery_result = {
            "success": True,
            "data": {"successful_files": [TEST_FILE_PATH_1, TEST_FILE_PATH_2]},
        }
        mock_discovery.discover_documentation.return_value = mock_discovery_result
        mock_discovery_class.return_value = mock_discovery

        # Mock file index manager
        mock_file_index = Mock()
        mock_file_index.needs_rebuild.return_value = False
        mock_file_index.index_path = Mock()
        mock_file_index.index_path.read_text.return_value = json.dumps({"files": {}})
        mock_file_index_class.return_value = mock_file_index

        # Mock search engine
        mock_search_engine = Mock()
        mock_search_result = {
            "success": True,
            "data": {"search_results": [], "similarity_scores": [], "metadata": {}},
        }
        mock_search_engine.search.return_value = mock_search_result
        mock_search_engine_class.return_value = mock_search_engine

        result = perform_semantic_search(
            TEST_QUERY, TEST_MAX_RESULTS, TEST_SIMILARITY_THRESHOLD
        )

        assert result == mock_search_result
        mock_config_loader.load_ai_config.assert_called_once()
        mock_discovery.discover_documentation.assert_called_once()
        mock_search_engine.search.assert_called_once_with(
            TEST_QUERY, {"files": {}}, TEST_MAX_RESULTS, TEST_SIMILARITY_THRESHOLD
        )

    @patch("spec_cli.ai.context.semantic_search.AIConfigLoader")
    @patch("spec_cli.ai.context.semantic_search.DocumentationDiscovery")
    def test_perform_semantic_search_when_discovery_fails_then_returns_discovery_error(
        self, mock_discovery_class, mock_config_loader_class
    ):
        """Test perform_semantic_search handles discovery failures."""
        mock_config_loader = Mock()
        mock_config_loader_class.return_value = mock_config_loader

        mock_discovery = Mock()
        mock_discovery_result = {"success": False, "error": "Discovery failed"}
        mock_discovery.discover_documentation.return_value = mock_discovery_result
        mock_discovery_class.return_value = mock_discovery

        result = perform_semantic_search(TEST_QUERY)

        assert result == mock_discovery_result

    @patch("spec_cli.ai.context.semantic_search.AIConfigLoader")
    @patch("spec_cli.ai.context.semantic_search.DocumentationDiscovery")
    @patch("spec_cli.ai.context.semantic_search.FileIndexManager")
    def test_perform_semantic_search_when_index_rebuild_needed_then_rebuilds_index(
        self, mock_file_index_class, mock_discovery_class, mock_config_loader_class
    ):
        """Test perform_semantic_search rebuilds index when needed."""
        # Setup mocks
        mock_config_loader = Mock()
        mock_config_loader_class.return_value = mock_config_loader

        mock_discovery = Mock()
        mock_discovery_result = {
            "success": True,
            "data": {"successful_files": [TEST_FILE_PATH_1]},
        }
        mock_discovery.discover_documentation.return_value = mock_discovery_result
        mock_discovery_class.return_value = mock_discovery

        mock_file_index = Mock()
        mock_file_index.needs_rebuild.return_value = True
        mock_build_result = {"success": True}
        mock_file_index.build_file_index.return_value = mock_build_result
        mock_file_index.index_path = Mock()
        mock_file_index.index_path.read_text.return_value = json.dumps({"files": {}})
        mock_file_index_class.return_value = mock_file_index

        with patch("spec_cli.ai.context.semantic_search.SemanticSearchEngine"):
            perform_semantic_search(TEST_QUERY)

        mock_file_index.build_file_index.assert_called_once_with([TEST_FILE_PATH_1])


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_search_when_exception_during_processing_then_handles_gracefully(
        self, mock_ai_config, sample_file_index_data
    ):
        """Test search handles unexpected exceptions gracefully."""
        with patch(
            "spec_cli.ai.context.semantic_search.EmbeddingGenerator"
        ) as mock_embedder_class:
            mock_embedder = Mock()
            mock_embedder.generate_embeddings.side_effect = RuntimeError(
                "Unexpected error"
            )
            mock_embedder_class.return_value = mock_embedder

            engine = SemanticSearchEngine(mock_ai_config)
            result = engine.search(TEST_QUERY, sample_file_index_data)

            assert result["success"] is False
            assert "Semantic search failed" in result["error"]
            assert "Unexpected error" in result["error"]

    @patch("spec_cli.ai.context.semantic_search.AIConfigLoader")
    def test_perform_semantic_search_when_initialization_fails_then_returns_error(
        self, mock_config_loader_class
    ):
        """Test perform_semantic_search handles initialization failures."""
        mock_config_loader_class.side_effect = Exception("Config loading failed")

        result = perform_semantic_search(TEST_QUERY)

        assert result["success"] is False
        assert "Semantic search initialization failed" in result["error"]


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility requirements."""

    def test_get_document_embedding_when_different_path_separators_then_handles_correctly(
        self, mock_ai_config
    ):
        """Test document embedding handles different path separators correctly."""
        engine = SemanticSearchEngine(mock_ai_config)

        # Test with both forward and backslash paths
        windows_path = "C:\\project\\src\\auth.py"
        unix_path = "/project/src/auth.py"

        # Both should work and not cause issues
        file_info = {}

        result_windows = engine._get_document_embedding(windows_path, file_info)
        result_unix = engine._get_document_embedding(unix_path, file_info)

        # Both should return None for non-existent files without errors
        assert result_windows is None
        assert result_unix is None
