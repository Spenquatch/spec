# Slice 3.1a: AI Provider Integration

**Goal**: Integrate AI provider with existing gen command for AI-first documentation generation

**Slice Type**: AI Integration Core

**Helper Dependencies & Search Evidence:**
- Helper search performed: `find /Users/spensermcconnell/__Active_Code/spec-cli -name "*gen*" -o -name "*provider*" | grep -v __pycache__`
- spec_cli/ai/config/loader.py → ConfigLoader (existing, from slice 1b)
- spec_cli/ai/providers/local.py → LocalAIProvider (existing, from slice 2b)
- spec_cli/utils/workflow_utils.py → create_workflow_result() for result handling
- spec_cli/utils/path_utils.py → resolve_project_root(), safe_relative_to() for file processing
- Create helper: spec_cli/ai/providers/manager.py → get_available_provider() → "Get best available AI provider with configuration validation"

**Complexity Analysis:**
- Decision points: 5/7 (provider availability, config validation, AI generation success, error handling, provider selection)
- Helper calls: 5 (ConfigLoader.load_ai_config, get_available_provider, provider.generate_documentation, create_workflow_result, path helpers)
- McCabe validation: Pass (5 ≤ 7, well under limit)

**Inputs → Action → Outputs:**
- **Inputs**: {target_path: Path, doc_type: str, ai_config_override: Optional[Dict]}
- **Action**:
  1. Load AI configuration using config helper (decision point + try/except)
  2. Validate AI provider availability using manager helper (decision point)
  3. Initialize AI provider with configuration (decision point + try/except)
  4. Generate documentation using AI provider (decision point + try/except)
  5. Process AI results and format for output (try/except)
- **Outputs**: {generated_docs: Dict[str, str], generation_metadata: Dict[str, Any], success: bool} or {error_message: str, fallback_needed: bool}

**Files to Create/Modify:**
- spec_cli/ai/providers/manager.py (new - provider selection and management helper)
- spec_cli/ai/generation/ai_generator.py (new - AI documentation generation logic)

**Dependencies**:
- Uses existing AI configuration from slice 1b
- Uses existing LocalAIProvider from slice 2b
- Results passed to Slice 3.1b for fallback handling if AI fails

**Classes**: 2 (ProviderManager, AIDocumentationGenerator)
**External Integrations**: 1 (AI provider - LocalAI or configured LLM)

**Test Requirements:**
- **Unit Tests**: Provider selection, configuration validation, AI generation success/failure, error handling
- **Integration Test**: End-to-end AI documentation generation with real AI provider
- **Idempotent Tests**: Consistent AI generation behavior on repeated runs
- **Mocks/Fixtures**: Mock AI providers, configuration scenarios, sample source files

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions (achieved: 5/7)
- Performance: AI generation completes within 20 seconds per file

**Integration Validation:**
Successfully generate documentation using AI provider for sample source files, handle AI provider failures gracefully, and provide clear error messages for debugging.

**Expected Implementation Pattern:**
```python
class ProviderManager:
    """Manage AI provider selection and availability."""

    def __init__(self, ai_config: AIConfig):
        self.ai_config = ai_config

    def get_available_provider(self) -> Optional[AIProvider]:
        """Get best available AI provider with validation."""
        try:
            # Validate configuration (decision point 1)
            if not self.ai_config.enabled:
                return None

            # Check provider availability (decision point 2)
            if self.ai_config.provider_type == "local":
                provider = LocalAIProvider(self.ai_config)
                if provider.is_available():
                    return provider

            return None

        except Exception as e:  # try/except block
            logger.warning(f"Provider selection failed: {e}")
            return None

class AIDocumentationGenerator:
    """Generate documentation using AI providers."""

    def __init__(self, provider: AIProvider):
        self.provider = provider

    def generate_documentation(self, target_path: Path, doc_type: str) -> WorkflowResult:
        """Generate documentation using AI."""
        try:
            # Validate target path (decision point 3)
            if not target_path.exists():
                return create_workflow_result(
                    success=False,
                    error=f"Target path does not exist: {target_path}",
                    data={"fallback_needed": True}
                )

            # Generate documentation (decision point 4 + try/except)
            generated_docs = self.provider.generate_documentation(
                target_path=target_path,
                doc_type=doc_type
            )

            # Validate generation results (decision point 5)
            if not generated_docs:
                return create_workflow_result(
                    success=False,
                    error="AI generation returned empty results",
                    data={"fallback_needed": True}
                )

            generation_metadata = {
                "provider_type": self.provider.provider_type,
                "generation_time": datetime.now().isoformat(),
                "files_generated": len(generated_docs),
                "doc_type": doc_type
            }

            return create_workflow_result(
                success=True,
                data={
                    "generated_docs": generated_docs,
                    "generation_metadata": generation_metadata
                },
                message=f"Generated {len(generated_docs)} documentation files using AI"
            )

        except Exception as e:  # try/except block
            return create_workflow_result(
                success=False,
                error=f"AI documentation generation failed: {str(e)}",
                data={"fallback_needed": True}
            )

def generate_with_ai(target_path: Path, doc_type: str, ai_config_override: Optional[Dict] = None) -> WorkflowResult:
    """Primary AI generation function."""
    try:
        # Load configuration (decision point + try/except)
        config_loader = ConfigLoader()
        ai_config = config_loader.load_ai_config()

        if ai_config_override:
            ai_config.update(ai_config_override)

        # Get available provider (decision point)
        provider_manager = ProviderManager(ai_config)
        provider = provider_manager.get_available_provider()

        if not provider:
            return create_workflow_result(
                success=False,
                error="No AI provider available",
                data={"fallback_needed": True}
            )

        # Generate documentation (decision point + try/except)
        generator = AIDocumentationGenerator(provider)
        return generator.generate_documentation(target_path, doc_type)

    except Exception as e:  # try/except block
        return create_workflow_result(
            success=False,
            error=f"AI generation initialization failed: {str(e)}",
            data={"fallback_needed": True}
        )
```

This sub-slice focuses solely on AI provider integration and documentation generation, with clear fallback signaling for the template fallback sub-slice (3.1b).
