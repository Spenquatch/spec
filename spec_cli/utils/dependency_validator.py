"""Architecture dependency validation utilities.

This module provides tools to validate that the codebase follows the expected
architecture hierarchy: Utils → Config → Core → CLI. It helps detect and report
any violations of this dependency hierarchy.
"""

import ast
from pathlib import Path
from typing import Any


class LayerDefinition:
    """Defines a layer in the architecture hierarchy."""

    def __init__(self, name: str, allowed_imports: list[str]) -> None:
        """Initialize layer definition.

        Args:
            name: Name of the layer (e.g., 'utils', 'config')
            allowed_imports: List of layer names this layer can import from
        """
        self.name = name
        self.allowed_imports = allowed_imports


class ImportViolation:
    """Represents a violation of the architecture dependency rules."""

    def __init__(
        self,
        file_path: Path,
        importing_layer: str,
        imported_layer: str,
        line_number: int,
    ) -> None:
        """Initialize import violation.

        Args:
            file_path: Path to the file containing the violation
            importing_layer: The layer doing the import
            imported_layer: The layer being imported
            line_number: Line number of the import statement
        """
        self.file_path = file_path
        self.importing_layer = importing_layer
        self.imported_layer = imported_layer
        self.line_number = line_number

    def to_dict(self) -> dict[str, Any]:
        """Convert violation to dictionary representation."""
        return {
            "file": str(self.file_path),
            "importing_layer": self.importing_layer,
            "imported_layer": self.imported_layer,
            "line": self.line_number,
            "message": f"{self.importing_layer} layer imports from {self.imported_layer} layer",
        }


class DependencyValidator:
    """Validates architecture dependencies in the codebase."""

    def __init__(self, codebase_path: Path, expected_hierarchy: list[str]) -> None:
        """Initialize dependency validator.

        Args:
            codebase_path: Root path of the codebase to validate
            expected_hierarchy: List of layer names in order from lowest to highest
                               e.g., ['utils', 'config', 'core', 'cli']
        """
        self.codebase_path = codebase_path
        self.expected_hierarchy = expected_hierarchy
        self.layer_definitions = self._create_layer_definitions()

    def _create_layer_definitions(self) -> dict[str, LayerDefinition]:
        """Create layer definitions based on expected hierarchy.

        Returns:
            Dictionary mapping layer names to their definitions
        """
        definitions = {}

        for i, layer_name in enumerate(self.expected_hierarchy):
            # Each layer can only import from layers below it in the hierarchy
            allowed_imports = self.expected_hierarchy[:i]
            definitions[layer_name] = LayerDefinition(layer_name, allowed_imports)

        return definitions

    def _get_layer_from_path(self, file_path: Path) -> str | None:
        """Determine which layer a file belongs to based on its path.

        Args:
            file_path: Path to the file

        Returns:
            Layer name or None if not part of any defined layer
        """
        # Get relative path from codebase root
        try:
            relative_path = file_path.relative_to(self.codebase_path)
        except ValueError:
            return None

        # Check if it's in spec_cli directory
        parts = relative_path.parts
        if len(parts) < 2 or parts[0] != "spec_cli":
            return None

        # Get the module name
        module_name = parts[1]

        # Map module directories to layers
        if module_name in self.expected_hierarchy:
            return module_name

        # Handle special cases
        if module_name in [
            "file_processing",
            "file_system",
            "git",
            "templates",
            "validation",
        ]:
            # These are considered part of core functionality
            return "core" if "core" in self.expected_hierarchy else None

        if module_name == "ui":
            # UI is at the same level as CLI
            return "cli" if "cli" in self.expected_hierarchy else None

        if module_name == "logging":
            # Logging is a utility
            return "utils" if "utils" in self.expected_hierarchy else None

        return None

    def _extract_imports(self, file_path: Path) -> list[tuple[str, int]]:
        """Extract import statements from a Python file.

        Args:
            file_path: Path to the Python file

        Returns:
            List of tuples containing (imported_module, line_number)
        """
        imports: list[tuple[str, int]] = []

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
        except Exception:
            return imports

        try:
            tree = ast.parse(content)
        except SyntaxError:
            return imports

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith("spec_cli"):
                        imports.append((alias.name, node.lineno))
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith("spec_cli"):
                    imports.append((node.module, node.lineno))

        return imports

    def _check_import_validity(
        self, importing_file: Path, imported_module: str, line_number: int
    ) -> ImportViolation | None:
        """Check if an import violates architecture rules.

        Args:
            importing_file: Path to the file doing the import
            imported_module: Name of the module being imported
            line_number: Line number of the import

        Returns:
            ImportViolation if rules are violated, None otherwise
        """
        # Get layer of the importing file
        importing_layer = self._get_layer_from_path(importing_file)
        if not importing_layer:
            return None

        # Parse the imported module to determine its layer
        if not imported_module.startswith("spec_cli"):
            return None

        parts = imported_module.split(".")
        if len(parts) < 2:
            return None

        imported_module_name = parts[1]

        # Map imported module to layer
        imported_layer = None
        if imported_module_name in self.expected_hierarchy:
            imported_layer = imported_module_name
        elif imported_module_name in [
            "file_processing",
            "file_system",
            "git",
            "templates",
            "validation",
        ]:
            imported_layer = "core"
        elif imported_module_name == "ui":
            imported_layer = "cli"
        elif imported_module_name == "logging":
            imported_layer = "utils"

        if not imported_layer:
            return None

        # Check if the import is allowed
        layer_def = self.layer_definitions.get(importing_layer)
        if not layer_def:
            return None

        if (
            imported_layer not in layer_def.allowed_imports
            and imported_layer != importing_layer
        ):
            return ImportViolation(
                importing_file, importing_layer, imported_layer, line_number
            )

        return None

    def validate_import_hierarchy(self) -> list[str]:
        """Validate the import hierarchy of the codebase.

        Returns:
            List of violation messages, empty if no violations found
        """
        violations: list[ImportViolation] = []

        # Find all Python files in the codebase
        spec_cli_path = self.codebase_path / "spec_cli"
        if not spec_cli_path.exists():
            return ["spec_cli directory not found"]

        python_files = list(spec_cli_path.rglob("*.py"))

        # Skip test files
        python_files = [f for f in python_files if "test" not in f.parts]

        # Check each file for violations
        for file_path in python_files:
            imports = self._extract_imports(file_path)

            for imported_module, line_number in imports:
                violation = self._check_import_validity(
                    file_path, imported_module, line_number
                )
                if violation:
                    violations.append(violation)

        # Format violations as messages
        messages = []
        for violation in violations:
            relative_path = violation.file_path.relative_to(self.codebase_path)
            message = (
                f"{relative_path}:{violation.line_number} - "
                f"{violation.importing_layer} imports from {violation.imported_layer}"
            )
            messages.append(message)

        return messages

    def generate_validation_report(self) -> dict[str, Any]:
        """Generate a comprehensive validation report.

        Returns:
            Dictionary containing validation results and statistics
        """
        violations = []
        layer_stats: dict[str, dict[str, int]] = {}

        # Initialize layer statistics
        for layer_name in self.expected_hierarchy:
            layer_stats[layer_name] = {"files": 0, "imports": 0, "violations": 0}

        # Find all Python files
        spec_cli_path = self.codebase_path / "spec_cli"
        if not spec_cli_path.exists():
            return {
                "success": False,
                "error": "spec_cli directory not found",
                "violations": [],
                "statistics": {},
            }

        python_files = list(spec_cli_path.rglob("*.py"))
        python_files = [f for f in python_files if "test" not in f.parts]

        # Analyze each file
        for file_path in python_files:
            layer = self._get_layer_from_path(file_path)
            if layer is not None and layer in layer_stats:
                layer_stats[layer]["files"] += 1

            imports = self._extract_imports(file_path)

            for imported_module, line_number in imports:
                if layer is not None and layer in layer_stats:
                    layer_stats[layer]["imports"] += 1

                violation = self._check_import_validity(
                    file_path, imported_module, line_number
                )
                if violation:
                    violations.append(violation.to_dict())
                    if layer is not None and layer in layer_stats:
                        layer_stats[layer]["violations"] += 1

        # Calculate compliance percentage
        total_imports = sum(stats["imports"] for stats in layer_stats.values())
        total_violations = len(violations)
        compliance_percentage = (
            ((total_imports - total_violations) / total_imports * 100)
            if total_imports > 0
            else 100
        )

        return {
            "success": len(violations) == 0,
            "violations": violations,
            "statistics": {
                "total_files": len(python_files),
                "total_imports": total_imports,
                "total_violations": total_violations,
                "compliance_percentage": round(compliance_percentage, 2),
                "layer_statistics": layer_stats,
            },
            "expected_hierarchy": self.expected_hierarchy,
        }


# Convenience function
def validate_import_hierarchy(
    codebase_path: Path | None = None, expected_hierarchy: list[str] | None = None
) -> list[str]:
    """Validate import hierarchy for the codebase.

    Args:
        codebase_path: Root path of the codebase (defaults to current directory)
        expected_hierarchy: Expected layer hierarchy (defaults to standard spec-cli hierarchy)

    Returns:
        List of violation messages
    """
    if codebase_path is None:
        codebase_path = Path.cwd()

    if expected_hierarchy is None:
        expected_hierarchy = ["utils", "config", "core", "cli"]

    validator = DependencyValidator(codebase_path, expected_hierarchy)
    return validator.validate_import_hierarchy()
