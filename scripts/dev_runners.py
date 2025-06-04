#!/usr/bin/env python3
"""Simple development task runners for spec-cli project."""

import subprocess
import sys


def type_check():
    """MyPy strict type checking."""
    print("🔄 Running MyPy type check...")
    try:
        subprocess.run(["mypy", "spec_cli/"], check=True)
        print("✅ Type check passed")
    except subprocess.CalledProcessError:
        print("❌ Type check failed")
        sys.exit(1)


def all_tests_cov():
    """Pytest with strict coverage."""
    print("🔄 Running tests with coverage...")
    try:
        subprocess.run(
            [
                "pytest",
                "tests/unit/",
                "--cov=spec_cli",
                "--cov-report=term-missing",
                "--cov-fail-under=80",
                "-v",
            ],
            check=True,
        )
        print("✅ Tests passed")
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
        sys.exit(1)


def ruff_check():
    """Ruff linting check with auto-fix (like pre-commit)."""
    print("🔄 Running Ruff check with auto-fix...")
    try:
        subprocess.run(["ruff", "check", "spec_cli/", "--fix"], check=True)
        print("✅ Ruff check passed")
    except subprocess.CalledProcessError:
        print("❌ Ruff check failed")
        sys.exit(1)


def ruff_format():
    """Ruff code formatting."""
    print("🔄 Running Ruff format...")
    try:
        subprocess.run(["ruff", "format", "spec_cli/"], check=True)
        print("✅ Ruff format completed")
    except subprocess.CalledProcessError:
        print("❌ Ruff format failed")
        sys.exit(1)


def pre_commit():
    """Run all pre-commit hooks."""
    print("🔄 Running pre-commit hooks...")
    try:
        subprocess.run(["pre-commit", "run", "--all-files"], check=True)
        print("✅ Pre-commit hooks passed")
    except subprocess.CalledProcessError:
        print("❌ Pre-commit hooks failed")
        sys.exit(1)


def all_checks():
    """Run all quality checks in sequence."""
    print("🚀 Running all quality checks...")

    checks = [
        (ruff_check, "Ruff linting"),
        (ruff_format, "Ruff formatting"),
        (type_check, "Type checking"),
        (all_tests_cov, "Tests with coverage"),
    ]

    failed_checks = []

    for check_func, name in checks:
        print(f"\n{'='*50}")
        print(f"Running: {name}")
        print(f"{'='*50}")

        # Capture the check function's exit behavior
        original_exit = sys.exit
        exit_called = False
        exit_code = 0

        def mock_exit(code=0):
            nonlocal exit_called, exit_code
            exit_called = True
            exit_code = code

        sys.exit = mock_exit

        try:
            check_func()
        except SystemExit as e:
            exit_code = e.code or 0
            exit_called = True
        except Exception as e:
            exit_code = 1
            exit_called = True
            print(f"❌ {name} failed with exception: {e}")
        finally:
            sys.exit = original_exit

        if exit_called and exit_code != 0:
            failed_checks.append(name)
            print(f"❌ {name} failed")
        else:
            print(f"✅ {name} passed")

    # Summary
    print(f"\n{'='*50}")
    print("QUALITY CHECK SUMMARY")
    print(f"{'='*50}")

    if failed_checks:
        print(f"❌ {len(failed_checks)} checks failed:")
        for check in failed_checks:
            print(f"   - {check}")
        sys.exit(1)
    else:
        print("✅ All quality checks passed!")
        print("🚀 Ready for production!")


if __name__ == "__main__":
    print("🚀 Development Task Runners for spec-cli")
    print("=" * 50)
    print("Available commands:")
    print("  poetry run type-check      # MyPy strict type checking")
    print("  poetry run all-tests-cov   # Pytest with strict 80%+ coverage")
    print("  poetry run ruff-check      # Ruff linting with auto-fix")
    print("  poetry run ruff-format     # Ruff code formatting")
    print("  poetry run all             # Run ALL quality checks (CI simulation)")
    print("\n✨ All commands have consistent behavior and proper exit codes for CI/CD")
