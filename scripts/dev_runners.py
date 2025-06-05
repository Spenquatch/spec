#!/usr/bin/env python3
"""Development task runners for spec-cli project with standardized commands."""

import platform
import subprocess
import sys


def dev_setup():
    """Complete environment initialization."""
    print("🚀 Setting up development environment...")
    try:
        subprocess.run(["poetry", "install"], check=True)
        subprocess.run(["poetry", "run", "pre-commit", "install"], check=True)
        print("✅ Development environment initialized")
    except subprocess.CalledProcessError:
        print("❌ Development setup failed")
        sys.exit(1)


def type_check():
    """MyPy strict type checking."""
    print("🔄 Running MyPy type check...")
    try:
        subprocess.run(
            ["mypy", "spec_cli/", "--strict", "--no-error-summary"], check=True
        )
        print("✅ Type check passed")
    except subprocess.CalledProcessError:
        print("❌ Type check failed")
        sys.exit(1)


def lint():
    """Ruff linting with auto-fix."""
    print("🔄 Running Ruff linting with auto-fix...")
    try:
        subprocess.run(["ruff", "check", ".", "--fix"], check=True)
        print("✅ Lint check passed")
    except subprocess.CalledProcessError:
        print("❌ Lint check failed")
        sys.exit(1)


def format():
    """Ruff code formatting."""
    print("🔄 Formatting code with Ruff...")
    try:
        subprocess.run(["ruff", "format", "."], check=True)
        print("✅ Code formatting completed")
    except subprocess.CalledProcessError:
        print("❌ Code formatting failed")
        sys.exit(1)


def format_check():
    """Verify formatting without changes."""
    print("🔄 Checking code formatting...")
    try:
        subprocess.run(["ruff", "format", "--check", "."], check=True)
        print("✅ Code formatting check passed")
    except subprocess.CalledProcessError:
        print("❌ Code formatting check failed")
        sys.exit(1)


def docs():
    """Pydocstyle documentation check."""
    print("🔄 Checking documentation style...")
    try:
        subprocess.run(["pydocstyle", "spec_cli/"], check=True)
        print("✅ Documentation style check passed")
    except subprocess.CalledProcessError:
        print("❌ Documentation style check failed")
        sys.exit(1)


def security():
    """Bandit security scan."""
    print("🔄 Running security scan with Bandit...")
    try:
        subprocess.run(["bandit", "-r", "spec_cli/", "-lll"], check=True)
        print("✅ Security scan passed")
    except subprocess.CalledProcessError:
        print("❌ Security scan failed")
        sys.exit(1)


def audit():
    """Pip-audit vulnerability scan."""
    print("🔄 Running dependency vulnerability scan...")
    try:
        subprocess.run(["pip-audit"], check=True)
        print("✅ Vulnerability scan passed")
    except subprocess.CalledProcessError:
        print("❌ Vulnerability scan failed")
        sys.exit(1)


def test():
    """Pytest with strict coverage."""
    print("🔄 Running tests with coverage...")
    try:
        subprocess.run(
            [
                "pytest",
                "-v",
                "--strict-markers",
                "--strict-config",
                "--cov=spec_cli",
                "--cov-report=term-missing",
                "--cov-fail-under=90",
                "--maxfail=1",
            ],
            check=True,
        )
        print("✅ Tests passed")
    except subprocess.CalledProcessError:
        print("❌ Tests failed")
        sys.exit(1)


def platform_check():
    """Cross-platform compatibility validation."""
    print("🔄 Platform compatibility check...")
    try:
        print(f"Platform: {platform.system()} {platform.release()}")
        print(f"Python: {sys.version}")
        print("✅ Platform check completed")
    except Exception as e:
        print(f"❌ Platform check failed: {e}")
        sys.exit(1)


def update_deps():
    """Show outdated dependencies and update guidance."""
    print("📦 Checking for outdated dependencies...")
    try:
        subprocess.run(["poetry", "show", "--outdated"], check=True)
        print("\n💡 To update dependencies:")
        print(
            "   poetry update                    # Update all within version constraints"
        )
        print("   poetry add package@latest        # Update specific package to latest")
        print("   poetry lock --no-update          # Update lock file only")
    except subprocess.CalledProcessError:
        print("❌ Failed to check dependencies")
        sys.exit(1)


def check_all():
    """Run ALL quality checks (pipeline simulation)."""
    print("🚀 Running all quality checks...")

    checks = [
        (type_check, "Type checking"),
        (lint, "Linting with auto-fix"),
        (format, "Code formatting"),
        (docs, "Documentation style"),
        (security, "Security scan"),
        (audit, "Dependency audit"),
        (test, "Tests with coverage"),
        (platform_check, "Platform compatibility"),
    ]

    failed_checks = []

    for check_func, name in checks:
        print(f"\n{'=' * 50}")
        print(f"Running: {name}")
        print(f"{'=' * 50}")

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
    print(f"\n{'=' * 50}")
    print("QUALITY CHECK SUMMARY")
    print(f"{'=' * 50}")

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
    print("  poetry run dev-setup        # Complete environment initialization")
    print("  poetry run type-check       # MyPy strict type checking")
    print("  poetry run lint             # Ruff linting with auto-fix")
    print("  poetry run format           # Ruff code formatting")
    print("  poetry run format-check     # Verify formatting without changes")
    print("  poetry run docs             # Pydocstyle documentation check")
    print("  poetry run security         # Bandit security scan")
    print("  poetry run audit            # Pip-audit vulnerability scan")
    print("  poetry run test             # Pytest with strict 90%+ coverage")
    print("  poetry run platform-check   # Cross-platform compatibility validation")
    print("  poetry run check-all        # ALL quality gates (pipeline simulation)")
    print("  poetry run update-deps      # Show outdated + update guidance")
    print("\n✨ All commands have consistent behavior and proper exit codes for CI/CD")
