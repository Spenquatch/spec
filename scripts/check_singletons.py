#!/usr/bin/env python3
"""Pre-commit hook for singleton pattern detection."""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from spec_cli.utils.singleton_detection import scan_for_singleton_patterns
except ImportError as e:
    print(f"ERROR: Cannot import singleton detection: {e}")
    sys.exit(1)


def main() -> int:
    """Run singleton detection on provided files."""
    if len(sys.argv) < 2:
        print("Usage: check_singletons.py <file1> [file2] ...")
        return 1

    violation_count = 0

    for file_path_str in sys.argv[1:]:
        file_path = Path(file_path_str)

        # Only check Python files
        if not file_path.suffix == ".py":
            continue

        if not file_path.exists():
            print(f"WARNING: File not found: {file_path}")
            continue

        try:
            violations = scan_for_singleton_patterns(file_path)

            if violations:
                print(f"\nSingleton violations found in {file_path}:")
                for violation in violations:
                    print(f"  Line {violation.line_number}: {violation.description}")
                    print(f"    Code: {violation.code_snippet}")
                violation_count += len(violations)

        except Exception as e:
            print(f"ERROR checking {file_path}: {e}")
            return 1

    if violation_count > 0:
        print(f"\nFAILED: Found {violation_count} singleton pattern violations")
        print("Please remove singleton patterns before committing.")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
