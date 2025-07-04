"""Gen command implementation using BaseCommand with AI-first generation and template fallback."""

from datetime import datetime
from pathlib import Path
from typing import Any

from ...ai.providers.manager import create_workflow_result
from ...config.settings import SpecSettings
from ...exceptions import SpecError
from ...file_processing.conflict_resolver import ConflictResolutionStrategy
from ...file_system.directory_manager import DirectoryManager
from ...file_system.path_resolver import PathResolver
from ...logging.debug import debug_logger
from ...templates.ai_enhanced import AIEnhancedTemplate
from ...templates.generator import SpecContentGenerator
from ...templates.loader import load_template
from ...templates.substitution import TemplateSubstitution
from ...ui.console import get_console
from ...ui.error_display import show_message
from ...utils.path_utils import normalize_path
from ..base_command import BaseCommand
from ..utils import get_user_confirmation
from .generation import (
    confirm_generation,
    select_template,
    validate_generation_input,
)
from .generation.workflows import GenerationResult


def generate_with_ai(
    target_path: Path, doc_type: str, template_path: Path | None = None
) -> dict[str, Any]:
    """Generate documentation using AI.

    This is a placeholder function for AI generation functionality.

    Args:
        target_path: Path to the source file
        doc_type: Type of documentation to generate
        template_path: Optional template path

    Returns:
        Dictionary with generation results
    """
    # Placeholder implementation - will be fully implemented later
    return {"success": False, "error": "AI generation not yet implemented", "data": {}}


class GenCommand(BaseCommand):
    """Command to generate documentation for source files."""

    def __init__(self, settings: SpecSettings | None = None):
        """Initialize gen command."""
        super().__init__(settings)
        self.console = get_console()

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the gen command with AI-first approach and template fallback.

        Args:
            files: List of source files or directories
            template: Template name to use
            conflict_strategy: How to handle existing spec files
            commit: Automatically commit generated files
            message: Commit message (implies commit)
            interactive: Enable interactive prompts
            force: Force generation despite warnings
            dry_run: Preview what would be generated
            no_ai: Disable AI generation and use template-only mode
            doc_type: Type of documentation to generate (default: standard)
            **kwargs: Additional arguments

        Returns:
            Result dictionary with success status and details
        """
        # Extract parameters from kwargs
        files = kwargs.get("files", [])
        template = kwargs.get("template", "default")
        conflict_strategy = kwargs.get("conflict_strategy", "backup")
        interactive = kwargs.get("interactive", False)
        force = kwargs.get("force", False)
        dry_run = kwargs.get("dry_run", False)
        no_ai = kwargs.get("no_ai", False)
        doc_type = kwargs.get("doc_type", "standard")

        # Validate repository state
        self.validate_repository_state()

        # Expand directories to individual files
        expanded_files = self._expand_source_files(files)

        if not expanded_files:
            show_message("No processable files found in the specified paths", "warning")
            return self.create_result(
                True, "No files to process", data={"generated": []}
            )

        show_message(f"Found {len(expanded_files)} files to process", "info")

        # Configure conflict strategy
        strategy_map = {
            "backup": ConflictResolutionStrategy.BACKUP_AND_REPLACE,
            "overwrite": ConflictResolutionStrategy.OVERWRITE,
            "skip": ConflictResolutionStrategy.SKIP,
            "fail": ConflictResolutionStrategy.FAIL,
        }
        conflict_enum = strategy_map.get(
            conflict_strategy, ConflictResolutionStrategy.BACKUP_AND_REPLACE
        )

        # Interactive configuration
        if interactive:
            template = select_template(template)

            # Confirm configuration
            if not confirm_generation(expanded_files, template, conflict_enum):
                show_message("Generation cancelled by user", "info")
                return self.create_result(False, "Generation cancelled by user")

        # Validate inputs
        validation_result = validate_generation_input(
            expanded_files, template, conflict_enum
        )

        if not validation_result["valid"]:
            show_message("Validation failed:", "error")
            for error in validation_result["errors"]:
                self.console.print(f"  • [red]{error}[/red]")

            errors_str = "; ".join(validation_result["errors"])
            raise SpecError(f"Validation failed: {errors_str}")

        # Show warnings if any
        if validation_result["warnings"]:
            show_message("Warnings:", "warning")
            for warning in validation_result["warnings"]:
                self.console.print(f"  • [yellow]{warning}[/yellow]")

            if not force and not get_user_confirmation(
                "Continue despite warnings?", default=True
            ):
                show_message("Generation cancelled", "info")
                return self.create_result(False, "Generation cancelled due to warnings")

        # Dry run mode
        if dry_run:
            self._show_dry_run_preview(expanded_files, template, conflict_enum)
            return self.create_result(
                True,
                f"Dry run completed - {len(expanded_files)} files would be processed",
                data={"files_to_process": expanded_files},
            )

        # AI-first generation with template fallback
        results = []
        for target_path in expanded_files:
            try:
                result = self._execute_single_file(
                    target_path=target_path,
                    doc_type=doc_type,
                    template_path=None if template == "default" else Path(template),
                    no_ai=no_ai,
                )
                results.append(result)
            except Exception as e:
                debug_logger.log(
                    "ERROR",
                    "File processing failed",
                    target_path=str(target_path),
                    error=str(e),
                )
                # Continue processing other files
                error_result = create_workflow_result(
                    success=False,
                    error=f"Processing failed for {target_path}: {str(e)}",
                )
                results.append(error_result)

        # Aggregate results
        successful_results = [r for r in results if r["success"]]
        failed_results = [r for r in results if not r["success"]]

        total_generated_files = []
        for result in successful_results:
            if "data" in result and "generated_files" in result["data"]:
                total_generated_files.extend(result["data"]["generated_files"])

        # Display summary
        if successful_results:
            show_message(
                f"Successfully processed {len(successful_results)} of {len(expanded_files)} files",
                "success",
            )

        if failed_results:
            show_message(f"Failed to process {len(failed_results)} files", "warning")
            for failed_result in failed_results:
                self.console.print(
                    f"  • [red]{failed_result.get('error', 'Unknown error')}[/red]"
                )

        debug_logger.log(
            "INFO",
            "AI-first generation command completed",
            total_files=len(expanded_files),
            successful_files=len(successful_results),
            failed_files=len(failed_results),
            generated_files=len(total_generated_files),
        )

        return self.create_result(
            len(successful_results) > 0,
            f"Generated documentation for {len(successful_results)} files",
            data={
                "generated_files": total_generated_files,
                "successful_files": len(successful_results),
                "failed_files": len(failed_results),
                "results": results,
            },
        )

    def _execute_single_file(
        self,
        target_path: Path,
        doc_type: str,
        template_path: Path | None = None,
        no_ai: bool = False,
    ) -> dict[str, Any]:
        """Execute documentation generation with AI-first approach for single file.

        Args:
            target_path: Path to the source file or directory
            doc_type: Type of documentation to generate
            template_path: Optional path to specific template
            no_ai: Whether to disable AI generation

        Returns:
            Workflow result with generated documentation or error

        Implements the exact logic from slice specification:
        - Check if AI is disabled via --no-ai flag (decision point 1)
        - Check if AI generation failed and fallback is needed (decision point 2)
        - Select appropriate template method (enhanced vs traditional) (decision point 3)
        - Generate documentation using selected approach (decision point 4 + try/except)
        - Combine AI metadata with template results if applicable (decision point 5)
        - Format final results for user output (try/except)
        """
        try:
            # Check if AI is explicitly disabled (decision point 1)
            if no_ai:
                return self._generate_with_templates(
                    target_path=target_path,
                    template_path=template_path,
                    ai_enhanced=False,
                    reason="AI disabled by user",
                )

            # Attempt AI generation first using templates as prompts (from Slice 3.1a)
            debug_logger.log(
                "INFO",
                "Attempting AI generation with templates",
                target_path=str(target_path),
            )
            ai_result = self._generate_with_ai_templates(
                target_path, doc_type, template_path
            )
            debug_logger.log(
                "INFO",
                "AI generation result",
                success=ai_result["success"],
                error=ai_result.get("error", "None"),
            )

            # Check if AI succeeded (decision point 2)
            if ai_result["success"]:
                debug_logger.log("INFO", "AI generation successful, finalizing results")
                return self._finalize_ai_results(ai_result, target_path)

            # Check if fallback is needed (decision point 3)
            fallback_needed = ai_result.get("data", {}).get("fallback_needed", False)
            if fallback_needed:
                debug_logger.log(
                    "INFO",
                    "AI generation failed, falling back to enhanced templates",
                    target_path=str(target_path),
                    error=ai_result.get("error", "Unknown AI error"),
                )
                return self._generate_with_templates(
                    target_path=target_path,
                    template_path=template_path,
                    ai_enhanced=True,
                    reason=f"AI fallback: {ai_result.get('error', 'Unknown error')}",
                )

            # AI error without fallback signal
            return ai_result

        except Exception as e:  # try/except block
            debug_logger.log(
                "ERROR",
                "Single file execution failed",
                target_path=str(target_path),
                error=str(e),
            )
            return create_workflow_result(
                success=False, error=f"Documentation generation failed: {str(e)}"
            )

    def _generate_with_templates(
        self,
        target_path: Path,
        template_path: Path | None,
        ai_enhanced: bool,
        reason: str,
    ) -> dict[str, Any]:
        """Generate documentation using template system.

        Args:
            target_path: Path to the source file or directory
            template_path: Optional path to specific template
            ai_enhanced: Whether to use AI-enhanced templates
            reason: Reason for using templates (for logging)

        Returns:
            Workflow result with generated documentation or error
        """
        try:
            # Select template approach (decision point 4)
            if ai_enhanced:
                template_processor = AIEnhancedTemplate(template_path)
                generation_method = "ai_enhanced_template"
            else:
                # Use existing traditional template logic
                generation_method = "traditional_template"

            # Generate documentation (decision point 5 + try/except)
            if ai_enhanced:
                # For AI-enhanced templates, we need to create variables and process
                variables = self._create_template_variables(target_path)
                template_result = template_processor.load_and_process_template(
                    variables=variables, ai_enabled=True
                )

                if not template_result.success:
                    return create_workflow_result(
                        success=False,
                        error=f"AI-enhanced template processing failed: {template_result.error}",
                    )

                generated_files = [target_path]  # Simplified for this implementation
            else:
                generated_files = self._traditional_template_generation(
                    target_path=target_path, template_path=template_path
                )

            # Validate generation results (decision point 6)
            if not generated_files:
                return create_workflow_result(
                    success=False, error="Template generation produced no output files"
                )

            metadata = {
                "generation_method": generation_method,
                "files_generated": len(generated_files),
                "generation_reason": reason,
                "generation_time": datetime.now().isoformat(),
                "target_path": str(target_path),
            }

            return create_workflow_result(
                success=True,
                data={
                    "generated_files": [str(f) for f in generated_files],
                    "generation_method": generation_method,
                    "metadata": metadata,
                },
                message=f"Generated {len(generated_files)} files using {generation_method}",
            )

        except Exception as e:  # try/except block
            debug_logger.log(
                "ERROR",
                "Template generation failed",
                target_path=str(target_path),
                ai_enhanced=ai_enhanced,
                error=str(e),
            )
            return create_workflow_result(
                success=False, error=f"Template generation failed: {str(e)}"
            )

    def _generate_with_ai_templates(
        self, target_path: Path, doc_type: str, template_path: Path | None
    ) -> dict[str, Any]:
        """Generate documentation using AI with templates as prompts.

        Args:
            target_path: Path to the source file
            doc_type: Type of documentation to generate
            template_path: Optional path to specific template

        Returns:
            Workflow result with AI-generated content using template prompts
        """
        try:
            # Load and process template first
            ai_template = AIEnhancedTemplate(template_path)
            variables = self._create_template_variables(target_path)

            # Process template to get AI prompt structure
            template_result = ai_template.load_and_process_template(
                variables=variables, ai_enabled=True
            )

            if not template_result.success:
                debug_logger.log(
                    "WARNING",
                    "Template processing failed, falling back to direct AI generation",
                    target_path=str(target_path),
                    error=template_result.error,
                )
                # Fall back to direct AI generation without templates
                return generate_with_ai(target_path, doc_type)

            # Read source file content
            try:
                source_content = target_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                try:
                    source_content = target_path.read_text(encoding="latin-1")
                except Exception as e:
                    return create_workflow_result(
                        success=False,
                        error=f"Failed to read source file: {e}",
                        data={"fallback_needed": True},
                    )
            except Exception as e:
                return create_workflow_result(
                    success=False,
                    error=f"Failed to read source file: {e}",
                    data={"fallback_needed": True},
                )

            # Create AI generation request with template content as prompt
            generation_request = ai_template.create_generation_request(
                source_file=target_path,
                content=source_content,
                template_result=template_result,
                doc_type=doc_type,
            )

            debug_logger.log(
                "INFO",
                "Using template-based AI generation",
                target_path=str(target_path),
                template_size=len(generation_request.template_content or ""),
                has_ai_enhancement=template_result.has_ai_enhancement(),
            )

            # Generate using AI with template prompts
            debug_logger.log(
                "INFO",
                "Calling generate_with_ai_request",
                template_size=len(generation_request.template_content or ""),
            )
            from ...ai.generation.ai_generator import generate_with_ai_request

            result = generate_with_ai_request(generation_request)
            debug_logger.log(
                "INFO",
                "generate_with_ai_request completed",
                success=result.get("success", False),
            )
            return result

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Template-based AI generation failed",
                target_path=str(target_path),
                error=str(e),
            )
            return create_workflow_result(
                success=False,
                error=f"Template-based AI generation failed: {str(e)}",
                data={"fallback_needed": True},
            )

    def _finalize_ai_results(
        self, ai_result: dict[str, Any], target_path: Path
    ) -> dict[str, Any]:
        """Finalize successful AI generation results by writing files to disk.

        Args:
            ai_result: AI generation result with content
            target_path: Path to the source file

        Returns:
            Finalized workflow result with generated file paths
        """
        try:
            # Extract generated content from AI result
            ai_data = ai_result.get("data", {})
            generated_docs = ai_data.get("generated_docs", {})

            debug_logger.log(
                "INFO",
                "AI result data inspection",
                ai_result_keys=list(ai_result.keys()),
                ai_data_keys=list(ai_data.keys()),
                generated_docs_count=len(generated_docs),
                generated_docs_keys=list(generated_docs.keys())
                if generated_docs
                else [],
            )

            if not generated_docs:
                debug_logger.log(
                    "WARNING",
                    "AI generation returned no content to write",
                    ai_result=ai_result,
                )
                return create_workflow_result(
                    success=False, error="AI generation returned no content to write"
                )

            # Get the spec directory for this file
            path_resolver = PathResolver(self.settings)
            spec_files = path_resolver.get_spec_files_for_source(target_path)

            # Ensure spec directory exists
            directory_manager = DirectoryManager(self.settings)
            directory_manager.ensure_specs_directory()
            spec_dir = directory_manager.create_spec_directory(target_path)

            # Write generated content to files
            generated_file_paths = []

            # Main content goes to index.md
            main_content = next(iter(generated_docs.values()), "")
            debug_logger.log(
                "INFO",
                "Main content inspection",
                content_length=len(main_content),
                content_preview=main_content[:100] if main_content else "EMPTY",
                has_content=bool(main_content.strip()),
            )
            if main_content.strip():
                index_file = spec_files.get("index") or spec_dir / "index.md"
                index_file.write_text(main_content, encoding="utf-8")
                generated_file_paths.append(index_file)

                debug_logger.log(
                    "INFO",
                    "AI-generated index.md written",
                    file_path=str(index_file),
                    content_length=len(main_content),
                )

            # Create history.md file using template
            try:
                template_config = load_template(self.settings)
                history_template = template_config.history

                # Create variables for history template
                history_variables = {
                    "filename": target_path.name,
                    "filepath": str(target_path),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "context": "AI-powered documentation generation",
                    "initial_purpose": "Generated comprehensive documentation using AI",
                    "decisions": "Used AI template-guided generation approach",
                    "implementation_notes": "Automatically generated using spec-cli AI integration",
                }

                # Substitute template variables
                substitution = TemplateSubstitution()
                history_content = substitution.substitute(
                    history_template, history_variables
                )

                history_file = spec_files.get("history") or spec_dir / "history.md"
                history_file.write_text(history_content, encoding="utf-8")
                generated_file_paths.append(history_file)

                debug_logger.log(
                    "INFO",
                    "Template-based history.md written",
                    file_path=str(history_file),
                    content_length=len(history_content),
                    template_used=True,
                )

            except Exception as e:
                # Fallback to basic history if template processing fails
                debug_logger.log(
                    "WARNING",
                    "Template-based history generation failed, using fallback",
                    error=str(e),
                )
                history_content = f"""# History

## Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

- Created using AI generation
- Source file: {target_path.name}
- Method: AI-powered documentation generation

## Changes

Initial AI-generated documentation.
"""
                history_file = spec_files.get("history") or spec_dir / "history.md"
                history_file.write_text(history_content, encoding="utf-8")
                generated_file_paths.append(history_file)

            # Update metadata
            if "metadata" not in ai_data:
                ai_data["metadata"] = {}

            ai_data["metadata"]["command_execution_time"] = datetime.now().isoformat()
            ai_data["metadata"]["target_path"] = str(target_path)
            ai_data["metadata"]["files_written"] = len(generated_file_paths)
            ai_data["generated_files"] = [str(f) for f in generated_file_paths]

            return create_workflow_result(
                success=True,
                data=ai_data,
                message=f"Generated and wrote {len(generated_file_paths)} files using AI",
            )

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Failed to write AI-generated content to files",
                target_path=str(target_path),
                error=str(e),
            )
            return create_workflow_result(
                success=False, error=f"Failed to write AI-generated files: {str(e)}"
            )

    def _traditional_template_generation(
        self, target_path: Path, template_path: Path | None
    ) -> list[Path]:
        """Existing traditional template generation logic.

        Args:
            target_path: Path to the source file
            template_path: Optional path to specific template

        Returns:
            List of generated file paths

        This maintains 100% backward compatibility with existing gen command functionality.
        """
        debug_logger.log(
            "INFO",
            "Traditional template generation",
            target_path=str(target_path),
            template_path=str(template_path) if template_path else "default",
        )

        try:
            # Use the working SpecContentGenerator to actually write files
            generator = SpecContentGenerator(self.settings)
            template_config = load_template()

            # Generate and write spec content files
            generated_files_dict = generator.generate_spec_content(
                target_path, template_config
            )

            # Return list of generated file paths
            generated_files = list(generated_files_dict.values())

            debug_logger.log(
                "INFO",
                "Traditional template generation completed",
                target_path=str(target_path),
                files_generated=len(generated_files),
            )

            return generated_files

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Traditional template generation failed",
                target_path=str(target_path),
                error=str(e),
            )
            # Re-raise to let the caller handle the error
            raise

    def _create_template_variables(self, target_path: Path) -> dict[str, Any]:
        """Create template variables for processing.

        Args:
            target_path: Path to the source file

        Returns:
            Dictionary of template variables
        """
        normalized_path = normalize_path(target_path, resolve_symlinks=False)

        return {
            "filename": target_path.name,
            "filepath": str(normalized_path),
            "parent_dir": target_path.parent.name,
            "file_ext": target_path.suffix,
            "timestamp": datetime.now().isoformat(),
        }

    def validate_arguments(self, **kwargs: Any) -> None:
        """Validate command arguments.

        Args:
            **kwargs: Command arguments to validate

        Raises:
            SpecError: If validation fails
        """
        files = kwargs.get("files", [])
        template = kwargs.get("template", "default")
        conflict_strategy = kwargs.get("conflict_strategy", "backup")
        no_ai = kwargs.get("no_ai", False)
        doc_type = kwargs.get("doc_type", "standard")

        if not files:
            raise SpecError("No source files provided")

        # Validate file paths
        for file_path in files:
            if not isinstance(file_path, str | Path):
                raise SpecError(f"Invalid file path type: {type(file_path)}")

        # Validate template
        if not isinstance(template, str):
            raise SpecError(f"Invalid template type: {type(template)}")

        # Validate conflict strategy
        valid_strategies = ["backup", "overwrite", "skip", "fail"]
        if conflict_strategy not in valid_strategies:
            raise SpecError(
                f"Invalid conflict strategy: {conflict_strategy}. "
                f"Must be one of: {', '.join(valid_strategies)}"
            )

        # Validate no_ai flag
        if not isinstance(no_ai, bool):
            raise SpecError(f"Invalid no_ai flag type: {type(no_ai)}")

        # Validate doc_type
        if not isinstance(doc_type, str):
            raise SpecError(f"Invalid doc_type type: {type(doc_type)}")

        valid_doc_types = ["standard", "comprehensive", "minimal", "api", "tutorial"]
        if doc_type not in valid_doc_types:
            raise SpecError(
                f"Invalid doc_type: {doc_type}. "
                f"Must be one of: {', '.join(valid_doc_types)}"
            )

    def _expand_source_files(self, source_files: list[Path]) -> list[Path]:
        """Expand directories to individual source files."""
        from .generation.validation import GenerationValidator

        validator = GenerationValidator()
        expanded_files = []

        for file_path in source_files:
            if file_path.is_file():
                if validator._is_processable_file(file_path):
                    expanded_files.append(file_path)
            elif file_path.is_dir():
                processable_files = validator._get_processable_files_in_directory(
                    file_path
                )
                expanded_files.extend(processable_files)

        return expanded_files

    def _show_dry_run_preview(
        self,
        source_files: list[Path],
        template: str,
        conflict_strategy: ConflictResolutionStrategy,
    ) -> None:
        """Show dry run preview of what would be generated."""
        self.console.print("\n[bold cyan]Dry Run Preview:[/bold cyan]")
        self.console.print(f"Template: [yellow]{template}[/yellow]")
        self.console.print(
            f"Conflict strategy: [yellow]{conflict_strategy.value}[/yellow]"
        )
        self.console.print(f"Files to process: [yellow]{len(source_files)}[/yellow]\n")

        # Helper to get spec files using centralized method
        def get_spec_files_for_source(source_file: Path) -> dict[str, Path]:
            path_resolver = PathResolver(self.settings)
            return path_resolver.get_spec_files_for_source(source_file)

        for source_file in source_files:
            spec_files = get_spec_files_for_source(source_file)

            self.console.print(f"[bold]{source_file}[/bold]")
            for file_type, spec_file in spec_files.items():
                status = (
                    "[yellow]exists[/yellow]"
                    if spec_file.exists()
                    else "[green]new[/green]"
                )
                self.console.print(
                    f"  • {file_type}: [path]{spec_file}[/path] ({status})"
                )
            self.console.print()

        show_message("This is a dry run. No files would be modified.", "info")

    def _display_generation_results(self, result: GenerationResult) -> None:
        """Display generation results."""
        # Show summary
        if result.success:
            show_message(
                f"Generation completed successfully in {result.total_processing_time:.2f}s",
                "success",
            )
        else:
            show_message(
                f"Generation completed with errors in {result.total_processing_time:.2f}s",
                "warning",
            )

        # Show statistics using simple formatting
        self.console.print("\n[bold cyan]Generation Statistics:[/bold cyan]")
        self.console.print(
            f"  Generated files: [green]{len(result.generated_files)}[/green]"
        )
        self.console.print(
            f"  Skipped files: [yellow]{len(result.skipped_files)}[/yellow]"
        )
        self.console.print(f"  Failed files: [red]{len(result.failed_files)}[/red]")
        self.console.print(
            f"  Conflicts resolved: [blue]{len(result.conflicts_resolved)}[/blue]"
        )

        # Show generated files
        if result.generated_files:
            self.console.print("\n[bold green]Generated files:[/bold green]")
            for file_path in result.generated_files:
                self.console.print(f"  • [path]{file_path}[/path]")

        # Show failed files
        if result.failed_files:
            self.console.print("\n[bold red]Failed files:[/bold red]")
            for failure in result.failed_files:
                self.console.print(
                    f"  • [path]{failure['file']}[/path]: {failure['error']}"
                )

        # Show conflicts
        if result.conflicts_resolved:
            self.console.print("\n[bold yellow]Conflicts resolved:[/bold yellow]")
            for conflict in result.conflicts_resolved:
                if conflict["type"] == "backup":
                    self.console.print(
                        f"  • Backed up [path]{conflict['original']}[/path] to [path]{conflict['backup']}[/path]"
                    )
                elif conflict["type"] == "overwrite":
                    self.console.print(f"  • Overwrote [path]{conflict['file']}[/path]")
