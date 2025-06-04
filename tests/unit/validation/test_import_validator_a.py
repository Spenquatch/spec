"""Tests for ImportValidator - Slice 3.1a: Core dataclass and stub validator."""

import ast

import pytest

from spec_cli.validation.import_validator import ImportValidator, ImportViolation


class TestImportViolation:
    """Test ImportViolation dataclass."""

    def test_import_violation_when_valid_params_then_creates_successfully(self):
        """Test ImportViolation creates with valid parameters."""
        violation = ImportViolation(
            module_name="spec_cli.core.test", line_no=42, reason="Test violation reason"
        )

        assert violation.module_name == "spec_cli.core.test"
        assert violation.line_no == 42
        assert violation.reason == "Test violation reason"

    def test_import_violation_when_minimal_data_then_stores_correctly(self):
        """Test ImportViolation with minimal data."""
        violation = ImportViolation(module_name="test", line_no=1, reason="error")

        assert violation.module_name == "test"
        assert violation.line_no == 1
        assert violation.reason == "error"


class TestImportValidator:
    """Test ImportValidator class."""

    @pytest.fixture
    def sample_ast_tree(self):
        """Create sample AST tree for testing."""
        source_code = """
import os
from pathlib import Path

def test_function():
    pass
"""
        return ast.parse(source_code)

    def test_import_validator_when_valid_ast_then_initializes_successfully(
        self, sample_ast_tree
    ):
        """Test ImportValidator initializes with valid AST."""
        validator = ImportValidator(sample_ast_tree)

        assert validator.tree == sample_ast_tree
        assert isinstance(validator.tree, ast.AST)

    def test_import_validator_when_invalid_tree_then_raises_type_error(self):
        """Test ImportValidator raises TypeError with invalid tree."""
        with pytest.raises(TypeError, match="tree must be an AST object"):
            ImportValidator("not an ast")

    def test_import_validator_when_none_tree_then_raises_type_error(self):
        """Test ImportValidator raises TypeError with None tree."""
        with pytest.raises(TypeError, match="tree must be an AST object"):
            ImportValidator(None)

    def test_validate_when_called_then_returns_violations_for_disallowed_imports(
        self, sample_ast_tree
    ):
        """Test validate returns violations for disallowed imports."""
        validator = ImportValidator(sample_ast_tree)
        result = validator.validate()

        # sample_ast_tree contains 'import os' which is disallowed
        assert len(result) == 1
        assert isinstance(result, list)
        assert result[0].module_name == "os"
        assert "is not allowed" in result[0].reason

    def test_validate_when_complex_ast_then_returns_violations_for_disallowed_imports(
        self,
    ):
        """Test validate returns violations for disallowed imports in complex AST."""
        complex_source = """
import os
import sys
from pathlib import Path
from typing import List, Dict

class TestClass:
    def method(self):
        import json
        from collections import defaultdict
"""
        tree = ast.parse(complex_source)
        validator = ImportValidator(tree)
        result = validator.validate()

        # Should find violations for 'os' and 'sys'
        assert len(result) == 2
        assert isinstance(result, list)

        violation_modules = {v.module_name for v in result}
        assert violation_modules == {"os", "sys"}
