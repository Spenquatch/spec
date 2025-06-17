# Development Workflow Guide

This guide covers the complete development workflow for the `spec-cli` project, including setup, quality standards, testing practices, and contribution guidelines.

## Quick Start

```bash
# Environment setup
uv venv && source .venv/bin/activate  # Create and activate venv
poetry install                        # Install dependencies
poetry run dev-setup                  # Initialize pre-commit hooks

# Development cycle
poetry run check-all                  # Verify environment
# ... make changes ...
poetry run test                       # Run tests during development
poetry run check-all                  # Final validation before commit
git commit -m "feat: description"     # Commit with conventional format
```

## Development Philosophy

### Vertical Slice Development

We follow a **vertical slice** approach - implementing features completely through all layers before moving on:

1. **Implementation**: Complete functionality with proper interfaces
2. **Testing**: Comprehensive test coverage (85%+) written immediately
3. **Quality**: Type checking, linting, and documentation validation
4. **Integration**: Verify compatibility with existing codebase
5. **Commit**: Atomic commits with working state

### Quality-First Approach

Every change must pass all quality gates:
- **Type Safety**: MyPy strict mode (zero errors)
- **Code Quality**: Ruff linting (zero violations)
- **Test Coverage**: 85%+ with comprehensive edge cases
- **Security**: Bandit scanning for vulnerabilities
- **Cross-Platform**: Compatibility across Windows/macOS/Linux

## Development Environment

### Prerequisites

- **Python 3.10+**: Required for modern type hints and syntax
- **uv**: Fast Python package installer and resolver
- **Poetry**: Dependency management and virtual environments
- **Git**: Version control with conventional commit support

### Environment Setup

```bash
# 1. Clone and setup
git clone <repository-url>
cd spec-cli

# 2. Create virtual environment
uv venv
source .venv/bin/activate  # Unix/macOS
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
poetry install

# 4. Setup development tools
poetry run dev-setup
```

The `dev-setup` command configures:
- Pre-commit hooks for automated quality checks
- Git hooks for dependency synchronization
- IDE integration settings

## Quality Assurance Commands

### Core Commands

| Command | Purpose | When to Use |
|---------|---------|-------------|
| `check-all` | Run all quality gates | Before committing, after major changes |
| `test` | Run tests with coverage | During development, debugging |
| `type-check` | MyPy type validation | After interface changes |
| `lint` | Ruff linting with auto-fix | After code changes |
| `format` | Code formatting | Before committing (auto-runs) |
| `security` | Security scanning | Before releases, after dep changes |
| `docs` | Documentation validation | After docstring changes |

### Quality Gates Detail

#### 1. Type Safety (`type-check`)
- **Tool**: MyPy in strict mode
- **Standard**: Zero errors across entire codebase
- **Coverage**: All functions, classes, and modules
- **Special handling**: Test files allow some flexibility for pytest fixtures

#### 2. Code Quality (`lint`)
- **Tool**: Ruff with comprehensive rule set
- **Standards**: PEP 8 compliance, complexity limits, security patterns
- **McCabe complexity**: ≤7 per function, ≤10 overall
- **Auto-fix**: Automatically resolves most issues

#### 3. Testing (`test`)
- **Framework**: pytest with coverage reporting
- **Requirement**: 85%+ branch coverage
- **Pattern**: Immediate test writing per vertical slice methodology
- **Scope**: Unit tests only (integration tests in separate CI)

#### 4. Security (`security`)
- **Tool**: Bandit static analysis
- **Scope**: All production code (excludes tests/)
- **Focus**: SQL injection, hardcoded secrets, unsafe practices

#### 5. Dependencies (`audit`)
- **Tool**: pip-audit vulnerability scanning
- **Frequency**: After dependency updates, before releases
- **Action**: Must resolve all high/critical vulnerabilities

### Automation Features

#### Pre-commit Hooks
Automatically run on every commit:
- **Dependency sync**: Updates pre-commit config from Poetry dependencies
- **Auto-formatting**: Ruff format with auto-staging
- **Quick validation**: Fast checks before detailed CI

#### Dependency Synchronization
- **Automatic**: Triggered when `pyproject.toml` changes
- **Mapping**: Poetry packages → pre-commit repositories
- **Type stubs**: Automatically detects and includes `types-*` packages
- **Safety**: Backs up existing configuration

## Testing Standards

### Test Structure

```
tests/
├── unit/                   # Unit tests (fast, isolated)
│   ├── cli/               # CLI command tests
│   ├── core/              # Business logic tests
│   ├── file_processing/   # File operation tests
│   └── ...
└── integration/           # Integration tests (slower, real filesystem)
```

### Test Writing Guidelines

#### Immediate Testing
- **When**: Write tests immediately after implementing each function
- **Why**: Fresh context, better coverage, prevents technical debt
- **Coverage**: Every function gets 3-5 test cases minimum

#### Test Patterns
```python
class TestFunctionName:
    def test_function_when_valid_input_then_expected_result(self):
        """Test happy path with clear naming."""

    def test_function_when_invalid_input_then_raises_specific_error(self):
        """Test error conditions with specific exceptions."""

    def test_function_when_edge_case_then_handles_gracefully(self):
        """Test boundary conditions and edge cases."""
```

#### Fixtures and Mocking
- **Fixtures**: Use pytest fixtures for common setup
- **Mocking**: Mock external dependencies (filesystem, network)
- **Cross-platform**: Use path normalization utilities

### Cross-Platform Testing

#### Path Handling
```python
# ✅ Correct - use normalization utilities
from spec_cli.file_system.path_utils import normalize_path_separators
expected = normalize_path_separators("/expected/path")
actual = normalize_path_separators(result_path)
assert actual == expected

# ❌ Wrong - hardcoded separators fail on Windows
assert result_path == "/expected/path"
```

#### Mock Patching
```python
# ✅ Correct - patch at import location
with patch("spec_cli.cli.commands.my_command.imported_function"):

# ❌ Wrong - patch at source (fails Python < 3.11)
with patch("spec_cli.original.module.imported_function"):
```

## Code Organization

### Architecture Compliance

#### Dependency Direction Rules
- **Core** modules should NOT import UI components
- **UI** modules can import from core, but not vice versa
- **CLI** is the top layer, imports from all others
- **Utils** are shared, imported by all layers

#### Import Standards
```python
# Standard library imports
import logging
from pathlib import Path

# Third-party imports
import click
from rich.console import Console

# Local imports
from ..config.settings import SpecSettings
from ..exceptions import SpecError
```

### Component Design

#### Single Responsibility
Each component has one clear purpose:
- **SpecWorkflowOrchestrator**: High-level workflow coordination
- **WorkflowExecutor**: Workflow step execution
- **WorkflowBackupManager**: Backup and rollback operations
- **BatchProgressTracker**: Progress tracking and display

#### Interface Design
```python
class ComponentName:
    """Clear docstring explaining purpose and responsibilities."""

    def __init__(self, dependencies: DependencyType):
        """Initialize with dependency injection for testability."""

    def primary_method(self, input: InputType) -> OutputType:
        """Main interface method with clear signature."""
```

## Contribution Workflow

### Branch Strategy
- **main**: Production-ready code
- **develop/***: Feature development branches
- **hotfix/***: Critical bug fixes

### Commit Standards
```bash
# Conventional commit format
git commit -m "type(scope): description"

# Examples
git commit -m "feat(cli): add --ai flag to gen command"
git commit -m "fix(core): handle edge case in path resolution"
git commit -m "refactor(utils): consolidate path utilities"
git commit -m "test(cli): add comprehensive gen command tests"
```

### Pull Request Process
1. **Branch**: Create feature branch from develop
2. **Implement**: Follow vertical slice methodology
3. **Test**: Ensure 85%+ coverage for new code
4. **Quality**: All quality gates must pass
5. **Review**: Code review focusing on architecture and testing
6. **Merge**: Squash merge with conventional commit message

## Debugging and Troubleshooting

### Debug Mode
```bash
# Enable comprehensive debugging
SPEC_DEBUG=1 spec command

# Debug with timing information
SPEC_DEBUG=1 SPEC_DEBUG_TIMING=1 spec command

# Debug specific components
SPEC_DEBUG_LEVEL=DEBUG spec command
```

### Common Issues

#### Type Checking Failures
```bash
# Run type checking on specific file
poetry run mypy spec_cli/path/to/file.py

# Common fixes:
# - Add type hints to function signatures
# - Import TYPE_CHECKING for circular imports
# - Use Optional[Type] for nullable parameters
```

#### Test Failures
```bash
# Run specific test file
poetry run pytest tests/unit/path/to/test_file.py -v

# Run with debugging
poetry run pytest tests/unit/path/to/test_file.py -v -s --pdb

# Common fixes:
# - Check mock import locations
# - Verify path normalization
# - Update fixtures for changed interfaces
```

#### Import Errors
```bash
# Check import validator
poetry run python -m spec_cli.validation.import_validator

# Common fixes:
# - Verify __init__.py files exist
# - Check circular import patterns
# - Use absolute imports from package root
```

## Performance Considerations

### Development Performance
- **Fast feedback**: `poetry run test` completes in <30 seconds
- **Incremental**: Run specific test files during development
- **Parallel**: Tests run in parallel where possible

### Code Performance
- **Path operations**: Use centralized utilities for consistency
- **File processing**: Batch operations where possible
- **Memory usage**: Limit to <500MB during normal operations

## Future Enhancements

### Planned Improvements
1. **AI Integration**: LangChain-based documentation generation
2. **Performance**: Async file processing for large codebases
3. **UI**: Enhanced progress tracking and error reporting
4. **Configuration**: More flexible template and provider systems

### Contributing Guidelines
- Follow vertical slice methodology
- Maintain test coverage standards
- Update documentation for public interfaces
- Consider cross-platform compatibility
- Ensure security best practices

## Resources

- **Project Issues**: [GitHub Issues](https://github.com/Spenquatch/spec/issues)
- **Architecture Guide**: [CLAUDE.md](../CLAUDE.md)
- **Dependency Sync**: [DEPENDENCY-SYNC-SOLUTION.md](DEPENDENCY-SYNC-SOLUTION.md)
- **Development Scripts**: [DEVELOPMENT-SCRIPTS.md](DEVELOPMENT-SCRIPTS.md)
