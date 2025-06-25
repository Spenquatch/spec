**Slice 5.3: Status Command Real AI Provider Integration**

**Goal**: Update status command to show real AI provider status instead of hardcoded placeholder messages

**Slice Type**: Integration

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -r "def format" /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/ | head -5`
  Found: No format utilities, but workflow_utils.py exists for result formatting
- Existing helper: spec_cli/utils/workflow_utils.py → Workflow result formatting
- Existing helper: spec_cli/utils/error_handler.py → Error handling with context
- No new helpers needed - uses existing provider manager interfaces

**Complexity Analysis:**
- Decision points: 4/7 (config check, provider availability check, error handling, status formatting)
- Helper calls: 2 (workflow_utils for formatting, error_handler for exceptions)
- McCabe validation: Pass (4 ≤ 7)

**Inputs → Action → Outputs:**
- **Inputs**: {show_summary: bool, verbose: bool}
- **Action**:
  1. Import ProviderManager and AI config loading from new system
  2. Replace hardcoded AI status messages (lines 188-191 in status.py)
  3. Connect to real ProviderManager.get_provider_info()
  4. Display actual provider availability, configuration, and performance metrics
  5. Show provider fallback chain status (llama.cpp → PyTorch → template)
  6. Format AI status using existing workflow utilities
- **Outputs**: {formatted_status: str, provider_info: dict[str, Any]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/cli/commands/status.py (modify AI status reporting, lines 188-191)
- tests/unit/cli/commands/test_status.py (update tests for real AI integration)

**Test Requirements:**
- **Unit Tests**:
  - test_status_shows_real_ai_provider_info()
  - test_status_shows_provider_fallback_chain()
  - test_status_handles_disabled_ai_gracefully()
  - test_status_shows_performance_metrics()
  - test_status_error_handling_when_providers_unavailable()
- **Integration Test**: Run spec status --summary and verify real AI provider information displayed
- **Idempotent Tests**: All tests must pass consistently on repeated runs
- **Mocks/Fixtures**: Mock ProviderManager, AI config objects

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
Run `spec status --summary` and verify it shows actual AI provider status, availability, model information, and performance metrics from the new provider system

**AI Agent Execution Notes:**
- This slice depends on slice 5.1 being completed (AIContentManager reconnection)
- Replace hardcoded placeholder messages with real provider info
- Use existing workflow_utils for consistent status formatting
- Ensure status command performance remains under 1s for user experience
- Handle cases where AI system is disabled or providers unavailable gracefully
