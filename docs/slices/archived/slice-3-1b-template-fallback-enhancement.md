# Slice 3.1b: Template Fallback & Enhancement

**Goal**: Implement enhanced template fallback system and integrate with existing gen command interface

**Slice Type**: Command Enhancement & Fallback Logic

**Helper Dependencies & Search Evidence:**
- Helper search performed: `find /Users/spensermcconnell/__Active_Code/spec-cli -name "*gen*" -o -name "*template*" | grep -v __pycache__`
- spec_cli/cli/commands/gen_command.py → existing gen command (needs enhancement)
- spec_cli/templates/ai_enhanced.py → AIEnhancedTemplate (from slice 2.1)
- spec_cli/utils/workflow_utils.py → create_workflow_result() for result handling
- spec_cli/utils/path_utils.py → resolve_project_root(), safe_relative_to() for file processing
- Results from Slice 3.1a for AI generation attempts
- No new helpers created (uses existing template and utility helpers)

**Complexity Analysis:**
- Decision points: 6/7 (no_ai flag, fallback_needed check, template type selection, generation success, error handling, result combination)
- Helper calls: 5 (AIEnhancedTemplate processing, create_workflow_result, path helpers, existing gen logic)
- McCabe validation: Pass (6 ≤ 7, under limit)

**Inputs → Action → Outputs:**
- **Inputs**: {target_path: Path, doc_type: str, template_path: Optional[Path], no_ai: bool, ai_result: Optional[WorkflowResult]}
- **Action**:
  1. Check if AI was disabled via --no-ai flag (decision point)
  2. Check if AI generation failed and fallback is needed (decision point)
  3. Select appropriate template method (enhanced vs traditional) (decision point)
  4. Generate documentation using selected template approach (decision point + try/except)
  5. Combine AI metadata with template results if applicable (decision point)
  6. Format final results for user output (try/except)
- **Outputs**: {generated_files: List[Path], generation_method: str, metadata: Dict[str, Any]} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/cli/commands/gen_command.py (modify existing - enhance with AI-first orchestration)

**Dependencies**:
- Receives AI generation results from Slice 3.1a (may be failure with fallback_needed=True)
- Uses AIEnhancedTemplate from slice 2.1
- Uses existing gen command infrastructure
- No external integrations (internal template processing only)

**Classes**: 1 (Enhanced GenCommand - modify existing)
**External Integrations**: 0 (internal template processing only)

**Test Requirements:**
- **Unit Tests**: Template fallback logic, --no-ai flag behavior, AI failure handling, template selection, backward compatibility
- **Integration Test**: Full gen command with AI-first → template fallback workflow, traditional template-only mode
- **Idempotent Tests**: Consistent template generation on repeated runs
- **Mocks/Fixtures**: Mock AI results, template fixtures, command line argument scenarios

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions (achieved: 6/7)
- Performance: Template generation completes within 10 seconds per directory

**Integration Validation:**
Run complete gen command workflow: `spec gen src/` (AI-first with template fallback), `spec gen src/ --no-ai` (template-only), and verify backward compatibility with existing usage patterns.

**Expected Implementation Pattern:**
```python
class GenCommand(BaseCommand):
    """Enhanced gen command with AI-first generation and template fallback."""

    def execute(self, target_path: Path, doc_type: str = "standard",
                template_path: Optional[Path] = None, no_ai: bool = False) -> WorkflowResult:
        """Execute documentation generation with AI-first approach."""
        try:
            # Check if AI is explicitly disabled (decision point 1)
            if no_ai:
                return self._generate_with_templates(
                    target_path=target_path,
                    template_path=template_path,
                    ai_enhanced=False,
                    reason="AI disabled by user"
                )

            # Attempt AI generation first (from Slice 3.1a)
            ai_result = generate_with_ai(target_path, doc_type)

            # Check if AI succeeded (decision point 2)
            if ai_result.success:
                return self._finalize_ai_results(ai_result, target_path)

            # Check if fallback is needed (decision point 3)
            fallback_needed = ai_result.data and ai_result.data.get("fallback_needed", False)
            if fallback_needed:
                self.logger.info("AI generation failed, falling back to enhanced templates")
                return self._generate_with_templates(
                    target_path=target_path,
                    template_path=template_path,
                    ai_enhanced=True,
                    reason=f"AI fallback: {ai_result.error}"
                )

            # AI error without fallback signal
            return ai_result

        except Exception as e:  # try/except block
            return create_workflow_result(
                success=False,
                error=f"Documentation generation failed: {str(e)}"
            )

    def _generate_with_templates(self, target_path: Path, template_path: Optional[Path],
                                ai_enhanced: bool, reason: str) -> WorkflowResult:
        """Generate documentation using template system."""
        try:
            # Select template approach (decision point 4)
            if ai_enhanced:
                template_processor = AIEnhancedTemplate()
                generation_method = "ai_enhanced_template"
            else:
                # Use existing traditional template logic
                generation_method = "traditional_template"

            # Generate documentation (decision point 5 + try/except)
            if ai_enhanced:
                generated_files = template_processor.process_template(
                    target_path=target_path,
                    template_path=template_path
                )
            else:
                generated_files = self._traditional_template_generation(
                    target_path=target_path,
                    template_path=template_path
                )

            # Validate generation results (decision point 6)
            if not generated_files:
                return create_workflow_result(
                    success=False,
                    error="Template generation produced no output files"
                )

            metadata = {
                "generation_method": generation_method,
                "files_generated": len(generated_files),
                "generation_reason": reason,
                "generation_time": datetime.now().isoformat(),
                "target_path": str(target_path)
            }

            return create_workflow_result(
                success=True,
                data={
                    "generated_files": generated_files,
                    "generation_method": generation_method,
                    "metadata": metadata
                },
                message=f"Generated {len(generated_files)} files using {generation_method}"
            )

        except Exception as e:  # try/except block
            return create_workflow_result(
                success=False,
                error=f"Template generation failed: {str(e)}"
            )

    def _finalize_ai_results(self, ai_result: WorkflowResult, target_path: Path) -> WorkflowResult:
        """Finalize successful AI generation results."""
        # Add command-level metadata to AI results
        ai_data = ai_result.data or {}
        ai_data["metadata"]["command_execution_time"] = datetime.now().isoformat()
        ai_data["metadata"]["target_path"] = str(target_path)

        return create_workflow_result(
            success=True,
            data=ai_data,
            message=f"Generated documentation using AI: {ai_result.message}"
        )

    def _traditional_template_generation(self, target_path: Path, template_path: Optional[Path]) -> List[Path]:
        """Existing traditional template generation logic."""
        # Preserve existing gen command functionality
        # This maintains 100% backward compatibility
        pass
```

This sub-slice handles template fallback logic and command orchestration while maintaining clean separation from AI integration complexity, ensuring each sub-slice stays within complexity limits.
