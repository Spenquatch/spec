"""Tests for check_imports command."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.cli.commands.check_imports import check_imports_in_file, cmd_check_imports
from spec_cli.validation.import_validator import ImportViolation


class TestCheckImportsInFile:
    """Test check_imports_in_file function."""

    @pytest.fixture
    def temp_python_file_with_violations(self):
        """Create temporary Python file with import violations."""
        content = """
import os
import json
from sys import argv
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        yield temp_path
        temp_path.unlink()  # Clean up

    @pytest.fixture
    def temp_python_file_clean(self):
        """Create temporary Python file with no violations."""
        content = """
import json
from typing import List
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        yield temp_path
        temp_path.unlink()  # Clean up

    @pytest.fixture
    def temp_non_python_file(self):
        """Create temporary non-Python file."""
        content = "This is not Python code"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        yield temp_path
        temp_path.unlink()  # Clean up

    def test_check_imports_in_file_when_violations_found_then_returns_violations(
        self, temp_python_file_with_violations
    ):
        """Test checking file with violations."""
        violations = check_imports_in_file(temp_python_file_with_violations)

        assert len(violations) == 2  # Should find 'os' and 'sys'

        violation_modules = {v.module_name for v in violations}
        assert violation_modules == {"os", "sys"}

        for violation in violations:
            assert isinstance(violation, ImportViolation)
            assert violation.line_no > 0
            assert "is not allowed" in violation.reason

    def test_check_imports_in_file_when_no_violations_then_returns_empty_list(
        self, temp_python_file_clean
    ):
        """Test checking file with no violations."""
        violations = check_imports_in_file(temp_python_file_clean)

        assert violations == []

    def test_check_imports_in_file_when_non_python_file_then_returns_empty_list(
        self, temp_non_python_file
    ):
        """Test checking non-Python file."""
        violations = check_imports_in_file(temp_non_python_file)

        assert violations == []

    def test_check_imports_in_file_when_file_not_found_then_raises_file_not_found_error(
        self,
    ):
        """Test checking non-existent file."""
        non_existent_path = Path("non_existent_file.py")

        with pytest.raises(FileNotFoundError, match="File not found"):
            check_imports_in_file(non_existent_path)

    def test_check_imports_in_file_when_syntax_error_then_raises_syntax_error(self):
        """Test checking file with syntax errors."""
        content = """
import os
def broken_function(
    # Missing closing parenthesis
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content)
            temp_path = Path(f.name)

        try:
            with pytest.raises(SyntaxError, match="Syntax error"):
                check_imports_in_file(temp_path)
        finally:
            temp_path.unlink()  # Clean up


class TestCmdCheckImports:
    """Test cmd_check_imports function."""

    @pytest.fixture
    def temp_files_with_violations(self):
        """Create multiple temporary files with violations."""
        files = []

        # File 1: Has violations
        content1 = """
import os
import json
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content1)
            files.append(Path(f.name))

        # File 2: Clean
        content2 = """
import json
from typing import List
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(content2)
            files.append(Path(f.name))

        yield files

        # Clean up
        for file_path in files:
            file_path.unlink()

    @pytest.fixture
    def temp_files_clean(self):
        """Create multiple temporary files with no violations."""
        files = []

        for _i in range(2):
            content = """
import json
from typing import List
"""
            with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
                f.write(content)
                files.append(Path(f.name))

        yield files

        # Clean up
        for file_path in files:
            file_path.unlink()

    def test_cmd_check_imports_when_violations_found_then_returns_error_code(
        self, temp_files_with_violations
    ):
        """Test command with violations."""
        file_paths = [str(f) for f in temp_files_with_violations]

        with patch("builtins.print") as mock_print:
            exit_code = cmd_check_imports(file_paths)

        assert exit_code == 1

        # Check that violations were printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        violation_output = "\n".join(print_calls)
        assert "Violations in" in violation_output
        assert "Total violations found:" in violation_output

    def test_cmd_check_imports_when_no_violations_then_returns_success_code(
        self, temp_files_clean
    ):
        """Test command with no violations."""
        file_paths = [str(f) for f in temp_files_clean]

        with patch("builtins.print") as mock_print:
            exit_code = cmd_check_imports(file_paths)

        assert exit_code == 0

        # Check success message was printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert "No import violations found." in print_calls

    def test_cmd_check_imports_when_file_error_then_returns_error_code(self):
        """Test command with file errors."""
        file_paths = ["non_existent_file.py"]

        with patch("builtins.print") as mock_print:
            exit_code = cmd_check_imports(file_paths)

        assert exit_code == 1

        # Check error message was printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        error_output = "\n".join(print_calls)
        assert "Error checking" in error_output

    def test_cmd_check_imports_when_empty_file_list_then_returns_success_code(self):
        """Test command with empty file list."""
        with patch("builtins.print") as mock_print:
            exit_code = cmd_check_imports([])

        assert exit_code == 0

        # Check success message was printed
        print_calls = [call.args[0] for call in mock_print.call_args_list]
        assert "No import violations found." in print_calls
