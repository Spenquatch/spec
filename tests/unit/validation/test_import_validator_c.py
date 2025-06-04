"""Tests for ImportValidator - Slice 3.1c: Violation checks and integration."""

import ast

import pytest

from spec_cli.validation.import_validator import ImportValidator, ImportViolation


class TestImportValidatorWithViolations:
    """Test ImportValidator violation detection."""

    @pytest.fixture
    def tree_with_disallowed_imports(self):
        """Create AST tree with disallowed imports."""
        source_code = """
import os
import json
from sys import argv
from pathlib import Path
"""
        return ast.parse(source_code)

    @pytest.fixture
    def tree_with_allowed_imports(self):
        """Create AST tree with only allowed imports."""
        source_code = """
import json
import pathlib
from typing import List
from collections import defaultdict
"""
        return ast.parse(source_code)

    @pytest.fixture
    def tree_no_imports(self):
        """Create AST tree with no imports."""
        source_code = """
def test_function():
    return 42

class TestClass:
    pass
"""
        return ast.parse(source_code)

    def test_validate_when_disallowed_imports_then_returns_violations(
        self, tree_with_disallowed_imports
    ):
        """Test validation finds violations for disallowed imports."""
        validator = ImportValidator(tree_with_disallowed_imports)
        violations = validator.validate()

        # Should find violations for 'os' and 'sys'
        assert len(violations) == 2

        violation_modules = {v.module_name for v in violations}
        assert "os" in violation_modules
        assert "sys" in violation_modules

        # Check violation details
        for violation in violations:
            assert isinstance(violation, ImportViolation)
            assert violation.line_no > 0
            assert "is not allowed" in violation.reason

    def test_validate_when_allowed_imports_then_returns_no_violations(
        self, tree_with_allowed_imports
    ):
        """Test validation finds no violations for allowed imports."""
        validator = ImportValidator(tree_with_allowed_imports)
        violations = validator.validate()

        assert violations == []

    def test_validate_when_no_imports_then_returns_no_violations(self, tree_no_imports):
        """Test validation with no imports."""
        validator = ImportValidator(tree_no_imports)
        violations = validator.validate()

        assert violations == []

    def test_validate_when_mixed_imports_then_returns_only_violations(self):
        """Test validation with mix of allowed and disallowed imports."""
        source_code = """
import os        # Line 2 - disallowed
import json      # Line 3 - allowed
from sys import argv  # Line 4 - disallowed
from typing import List  # Line 5 - allowed
"""
        tree = ast.parse(source_code)
        validator = ImportValidator(tree)
        violations = validator.validate()

        # Should find violations for 'os' and 'sys' only
        assert len(violations) == 2

        violation_modules = {v.module_name for v in violations}
        assert violation_modules == {"os", "sys"}

        # Check line numbers are correct
        violation_lines = {v.line_no for v in violations}
        assert 2 in violation_lines  # import os
        assert 4 in violation_lines  # from sys import argv

    def test_validate_when_multiple_aliases_then_detects_all_violations(self):
        """Test validation with multiple imports on same line."""
        source_code = """
import os, sys, json
"""
        tree = ast.parse(source_code)
        validator = ImportValidator(tree)
        violations = validator.validate()

        # Should find violations for both 'os' and 'sys'
        assert len(violations) == 2

        violation_modules = {v.module_name for v in violations}
        assert violation_modules == {"os", "sys"}

        # Both should be on line 2
        for violation in violations:
            assert violation.line_no == 2

    def test_validate_when_nested_imports_then_finds_all_violations(self):
        """Test validation finds violations in nested scopes."""
        source_code = """
import json

def function():
    import os

    def nested():
        import sys
"""
        tree = ast.parse(source_code)
        validator = ImportValidator(tree)
        violations = validator.validate()

        # Should find violations for 'os' and 'sys'
        assert len(violations) == 2

        violation_modules = {v.module_name for v in violations}
        assert violation_modules == {"os", "sys"}


class TestImportValidatorEdgeCases:
    """Test ImportValidator edge cases."""

    def test_validate_when_from_import_none_module_then_handles_gracefully(self):
        """Test validation handles from-imports with None module."""
        # Create a from-import node with None module (relative import at package level)
        tree = ast.Module(body=[], type_ignores=[])
        from_import = ast.ImportFrom(
            module=None,  # Relative import like "from . import something"
            names=[ast.alias(name="something", asname=None)],
            level=1,
            lineno=1,
            col_offset=0,
        )
        tree.body.append(from_import)

        validator = ImportValidator(tree)
        violations = validator.validate()

        # Should not crash and return no violations (None module not in disallowed set)
        assert violations == []

    def test_validate_when_import_with_asname_then_checks_original_name(self):
        """Test validation checks original module name, not alias."""
        source_code = """
import os as operating_system
from sys import argv as arguments
"""
        tree = ast.parse(source_code)
        validator = ImportValidator(tree)
        violations = validator.validate()

        # Should find violations for 'os' and 'sys' despite aliases
        assert len(violations) == 2

        violation_modules = {v.module_name for v in violations}
        assert violation_modules == {"os", "sys"}
