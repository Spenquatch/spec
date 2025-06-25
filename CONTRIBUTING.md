# Contributing to spec-cli

Thank you for your interest in contributing to spec-cli! This document provides guidelines for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Poetry for dependency management
- Git

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/spec-cli.git
cd spec-cli

# Create virtual environment and install dependencies
poetry install

# Install with AI features (recommended for full functionality)
poetry install --extras ai

# Set up development environment
poetry run dev-setup

# Verify installation
poetry run pytest

# Test spec-cli installation
poetry run spec --help
```

### Local AI Setup (Optional but Recommended)

For full AI documentation generation capabilities:

```bash
# Install AI dependencies
poetry install --extras ai

# Download AI models (first run may take a few minutes)
poetry run spec gen --help  # This will trigger model download

# Verify AI functionality
cd /tmp
mkdir test-spec && cd test-spec
poetry run spec init
echo "def hello(): pass" > test.py
poetry run spec gen test.py
```

### Project Structure

```
spec-cli/
├── spec_cli/           # Main source code
│   ├── cli/           # Command-line interface layer
│   ├── core/          # Core business logic
│   ├── file_processing/  # Batch processing and tracking
│   ├── file_system/   # Cross-platform file operations
│   ├── git/           # Git operations with isolation
│   ├── templates/     # Template system
│   ├── ui/            # Rich terminal UI
│   └── utils/         # Shared utilities
├── tests/             # Test suite (2,426 tests, 85%+ coverage)
│   ├── unit/          # Unit tests
│   └── integration/   # Integration tests
├── docs/              # Documentation
│   ├── development/   # Development guides
│   └── examples/      # Usage examples
├── scripts/           # Development scripts
├── .github/           # GitHub workflows and templates
├── pyproject.toml     # Project configuration
├── CONTRIBUTING.md    # This file
├── CODE_OF_CONDUCT.md # Community guidelines
├── SECURITY.md        # Security reporting
└── CHANGELOG.md       # Release history
```

### Key Architecture Principles

- **Layered Architecture**: Clear separation between CLI, core logic, and utilities
- **Cross-Platform**: Works consistently on Windows, macOS, and Linux
- **Type Safety**: MyPy strict mode with 100% type coverage
- **Rich UX**: Beautiful terminal interface with progress indicators
- **Modular Design**: Clean interfaces between components

## Development Workflow

### Vertical Slice Development

We follow a "vertical slice" development philosophy:

1. **Implement** the feature completely
2. **Write tests** immediately while context is fresh
3. **Add type hints** and validate with mypy
4. **Run quality checks** (pytest, mypy, ruff)
5. **Commit** the completed slice
6. **Move** to the next feature

### Quality Gates

All contributions must pass these quality gates:

```bash
# Run all quality checks
poetry run check-all

# Individual checks
poetry run pytest              # Tests with 80%+ coverage
poetry run mypy spec_cli/      # Type checking
poetry run ruff check .        # Linting
poetry run ruff format .       # Code formatting
```

## Testing

### Test Requirements

- **Coverage**: Maintain 80%+ test coverage
- **Test Types**: Unit tests only in `tests/` directory
- **Naming**: `test_function_name_when_condition_then_expected_result`
- **Fixtures**: Use pytest fixtures for common setup

### Running Tests

```bash
# Run all tests with coverage
poetry run pytest --cov=spec_cli --cov-report=term-missing

# Run specific test file
poetry run pytest tests/unit/test_example.py

# Run with verbose output
poetry run pytest -v
```

### Writing Tests

```python
def test_function_name_when_valid_input_then_returns_expected_result():
    # Arrange
    input_data = "test"

    # Act
    result = function_name(input_data)

    # Assert
    assert result == "expected"
```

## Code Style

### Python Code Standards

- **PEP 8** compliance enforced by ruff
- **Type hints** required for all functions
- **Docstrings** using Google style for public APIs
- **Import order**: standard library, third-party, local
- **Line length**: 88 characters (Black default)

### Function Complexity Limits

- Maximum function complexity: 10 (McCabe)
- Maximum function length: 50 statements
- Maximum function arguments: 5
- Maximum returns per function: 3

### Example Function

```python
def process_file(file_path: Path, options: ProcessingOptions) -> ProcessingResult:
    """Process a file with the given options.

    Args:
        file_path: Path to the file to process
        options: Processing configuration options

    Returns:
        Processing result with status and metadata

    Raises:
        FileNotFoundError: If file doesn't exist
        ProcessingError: If processing fails
    """
    # Implementation here
```

## Pull Request Process

### Before Submitting

1. **Run quality checks**: `poetry run check-all`
2. **Write tests**: Ensure 80%+ coverage for new code
3. **Update documentation**: Add/update relevant docs
4. **Test cross-platform**: Verify Windows/macOS/Linux compatibility

### PR Guidelines

- **Title**: Use conventional commits format: `feat: add semantic search`
- **Description**: Explain what and why, not just how
- **Size**: Keep PRs focused and reasonably sized
- **Tests**: Include tests for all new functionality
- **Documentation**: Update relevant documentation

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] New tests added for new functionality
- [ ] Coverage maintains 80%+

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## Reporting Issues

### Bug Reports

Use the bug report template and include:

- **Environment**: OS, Python version, spec-cli version
- **Installation method**: pip, poetry, development install
- **AI features**: Whether AI features are installed and working
- **Steps to reproduce**: Minimal reproduction case
- **Expected behavior**: What should happen
- **Actual behavior**: What actually happens
- **Logs**: Relevant error messages or debug output
- **Debug output**: Run with `SPEC_DEBUG=1` for detailed logging

### Bug Report Template

```markdown
**Environment**
- OS: [e.g., Windows 11, macOS 13, Ubuntu 22.04]
- Python version: [e.g., 3.10.5]
- spec-cli version: [e.g., 0.1.0]
- Installation: [pip/poetry/development]
- AI features: [installed/not installed/not working]

**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected behavior**
A clear description of what you expected to happen.

**Actual behavior**
What actually happened instead.

**Logs and Debug Output**
```
# Run with debug mode and paste output
SPEC_DEBUG=1 spec [your-command]
```

**Additional context**
Add any other context about the problem here.
```

### Feature Requests

Use the feature request template and include:

- **Use case**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives**: Other approaches considered
- **Implementation**: Any implementation ideas

## Development Resources

### Documentation

- [Development Workflow](docs/development/DEVELOPMENT-WORKFLOW.md)
- [Development Scripts](docs/development/DEVELOPMENT-SCRIPTS.md)
- [Dependency Management](docs/development/DEPENDENCY-SYNC-SOLUTION.md)

### Tools and Commands

```bash
# Development helpers
poetry run dev-setup           # Initialize development environment
poetry run check-all          # Run all quality gates
poetry run type-check         # MyPy type checking only
poetry run security           # Security scanning

# Testing shortcuts
poetry run test               # Run tests with coverage
poetry run test-unit          # Unit tests only
poetry run test-integration   # Integration tests only
```

## Recognition

Contributors will be recognized in:

- GitHub contributors list
- Release notes for significant contributions
- Annual contributor acknowledgments

## Questions?

- **General questions**: Open a GitHub Discussion
- **Bug reports**: Open a GitHub Issue
- **Feature requests**: Open a GitHub Issue with feature template
- **Security issues**: See [SECURITY.md](SECURITY.md)

Thank you for contributing to spec-cli!
