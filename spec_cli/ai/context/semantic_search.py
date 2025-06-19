"""AI-powered semantic search using vector embeddings.

This module provides semantic search functionality using Qwen3-Emb-0.6B embeddings
to find semantically similar documentation based on vector similarity.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from spec_cli.ai.config.loader import AIConfigLoader
from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.context.embeddings import EmbeddingGenerator
from spec_cli.ai.context.file_discovery import DocumentationDiscovery
from spec_cli.ai.context.search_index import FileIndexManager
from spec_cli.ai.providers.manager import create_workflow_result
from spec_cli.utils.workflow_utils import WorkflowResult

# Import numpy conditionally for type checking and runtime
if TYPE_CHECKING:
    import numpy as np_module  # type: ignore[import-not-found,unused-ignore]
else:
    try:
        import numpy as np_module  # type: ignore[import-not-found,unused-ignore]
    except ImportError:
        np_module = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)


class SemanticSearchEngine:
    """AI-powered semantic search using vector embeddings."""

    def __init__(self, ai_config: AIConfig) -> None:
        """Initialize semantic search engine with AI configuration.

        Args:
            ai_config: AI configuration settings
        """
        self.ai_config = ai_config
        self.embedder = EmbeddingGenerator(ai_config)
        self.embeddings_cache: dict[str, list[float]] = {}
        logger.info("Initialized SemanticSearchEngine")

    def search(
        self,
        query: str,
        file_index_data: dict[str, Any],
        max_results: int = 10,
        similarity_threshold: float = 0.7,
    ) -> WorkflowResult:
        """Perform semantic search over documentation.

        Args:
            query: Search query text
            file_index_data: File index data from FileIndexManager
            max_results: Maximum number of results to return
            similarity_threshold: Minimum similarity score (0-1)

        Returns:
            WorkflowResult containing search results and metadata
        """
        try:
            # Validate inputs
            if not query or not query.strip():
                return create_workflow_result(
                    success=False, error="Empty query provided for semantic search"
                )

            if "files" not in file_index_data:
                return create_workflow_result(
                    success=False, error="Invalid file index data: missing 'files' key"
                )

            # Generate query embedding (decision point 4 + try/except)
            logger.info("Generating query embedding for: %s", query)
            query_result = self.embedder.generate_embeddings(query)
            if not query_result["success"]:
                return create_workflow_result(
                    success=False,
                    error=f"Query embedding failed: {query_result.get('error', 'Unknown error')}",
                )

            query_embedding = query_result["data"]["embeddings"]

            # Generate or load document embeddings (decision point 5)
            logger.info(
                "Computing similarities for %d files", len(file_index_data["files"])
            )
            doc_similarities = []
            for file_path, file_info in file_index_data["files"].items():
                doc_embedding = self._get_document_embedding(file_path, file_info)
                if doc_embedding is not None:
                    similarity = self._calculate_cosine_similarity(
                        query_embedding, doc_embedding
                    )
                    doc_similarities.append(
                        {
                            "file_path": file_path,
                            "similarity": similarity,
                            "file_info": file_info,
                        }
                    )

            # Filter and rank by similarity (decision point 6)
            filtered_results = [
                result
                for result in doc_similarities
                if result["similarity"] >= similarity_threshold
            ]

            # Sort by similarity descending
            filtered_results.sort(key=lambda x: x["similarity"], reverse=True)
            top_results = filtered_results[:max_results]

            search_metadata = {
                "query": query,
                "total_documents": len(file_index_data["files"]),
                "documents_with_embeddings": len(doc_similarities),
                "matches_found": len(filtered_results),
                "results_returned": len(top_results),
                "similarity_threshold": similarity_threshold,
                "search_time": datetime.now().isoformat(),
            }

            logger.info(
                "Semantic search completed: %d results from %d documents",
                len(top_results),
                len(doc_similarities),
            )

            return create_workflow_result(
                success=True,
                data={
                    "search_results": top_results,
                    "similarity_scores": [r["similarity"] for r in top_results],
                    "metadata": search_metadata,
                },
                message=f"Found {len(top_results)} semantically similar documents",
            )

        except Exception as e:  # try/except block
            logger.error("Semantic search failed: %s", e)
            return create_workflow_result(
                success=False, error=f"Semantic search failed: {str(e)}"
            )

    def _get_document_embedding(
        self, file_path: str, file_info: dict[str, Any]
    ) -> list[float] | None:
        """Get cached or generate document embedding.

        Args:
            file_path: Path to the document file
            file_info: File information from index

        Returns:
            Embedding vector or None if generation fails
        """
        # Check if embedding exists in file_info from index (persistent storage)
        if "embeddings" in file_info:
            return list(file_info["embeddings"])

        # Check runtime cache
        if file_path in self.embeddings_cache:
            return self.embeddings_cache[file_path]

        try:
            # Read document content
            content_path = Path(file_path)
            if not content_path.exists():
                logger.warning("File not found for embedding generation: %s", file_path)
                return None

            content = content_path.read_text(encoding="utf-8")

            # Generate embedding using Qwen3-Emb-0.6B
            embedding_result = self.embedder.generate_embeddings(content)
            if embedding_result["success"]:
                embedding = list(embedding_result["data"]["embeddings"])
                self.embeddings_cache[file_path] = embedding

                # Note: In production, embeddings should be persisted back to the search index
                # This would be handled by extending FileIndexManager to store embeddings
                logger.debug("Generated embedding for %s", file_path)
                return embedding

        except Exception as e:
            logger.warning("Failed to generate embedding for %s: %s", file_path, e)

        return None

    def _calculate_cosine_similarity(
        self, vec1: list[float], vec2: list[float]
    ) -> float:
        """Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score between 0 and 1
        """
        if np_module is None:
            raise ImportError("NumPy is required for similarity calculations")
        np = np_module

        # Convert to numpy arrays for efficient computation
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0

        return float(dot_product / (norm_v1 * norm_v2))


def perform_semantic_search(
    query: str, max_results: int = 10, similarity_threshold: float = 0.7
) -> WorkflowResult:
    """Perform semantic search combining file index from 4.1a and Qwen3-Emb embeddings.

    Args:
        query: Search query text
        max_results: Maximum number of results to return
        similarity_threshold: Minimum similarity score (0-1)

    Returns:
        WorkflowResult containing search results or error information
    """
    try:
        # Load AI configuration (decision point + try/except)
        config_loader = AIConfigLoader()
        ai_config = config_loader.load_ai_config()

        # Use FileIndexManager and DocumentationDiscovery from Slice 4.1a
        file_discovery = DocumentationDiscovery()
        discovery_result = file_discovery.discover_documentation()

        if not discovery_result["success"]:
            return discovery_result

        file_index_manager = FileIndexManager()
        if file_index_manager.needs_rebuild():
            # Build fresh index including files for embedding generation
            logger.info("Building fresh file index for semantic search")
            index_result = file_index_manager.build_file_index(
                discovery_result["data"]["successful_files"]
            )
            if not index_result["success"]:
                return index_result
            file_index_data = json.loads(file_index_manager.index_path.read_text())
        else:
            # Load existing search index from .spec/search_index.json
            logger.info(
                "Loading existing file index from %s", file_index_manager.index_path
            )
            file_index_data = json.loads(file_index_manager.index_path.read_text())

        # Perform semantic search with Qwen3-Emb-0.6B embeddings
        search_engine = SemanticSearchEngine(ai_config)
        return search_engine.search(
            query, file_index_data, max_results, similarity_threshold
        )

    except Exception as e:  # try/except block
        logger.error("Semantic search initialization failed: %s", e)
        return create_workflow_result(
            success=False, error=f"Semantic search initialization failed: {str(e)}"
        )
