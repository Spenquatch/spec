"""Unit tests for AI generation provider - Slice ai_providers_002.

This module provides comprehensive unit tests for the DocumentationGenerator
class, testing all AI model operations, error scenarios, and edge cases
without external dependencies.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from spec_cli.ai.config.settings import LocalModelConfig
from spec_cli.ai.providers.base import GenerationRequest
from spec_cli.ai.providers.generation import DocumentationGenerator


class TestDocumentationGeneratorInitialization:
    """Test DocumentationGenerator initialization and configuration."""

    def test_init_with_valid_config(self):
        """Test successful initialization with valid LocalModelConfig."""
        config = LocalModelConfig(
            model_name="test/model",
            max_tokens=256,
            temperature=0.5,
            use_4bit=False,
            device="cpu",
        )

        generator = DocumentationGenerator(config)

        assert generator.config == config
        assert generator.model is None
        assert generator.tokenizer is None
        assert generator.device is None
        assert generator._generation_count == 0

    def test_init_preserves_config_values(self):
        """Test that initialization preserves all config values."""
        config = LocalModelConfig(
            model_name="custom/model-name",
            max_tokens=1024,
            temperature=0.7,
            use_4bit=True,
            device="cuda",
            cache_enabled=False,
        )

        generator = DocumentationGenerator(config)

        assert generator.config.model_name == "custom/model-name"
        assert generator.config.max_tokens == 1024
        assert generator.config.temperature == 0.7
        assert generator.config.use_4bit is True
        assert generator.config.device == "cuda"
        assert generator.config.cache_enabled is False


class TestDocumentationGeneratorModelLoading:
    """Test model loading functionality with various scenarios."""

    def setup_method(self):
        """Setup for each test method."""
        self.config = LocalModelConfig(
            model_name="test/model",
            max_tokens=256,
            device="cpu",
            use_4bit=False,  # Disable to avoid BitsAndBytesConfig issues
        )
        self.generator = DocumentationGenerator(self.config)

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.AutoTokenizer")
    @patch("spec_cli.ai.providers.generation.AutoModelForCausalLM")
    def test_load_model_success_cpu(
        self, mock_model_class, mock_tokenizer_class, mock_torch
    ):
        """Test successful model loading on CPU device."""
        # Setup mocks
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        mock_torch.set_num_threads = Mock()

        # Test loading
        result = self.generator.load_model("cpu")

        assert result is True
        assert self.generator.model == mock_model
        assert self.generator.tokenizer == mock_tokenizer
        assert self.generator.device == "cpu"

        # Verify CPU optimization was called
        mock_torch.set_num_threads.assert_called_once()

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.AutoTokenizer")
    @patch("spec_cli.ai.providers.generation.AutoModelForCausalLM")
    def test_load_model_success_cuda(
        self, mock_model_class, mock_tokenizer_class, mock_torch
    ):
        """Test successful model loading on CUDA device without quantization."""
        # Setup mocks
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        mock_torch.float16 = "float16_dtype"

        # Test loading
        result = self.generator.load_model("cuda")

        assert result is True
        assert self.generator.device == "cuda"

        # Verify model was loaded with CUDA configuration
        mock_model_class.from_pretrained.assert_called_once()

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", False)
    def test_load_model_failure_hf_not_available(self):
        """Test model loading failure when HuggingFace is not available."""
        result = self.generator.load_model("cpu")

        assert result is False
        assert self.generator.model is None
        assert self.generator.tokenizer is None

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.generation.AutoTokenizer")
    def test_load_model_failure_tokenizer_exception(self, mock_tokenizer_class):
        """Test model loading failure when tokenizer loading raises exception."""
        mock_tokenizer_class.from_pretrained.side_effect = Exception(
            "Tokenizer loading failed"
        )

        result = self.generator.load_model("cpu")

        assert result is False
        assert self.generator.model is None
        assert self.generator.tokenizer is None

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.generation.AutoTokenizer")
    @patch("spec_cli.ai.providers.generation.AutoModelForCausalLM")
    def test_load_model_failure_model_exception(
        self, mock_model_class, mock_tokenizer_class
    ):
        """Test model loading failure when model loading raises exception."""
        mock_tokenizer_class.from_pretrained.return_value = Mock()
        mock_model_class.from_pretrained.side_effect = Exception("Model loading failed")

        result = self.generator.load_model("cpu")

        assert result is False
        assert self.generator.model is None
        assert self.generator.tokenizer is None


class TestDocumentationGeneratorGeneration:
    """Test documentation generation functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.config = LocalModelConfig(
            model_name="test/model",
            max_tokens=256,
            device="cpu",
        )
        self.generator = DocumentationGenerator(self.config)

        # Setup mock model and tokenizer
        self.mock_model = Mock()
        self.mock_tokenizer = Mock()
        self.generator.model = self.mock_model
        self.generator.tokenizer = self.mock_tokenizer
        self.generator.device = "cpu"

    def test_generate_documentation_model_not_loaded(self):
        """Test generation failure when model is not loaded."""
        generator = DocumentationGenerator(
            self.config
        )  # Fresh generator without loaded model

        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
        )

        result = generator.generate_documentation(request)

        assert result.success is False
        assert "Model not loaded" in result.error
        assert result.content == {}

    def test_generate_documentation_success_without_template(self):
        """Test successful documentation generation without template."""
        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
        )

        # Mock the generation pipeline
        with (
            patch.object(self.generator, "_create_documentation_prompt") as mock_prompt,
            patch.object(self.generator, "_generate_with_model") as mock_generate,
            patch.object(self.generator, "_parse_generated_content") as mock_parse,
        ):
            mock_prompt.return_value = "test prompt"
            mock_generate.return_value = "generated content"
            mock_parse.return_value = {
                "index.md": "# Test Documentation",
                "history.md": "# History",
            }

            result = self.generator.generate_documentation(request)

            assert result.success is True
            assert "index.md" in result.content
            assert "history.md" in result.content
            assert result.metadata["provider"] == "local"
            assert result.metadata["model"] == "test/model"
            assert "processing_time_ms" in result.metadata

    def test_generate_documentation_success_with_template(self):
        """Test successful documentation generation with template."""
        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
            template_content="# {{filename}}\n\n{{purpose}}",
        )

        # Mock the generation pipeline
        with (
            patch.object(self.generator, "_create_documentation_prompt") as mock_prompt,
            patch.object(self.generator, "_generate_with_model") as mock_generate,
            patch.object(self.generator, "_parse_generated_content") as mock_parse,
            patch.object(
                self.generator, "_validate_template_completion"
            ) as mock_validate,
        ):
            mock_prompt.return_value = "test prompt"
            mock_generate.return_value = "# test.py\n\nTesting function"
            mock_parse.return_value = {
                "index.md": "# test.py\n\nTesting function",
                "history.md": "# History",
            }
            mock_validate.return_value = (True, [])

            result = self.generator.generate_documentation(request)

            assert result.success is True
            assert result.content["index.md"] == "# test.py\n\nTesting function"
            assert "template_validation_warnings" not in result.metadata

    def test_generate_documentation_template_validation_failure(self):
        """Test generation with template validation failure."""
        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
            template_content="# {{filename}}\n\n{{purpose}}",
        )

        # Mock the generation pipeline
        with (
            patch.object(self.generator, "_create_documentation_prompt") as mock_prompt,
            patch.object(self.generator, "_generate_with_model") as mock_generate,
            patch.object(self.generator, "_parse_generated_content") as mock_parse,
            patch.object(
                self.generator, "_validate_template_completion"
            ) as mock_validate,
        ):
            mock_prompt.return_value = "test prompt"
            mock_generate.return_value = "# test.py\n\n{{purpose}}"  # Unfilled template
            mock_parse.return_value = {
                "index.md": "# test.py\n\n{{purpose}}",
                "history.md": "# History",
            }
            mock_validate.return_value = (False, ["purpose"])

            result = self.generator.generate_documentation(request)

            assert result.success is True  # Still successful but with warnings
            assert "template_validation_warnings" in result.metadata
            assert "purpose" in result.metadata["template_validation_warnings"][0]

    def test_generate_documentation_generation_exception(self):
        """Test generation failure due to exception in generation process."""
        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
        )

        # Mock the generation to raise exception
        with patch.object(
            self.generator, "_create_documentation_prompt"
        ) as mock_prompt:
            mock_prompt.side_effect = Exception("Generation failed")

            result = self.generator.generate_documentation(request)

            assert result.success is False
            assert "Generation failed" in result.error
            assert "processing_time_ms" in result.metadata


class TestDocumentationGeneratorPromptCreation:
    """Test prompt creation functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.config = LocalModelConfig(model_name="test/model")
        self.generator = DocumentationGenerator(self.config)

    def test_create_documentation_prompt_without_template(self):
        """Test prompt creation without template."""
        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
        )

        prompt = self.generator._create_documentation_prompt(request)

        assert "test.py" in prompt
        assert "python" in prompt
        assert "def hello(): pass" in prompt
        assert "You are an expert technical writer" in prompt

    def test_create_documentation_prompt_with_template(self):
        """Test prompt creation with template."""
        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
            template_content="# {{filename}}\n\n{{purpose}}",
        )

        prompt = self.generator._create_documentation_prompt(request)

        assert "{{filename}}" in prompt
        assert "{{purpose}}" in prompt
        assert "def hello(): pass" in prompt
        assert "COPY the template structure exactly" in prompt

    def test_create_documentation_prompt_large_content(self):
        """Test prompt creation with large content that needs truncation."""
        large_content = "def function():\n    pass\n" * 1000  # Large content
        request = GenerationRequest(
            source_file=Path("test.py"),
            content=large_content,
            template_content="# {{filename}}\n\n{{purpose}}",
        )

        prompt = self.generator._create_documentation_prompt(request)

        # Content should be truncated but template should be preserved
        assert "{{filename}}" in prompt
        assert "{{purpose}}" in prompt
        assert (
            len(prompt) < len(large_content) + 1000
        )  # Should be significantly smaller


class TestDocumentationGeneratorModelGeneration:
    """Test actual model generation functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.config = LocalModelConfig(model_name="test/model", max_tokens=256)
        self.generator = DocumentationGenerator(self.config)

        # Setup mock model and tokenizer
        self.mock_model = Mock()
        self.mock_tokenizer = Mock()
        self.generator.model = self.mock_model
        self.generator.tokenizer = self.mock_tokenizer
        self.generator.device = "cpu"

    @patch("spec_cli.ai.providers.generation.torch")
    def test_generate_with_model_success(self, mock_torch):
        """Test successful text generation with model."""
        # Setup tokenizer mock with proper tensor-like behavior
        mock_input_tensor = MagicMock()
        mock_input_tensor.shape = [1, 10]  # Mock input shape
        mock_inputs = {"input_ids": mock_input_tensor}
        self.mock_tokenizer.return_value = mock_inputs
        self.mock_tokenizer.eos_token_id = 2

        # Setup model mock with proper tensor-like output
        mock_output_tensor = MagicMock()
        mock_output_tensor.shape = [1, 20]  # Mock output shape (input + generated)
        mock_output_tensor.__getitem__ = Mock(return_value="generated_tokens")
        mock_outputs = [mock_output_tensor]
        self.mock_model.generate.return_value = mock_outputs

        # Setup decode mock
        self.mock_tokenizer.decode.return_value = "Generated documentation text"

        # Mock torch context manager
        mock_torch.no_grad.return_value.__enter__ = Mock()
        mock_torch.no_grad.return_value.__exit__ = Mock()

        result = self.generator._generate_with_model("test prompt")

        assert result == "Generated documentation text"
        self.mock_model.generate.assert_called_once()
        self.mock_tokenizer.decode.assert_called_once()

    def test_generate_with_model_tokenizer_not_loaded(self):
        """Test generation failure when tokenizer is not loaded."""
        self.generator.tokenizer = None

        with pytest.raises(RuntimeError, match="Tokenizer not loaded"):
            self.generator._generate_with_model("test prompt")

    @patch("spec_cli.ai.providers.generation.torch", None)
    def test_generate_with_model_torch_not_available(self):
        """Test generation failure when PyTorch is not available."""
        # Setup tokenizer mock
        mock_inputs = {"input_ids": Mock()}
        self.mock_tokenizer.return_value = mock_inputs

        with pytest.raises(RuntimeError, match="PyTorch not available"):
            self.generator._generate_with_model("test prompt")


class TestDocumentationGeneratorUtilityMethods:
    """Test utility and helper methods."""

    def setup_method(self):
        """Setup for each test method."""
        self.config = LocalModelConfig(model_name="test/model", use_4bit=False)
        self.generator = DocumentationGenerator(self.config)

    def test_detect_language_python(self):
        """Test language detection for Python files."""
        result = self.generator._detect_language(".py")
        assert result == "python"

    def test_detect_language_javascript(self):
        """Test language detection for JavaScript files."""
        result = self.generator._detect_language(".js")
        assert result == "javascript"

    def test_detect_language_unknown(self):
        """Test language detection for unknown file extensions."""
        result = self.generator._detect_language(".xyz")
        assert result == "text"

    def test_get_field_description_known_field(self):
        """Test field description for known template fields."""
        result = self.generator._get_field_description("purpose")
        assert "purpose" in result.lower()

    def test_get_field_description_unknown_field(self):
        """Test field description for unknown template fields."""
        result = self.generator._get_field_description("custom_field")
        assert "custom field" in result.lower()

    def test_validate_template_completion_success(self):
        """Test template validation when all placeholders are filled."""
        template = "# {{filename}}\n\n{{purpose}}"
        generated = "# test.py\n\nTesting function"

        is_valid, missing = self.generator._validate_template_completion(
            template, generated
        )

        assert is_valid is True
        assert missing == []

    def test_validate_template_completion_failure(self):
        """Test template validation when placeholders remain unfilled."""
        template = "# {{filename}}\n\n{{purpose}}"
        generated = "# test.py\n\n{{purpose}}"  # Purpose not filled

        is_valid, missing = self.generator._validate_template_completion(
            template, generated
        )

        assert is_valid is False
        assert "purpose" in missing

    def test_parse_generated_content(self):
        """Test parsing of generated content into structured format."""
        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
        )

        result = self.generator._parse_generated_content("Generated content", request)

        assert "index.md" in result
        assert "history.md" in result
        assert result["index.md"] == "Generated content"
        assert "test.py" in result["history.md"]

    @patch("spec_cli.ai.providers.generation.sys.platform", "darwin")
    def test_get_model_kwargs_mps_device(self):
        """Test model kwargs generation for MPS device on macOS."""
        kwargs = self.generator._get_model_kwargs("mps")

        assert "device_map" in kwargs
        assert kwargs["device_map"] == {"": "mps"}

    def test_get_model_kwargs_cuda_device_no_quantization(self):
        """Test model kwargs generation for CUDA device without quantization."""
        # Disable quantization to avoid BitsAndBytesConfig dependency
        self.config.use_4bit = False

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            mock_torch.float16 = "float16_dtype"

            kwargs = self.generator._get_model_kwargs("cuda")

            assert "device_map" in kwargs
            assert kwargs["device_map"] == "auto"
            assert "torch_dtype" in kwargs

    @patch("spec_cli.ai.providers.generation.torch")
    def test_get_model_kwargs_cpu_device(self, mock_torch):
        """Test model kwargs generation for CPU device."""
        mock_torch.float16 = "float16"

        kwargs = self.generator._get_model_kwargs("cpu")

        assert "torch_dtype" in kwargs
        assert kwargs["torch_dtype"] == "float16"

    def test_get_cache_dir_disabled(self):
        """Test cache directory when caching is disabled."""
        self.config.cache_enabled = False

        result = self.generator._get_cache_dir()

        assert result is None

    @patch.dict(os.environ, {"HF_HOME": "/custom/cache"})
    def test_get_cache_dir_from_environment(self):
        """Test cache directory from environment variable."""
        result = self.generator._get_cache_dir()

        assert "/custom/cache" in result

    def test_cleanup_resources(self):
        """Test cleanup of model resources."""
        # Setup some mock resources
        self.generator.model = Mock()
        self.generator.tokenizer = Mock()

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            mock_torch.backends.mps.is_available.return_value = False

            self.generator.cleanup()

            assert self.generator.model is None
            assert self.generator.tokenizer is None

    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.sys.platform", "darwin")
    def test_cleanup_with_mps_cache(self, mock_torch):
        """Test cleanup with MPS cache clearing on macOS."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.mps.empty_cache = Mock()

        self.generator.cleanup()

        mock_torch.mps.empty_cache.assert_called_once()


class TestDocumentationGeneratorEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Setup for each test method."""
        self.config = LocalModelConfig(model_name="test/model")
        self.generator = DocumentationGenerator(self.config)

    def test_generate_documentation_empty_content(self):
        """Test generation with empty content."""
        with pytest.raises(ValueError, match="content cannot be empty"):
            GenerationRequest(
                source_file=Path("test.py"),
                content="",
            )

    def test_generate_documentation_unicode_content(self):
        """Test generation with Unicode content."""
        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def функция(): return '测试'",
        )

        prompt = self.generator._create_documentation_prompt(request)

        assert "функция" in prompt
        assert "测试" in prompt

    def test_language_detection_case_insensitive(self):
        """Test language detection is case insensitive."""
        result_lower = self.generator._detect_language(".py")
        result_upper = self.generator._detect_language(".PY")

        assert result_lower == result_upper == "python"

    def test_field_description_partial_matching(self):
        """Test field description with partial matching."""
        result = self.generator._get_field_description("example_usage")

        assert "example" in result.lower() or "usage" in result.lower()

    def test_validate_template_completion_no_placeholders(self):
        """Test template validation with no placeholders."""
        template = "# Static Content"
        generated = "# Static Content"

        is_valid, missing = self.generator._validate_template_completion(
            template, generated
        )

        assert is_valid is True
        assert missing == []

    def test_parse_generated_content_includes_metadata(self):
        """Test that parsed content includes proper metadata."""
        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
        )

        result = self.generator._parse_generated_content("Generated content", request)

        assert "history.md" in result
        history_content = result["history.md"]
        assert self.config.model_name in history_content
        assert (
            str(request.source_file) in history_content or "test.py" in history_content
        )


class TestDocumentationGeneratorPerformance:
    """Test performance-related functionality."""

    def setup_method(self):
        """Setup for each test method."""
        self.config = LocalModelConfig(model_name="test/model")
        self.generator = DocumentationGenerator(self.config)

    def test_generation_count_tracking(self):
        """Test that generation count is properly tracked."""
        # Setup minimal mocks
        self.generator.model = Mock()
        self.generator.tokenizer = Mock()
        self.generator.device = "cpu"

        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
        )

        initial_count = self.generator._generation_count

        with (
            patch.object(self.generator, "_create_documentation_prompt") as mock_prompt,
            patch.object(self.generator, "_generate_with_model") as mock_generate,
            patch.object(self.generator, "_parse_generated_content") as mock_parse,
        ):
            mock_prompt.return_value = "test prompt"
            mock_generate.return_value = "generated content"
            mock_parse.return_value = {"index.md": "content", "history.md": "history"}

            result = self.generator.generate_documentation(request)

            assert self.generator._generation_count == initial_count + 1
            assert result.metadata["generation_count"] == initial_count + 1

    def test_processing_time_measurement(self):
        """Test that processing time is measured and included in metadata."""
        # Setup minimal mocks
        self.generator.model = Mock()
        self.generator.tokenizer = Mock()
        self.generator.device = "cpu"

        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
        )

        with (
            patch.object(self.generator, "_create_documentation_prompt") as mock_prompt,
            patch.object(self.generator, "_generate_with_model") as mock_generate,
            patch.object(self.generator, "_parse_generated_content") as mock_parse,
        ):
            mock_prompt.return_value = "test prompt"
            mock_generate.return_value = "generated content"
            mock_parse.return_value = {"index.md": "content", "history.md": "history"}

            result = self.generator.generate_documentation(request)

            assert "processing_time_ms" in result.metadata
            assert isinstance(result.metadata["processing_time_ms"], int)
            assert result.metadata["processing_time_ms"] >= 0


class TestDocumentationGeneratorIntegration:
    """Integration tests combining multiple components."""

    def setup_method(self):
        """Setup for each test method."""
        self.config = LocalModelConfig(model_name="test/model", use_4bit=False)
        self.generator = DocumentationGenerator(self.config)

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.AutoTokenizer")
    @patch("spec_cli.ai.providers.generation.AutoModelForCausalLM")
    def test_full_workflow_success(
        self, mock_model_class, mock_tokenizer_class, mock_torch
    ):
        """Test complete workflow from model loading to documentation generation."""
        # Setup model loading mocks
        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model
        mock_torch.set_num_threads = Mock()

        # Setup generation mocks with proper tensor-like behavior
        mock_input_tensor = MagicMock()
        mock_input_tensor.shape = [1, 10]
        mock_inputs = {"input_ids": mock_input_tensor}
        mock_tokenizer.return_value = mock_inputs
        mock_tokenizer.eos_token_id = 2

        mock_output_tensor = MagicMock()
        mock_output_tensor.shape = [1, 20]
        mock_output_tensor.__getitem__ = Mock(return_value="generated_tokens")
        mock_outputs = [mock_output_tensor]
        mock_model.generate.return_value = mock_outputs
        mock_tokenizer.decode.return_value = "Generated documentation"

        mock_torch.no_grad.return_value.__enter__ = Mock()
        mock_torch.no_grad.return_value.__exit__ = Mock()

        # Test complete workflow
        load_result = self.generator.load_model("cpu")
        assert load_result is True

        request = GenerationRequest(
            source_file=Path("test.py"),
            content="def hello(): pass",
        )

        result = self.generator.generate_documentation(request)

        assert result.success is True
        assert "index.md" in result.content
        assert "history.md" in result.content
        assert result.metadata["provider"] == "local"
