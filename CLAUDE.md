# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

`spec` is a CLI tool that maintains a versioned documentation layer for AI-assisted development. It creates an isolated Git repository (`.spec/`) to track contextual documentation in `.specs/` without polluting the main Git history.

## Key Architecture Decisions

1. **Directory Structure**:
   - `.spec/` = bare Git repository (like `.git`)
   - `.specs/` = working tree containing documentation
   - Documentation mirrors project structure with directories per file:
     ```
     .specs/
     └── src/
         └── models/
             ├── index.md    # Current understanding
             └── history.md  # Evolution, failed attempts, lessons learned
     ```

2. **Git Isolation**: Uses environment variables to maintain complete separation:
   ```python
   env = {
       "GIT_DIR": ".spec",
       "GIT_WORK_TREE": ".specs", 
       "GIT_INDEX_FILE": ".spec-index"
   }
   ```

3. **Path Handling**: The `run_git()` function converts paths from `.specs/file.md` to `file.md` relative to the work tree.

## Development Commands

```bash
# Install for development
pip install -e .

# Test in isolated directory
cd test_area
spec init
spec add .specs/demo.md
spec commit -m "message"

# Debug mode
SPEC_DEBUG=1 spec add .specs/file.md
```

## Current Implementation Status

### ✅ Implemented
- `spec init` - Creates `.spec/` repo and `.specs/` directory
- `spec add` - Stages files (uses `-f` flag to bypass ignore rules)
- `spec commit` - Commits changes
- `spec status`, `spec log`, `spec diff` - Basic Git operations
- Debug mode with `SPEC_DEBUG=1`

### 🚧 In Progress
- `spec gen <path>` - Generate documentation for files
  - Should create `.specs/path/to/file/index.md` and `history.md`
  - Use template system from `.spectemplate`
  - Placeholder content for now, AI integration later

### 📋 Planned
- `spec regen` - Regenerate docs preserving history
- `spec show` - Display documentation
- `spec agent-scope` - Export scoped context for AI
- Template system with `.spectemplate`
- AI integration for generating documentation content
- Git hooks and automation

## Known Issues & Solutions

1. **Git Ignore Problem** (SOLVED):
   - Issue: Git was ignoring `.specs/` files even with custom work tree
   - Solution: Added `-f` flag to force add in `run_git()` function

## Next Steps

1. Implement `cmd_gen()` function with:
   - Directory structure creation (`.specs/path/to/file/`)
   - Basic template for `index.md` and `history.md`
   - Support for single files and directories

2. Create template system:
   - Read from `.spectemplate` if exists
   - Default template with standard sections
   - Placeholder for AI integration

3. Test the complete workflow in `test_area/`

## Important Context

- The project aims to provide AI agents with versioned context about code
- Documentation should be structured for LLM consumption
- `history.md` tracks failed attempts and lessons learned
- Keep `.spec/` hidden in IDEs just like `.git/`
- Never commit to the main Git repo unless explicitly asked


## Naming Conventions (PEP 8 Compliant)

### File Naming
- **Python modules**: `snake_case.py` (e.g., `claude_code_wrapper.py`)
- **Test files**: `test_*.py` located in `tests/` directory
- **Example files**: `*_example.py` located in `examples/` directory
- **Documentation**: `lowercase-with-hyphens.md` in `docs/` directory
- **Special files**: `README.md`, `CLAUDE.md` remain uppercase (standard convention)
- **Configuration**: `snake_case.json` or `descriptive-name.json`

### Directory Structure
- **Python packages**: `tests`, `examples` (lowercase, no underscores)
- **Documentation**: `docs`
- **Temporary**: `safe_to_delete`

### Code Conventions
- **Classes**: `PascalCase` (e.g., `ClaudeCodeWrapper`, `ClaudeCodeConfig`)
- **Functions/Methods**: `snake_case` (e.g., `ask_claude()`, `get_response()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Private**: `_leading_underscore` (e.g., `_internal_method()`, `_private_var`)
- **Module-level private**: `_single_leading_underscore`
- **Name mangling**: `__double_leading_underscore` (use sparingly)

## Development Philosophy: Vertical Slices

**IMPORTANT**: We build in vertical slices - implementing features completely from implementation through testing and typing before moving on.

### Workflow for New Features:
1. Implement the function/feature
2. Write pytest unit tests immediately while the implementation context is fresh
3. Add type hints and validate with mypy
4. Run all quality checks (pytest, mypy, ruff, pre-commit)
5. Commit the completed slice
6. Move to the next slice

### Test Writing Rules:
- Write pytest unit tests in `tests/unit/` immediately after implementing a function
- When writing tests later, ALWAYS read the function implementation first
- Never make assumptions about function behavior - verify by reading the code
- Each test should cover the actual implementation, not imagined behavior
- Use pytest fixtures for common test setup
- Mock external dependencies appropriately

### Quality Assurance per Slice:
```bash
# Run unit tests with coverage (must be 80%+)
poetry run pytest tests/unit/ -v --cov=spec_cli --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/

# Run linting and formatting
poetry run ruff check --fix .
poetry run ruff format .

# Run all pre-commit hooks
poetry run pre-commit run --all-files

# If all pass, commit the slice
git add . && git commit -m "feat: implement slice X - description"
```

### Testing Guidelines:
- **Unit tests only** in `tests/` directory - no integration or automation scripts
- **Coverage requirement**: Each slice must achieve 80%+ test coverage
- For automation testing/scripts, create temporary files in project root and clean up after
- Always use pytest fixtures for test setup
- Test both happy path and error cases
- Use descriptive test names: `test_function_name_when_condition_then_expected_result`
- Cover edge cases, error conditions, and boundary values

## Best Practices for AI/ML Engineering

### Error Handling & Logging
```python
import logging
logger = logging.getLogger(__name__)

# Structured logging for AI debugging
logger.info("Generating spec", extra={
    "file_path": file_path,
    "template_used": template_name,
    "token_count": estimated_tokens
})
```

### Configuration Management
- Environment variables for sensitive data (API keys)
- Support `.specconfig.yaml` or `pyproject.toml` [tool.spec] section
- Config hierarchy: defaults → project → user → environment

### AI/LLM Integration Patterns
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_llm_api(prompt: str) -> str:
    """Retry logic for API calls"""
    pass
```

### Testing Strategy
- `tests/unit/` - Core logic tests
- `tests/integration/` - Git operation tests
- Mock LLM responses for predictable testing
- Test fixtures for different project structures

### Documentation Standards
```python
def generate_spec(file_path: Path, template: Optional[str] = None) -> str:
    """Generate spec documentation for a file.
    
    Args:
        file_path: Path to the source file
        template: Optional template name to use
        
    Returns:
        Generated markdown content
        
    Raises:
        FileNotFoundError: If source file doesn't exist
        TemplateError: If template is invalid
    """
```

### Data Validation
```python
from pydantic import BaseModel, Field

class SpecConfig(BaseModel):
    """Configuration for spec generation."""
    max_tokens: int = Field(default=4000, ge=100, le=16000)
    model: str = Field(default="gpt-4", pattern="^(gpt-4|claude)")
    temperature: float = Field(default=0.3, ge=0, le=1)
```

### Performance Considerations
- Batch operations for multiple files
- Async/concurrent processing for LLM calls
- Token counting before API calls
- Caching for repeated operations

### Security Best Practices
- Never log API keys or sensitive data
- Sanitize file paths before operations
- Validate template inputs to prevent injection
- Use `.specignore` to exclude sensitive files

### Version Compatibility
- Support Python 3.8+
- Use `__future__` imports for forward compatibility
- Pin major versions in dependencies

### CLI Best Practices
- Consider `click` for more robust CLI (current uses basic argparse)
- Provide `--dry-run` for destructive operations
- Support `--quiet` and `--verbose` modes
- Return proper exit codes (0 for success, non-zero for errors)

## Project Setup

This project uses:
- `uv` for virtual environment management
- `poetry` for dependency management
- `pyproject.toml` for all project configuration

### Development Setup
```bash
# Create virtual environment with uv
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate  # On Windows

# Install dependencies with poetry
poetry install

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=spec_cli --cov-report=html
```