#!/bin/bash
# Poetry wrapper commands for quality checks
set -euo pipefail

COMMAND="${1:-}"

case "$COMMAND" in
    "dev-setup")
        echo "🚀 Setting up development environment..."
        poetry install
        poetry run pre-commit install
        echo "Development environment initialized"
        ;;

    "type-check")
        echo "Running MyPy type checking..."
        poetry run mypy spec_cli/ --strict --no-error-summary
        ;;

    "lint")
        echo "Running Ruff linting with auto-fix..."
        poetry run ruff check . --fix
        ;;

    "format")
        echo "Formatting code with Ruff..."
        poetry run ruff format .
        ;;

    "format-check")
        echo "Checking code formatting..."
        poetry run ruff format --check .
        ;;

    "docs")
        echo "Checking documentation style..."
        poetry run pydocstyle spec_cli/
        ;;

    "security")
        echo "Running security scan with Bandit..."
        poetry run bandit -r spec_cli/ -lll
        ;;

    "audit")
        echo "Running dependency vulnerability scan..."
        poetry run pip-audit
        ;;

    "test")
        echo "Running tests with coverage..."
        poetry run pytest -v --strict-markers --strict-config --cov=spec_cli --cov-report=term-missing --cov-fail-under=90 --maxfail=1
        ;;

    "platform-check")
        echo "Platform compatibility check..."
        python -c "import platform; print(f'Platform: {platform.system()} {platform.release()}'); import sys; print(f'Python: {sys.version}')"
        ;;

    "check-all")
        echo "Running ALL quality checks (pipeline simulation)..."
        ./scripts/check-quality.sh
        ;;

    "update-deps")
        echo "📦 Checking for outdated dependencies..."
        poetry show --outdated
        echo ""
        echo "💡 To update dependencies:"
        echo "   poetry update                    # Update all within version constraints"
        echo "   poetry add package@latest        # Update specific package to latest"
        echo "   poetry lock --no-update          # Update lock file only"
        ;;

    *)
        echo "❌ Unknown command: $COMMAND"
        echo ""
        echo "Available commands:"
        echo "  dev-setup              # Complete environment initialization"
        echo ""
        echo "  # Quality checks (individual)"
        echo "  type-check            # MyPy strict type checking"
        echo "  lint                  # Ruff linting with exit-on-fix"
        echo "  format                # Ruff code formatting"
        echo "  format-check          # Verify formatting without changes"
        echo "  docs                  # Pydocstyle documentation check"
        echo "  security              # Bandit security scan"
        echo "  audit                 # Pip-audit vulnerability scan"
        echo "  test                  # Pytest with strict coverage"
        echo "  platform-check        # Cross-platform compatibility validation"
        echo ""
        echo "  # Comprehensive validation"
        echo "  check-all             # ALL quality gates (pipeline simulation)"
        echo ""
        echo "  # Dependency management"
        echo "  update-deps           # Show outdated + update guidance"
        echo ""
        echo "Usage: $0 <command>"
        exit 1
        ;;
esac
