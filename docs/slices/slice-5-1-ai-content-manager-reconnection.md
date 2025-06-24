**Slice 5.1: AIContentManager Reconnection to New AI System**

**Goal**: Reconnect the disabled AIContentManager to use the new ProviderManager instead of deprecated PlaceholderAIProvider

**Slice Type**: Integration

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -r "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/ | head -15`
  Found: error_handler.py, workflow_utils.py, path_utils.py
- Existing helper: spec_cli/utils/error_handler.py → Error handling with structured context
- Existing helper: spec_cli/utils/workflow_utils.py → Workflow result creation utilities
- No new helpers needed - integration uses existing provider interfaces

**Complexity Analysis:**
- Decision points: 6/7 (provider availability check, config enabled check, content generation loop, exception handling, fallback logic, result validation)
- Helper calls: 3 (error_handler.wrap, workflow result creation, path normalization)
- McCabe validation: Pass (6 ≤ 7)

**Inputs → Action → Outputs:**
- **Inputs**: {file_path: Path, context: dict[str, Any], content_requests: list[str], max_tokens_per_request: int}
- **Action**:
  1. Import ProviderManager and AI config loading utilities
  2. Replace disabled initialization with ProviderManager connection
  3. Update generate_ai_content() to use GenerationRequest/GenerationResult pattern
  4. Implement provider fallback chain (llama.cpp → PyTorch → template fallback)
  5. Convert GenerationResult to expected content dict format
  6. Re-enable AIContentManager (self.enabled = True from config)
- **Outputs**: {content_type: str} mapping or {error_message: str}

**Files to Create/Modify:**
- spec_cli/templates/ai_integration.py (modify AIContentManager class, lines 334-625)
- tests/unit/templates/test_ai_integration.py (update tests for new provider integration)

**Test Requirements:**
- **Unit Tests**:
  - test_ai_content_manager_connects_to_provider_manager()
  - test_generate_ai_content_uses_new_providers()
  - test_provider_fallback_chain_works()
  - test_disabled_ai_returns_placeholder_content()
  - test_generation_result_conversion_to_content_dict()
- **Integration Test**: End-to-end template generation with AI content from new providers
- **Idempotent Tests**: All tests must pass consistently on repeated runs
- **Mocks/Fixtures**: Mock ProviderManager, GenerationRequest/Result objects

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- Integration tests validate end-to-end functionality
- McCabe complexity ≤ 7 for all functions
- Performance micro-bench: median under 10ms on representative input
- All tests idempotent (pass on repeated runs)

**Integration Validation:**
Create template file, run spec gen with AI enabled, verify AIContentManager uses new providers to generate enhanced content and falls back gracefully when providers unavailable

**AI Agent Execution Notes:**
- Remove lines 335-336 that disable AIContentManager
- Import from ..ai.config.loader and ..ai.providers.manager
- Use existing error_handler.wrap decorator for exception handling
- Maintain backward compatibility - existing template system must continue working
- Ensure provider fallback chain matches new AI system architecture
