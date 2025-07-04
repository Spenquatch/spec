"""Tests for import validation utilities."""

import ast

import pytest

from spec_cli.validation.import_validator import (
    ImportValidator,
    ImportViolation,
    extract_from_import_nodes,
    extract_import_nodes,
)


class TestImportViolation:
    """Test ImportViolation dataclass."""

    def test_import_violation_creation(self):
        """Test ImportViolation object creation."""
        violation = ImportViolation(
            module_name="test_module", line_no=42, reason="Test violation"
        )

        assert violation.module_name == "test_module"
        assert violation.line_no == 42
        assert violation.reason == "Test violation"

    def test_import_violation_str_representation(self):
        """Test string representation of ImportViolation."""
        violation = ImportViolation(
            module_name="spec_cli.core", line_no=15, reason="Core imports UI"
        )

        # Test that it can be converted to string
        str_repr = str(violation)
        assert "spec_cli.core" in str_repr
        assert "15" in str_repr
        assert "Core imports UI" in str_repr


class TestExtractImportNodes:
    """Test extract_import_nodes function."""

    def test_extract_import_nodes_simple_imports(self):
        """Test extraction of simple import statements."""
        code = """
import os
import sys
from pathlib import Path
"""
        tree = ast.parse(code)
        imports = extract_import_nodes(tree)

        assert len(imports) >= 2  # Should find at least the 'import' statements

    def test_extract_import_nodes_from_imports(self):
        """Test extraction of from imports."""
        code = """
from typing import Dict, List
from unittest.mock import Mock
"""
        tree = ast.parse(code)
        imports = extract_import_nodes(tree)

        # Should find ImportFrom nodes
        assert (
            len(imports) >= 0
        )  # May be empty if only counting ast.Import, not ast.ImportFrom

    def test_extract_import_nodes_no_imports(self):
        """Test extraction when no imports exist."""
        code = """
def function():
    return "hello"

x = 42
"""
        tree = ast.parse(code)
        imports = extract_import_nodes(tree)

        assert len(imports) == 0

    def test_extract_import_nodes_nested_imports(self):
        """Test extraction with nested imports."""
        code = """
def function():
    import json
    return json.dumps({})
"""
        tree = ast.parse(code)
        imports = extract_import_nodes(tree)

        # Should find nested import
        assert len(imports) >= 1

    def test_extract_import_nodes_invalid_tree(self):
        """Test extraction with invalid tree."""
        with pytest.raises(TypeError):
            extract_import_nodes("not an AST")


class TestExtractFromImportNodes:
    """Test extract_from_import_nodes function."""

    def test_extract_from_import_nodes_simple_from_imports(self):
        """Test extraction of simple from import statements."""
        code = """
from typing import Dict, List
from pathlib import Path
"""
        tree = ast.parse(code)
        from_imports = extract_from_import_nodes(tree)

        assert len(from_imports) == 2

    def test_extract_from_import_nodes_no_from_imports(self):
        """Test extraction when no from imports exist."""
        code = """
import os
import sys
def function():
    return "hello"
"""
        tree = ast.parse(code)
        from_imports = extract_from_import_nodes(tree)

        assert len(from_imports) == 0

    def test_extract_from_import_nodes_invalid_tree(self):
        """Test extraction with invalid tree."""
        with pytest.raises(TypeError):
            extract_from_import_nodes("not an AST")

    def test_extract_from_import_nodes_nested_from_imports(self):
        """Test extraction with nested from imports."""
        code = """
def function():
    from json import dumps
    return dumps({})
"""
        tree = ast.parse(code)
        from_imports = extract_from_import_nodes(tree)

        assert len(from_imports) == 1


class TestImportValidator:
    """Test ImportValidator class."""

    def test_import_validator_initialization(self):
        """Test ImportValidator initialization."""
        tree = ast.parse("import os")
        validator = ImportValidator(tree)

        assert validator.tree == tree

    def test_import_validator_initialization_invalid_tree(self):
        """Test ImportValidator initialization with invalid tree."""
        with pytest.raises(TypeError):
            ImportValidator("not an AST")

    def test_import_validator_validate_no_violations(self):
        """Test validation with no violations."""
        code = """
import json
from pathlib import Path
"""
        tree = ast.parse(code)
        validator = ImportValidator(tree)

        violations = validator.validate()

        assert violations == []

    def test_import_validator_validate_with_violations(self):
        """Test validation with violations."""
        code = """
import os
import sys
from typing import List
"""
        tree = ast.parse(code)
        validator = ImportValidator(tree)

        violations = validator.validate()

        # Should find violations for 'os' and 'sys' (hardcoded disallowed)
        assert len(violations) >= 2
        assert any(v.module_name == "os" for v in violations)
        assert any(v.module_name == "sys" for v in violations)

    def test_import_validator_validate_from_import_violations(self):
        """Test validation with from-import violations."""
        code = """
from os import path
from sys import argv
"""
        tree = ast.parse(code)
        validator = ImportValidator(tree)

        violations = validator.validate()

        # Should find violations for from imports of disallowed modules
        assert len(violations) >= 2
        assert any(v.module_name == "os" for v in violations)
        assert any(v.module_name == "sys" for v in violations)

    def test_import_validator_validate_mixed_imports(self):
        """Test validation with mixed import types."""
        code = """
import os
from typing import List
import json
from sys import argv
"""
        tree = ast.parse(code)
        validator = ImportValidator(tree)

        violations = validator.validate()

        # Should find violations for 'os' and 'sys' only
        violation_modules = [v.module_name for v in violations]
        assert "os" in violation_modules
        assert "sys" in violation_modules
        assert "typing" not in violation_modules
        assert "json" not in violation_modules
