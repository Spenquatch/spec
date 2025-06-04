from datetime import datetime
from pathlib import Path
from typing import Any

from ..config.settings import SpecSettings, get_settings
from ..exceptions import SpecFileError, SpecTemplateError
from ..file_system.directory_manager import DirectoryManager
from ..file_system.file_metadata import FileMetadataExtractor
from ..file_system.path_utils import normalize_path_separators
from ..logging.debug import debug_logger
from ..utils.path_utils import ensure_directory, normalize_path
from .config import TemplateConfig
from .substitution import TemplateSubstitution


class SpecContentGenerator:
    """Generates spec content files using template substitution."""

    def __init__(self, settings: SpecSettings | None = None):
        self.settings = settings or get_settings()
        self.substitution = TemplateSubstitution()
        self.directory_manager = DirectoryManager(self.settings)
        self.metadata_extractor = FileMetadataExtractor()

        debug_logger.log("INFO", "SpecContentGenerator initialized")

    def generate_spec_content(
        self,
        file_path: Path,
        template: TemplateConfig,
        custom_variables: dict[str, Any] | None = None,
        backup_existing: bool = True,
    ) -> dict[str, Path]:
        """Generate spec content files using template substitution.

        Args:
            file_path: Path to source file (relative to project root)
            template: Template configuration to use
            custom_variables: Optional custom variables for substitution
            backup_existing: Whether to backup existing spec files

        Returns:
            Dictionary mapping file types to created file paths

        Raises:
            SpecTemplateError: If content generation fails
        """
        debug_logger.log(
            "INFO",
            "Generating spec content",
            source_file=str(file_path),
            backup_existing=backup_existing,
        )

        try:
            with debug_logger.timer("generate_spec_content"):
                # Create spec directory and handle existing files
                spec_dir = self._prepare_spec_directory(file_path, backup_existing)

                # Prepare substitution variables
                substitutions = self._prepare_substitutions(
                    file_path, custom_variables or {}, template
                )

                # Generate content files
                created_files = {}

                # Generate index.md content
                with debug_logger.timer("generate_index_content"):
                    index_content = self.substitution.substitute(
                        template.index, substitutions
                    )
                    index_file = spec_dir / "index.md"
                    self._write_content_file(index_file, index_content)
                    created_files["index"] = index_file

                # Generate history.md content
                with debug_logger.timer("generate_history_content"):
                    history_content = self.substitution.substitute(
                        template.history, substitutions
                    )
                    history_file = spec_dir / "history.md"
                    self._write_content_file(history_file, history_content)
                    created_files["history"] = history_file

                debug_logger.log(
                    "INFO",
                    "Spec content generation complete",
                    source_file=str(file_path),
                    files_created=len(created_files),
                    index_length=len(index_content),
                    history_length=len(history_content),
                )

                return created_files

        except Exception as e:
            error_msg = f"Failed to generate spec content for {file_path}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e

    def _prepare_spec_directory(self, file_path: Path, backup_existing: bool) -> Path:
        """Prepare spec directory and handle existing files.

        Args:
            file_path: Path to the source file
            backup_existing: Whether to backup existing files

        Returns:
            Path to the spec directory
        """
        debug_logger.log(
            "DEBUG",
            "Preparing spec directory",
            file_path=str(file_path),
            backup_existing=backup_existing,
        )

        # Ensure .specs directory exists
        self.directory_manager.ensure_specs_directory()

        # Create specific spec directory for this file
        spec_dir = self.directory_manager.create_spec_directory(file_path)

        # Handle existing files if requested
        if backup_existing:
            existing_files = self.directory_manager.check_existing_specs(spec_dir)
            if existing_files["index.md"] or existing_files["history.md"]:
                backup_files = self.directory_manager.backup_existing_files(spec_dir)
                debug_logger.log(
                    "INFO",
                    "Backed up existing spec files",
                    spec_dir=str(spec_dir),
                    backup_count=len(backup_files),
                )

        return spec_dir

    def _prepare_substitutions(
        self,
        file_path: Path,
        custom_variables: dict[str, Any],
        template: TemplateConfig,
    ) -> dict[str, Any]:
        """Prepare complete substitution variables.

        Args:
            file_path: Path to the source file
            custom_variables: Custom variables provided by user
            template: Template configuration

        Returns:
            Complete substitution context
        """
        debug_logger.log(
            "DEBUG",
            "Preparing substitution variables",
            file_path=str(file_path),
            custom_count=len(custom_variables),
        )

        # Base file information
        substitutions = self._get_file_based_variables(file_path)

        # Add template-specific defaults
        template_defaults = self._get_template_defaults(template)
        substitutions.update(template_defaults)

        # Add custom variables (highest precedence)
        substitutions.update(custom_variables)

        debug_logger.log(
            "DEBUG",
            "Substitution variables prepared",
            total_variables=len(substitutions),
        )

        return substitutions

    def _get_file_based_variables(self, file_path: Path) -> dict[str, Any]:
        """Get variables based on file information.

        Args:
            file_path: Path to the source file

        Returns:
            Dictionary of file-based variables
        """
        try:
            # Get file metadata
            file_metadata = self.metadata_extractor.get_file_metadata(file_path)

            # Basic file information with normalized separators
            variables = {
                "filename": file_path.name,
                "filepath": normalize_path_separators(file_path),
                "file_extension": file_path.suffix.lstrip(".") or "txt",
                "file_stem": file_path.stem,
                "parent_directory": file_path.parent.name,
                "relative_path": normalize_path_separators(file_path),
            }

            # Add file metadata if available
            if file_metadata:
                variables.update(
                    {
                        "file_type": file_metadata.get("type", "unknown"),
                        "file_category": file_metadata.get("category", "other"),
                        "is_binary": file_metadata.get("is_binary", False),
                    }
                )

                # Add file size information if available
                if "size" in file_metadata:
                    from ..file_system.file_utils import format_file_size

                    size_bytes = file_metadata["size"]
                    variables["file_size"] = format_file_size(size_bytes)

            debug_logger.log(
                "DEBUG",
                "File-based variables extracted",
                filename=variables["filename"],
                file_type=variables.get("file_type", "unknown"),
            )

            return variables

        except Exception as e:
            debug_logger.log(
                "WARNING",
                "Could not extract file metadata",
                file_path=str(file_path),
                error=str(e),
            )
            # Return minimal variables with normalized separators
            return {
                "filename": file_path.name,
                "filepath": normalize_path_separators(file_path),
                "file_extension": file_path.suffix.lstrip(".") or "txt",
                "file_stem": file_path.stem,
                "parent_directory": file_path.parent.name,
                "relative_path": normalize_path_separators(file_path),
                "file_type": "unknown",
                "file_category": "other",
                "is_binary": False,
                "file_size": "unknown",
            }

    def _get_template_defaults(self, template: TemplateConfig) -> dict[str, Any]:
        """Get default variables from template configuration.

        Args:
            template: Template configuration

        Returns:
            Dictionary of template default variables
        """
        defaults = {
            "template_name": getattr(template, "name", "default"),
            "template_description": template.description or "Default template",
            "template_version": template.version,
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
            "creation_time": datetime.now().strftime("%H:%M:%S"),
        }

        # Add any template-specific defaults if they exist
        if hasattr(template, "defaults") and template.defaults:
            defaults.update(template.defaults)

        return defaults

    def _write_content_file(self, file_path: Path, content: str) -> None:
        """Write content to a file with proper encoding and error handling.

        Args:
            file_path: Path to the file to write
            content: Content to write

        Raises:
            SpecTemplateError: If file writing fails
        """
        try:
            # Ensure parent directory exists using path utilities
            normalized_file_path = normalize_path(file_path)
            ensure_directory(normalized_file_path.parent)
            debug_logger.log(
                "DEBUG",
                "Output directory ensured",
                file_path=str(normalized_file_path),
                output_dir=str(normalized_file_path.parent),
                operation="spec_file_generation",
            )

            # Write content with UTF-8 encoding
            with normalized_file_path.open("w", encoding="utf-8", newline="\n") as f:
                f.write(content)

            debug_logger.log(
                "DEBUG",
                "Content file written",
                file_path=str(file_path),
                content_length=len(content),
            )

        except OSError as e:
            error_msg = f"Failed to write content to {file_path}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e

    def preview_generation(
        self,
        file_path: Path,
        template: TemplateConfig,
        custom_variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Preview what content generation would produce.

        Args:
            file_path: Path to source file
            template: Template configuration
            custom_variables: Optional custom variables

        Returns:
            Dictionary with preview information
        """
        debug_logger.log("DEBUG", "Generating preview", file_path=str(file_path))

        try:
            substitutions = self._prepare_substitutions(
                file_path, custom_variables or {}, template
            )

            # Get substitution previews
            index_preview = self.substitution.preview_substitution(
                template.index, substitutions
            )
            history_preview = self.substitution.preview_substitution(
                template.history, substitutions
            )

            preview = {
                "file_path": str(file_path),
                "template_name": getattr(template, "name", "default"),
                "substitution_variables": len(substitutions),
                "custom_variables_provided": len(custom_variables)
                if custom_variables
                else 0,
                "template_variables": {
                    "index": {
                        "found": index_preview["variables_found"],
                        "resolved": index_preview["variables_resolved"],
                        "unresolved": index_preview["variables_unresolved"],
                        "syntax_issues": index_preview["syntax_issues"],
                    },
                    "history": {
                        "found": history_preview["variables_found"],
                        "resolved": history_preview["variables_resolved"],
                        "unresolved": history_preview["variables_unresolved"],
                        "syntax_issues": history_preview["syntax_issues"],
                    },
                },
                "substitution_sample": {
                    k: v[:100] + "..." if len(v) > 100 else v
                    for k, v in list(substitutions.items())[:5]
                },
                "generation_ready": (
                    len(index_preview["syntax_issues"]) == 0
                    and len(history_preview["syntax_issues"]) == 0
                ),
            }

            return preview

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "Preview generation failed",
                file_path=str(file_path),
                error=str(e),
            )
            return {
                "file_path": str(file_path),
                "error": str(e),
                "generation_ready": False,
            }

    def validate_generation(
        self,
        file_path: Path,
        template: TemplateConfig,
        custom_variables: dict[str, Any] | None = None,
    ) -> list[str]:
        """Validate that generation can proceed without errors.

        Args:
            file_path: Path to source file
            template: Template configuration
            custom_variables: Optional custom variables

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        try:
            # Check if source file exists using normalized path
            normalized_file_path = normalize_path(file_path)
            if not normalized_file_path.exists():
                issues.append(f"Source file does not exist: {normalized_file_path}")
                debug_logger.log(
                    "WARNING",
                    "Source file validation failed",
                    file_path=str(normalized_file_path),
                    operation="template_validation",
                )

            # Validate template configuration
            if not template.index.strip():
                issues.append("Template index content is empty")
            if not template.history.strip():
                issues.append("Template history content is empty")

            # Check template syntax
            index_issues = self.substitution.validate_template_syntax(template.index)
            if index_issues:
                issues.extend([f"Index template: {issue}" for issue in index_issues])

            history_issues = self.substitution.validate_template_syntax(
                template.history
            )
            if history_issues:
                issues.extend(
                    [f"History template: {issue}" for issue in history_issues]
                )

            # Check substitution readiness
            if not issues:  # Only check if no syntax issues
                substitutions = self._prepare_substitutions(
                    file_path, custom_variables or {}, template
                )

                index_vars = self.substitution.get_variables_in_template(template.index)
                history_vars = self.substitution.get_variables_in_template(
                    template.history
                )
                all_vars = index_vars | history_vars

                unresolved = [v for v in all_vars if v not in substitutions]
                if unresolved:
                    issues.append(
                        f"Unresolved variables: {', '.join(sorted(unresolved))}"
                    )

            # Check write permissions
            try:
                spec_dir = self.directory_manager.create_spec_directory(
                    normalized_file_path
                )
                normalized_spec_dir = normalize_path(spec_dir)
                if not normalized_spec_dir.exists():
                    issues.append(
                        f"Cannot create spec directory: {normalized_spec_dir}"
                    )
                    debug_logger.log(
                        "WARNING",
                        "Spec directory creation failed",
                        spec_dir=str(normalized_spec_dir),
                        file_path=str(normalized_file_path),
                        operation="template_validation",
                    )
            except SpecFileError as e:
                issues.append(f"Directory creation error: {e}")

        except Exception as e:
            issues.append(f"Validation error: {e}")

        return issues

    def get_generation_stats(
        self,
        file_path: Path,
        template: TemplateConfig,
        custom_variables: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Get detailed statistics about what generation would produce.

        Args:
            file_path: Path to source file
            template: Template configuration
            custom_variables: Optional custom variables

        Returns:
            Dictionary with generation statistics
        """
        try:
            substitutions = self._prepare_substitutions(
                file_path, custom_variables or {}, template
            )

            index_stats = self.substitution.get_substitution_stats(
                template.index, substitutions
            )
            history_stats = self.substitution.get_substitution_stats(
                template.history, substitutions
            )

            stats = {
                "file_path": str(file_path),
                "template_name": getattr(template, "name", "default"),
                "total_variables_available": len(substitutions),
                "custom_variables_provided": len(custom_variables)
                if custom_variables
                else 0,
                "index_template": {
                    "length": index_stats["template_length"],
                    "variables": index_stats["unique_variables"],
                    "coverage": index_stats["substitution_coverage"],
                    "syntax_valid": index_stats["syntax_valid"],
                },
                "history_template": {
                    "length": history_stats["template_length"],
                    "variables": history_stats["unique_variables"],
                    "coverage": history_stats["substitution_coverage"],
                    "syntax_valid": history_stats["syntax_valid"],
                },
                "generation_ready": (
                    index_stats["syntax_valid"]
                    and history_stats["syntax_valid"]
                    and index_stats["substitution_coverage"] > 0
                    and history_stats["substitution_coverage"] > 0
                ),
            }

            return stats

        except Exception as e:
            return {
                "file_path": str(file_path),
                "error": str(e),
                "generation_ready": False,
            }


# Convenience function for backward compatibility
def generate_spec_content(
    file_path: Path,
    template: TemplateConfig,
    custom_variables: dict[str, Any] | None = None,
) -> dict[str, Path]:
    """Generate spec content (backward compatibility function).

    Args:
        file_path: Path to source file
        template: Template configuration
        custom_variables: Optional custom variables

    Returns:
        Dictionary mapping file types to created file paths
    """
    generator = SpecContentGenerator()
    return generator.generate_spec_content(file_path, template, custom_variables)
