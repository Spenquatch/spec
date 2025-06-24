# Slice 2.2b: Context Extraction & Ranking

**Goal**: Implement context extraction and relevance ranking for AI agent consumption

**Slice Type**: AI Processing Engine

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -n "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/*.py | grep -E "(path|workflow)"`
- spec_cli/utils/workflow_utils.py → create_workflow_result() for result handling
- Create helper: spec_cli/ai/context/extractor.py → extract_relevant_context(files: List[Path], query: str, context_window: int) → "Extract relevant code snippets within token limits"
- Create helper: spec_cli/ai/context/ranking.py → rank_by_relevance(files: List[Path], query: str) → "Rank files by relevance using text similarity"

**Complexity Analysis:**
- Decision points: 6/7 (context extraction validation, token counting, ranking threshold, export format validation, error handling)
- Helper calls: 4 (extract_relevant_context, rank_by_relevance, create_workflow_result, token counting)
- McCabe validation: Pass (6 ≤ 7, under limit with helper usage)

**Inputs → Action → Outputs:**
- **Inputs**: {validated_params: Dict[str, Any], file_list: List[Path], project_metadata: Dict[str, Any]} (from Slice 2.2a)
- **Action**:
  1. Extract relevant context from files using context extraction helper (decision point + try/except)
  2. Count tokens to ensure context window compliance (decision point)
  3. Rank files by relevance to query using ranking helper (decision point + try/except)
  4. Filter results by relevance threshold (decision point)
  5. Generate structured export format for AI consumption (decision point)
  6. Combine with metadata from 2.2a for final output (try/except)
- **Outputs**: {context_data: Dict[str, Any], ranked_files: List[Dict], metadata: Dict[str, Any]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/ai/context/extractor.py (new - context extraction helper)
- spec_cli/ai/context/ranking.py (new - relevance ranking helper)

**Dependencies**:
- Receives validated parameters and file list from Slice 2.2a
- Uses existing workflow helpers for result handling
- No external integrations (internal text processing only)

**Classes**: 2 (ContextExtractor, RelevanceRanker)
**External Integrations**: 0 (internal processing only)

**Test Requirements:**
- **Unit Tests**: Context extraction with various file types, relevance ranking accuracy, token counting validation, export format validation
- **Integration Test**: End-to-end context extraction and ranking with real code files
- **Idempotent Tests**: Consistent ranking results for same inputs
- **Mocks/Fixtures**: Sample code files, query-relevance pairs, token counting scenarios

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions (achieved: 6/7)
- Performance: Context extraction and ranking complete within 8 seconds for large codebases

**Integration Validation:**
Receive file list and validated parameters from Slice 2.2a, extract relevant context, rank by relevance, and return structured data suitable for AI agent consumption.

**Expected Implementation Pattern:**
```python
class ContextExtractor:
    """Extract relevant context from source code files."""

    def extract_relevant_context(self, files: List[Path], query: str, context_window: int) -> Dict[str, Any]:
        """Extract context snippets within token limits."""
        try:
            extracted_context = {}
            total_tokens = 0

            for file_path in files:
                # Extract relevant snippets (decision point 1)
                if total_tokens >= context_window:
                    break

                snippets = self._extract_file_snippets(file_path, query)

                # Count tokens (decision point 2)
                snippet_tokens = self._count_tokens(snippets)
                if total_tokens + snippet_tokens <= context_window:
                    extracted_context[str(file_path)] = snippets
                    total_tokens += snippet_tokens

            return {
                "extracted_context": extracted_context,
                "total_tokens": total_tokens,
                "files_processed": len(extracted_context)
            }

        except Exception as e:  # try/except block
            raise ContextExtractionError(f"Context extraction failed: {e}") from e

class RelevanceRanker:
    """Rank files by relevance to query."""

    def rank_by_relevance(self, files: List[Path], query: str) -> List[Dict[str, Any]]:
        """Rank files using text similarity algorithms."""
        try:
            ranked_files = []

            for file_path in files:
                # Calculate relevance score (decision point 3)
                relevance_score = self._calculate_relevance(file_path, query)

                # Apply relevance threshold (decision point 4)
                if relevance_score >= 0.1:  # Minimum relevance threshold
                    ranked_files.append({
                        "file_path": str(file_path),
                        "relevance_score": relevance_score,
                        "file_type": file_path.suffix
                    })

            # Sort by relevance score (decision point 5)
            ranked_files.sort(key=lambda x: x["relevance_score"], reverse=True)

            return ranked_files

        except Exception as e:  # try/except block
            raise RankingError(f"File ranking failed: {e}") from e

def process_agent_scope_context(validated_params: Dict, file_list: List[Path], project_metadata: Dict) -> WorkflowResult:
    """Main processing function combining extraction and ranking."""
    try:
        # Extract context using helper (decision point + try/except)
        extractor = ContextExtractor()
        context_data = extractor.extract_relevant_context(
            file_list,
            validated_params["query"],
            validated_params["context_window"]
        )

        # Rank files using helper (decision point + try/except)
        ranker = RelevanceRanker()
        ranked_files = ranker.rank_by_relevance(file_list, validated_params["query"])

        # Generate final export format (decision point)
        export_data = {
            "query": validated_params["query"],
            "context_window": validated_params["context_window"],
            "context_data": context_data["extracted_context"],
            "ranked_files": ranked_files,
            "metadata": {
                **project_metadata,
                "extraction_time": datetime.now().isoformat(),
                "total_tokens_used": context_data["total_tokens"],
                "relevance_threshold": 0.1
            }
        }

        return create_workflow_result(
            success=True,
            data=export_data,
            message=f"Extracted context with {len(ranked_files)} relevant files"
        )

    except Exception as e:  # try/except block
        return create_workflow_result(
            success=False,
            error=f"Context processing failed: {str(e)}"
        )
```

This sub-slice handles the complex context extraction and ranking logic while staying within complexity limits through helper function usage and focused responsibility.
