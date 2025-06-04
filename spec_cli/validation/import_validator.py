"""Import validation utilities for spec-cli."""

import ast
from dataclasses import dataclass
from typing import List


@dataclass
class ImportViolation:
    """Represents an import policy violation.

    Args:
        module_name: Name of the module with the violation
        line_no: Line number where violation occurs
        reason: Description of why this is a violation

    Example:
        violation = ImportViolation(
            module_name="spec_cli.core.repository",
            line_no=15,
            reason="Core module imports UI component"
        )
    """

    module_name: str
    line_no: int
    reason: str


def extract_import_nodes(tree: ast.AST) -> List[ast.Import]:
    """Extract all import statements from AST tree.

    Args:
        tree: AST tree to extract imports from

    Returns:
        List of ast.Import nodes found in the tree

    Example:
        tree = ast.parse("import os\\nimport sys")
        imports = extract_import_nodes(tree)
        assert len(imports) == 2
    """
    if not isinstance(tree, ast.AST):
        raise TypeError("tree must be an AST object")

    import_nodes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            import_nodes.append(node)

    return import_nodes


def extract_from_import_nodes(tree: ast.AST) -> List[ast.ImportFrom]:
    """Extract all from-import statements from AST tree.

    Args:
        tree: AST tree to extract from-imports from

    Returns:
        List of ast.ImportFrom nodes found in the tree

    Example:
        tree = ast.parse("from pathlib import Path\\nfrom typing import List")
        from_imports = extract_from_import_nodes(tree)
        assert len(from_imports) == 2
    """
    if not isinstance(tree, ast.AST):
        raise TypeError("tree must be an AST object")

    from_import_nodes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            from_import_nodes.append(node)

    return from_import_nodes


class ImportValidator:
    """Validates import statements against policy rules.

    Args:
        tree: AST tree to validate

    Example:
        tree = ast.parse(source_code)
        validator = ImportValidator(tree)
        violations = validator.validate()
    """

    def __init__(self, tree: ast.AST):
        """Initialize validator with AST tree.

        Args:
            tree: AST tree to validate

        Raises:
            TypeError: If tree is not an AST object
        """
        if not isinstance(tree, ast.AST):
            raise TypeError("tree must be an AST object")

        self.tree = tree

    def validate(self) -> List[ImportViolation]:
        """Validate imports against policy rules.

        Returns:
            List of import violations found

        Note:
            This implementation checks against hardcoded disallowed modules.
            More sophisticated policy rules can be added later.
        """
        violations = []

        # Hardcoded disallowed modules for demonstration
        disallowed_modules = {"os", "sys"}

        # Check regular imports
        import_nodes = extract_import_nodes(self.tree)
        for import_node in import_nodes:
            for alias in import_node.names:
                if alias.name in disallowed_modules:
                    violations.append(
                        ImportViolation(
                            module_name=alias.name,
                            line_no=import_node.lineno,
                            reason=f"Module '{alias.name}' is not allowed",
                        )
                    )

        # Check from-imports
        from_import_nodes = extract_from_import_nodes(self.tree)
        for from_import_node in from_import_nodes:
            if (
                from_import_node.module
                and from_import_node.module in disallowed_modules
            ):
                violations.append(
                    ImportViolation(
                        module_name=from_import_node.module,
                        line_no=from_import_node.lineno,
                        reason=f"Module '{from_import_node.module}' is not allowed",
                    )
                )

        return violations
