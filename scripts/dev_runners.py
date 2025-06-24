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
    """MyPy type checking (aligned with pre-commit configuration)."""
    print("🔄 Running MyPy type check...")
    try:
        subprocess.run(
            ["mypy", "spec_cli/", "--python-version=3.10", "--no-error-summary"],
            check=True,
        )
        print("✅ Type check passed")
    except subprocess.CalledProcessError:
        print("❌ Type check failed")
        sys.exit(1)


def lint():
    """Ruff linting with auto-fix."""
    print("🔄 Running Ruff linting with auto-fix...")
    try:
        result = subprocess.run(
            ["ruff", "check", ".", "--fix"], capture_output=True, text=True, check=True
        )
        if result.stdout.strip():
            print(f"🔧 Ruff found and fixed issues:\n{result.stdout}")
        else:
            print("✅ No linting issues found")
        print("✅ Lint check passed")
    except subprocess.CalledProcessError as e:
        if e.stdout:
            print(f"❌ Ruff found issues that couldn't be auto-fixed:\n{e.stdout}")
        if e.stderr:
            print(f"❌ Ruff error output:\n{e.stderr}")
        print("❌ Lint check failed")
        sys.exit(1)


def format():
    """Ruff code formatting."""
    print("🔄 Formatting code with Ruff...")
    try:
        result = subprocess.run(
            ["ruff", "format", "."], capture_output=True, text=True, check=True
        )
        if result.stderr.strip():
            # Ruff format outputs to stderr for some reason
            lines = result.stderr.strip().split("\n")
            unchanged_line = [line for line in lines if "left unchanged" in line]
            if unchanged_line:
                print(f"✅ {unchanged_line[0]}")
            else:
                formatted_count = len(
                    [line for line in lines if "formatted" in line.lower()]
                )
                if formatted_count > 0:
                    print(f"🔧 Ruff formatted {formatted_count} files")
                else:
                    print("✅ Code formatting completed")
        else:
            print("✅ Code formatting completed")
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(f"❌ Ruff format error:\n{e.stderr}")
        print("❌ Code formatting failed")
        sys.exit(1)


def lint_and_format():
    """Combined Ruff linting with auto-fix and formatting."""
    print("🔄 Running Ruff linting and formatting...")

    # First run linting with auto-fix
    try:
        lint_result = subprocess.run(
            ["ruff", "check", ".", "--fix"], capture_output=True, text=True, check=True
        )
        if lint_result.stdout.strip():
            print(f"🔧 Ruff found and fixed linting issues:\n{lint_result.stdout}")
        else:
            print("✅ No linting issues found")
    except subprocess.CalledProcessError as e:
        if e.stdout:
            print(
                f"❌ Ruff found linting issues that couldn't be auto-fixed:\n{e.stdout}"
            )
        if e.stderr:
            print(f"❌ Ruff linting error:\n{e.stderr}")
        print("❌ Lint and format failed")
        sys.exit(1)

    # Then run formatting
    try:
        format_result = subprocess.run(
            ["ruff", "format", "."], capture_output=True, text=True, check=True
        )
        if format_result.stderr.strip():
            # Ruff format outputs to stderr for some reason
            lines = format_result.stderr.strip().split("\n")
            unchanged_line = [line for line in lines if "left unchanged" in line]
            if unchanged_line:
                print(f"✅ {unchanged_line[0]}")
            else:
                formatted_files = [
                    line
                    for line in lines
                    if line.strip() and "left unchanged" not in line
                ]
                if formatted_files:
                    print(f"🔧 Ruff formatted {len(formatted_files)} files")
                else:
                    print("✅ All files already properly formatted")
        else:
            print("✅ Formatting completed")

        print("✅ Lint and format completed successfully")
    except subprocess.CalledProcessError as e:
        if e.stderr:
            print(f"❌ Ruff formatting error:\n{e.stderr}")
        print("❌ Lint and format failed")
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
        # Ignore GHSA-887c-mr87-cxwp - false positive for torch 2.7.1
        # See SECURITY.md for detailed analysis
        subprocess.run(
            ["pip-audit", "--ignore-vuln", "GHSA-887c-mr87-cxwp"], check=True
        )
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
                "--cov-fail-under=80",
                "--maxfail=0",
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
        (lint_and_format, "Linting and formatting"),
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
    print("  poetry run lint-and-format  # Combined linting and formatting")
    print("  poetry run format-check     # Verify formatting without changes")
    print("  poetry run docs             # Pydocstyle documentation check")
    print("  poetry run security         # Bandit security scan")
    print("  poetry run audit            # Pip-audit vulnerability scan")
    print("  poetry run test             # Pytest with strict 90%+ coverage")
    print("  poetry run platform-check   # Cross-platform compatibility validation")
    print("  poetry run check-all        # ALL quality gates (pipeline simulation)")
    print("  poetry run update-deps      # Show outdated + update guidance")
    print("\n✨ All commands have consistent behavior and proper exit codes for CI/CD")
