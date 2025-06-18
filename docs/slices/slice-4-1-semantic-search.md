# Slice 4.1: Semantic Search

**Goal**: Implement AI-powered semantic search over existing documentation for intelligent content discovery

**Slice Type**: Component

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -n "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/*.py | grep -E "(path|platform)"`
- spec_cli/utils/path_utils.py → resolve_project_root(), is_specs_path() for documentation discovery
- spec_cli/utils/platform_utils.py → get_gpu_capabilities() for embedding computation device
- spec_cli/ai/config/loader.py → ConfigLoader (existing, from slice 1b)
- spec_cli/ai/providers/base.py → AIProvider interface (existing, from slice 2a)
- Create helper: spec_cli/ai/context/embeddings.py → generate_embeddings(text: str) → "Generate vector embeddings for text content"
- Create helper: spec_cli/ai/context/search_index.py → build_search_index(docs: List[Path]) → "Build searchable index from documentation"

**Complexity Analysis:**
- Decision points: 5/7 (if docs_found, if index_exists, if embeddings_available, try/except blocks)
- Helper calls: 4 (resolve_project_root, get_gpu_capabilities, generate_embeddings, build_search_index)
- McCabe validation: Pass (5 ≤ 7)

**Inputs → Action → Outputs:**
- **Inputs**: {query: str, max_results: int, similarity_threshold: float}
- **Action**:
  1. Discover documentation files using path helpers (decision point + try/except)
  2. Check if search index exists or needs rebuilding (decision point)
  3. Generate query embeddings using AI helper (decision point + try/except)
  4. Search index for similar content using vector similarity (decision point)
  5. Rank and filter results by similarity threshold (decision point)
- **Outputs**: {results: List[SearchResult], metadata: Dict[str, Any]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/ai/context/search.py (new - main semantic search implementation)
- spec_cli/ai/context/embeddings.py (new - text embedding helper)
- spec_cli/ai/context/search_index.py (new - search index management helper)

**Test Requirements:**
- **Unit Tests**: Test query processing, embedding generation, similarity search, index building, error handling for missing docs
- **Integration Test**: End-to-end test with real documentation, verify semantic search finds relevant content better than keyword search
- **Idempotent Tests**: All tests must pass consistently on repeated runs
- **Mocks/Fixtures**: Sample documentation files, pre-computed embeddings, query fixtures, similarity test cases

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions
- Performance: Search completes within 2 seconds for typical documentation set

**Integration Validation:**
Build documentation index, run semantic search with query like "authentication flow", verify results include relevant docs ranked by semantic similarity. Compare results with keyword search to demonstrate improved relevance. Test with different query types (technical terms, natural language, code concepts).

**AI Agent Execution Notes:**
This slice is optional but provides significant value for large codebases. Focus on efficient vector similarity search and caching of embeddings. The search should understand semantic relationships (e.g., "auth" and "authentication" should be similar). Consider using lightweight embedding models for performance. Ensure graceful degradation when AI dependencies are missing.

**Expected Implementation Pattern:**
```python
class SemanticSearchEngine:
    """AI-powered semantic search over documentation."""

    def __init__(self, config: AIConfig):
        self.config = config
        self.embedder = EmbeddingGenerator(config)
        self.index = SearchIndex()

    def search(self, query: str, max_results: int = 10,
               similarity_threshold: float = 0.7) -> SearchResult:
        """Perform semantic search over documentation."""
        try:
            # Discover documentation using path helpers
            project_root = resolve_project_root()
            docs_path = project_root / ".specs"

            if not docs_path.exists():
                return SearchResult(
                    success=False,
                    error="No documentation found - run 'spec gen' first"
                )

            # Ensure search index is built
            if not self.index.exists() or self.index.needs_rebuild():
                doc_files = self._discover_documentation(docs_path)
                self.index.build_search_index(doc_files)

            # Generate query embedding
            query_embedding = self.embedder.generate_embeddings(query)

            # Search for similar content
            similar_docs = self.index.find_similar(
                query_embedding,
                max_results,
                similarity_threshold
            )

            return SearchResult(
                success=True,
                results=similar_docs,
                metadata={
                    "query": query,
                    "total_results": len(similar_docs),
                    "search_time": time.time() - start_time
                }
            )

        except Exception as e:
            return SearchResult(
                success=False,
                error=f"Semantic search failed: {str(e)}"
            )

    def _discover_documentation(self, docs_path: Path) -> List[Path]:
        """Discover all documentation files for indexing."""
        doc_files = []
        for file_path in docs_path.rglob("*.md"):
            if is_specs_path(file_path):
                doc_files.append(file_path)
        return doc_files
```

This slice enables intelligent content discovery that goes beyond keyword matching to understand semantic relationships in documentation.
