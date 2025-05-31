# Slice 1: Custom Exception Hierarchy

## Goal

Create a comprehensive custom exception hierarchy that provides structured error handling with context information for all spec operations.

## Context

Currently, the monolithic `__main__.py` uses basic Python exceptions without structured error handling or contextual information. This slice establishes the foundation for proper error handling that all other components will use. The exception hierarchy needs to support different error types (Git, file system, configuration, template) while providing user-friendly error messages and debugging context.

## Scope

**Included in this slice:**
- Base `SpecError` exception class with context support
- Specific exception types for different operations
- Error context management and user-friendly messaging
- Exception hierarchy following single inheritance pattern

**NOT included in this slice:**
- Error handling logic (comes in later slices)
- User interface for displaying errors (PHASE-5)
- Recovery mechanisms (handled by individual components)

## Prerequisites

- Python environment with typing support
- No other modules required (this is the foundation)

## Files to Create

```
spec_cli/
└── exceptions.py           # Complete exception hierarchy
```

## Implementation Steps

### Step 1: Create spec_cli/exceptions.py

Create the file with the complete exception hierarchy:

```python
from typing import Dict, Any, Optional, List

class SpecError(Exception):
    """Base exception for all spec-related errors.
    
    Provides structured error handling with context information
    for debugging and user-friendly error messages.
    """
    
    def __init__(self, message: str, context: Optional[Dict[str, Any]] = None):
        self.message = message
        self.context = context or {}
        super().__init__(self.message)
    
    def get_user_message(self) -> str:
        """Get user-friendly error message."""
        return self.message
    
    def get_context(self) -> Dict[str, Any]:
        """Get error context for debugging."""
        return self.context
    
    def add_context(self, key: str, value: Any) -> None:
        """Add additional context to the error."""
        self.context[key] = value

class SpecNotInitializedError(SpecError):
    """Raised when spec operations are attempted in uninitialized directory."""
    
    def __init__(self, message: str = "Spec repository not initialized", context: Optional[Dict[str, Any]] = None):
        super().__init__(message, context)
    
    def get_user_message(self) -> str:
        return f"{self.message}. Run 'spec init' to initialize."

class SpecPermissionError(SpecError):
    """Raised when permission is denied for spec operations."""
    
    def get_user_message(self) -> str:
        return f"Permission denied: {self.message}. Check file permissions and try again."

class SpecGitError(SpecError):
    """Raised when Git operations fail."""
    
    def get_user_message(self) -> str:
        return f"Git operation failed: {self.message}"

class SpecConfigurationError(SpecError):
    """Raised when configuration is invalid."""
    
    def get_user_message(self) -> str:
        return f"Configuration error: {self.message}"

class SpecTemplateError(SpecError):
    """Raised when template processing fails."""
    
    def get_user_message(self) -> str:
        return f"Template error: {self.message}"

class SpecFileError(SpecError):
    """Raised when file operations fail."""
    
    def get_user_message(self) -> str:
        return f"File operation failed: {self.message}"

class SpecValidationError(SpecError):
    """Raised when validation fails."""
    
    def get_user_message(self) -> str:
        return f"Validation failed: {self.message}"

# Convenience function for creating errors with context
def create_spec_error(
    error_type: type,
    message: str,
    **context_kwargs
) -> SpecError:
    """Create a spec error with context information."""
    if not issubclass(error_type, SpecError):
        raise ValueError(f"error_type must be a subclass of SpecError, got {error_type}")
    
    return error_type(message, context=context_kwargs)
```

### Step 2: Create __init__.py updates

Update `spec_cli/__init__.py` to export the exception classes:

```python
# Add to existing exports
from .exceptions import (
    SpecError,
    SpecNotInitializedError,
    SpecPermissionError,
    SpecGitError,
    SpecConfigurationError,
    SpecTemplateError,
    SpecFileError,
    SpecValidationError,
    create_spec_error,
)
```

## Test Requirements

Create `tests/unit/test_exceptions.py` with these specific test cases:

### Test Cases (15 tests total)

1. **test_spec_error_stores_message_and_context**
   - Create SpecError with message and context
   - Verify message and context are stored correctly
   - Verify str() representation works

2. **test_spec_error_get_user_message_returns_message**
   - Create SpecError with custom message
   - Verify get_user_message() returns the message

3. **test_spec_error_add_context_updates_context**
   - Create SpecError with initial context
   - Add additional context using add_context()
   - Verify context is merged correctly

4. **test_spec_not_initialized_error_provides_helpful_message**
   - Create SpecNotInitializedError
   - Verify get_user_message() includes init instruction

5. **test_spec_permission_error_includes_permission_guidance**
   - Create SpecPermissionError
   - Verify get_user_message() includes permission guidance

6. **test_spec_git_error_indicates_git_operation_failure**
   - Create SpecGitError with specific Git error
   - Verify get_user_message() indicates Git operation failure

7. **test_spec_configuration_error_indicates_config_problem**
   - Create SpecConfigurationError
   - Verify get_user_message() indicates configuration issue

8. **test_spec_template_error_indicates_template_problem**
   - Create SpecTemplateError
   - Verify get_user_message() indicates template issue

9. **test_spec_file_error_indicates_file_operation_failure**
   - Create SpecFileError
   - Verify get_user_message() indicates file operation failure

10. **test_spec_validation_error_indicates_validation_failure**
    - Create SpecValidationError
    - Verify get_user_message() indicates validation failure

11. **test_exception_hierarchy_inheritance_correct**
    - Verify all custom exceptions inherit from SpecError
    - Verify SpecError inherits from Exception

12. **test_create_spec_error_creates_correct_type_with_context**
    - Use create_spec_error() with different exception types
    - Verify correct exception type is created with context

13. **test_create_spec_error_rejects_invalid_error_type**
    - Call create_spec_error() with non-SpecError type
    - Verify ValueError is raised

14. **test_exception_context_preserves_original_traceback**
    - Raise and catch custom exception
    - Verify original traceback information is preserved

15. **test_exceptions_work_with_exception_chaining**
    - Create exception chain using "from" syntax
    - Verify both original and new exceptions are accessible

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/test_exceptions.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/test_exceptions.py --cov=spec_cli.exceptions --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/exceptions.py

# Check code formatting
poetry run ruff check spec_cli/exceptions.py
poetry run ruff format spec_cli/exceptions.py

# Verify imports work correctly
python -c "from spec_cli.exceptions import SpecError, SpecNotInitializedError; print('Import successful')"
```

## Definition of Done

- [ ] `spec_cli/exceptions.py` created with complete exception hierarchy
- [ ] All exception classes inherit from `SpecError` base class
- [ ] Each exception type provides user-friendly error messages
- [ ] Context management system implemented and tested
- [ ] All 15 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Code formatted and linted successfully
- [ ] Imports work correctly from other modules

## Next Slice Preparation

This slice enables **slice-2-logging.md** by providing:
- `SpecError` base class for logging error scenarios
- Exception hierarchy for structured error categorization
- Context management for debugging information

The logging slice will use these exceptions to provide proper error handling during log operations.