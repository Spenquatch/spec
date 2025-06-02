"""Generation workflow coordination."""

import time
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass
from ....templates.generator import SpecContentGenerator
from ....file_processing.conflict_resolver import ConflictResolutionStrategy
from ....git.repository import SpecGitRepository
from ....ui.progress_manager import get_progress_manager
from ....ui.console import get_console
from ....logging.debug import debug_logger
from ....exceptions import SpecGenerationError, SpecValidationError


@dataclass
class GenerationResult:
    """Result of a generation operation."""

    generated_files: List[Path]
    skipped_files: List[Path]
    failed_files: List[Dict[str, Any]]
    conflicts_resolved: List[Dict[str, Any]]
    total_processing_time: float
    success: bool

    @property
    def summary(self) -> Dict[str, Any]:
        """Get operation summary."""
        return {
            "generated": len(self.generated_files),
            "skipped": len(self.skipped_files),
            "failed": len(self.failed_files),
            "conflicts": len(self.conflicts_resolved),
            "time": f"{self.total_processing_time:.2f}s",
            "success": self.success,
        }


class GenerationWorkflow:
    """Coordinates file generation workflow."""

    def __init__(
        self,
        template_name: str = "default",
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.BACKUP_AND_REPLACE,
        auto_commit: bool = False,
        commit_message: Optional[str] = None,
    ):
        """Initialize generation workflow.

        Args:
            template_name: Template to use for generation
            conflict_strategy: How to handle existing files
            auto_commit: Whether to automatically commit generated files
            commit_message: Commit message if auto_commit is True
        """
        self.template_name = template_name
        self.conflict_strategy = conflict_strategy
        self.auto_commit = auto_commit
        self.commit_message = commit_message

        # Initialize components
        self.generator = SpecContentGenerator()
        self.git_repo = SpecGitRepository()
        self.progress_manager = get_progress_manager()
        self.console = get_console()

        debug_logger.log(
            "INFO",
            "GenerationWorkflow initialized",
            template=template_name,
            conflict_strategy=conflict_strategy.value,
        )

    def generate(self, source_files: List[Path]) -> GenerationResult:
        """Generate documentation for source files.

        Args:
            source_files: List of source files to generate docs for

        Returns:
            GenerationResult with operation details
        """
        start_time = time.time()
        generated_files = []
        skipped_files = []
        failed_files = []
        conflicts_resolved = []

        try:
            # Validate inputs
            self._validate_generation_inputs(source_files)

            # Set up progress tracking
            operation_id = f"generation_{int(time.time())}"
            self.progress_manager.start_indeterminate_operation(
                operation_id, f"Generating documentation for {len(source_files)} files"
            )

            try:
                # Process each file
                for source_file in source_files:
                    try:
                        result = self._generate_single_file(source_file)

                        if result["generated"]:
                            generated_files.extend(result["files"])
                        elif result["skipped"]:
                            skipped_files.append(source_file)

                        if result["conflicts"]:
                            conflicts_resolved.extend(result["conflicts"])

                        # Update progress
                        self.progress_manager._update_operation_text(
                            operation_id, f"Generated: {source_file.name}"
                        )

                    except Exception as e:
                        failed_files.append(
                            {
                                "file": str(source_file),
                                "error": str(e),
                                "error_type": type(e).__name__,
                            }
                        )
                        debug_logger.log(
                            "ERROR",
                            "File generation failed",
                            file=str(source_file),
                            error=str(e),
                        )

                # Auto-commit if requested
                if self.auto_commit and generated_files:
                    self._commit_generated_files(generated_files)

            finally:
                self.progress_manager.finish_operation(operation_id)

            # Create result
            processing_time = time.time() - start_time
            success = len(failed_files) == 0

            result = GenerationResult(
                generated_files=generated_files,
                skipped_files=skipped_files,
                failed_files=failed_files,
                conflicts_resolved=conflicts_resolved,
                total_processing_time=processing_time,
                success=success,
            )

            debug_logger.log("INFO", "Generation completed", **result.summary)

            return result

        except Exception as e:
            processing_time = time.time() - start_time
            debug_logger.log("ERROR", "Generation workflow failed", error=str(e))

            return GenerationResult(
                generated_files=generated_files,
                skipped_files=skipped_files,
                failed_files=failed_files
                + [
                    {
                        "file": "workflow",
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                ],
                conflicts_resolved=conflicts_resolved,
                total_processing_time=processing_time,
                success=False,
            )

    def _validate_generation_inputs(self, source_files: List[Path]) -> None:
        """Validate generation inputs."""
        if not source_files:
            raise SpecValidationError("No source files provided for generation")

        # Check template exists - validate template name
        valid_templates = ["default", "minimal", "comprehensive"]
        if self.template_name not in valid_templates:
            raise SpecValidationError(
                f"Template '{self.template_name}' not found. "
                f"Available templates: {', '.join(valid_templates)}"
            )

        # Validate file paths
        for source_file in source_files:
            if not source_file.exists():
                raise SpecValidationError(f"Source file does not exist: {source_file}")

    def _generate_single_file(self, source_file: Path) -> Dict[str, Any]:
        """Generate documentation for a single file."""
        try:
            # Check if spec already exists
            spec_files = self._get_spec_files_for_source(source_file)
            conflicts = []

            # Handle conflicts if files exist
            if any(f.exists() for f in spec_files.values()):
                conflict_result = self._handle_conflicts(source_file, spec_files)

                if conflict_result["skip"]:
                    return {
                        "generated": False,
                        "skipped": True,
                        "files": [],
                        "conflicts": [],
                    }

                conflicts = conflict_result["resolutions"]

            # Generate documentation
            from ....templates.loader import load_template

            template_config = load_template()

            generated_files_dict = self.generator.generate_spec_content(
                source_file, template_config
            )
            generated_files = list(generated_files_dict.values())

            return {
                "generated": True,
                "skipped": False,
                "files": generated_files,
                "conflicts": conflicts,
            }

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Single file generation failed",
                file=str(source_file),
                error=str(e),
            )
            raise SpecGenerationError(
                f"Failed to generate docs for {source_file}: {e}"
            ) from e

    def _handle_conflicts(
        self, source_file: Path, spec_files: Dict[str, Path]
    ) -> Dict[str, Any]:
        """Handle file conflicts based on strategy."""
        resolutions = []

        if self.conflict_strategy == ConflictResolutionStrategy.SKIP:
            return {"skip": True, "resolutions": []}

        elif self.conflict_strategy == ConflictResolutionStrategy.FAIL:
            existing_files = [f for f in spec_files.values() if f.exists()]
            raise SpecGenerationError(
                f"Spec files already exist for {source_file}: {existing_files}"
            )

        elif self.conflict_strategy == ConflictResolutionStrategy.BACKUP_AND_REPLACE:
            for file_type, spec_file in spec_files.items():
                if spec_file.exists():
                    backup_file = self._create_backup(spec_file)
                    resolutions.append(
                        {
                            "type": "backup",
                            "original": str(spec_file),
                            "backup": str(backup_file),
                        }
                    )

        elif self.conflict_strategy == ConflictResolutionStrategy.OVERWRITE:
            for file_type, spec_file in spec_files.items():
                if spec_file.exists():
                    resolutions.append({"type": "overwrite", "file": str(spec_file)})

        return {"skip": False, "resolutions": resolutions}

    def _create_backup(self, file_path: Path) -> Path:
        """Create backup of existing file."""
        timestamp = int(time.time())
        backup_path = file_path.with_suffix(f".backup-{timestamp}{file_path.suffix}")

        import shutil

        shutil.copy2(file_path, backup_path)

        debug_logger.log(
            "INFO", "Backup created", original=str(file_path), backup=str(backup_path)
        )

        return backup_path

    def _get_spec_files_for_source(self, source_file: Path) -> Dict[str, Path]:
        """Get spec file paths for a source file."""
        # Create spec directory path based on source file
        relative_path = (
            source_file.relative_to(Path.cwd())
            if source_file.is_absolute()
            else source_file
        )
        spec_dir = Path(".specs") / relative_path

        return {"index": spec_dir / "index.md", "history": spec_dir / "history.md"}

    def _commit_generated_files(self, generated_files: List[Path]) -> None:
        """Commit generated files to Git."""
        try:
            # Add files to Git
            file_paths_str = [str(f) for f in generated_files]
            self.git_repo.add_files(file_paths_str)

            # Create commit
            message = (
                self.commit_message
                or f"Generate documentation for {len(generated_files)} files"
            )
            commit_hash = self.git_repo.commit(message)

            self.console.print(
                f"[green]Generated files committed: {commit_hash[:8]}[/green]"
            )

            debug_logger.log(
                "INFO",
                "Generated files committed",
                files=len(generated_files),
                commit=commit_hash,
            )

        except Exception as e:
            debug_logger.log("ERROR", "Auto-commit failed", error=str(e))
            self.console.print(
                f"[yellow]Generated files successfully, but auto-commit failed: {e}[/yellow]"
            )


class RegenerationWorkflow(GenerationWorkflow):
    """Workflow for regenerating existing documentation."""

    def __init__(self, **kwargs):
        """Initialize regeneration workflow."""
        # Default to overwrite for regeneration
        if "conflict_strategy" not in kwargs:
            kwargs["conflict_strategy"] = ConflictResolutionStrategy.OVERWRITE

        super().__init__(**kwargs)

    def regenerate(
        self, source_files: List[Path], preserve_history: bool = True
    ) -> GenerationResult:
        """Regenerate documentation for existing files.

        Args:
            source_files: Source files to regenerate docs for
            preserve_history: Whether to preserve history.md files

        Returns:
            GenerationResult with operation details
        """
        # Filter to only files that have existing specs
        existing_spec_files = []

        for source_file in source_files:
            spec_files = self._get_spec_files_for_source(source_file)
            if any(f.exists() for f in spec_files.values()):
                existing_spec_files.append(source_file)

        if not existing_spec_files:
            self.console.print(
                "[yellow]No existing spec files found for regeneration[/yellow]"
            )
            return GenerationResult(
                generated_files=[],
                skipped_files=source_files,
                failed_files=[],
                conflicts_resolved=[],
                total_processing_time=0.0,
                success=True,
            )

        # Preserve history files if requested
        if preserve_history:
            self._preserve_history_files(existing_spec_files)

        # Use parent generation method
        return self.generate(existing_spec_files)

    def _preserve_history_files(self, source_files: List[Path]) -> None:
        """Preserve history.md files during regeneration."""
        import shutil

        for source_file in source_files:
            spec_files = self._get_spec_files_for_source(source_file)
            history_file = spec_files.get("history")

            if history_file and history_file.exists():
                temp_file = history_file.with_suffix(".temp")
                shutil.copy2(history_file, temp_file)

                debug_logger.log(
                    "INFO", "History file preserved", file=str(history_file)
                )


class AddWorkflow:
    """Workflow for adding files to spec tracking."""

    def __init__(self, force: bool = False):
        """Initialize add workflow.

        Args:
            force: Whether to force add ignored files
        """
        self.force = force
        self.git_repo = SpecGitRepository()

        debug_logger.log("INFO", "AddWorkflow initialized", force=force)

    def add_files(self, file_paths: List[Path]) -> Dict[str, Any]:
        """Add files to spec tracking.

        Args:
            file_paths: Files to add to tracking

        Returns:
            Dictionary with operation results
        """
        added_files = []
        skipped_files = []
        failed_files = []

        for file_path in file_paths:
            try:
                # Validate file is in .specs directory
                if not self._is_spec_file(file_path):
                    skipped_files.append(
                        {"file": str(file_path), "reason": "Not in .specs directory"}
                    )
                    continue

                # Add to Git
                self.git_repo.add_files([str(file_path)])
                added_files.append(file_path)

                debug_logger.log("INFO", "File added to tracking", file=str(file_path))

            except Exception as e:
                failed_files.append(
                    {
                        "file": str(file_path),
                        "error": str(e),
                        "error_type": type(e).__name__,
                    }
                )
                debug_logger.log(
                    "ERROR", "Failed to add file", file=str(file_path), error=str(e)
                )

        return {
            "added": added_files,
            "skipped": skipped_files,
            "failed": failed_files,
            "success": len(failed_files) == 0,
        }

    def _is_spec_file(self, file_path: Path) -> bool:
        """Check if file is in .specs directory."""
        try:
            file_path.relative_to(Path(".specs"))
            return True
        except ValueError:
            return False


# Factory functions
def create_generation_workflow(**kwargs) -> GenerationWorkflow:
    """Create a generation workflow with configuration."""
    return GenerationWorkflow(**kwargs)


def create_regeneration_workflow(**kwargs) -> RegenerationWorkflow:
    """Create a regeneration workflow with configuration."""
    return RegenerationWorkflow(**kwargs)


def create_add_workflow(**kwargs) -> AddWorkflow:
    """Create an add workflow with configuration."""
    return AddWorkflow(**kwargs)
