"""Check imports command for spec-cli."""

import ast
from pathlib import Path

from spec_cli.validation.import_validator import ImportValidator, ImportViolation


def check_imports_in_file(file_path: Path) -> list[ImportViolation]:
    """Check imports in a single Python file.

    Args:
        file_path: Path to Python file to check

    Returns:
        List of import violations found

    Raises:
        FileNotFoundError: If file doesn't exist
        SyntaxError: If file has syntax errors

    Example:
        violations = check_imports_in_file(Path("test.py"))
        for violation in violations:
            print(f"Line {violation.line_no}: {violation.reason}")
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not file_path.suffix == ".py":
        return []  # Only check Python files

    try:
        source_code = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_code)
        validator = ImportValidator(tree)
        return validator.validate()
    except SyntaxError as e:
        raise SyntaxError(f"Syntax error in {file_path}: {e}") from e


def cmd_check_imports(file_paths: list[str]) -> int:
    """Check imports command entry point.

    Args:
        file_paths: List of file paths to check

    Returns:
        Exit code (0 for success, 1 for violations found)

    Example:
        exit_code = cmd_check_imports(["src/main.py", "tests/test_main.py"])
    """
    total_violations = 0

    for file_path_str in file_paths:
        file_path = Path(file_path_str)
        try:
            violations = check_imports_in_file(file_path)
            if violations:
                print(f"\nViolations in {file_path}:")
                for violation in violations:
                    print(f"  Line {violation.line_no}: {violation.reason}")
                    total_violations += 1
        except (FileNotFoundError, SyntaxError) as e:
            print(f"Error checking {file_path}: {e}")
            return 1

    if total_violations > 0:
        print(f"\nTotal violations found: {total_violations}")
        return 1
    else:
        print("No import violations found.")
        return 0
