"""Unit tests for AI Generation Provider - Content Generation (Slice ai_001).

Comprehensive unit tests for DocumentationGenerator.generate_documentation,
_create_documentation_prompt, and _validate_template_completion functions
with 85% coverage target.
"""

import os
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.config.settings import LocalModelConfig
from spec_cli.ai.providers.base import GenerationRequest
from spec_cli.ai.providers.generation import DocumentationGenerator


class TestDocumentationGeneratorInitialization:
    """Test DocumentationGenerator initialization and configuration."""

    def test_init_with_valid_config(self):
        """Test initialization with valid LocalModelConfig."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
        config.max_tokens = 512
        config.cache_enabled = True

        generator = DocumentationGenerator(config)

        assert generator.config == config
        assert generator.model is None
        assert generator.tokenizer is None
        assert generator.device is None
        assert generator._generation_count == 0

    def test_init_stores_config_reference(self):
        """Test that initialization stores reference to config object."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"

        generator = DocumentationGenerator(config)

        assert generator.config is config


class TestDocumentationGeneratorModelLoading:
    """Test DocumentationGenerator model loading functionality."""

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", False)
    def test_load_model_when_hf_not_available_then_returns_false(self):
        """Test load_model returns False when HuggingFace not available."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        result = generator.load_model("cpu")

        assert result is False

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.AutoTokenizer")
    @patch("spec_cli.ai.providers.generation.AutoModelForCausalLM")
    def test_load_model_success_cpu_device(
        self, mock_model_class, mock_tokenizer_class, mock_torch
    ):
        """Test successful model loading on CPU device."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"
        config.cache_enabled = True
        config.use_4bit = False

        mock_tokenizer = Mock()
        mock_model = Mock()
        mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
        mock_model_class.from_pretrained.return_value = mock_model

        generator = DocumentationGenerator(config)

        with patch.object(generator, "_get_cache_dir", return_value="/test/cache"):
            with patch.object(
                generator, "_get_model_kwargs", return_value={"torch_dtype": "float16"}
            ):
                result = generator.load_model("cpu")

        assert result is True
        assert generator.device == "cpu"
        assert generator.tokenizer == mock_tokenizer
        assert generator.model == mock_model

        # Verify tokenizer loading
        mock_tokenizer_class.from_pretrained.assert_called_once_with(
            "test-model", trust_remote_code=True, cache_dir="/test/cache"
        )

        # Verify model loading
        mock_model_class.from_pretrained.assert_called_once_with(
            "test-model",
            trust_remote_code=True,
            cache_dir="/test/cache",
            torch_dtype="float16",
        )

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.AutoTokenizer")
    @patch("spec_cli.ai.providers.generation.AutoModelForCausalLM")
    def test_load_model_optimizes_cpu_threading(
        self, mock_model_class, mock_tokenizer_class, mock_torch
    ):
        """Test CPU threading optimization for Apple Silicon."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"
        config.cache_enabled = False

        mock_torch.set_num_threads = Mock()
        mock_tokenizer_class.from_pretrained.return_value = Mock()
        mock_model_class.from_pretrained.return_value = Mock()

        generator = DocumentationGenerator(config)

        with patch("os.cpu_count", return_value=8):
            with patch.object(generator, "_get_model_kwargs", return_value={}):
                generator.load_model("cpu")

        # Verify threading optimization (min of 8 and 6 = 6)
        mock_torch.set_num_threads.assert_called_once_with(6)

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.generation.AutoTokenizer")
    def test_load_model_handles_tokenizer_exception(self, mock_tokenizer_class):
        """Test error handling when tokenizer loading fails."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "invalid-model"
        config.cache_enabled = False

        mock_tokenizer_class.from_pretrained.side_effect = Exception(
            "Tokenizer load failed"
        )

        generator = DocumentationGenerator(config)

        with patch.object(generator, "_get_cache_dir", return_value=None):
            result = generator.load_model("cpu")

        assert result is False
        assert generator.model is None
        assert generator.tokenizer is None

    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.generation.AutoTokenizer")
    @patch("spec_cli.ai.providers.generation.AutoModelForCausalLM")
    def test_load_model_handles_model_exception(
        self, mock_model_class, mock_tokenizer_class
    ):
        """Test error handling when model loading fails."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"

        mock_tokenizer_class.from_pretrained.return_value = Mock()
        mock_model_class.from_pretrained.side_effect = Exception("Model load failed")

        generator = DocumentationGenerator(config)

        with patch.object(generator, "_get_cache_dir", return_value=None):
            with patch.object(generator, "_get_model_kwargs", return_value={}):
                result = generator.load_model("cpu")

        assert result is False
        assert generator.model is None
        assert generator.tokenizer is None


class TestDocumentationGeneratorContentGeneration:
    """Test DocumentationGenerator content generation functionality."""

    def test_generate_documentation_when_model_not_loaded_then_returns_error(self):
        """Test generation fails when model not loaded."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/file.py")

        result = generator.generate_documentation(request)

        assert result.success is False
        assert "Model not loaded" in result.error
        assert result.content == {}

    def test_generate_documentation_success_with_template(self):
        """Test successful documentation generation with template."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"
        generator = DocumentationGenerator(config)

        # Mock loaded model state
        generator.model = Mock()
        generator.tokenizer = Mock()
        generator.device = "cpu"

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/file.py")
        request.content = "def test_function(): pass"
        request.template_content = "# {{filename}}\n{{purpose}}"

        with patch.object(
            generator, "_create_documentation_prompt", return_value="test prompt"
        ):
            with patch.object(
                generator,
                "_generate_with_model",
                return_value="# file.py\nTest function",
            ):
                with patch.object(
                    generator,
                    "_parse_generated_content",
                    return_value={"index.md": "content"},
                ):
                    with patch.object(
                        generator,
                        "_validate_template_completion",
                        return_value=(True, []),
                    ):
                        result = generator.generate_documentation(request)

        assert result.success is True
        assert result.content == {"index.md": "content"}
        assert result.metadata["provider"] == "local"
        assert result.metadata["model"] == "test-model"
        assert "processing_time_ms" in result.metadata

    def test_generate_documentation_with_template_validation_failure(self):
        """Test generation with template validation failure."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"
        generator = DocumentationGenerator(config)

        # Mock loaded model state
        generator.model = Mock()
        generator.tokenizer = Mock()
        generator.device = "cpu"

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/file.py")
        request.content = "def test_function(): pass"
        request.template_content = "# {{filename}}\n{{purpose}}"

        with patch.object(
            generator, "_create_documentation_prompt", return_value="test prompt"
        ):
            with patch.object(
                generator, "_generate_with_model", return_value="incomplete content"
            ):
                with patch.object(
                    generator,
                    "_parse_generated_content",
                    return_value={"index.md": "content"},
                ):
                    with patch.object(
                        generator,
                        "_validate_template_completion",
                        return_value=(False, ["purpose"]),
                    ):
                        result = generator.generate_documentation(request)

        assert result.success is True
        assert "template_validation_warnings" in result.metadata
        assert "purpose" in str(result.metadata["template_validation_warnings"])

    def test_generate_documentation_handles_generation_exception(self):
        """Test error handling during documentation generation."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        # Mock loaded model state
        generator.model = Mock()
        generator.tokenizer = Mock()

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/file.py")

        with patch.object(
            generator,
            "_create_documentation_prompt",
            side_effect=Exception("Generation failed"),
        ):
            result = generator.generate_documentation(request)

        assert result.success is False
        assert "Generation failed" in result.error
        assert "processing_time_ms" in result.metadata

    def test_generate_documentation_increments_count(self):
        """Test that generation count is incremented."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"
        generator = DocumentationGenerator(config)

        # Mock loaded model state
        generator.model = Mock()
        generator.tokenizer = Mock()
        generator.device = "cpu"

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/file.py")
        request.content = "def test_function(): pass"
        request.template_content = None

        with patch.object(
            generator, "_create_documentation_prompt", return_value="test prompt"
        ):
            with patch.object(
                generator, "_generate_with_model", return_value="generated content"
            ):
                with patch.object(
                    generator,
                    "_parse_generated_content",
                    return_value={"index.md": "content"},
                ):
                    generator.generate_documentation(request)

        assert generator._generation_count == 1

        # Generate again
        with patch.object(
            generator, "_create_documentation_prompt", return_value="test prompt"
        ):
            with patch.object(
                generator, "_generate_with_model", return_value="generated content"
            ):
                with patch.object(
                    generator,
                    "_parse_generated_content",
                    return_value={"index.md": "content"},
                ):
                    result = generator.generate_documentation(request)

        assert generator._generation_count == 2
        assert result.metadata["generation_count"] == 2


class TestDocumentationGeneratorPromptCreation:
    """Test DocumentationGenerator prompt creation functionality."""

    def test_create_documentation_prompt_with_template(self):
        """Test prompt creation with template content."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/file.py")
        request.content = "def hello(): print('Hello, World!')"
        request.template_content = (
            "# {{filename}}\n\n## Purpose\n{{purpose}}\n\n## Details\n{{details}}"
        )
        request.get_file_extension = Mock(return_value=".py")

        prompt = generator._create_documentation_prompt(request)

        assert "You are a technical documentation expert" in prompt
        assert "def hello(): print('Hello, World!')" in prompt
        assert "# {{filename}}" in prompt
        assert "{{purpose}}" in prompt
        assert "{{details}}" in prompt
        assert "COPY the template structure exactly" in prompt

    def test_create_documentation_prompt_with_long_content_truncation(self):
        """Test prompt creation truncates long content."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        # Create content longer than 14000 characters
        long_content = "def test(): pass\n" * 1000  # ~16000 chars

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/file.py")
        request.content = long_content
        request.template_content = "# {{filename}}\n{{purpose}}"
        request.get_file_extension = Mock(return_value=".py")

        prompt = generator._create_documentation_prompt(request)

        # Verify content was truncated to max_code_chars (14000)
        code_section = prompt.split("```python\n")[1].split("\n```")[0]
        assert len(code_section) <= 14000

    def test_create_documentation_prompt_without_template(self):
        """Test prompt creation without template (fallback)."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/example.py")
        request.content = "def example(): return 42"
        request.template_content = None
        request.get_file_extension = Mock(return_value=".py")

        with patch.object(generator, "_detect_language", return_value="python"):
            prompt = generator._create_documentation_prompt(request)

        assert "You are an expert technical writer" in prompt
        assert "def example(): return 42" in prompt
        assert "example.py" in prompt
        assert "## Purpose" in prompt
        assert "## Key Components" in prompt
        assert "## Dependencies" in prompt

    def test_create_documentation_prompt_with_empty_template(self):
        """Test prompt creation with empty template falls back to default."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/file.py")
        request.content = "def test(): pass"
        request.template_content = "   "  # Empty/whitespace template
        request.get_file_extension = Mock(return_value=".py")

        with patch.object(generator, "_detect_language", return_value="python"):
            prompt = generator._create_documentation_prompt(request)

        # Should use default prompt structure
        assert "You are an expert technical writer" in prompt
        assert "## Purpose" in prompt


class TestDocumentationGeneratorTemplateValidation:
    """Test DocumentationGenerator template validation functionality."""

    def test_validate_template_completion_all_placeholders_filled(self):
        """Test template validation when all placeholders are filled."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        template = (
            "# {{filename}}\n\n## Purpose\n{{purpose}}\n\n## Details\n{{details}}"
        )
        generated = "# example.py\n\n## Purpose\nThis is a test file\n\n## Details\nImplements test functionality"

        is_valid, missing = generator._validate_template_completion(template, generated)

        assert is_valid is True
        assert missing == []

    def test_validate_template_completion_missing_placeholders(self):
        """Test template validation when placeholders are missing."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        template = (
            "# {{filename}}\n\n## Purpose\n{{purpose}}\n\n## Details\n{{details}}"
        )
        generated = (
            "# example.py\n\n## Purpose\n{{purpose}}\n\n## Details\nSome details"
        )

        is_valid, missing = generator._validate_template_completion(template, generated)

        assert is_valid is False
        assert "purpose" in missing
        assert "details" not in missing
        assert len(missing) == 1

    def test_validate_template_completion_no_placeholders_in_template(self):
        """Test template validation with no placeholders in template."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        template = "# Static Template\n\nThis has no placeholders."
        generated = "# Static Template\n\nThis has no placeholders."

        is_valid, missing = generator._validate_template_completion(template, generated)

        assert is_valid is True
        assert missing == []

    def test_validate_template_completion_extra_placeholders_in_generated(self):
        """Test template validation ignores extra placeholders in generated content."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        template = "# {{filename}}"
        generated = "# example.py\n\nExtra content with {{unexpected}} placeholder"

        is_valid, missing = generator._validate_template_completion(template, generated)

        # Should be valid - we only care about original template placeholders
        assert is_valid is True
        assert missing == []


class TestDocumentationGeneratorUtilityMethods:
    """Test DocumentationGenerator utility methods."""

    def test_detect_language_python_extension(self):
        """Test language detection for Python files."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        language = generator._detect_language(".py")
        assert language == "python"

    def test_detect_language_javascript_extension(self):
        """Test language detection for JavaScript files."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        language = generator._detect_language(".js")
        assert language == "javascript"

    def test_detect_language_unknown_extension(self):
        """Test language detection for unknown extensions."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        language = generator._detect_language(".unknown")
        assert language == "text"

    def test_detect_language_case_insensitive(self):
        """Test language detection is case insensitive."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        language = generator._detect_language(".PY")
        assert language == "python"

    def test_get_field_description_exact_match(self):
        """Test field description for exact placeholder matches."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        description = generator._get_field_description("purpose")
        assert description == "Primary purpose or function of the code"

        description = generator._get_field_description("filename")
        assert description == "Source file name"

    def test_get_field_description_partial_match(self):
        """Test field description for partial placeholder matches."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        # Should match "examples" pattern
        description = generator._get_field_description("code_examples")
        assert "examples" in description.lower()

    def test_get_field_description_no_match(self):
        """Test field description for unknown placeholders."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        description = generator._get_field_description("unknown_placeholder")
        assert "Content for unknown placeholder" in description

    def test_get_cache_dir_when_disabled(self):
        """Test cache directory when caching is disabled."""
        config = Mock(spec=LocalModelConfig)
        config.cache_enabled = False
        generator = DocumentationGenerator(config)

        cache_dir = generator._get_cache_dir()
        assert cache_dir is None

    def test_get_cache_dir_with_custom_directory(self):
        """Test cache directory with custom configuration."""
        config = Mock(spec=LocalModelConfig)
        config.cache_enabled = True
        config.cache_dir = "/custom/cache/dir"
        generator = DocumentationGenerator(config)

        with patch(
            "spec_cli.ai.providers.generation.normalize_path_separators",
            return_value="/custom/cache/dir",
        ):
            cache_dir = generator._get_cache_dir()

        assert cache_dir == "/custom/cache/dir"

    def test_get_cache_dir_with_hf_home_env(self):
        """Test cache directory with HF_HOME environment variable."""
        config = Mock(spec=LocalModelConfig)
        config.cache_enabled = True
        generator = DocumentationGenerator(config)

        # Mock config without cache_dir attribute
        if hasattr(config, "cache_dir"):
            del config.cache_dir

        with patch.dict(os.environ, {"HF_HOME": "/env/hf/cache"}):
            with patch(
                "spec_cli.ai.providers.generation.normalize_path_separators",
                return_value="/env/hf/cache",
            ):
                cache_dir = generator._get_cache_dir()

        assert cache_dir == "/env/hf/cache"

    def test_get_cache_dir_default_unix(self):
        """Test default cache directory on Unix-like systems."""
        config = Mock(spec=LocalModelConfig)
        config.cache_enabled = True
        generator = DocumentationGenerator(config)

        # Mock config without cache_dir attribute
        if hasattr(config, "cache_dir"):
            del config.cache_dir

        with patch.dict(os.environ, {}, clear=True):  # Clear HF_HOME
            with patch("sys.platform", "linux"):
                with patch("os.path.expanduser", return_value="/home/user"):
                    cache_dir = generator._get_cache_dir()

        assert "/home/user/.cache/huggingface" in cache_dir

    def test_get_cache_dir_default_windows(self):
        """Test default cache directory on Windows."""
        config = Mock(spec=LocalModelConfig)
        config.cache_enabled = True
        generator = DocumentationGenerator(config)

        # Mock config without cache_dir attribute
        if hasattr(config, "cache_dir"):
            del config.cache_dir

        with patch.dict(os.environ, {}, clear=True):  # Clear HF_HOME
            with patch("sys.platform", "win32"):
                with patch("os.path.expanduser", return_value="C:\\Users\\user"):
                    with patch(
                        "spec_cli.ai.providers.generation.normalize_path_separators",
                        return_value="C:/Users/user/.cache/huggingface",
                    ):
                        cache_dir = generator._get_cache_dir()

        assert cache_dir == "C:/Users/user/.cache/huggingface"

    def test_cleanup_clears_model_references(self):
        """Test cleanup clears model and tokenizer references."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        # Set up loaded state
        generator.model = Mock()
        generator.tokenizer = Mock()

        generator.cleanup()

        assert generator.model is None
        assert generator.tokenizer is None

    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    def test_cleanup_clears_cuda_cache(self, mock_torch):
        """Test cleanup clears CUDA cache when available."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.empty_cache = Mock()

        generator.cleanup()

        mock_torch.cuda.empty_cache.assert_called_once()

    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    def test_cleanup_clears_mps_cache_when_available(self, mock_torch):
        """Test cleanup clears MPS cache on Apple Silicon."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.mps.empty_cache = Mock()

        with patch("sys.platform", "darwin"):
            generator.cleanup()

        mock_torch.mps.empty_cache.assert_called_once()

    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    def test_cleanup_handles_mps_cache_attribute_error(self, mock_torch):
        """Test cleanup handles MPS cache AttributeError gracefully."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.mps.empty_cache.side_effect = AttributeError("MPS not available")

        with patch("sys.platform", "darwin"):
            # Should not raise exception
            generator.cleanup()

        assert generator.model is None
        assert generator.tokenizer is None


class TestDocumentationGeneratorModelKwargs:
    """Test DocumentationGenerator model kwargs configuration."""

    def test_get_model_kwargs_cuda_device(self):
        """Test model kwargs for CUDA device."""
        config = Mock(spec=LocalModelConfig)
        config.use_4bit = False
        generator = DocumentationGenerator(config)

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            kwargs = generator._get_model_kwargs("cuda")

        assert kwargs["device_map"] == "auto"
        assert kwargs["torch_dtype"] == mock_torch.float16

    def test_get_model_kwargs_mps_device(self):
        """Test model kwargs for MPS device on macOS."""
        config = Mock(spec=LocalModelConfig)
        config.use_4bit = False
        generator = DocumentationGenerator(config)

        with patch("sys.platform", "darwin"):
            with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
                kwargs = generator._get_model_kwargs("mps")

        assert kwargs["device_map"] == {"": "mps"}
        assert kwargs["torch_dtype"] == mock_torch.float32

    def test_get_model_kwargs_cpu_device(self):
        """Test model kwargs for CPU device."""
        config = Mock(spec=LocalModelConfig)
        config.use_4bit = False
        generator = DocumentationGenerator(config)

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            kwargs = generator._get_model_kwargs("cpu")

        # CPU device should not have device_map
        assert "device_map" not in kwargs
        assert kwargs["torch_dtype"] == mock_torch.float16

    @patch("spec_cli.ai.providers.generation.BitsAndBytesConfig")
    def test_get_model_kwargs_4bit_quantization_cuda(self, mock_bnb_config):
        """Test model kwargs with 4-bit quantization on CUDA."""
        config = Mock(spec=LocalModelConfig)
        config.use_4bit = True
        generator = DocumentationGenerator(config)

        mock_bnb_config.return_value = "mock_quantization_config"

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            kwargs = generator._get_model_kwargs("cuda")

        assert kwargs["device_map"] == "auto"
        assert kwargs["quantization_config"] == "mock_quantization_config"

        # Verify BitsAndBytesConfig was called with correct parameters
        mock_bnb_config.assert_called_once_with(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=mock_torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4",
        )

    def test_get_model_kwargs_4bit_disabled_on_non_cuda(self):
        """Test that 4-bit quantization is disabled on non-CUDA devices."""
        config = Mock(spec=LocalModelConfig)
        config.use_4bit = True
        generator = DocumentationGenerator(config)

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            kwargs = generator._get_model_kwargs("cpu")

        # Should not have quantization_config for CPU
        assert "quantization_config" not in kwargs
        assert kwargs["torch_dtype"] == mock_torch.float16


class TestDocumentationGeneratorTextGeneration:
    """Test DocumentationGenerator text generation with model."""

    def test_generate_with_model_tokenizer_not_loaded(self):
        """Test _generate_with_model raises error when tokenizer not loaded."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        generator.tokenizer = None

        with pytest.raises(RuntimeError, match="Tokenizer not loaded"):
            generator._generate_with_model("test prompt")

    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    def test_generate_with_model_success_cpu(self, mock_torch):
        """Test successful text generation on CPU device."""
        config = Mock(spec=LocalModelConfig)
        config.max_tokens = 100
        generator = DocumentationGenerator(config)

        # Mock tokenizer
        mock_tokenizer = Mock()
        mock_inputs = {"input_ids": Mock(), "attention_mask": Mock()}
        mock_inputs["input_ids"].shape = [1, 50]  # Input length as tensor shape
        mock_tokenizer.return_value = mock_inputs
        mock_tokenizer.eos_token_id = 1
        generator.tokenizer = mock_tokenizer

        # Mock model with proper tensor simulation
        mock_model = Mock()

        # Create a mock tensor that supports slicing
        class MockTensor:
            def __init__(self):
                self.shape = [1, 100]  # Output length (input + generated)

            def __getitem__(self, slice_obj):
                # Return a mock for the sliced tensor
                return Mock()

        mock_output_tensor = MockTensor()
        mock_model.generate.return_value = [mock_output_tensor]
        generator.model = mock_model
        generator.device = "cpu"

        # Mock torch operations
        mock_torch.no_grad.return_value.__enter__ = Mock()
        mock_torch.no_grad.return_value.__exit__ = Mock()
        mock_tokenizer.decode.return_value = "Generated documentation content"

        result = generator._generate_with_model("Test prompt")

        assert result == "Generated documentation content"

        # Verify tokenizer was called
        mock_tokenizer.assert_called_once_with(
            "Test prompt",
            return_tensors="pt",
            truncation=True,
            max_length=16384,
        )

        # Verify model.generate was called
        mock_model.generate.assert_called_once()
        call_kwargs = mock_model.generate.call_args[1]
        assert call_kwargs["max_new_tokens"] == 100
        assert call_kwargs["do_sample"] is False
        assert call_kwargs["pad_token_id"] == 1
        assert call_kwargs["eos_token_id"] == 1
        assert call_kwargs["use_cache"] is True

    @patch("spec_cli.ai.providers.generation.torch")
    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    def test_generate_with_model_moves_inputs_to_device(self, mock_torch):
        """Test that inputs are moved to device when not CPU."""
        config = Mock(spec=LocalModelConfig)
        config.max_tokens = 50
        generator = DocumentationGenerator(config)

        # Mock tokenizer
        mock_tokenizer = Mock()
        mock_inputs = {"input_ids": Mock(), "attention_mask": Mock()}
        mock_inputs["input_ids"].shape = [1, 50]
        mock_inputs["input_ids"].to = Mock(return_value=mock_inputs["input_ids"])
        mock_inputs["attention_mask"].to = Mock(
            return_value=mock_inputs["attention_mask"]
        )
        mock_tokenizer.return_value = mock_inputs
        mock_tokenizer.eos_token_id = 1
        generator.tokenizer = mock_tokenizer

        # Mock model
        mock_model = Mock()

        # Create a mock tensor that supports slicing
        class MockTensor:
            def __init__(self):
                self.shape = [1, 80]

            def __getitem__(self, slice_obj):
                return Mock()

        mock_output_tensor = MockTensor()
        mock_model.generate.return_value = [mock_output_tensor]
        generator.model = mock_model
        generator.device = "cuda"

        # Mock torch operations
        mock_torch.no_grad.return_value.__enter__ = Mock()
        mock_torch.no_grad.return_value.__exit__ = Mock()
        mock_tokenizer.decode.return_value = "Generated content"

        generator._generate_with_model("Test prompt")

        # Verify inputs were moved to device
        mock_inputs["input_ids"].to.assert_called_once_with("cuda")
        mock_inputs["attention_mask"].to.assert_called_once_with("cuda")

    @patch("spec_cli.ai.providers.generation.torch", None)
    @patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True)
    def test_generate_with_model_torch_not_available(self):
        """Test _generate_with_model raises error when torch not available."""
        config = Mock(spec=LocalModelConfig)
        generator = DocumentationGenerator(config)

        # Mock tokenizer
        mock_tokenizer = Mock()
        mock_inputs = {"input_ids": Mock(), "attention_mask": Mock()}
        mock_tokenizer.return_value = mock_inputs
        generator.tokenizer = mock_tokenizer
        generator.model = Mock()
        generator.device = "cpu"

        with pytest.raises(RuntimeError, match="PyTorch not available"):
            generator._generate_with_model("Test prompt")


class TestDocumentationGeneratorParseContent:
    """Test DocumentationGenerator content parsing functionality."""

    def test_parse_generated_content_creates_index_and_history(self):
        """Test parsing creates both index.md and history.md files."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"
        generator = DocumentationGenerator(config)

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/project/src/example.py")

        with patch("sys.platform", "linux"):
            with patch("spec_cli.ai.providers.generation.datetime") as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "2025-01-01"
                result = generator._parse_generated_content(
                    "Generated documentation", request
                )

        assert "index.md" in result
        assert "history.md" in result
        assert result["index.md"] == "Generated documentation"

        history_content = result["history.md"]
        assert "Documentation History for example.py" in history_content
        assert "/project/src/example.py" in history_content
        assert "2025-01-01 - Initial Creation" in history_content
        assert "test-model" in history_content
        assert "linux" in history_content

    def test_parse_generated_content_handles_windows_path(self):
        """Test parsing handles Windows paths correctly."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"
        generator = DocumentationGenerator(config)

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("C:\\project\\src\\example.py")

        with patch(
            "spec_cli.ai.providers.generation.normalize_path_separators",
            return_value="C:/project/src/example.py",
        ):
            result = generator._parse_generated_content("Content", request)

        history_content = result["history.md"]
        assert "C:/project/src/example.py" in history_content

    def test_parse_generated_content_preserves_generated_text(self):
        """Test parsing preserves the generated text exactly."""
        config = Mock(spec=LocalModelConfig)
        config.model_name = "test-model"
        generator = DocumentationGenerator(config)

        request = Mock(spec=GenerationRequest)
        request.source_file = Path("/test/file.py")

        complex_content = """# Complex Documentation

## Multiple Sections
With various content types and formatting.

```python
def example():
    return "code block"
```

- List items
- More items

> Blockquote content
"""

        result = generator._parse_generated_content(complex_content, request)

        assert result["index.md"] == complex_content
