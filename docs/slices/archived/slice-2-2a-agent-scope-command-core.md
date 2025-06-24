# Slice 2.2a: Agent Scope Command Core

**Goal**: Implement `spec agent-scope` command interface with basic file discovery and validation

**Slice Type**: Command Interface

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -n "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/*.py | grep -E "(path|workflow|platform)"`
- spec_cli/utils/path_utils.py → resolve_project_root(), is_subpath(), safe_relative_to() for file discovery
- spec_cli/utils/workflow_utils.py → create_workflow_result() for command result handling
- spec_cli/utils/platform_utils.py → get_environment_info() for system context
- spec_cli/cli/commands/base.py → BaseCommand (existing command pattern)
- No new helpers created (uses existing utilities)

**Complexity Analysis:**
- Decision points: 5/7 (query validation, context window validation, file discovery, error handling blocks)
- Helper calls: 4 (resolve_project_root, create_workflow_result, get_environment_info, file discovery)
- McCabe validation: Pass (5 ≤ 7, well under limit)

**Inputs → Action → Outputs:**
- **Inputs**: {query: str, context_window: int, exclude_patterns: List[str]}
- **Action**:
  1. Validate query is not empty (decision point)
  2. Validate context window limits between 1-32000 (decision point)
  3. Resolve project root using path helper (decision point + try/except)
  4. Discover relevant files using path helpers and exclusion patterns (decision point)
  5. Prepare file list for context extraction by Slice 2.2b (try/except)
- **Outputs**: {validated_params: Dict[str, Any], file_list: List[Path], project_metadata: Dict[str, Any]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/cli/commands/agent_scope.py (new - command interface only)

**Dependencies**:
- Results passed to Slice 2.2b for context extraction and ranking
- Uses existing helper functions from /src/utils/

**Classes**: 1 (AgentScopeCommand only)
**External Integrations**: 0 (internal file system operations only)

**Test Requirements:**
- **Unit Tests**: Command argument parsing, input validation, file discovery with exclusion patterns, error handling for invalid inputs
- **Integration Test**: File discovery across different project structures
- **Idempotent Tests**: Consistent file discovery results on repeated runs
- **Mocks/Fixtures**: Sample project structures, invalid input cases, permission error scenarios

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions (achieved: 5/7)
- Performance: File discovery completes within 2 seconds for large codebases

**Integration Validation:**
Run `spec agent-scope --query "test" --context-window 1000` and verify it discovers files correctly and passes validated parameters to context extraction layer.

**Expected Implementation Pattern:**
```python
class AgentScopeCommand(BaseCommand):
    """Extract and export relevant codebase context for AI agents."""

    def execute(self, query: str, context_window: int = 8000, exclude: List[str] = None) -> WorkflowResult:
        """Execute agent scope command with validation and file discovery."""
        try:
            # Validate query (decision point 1)
            if not query or not query.strip():
                return create_workflow_result(
                    success=False,
                    error="Query cannot be empty"
                )

            # Validate context window (decision point 2)
            if context_window <= 0 or context_window > 32000:
                return create_workflow_result(
                    success=False,
                    error="Context window must be between 1 and 32000 tokens"
                )

            # Resolve project root (decision point 3 + try/except)
            project_root = resolve_project_root()
            if not project_root.exists():
                return create_workflow_result(
                    success=False,
                    error=f"Project root not found: {project_root}"
                )

            # Discover files with exclusions (decision point 4)
            file_list = self._discover_files(project_root, exclude or [])
            if not file_list:
                return create_workflow_result(
                    success=False,
                    error="No relevant files found in project"
                )

            # Prepare validated parameters for context extraction
            validated_params = {
                "query": query.strip(),
                "context_window": context_window,
                "exclude_patterns": exclude or [],
                "project_root": project_root
            }

            project_metadata = {
                "project_root": str(project_root),
                "total_files_discovered": len(file_list),
                "environment": get_environment_info()
            }

            return create_workflow_result(
                success=True,
                data={
                    "validated_params": validated_params,
                    "file_list": file_list,
                    "project_metadata": project_metadata
                },
                message=f"Discovered {len(file_list)} files for query '{query}'"
            )

        except Exception as e:  # try/except block
            return create_workflow_result(
                success=False,
                error=f"Agent scope command failed: {str(e)}"
            )

    def _discover_files(self, project_root: Path, exclude_patterns: List[str]) -> List[Path]:
        """Discover relevant files using path helpers."""
        # Implementation uses existing path helpers
        # Simple file discovery logic - complexity handled by helpers
        pass
```

This sub-slice handles command interface, validation, and file discovery with reduced complexity, preparing inputs for the context extraction and ranking sub-slice (2.2b).
