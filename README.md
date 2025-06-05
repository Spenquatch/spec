# spec

[![CI](https://github.com/Spenquatch/spec/actions/workflows/ci.yml/badge.svg)](https://github.com/Spenquatch/spec/actions/workflows/ci.yml)[![Release](https://github.com/Spenquatch/spec/actions/workflows/release.yml/badge.svg)](https://github.com/Spenquatch/spec/actions/workflows/release.yml)[![codecov](https://codecov.io/gh/Spenquatch/spec/graph/badge.svg)](https://codecov.io/gh/Spenquatch/spec)
[![PyPI version](https://badge.fury.io/py/spec-ai.svg)](https://badge.fury.io/py/spec-ai)[![Python Support](https://img.shields.io/pypi/pyversions/spec-ai.svg)](https://pypi.org/project/spec-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](https://mypy-lang.org/)

A versioned documentation layer for AI-assisted development. `spec` maintains a separate Git repository of contextual documentation that helps AI agents understand your codebase without polluting your main Git history.

## Why spec?

- **AI-Optimized Context**: Structured documentation designed for LLM consumption
- **Version-Controlled Memory**: AI agents can learn from past attempts and decisions
- **Isolated Git History**: Documentation changes don't clutter your main repository
- **Scoped Context Windows**: Load only relevant documentation to fit within token limits
- **Rich Terminal UI**: Beautiful, colorful interface with progress indicators
- **Modular Architecture**: Clean, testable codebase built for extensibility

## Installation

```bash
pip install spec-cli
```

## Quick Start

```bash
# Initialize spec in your project
spec init

# Generate documentation for files
spec gen src/models.py        # Single file
spec gen src/                 # Directory
spec gen .                    # Current directory (all files)

# Track documentation changes
spec add .
spec commit -m "Document authentication flow"

# View documentation status
spec status
spec log
spec diff
```

## Features

### ✅ Core Features
- **Project Initialization**: `spec init` creates isolated Git repository structure
- **Documentation Generation**: `spec gen` creates structured documentation with templates
- **Version Control**: Full Git workflow (`add`, `commit`, `status`, `log`, `diff`)
- **Template System**: Customizable documentation templates via `.spectemplate`
- **File Filtering**: Smart filtering with `.specignore` patterns
- **Rich Terminal UI**: Beautiful interface with colors, progress bars, and styling
- **Batch Processing**: Generate documentation for entire directories
- **File Type Detection**: Support for 20+ programming languages and file types
- **Conflict Resolution**: Interactive handling of existing documentation
- **Debug Mode**: Comprehensive debugging with `SPEC_DEBUG=1`
- **Modular Architecture**: Clean, maintainable codebase with 80%+ test coverage

### 🔮 Future Features
- **AI Documentation Generation**: Replace placeholder content with AI-generated documentation
- **Git Hook Integration**: Auto-generate documentation on code changes
- **Enhanced CLI**: Advanced options and configuration management

## How It Works

`spec` creates two directories:
- `.spec/` - A bare Git repository (like `.git`)
- `.specs/` - Working tree containing documentation

Your documentation mirrors your project structure:

```
project/
├── .spec/              # Bare Git repo for versioning
├── .specs/             # Documentation working tree
│   ├── src/
│   │   └── models/
│   │       ├── index.md
│   │       └── history.md
│   └── api/
│       └── users/
│           ├── index.md
│           └── history.md
├── .spectemplate       # Customizable templates
├── .specignore         # Ignore patterns
├── src/
│   └── models.py
└── api/
    └── users.py
```

Each source file gets a documentation directory with:
- `index.md`: Current understanding and specifications
- `history.md`: Evolution, decisions, and lessons learned


## Commands

### Core Commands
- `spec init` - Initialize spec in current directory
- `spec gen <path>` - Generate documentation for file(s) or directory
- `spec add <path>` - Stage documentation changes
- `spec commit -m "message"` - Commit documentation changes

### View Documentation
- `spec status` - Show documentation status
- `spec log [path]` - Show documentation history
- `spec diff [path]` - Show uncommitted changes
- `spec show <path>` - Display documentation for a file (coming soon)

### Future Commands
- `spec regen <path>` - Regenerate documentation (preserves history)
- `spec agent-scope [options]` - Export scoped context for AI agents

## Advanced Usage

### Custom Templates

Create a `.spectemplate` file to customize documentation format:

```yaml
index:
  template: |
    # {{filename}}

    **Location**: {{filepath}}
    **Purpose**: {{purpose}}
    **Responsibilities**: {{responsibilities}}
    **Requirements**: {{requirements}}
    **Example Usage**: {{example_usage}}
    **Notes**: {{notes}}

history:
  template: |
    ## {{date}} - Initial Creation

    **Purpose**: Created initial specification for {{filename}}
    **Context**: {{context}}
    **Decisions**: {{decisions}}
    **Lessons Learned**: {{lessons}}
```

### Environment Variables

Control spec behavior with environment variables:

- `SPEC_DEBUG=1` - Enable debug output for troubleshooting
- `SPEC_DEBUG_LEVEL=INFO|DEBUG|WARNING|ERROR` - Set debug level
- `SPEC_DEBUG_TIMING=1` - Enable operation timing

### File Filtering

Use `.specignore` to exclude files from documentation generation:

```
# Ignore patterns
*.log
node_modules/
build/
*.min.js
```

## Architecture

`spec` follows a clean, modular architecture built through a comprehensive refactoring:

### Directory Structure
```
spec_cli/
├── cli/                     # Command-line interface layer
├── core/                    # Core business logic and workflow orchestration
├── git/                     # Git operations abstraction
├── templates/               # Template system for documentation generation
├── file_system/             # File system operations and path handling
├── config/                  # Configuration management
├── ui/                      # Rich terminal UI components
├── file_processing/         # Batch processing and conflict resolution
├── exceptions.py            # Custom exception hierarchy
└── logging/                 # Debug logging and timing
```

### Key Design Principles
- **Single Responsibility**: Each module has a clear, focused purpose
- **Dependency Injection**: Services are easily testable and mockable
- **Clean Interfaces**: Well-defined boundaries between layers
- **Rich Terminal UI**: Beautiful, colorful interface throughout
- **Comprehensive Testing**: 80%+ test coverage across all modules

## Development Setup

This project uses Poetry for dependency management and uv for virtual environments:

```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Complete environment setup
poetry run dev-setup

# Run all quality checks
poetry run check-all

# Individual gates (if debugging):
poetry run type-check         # 0 errors, 0 suppressions
poetry run lint              # Auto-fix style issues
poetry run format            # Code formatting
poetry run docs              # Docstring validation
poetry run security          # Security scan
poetry run audit             # Vulnerability scan
poetry run test              # Test with coverage
poetry run platform-check    # Cross-platform validation
```

### Quality Assurance Commands

All commands follow standardized naming and provide consistent behavior:

| Command | Purpose | Exit Code |
|---------|---------|-----------|
| `poetry run dev-setup` | Complete environment initialization | 0 on success |
| `poetry run type-check` | MyPy strict type checking (0 errors required) | 1 on any errors |
| `poetry run lint` | Ruff linting with auto-fix | 1 on unfixable issues |
| `poetry run format` | Ruff code formatting | 1 on formatting errors |
| `poetry run format-check` | Verify formatting without changes | 1 if reformatting needed |
| `poetry run docs` | Pydocstyle documentation validation | 1 on missing/bad docstrings |
| `poetry run security` | Bandit security scan | 1 on security issues |
| `poetry run audit` | Pip-audit vulnerability scan | 1 on vulnerabilities |
| `poetry run test` | Pytest with 90%+ coverage requirement | 1 on test failures |
| `poetry run platform-check` | Cross-platform compatibility check | 1 on platform issues |
| `poetry run check-all` | ALL quality gates (pipeline simulation) | 1 if any gate fails |
| `poetry run update-deps` | Show outdated dependencies + guidance | 0 (informational only) |

### Continuous Integration Pipeline

The `check-all` command simulates the complete CI pipeline:

1. **Type Safety**: MyPy strict type checking with zero tolerance
2. **Code Quality**: Ruff linting with auto-fix capability
3. **Formatting**: Consistent code style enforcement
4. **Documentation**: Comprehensive docstring validation
5. **Security**: Static security analysis with Bandit
6. **Dependencies**: Vulnerability scanning with pip-audit
7. **Testing**: Unit tests with 90%+ coverage requirement
8. **Compatibility**: Cross-platform validation

## Use Cases

### For AI Development
- Provide rich context to AI coding assistants
- Track why certain approaches failed
- Maintain institutional knowledge across AI sessions
- Export scoped documentation for specific tasks

### For Teams
- Onboard new developers with comprehensive docs
- Document architectural decisions and trade-offs
- Track technical debt and future improvements
- Maintain living documentation that evolves with code

### For Code Review
- Understand the "why" behind implementations
- Review documentation changes alongside code
- Ensure specs stay synchronized with reality
- Track decision history and lessons learned

## IDE Integration

Hide `.spec/` and `.specs/` directories in your IDE. For VSCode, add to workspace settings:

```json
{
  "files.exclude": {
    ".spec": true,
    ".specs": true
  }
}
```

## Install Testing Branch From Test PyPI

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ --pre spec-ai
```

## Cross-Platform Compatibility

`spec` is designed to work consistently across all platforms (Windows, macOS, Linux). We handle cross-platform differences systematically:

### Path Handling
- **Problem**: Windows uses backslashes (`\`) while Unix systems use forward slashes (`/`)
- **Solution**: We use dedicated path utilities in `spec_cli.file_system.path_utils`:
  - `normalize_path_separators()` - Converts all paths to forward slashes
  - `convert_to_posix_style()` - Alias for consistent POSIX-style paths
  - All `.specs/` path operations use normalized separators

### Testing Compatibility
- **Problem**: Mock behavior and path assertions differ between Python versions
- **Solution**:
  - Tests use cross-platform path normalization for assertions
  - Mock patches target the import location (`module.imported_function`) not source
  - CI tests on Python 3.8-3.12 across Windows, macOS, and Linux

### Mock Patching Guidelines
When writing tests, always patch imported functions at their import location:
```python
# ✅ Correct - patch where function is imported
with patch("spec_cli.cli.commands.my_command.imported_function"):

# ❌ Wrong - patch at source (fails on Python < 3.11)
with patch("spec_cli.original.module.imported_function"):
```

### Path Testing Guidelines
Use path utilities for cross-platform test assertions:
```python
# ✅ Correct - normalize paths for comparison
from spec_cli.file_system.path_utils import normalize_path_separators
expected = normalize_path_separators("/expected/path")
actual = normalize_path_separators(result_path)
assert actual == expected

# ❌ Wrong - hardcoded path separators
assert result_path == "/expected/path"  # Fails on Windows
```

## Contributing

We follow a vertical slice development philosophy - implementing features completely through implementation, testing, and typing before moving on. See [CLAUDE.md](CLAUDE.md) for detailed development guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.
