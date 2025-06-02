import pytest
from spec_cli.exceptions import (
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


def test_spec_error_stores_message_and_context():
    """Test that SpecError stores message and context correctly."""
    context = {"file": "test.py", "line": 42}
    error = SpecError("Test error message", context)
    
    assert error.message == "Test error message"
    assert error.get_context() == context
    assert str(error) == "Test error message"


def test_spec_error_get_user_message_returns_message():
    """Test that get_user_message returns the message."""
    error = SpecError("Custom error message")
    assert error.get_user_message() == "Custom error message"


def test_spec_error_add_context_updates_context():
    """Test that add_context updates the error context."""
    initial_context = {"key1": "value1"}
    error = SpecError("Test error", initial_context)
    
    error.add_context("key2", "value2")
    error.add_context("key3", 123)
    
    expected_context = {"key1": "value1", "key2": "value2", "key3": 123}
    assert error.get_context() == expected_context


def test_spec_not_initialized_error_provides_helpful_message():
    """Test that SpecNotInitializedError provides helpful init instruction."""
    error = SpecNotInitializedError()
    assert error.get_user_message() == "Spec repository not initialized. Run 'spec init' to initialize."
    
    # Test with custom message
    error2 = SpecNotInitializedError("Custom not initialized message")
    assert error2.get_user_message() == "Custom not initialized message. Run 'spec init' to initialize."


def test_spec_permission_error_includes_permission_guidance():
    """Test that SpecPermissionError includes permission guidance."""
    error = SpecPermissionError("Cannot write to protected directory")
    expected = "Permission denied: Cannot write to protected directory. Check file permissions and try again."
    assert error.get_user_message() == expected


def test_spec_git_error_indicates_git_operation_failure():
    """Test that SpecGitError indicates Git operation failure."""
    error = SpecGitError("Failed to commit changes")
    assert error.get_user_message() == "Git operation failed: Failed to commit changes"


def test_spec_configuration_error_indicates_config_problem():
    """Test that SpecConfigurationError indicates configuration issue."""
    error = SpecConfigurationError("Invalid YAML format")
    assert error.get_user_message() == "Configuration error: Invalid YAML format"


def test_spec_template_error_indicates_template_problem():
    """Test that SpecTemplateError indicates template issue."""
    error = SpecTemplateError("Missing required variable")
    assert error.get_user_message() == "Template error: Missing required variable"


def test_spec_file_error_indicates_file_operation_failure():
    """Test that SpecFileError indicates file operation failure."""
    error = SpecFileError("Cannot read file")
    assert error.get_user_message() == "File operation failed: Cannot read file"


def test_spec_validation_error_indicates_validation_failure():
    """Test that SpecValidationError indicates validation failure."""
    error = SpecValidationError("Path must be absolute")
    assert error.get_user_message() == "Validation failed: Path must be absolute"


def test_exception_hierarchy_inheritance_correct():
    """Test that all custom exceptions inherit from SpecError."""
    # All custom exceptions should inherit from SpecError
    assert issubclass(SpecNotInitializedError, SpecError)
    assert issubclass(SpecPermissionError, SpecError)
    assert issubclass(SpecGitError, SpecError)
    assert issubclass(SpecConfigurationError, SpecError)
    assert issubclass(SpecTemplateError, SpecError)
    assert issubclass(SpecFileError, SpecError)
    assert issubclass(SpecValidationError, SpecError)
    
    # SpecError should inherit from Exception
    assert issubclass(SpecError, Exception)


def test_create_spec_error_creates_correct_type_with_context():
    """Test that create_spec_error creates correct exception type with context."""
    # Test with different exception types
    error1 = create_spec_error(SpecGitError, "Git failed", repo=".spec", command="git add")
    assert isinstance(error1, SpecGitError)
    assert error1.message == "Git failed"
    assert error1.get_context() == {"repo": ".spec", "command": "git add"}
    
    error2 = create_spec_error(SpecFileError, "File not found", path="/tmp/test.py", mode="r")
    assert isinstance(error2, SpecFileError)
    assert error2.message == "File not found"
    assert error2.get_context() == {"path": "/tmp/test.py", "mode": "r"}


def test_create_spec_error_rejects_invalid_error_type():
    """Test that create_spec_error rejects non-SpecError types."""
    with pytest.raises(ValueError) as exc_info:
        create_spec_error(ValueError, "Invalid type")
    
    assert "error_type must be a subclass of SpecError" in str(exc_info.value)


def test_exception_context_preserves_original_traceback():
    """Test that exception context preserves original traceback."""
    try:
        # Simulate an error with context
        context = {"operation": "test", "value": 42}
        raise SpecGitError("Test error", context)
    except SpecGitError as e:
        # Verify we can access the exception details
        assert e.message == "Test error"
        assert e.get_context() == {"operation": "test", "value": 42}
        assert e.__traceback__ is not None


def test_exceptions_work_with_exception_chaining():
    """Test that exceptions work properly with exception chaining."""
    try:
        try:
            # Original error
            raise ValueError("Original error")
        except ValueError as original:
            # Chain with our custom exception
            raise SpecConfigurationError("Config error occurred") from original
    except SpecConfigurationError as e:
        # Verify exception chaining works
        assert e.message == "Config error occurred"
        assert e.__cause__ is not None
        assert isinstance(e.__cause__, ValueError)
        assert str(e.__cause__) == "Original error"