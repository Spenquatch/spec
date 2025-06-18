"""Tests for AI provider base classes and data structures."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.providers.base import (
    AIProvider,
    GenerationRequest,
    GenerationResult,
)
from spec_cli.utils.path_utils import normalize_path_separators

# Test constants
DEFAULT_SOURCE_FILE = Path("src/models/user.py")
DEFAULT_CONTENT = "class User:\n    def __init__(self):\n        pass"
DEFAULT_CONTEXT = {"project": "test", "language": "python"}
DEFAULT_DOC_TYPE = "comprehensive"
DEFAULT_TEMPLATE = "# Template\n{{content}}"

SAMPLE_CONTENT_DICT = {
    "index.md": "# User Model\nThis is the main documentation.",
    "history.md": "# History\nInitial implementation.",
}
SAMPLE_METADATA = {"tokens_used": 150, "model": "test-model"}
DEFAULT_PROCESSING_TIME = 500

TEST_EXTENSION = ".py"
CONTENT_SIZE = len(DEFAULT_CONTENT)
NORMALIZED_PATH = "src/models/user.py"

ERROR_MESSAGE = "Test error occurred"
VALIDATION_ERROR = "Validation failed"


class TestGenerationRequestValidation:
    """Test GenerationRequest validation in __post_init__."""

    def test_generation_request_when_valid_data_then_creates_successfully(self):
        """Test that valid data creates GenerationRequest successfully."""
        request = GenerationRequest(
            source_file=DEFAULT_SOURCE_FILE,
            content=DEFAULT_CONTENT,
            context=DEFAULT_CONTEXT,
            doc_type=DEFAULT_DOC_TYPE,
            template_content=DEFAULT_TEMPLATE,
        )

        assert request.source_file == DEFAULT_SOURCE_FILE
        assert request.content == DEFAULT_CONTENT
        assert request.context == DEFAULT_CONTEXT
        assert request.doc_type == DEFAULT_DOC_TYPE
        assert request.template_content == DEFAULT_TEMPLATE

    def test_generation_request_when_missing_source_file_then_raises_value_error(self):
        """Test that missing source_file raises ValueError."""
        with pytest.raises(ValueError, match="source_file is required"):
            GenerationRequest(
                source_file=None,  # type: ignore
                content=DEFAULT_CONTENT,
            )

    def test_generation_request_when_empty_content_then_raises_value_error(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            GenerationRequest(source_file=DEFAULT_SOURCE_FILE, content="")

    def test_generation_request_when_invalid_context_type_then_raises_value_error(self):
        """Test that non-dict context raises ValueError."""
        with pytest.raises(ValueError, match="context must be a dictionary"):
            GenerationRequest(
                source_file=DEFAULT_SOURCE_FILE,
                content=DEFAULT_CONTENT,
                context="invalid",  # type: ignore
            )

    @patch("spec_cli.ai.providers.base.normalize_path_separators")
    def test_generation_request_when_created_then_normalizes_path(self, mock_normalize):
        """Test that source_file path is normalized during creation."""
        mock_normalize.return_value = NORMALIZED_PATH

        request = GenerationRequest(
            source_file=Path("src\\models\\user.py"), content=DEFAULT_CONTENT
        )

        mock_normalize.assert_called_once()
        assert str(request.source_file) == NORMALIZED_PATH


class TestGenerationRequestUtilityMethods:
    """Test GenerationRequest utility methods."""

    def test_get_file_extension_when_python_file_then_returns_py_extension(self):
        """Test that get_file_extension returns correct extension."""
        request = GenerationRequest(
            source_file=Path("test.py"), content=DEFAULT_CONTENT
        )

        assert request.get_file_extension() == TEST_EXTENSION

    def test_get_file_extension_when_uppercase_extension_then_returns_lowercase(self):
        """Test that get_file_extension returns lowercase extension."""
        request = GenerationRequest(
            source_file=Path("test.PY"), content=DEFAULT_CONTENT
        )

        assert request.get_file_extension() == TEST_EXTENSION

    def test_get_content_size_when_content_provided_then_returns_correct_size(self):
        """Test that get_content_size returns correct character count."""
        request = GenerationRequest(
            source_file=DEFAULT_SOURCE_FILE, content=DEFAULT_CONTENT
        )

        assert request.get_content_size() == CONTENT_SIZE

    @patch("spec_cli.ai.providers.base.normalize_path_separators")
    def test_get_normalized_path_when_called_then_returns_normalized_string(
        self, mock_normalize
    ):
        """Test that get_normalized_path returns normalized path string."""
        mock_normalize.return_value = NORMALIZED_PATH

        request = GenerationRequest(
            source_file=DEFAULT_SOURCE_FILE, content=DEFAULT_CONTENT
        )

        result = request.get_normalized_path()

        assert result == NORMALIZED_PATH
        mock_normalize.assert_called()


class TestGenerationRequestCrossPlatformPaths:
    """Test GenerationRequest cross-platform path handling."""

    @patch("spec_cli.ai.providers.base.normalize_path_separators")
    def test_generation_request_when_windows_path_then_normalizes_correctly(
        self, mock_normalize
    ):
        """Test Windows path normalization."""
        windows_path = "src\\models\\user.py"
        mock_normalize.return_value = "src/models/user.py"

        request = GenerationRequest(
            source_file=Path(windows_path), content=DEFAULT_CONTENT
        )

        normalized_result = request.get_normalized_path()
        expected = normalize_path_separators("src/models/user.py")
        actual = normalize_path_separators(normalized_result)
        assert actual == expected

    @patch("spec_cli.ai.providers.base.normalize_path_separators")
    def test_get_file_extension_when_windows_path_then_handles_correctly(
        self, mock_normalize
    ):
        """Test file extension extraction with Windows paths."""
        mock_normalize.return_value = "src/models/user.py"

        request = GenerationRequest(
            source_file=Path("src\\models\\user.py"), content=DEFAULT_CONTENT
        )

        assert request.get_file_extension() == TEST_EXTENSION


class TestGenerationResultValidation:
    """Test GenerationResult validation for success/failure states."""

    def test_generation_result_when_successful_with_content_then_creates_successfully(
        self,
    ):
        """Test successful result with content creates correctly."""
        result = GenerationResult(
            success=True,
            content=SAMPLE_CONTENT_DICT,
            metadata=SAMPLE_METADATA,
            processing_time_ms=DEFAULT_PROCESSING_TIME,
        )

        assert result.success is True
        assert result.content == SAMPLE_CONTENT_DICT
        assert result.metadata == SAMPLE_METADATA
        assert result.processing_time_ms == DEFAULT_PROCESSING_TIME
        assert result.error is None

    def test_generation_result_when_failed_with_error_then_creates_successfully(self):
        """Test failed result with error message creates correctly."""
        result = GenerationResult(success=False, error=ERROR_MESSAGE)

        assert result.success is False
        assert result.error == ERROR_MESSAGE
        assert result.content == {}
        assert result.metadata == {}

    def test_generation_result_when_successful_without_content_then_raises_value_error(
        self,
    ):
        """Test that successful result without content raises ValueError."""
        with pytest.raises(ValueError, match="Successful result must have content"):
            GenerationResult(success=True)

    def test_generation_result_when_failed_without_error_then_raises_value_error(self):
        """Test that failed result without error message raises ValueError."""
        with pytest.raises(ValueError, match="Failed result must have error message"):
            GenerationResult(success=False)


class TestGenerationResultUtilityMethods:
    """Test GenerationResult content retrieval methods."""

    def test_get_main_content_when_index_exists_then_returns_index_content(self):
        """Test get_main_content returns index.md content."""
        result = GenerationResult(success=True, content=SAMPLE_CONTENT_DICT)

        assert result.get_main_content() == SAMPLE_CONTENT_DICT["index.md"]

    def test_get_main_content_when_index_missing_then_returns_empty_string(self):
        """Test get_main_content returns empty string when index.md missing."""
        result = GenerationResult(success=True, content={"other.md": "content"})

        assert result.get_main_content() == ""

    def test_get_history_content_when_history_exists_then_returns_history_content(self):
        """Test get_history_content returns history.md content."""
        result = GenerationResult(success=True, content=SAMPLE_CONTENT_DICT)

        assert result.get_history_content() == SAMPLE_CONTENT_DICT["history.md"]

    def test_get_history_content_when_history_missing_then_returns_empty_string(self):
        """Test get_history_content returns empty string when history.md missing."""
        result = GenerationResult(success=True, content={"index.md": "content"})

        assert result.get_history_content() == ""


class TestGenerationResultCompleteDocumentationCheck:
    """Test GenerationResult completeness validation."""

    def test_has_complete_documentation_when_index_with_content_then_returns_true(self):
        """Test has_complete_documentation returns True for complete docs."""
        result = GenerationResult(
            success=True, content={"index.md": "# Documentation\nThis is content."}
        )

        assert result.has_complete_documentation() is True

    def test_has_complete_documentation_when_index_empty_then_returns_false(self):
        """Test has_complete_documentation returns False for empty index."""
        result = GenerationResult(success=True, content={"index.md": "   "})

        assert result.has_complete_documentation() is False

    def test_has_complete_documentation_when_no_index_then_returns_false(self):
        """Test has_complete_documentation returns False when no index.md."""
        result = GenerationResult(success=True, content={"history.md": "content"})

        assert result.has_complete_documentation() is False


class ConcreteAIProvider(AIProvider):
    """Concrete implementation of AIProvider for testing."""

    def __init__(self, available: bool = True):
        """Initialize with availability status."""
        super().__init__()
        self._available = available

    def is_available(self) -> bool:
        """Return availability status."""
        return self._available

    def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate mock documentation."""
        return GenerationResult(
            success=True, content={"index.md": "Generated documentation"}
        )

    def cleanup(self) -> None:
        """Clean up resources."""
        pass


class TestAIProviderAbstractMethods:
    """Test that abstract methods cannot be instantiated."""

    def test_ai_provider_when_instantiated_directly_then_raises_type_error(self):
        """Test that AIProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            AIProvider()  # type: ignore

    def test_ai_provider_when_concrete_implementation_then_can_instantiate(self):
        """Test that concrete implementation can be instantiated."""
        provider = ConcreteAIProvider()

        assert isinstance(provider, AIProvider)
        assert hasattr(provider, "logger")
        assert provider.is_available() is True


class TestAIProviderRequestValidation:
    """Test AIProvider request validation."""

    def test_validate_request_when_valid_request_then_passes_validation(self):
        """Test that valid request passes validation."""
        provider = ConcreteAIProvider()
        request = GenerationRequest(
            source_file=DEFAULT_SOURCE_FILE, content=DEFAULT_CONTENT
        )

        # Should not raise any exception
        provider.validate_request(request)

    def test_validate_request_when_invalid_type_then_raises_value_error(self):
        """Test that non-GenerationRequest raises ValueError."""
        provider = ConcreteAIProvider()

        with pytest.raises(
            ValueError, match="request must be a GenerationRequest instance"
        ):
            provider.validate_request("invalid")  # type: ignore

    def test_validate_request_when_called_then_logs_debug_message(self):
        """Test that validation logs debug message with normalized path."""
        provider = ConcreteAIProvider()
        request = GenerationRequest(
            source_file=DEFAULT_SOURCE_FILE, content=DEFAULT_CONTENT
        )

        # Mock the provider's logger
        provider.logger = Mock()

        provider.validate_request(request)

        # Check that logger.debug was called on the provider's logger
        provider.logger.debug.assert_called_once()


class TestAIProviderInfoMethod:
    """Test AIProvider info metadata."""

    def test_get_provider_info_when_available_provider_then_returns_complete_info(self):
        """Test get_provider_info returns complete metadata for available provider."""
        provider = ConcreteAIProvider(available=True)

        info = provider.get_provider_info()

        assert info["provider_class"] == "ConcreteAIProvider"
        assert info["available"] is True
        assert info["supports_cleanup"] is True

    def test_get_provider_info_when_unavailable_provider_then_returns_unavailable_status(
        self,
    ):
        """Test get_provider_info returns unavailable status."""
        provider = ConcreteAIProvider(available=False)

        info = provider.get_provider_info()

        assert info["provider_class"] == "ConcreteAIProvider"
        assert info["available"] is False
        assert info["supports_cleanup"] is True


class TestInvalidRequestCreation:
    """Test various invalid request scenarios."""

    def test_generation_request_when_none_source_file_then_raises_value_error(self):
        """Test that None source_file raises ValueError."""
        with pytest.raises(ValueError, match="source_file is required"):
            GenerationRequest(
                source_file=None,  # type: ignore
                content=DEFAULT_CONTENT,
            )

    def test_generation_request_when_none_content_then_raises_value_error(self):
        """Test that None content raises ValueError."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            GenerationRequest(
                source_file=DEFAULT_SOURCE_FILE,
                content=None,  # type: ignore
            )

    def test_generation_request_when_list_context_then_raises_value_error(self):
        """Test that list context raises ValueError."""
        with pytest.raises(ValueError, match="context must be a dictionary"):
            GenerationRequest(
                source_file=DEFAULT_SOURCE_FILE,
                content=DEFAULT_CONTENT,
                context=["invalid", "context"],  # type: ignore
            )


class TestInvalidResultCreation:
    """Test various invalid result scenarios."""

    def test_generation_result_when_success_true_empty_content_then_raises_value_error(
        self,
    ):
        """Test that successful result with empty dict content raises ValueError."""
        with pytest.raises(ValueError, match="Successful result must have content"):
            GenerationResult(success=True, content={})

    def test_generation_result_when_success_false_no_error_then_raises_value_error(
        self,
    ):
        """Test that failed result without error raises ValueError."""
        with pytest.raises(ValueError, match="Failed result must have error message"):
            GenerationResult(success=False, error=None)

    def test_generation_result_when_success_false_empty_error_then_raises_value_error(
        self,
    ):
        """Test that failed result with empty error string raises ValueError."""
        with pytest.raises(ValueError, match="Failed result must have error message"):
            GenerationResult(success=False, error="")


class TestRequestPathNormalizationConsistency:
    """Test normalized path methods across platforms."""

    @patch("spec_cli.ai.providers.base.normalize_path_separators")
    def test_path_normalization_when_multiple_calls_then_consistent_results(
        self, mock_normalize
    ):
        """Test that multiple path normalization calls return consistent results."""
        mock_normalize.return_value = NORMALIZED_PATH

        request = GenerationRequest(
            source_file=Path("src\\models\\user.py"), content=DEFAULT_CONTENT
        )

        # Call normalization methods multiple times
        result1 = request.get_normalized_path()
        result2 = request.get_normalized_path()

        assert result1 == result2
        assert result1 == NORMALIZED_PATH

    def test_path_handling_when_posix_and_windows_paths_then_normalizes_consistently(
        self,
    ):
        """Test that both POSIX and Windows paths normalize consistently."""
        posix_request = GenerationRequest(
            source_file=Path("src/models/user.py"), content=DEFAULT_CONTENT
        )

        windows_request = GenerationRequest(
            source_file=Path("src\\models\\user.py"), content=DEFAULT_CONTENT
        )

        # Both should normalize to the same result
        posix_normalized = normalize_path_separators(
            posix_request.get_normalized_path()
        )
        windows_normalized = normalize_path_separators(
            windows_request.get_normalized_path()
        )

        assert posix_normalized == windows_normalized
