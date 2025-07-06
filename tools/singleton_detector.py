#!/usr/bin/env python3
"""Standalone singleton pattern detection tool.

This tool scans Python files in a directory for singleton patterns and reports violations.
It can be used for continuous integration, pre-commit hooks, and development validation.
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import after path modification with noqa to suppress E402
from spec_cli.utils.singleton_detection import (  # noqa: E402
    SingletonDetectionError,
    SingletonViolation,
    scan_for_singleton_patterns,
)

# Configure logging immediately after imports
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class SingletonDetectionSystem:
    """System for detecting singleton patterns in codebase."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.total_files_scanned = 0
        self.total_violations = 0

    def scan_directory(
        self, directory: Path, recursive: bool = True
    ) -> list[SingletonViolation]:
        """Scan directory for singleton patterns.

        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories

        Returns:
            List of all detected violations
        """
        all_violations = []
        python_files = self._find_python_files(directory, recursive)

        for file_path in python_files:
            try:
                violations = scan_for_singleton_patterns(file_path)
                all_violations.extend(violations)
                self.total_files_scanned += 1

                if self.verbose and violations:
                    logger.info("Found %d violations in %s", len(violations), file_path)

            except SingletonDetectionError as e:
                logger.error("Failed to analyze %s: %s", file_path, e)

        self.total_violations = len(all_violations)
        return all_violations

    def _find_python_files(self, directory: Path, recursive: bool) -> list[Path]:
        """Find Python files in directory."""
        if recursive:
            return list(directory.rglob("*.py"))
        else:
            return list(directory.glob("*.py"))

    def format_violations_report(self, violations: list[SingletonViolation]) -> str:
        """Format violations into a human-readable report."""
        if not violations:
            return "No singleton patterns detected."

        lines = [
            f"SINGLETON PATTERN VIOLATIONS DETECTED: {len(violations)} total",
            "=" * 60,
        ]

        # Group violations by file
        violations_by_file: dict[Path, list[SingletonViolation]] = {}
        for violation in violations:
            file_path = violation.file_path
            if file_path not in violations_by_file:
                violations_by_file[file_path] = []
            violations_by_file[file_path].append(violation)

        for file_path, file_violations in violations_by_file.items():
            lines.append(f"\nFile: {file_path}")
            lines.append("-" * 40)

            for violation in file_violations:
                lines.extend(
                    [
                        f"  Line {violation.line_number}: {violation.pattern_type}",
                        f"    Description: {violation.description}",
                        f"    Code: {violation.code_snippet}",
                        "",
                    ]
                )

        lines.extend(
            [
                "=" * 60,
                f"Summary: {len(violations)} violations in {len(violations_by_file)} files",
                f"Files scanned: {self.total_files_scanned}",
            ]
        )

        return "\n".join(lines)

    def format_ci_report(self, violations: list[SingletonViolation]) -> str:
        """Format violations for CI/automation consumption."""
        if not violations:
            return "✓ No singleton patterns detected"

        lines = []
        for violation in violations:
            lines.append(
                f"::error file={violation.file_path},"
                f"line={violation.line_number},"
                f"col={violation.column}::"
                f"{violation.pattern_type}: {violation.description}"
            )

        lines.append(f"✗ {len(violations)} singleton violations detected")
        return "\n".join(lines)

def main() -> int:
    """Main entry point for singleton detection tool."""
    parser = argparse.ArgumentParser(
        description="Detect singleton patterns in Python code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s .                    # Scan current directory recursively
  %(prog)s src/ --no-recursive  # Scan only src/ directory
  %(prog)s . --ci-format        # Output in CI-friendly format
  %(prog)s . --verbose          # Verbose output with details
        """,
    )

    parser.add_argument(
        "directory",
        type=Path,
        help="Directory to scan for singleton patterns",
    )

    parser.add_argument(
        "--recursive",
        action="store_true",
        default=True,
        help="Scan subdirectories recursively (default: True)",
    )

    parser.add_argument(
        "--no-recursive",
        dest="recursive",
        action="store_false",
        help="Do not scan subdirectories",
    )

    parser.add_argument(
        "--ci-format",
        action="store_true",
        help="Output in CI-friendly format",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Verbose output with detailed information",
    )

    parser.add_argument(
        "--fail-on-violations",
        action="store_true",
        default=True,
        help="Exit with non-zero code if violations found (default: True)",
    )

    args = parser.parse_args()

    # Validate directory exists
    if not args.directory.exists():
        logger.error("Directory does not exist: %s", args.directory)
        return 1

    if not args.directory.is_dir():
        logger.error("Path is not a directory: %s", args.directory)
        return 1

    # Initialize detection system
    detector = SingletonDetectionSystem(verbose=args.verbose)

    try:
        # Scan for violations
        violations = detector.scan_directory(args.directory, args.recursive)

        # Output results
        if args.ci_format:
            report = detector.format_ci_report(violations)
        else:
            report = detector.format_violations_report(violations)

        print(report)

        # Return appropriate exit code
        if violations and args.fail_on_violations:
            return 1
        else:
            return 0

    except Exception as e:
        logger.error("Singleton detection failed: %s", e)
        return 1

if __name__ == "__main__":
    sys.exit(main())
