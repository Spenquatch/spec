# Slice 2.2: Agent Scope Command

**Goal**: Implement `spec agent-scope` command for AI context extraction and export for AI-to-AI workflows

**Slice Type**: Integration

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -n "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/*.py | grep -E "(path|workflow|platform)"`
- spec_cli/utils/path_utils.py → resolve_project_root(), is_subpath(), safe_relative_to() for context discovery
- spec_cli/utils/workflow_utils.py → create_workflow_result() for command result handling
- spec_cli/utils/platform_utils.py → get_environment_info() for system context
- spec_cli/cli/commands/base.py → BaseCommand (existing command pattern)
- Create helper: spec_cli/ai/context/extractor.py → extract_relevant_context(query: str, context_window: int) → "Extract and rank relevant code context"
- Create helper: spec_cli/ai/context/ranking.py → rank_by_relevance(files: List[Path], query: str) → "Rank files by relevance to query"

**Complexity Analysis:**
- Decision points: 7/7 (if query_provided, if context_window_valid, if files_found, if context_extracted, try/except blocks)
- Helper calls: 5 (resolve_project_root, extract_relevant_context, rank_by_relevance, create_workflow_result, get_environment_info)
- McCabe validation: Pass (7 ≤ 7, at the limit but acceptable)

**Inputs → Action → Outputs:**
- **Inputs**: {query: str, context_window: int, exclude_patterns: List[str]}
- **Action**:
  1. Resolve project root using path helper (decision point + try/except)
  2. Validate context window limits (decision point)
  3. Discover relevant files using path helpers (decision point)
  4. Extract context using AI context helper (decision point + try/except)
  5. Rank files by relevance to query using ranking helper (decision point)
  6. Generate structured output for AI consumption (decision point)
  7. Export context with metadata using workflow helper (try/except)
- **Outputs**: {context_data: Dict[str, Any], metadata: Dict[str, Any]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/cli/commands/agent_scope.py (new - main command implementation)
- spec_cli/ai/context/extractor.py (new - context extraction helper)
- spec_cli/ai/context/ranking.py (new - relevance ranking helper)

**Test Requirements:**
- **Unit Tests**: Test command parsing, context extraction, file ranking, error handling for invalid queries, context window limits
- **Integration Test**: End-to-end test with real codebase, verify exported context is valid JSON and usable by AI agents
- **Idempotent Tests**: All tests must pass consistently on repeated runs
- **Mocks/Fixtures**: Sample project structure, mock file content, query fixtures, context window test cases

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions
- Performance: Context extraction completes within 10 seconds for large codebases

**Integration Validation:**
Run `spec agent-scope --query "authentication implementation" --context-window 8000` on a real codebase, verify that it exports structured JSON with relevant files, code snippets, and metadata that can be consumed by AI agents for intelligent context understanding.

**AI Agent Execution Notes:**
This command is core to AI-to-AI workflows. The exported context must be structured for AI consumption with clear metadata, relevance scores, and file relationships. Focus on efficient file discovery and ranking algorithms. Ensure the output format is standardized for AI agent consumption. Use existing path helpers for cross-platform compatibility.

**Expected Implementation Pattern:**
```python
class AgentScopeCommand(BaseCommand):
    """Extract and export relevant codebase context for AI agents."""

    def execute(self, query: str, context_window: int = 8000, exclude: List[str] = None) -> WorkflowResult:
        """Execute agent scope extraction."""
        try:
            # Resolve project root using helper
            project_root = resolve_project_root()

            # Validate context window
            if context_window <= 0 or context_window > 32000:
                return create_workflow_result(
                    success=False,
                    error="Context window must be between 1 and 32000 tokens"
                )

            # Extract relevant context using helper
            extractor = ContextExtractor(project_root)
            context_data = extractor.extract_relevant_context(query, context_window)

            # Rank files by relevance using helper
            ranker = RelevanceRanker()
            ranked_files = ranker.rank_by_relevance(context_data.files, query)

            # Generate structured output
            export_data = {
                "query": query,
                "context_window": context_window,
                "files": ranked_files,
                "metadata": {
                    "project_root": str(project_root),
                    "extraction_time": datetime.now().isoformat(),
                    "total_files": len(ranked_files),
                    "environment": get_environment_info()
                }
            }

            return create_workflow_result(
                success=True,
                data=export_data,
                message=f"Extracted context for '{query}' with {len(ranked_files)} relevant files"
            )

        except Exception as e:
            return create_workflow_result(
                success=False,
                error=f"Agent scope extraction failed: {str(e)}"
            )
```

This slice enables AI agents to intelligently extract and share relevant codebase context, forming the foundation for AI-to-AI development workflows.
