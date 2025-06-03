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

**IMPORTANT**: We build in vertical slices - implementing features completely from implementation through testing and typing before moving on.

### Workflow for New Features:
1. **Implement** the function/feature with complete specification
2. **Write pytest unit tests immediately** while the implementation context is fresh
3. **Add type hints and validate** with mypy
4. **Run all quality checks** (pytest, mypy, ruff, pre-commit)
5. **Commit the completed slice**
6. **Move to the next slice**

### Detailed Implementation Standards

**Each slice must include:**
- **Exact function signatures** with parameters, types, and return values
- **Complete error handling** with specific exception types and context
- **Comprehensive logging** with structured debug information
- **Thread safety** where applicable (use threading.Lock appropriately)
- **Performance considerations** (caching, batch operations, async when needed)
- **Security validation** (input sanitization, path validation, no secret logging)

### Function Design Requirements

**Every function must have:**
- **Purpose statement**: Single sentence describing what it does
- **Parameter validation**: Type checking and range validation where applicable
- **Error context**: Structured error messages with relevant context data
- **Return value documentation**: Clear description of what is returned
- **Example usage**: Demonstrating proper usage patterns

**Example of proper function specification:**
```python
def process_template_variables(
    template_path: Path,
    source_file: Path,
    custom_vars: Dict[str, Any],
    include_system_vars: bool = True
) -> Dict[str, Any]:
    """Generate complete variable set for template substitution.

    Args:
        template_path: Path to template file (must exist)
        source_file: Path to source file being documented
        custom_vars: User-provided variables (validated)
        include_system_vars: Whether to include built-in system variables

    Returns:
        Dictionary with all variables merged according to precedence rules

    Raises:
        TemplateError: If template_path doesn't exist or is invalid
        ValidationError: If custom_vars contains invalid types

    Example:
        vars = process_template_variables(
            Path(".spectemplate"),
            Path("src/main.py"),
            {"purpose": "Main module"},
            include_system_vars=True
        )
    """
```

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

### Testing Philosophy

**Write tests immediately after implementing each function while the implementation context is fresh.**

### Comprehensive Testing Requirements

- **Unit tests only** in `tests/unit/` directory - no integration or automation scripts
- **Coverage requirement**: Each slice must achieve 80%+ test coverage
- **Test immediately** after implementing each function
- **Read implementation first** when writing tests later
- **Test actual behavior**, not assumptions about how code should work

### Test Structure Requirements

**Every test class must include:**
- **Test naming convention**: `test_function_name_when_condition_then_expected_result`
- **Fixtures for common setup**: Use pytest fixtures to avoid duplication
- **Mock external dependencies**: Never depend on external services or file system
- **Test all paths**: Happy path, error cases, edge cases, and boundary values
- **Specific assertions**: Test exact return values, exception types, and side effects

### Required Test Categories per Function

**1. Happy Path Tests**
```python
def test_process_variables_when_valid_inputs_then_returns_merged_variables(self)
def test_validate_template_when_valid_template_then_returns_success_result(self)
```

**2. Error Condition Tests**
```python
def test_process_variables_when_template_missing_then_raises_template_error(self)
def test_validate_template_when_invalid_format_then_returns_error_result(self)
```

**3. Edge Case Tests**
```python
def test_process_variables_when_empty_custom_vars_then_uses_defaults_only(self)
def test_validate_template_when_minimal_template_then_validates_successfully(self)
```

**4. Type Safety Tests**
```python
def test_process_variables_when_invalid_type_then_raises_type_error(self)
def test_validate_template_when_wrong_parameter_type_then_raises_type_error(self)
```

### Test Implementation Standards

**Required Mocks and Fixtures:**
```python
@pytest.fixture
def mock_debug_logger():
    """Mock debug logger to capture logging calls."""
    return Mock(spec=['log'])

@pytest.fixture
def sample_template_path(tmp_path):
    """Create sample template file for testing."""
    template_file = tmp_path / ".spectemplate"
    template_file.write_text("# Template\n{{filename}}: {{purpose}}")
    return template_file

@pytest.fixture
def mock_file_metadata():
    """Mock file metadata extractor."""
    return Mock(spec=FileMetadataExtractor)
```

**Error Testing Requirements:**
- Test every exception path with specific exception types
- Verify error messages contain relevant context
- Test error handling doesn't leak sensitive information
- Ensure errors include debugging context for troubleshooting


## Code Complexity Limits (Enforced by Ruff)

* Maximum line length: 88 (Black default)
* Maximum function complexity: 10 (McCabe)
* Maximum file length: 500 lines
* Maximum function length: 50 statements
* Maximum function arguments: 5
* Maximum returns per function: 3
* Maximum branches: 12

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

Each slice file must include complete specifications with industry-standard detail:

- **Goal**: Single sentence objective with measurable outcome
- **Context**: Brief background explaining why this slice is needed
- **Scope**: Explicit boundaries (what IS/ISN'T included) with technical justification
- **Prerequisites**: Required files/functions from previous slices with version dependencies
- **Implementation Steps**: Numbered instructions with exact commands and expected outputs
- **Code Templates**: Complete, working examples following all complexity limits
- **Function Specifications**: Exact signatures with parameters, types, returns, and error handling
- **Good/Bad Examples**: Industry best practices vs anti-patterns with explanations
- **Test Requirements**: Specific test classes, functions, fixtures, and mocks
- **Validation Steps**: Exact verification commands with expected success criteria
- **Quality Gates**: Coverage requirements, type checking, linting standards
- **Definition of Done**: Detailed completion checklist with verification steps

### Implementation Specification Standards

**Every slice must define:**

**1. Exact Function Signatures**
```python
def function_name(
    param1: Type1,
    param2: Optional[Type2] = None,
    param3: Type3 = default_value
) -> ReturnType:
    """Detailed docstring with Args, Returns, Raises, Example."""
```

**2. Complete Error Handling**
```python
try:
    result = risky_operation()
except SpecificError as e:
    context = {"operation": "description", "param": value}
    debug_logger.log("ERROR", f"Operation failed: {e}", **context)
    raise WellDefinedError(f"Failed to perform operation: {e}", context) from e
```

**3. Comprehensive Test Specifications**
```python
class TestFunctionName:
    def test_function_when_valid_inputs_then_returns_expected_result(self)
    def test_function_when_invalid_input_then_raises_specific_error(self)
    def test_function_when_edge_case_then_handles_gracefully(self)

    @pytest.fixture
    def required_fixture(self):
        return MockObject(spec=['method1', 'method2'])
```

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

## Systematic Refactoring Process

When eliminating duplicate code and improving architecture, follow this systematic approach to ensure quality and maintainability:

### Step 1: Identify Target Module
- Select module with highest code duplication
- Focus on utility functions and common patterns
- Avoid complex workflow methods initially

**Commands:**
```bash
# Find modules with duplicate patterns
grep -r "def.*format.*size" spec_cli/ | wc -l
grep -r "try:" spec_cli/ | head -10
rg "class.*Error" spec_cli/ --type py
```

### Step 2: Analyze Code Implementation
- Read the target files to understand duplication
- Identify simple utility functions and common patterns
- Focus on methods with clear inputs/outputs and minimal dependencies

**Commands:**
```bash
# Find function definitions
grep -n "def " "/path/to/target/file.py"
# Use Read tool to examine actual implementation
```

### Step 3: Create Centralized Utilities
- Extract common logic into utilities module (e.g., `spec_cli/utils/`)
- Create 1-2 focused utility functions per slice
- Use descriptive names: `format_file_size()`, `safe_relative_to()`
- Ensure utilities have clear interfaces and error handling

### Step 4: Test Utilities in Isolation
- Run only the new utility tests to ensure they work independently
- This catches import issues, logic errors, and interface problems early

**Command:**
```bash
poetry run pytest tests/unit/utils/test_new_utility.py -v
```

### Step 5: Update Existing Code
- Replace duplicate code with utility calls
- Update 2-3 modules per slice (not all at once)
- Maintain backward compatibility
- Common fixes:
  - Replace inline implementations with utility imports
  - Adjust error handling to match utility patterns

### Step 6: Validate Module Integration
- Run tests for the specific modules you updated
- Ensure all existing functionality works with new utilities

**Command:**
```bash
poetry run pytest tests/unit/path/to/updated_modules/ -v
```

### Step 7: Run Full Test Suite
- Execute complete test suite to verify no regressions
- Verify that utilities integrate properly with existing infrastructure

**Command:**
```bash
poetry run pytest tests/unit/ -v
```

### Step 8: Quality Validation
- Run all quality checks to ensure code meets standards
- This includes: ruff linting, ruff formatting, mypy type checking, and pre-commit hooks

**Command:**
```bash
poetry run pre-commit run --all-files
```

### Step 9: Coverage and Architecture Verification
- Check that utilities have good test coverage
- Verify overall project coverage is maintained
- Run type checking to ensure clean interfaces

**Commands:**
```bash
# Check specific utility coverage
poetry run pytest --cov=spec_cli.utils tests/unit/utils/ -v --cov-report=term-missing

# Check overall project coverage
poetry run pytest tests/unit/ --cov=spec_cli --cov-report=term-missing --cov-fail-under=80

# Type checking
poetry run mypy spec_cli/
```

### Key Success Principles for Refactoring

1. **Focus on High-Impact Utilities**: Target duplicate code that appears 3+ times across modules
2. **Incremental Progress**: Update 3-5 files per slice, not entire codebase at once
3. **Utility Isolation**: Always test new utilities independently before integration
4. **Quality First**: Never compromise code quality for deduplication speed
5. **Systematic Approach**: Complete all 9 steps for each refactoring slice before moving on
6. **One Task In Progress**: Mark only one todo as in_progress at a time
7. **Immediate Completion**: Mark todos as completed as soon as each step finishes
8. **Rollback Ready**: Each slice should be independently revertible if issues arise

### Implementation Excellence Standards

**Thread Safety Requirements:**
- Use `threading.Lock()` for shared mutable state
- Implement proper double-checked locking patterns
- Document thread safety guarantees in docstrings
- Test concurrent access scenarios

**Performance Optimization:**
- Implement caching with TTL and size limits
- Use batch operations for multiple items
- Add performance metrics and monitoring
- Profile critical paths and optimize bottlenecks

**Security Best Practices:**
- Validate all inputs with type checking and range validation
- Sanitize file paths to prevent directory traversal
- Never log sensitive information (API keys, tokens, passwords)
- Use secure defaults and fail closed on security errors

**Error Handling Excellence:**
- Create structured error context with relevant debugging information
- Use specific exception types, not generic Exception
- Log errors with structured data for debugging
- Provide clear error messages for end users
- Include recovery suggestions where applicable

**Type Safety and Validation:**
- Use `typing` module for all function signatures
- Validate inputs at function boundaries
- Use `dataclasses` for structured data
- Implement runtime type checking for critical paths
- Use `Optional[T]` explicitly for nullable parameters

### Architecture Compliance

**Dependency Direction Rules:**
- Core modules should NOT import UI components
- Logging modules should have NO dependencies
- Configuration should only depend on exceptions and logging
- CLI should be the only layer importing from all others

**Import Standards:**
- Use absolute imports: `from spec_cli.core import module`
- No star imports: avoid `from module import *`
- Group imports: standard library, third-party, local
- Use `TYPE_CHECKING` for type-only imports

### Common Refactoring Patterns

**Error Handling Consolidation:**
```python
# Before: Duplicate try/catch in multiple files
try:
    operation()
except OSError as e:
    error_msg = f"Failed to {operation_name}: {e}"
    debug_logger.log("ERROR", error_msg)
    raise SpecError(error_msg) from e

# After: Centralized error handler
from ..utils.error_handling import handle_os_error

@handle_os_error("operation_name")
def operation():
    # actual logic
```

**Path Operation Consolidation:**
```python
# Before: Repeated relative_to patterns
try:
    relative_path = absolute_path.relative_to(root_path)
except ValueError:
    raise SpecValidationError(f"Path outside root: {absolute_path}")

# After: Centralized utility
from ..utils.path_operations import safe_relative_to

relative_path = safe_relative_to(absolute_path, root_path)
```

**Validation Pattern Consolidation:**
```python
# Before: Similar validation in multiple validators
def validate_string(value, field_name):
    if not isinstance(value, str):
        return f"{field_name} must be a string"
    if not value.strip():
        return f"{field_name} cannot be empty"

# After: Base validator class
from ..utils.validation import BaseValidator

class MyValidator(BaseValidator):
    def validate_config(self, config):
        self.validate_required_string(config.get("name"), "name")
```
