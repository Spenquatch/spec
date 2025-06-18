"""Unit tests for Slice 3.1a: AI Provider Integration."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Test constants
TEST_MODEL_NAME = "test-model"
TEST_TARGET_PATH = "/test/source.py"
TEST_DOC_TYPE = "index"
TEST_CONTENT = "def test_function(): pass"
TEST_GENERATED_CONTENT = "# Generated Documentation\nThis is a test function."
DEFAULT_AI_CONFIG = {"enabled": True, "provider": "local"}
EXPECTED_METADATA_KEYS = {
    "provider_type",
    "generation_time",
    "files_generated",
    "doc_type",
    "source_file",
}


@pytest.fixture
def mock_ai_config():
    """Mock AI configuration for testing."""
    config = Mock()
    config.enabled = True
    config.provider = "local"
    config.local = Mock()
    config.local.model_name = TEST_MODEL_NAME
    return config


@pytest.fixture
def mock_local_ai_provider():
    """Mock LocalAI provider for testing."""
    provider = Mock()
    provider.provider_type = "local"
    provider.is_available.return_value = True
    provider.get_provider_info.return_value = {"model": TEST_MODEL_NAME}
    return provider


@pytest.fixture
def mock_generation_result():
    """Mock successful generation result."""
    result = Mock()
    result.success = True
    result.content = {"index.md": TEST_GENERATED_CONTENT}
    result.error = None
    result.metadata = {"tokens_used": 100}
    return result


@pytest.fixture
def test_target_path(tmp_path):
    """Create a test file for generation."""
    test_file = tmp_path / "source.py"
    test_file.write_text(TEST_CONTENT)
    return test_file


class TestCreateWorkflowResult:
    """Test workflow result creation helper function."""

    def test_create_workflow_result_when_success_then_returns_success_structure(self):
        """Test successful workflow result creation."""
        from spec_cli.ai.providers.manager import create_workflow_result

        data = {"test": "data"}
        message = "Success message"

        result = create_workflow_result(True, data, message=message)

        assert result["success"] is True
        assert result["data"] == data
        assert result["message"] == message
        assert "timestamp" in result

    def test_create_workflow_result_when_failure_then_returns_error_structure(self):
        """Test failed workflow result creation."""
        from spec_cli.ai.providers.manager import create_workflow_result

        error = "Test error"
        data = {"fallback_needed": True}

        result = create_workflow_result(False, data, error=error)

        assert result["success"] is False
        assert result["error"] == error
        assert result["data"] == data
        assert "timestamp" in result

    def test_create_workflow_result_when_minimal_params_then_returns_defaults(self):
        """Test workflow result with minimal parameters."""
        from spec_cli.ai.providers.manager import create_workflow_result

        result = create_workflow_result(True)

        assert result["success"] is True
        assert result["data"] == {}
        assert "timestamp" in result


class TestProviderManager:
    """Test AI provider manager functionality."""

    def test_init_with_ai_config_creates_manager(self, mock_ai_config):
        """Test provider manager initialization."""
        from spec_cli.ai.providers.manager import ProviderManager

        manager = ProviderManager(mock_ai_config)

        assert manager.ai_config == mock_ai_config
        assert hasattr(manager, "logger")

    def test_get_available_provider_when_ai_disabled_then_returns_none(
        self, mock_ai_config
    ):
        """Test provider selection when AI is disabled."""
        from spec_cli.ai.providers.manager import ProviderManager

        mock_ai_config.enabled = False
        manager = ProviderManager(mock_ai_config)

        result = manager.get_available_provider()

        assert result is None

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    def test_get_available_provider_when_local_available_then_returns_provider(
        self, mock_local_provider_class, mock_ai_config
    ):
        """Test provider selection with available local provider."""
        from spec_cli.ai.providers.manager import ProviderManager

        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_local_provider_class.return_value = mock_provider

        manager = ProviderManager(mock_ai_config)
        result = manager.get_available_provider()

        assert result == mock_provider
        mock_local_provider_class.assert_called_once_with(mock_ai_config.local)

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    def test_get_available_provider_when_local_unavailable_then_returns_none(
        self, mock_local_provider_class, mock_ai_config
    ):
        """Test provider selection with unavailable local provider."""
        from spec_cli.ai.providers.manager import ProviderManager

        mock_provider = Mock()
        mock_provider.is_available.return_value = False
        mock_local_provider_class.return_value = mock_provider

        manager = ProviderManager(mock_ai_config)
        result = manager.get_available_provider()

        assert result is None

    def test_get_available_provider_when_exception_occurs_then_returns_none(
        self, mock_ai_config
    ):
        """Test provider selection with exception handling."""
        from spec_cli.ai.providers.manager import ProviderManager

        # Simulate exception by setting invalid provider type
        mock_ai_config.provider = "invalid"
        manager = ProviderManager(mock_ai_config)

        result = manager.get_available_provider()

        assert result is None

    def test_get_provider_info_when_no_provider_then_returns_base_info(
        self, mock_ai_config
    ):
        """Test provider info when no provider available."""
        from spec_cli.ai.providers.manager import ProviderManager

        mock_ai_config.enabled = False
        manager = ProviderManager(mock_ai_config)

        info = manager.get_provider_info()

        assert info["ai_enabled"] is False
        assert info["provider_available"] is False
        assert info["provider_details"] == {}

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    def test_get_provider_info_when_provider_available_then_returns_detailed_info(
        self, mock_local_provider_class, mock_ai_config
    ):
        """Test provider info with available provider."""
        from spec_cli.ai.providers.manager import ProviderManager

        mock_provider = Mock()
        mock_provider.is_available.return_value = True
        mock_provider.get_provider_info.return_value = {"model": TEST_MODEL_NAME}
        mock_local_provider_class.return_value = mock_provider

        manager = ProviderManager(mock_ai_config)
        info = manager.get_provider_info()

        assert info["ai_enabled"] is True
        assert info["provider_available"] is True
        assert info["provider_details"]["model"] == TEST_MODEL_NAME


class TestAIDocumentationGenerator:
    """Test AI documentation generator functionality."""

    def test_init_with_provider_creates_generator(self, mock_local_ai_provider):
        """Test generator initialization."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        generator = AIDocumentationGenerator(mock_local_ai_provider)

        assert generator.provider == mock_local_ai_provider
        assert hasattr(generator, "logger")

    def test_generate_documentation_when_path_not_exists_then_returns_error(
        self, mock_local_ai_provider
    ):
        """Test generation with non-existent path."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        generator = AIDocumentationGenerator(mock_local_ai_provider)
        nonexistent_path = Path("/nonexistent/file.py")

        result = generator.generate_documentation(nonexistent_path, TEST_DOC_TYPE)

        assert result["success"] is False
        assert "does not exist" in result["error"]
        assert result["data"]["fallback_needed"] is True

    def test_generate_documentation_when_valid_file_then_generates_docs(
        self, mock_local_ai_provider, mock_generation_result, test_target_path
    ):
        """Test successful documentation generation for file."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        mock_local_ai_provider.generate_documentation.return_value = (
            mock_generation_result
        )
        generator = AIDocumentationGenerator(mock_local_ai_provider)

        result = generator.generate_documentation(test_target_path, TEST_DOC_TYPE)

        assert result["success"] is True
        assert str(test_target_path) in result["data"]["generated_docs"]
        assert (
            result["data"]["generated_docs"][str(test_target_path)]
            == TEST_GENERATED_CONTENT
        )

        metadata = result["data"]["generation_metadata"]
        assert all(key in metadata for key in EXPECTED_METADATA_KEYS)
        assert metadata["doc_type"] == TEST_DOC_TYPE
        assert metadata["files_generated"] == 1

    def test_generate_documentation_when_directory_then_processes_directory(
        self, mock_local_ai_provider, mock_generation_result, tmp_path
    ):
        """Test documentation generation for directory."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        mock_local_ai_provider.generate_documentation.return_value = (
            mock_generation_result
        )
        generator = AIDocumentationGenerator(mock_local_ai_provider)

        result = generator.generate_documentation(tmp_path, TEST_DOC_TYPE)

        assert result["success"] is True
        assert str(tmp_path) in result["data"]["generated_docs"]

    def test_generate_documentation_when_ai_generation_fails_then_returns_error(
        self, mock_local_ai_provider, test_target_path
    ):
        """Test handling of AI generation failure."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        failed_result = Mock()
        failed_result.success = False
        failed_result.error = "AI model failed"
        failed_result.content = None
        mock_local_ai_provider.generate_documentation.return_value = failed_result

        generator = AIDocumentationGenerator(mock_local_ai_provider)
        result = generator.generate_documentation(test_target_path, TEST_DOC_TYPE)

        assert result["success"] is False
        assert "AI model failed" in result["error"]
        assert result["data"]["fallback_needed"] is True

    def test_generate_documentation_when_empty_content_then_returns_error(
        self, mock_local_ai_provider, test_target_path
    ):
        """Test handling of empty AI generation result."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        empty_result = Mock()
        empty_result.success = True
        empty_result.content = ""
        empty_result.error = None
        mock_local_ai_provider.generate_documentation.return_value = empty_result

        generator = AIDocumentationGenerator(mock_local_ai_provider)
        result = generator.generate_documentation(test_target_path, TEST_DOC_TYPE)

        assert result["success"] is False
        assert "empty results" in result["error"]
        assert result["data"]["fallback_needed"] is True

    def test_generate_documentation_when_file_read_error_then_returns_error(
        self, mock_local_ai_provider, tmp_path
    ):
        """Test handling of file reading errors."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        # Create a file with invalid encoding
        bad_file = tmp_path / "bad.py"
        bad_file.write_bytes(b"\\xff\\xfe invalid utf-8")

        generator = AIDocumentationGenerator(mock_local_ai_provider)

        with patch.object(Path, "read_text") as mock_read:
            mock_read.side_effect = [
                UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
                Exception("Read failed"),
            ]

            result = generator.generate_documentation(bad_file, TEST_DOC_TYPE)

            assert result["success"] is False
            assert "Failed to read file content" in result["error"]
            assert result["data"]["fallback_needed"] is True

    def test_generate_documentation_when_exception_occurs_then_handles_gracefully(
        self, mock_local_ai_provider, test_target_path
    ):
        """Test exception handling in generation process."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        mock_local_ai_provider.generate_documentation.side_effect = Exception(
            "Unexpected error"
        )
        generator = AIDocumentationGenerator(mock_local_ai_provider)

        result = generator.generate_documentation(test_target_path, TEST_DOC_TYPE)

        assert result["success"] is False
        assert "AI documentation generation failed" in result["error"]
        assert result["data"]["fallback_needed"] is True


class TestGenerateWithAI:
    """Test the main AI generation function."""

    @patch("spec_cli.ai.generation.ai_generator.AIConfigLoader")
    @patch("spec_cli.ai.generation.ai_generator.ProviderManager")
    @patch("spec_cli.ai.generation.ai_generator.AIDocumentationGenerator")
    def test_generate_with_ai_when_valid_inputs_then_generates_successfully(
        self,
        mock_generator_class,
        mock_manager_class,
        mock_loader_class,
        test_target_path,
    ):
        """Test successful AI generation workflow."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        # Setup mocks
        mock_loader = Mock()
        mock_config = Mock()
        mock_loader.load_ai_config.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        mock_manager = Mock()
        mock_provider = Mock()
        mock_manager.get_available_provider.return_value = mock_provider
        mock_manager_class.return_value = mock_manager

        mock_generator = Mock()
        expected_result = {
            "success": True,
            "data": {
                "generated_docs": {str(test_target_path): TEST_GENERATED_CONTENT},
                "generation_metadata": {
                    "provider_type": "local",
                    "generation_time": "2023-01-01T00:00:00",
                    "files_generated": 1,
                    "doc_type": TEST_DOC_TYPE,
                },
            },
        }
        mock_generator.generate_documentation.return_value = expected_result
        mock_generator_class.return_value = mock_generator

        result = generate_with_ai(test_target_path, TEST_DOC_TYPE)

        assert result["success"] is True
        mock_loader_class.assert_called_once()
        mock_manager_class.assert_called_once_with(mock_config)
        mock_generator_class.assert_called_once_with(mock_provider)

    @patch("spec_cli.ai.generation.ai_generator.AIConfigLoader")
    @patch("spec_cli.ai.generation.ai_generator.ProviderManager")
    def test_generate_with_ai_when_no_provider_then_returns_fallback_error(
        self, mock_manager_class, mock_loader_class, test_target_path
    ):
        """Test AI generation when no provider is available."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        # Setup mocks
        mock_loader = Mock()
        mock_config = Mock()
        mock_loader.load_ai_config.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        mock_manager = Mock()
        mock_manager.get_available_provider.return_value = None
        mock_manager_class.return_value = mock_manager

        result = generate_with_ai(test_target_path, TEST_DOC_TYPE)

        assert result["success"] is False
        assert "No AI provider available" in result["error"]
        assert result["data"]["fallback_needed"] is True

    @patch("spec_cli.ai.generation.ai_generator.AIConfigLoader")
    def test_generate_with_ai_when_config_override_then_applies_overrides(
        self, mock_loader_class, test_target_path
    ):
        """Test AI generation with configuration overrides."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        # Setup mocks
        mock_loader = Mock()
        mock_config = Mock()
        mock_config.enabled = True
        mock_config.provider = "local"
        mock_loader.load_ai_config.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        override_config = {"enabled": False}

        with patch(
            "spec_cli.ai.generation.ai_generator.ProviderManager"
        ) as mock_manager_class:
            mock_manager = Mock()
            mock_manager.get_available_provider.return_value = None
            mock_manager_class.return_value = mock_manager

            result = generate_with_ai(test_target_path, TEST_DOC_TYPE, override_config)

            # Verify override was applied
            assert mock_config.enabled is False
            assert result["success"] is False

    @patch("spec_cli.ai.generation.ai_generator.AIConfigLoader")
    def test_generate_with_ai_when_initialization_fails_then_returns_error(
        self, mock_loader_class, test_target_path
    ):
        """Test AI generation initialization failure handling."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        mock_loader_class.side_effect = Exception("Config loading failed")

        result = generate_with_ai(test_target_path, TEST_DOC_TYPE)

        assert result["success"] is False
        assert "AI generation initialization failed" in result["error"]
        assert result["data"]["fallback_needed"] is True


class TestCrossPlatformCompatibility:
    """Test cross-platform path handling."""

    def test_generate_documentation_when_windows_path_then_handles_correctly(
        self, mock_local_ai_provider, mock_generation_result
    ):
        """Test documentation generation with Windows-style paths."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        mock_local_ai_provider.generate_documentation.return_value = (
            mock_generation_result
        )
        generator = AIDocumentationGenerator(mock_local_ai_provider)

        # Mock a Windows path
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.read_text", return_value=TEST_CONTENT),
        ):
            windows_path = Path("C:\\project\\source.py")
            result = generator.generate_documentation(windows_path, TEST_DOC_TYPE)

            assert result["success"] is True
            assert str(windows_path) in result["data"]["generated_docs"]


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    def test_provider_manager_when_invalid_config_then_handles_gracefully(self):
        """Test provider manager with invalid configuration."""
        from spec_cli.ai.providers.manager import ProviderManager

        invalid_config = None
        manager = ProviderManager(invalid_config)

        # Should handle gracefully and return None
        result = manager.get_available_provider()
        assert result is None

    def test_ai_generator_when_provider_none_then_handles_gracefully(self):
        """Test generator with None provider."""
        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        generator = AIDocumentationGenerator(None)
        result = generator.generate_documentation(Path("/test"), TEST_DOC_TYPE)

        # Should handle gracefully and return error
        assert result["success"] is False
        assert result["data"]["fallback_needed"] is True


class TestPerformanceRequirements:
    """Test performance requirements for AI generation."""

    def test_generate_documentation_performance_within_limits(
        self, mock_local_ai_provider, mock_generation_result, test_target_path
    ):
        """Test that generation completes within 20 second limit."""
        import time

        from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator

        mock_local_ai_provider.generate_documentation.return_value = (
            mock_generation_result
        )
        generator = AIDocumentationGenerator(mock_local_ai_provider)

        start_time = time.time()
        result = generator.generate_documentation(test_target_path, TEST_DOC_TYPE)
        end_time = time.time()

        assert result["success"] is True
        assert (end_time - start_time) < 20  # Must complete within 20 seconds
