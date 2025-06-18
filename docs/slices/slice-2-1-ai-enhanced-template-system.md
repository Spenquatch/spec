# Slice 2.1: AI-Enhanced Template System

**Goal**: Transform existing templates to work as AI prompt structures while preserving backward compatibility

**Slice Type**: Component

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -n "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/templates/*.py` (no matches - templates directory not in spec_cli)
- Helper search performed: `find /Users/spensermcconnell/__Active_Code/spec-cli -name "*template*" -type f`
- spec_cli/utils/path_utils.py → safe_relative_to(), normalize_path() for template file handling
- spec_cli/utils/error_handler.py → ErrorHandler.wrap() for template processing errors
- spec_cli/ai/providers/base.py → GenerationRequest (existing, from slice 2a)
- Create helper: spec_cli/templates/prompt_generator.py → convert_template_to_prompt(template_content: str) → "Convert template variables to AI prompt structure"

**Complexity Analysis:**
- Decision points: 6/7 (if template_exists, if variables_found, if ai_enabled, try/except blocks for file operations)
- Helper calls: 4 (normalize_path, safe_relative_to, convert_template_to_prompt, ErrorHandler.wrap)
- McCabe validation: Pass (6 ≤ 7)

**Inputs → Action → Outputs:**
- **Inputs**: {template_path: Path, variables: Dict[str, Any], ai_enabled: bool}
- **Action**:
  1. Load template file using path helpers (decision point + try/except)
  2. Parse template variables and structure (decision point)
  3. If AI enabled, convert to prompt format using helper (decision point)
  4. If AI disabled, use traditional variable substitution (decision point)
  5. Validate output structure and return result (try/except)
- **Outputs**: {template_content: str, prompt_structure: Dict[str, Any]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/templates/ai_enhanced.py (new - AI template processing logic)
- spec_cli/templates/prompt_generator.py (new - template-to-prompt conversion helper)

**Test Requirements:**
- **Unit Tests**: Test template loading, AI prompt conversion, variable substitution, error handling for missing templates, malformed templates
- **Integration Test**: End-to-end test with real template file converted to AI prompt and used for generation
- **Idempotent Tests**: All tests must pass consistently on repeated runs
- **Mocks/Fixtures**: Sample .spectemplate files, mock file system operations, template variable fixtures

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions
- Performance: Template processing completes within 1 second

**Integration Validation:**
Create a .spectemplate file with variables like {{filename}}, {{purpose}}, process it through the AI-enhanced system, verify that it produces both traditional template output and AI prompt structure. Test that existing templates work unchanged (backward compatibility) while new AI features enhance the output.

**AI Agent Execution Notes:**
This slice bridges existing template functionality with AI capabilities. Ensure 100% backward compatibility - existing templates must work exactly as before. The enhancement adds AI prompt generation as a parallel capability. Focus on preserving template structure while converting variables to AI-friendly prompt format. Use path helpers for cross-platform file operations.

**Expected Implementation Pattern:**
```python
class AIEnhancedTemplate:
    """Enhanced template processor with AI prompt generation."""

    def __init__(self, template_path: Path):
        self.template_path = normalize_path(template_path)
        self.prompt_generator = PromptGenerator()

    def process_template(self, variables: Dict[str, Any], ai_enabled: bool = True) -> TemplateResult:
        """Process template with optional AI enhancement."""
        try:
            # Load template using path helpers
            template_content = self._load_template()

            if ai_enabled:
                # Convert to AI prompt structure
                prompt_structure = self.prompt_generator.convert_template_to_prompt(template_content)
                return TemplateResult(
                    traditional_content=self._substitute_variables(template_content, variables),
                    ai_prompt=prompt_structure,
                    variables=variables
                )
            else:
                # Traditional template processing
                return TemplateResult(
                    traditional_content=self._substitute_variables(template_content, variables),
                    variables=variables
                )
        except Exception as e:
            return TemplateResult(success=False, error=str(e))
```

This slice enables templates to serve dual purposes: traditional variable substitution for backward compatibility and intelligent AI prompt structures for enhanced generation.
