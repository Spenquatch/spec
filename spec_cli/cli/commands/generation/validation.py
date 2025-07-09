"""Generation input validation."""

from pathlib import Path
from typing import Any, cast

from ....exceptions import SpecValidationError
from ....file_processing.conflict_resolver import ConflictResolutionStrategy
from ....logging.debug import debug_logger
from ....utils.path_utils import safe_relative_to


class GenerationValidator:
    """Validates generation command inputs."""

    def __init__(self) -> None:
        """Initialize generation validator."""
        pass

    def validate_generation_input(
        self,
        source_files: list[Path],
        template_name: str,
        conflict_strategy: ConflictResolutionStrategy,
    ) -> dict[str, Any]:
        """Validate complete generation input.

        Args:
            source_files: Source files to validate
            template_name: Template name to validate
            conflict_strategy: Conflict resolution strategy

        Returns:
            Validation result with details

        Raises:
            SpecValidationError: If validation fails
        """
        validation_result: dict[str, Any] = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "file_analysis": [],
        }

        try:
            # Validate file paths
            file_validation = self.validate_file_paths(source_files)
            validation_result["file_analysis"] = file_validation["analysis"]

            if file_validation["errors"]:
                cast(list[str], validation_result["errors"]).extend(
                    file_validation["errors"]
                )
                validation_result["valid"] = False

            if file_validation["warnings"]:
                cast(list[str], validation_result["warnings"]).extend(
                    file_validation["warnings"]
                )

            # Validate template
            template_validation = self.validate_template_selection(template_name)
            if not template_validation["valid"]:
                cast(list[str], validation_result["errors"]).append(
                    template_validation["error"]
                )
                validation_result["valid"] = False

            # Conflict strategy is validated by type annotation

            debug_logger.log(
                "INFO",
                "Generation input validated",
                valid=validation_result["valid"],
                errors=len(cast(list[str], validation_result["errors"])),
                warnings=len(cast(list[str], validation_result["warnings"])),
            )

            return validation_result

        except Exception as e:
            debug_logger.log("ERROR", "Validation failed", error=str(e))
            raise SpecValidationError(f"Validation failed: {e}") from e

    def validate_file_paths(self, file_paths: list[Path]) -> dict[str, Any]:
        """Validate source file paths.

        Args:
            file_paths: File paths to validate

        Returns:
            Validation result with file analysis
        """
        if not file_paths:
            return {
                "valid": False,
                "errors": ["No source files provided"],
                "warnings": [],
                "analysis": [],
            }

        errors = []
        warnings = []
        analysis = []

        for file_path in file_paths:
            file_info = {
                "path": file_path,
                "exists": file_path.exists(),
                "is_file": file_path.is_file() if file_path.exists() else None,
                "is_directory": file_path.is_dir() if file_path.exists() else None,
                "size": file_path.stat().st_size
                if file_path.exists() and file_path.is_file()
                else None,
                "processable": False,
                "existing_specs": {},
            }

            # Check existence
            if not file_path.exists():
                errors.append(f"File does not exist: {file_path}")
                file_info["processable"] = False

            elif file_path.is_dir():
                # Directory - check if it contains processable files
                processable_files = self._get_processable_files_in_directory(file_path)
                file_info["processable"] = len(processable_files) > 0
                file_info["processable_files"] = processable_files

                if not processable_files:
                    warnings.append(
                        f"Directory contains no processable files: {file_path}"
                    )

            elif file_path.is_file():
                # File - check if processable
                file_info["processable"] = self._is_processable_file(file_path)

                if not file_info["processable"]:
                    warnings.append(f"File type may not be processable: {file_path}")

                # Check for existing specs
                existing_specs = self._get_existing_specs(file_path)
                existing_files = {k: v for k, v in existing_specs.items() if v.exists()}
                file_info["existing_specs"] = existing_files

                if existing_files:
                    warnings.append(
                        f"Existing spec files found for {file_path}: {list(existing_files.keys())}"
                    )

            analysis.append(file_info)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "analysis": analysis,
        }

    def validate_template_selection(self, template_name: str) -> dict[str, Any]:
        """Validate template selection.

        Args:
            template_name: Template name to validate

        Returns:
            Validation result
        """
        try:
            available_templates = ["default", "minimal", "comprehensive"]

            if template_name in available_templates:
                return {
                    "valid": True,
                    "template": template_name,
                    "available": available_templates,
                }
            else:
                return {
                    "valid": False,
                    "error": (
                        f"Template '{template_name}' not found. "
                        f"Available templates: {', '.join(available_templates)}"
                    ),
                    "available": available_templates,
                }

        except Exception as e:
            return {
                "valid": False,
                "error": f"Failed to validate template: {e}",
                "available": [],
            }

    def _get_processable_files_in_directory(self, directory: Path) -> list[Path]:
        """Get processable files in a directory."""
        processable_files = []

        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file() and self._is_processable_file(file_path):
                    processable_files.append(file_path)
        except Exception as e:
            debug_logger.log(
                "WARNING",
                "Error scanning directory",
                directory=str(directory),
                error=str(e),
            )

        return processable_files

    def _is_processable_file(self, file_path: Path) -> bool:
        """Check if file is processable for documentation generation."""
        # Common processable file extensions
        processable_extensions = {
            ".py",
            ".js",
            ".ts",
            ".tsx",
            ".jsx",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".rs",
            ".go",
            ".rb",
            ".php",
            ".cs",
            ".md",
            ".rst",
            ".txt",
        }

        # Check extension
        if file_path.suffix.lower() not in processable_extensions:
            return False

        # Check file size (skip very large files)
        try:
            if file_path.stat().st_size > 10 * 1024 * 1024:  # 10MB limit
                return False
        except Exception:
            return False

        # Skip hidden files and common non-source files
        if file_path.name.startswith("."):
            return False

        skip_patterns = ["__pycache__", ".git", "node_modules", ".venv", "venv"]
        if any(pattern in str(file_path) for pattern in skip_patterns):
            return False

        return True

    def _get_existing_specs(self, source_file: Path) -> dict[str, Path]:
        """Get existing spec files for a source file."""
        # Create spec directory path based on source file
        try:
            relative_path = (
                safe_relative_to(source_file, Path.cwd(), strict=True)
                if source_file.is_absolute()
                else source_file
            )
        except Exception:
            # If can't make relative, use the source file as-is
            relative_path = source_file
        spec_dir = Path(".specs") / relative_path

        return {"index": spec_dir / "index.md", "history": spec_dir / "history.md"}


# Convenience functions
def validate_generation_input(
    source_files: list[Path],
    template_name: str,
    conflict_strategy: ConflictResolutionStrategy,
) -> dict[str, Any]:
    """Validate generation input."""
    validator = GenerationValidator()
    return validator.validate_generation_input(
        source_files, template_name, conflict_strategy
    )


def validate_template_selection(template_name: str) -> dict[str, Any]:
    """Validate template selection."""
    validator = GenerationValidator()
    return validator.validate_template_selection(template_name)


def validate_file_paths(file_paths: list[Path]) -> dict[str, Any]:
    """Validate file paths for generation."""
    validator = GenerationValidator()
    return validator.validate_file_paths(file_paths)
