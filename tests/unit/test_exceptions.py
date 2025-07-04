"""Unit tests for spec_cli.exceptions module.

Tests the custom exception hierarchy and structured error handling
functionality used throughout the spec CLI application.
"""

import pytest

from spec_cli.exceptions import (
    SpecBatchProcessingError,
    SpecConfigurationError,
    SpecConflictError,
    SpecError,
    SpecFileError,
    SpecGenerationError,
    SpecGitError,
    SpecNotInitializedError,
    SpecPermissionError,
    SpecProcessingError,
    SpecRepositoryError,
    SpecTemplateError,
    SpecValidationError,
    SpecWorkflowError,
    create_spec_error,
)


class TestSpecError:
    """Test SpecError base exception class."""

    def test_init_with_message_only(self) -> None:
        """Test SpecError initialization with message only."""
        error = SpecError("Test error message")

        assert error.message == "Test error message"
        assert error.context == {}
        assert error.details is None
        assert str(error) == "Test error message"

    def test_init_with_message_and_context(self) -> None:
        """Test SpecError initialization with message and context."""
        context = {"file": "test.py", "line": 42}
        error = SpecError("Test error", context)

        assert error.message == "Test error"
        assert error.context == context
        assert error.details is None

    def test_init_with_none_context(self) -> None:
        """Test SpecError initialization with None context."""
        error = SpecError("Test error", None)

        assert error.message == "Test error"
        assert error.context == {}
        assert error.details is None

    def test_get_user_message(self) -> None:
        """Test get_user_message returns the error message."""
        error = SpecError("User-friendly message")

        assert error.get_user_message() == "User-friendly message"

    def test_get_context(self) -> None:
        """Test get_context returns the error context."""
        context = {"operation": "test", "file": "example.py"}
        error = SpecError("Test error", context)

        assert error.get_context() == context

    def test_add_context(self) -> None:
        """Test add_context adds key-value pairs to context."""
        error = SpecError("Test error")

        error.add_context("file", "test.py")
        error.add_context("line", 10)

        assert error.context["file"] == "test.py"
        assert error.context["line"] == 10

    def test_add_context_overwrites_existing(self) -> None:
        """Test add_context overwrites existing keys."""
        context = {"file": "original.py"}
        error = SpecError("Test error", context)

        error.add_context("file", "updated.py")

        assert error.context["file"] == "updated.py"

    def test_inheritance_from_exception(self) -> None:
        """Test SpecError properly inherits from Exception."""
        error = SpecError("Test error")

        assert isinstance(error, Exception)
        assert isinstance(error, SpecError)

    def test_exception_raising_and_catching(self) -> None:
        """Test SpecError can be raised and caught properly."""
        with pytest.raises(SpecError) as exc_info:
            raise SpecError("Test exception", {"context": "test"})

        assert exc_info.value.message == "Test exception"
        assert exc_info.value.context == {"context": "test"}


class TestSpecNotInitializedError:
    """Test SpecNotInitializedError exception class."""

    def test_init_with_default_message(self) -> None:
        """Test SpecNotInitializedError with default message."""
        error = SpecNotInitializedError()

        assert error.message == "Spec repository not initialized"
        assert error.context == {}

    def test_init_with_custom_message(self) -> None:
        """Test SpecNotInitializedError with custom message."""
        error = SpecNotInitializedError("Custom initialization error")

        assert error.message == "Custom initialization error"

    def test_init_with_context(self) -> None:
        """Test SpecNotInitializedError with context."""
        context = {"directory": "/test/path"}
        error = SpecNotInitializedError("Init error", context)

        assert error.message == "Init error"
        assert error.context == context

    def test_get_user_message(self) -> None:
        """Test get_user_message includes initialization instruction."""
        error = SpecNotInitializedError("Repository not found")

        user_message = error.get_user_message()

        assert "Repository not found" in user_message
        assert "Run 'spec init' to initialize" in user_message

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecNotInitializedError inherits from SpecError."""
        error = SpecNotInitializedError()

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecNotInitializedError)


class TestSpecPermissionError:
    """Test SpecPermissionError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes permission guidance."""
        error = SpecPermissionError("Access denied to file")

        user_message = error.get_user_message()

        assert "Permission denied: Access denied to file" in user_message
        assert "Check file permissions and try again" in user_message

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecPermissionError inherits from SpecError."""
        error = SpecPermissionError("Permission error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecPermissionError)


class TestSpecGitError:
    """Test SpecGitError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes git context."""
        error = SpecGitError("Failed to commit changes")

        user_message = error.get_user_message()

        assert user_message == "Git operation failed: Failed to commit changes"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecGitError inherits from SpecError."""
        error = SpecGitError("Git error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecGitError)


class TestSpecConfigurationError:
    """Test SpecConfigurationError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes configuration context."""
        error = SpecConfigurationError("Invalid config value")

        user_message = error.get_user_message()

        assert user_message == "Configuration error: Invalid config value"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecConfigurationError inherits from SpecError."""
        error = SpecConfigurationError("Config error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecConfigurationError)


class TestSpecTemplateError:
    """Test SpecTemplateError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes template context."""
        error = SpecTemplateError("Template variable not found")

        user_message = error.get_user_message()

        assert user_message == "Template error: Template variable not found"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecTemplateError inherits from SpecError."""
        error = SpecTemplateError("Template error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecTemplateError)


class TestSpecFileError:
    """Test SpecFileError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes file operation context."""
        error = SpecFileError("Cannot read file")

        user_message = error.get_user_message()

        assert user_message == "File operation failed: Cannot read file"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecFileError inherits from SpecError."""
        error = SpecFileError("File error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecFileError)


class TestSpecRepositoryError:
    """Test SpecRepositoryError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes repository context."""
        error = SpecRepositoryError("Repository is corrupted")

        user_message = error.get_user_message()

        assert user_message == "Repository operation failed: Repository is corrupted"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecRepositoryError inherits from SpecError."""
        error = SpecRepositoryError("Repository error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecRepositoryError)


class TestSpecWorkflowError:
    """Test SpecWorkflowError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes workflow context."""
        error = SpecWorkflowError("Workflow step failed")

        user_message = error.get_user_message()

        assert user_message == "Workflow operation failed: Workflow step failed"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecWorkflowError inherits from SpecError."""
        error = SpecWorkflowError("Workflow error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecWorkflowError)


class TestSpecValidationError:
    """Test SpecValidationError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes validation context."""
        error = SpecValidationError("Input validation failed")

        user_message = error.get_user_message()

        assert user_message == "Validation failed: Input validation failed"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecValidationError inherits from SpecError."""
        error = SpecValidationError("Validation error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecValidationError)


class TestSpecConflictError:
    """Test SpecConflictError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes conflict context."""
        error = SpecConflictError("File conflict detected")

        user_message = error.get_user_message()

        assert user_message == "Conflict resolution failed: File conflict detected"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecConflictError inherits from SpecError."""
        error = SpecConflictError("Conflict error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecConflictError)


class TestSpecProcessingError:
    """Test SpecProcessingError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes processing context."""
        error = SpecProcessingError("File processing failed")

        user_message = error.get_user_message()

        assert user_message == "Processing failed: File processing failed"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecProcessingError inherits from SpecError."""
        error = SpecProcessingError("Processing error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecProcessingError)


class TestSpecBatchProcessingError:
    """Test SpecBatchProcessingError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes batch processing context."""
        error = SpecBatchProcessingError("Batch operation failed")

        user_message = error.get_user_message()

        assert user_message == "Batch processing failed: Batch operation failed"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecBatchProcessingError inherits from SpecError."""
        error = SpecBatchProcessingError("Batch error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecBatchProcessingError)


class TestSpecGenerationError:
    """Test SpecGenerationError exception class."""

    def test_get_user_message(self) -> None:
        """Test get_user_message includes generation context."""
        error = SpecGenerationError("Documentation generation failed")

        user_message = error.get_user_message()

        assert user_message == "Generation failed: Documentation generation failed"

    def test_inheritance_from_spec_error(self) -> None:
        """Test SpecGenerationError inherits from SpecError."""
        error = SpecGenerationError("Generation error")

        assert isinstance(error, SpecError)
        assert isinstance(error, SpecGenerationError)


class TestCreateSpecError:
    """Test create_spec_error convenience function."""

    def test_create_spec_error_basic(self) -> None:
        """Test create_spec_error with basic parameters."""
        error = create_spec_error(SpecValidationError, "Validation failed")

        assert isinstance(error, SpecValidationError)
        assert error.message == "Validation failed"
        assert error.context == {}

    def test_create_spec_error_with_context(self) -> None:
        """Test create_spec_error with context parameters."""
        error = create_spec_error(
            SpecFileError,
            "File not found",
            file_path="/test/file.txt",
            operation="read",
        )

        assert isinstance(error, SpecFileError)
        assert error.message == "File not found"
        assert error.context == {"file_path": "/test/file.txt", "operation": "read"}

    def test_create_spec_error_with_multiple_context_args(self) -> None:
        """Test create_spec_error with multiple context arguments."""
        error = create_spec_error(
            SpecGitError,
            "Commit failed",
            command="git commit",
            exit_code=1,
            repository="/path/to/repo",
        )

        assert isinstance(error, SpecGitError)
        assert error.message == "Commit failed"
        assert error.context["command"] == "git commit"
        assert error.context["exit_code"] == 1
        assert error.context["repository"] == "/path/to/repo"

    def test_create_spec_error_invalid_error_type(self) -> None:
        """Test create_spec_error raises ValueError for invalid error type."""
        with pytest.raises(ValueError) as exc_info:
            create_spec_error(ValueError, "Invalid error type")

        assert "error_type must be a subclass of SpecError" in str(exc_info.value)
        assert "ValueError" in str(exc_info.value)

    def test_create_spec_error_with_non_exception_type(self) -> None:
        """Test create_spec_error raises ValueError for non-exception type."""
        with pytest.raises(ValueError) as exc_info:
            create_spec_error(str, "Not an exception type")

        assert "error_type must be a subclass of SpecError" in str(exc_info.value)

    def test_create_spec_error_empty_context(self) -> None:
        """Test create_spec_error with no context kwargs."""
        error = create_spec_error(SpecError, "Base error")

        assert isinstance(error, SpecError)
        assert error.message == "Base error"
        assert error.context == {}


class TestExceptionIntegration:
    """Test exception integration and edge cases."""

    def test_exception_chaining(self) -> None:
        """Test exception chaining works properly."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as original:
                raise SpecError("Wrapped error") from original
        except SpecError as wrapped:
            assert wrapped.message == "Wrapped error"
            assert isinstance(wrapped.__cause__, ValueError)
            assert str(wrapped.__cause__) == "Original error"

    def test_context_modification_after_creation(self) -> None:
        """Test context can be modified after exception creation."""
        error = SpecError("Test error", {"initial": "value"})

        # Modify context after creation
        error.add_context("added", "new_value")
        error.context["direct"] = "direct_value"

        assert error.context["initial"] == "value"
        assert error.context["added"] == "new_value"
        assert error.context["direct"] == "direct_value"

    def test_details_attribute_modification(self) -> None:
        """Test details attribute can be set and retrieved."""
        error = SpecError("Test error")

        assert error.details is None

        error.details = "Additional error details"
        assert error.details == "Additional error details"

    def test_complex_context_types(self) -> None:
        """Test context can handle complex data types."""
        complex_context = {
            "string": "text",
            "number": 42,
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None,
            "bool": True,
        }

        error = SpecError("Test error", complex_context)

        assert error.context == complex_context
        assert error.get_context() == complex_context

    def test_all_exception_types_inherit_properly(self) -> None:
        """Test all exception types properly inherit from SpecError."""
        exception_classes = [
            SpecNotInitializedError,
            SpecPermissionError,
            SpecGitError,
            SpecConfigurationError,
            SpecTemplateError,
            SpecFileError,
            SpecRepositoryError,
            SpecWorkflowError,
            SpecValidationError,
            SpecConflictError,
            SpecProcessingError,
            SpecBatchProcessingError,
            SpecGenerationError,
        ]

        for exception_class in exception_classes:
            error = exception_class("Test message")
            assert isinstance(error, SpecError)
            assert isinstance(error, Exception)
            assert hasattr(error, "get_user_message")
            assert callable(error.get_user_message)

    def test_user_message_formats_consistently(self) -> None:
        """Test all exception types format user messages consistently."""
        test_cases = [
            (SpecNotInitializedError("Not init"), "Run 'spec init' to initialize"),
            (SpecPermissionError("No access"), "Permission denied: No access"),
            (SpecGitError("Git failed"), "Git operation failed: Git failed"),
            (SpecConfigurationError("Bad config"), "Configuration error: Bad config"),
            (SpecTemplateError("Template issue"), "Template error: Template issue"),
            (SpecFileError("File problem"), "File operation failed: File problem"),
            (
                SpecRepositoryError("Repo issue"),
                "Repository operation failed: Repo issue",
            ),
            (
                SpecWorkflowError("Workflow problem"),
                "Workflow operation failed: Workflow problem",
            ),
            (SpecValidationError("Invalid input"), "Validation failed: Invalid input"),
            (
                SpecConflictError("Conflict found"),
                "Conflict resolution failed: Conflict found",
            ),
            (
                SpecProcessingError("Process failed"),
                "Processing failed: Process failed",
            ),
            (
                SpecBatchProcessingError("Batch failed"),
                "Batch processing failed: Batch failed",
            ),
            (SpecGenerationError("Gen failed"), "Generation failed: Gen failed"),
        ]

        for error, expected_content in test_cases:
            user_message = error.get_user_message()
            assert expected_content in user_message
            assert isinstance(user_message, str)
            assert len(user_message) > 0
