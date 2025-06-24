# Slice 4.1b: Semantic Embeddings & Search

**Goal**: Implement AI-powered semantic search using Qwen3-Emb-0.6B embeddings and vector similarity

**Slice Type**: AI/ML Search Engine

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -n "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/*.py | grep -E "(platform|workflow)"`
- spec_cli/utils/platform_utils.py → get_gpu_capabilities() for embedding computation device selection
- spec_cli/utils/workflow_utils.py → create_workflow_result() for result handling
- spec_cli/ai/config/loader.py → ConfigLoader (existing, from slice 1b)
- Results from Slice 4.1a for file index and discovered documentation (FileIndexManager, DocumentationDiscovery)
- Create helper: spec_cli/ai/context/embeddings.py → generate_embeddings(text: str) → "Generate vector embeddings using Qwen3-Emb-0.6B model"

**Complexity Analysis:**
- Decision points: 6/7 (embeddings_available, gpu_available, similarity_threshold, result_filtering, error handling)
- Helper calls: 5 (get_gpu_capabilities, generate_embeddings, ConfigLoader.load_ai_config, create_workflow_result, vector similarity)
- McCabe validation: Pass (6 ≤ 7, under limit)

**Inputs → Action → Outputs:**
- **Inputs**: {query: str, max_results: int, similarity_threshold: float, file_index_data: Dict} (from Slice 4.1a)
- **Action**:
  1. Load AI configuration and validate embedding capabilities (decision point + try/except)
  2. Check GPU availability for faster embedding generation (decision point)
  3. Generate query embeddings using AI helper (decision point + try/except)
  4. Generate or load cached embeddings for indexed documents (decision point + try/except)
  5. Calculate vector similarities and rank results (decision point)
  6. Filter results by similarity threshold and return top matches (try/except)
- **Outputs**: {search_results: List[SearchResult], similarity_scores: List[float], metadata: Dict[str, Any]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/ai/context/embeddings.py (new - text embedding generation helper)
- spec_cli/ai/context/semantic_search.py (new - semantic search engine using embeddings)

**Dependencies**:
- Receives file index and discovered files from Slice 4.1a (FileIndexManager, DocumentationDiscovery)
- Uses existing AI configuration from slice 1b
- Leverages search index core from Slice 4.1a (.spec/search_index.json)
- Qwen3-Emb-0.6B model for embedding generation (complements existing Qwen2.5-Coder)

**Classes**: 2 (EmbeddingGenerator, SemanticSearchEngine)
**External Integrations**: 1 (Qwen3-Emb-0.6B embedding model via HuggingFace transformers)

**Test Requirements:**
- **Unit Tests**: Embedding generation, vector similarity calculation, search ranking, threshold filtering, GPU/CPU fallback
- **Integration Test**: End-to-end semantic search with real documentation, compare semantic vs keyword search quality
- **Idempotent Tests**: Consistent similarity scores for same queries
- **Mocks/Fixtures**: Pre-computed embeddings, similarity test cases, GPU availability scenarios

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions (achieved: 6/7)
- Performance: Semantic search completes within 5 seconds for typical documentation sets

**Integration Validation:**
Use FileIndexManager and DocumentationDiscovery from Slice 4.1a, extend search index with Qwen3-Emb-0.6B embeddings, perform semantic similarity search, and return ranked results that demonstrate semantic understanding beyond keyword matching. Results should integrate seamlessly with existing file index structure.

**Expected Implementation Pattern:**
```python
class EmbeddingGenerator:
    """Generate text embeddings using Qwen3-Emb-0.6B model."""

    def __init__(self, ai_config: AIConfig):
        self.ai_config = ai_config
        self.device = self._select_device()
        self.model_name = "Qwen/Qwen3-Emb-0.6B"
        self.model = None
        self.tokenizer = None

    def _select_device(self) -> str:
        """Select best available device for embedding generation."""
        # Check GPU availability (decision point 1)
        gpu_info = get_gpu_capabilities()
        if gpu_info.get("cuda_available", False):
            return "cuda"
        elif gpu_info.get("mps_available", False):  # Apple Silicon
            return "mps"
        else:
            return "cpu"

    def _load_model(self) -> bool:
        """Load Qwen3-Emb-0.6B model if not already loaded."""
        try:
            if self.model is None:
                from transformers import AutoModel, AutoTokenizer
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(
                    self.model_name,
                    trust_remote_code=True,
                    device_map=self.device if self.device != "cpu" else None
                )
                if self.device == "cpu":
                    self.model = self.model.to("cpu")
            return True
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return False

    def generate_embeddings(self, text: str) -> WorkflowResult:
        """Generate vector embeddings for text content using Qwen3-Emb-0.6B."""
        try:
            # Validate AI configuration (decision point 2)
            if not self.ai_config.enabled:
                return create_workflow_result(
                    success=False,
                    error="AI embeddings disabled in configuration"
                )

            # Load model if needed (decision point 3 + try/except)
            if not self._load_model():
                return create_workflow_result(
                    success=False,
                    error="Failed to load Qwen3-Emb-0.6B embedding model"
                )

            # Generate embeddings using Qwen3-Emb-0.6B
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden states for sentence embedding
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()

            return create_workflow_result(
                success=True,
                data={
                    "embeddings": embeddings.tolist(),
                    "text_length": len(text),
                    "device_used": self.device,
                    "model_name": self.model_name,
                    "embedding_dimension": len(embeddings),
                    "generation_time": datetime.now().isoformat()
                },
                message=f"Generated embeddings on {self.device} using {self.model_name}"
            )

        except Exception as e:  # try/except block
            return create_workflow_result(
                success=False,
                error=f"Embedding generation failed: {str(e)}"
            )

class SemanticSearchEngine:
    """AI-powered semantic search using vector embeddings."""

    def __init__(self, ai_config: AIConfig):
        self.ai_config = ai_config
        self.embedder = EmbeddingGenerator(ai_config)
        self.embeddings_cache = {}

    def search(self, query: str, file_index_data: Dict, max_results: int = 10,
               similarity_threshold: float = 0.7) -> WorkflowResult:
        """Perform semantic search over documentation."""
        try:
            # Generate query embedding (decision point 4 + try/except)
            query_result = self.embedder.generate_embeddings(query)
            if not query_result.success:
                return create_workflow_result(
                    success=False,
                    error=f"Query embedding failed: {query_result.error}"
                )

            query_embedding = query_result.data["embeddings"]

            # Generate or load document embeddings (decision point 5)
            doc_similarities = []
            for file_path, file_info in file_index_data["files"].items():
                doc_embedding = self._get_document_embedding(file_path, file_info)
                if doc_embedding is not None:
                    similarity = self._calculate_cosine_similarity(query_embedding, doc_embedding)
                    doc_similarities.append({
                        "file_path": file_path,
                        "similarity": similarity,
                        "file_info": file_info
                    })

            # Filter and rank by similarity (decision point 6)
            filtered_results = [
                result for result in doc_similarities
                if result["similarity"] >= similarity_threshold
            ]

            # Sort by similarity descending
            filtered_results.sort(key=lambda x: x["similarity"], reverse=True)
            top_results = filtered_results[:max_results]

            search_metadata = {
                "query": query,
                "total_documents": len(file_index_data["files"]),
                "matches_found": len(filtered_results),
                "results_returned": len(top_results),
                "similarity_threshold": similarity_threshold,
                "search_time": datetime.now().isoformat()
            }

            return create_workflow_result(
                success=True,
                data={
                    "search_results": top_results,
                    "similarity_scores": [r["similarity"] for r in top_results],
                    "metadata": search_metadata
                },
                message=f"Found {len(top_results)} semantically similar documents"
            )

        except Exception as e:  # try/except block
            return create_workflow_result(
                success=False,
                error=f"Semantic search failed: {str(e)}"
            )

    def _get_document_embedding(self, file_path: str, file_info: Dict) -> Optional[List[float]]:
        """Get cached or generate document embedding."""
        # Check if embedding exists in file_info from index (persistent storage)
        if "embeddings" in file_info:
            return file_info["embeddings"]

        # Check runtime cache
        if file_path in self.embeddings_cache:
            return self.embeddings_cache[file_path]

        try:
            # Read full document content
            content = Path(file_path).read_text(encoding='utf-8')

            # Generate embedding using Qwen3-Emb-0.6B
            embedding_result = self.embedder.generate_embeddings(content)
            if embedding_result.success:
                embedding = embedding_result.data["embeddings"]
                self.embeddings_cache[file_path] = embedding

                # Note: In production, embeddings should be persisted back to the search index
                # This would be handled by extending FileIndexManager to store embeddings
                return embedding

        except Exception as e:
            logger.warning(f"Failed to generate embedding for {file_path}: {e}")

        return None

    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        import numpy as np

        # Convert to numpy arrays for efficient computation
        v1 = np.array(vec1)
        v2 = np.array(vec2)

        # Calculate cosine similarity
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)

        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0

        return dot_product / (norm_v1 * norm_v2)

def perform_semantic_search(query: str, max_results: int = 10,
                           similarity_threshold: float = 0.7) -> WorkflowResult:
    """Main semantic search function combining file index from 4.1a and Qwen3-Emb embeddings."""
    try:
        # Load AI configuration (decision point + try/except)
        config_loader = ConfigLoader()
        ai_config = config_loader.load_ai_config()

        # Use FileIndexManager and DocumentationDiscovery from Slice 4.1a
        file_discovery = DocumentationDiscovery()
        discovery_result = file_discovery.discover_documentation()

        if not discovery_result.success:
            return discovery_result

        file_index_manager = FileIndexManager()
        if file_index_manager.needs_rebuild():
            # Build fresh index including files for embedding generation
            index_result = file_index_manager.build_file_index(
                discovery_result["successful_files"]
            )
            if not index_result.success:
                return index_result
            file_index_data = json.loads(file_index_manager.index_path.read_text())
        else:
            # Load existing search index from .spec/search_index.json
            file_index_data = json.loads(file_index_manager.index_path.read_text())

        # Perform semantic search with Qwen3-Emb-0.6B embeddings
        search_engine = SemanticSearchEngine(ai_config)
        return search_engine.search(query, file_index_data, max_results, similarity_threshold)

    except Exception as e:  # try/except block
        return create_workflow_result(
            success=False,
            error=f"Semantic search initialization failed: {str(e)}"
        )
```

This sub-slice focuses on the AI/ML complexity of Qwen3-Emb-0.6B embedding generation and semantic similarity search while leveraging and extending the clean file index foundation from slice 4.1a. The design maintains compatibility with existing search index structure while adding semantic capabilities through embeddings stored alongside traditional file metadata.
