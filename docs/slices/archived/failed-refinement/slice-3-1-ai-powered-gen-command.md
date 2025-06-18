# Slice 3.1: AI-Powered Gen Command

**Goal**: Transform existing `spec gen` command to use AI as the primary documentation generation method with template fallback

**Slice Type**: Integration

**Helper Dependencies & Search Evidence:**
- Helper search performed: `find /Users/spensermcconnell/__Active_Code/spec-cli -name "*gen*" -o -name "*command*" | grep -v __pycache__`
- spec_cli/cli/commands/gen_command.py → existing gen command (needs enhancement)
- spec_cli/utils/path_utils.py → resolve_project_root(), safe_relative_to() for file processing
- spec_cli/utils/workflow_utils.py → create_workflow_result() for command result handling
- spec_cli/ai/config/loader.py → ConfigLoader (existing, from slice 1b)
- spec_cli/ai/providers/local.py → LocalAIProvider (existing, from slice 2b)
- spec_cli/templates/ai_enhanced.py → AIEnhancedTemplate (from slice 2.1)
- Create helper: spec_cli/ai/providers/manager.py → get_available_provider() → "Get best available AI provider with fallback"

**Complexity Analysis:**
- Decision points: 6/7 (if ai_enabled, if provider_available, if generation_success, if fallback_needed, try/except blocks)
- Helper calls: 6 (resolve_project_root, ConfigLoader.load_ai_config, get_available_provider, AIEnhancedTemplate.process_template, create_workflow_result)
- McCabe validation: Pass (6 ≤ 7)

**Inputs → Action → Outputs:**
- **Inputs**: {target_path: Path, doc_type: str, template_path: Optional[Path], no_ai: bool}
- **Action**:
  1. Load AI configuration using config helper (try/except)
  2. Check if AI is enabled and available using provider helper (decision point)
  3. If AI available, attempt AI generation (decision point + try/except)
  4. If AI fails or disabled, fallback to enhanced templates (decision point)
  5. Process files using appropriate method (decision point)
  6. Generate documentation and return results using workflow helper (try/except)
- **Outputs**: {generated_files: List[Path], generation_method: str, metadata: Dict[str, Any]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/cli/commands/gen_command.py (modify existing - enhance with AI-first logic)
- spec_cli/ai/providers/manager.py (new - provider selection and fallback helper)

**Test Requirements:**
- **Unit Tests**: Test AI-first generation, template fallback, provider selection, error handling, --no-ai flag behavior
- **Integration Test**: End-to-end test with AI generation successful, AI unavailable fallback, traditional template mode
- **Idempotent Tests**: All tests must pass consistently on repeated runs
- **Mocks/Fixtures**: Mock AI providers, sample source files, template fixtures, configuration scenarios

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions
- Performance: Generation completes within 30 seconds for typical directory

**Integration Validation:**
Run `spec gen src/` with AI available and verify AI-generated documentation. Run with `--no-ai` flag and verify template fallback works. Test with AI dependencies missing and verify graceful degradation to templates. Ensure backward compatibility with existing gen command usage patterns.

**AI Agent Execution Notes:**
This slice transforms the core user experience to be AI-first while maintaining 100% backward compatibility. The existing gen command interface must remain unchanged, but the implementation switches to AI as the primary method. Ensure graceful fallback when AI is unavailable. Focus on user experience - the transition should be seamless and beneficial.

**Expected Implementation Pattern:**
```python
class GenCommand(BaseCommand):
    """Enhanced gen command with AI-first generation."""

    def execute(self, target_path: Path, doc_type: str = "standard",
                template_path: Optional[Path] = None, no_ai: bool = False) -> WorkflowResult:
        """Execute documentation generation with AI-first approach."""
        try:
            # Load configuration
            config_loader = ConfigLoader()
            ai_config = config_loader.load_ai_config()

            # Determine generation method
            if no_ai or not ai_config.enabled:
                return self._generate_with_templates(target_path, template_path)

            # Try AI generation first
            provider_manager = ProviderManager(ai_config)
            provider = provider_manager.get_available_provider()

            if provider:
                try:
                    result = self._generate_with_ai(target_path, provider, doc_type)
                    if result.success:
                        return result
                    # AI failed, fall back to templates
                    self.logger.warning("AI generation failed, falling back to templates")
                except Exception as e:
                    self.logger.warning(f"AI error: {e}, falling back to templates")

            # Fallback to enhanced templates
            return self._generate_with_templates(target_path, template_path, ai_enhanced=True)

        except Exception as e:
            return create_workflow_result(
                success=False,
                error=f"Documentation generation failed: {str(e)}"
            )

    def _generate_with_ai(self, target_path: Path, provider: AIProvider, doc_type: str) -> WorkflowResult:
        """Generate documentation using AI provider."""
        # Implementation using existing AI infrastructure
        pass

    def _generate_with_templates(self, target_path: Path, template_path: Optional[Path],
                                ai_enhanced: bool = False) -> WorkflowResult:
        """Generate documentation using templates with optional AI enhancement."""
        # Implementation using AIEnhancedTemplate if ai_enhanced=True
        pass
```

This slice completes the transformation of spec into an AI-first tool while maintaining full backward compatibility and graceful degradation.
