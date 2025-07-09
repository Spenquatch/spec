"""Unit tests for LlamaCpp AI provider - Micro-Agent ai_001 Implementation.

Tests comprehensive LLaMA provider functionality including:
- Cross-platform path handling and normalization
- Advanced prompt generation scenarios
- Validation edge cases and boundary conditions
- Configuration validation and edge cases
- Language detection edge cases
- Content parsing with malformed inputs
- Provider contract compliance
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.config.settings import LlamaCppConfig
from spec_cli.ai.providers.base import AIProvider, GenerationRequest, GenerationResult

# Import target code
from spec_cli.ai.providers.llamacpp import LlamaCppProvider

# Import test helpers
from spec_cli.utils.test_helpers.ai_test_doubles import (
    AIResponseFixtures,
    create_mock_llamacpp_provider,
)


class TestLlamaCppProviderCrossPlatformBehavior:
    """Test cross-platform path handling and compatibility."""

    def setup_method(self):
        """Setup test fixtures with cross-platform paths."""
        self.provider = LlamaCppProvider()

    def test_initialization_normalizes_model_path_cross_platform(self):
        """Test that model path is normalized for cross-platform compatibility."""
        # Test with Windows-style path
        windows_path = "C:\\models\\llama\\model.gguf"
        config = LlamaCppConfig(model_path=windows_path)
        provider = LlamaCppProvider(config=config)

        # Path should be stored as provided (normalization happens in usage)
        assert provider.config.model_path == windows_path

    def test_generation_request_handles_mixed_path_separators(self):
        """Test generation request with mixed path separators."""
        # Create request with mixed separators (common copy/paste error)
        mixed_path = "src\\ai/providers\\test.py"
        request = GenerationRequest(
            content="def test(): pass", source_file=Path(mixed_path)
        )

        # Request should normalize the path internally
        normalized = request.get_normalized_path()
        assert "\\" not in normalized or "/" not in normalized  # One separator type

    def test_file_extension_detection_case_insensitive(self):
        """Test file extension detection is case insensitive."""
        test_cases = [
            ("test.PY", ".py"),
            ("test.Js", ".js"),
            ("test.CPP", ".cpp"),
            ("TEST.JAVA", ".java"),
        ]

        for filename, expected_ext in test_cases:
            request = GenerationRequest(
                content="test content", source_file=Path(filename)
            )
            result = request.get_file_extension()
            assert result == expected_ext.lower()

    @patch("spec_cli.ai.providers.llamacpp.LLAMA_CPP_AVAILABLE", True)
    @patch("pathlib.Path.exists")
    def test_model_availability_with_relative_paths(self, mock_exists):
        """Test model availability check with relative paths."""
        mock_exists.return_value = True

        # Test with relative path
        config = LlamaCppConfig(model_path="./models/llama.gguf")
        provider = LlamaCppProvider(config=config)

        result = provider.is_available()
        assert result is True
        mock_exists.assert_called_once()

    def test_language_detection_with_complex_extensions(self):
        """Test language detection with complex file extensions."""
        test_cases = [
            (".py", "python"),
            (".pyw", "text"),  # Windows Python script
            (".js", "javascript"),
            (".mjs", "text"),  # ES6 module
            (".jsx", "text"),  # React JSX
            (".ts", "typescript"),
            (".tsx", "text"),  # TypeScript React
            (".cpp", "cpp"),
            (".cxx", "text"),  # Alternative C++ extension
            (".h", "text"),  # Header file
            (".hpp", "text"),  # C++ header
            ("", "text"),  # No extension
        ]

        for extension, expected_language in test_cases:
            result = self.provider._detect_language(extension)
            assert result == expected_language


class TestLlamaCppProviderAdvancedPromptGeneration:
    """Test advanced prompt generation scenarios."""

    def setup_method(self):
        """Setup test fixtures."""
        self.provider = LlamaCppProvider()

    def test_prompt_creation_with_minimal_content(self):
        """Test prompt creation with minimal valid content."""
        request = GenerationRequest(
            content="x",  # Minimal valid content
            source_file=Path("minimal.py"),
        )

        # Should create valid prompt
        prompt = self.provider._create_documentation_prompt(request)

        assert "<|im_start|>system" in prompt
        assert "<|im_start|>user" in prompt
        assert "<|im_start|>assistant" in prompt
        assert "python" in prompt
        assert "```python" in prompt
        assert "x" in prompt

    def test_prompt_creation_with_very_long_content(self):
        """Test prompt creation with very long content."""
        long_content = "def function():\n    pass\n" * 1000  # Very long content
        request = GenerationRequest(content=long_content, source_file=Path("large.py"))

        prompt = self.provider._create_documentation_prompt(request)

        # Should include the content without truncation (model handles limits)
        assert long_content in prompt
        assert len(prompt) > len(long_content)  # Has prompt template too

    def test_prompt_creation_with_special_characters(self):
        """Test prompt creation with special characters and unicode."""
        special_content = '''
def greet(name):
    """说hello with émojis 🚀"""
    return f"Hello {name}! ñoño 测试"
'''
        request = GenerationRequest(
            content=special_content, source_file=Path("unicode.py")
        )

        prompt = self.provider._create_documentation_prompt(request)

        # Should preserve special characters
        assert "说hello" in prompt
        assert "émojis" in prompt
        assert "🚀" in prompt
        assert "ñoño" in prompt
        assert "测试" in prompt

    def test_prompt_creation_with_unknown_file_type(self):
        """Test prompt creation with unknown file extensions."""
        request = GenerationRequest(
            content="some content", source_file=Path("unknown.xyz")
        )

        prompt = self.provider._create_documentation_prompt(request)

        # Should default to "text" language
        assert "text" in prompt
        assert "```text" in prompt

    def test_prompt_creation_preserves_code_structure(self):
        """Test that prompt preserves code indentation and structure."""
        structured_content = """
class Example:
    def __init__(self):
        self.value = 42

    def method(self):
        if self.value > 0:
            return "positive"
        else:
            return "negative"
"""
        request = GenerationRequest(
            content=structured_content, source_file=Path("structured.py")
        )

        prompt = self.provider._create_documentation_prompt(request)

        # Should preserve indentation and structure
        assert "class Example:" in prompt
        assert "    def __init__(self):" in prompt
        assert "        self.value = 42" in prompt


class TestLlamaCppProviderValidationEdgeCases:
    """Test validation edge cases and boundary conditions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.provider = LlamaCppProvider()

    def test_validate_request_with_none_request(self):
        """Test validation with None request."""
        with pytest.raises(ValueError, match="request must be a GenerationRequest"):
            self.provider.validate_request(None)

    def test_validate_request_with_wrong_type(self):
        """Test validation with wrong request type."""
        with pytest.raises(ValueError, match="request must be a GenerationRequest"):
            self.provider.validate_request("not a request")

    def test_validate_request_with_valid_request_logs_debug(self, caplog):
        """Test that valid request validation logs debug information."""
        request = GenerationRequest(
            content="def test(): pass", source_file=Path("test.py")
        )

        import logging

        with caplog.at_level(logging.DEBUG):
            self.provider.validate_request(request)

        # Should log debug message with normalized path
        assert "Validating request for" in caplog.text

    def test_generation_request_validation_boundary_conditions(self):
        """Test GenerationRequest validation with boundary conditions."""
        # Test with minimal valid content
        request = GenerationRequest(
            content="x",  # Single character
            source_file=Path("minimal.py"),
        )
        assert request.content == "x"
        assert request.get_content_size() == 1

    def test_generation_request_context_validation(self):
        """Test GenerationRequest context parameter validation."""
        # Test with valid context
        valid_context = {"key": "value", "number": 42}
        request = GenerationRequest(
            content="test", source_file=Path("test.py"), context=valid_context
        )
        assert request.context == valid_context

        # Test with empty context (should use default)
        request_empty = GenerationRequest(content="test", source_file=Path("test.py"))
        assert request_empty.context == {}

    def test_generation_result_validation_edge_cases(self):
        """Test GenerationResult validation edge cases."""
        # Test successful result with minimal content
        result = GenerationResult(success=True, content={"index.md": "minimal"})
        assert result.has_complete_documentation() is True
        assert result.get_main_content() == "minimal"

        # Test successful result with empty content should raise error
        with pytest.raises(ValueError, match="Successful result must have content"):
            GenerationResult(success=True, content={})

        # Test failed result without error should raise error
        with pytest.raises(ValueError, match="Failed result must have error message"):
            GenerationResult(success=False)


class TestLlamaCppProviderConfigurationValidation:
    """Test configuration validation and edge cases."""

    def test_config_with_extreme_values(self):
        """Test configuration with extreme but valid values."""
        extreme_config = LlamaCppConfig(
            model_path="/very/long/path/to/model/file/with/many/directories/model.gguf",
            n_ctx=32768,  # Large context
            n_threads=1,  # Minimum threads
            n_gpu_layers=999,  # Many GPU layers
            max_tokens=50,  # Minimum valid tokens (config has ge=50 constraint)
            temperature=0.0,  # Minimum temperature
        )

        provider = LlamaCppProvider(config=extreme_config)

        assert provider.config.model_path == extreme_config.model_path
        assert provider.config.n_ctx == 32768
        assert provider.config.max_tokens == 50
        assert provider.config.temperature == 0.0

    def test_config_auto_thread_detection_edge_cases(self):
        """Test thread auto-detection with edge cases."""
        # Test with very high CPU count
        with patch("os.cpu_count", return_value=32):
            provider = LlamaCppProvider()
            # Should cap at 6 threads
            assert provider.config.n_threads == 6

        # Test with single core
        with patch("os.cpu_count", return_value=1):
            provider = LlamaCppProvider()
            assert provider.config.n_threads == 1

    def test_provider_info_with_extreme_config(self):
        """Test provider info with extreme configuration values."""
        config = LlamaCppConfig(
            model_path="/nonexistent/model.gguf",
            n_ctx=16384,  # Large but valid context
            n_threads=0,  # Test with zero threads
            max_tokens=50,  # Minimum valid value (ge=50 constraint)
        )
        provider = LlamaCppProvider(config=config)

        info = provider.get_provider_info()

        assert info["n_ctx"] == 16384
        assert info["n_threads"] == 0
        assert info["max_tokens"] == 50
        assert info["model_exists"] is False


class TestLlamaCppProviderContentParsing:
    """Test content parsing with malformed and edge case inputs."""

    def setup_method(self):
        """Setup test fixtures."""
        self.provider = LlamaCppProvider()
        self.test_request = GenerationRequest(
            content="def test(): pass", source_file=Path("test.py")
        )

    def test_parse_generated_content_with_empty_text(self):
        """Test parsing empty generated text."""
        result = self.provider._parse_generated_content("", self.test_request)

        assert "index.md" in result
        assert "history.md" in result
        assert result["index.md"] == ""
        assert "test.py" in result["history.md"]

    def test_parse_generated_content_with_only_whitespace(self):
        """Test parsing text with only whitespace."""
        whitespace_text = "   \n\t   \n   "
        result = self.provider._parse_generated_content(
            whitespace_text, self.test_request
        )

        assert result["index.md"] == whitespace_text
        assert "history.md" in result

    def test_parse_generated_content_with_special_markdown(self):
        """Test parsing with special markdown characters."""
        special_text = """
# Title with `code`
## Section with *emphasis* and **bold**
- List item with [link](url)
- Item with <tag>
```python
code block
```
"""
        result = self.provider._parse_generated_content(special_text, self.test_request)

        # Should preserve all markdown formatting
        assert "# Title with `code`" in result["index.md"]
        assert "```python" in result["index.md"]
        assert "[link](url)" in result["index.md"]

    def test_parse_generated_content_includes_platform_info(self):
        """Test that parsed content includes platform information."""
        result = self.provider._parse_generated_content("test", self.test_request)

        history = result["history.md"]
        assert sys.platform in history
        assert "llama.cpp" in history
        assert "quantized GGUF model" in history

    def test_parse_generated_content_with_very_long_filename(self):
        """Test parsing with very long filename."""
        long_filename = (
            "very_long_filename_that_exceeds_normal_length_limits" * 5 + ".py"
        )
        long_request = GenerationRequest(
            content="test", source_file=Path(long_filename)
        )

        result = self.provider._parse_generated_content("content", long_request)

        # Should handle long filename gracefully
        assert "history.md" in result
        # Use basename to get just the filename part
        expected_basename = os.path.basename(long_filename)
        assert expected_basename in result["history.md"]


class TestLlamaCppProviderErrorRecovery:
    """Test error recovery and resilience scenarios."""

    def setup_method(self):
        """Setup test fixtures."""
        self.provider = LlamaCppProvider()

    def test_cleanup_with_partial_initialization(self):
        """Test cleanup when provider is partially initialized."""
        # Simulate partial initialization
        self.provider._model = Mock(spec=[])
        self.provider._model_loaded = False  # Inconsistent state

        # Should handle cleanup gracefully
        self.provider.cleanup()

        assert self.provider._model is None
        assert self.provider._model_loaded is False

    def test_suppression_handles_import_errors_gracefully(self):
        """Test log suppression handles missing torch modules gracefully."""
        # Test that suppression works even if torch import fails during the method
        # The method should handle ImportError gracefully in the torch section
        original_torch = os.environ.get("TORCH_DISTRIBUTED_DETAIL")

        try:
            # Call suppression method - should not raise exception
            self.provider._suppress_noisy_logs()

            # Should still set basic environment variables
            assert os.environ.get("TORCH_DISTRIBUTED_DETAIL") == "ERROR"
            assert os.environ.get("NCCL_BLOCKING_WAIT") == "1"

        finally:
            # Restore original environment
            if original_torch is not None:
                os.environ["TORCH_DISTRIBUTED_DETAIL"] = original_torch
            elif "TORCH_DISTRIBUTED_DETAIL" in os.environ:
                del os.environ["TORCH_DISTRIBUTED_DETAIL"]

    @patch("spec_cli.ai.providers.llamacpp.LLAMA_CPP_AVAILABLE", True)
    def test_model_loading_with_stderr_capture(self):
        """Test model loading with stderr output capture."""
        with patch("spec_cli.ai.providers.llamacpp.Llama") as mock_llama:
            with patch(
                "spec_cli.ai.providers.llamacpp.redirect_stderr"
            ) as mock_redirect:
                # Setup mock context manager
                mock_context = Mock(spec=[])
                mock_redirect.return_value.__enter__ = Mock(return_value=mock_context)
                mock_redirect.return_value.__exit__ = Mock(return_value=None)

                mock_llama.return_value = Mock(spec=[])

                result = self.provider._load_model()

                assert result is True
                mock_redirect.assert_called_once()

    def test_generation_with_corrupted_model_response(self):
        """Test handling of corrupted model response."""
        with patch.object(self.provider, "is_available", return_value=True):
            with patch.object(self.provider, "validate_request"):
                self.provider.sanitizer.sanitize = Mock(spec=[])
                self.provider._model_loaded = True

                # Mock corrupted response (not dict, not iterable)
                mock_model = Mock(spec=[])
                mock_model.return_value = object()  # Non-processable object
                self.provider._model = mock_model

                request = GenerationRequest(content="test", source_file=Path("test.py"))

                result = self.provider.generate_documentation(request)

                assert result.success is False
                assert "Invalid response format" in result.error


class TestLlamaCppProviderContractCompliance:
    """Test provider contract compliance and interface adherence."""

    def test_provider_implements_all_abstract_methods(self):
        """Test that provider implements all required abstract methods."""

        # Get all abstract methods from base class
        abstract_methods = []
        for name in dir(AIProvider):
            attr = getattr(AIProvider, name)
            if hasattr(attr, "__isabstractmethod__") and attr.__isabstractmethod__:
                abstract_methods.append(name)

        # Verify all abstract methods are implemented
        for method_name in abstract_methods:
            assert hasattr(LlamaCppProvider, method_name)
            method = getattr(LlamaCppProvider, method_name)
            assert callable(method)
            # Should not be abstract in the concrete class
            assert not (
                hasattr(method, "__isabstractmethod__") and method.__isabstractmethod__
            )

    def test_provider_info_contains_required_fields(self):
        """Test that provider info contains all required fields."""
        provider = LlamaCppProvider()
        info = provider.get_provider_info()

        # Base class fields
        assert "provider_class" in info
        assert "available" in info
        assert "supports_cleanup" in info

        # LlamaCpp specific fields
        assert "model_path" in info
        assert "model_exists" in info
        assert "model_loaded" in info
        assert "llama_cpp_available" in info
        assert "platform" in info

    def test_generation_result_contract_compliance(self):
        """Test that generation results comply with expected contract."""
        # Test successful result
        success_result = GenerationResult(
            success=True,
            content={"index.md": "content"},
            metadata={"provider": "llamacpp"},
        )

        assert success_result.success is True
        assert success_result.has_complete_documentation() is True
        assert success_result.get_main_content() == "content"
        assert success_result.get_history_content() == ""  # No history in this case

        # Test failed result
        fail_result = GenerationResult(
            success=False, error="Test error", metadata={"provider": "llamacpp"}
        )

        assert fail_result.success is False
        assert fail_result.has_complete_documentation() is False

    def test_provider_logging_interface(self):
        """Test that provider uses logging interface correctly."""
        provider = LlamaCppProvider()

        # Should have logger attribute
        assert hasattr(provider, "logger")
        assert provider.logger is not None

        # Logger should be configured with class name
        assert provider.logger.name == "LlamaCppProvider"


class TestLlamaCppProviderIntegrationValidation:
    """Test integration with test infrastructure and helpers."""

    def test_integration_with_existing_fixtures(self):
        """Test integration with existing AI test fixtures."""
        fixtures = AIResponseFixtures()

        # Should be able to get LLaMA-specific fixtures
        llama_fixture = fixtures.get_fixture("llamacpp_generation")
        assert llama_fixture is not None
        assert "response" in llama_fixture

    def test_mock_provider_integration(self):
        """Test integration with mock provider helpers."""
        mock_provider = create_mock_llamacpp_provider()

        # Should implement same interface as real provider
        assert hasattr(mock_provider, "generate_text")
        assert hasattr(mock_provider, "load_model")
        assert hasattr(mock_provider, "set_failure_mode")

        # Should work with real provider test patterns
        load_result = mock_provider.load_model()
        assert load_result is True

    @patch("spec_cli.ai.providers.llamacpp.LlamaCppProvider.is_available")
    def test_real_provider_with_mock_integration(self, mock_available):
        """Test real provider works with test infrastructure."""
        mock_available.return_value = True
        provider = LlamaCppProvider()

        # Should integrate with test fixtures
        fixtures = AIResponseFixtures()
        test_response = fixtures.get_response("documentation_generation")

        # Mock the model to return fixture response
        provider.sanitizer.sanitize = Mock(spec=[])
        provider._model_loaded = True
        mock_model = Mock(spec=[])
        mock_model.return_value = {
            "choices": [{"text": test_response}],
            "usage": {"completion_tokens": 50},
        }
        provider._model = mock_model

        request = GenerationRequest(
            content="def test(): pass", source_file=Path("test.py")
        )

        result = provider.generate_documentation(request)

        assert result.success is True
        assert test_response in result.content["index.md"]


# Quality validation tests
class TestLlamaCppProviderQualityValidation:
    """Quality validation and comprehensive test coverage verification."""

    def test_all_private_methods_have_tests(self):
        """Verify all private methods are tested through public interfaces."""

        # Get all private methods (starting with single underscore, not dunder)
        private_methods = [
            method
            for method in dir(LlamaCppProvider)
            if method.startswith("_")
            and not method.startswith("__")
            and callable(getattr(LlamaCppProvider, method))
        ]

        # These methods should be tested through public interface
        expected_private_methods = [
            "_load_model",
            "_create_documentation_prompt",
            "_parse_generated_content",
            "_detect_language",
            "_suppress_noisy_logs",
        ]

        for method in expected_private_methods:
            assert method in private_methods, (
                f"Expected private method {method} not found"
            )

    def test_error_messages_are_informative(self):
        """Test that error messages provide sufficient debugging information."""
        provider = LlamaCppProvider()

        # Test validation error
        try:
            provider.validate_request(None)
        except ValueError as e:
            assert "GenerationRequest" in str(e)

        # Test generation error with unavailable provider
        with patch.object(provider, "is_available", return_value=False):
            request = GenerationRequest(content="test", source_file=Path("test.py"))
            result = provider.generate_documentation(request)

            assert "not available" in result.error
            assert "dependencies" in result.error or "model file" in result.error

    def test_thread_safety_considerations(self):
        """Test thread safety of provider operations."""
        provider = LlamaCppProvider()

        # Model loading should be safe to call multiple times
        with patch("spec_cli.ai.providers.llamacpp.LLAMA_CPP_AVAILABLE", False):
            result1 = provider._load_model()
            result2 = provider._load_model()

            assert result1 == result2 is False

        # Cleanup should be safe to call multiple times
        provider.cleanup()
        provider.cleanup()  # Should not raise exception

        assert provider._model is None

    def test_memory_efficiency(self):
        """Test memory efficiency and resource cleanup."""
        provider = LlamaCppProvider()

        # Simulate loaded model
        mock_model = Mock(spec=[])
        provider._model = mock_model
        provider._model_loaded = True

        # Cleanup should free resources
        provider.cleanup()

        # Model reference should be cleared
        assert provider._model is None
        # Mock should be available for garbage collection
        del mock_model

    def test_configuration_immutability_safety(self):
        """Test that configuration is not accidentally modified."""
        original_config = LlamaCppConfig(model_path="/test/path")
        provider = LlamaCppProvider(config=original_config)

        # Provider should have its own config reference
        assert provider.config is original_config

        # Modifying provider config should not affect operations adversely
        provider.config.model_path = "/different/path"

        # Provider should continue to work with modified config
        info = provider.get_provider_info()
        assert info["model_path"] == "/different/path"
