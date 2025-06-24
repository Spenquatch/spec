# Slice 2d: Provider-Generator Integration

**Goal**: Connect DocumentationGenerator from slice 2c to LocalAIProvider from slice 2b to enable actual AI documentation generation

**Slice Type**: Integration

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -n "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/*.py | grep -E "(error|platform|path)"`
- spec_cli/utils/error_handler.py → ErrorHandler.wrap() for error handling
- spec_cli/utils/platform_utils.py → get_gpu_capabilities() for device detection
- spec_cli/utils/path_utils.py → safe_relative_to() for path validation
- spec_cli/ai/providers/generation.py → DocumentationGenerator (existing, from slice 2c)
- spec_cli/ai/providers/local.py → LocalAIProvider (existing, from slice 2b)

**Complexity Analysis:**
- Decision points: 5/7 (if model_exists, if load_success, if generation_success, try/except blocks)
- Helper calls: 3 (get_gpu_capabilities, DocumentationGenerator.load_model, DocumentationGenerator.generate_documentation)
- McCabe validation: Pass (5 ≤ 7)

**Inputs → Action → Outputs:**
- **Inputs**: {request: GenerationRequest, config: LocalModelConfig}
- **Action**:
  1. Initialize DocumentationGenerator with config (helper call)
  2. Detect optimal device using platform helper (decision point)
  3. Load AI model on detected device (decision point + try/except)
  4. Generate documentation using loaded model (decision point + try/except)
  5. Return structured result with metadata (helper call for error handling)
- **Outputs**: {result: GenerationResult} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/ai/providers/local.py (modify existing LocalAIProvider.generate_documentation method)

**Test Requirements:**
- **Unit Tests**: Test successful integration, model loading failure, generation failure, device detection, error handling
- **Integration Test**: End-to-end test proving AI generation works with real model
- **Idempotent Tests**: All tests must pass consistently on repeated runs
- **Mocks/Fixtures**: Mock DocumentationGenerator, mock device detection, sample GenerationRequest fixtures

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions
- Performance: AI generation completes within 5 seconds for typical file

**Integration Validation:**
Create a test Python file, run AI generation through LocalAIProvider, verify that actual AI-generated content is returned (not placeholder) and includes structured documentation with index.md and metadata.

**AI Agent Execution Notes:**
This slice is CRITICAL - it's the missing link that enables end-to-end AI functionality. The current LocalAIProvider.generate_documentation() method returns placeholder content. Replace this with actual DocumentationGenerator integration. Ensure proper error handling for missing dependencies, model loading failures, and generation errors. Use existing helpers for device detection and error reporting.

**Expected Implementation Pattern:**
```python
def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
    """Generate documentation using AI model."""
    try:
        # Use helper for device detection
        device = get_gpu_capabilities().best_device

        # Initialize generator (helper call)
        generator = DocumentationGenerator(self.config)

        # Load model with error handling
        if not generator.load_model(device):
            return GenerationResult(
                success=False,
                error="Failed to load AI model",
                metadata={"provider": "local", "device": device}
            )

        # Generate documentation
        return generator.generate_documentation(request)

    except Exception as e:
        # Use error handler helper
        error_context = {"provider": "local", "model": self.config.model_name}
        return GenerationResult(
            success=False,
            error=f"AI generation failed: {str(e)}",
            metadata=error_context
        )
```

This slice transforms the AI infrastructure from placeholder to functional, enabling actual AI-powered documentation generation for the first time.
