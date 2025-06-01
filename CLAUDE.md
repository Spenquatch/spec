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

# Development Standards & Guidelines

## Project Setup

This project uses:

- `uv` for virtual environment management
- `poetry` for dependency management
- `pyproject.toml` for all project configuration

### Development Setup

```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # Unix/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies and run tests
poetry install
poetry run pytest --cov=spec_cli --cov-report=html
```

## Naming Conventions (PEP 8 Compliant)

### Files & Directories

- **Python modules**: `snake_case.py` (e.g., `claude_code_wrapper.py`)
- **Test files**: `test_*.py` in `tests/` directory
- **Examples**: `*_example.py` in `examples/` directory
- **Documentation**: `lowercase-with-hyphens.md` in `docs/`
- **Configuration**: `snake_case.json` or `descriptive-name.json`
- **Packages**: `tests`, `examples` (lowercase, no underscores)

### Code Conventions

- **Classes**: `PascalCase` (e.g., `ClaudeCodeWrapper`)
- **Functions/Methods**: `snake_case` (e.g., `ask_claude()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
- **Private**: `_leading_underscore` for internal use

## Development Philosophy: Vertical Slices

**Build features completely from implementation through testing before moving on.**

### Workflow for New Features

1. **Implement** the function/feature
2. **Test** immediately with pytest while context is fresh
3. **Type** with hints and validate with mypy
4. **Quality check** all tools (pytest, mypy, ruff, pre-commit)
5. **Commit** the completed slice
6. **Next slice**

### Quality Assurance Commands

```bash
# Must achieve 80%+ coverage per slice
poetry run pytest tests/unit/ -v --cov=spec_cli --cov-report=term-missing --cov-fail-under=80

# Type checking and linting
poetry run mypy spec_cli/
poetry run ruff check --fix .
poetry run ruff format .
poetry run pre-commit run --all-files

# Commit when all pass
git add . && git commit -m "feat: implement slice X - description"
```

## Testing Standards

### Guidelines

- **Unit tests only** in `tests/unit/` directory
- **Coverage requirement**: 80%+ per slice
- **Test immediately** after implementing each function
- **Read implementation first** when writing tests later
- **Test actual behavior**, not assumptions

### Patterns

- Use pytest fixtures for common setup
- Mock external dependencies appropriately
- Descriptive names: `test_function_name_when_condition_then_expected_result`
- Cover happy path, error cases, and boundary values

## Feature Documentation Structure

For complex features requiring multiple phases, use this standardized structure:

```
FEATURE-PLAN/
├── index.md                    # Feature overview and phase index
├── PHASE-1-foundation/         # Core infrastructure phase
│   ├── README.md              # Phase overview
│   ├── slice-1-exceptions.md   # Self-contained slice plan
│   └── slice-2-logging.md
├── PHASE-2-implementation/     # Feature-specific phase
│   ├── README.md
│   └── slice-3-core-logic.md
└── PHASE-N-integration/        # Final integration
    └── slice-N-testing.md
```

### Slice Plan Requirements (Self-Contained)

Each slice file must include:

- **Goal**: Single sentence objective
- **Context**: Brief background (2-3 sentences)
- **Scope**: Explicit boundaries (what IS/ISN'T included)
- **Prerequisites**: Required files/functions from previous slices
- **Implementation Steps**: Numbered instructions
- **Code Templates**: Full examples, not snippets
- **Test Requirements**: Specific test cases
- **Validation Steps**: Exact verification commands
- **Definition of Done**: Completion checklist

### Token Efficiency for AI Agents

- **Minimal Context**: Read only current slice file + phase README
- **Self-Contained**: All needed info in slice file
- **Progressive Disclosure**: Goal → Implementation → Validation
- **Atomic Completion**: Single session, clear pass/fail, working state

## Engineering Best Practices

### Error Handling & Logging

```python
import logging
logger = logging.getLogger(__name__)

# Structured logging for debugging
logger.info("Generating spec", extra={
    "file_path": file_path,
    "template_used": template_name,
    "token_count": estimated_tokens
})
```

### Configuration Management

- Environment variables for sensitive data (API keys)
- Support `.specconfig.yaml` or `pyproject.toml` [tool.spec] section
- Hierarchy: defaults → project → user → environment

### API Integration Patterns

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def call_llm_api(prompt: str) -> str:
    """Retry logic for API calls"""
    pass
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

### Performance & Security

- **Performance**: Batch operations, async processing, token counting, caching
- **Security**: Never log sensitive data, sanitize paths, validate inputs, use `.specignore`
- **Compatibility**: Python 3.8+, pin major versions, proper exit codes
- **CLI**: Consider `click` for robust CLI, provide `--dry-run`, `--quiet`, `--verbose`
