**Slice 5.4: Template AI Workflow End-to-End Validation**

**Goal**: Validate complete template → AI enhancement → generation workflow works with new provider system

**Slice Type**: Integration

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -r "def validate" /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/ | head -5`
  Found: security_validators.py contains validation functions
- Existing helper: spec_cli/utils/security_validators.py → Input validation patterns
- Existing helper: spec_cli/utils/workflow_utils.py → Workflow result validation
- Existing helper: spec_cli/utils/error_handler.py → Error context and handling
- No new helpers needed - uses existing validation and workflow patterns

**Complexity Analysis:**
- Decision points: 7/7 (template load check, AI enabled check, provider availability, generation success, fallback handling, result validation, error recovery)
- Helper calls: 3 (validation utilities, workflow utilities, error handling)
- McCabe validation: Pass (7 ≤ 7, at limit but acceptable)

**Inputs → Action → Outputs:**
- **Inputs**: {source_file: Path, template_content: str, ai_enabled: bool}
- **Action**:
  1. Load template using AIEnhancedTemplate processor
  2. Verify template can create GenerationRequest for new provider system
  3. Test AIContentManager processes request through provider chain
  4. Validate GenerationResult conversion back to template content format
  5. Test fallback scenarios when providers unavailable
  6. Verify end-to-end: spec gen file.py uses templates + AI seamlessly
  7. Validate error handling and recovery in template AI workflow
- **Outputs**: {validation_result: bool, workflow_status: dict[str, Any]} or {error_details: str}

**Files to Create/Modify:**
- tests/integration/test_template_ai_workflow.py (new integration test file)
- tests/unit/templates/test_ai_enhanced_integration.py (unit tests for integration points)

**Test Requirements:**
- **Unit Tests**:
  - test_ai_enhanced_template_creates_generation_request()
  - test_generation_request_processed_by_new_providers()
  - test_generation_result_converted_to_template_format()
  - test_template_fallback_when_ai_unavailable()
  - test_error_handling_in_template_ai_pipeline()
- **Integration Test**: Complete spec gen workflow with AI template enhancement
- **Idempotent Tests**: All tests must pass consistently on repeated runs
- **Mocks/Fixtures**: Sample templates, mock provider responses, test source files

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
Create test template with AI placeholders, run spec gen on sample Python file, verify AI-enhanced content generated through new provider system, test fallback when AI disabled

**AI Agent Execution Notes:**
- This slice requires slices 5.1 (AIContentManager reconnection) to be completed first
- Focus on testing integration points rather than individual component functionality
- Verify the bridge between AIEnhancedTemplate and new provider system works
- Test both successful AI generation and graceful fallback scenarios
- Ensure template variable substitution works correctly with AI-generated content
