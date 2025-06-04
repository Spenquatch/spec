"""Tests for ImportValidator - Slice 3.1b: AST extraction helpers."""

import ast

import pytest

from spec_cli.validation.import_validator import (
    extract_from_import_nodes,
    extract_import_nodes,
)


class TestExtractImportNodes:
    """Test extract_import_nodes function."""

    @pytest.fixture
    def simple_import_tree(self):
        """Create AST tree with simple imports."""
        source_code = """
import os
import sys
import json
"""
        return ast.parse(source_code)

    @pytest.fixture
    def mixed_import_tree(self):
        """Create AST tree with mixed import types."""
        source_code = """
import os
from pathlib import Path
import sys
from typing import List
"""
        return ast.parse(source_code)

    @pytest.fixture
    def no_import_tree(self):
        """Create AST tree with no imports."""
        source_code = """
def test_function():
    x = 1 + 2
    return x

class TestClass:
    pass
"""
        return ast.parse(source_code)

    def test_extract_import_nodes_when_simple_imports_then_returns_correct_count(
        self, simple_import_tree
    ):
        """Test extraction of simple import statements."""
        imports = extract_import_nodes(simple_import_tree)

        assert len(imports) == 3
        assert all(isinstance(node, ast.Import) for node in imports)

        # Check import names
        import_names = []
        for import_node in imports:
            for alias in import_node.names:
                import_names.append(alias.name)

        assert "os" in import_names
        assert "sys" in import_names
        assert "json" in import_names

    def test_extract_import_nodes_when_mixed_imports_then_returns_only_import_nodes(
        self, mixed_import_tree
    ):
        """Test extraction returns only ast.Import nodes, not ast.ImportFrom."""
        imports = extract_import_nodes(mixed_import_tree)

        assert len(imports) == 2  # Should only get 'import os' and 'import sys'
        assert all(isinstance(node, ast.Import) for node in imports)

        # Verify it's not including from-imports
        import_names = []
        for import_node in imports:
            for alias in import_node.names:
                import_names.append(alias.name)

        assert "os" in import_names
        assert "sys" in import_names
        assert "pathlib" not in import_names  # This is from a from-import

    def test_extract_import_nodes_when_no_imports_then_returns_empty_list(
        self, no_import_tree
    ):
        """Test extraction with no import statements."""
        imports = extract_import_nodes(no_import_tree)

        assert imports == []
        assert isinstance(imports, list)

    def test_extract_import_nodes_when_invalid_tree_then_raises_type_error(self):
        """Test extract_import_nodes raises TypeError with invalid tree."""
        with pytest.raises(TypeError, match="tree must be an AST object"):
            extract_import_nodes("not an ast")

    def test_extract_import_nodes_when_nested_function_imports_then_finds_all(self):
        """Test extraction finds imports within functions."""
        source_code = """
import os

def function():
    import json
    import sys
"""
        tree = ast.parse(source_code)
        imports = extract_import_nodes(tree)

        assert len(imports) == 3
        assert all(isinstance(node, ast.Import) for node in imports)


class TestExtractFromImportNodes:
    """Test extract_from_import_nodes function."""

    @pytest.fixture
    def simple_from_import_tree(self):
        """Create AST tree with simple from-imports."""
        source_code = """
from pathlib import Path
from typing import List, Dict
from collections import defaultdict
"""
        return ast.parse(source_code)

    @pytest.fixture
    def mixed_import_tree(self):
        """Create AST tree with mixed import types."""
        source_code = """
import os
from pathlib import Path
import sys
from typing import List
"""
        return ast.parse(source_code)

    def test_extract_from_import_nodes_when_simple_from_imports_then_returns_correct_count(
        self, simple_from_import_tree
    ):
        """Test extraction of simple from-import statements."""
        from_imports = extract_from_import_nodes(simple_from_import_tree)

        assert len(from_imports) == 3
        assert all(isinstance(node, ast.ImportFrom) for node in from_imports)

        # Check module names
        module_names = [node.module for node in from_imports if node.module]
        assert "pathlib" in module_names
        assert "typing" in module_names
        assert "collections" in module_names

    def test_extract_from_import_nodes_when_mixed_imports_then_returns_only_from_import_nodes(
        self, mixed_import_tree
    ):
        """Test extraction returns only ast.ImportFrom nodes, not ast.Import."""
        from_imports = extract_from_import_nodes(mixed_import_tree)

        assert len(from_imports) == 2  # Should only get from-imports
        assert all(isinstance(node, ast.ImportFrom) for node in from_imports)

        # Verify module names
        module_names = [node.module for node in from_imports if node.module]
        assert "pathlib" in module_names
        assert "typing" in module_names

    def test_extract_from_import_nodes_when_no_from_imports_then_returns_empty_list(
        self,
    ):
        """Test extraction with no from-import statements."""
        source_code = """
import os
import sys

def test():
    pass
"""
        tree = ast.parse(source_code)
        from_imports = extract_from_import_nodes(tree)

        assert from_imports == []
        assert isinstance(from_imports, list)

    def test_extract_from_import_nodes_when_invalid_tree_then_raises_type_error(self):
        """Test extract_from_import_nodes raises TypeError with invalid tree."""
        with pytest.raises(TypeError, match="tree must be an AST object"):
            extract_from_import_nodes(None)

    def test_extract_from_import_nodes_when_relative_imports_then_finds_all(self):
        """Test extraction finds relative imports."""
        source_code = """
from .module import function
from ..parent import Class
from typing import List
"""
        tree = ast.parse(source_code)
        from_imports = extract_from_import_nodes(tree)

        assert len(from_imports) == 3
        assert all(isinstance(node, ast.ImportFrom) for node in from_imports)

        # Check for relative imports (level > 0)
        relative_imports = [node for node in from_imports if node.level > 0]
        assert len(relative_imports) == 2  # .module and ..parent

    def test_extract_from_import_nodes_when_nested_function_imports_then_finds_all(
        self,
    ):
        """Test extraction finds from-imports within functions."""
        source_code = """
from os import path

def function():
    from json import loads
    from sys import argv
"""
        tree = ast.parse(source_code)
        from_imports = extract_from_import_nodes(tree)

        assert len(from_imports) == 3
        assert all(isinstance(node, ast.ImportFrom) for node in from_imports)
