"""Unit tests for spec_cli.ai.providers.generation module."""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.config.settings import LocalModelConfig
from spec_cli.ai.providers.base import GenerationRequest
from spec_cli.ai.providers.generation import DocumentationGenerator

# Test constants
DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-Coder-0.5B"
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.3
TEST_DEVICE = "cpu"
TEST_CONTENT = "def hello():\n    return 'world'"
TEST_SOURCE_FILE = Path("/test/example.py")
NORMALIZED_TEST_PATH = "test/example.py"
TEST_CACHE_DIR = "/test/cache"
TEST_PROCESSING_TIME_MS = 150
TEST_GENERATION_COUNT = 1


class TestDocumentationGeneratorInitialization:
    """Test DocumentationGenerator initialization."""

    def test_init_with_config_creates_generator_with_defaults(self):
        """Test initialization with config creates generator with expected defaults."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        assert generator.config == config
        assert generator.model is None
        assert generator.tokenizer is None
        assert generator.device is None
        assert generator._generation_count == 0


class TestDocumentationGeneratorModelLoading:
    """Test DocumentationGenerator model loading functionality."""

    def test_load_model_when_successful_then_returns_true(self):
        """Test successful model loading returns True."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        mock_tokenizer = Mock()
        mock_model = Mock()

        with (
            patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True),
            patch(
                "spec_cli.ai.providers.generation.AutoTokenizer"
            ) as mock_tokenizer_class,
            patch(
                "spec_cli.ai.providers.generation.AutoModelForCausalLM"
            ) as mock_model_class,
            patch("spec_cli.ai.providers.generation.time.time", side_effect=[0.0, 2.5]),
        ):
            mock_tokenizer_class.from_pretrained.return_value = mock_tokenizer
            mock_model_class.from_pretrained.return_value = mock_model

            result = generator.load_model(TEST_DEVICE)

            assert result is True
            assert generator.device == TEST_DEVICE
            assert generator.tokenizer == mock_tokenizer
            assert generator.model == mock_model
            mock_tokenizer_class.from_pretrained.assert_called_once()
            mock_model_class.from_pretrained.assert_called_once()

    def test_load_model_when_hf_unavailable_then_returns_false(self):
        """Test model loading with HF unavailable returns False."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        with patch("spec_cli.ai.providers.generation.HF_AVAILABLE", False):
            result = generator.load_model(TEST_DEVICE)

        assert result is False
        assert generator.model is None
        assert generator.tokenizer is None

    def test_load_model_when_exception_occurs_then_returns_false(self):
        """Test model loading with exception returns False."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        with (
            patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True),
            patch(
                "spec_cli.ai.providers.generation.AutoTokenizer"
            ) as mock_tokenizer_class,
            patch("spec_cli.ai.providers.generation.AutoModelForCausalLM"),
        ):
            mock_tokenizer_class.from_pretrained.side_effect = Exception(
                "Model not found"
            )

            result = generator.load_model(TEST_DEVICE)

            assert result is False
            assert generator.model is None
            assert generator.tokenizer is None

    def test_load_model_when_cache_enabled_then_uses_cache_directory(self):
        """Test model loading with cache enabled uses cache directory."""
        config = LocalModelConfig(cache_enabled=True)
        generator = DocumentationGenerator(config)

        with (
            patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True),
            patch(
                "spec_cli.ai.providers.generation.AutoTokenizer"
            ) as mock_tokenizer_class,
            patch(
                "spec_cli.ai.providers.generation.AutoModelForCausalLM"
            ) as mock_model_class,
            patch.object(generator, "_get_cache_dir", return_value=TEST_CACHE_DIR),
        ):
            generator.load_model(TEST_DEVICE)

            tokenizer_call_args = mock_tokenizer_class.from_pretrained.call_args
            assert tokenizer_call_args.kwargs["cache_dir"] == TEST_CACHE_DIR

            model_call_args = mock_model_class.from_pretrained.call_args
            assert model_call_args.kwargs["cache_dir"] == TEST_CACHE_DIR


class TestDocumentationGeneratorGeneration:
    """Test DocumentationGenerator documentation generation."""

    def test_generate_documentation_when_model_not_loaded_then_returns_error_result(
        self,
    ):
        """Test generation without loaded model returns error result."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        result = generator.generate_documentation(request)

        assert result.success is False
        assert "Model not loaded" in result.error
        assert result.content == {}

    def test_generate_documentation_when_successful_then_returns_success_result(self):
        """Test successful documentation generation returns success result."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()
        generator.device = TEST_DEVICE

        test_prompt = "Test prompt"
        test_generated_text = "# Generated documentation"
        test_structured_content = {"index.md": test_generated_text}

        with (
            patch(
                "spec_cli.ai.providers.generation.normalize_path_separators",
                return_value=NORMALIZED_TEST_PATH,
            ),
            patch(
                "spec_cli.ai.providers.generation.time.time", side_effect=[0.0, 0.15]
            ),
            patch.object(
                generator, "_create_documentation_prompt", return_value=test_prompt
            ),
            patch.object(
                generator, "_generate_with_model", return_value=test_generated_text
            ),
            patch.object(
                generator,
                "_parse_generated_content",
                return_value=test_structured_content,
            ),
        ):
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            result = generator.generate_documentation(request)

        assert result.success is True
        assert result.content == test_structured_content
        assert result.metadata["provider"] == "local"
        assert result.metadata["model"] == config.model_name
        assert result.metadata["processing_time_ms"] == TEST_PROCESSING_TIME_MS
        assert result.metadata["generation_count"] == TEST_GENERATION_COUNT
        assert result.metadata["device"] == TEST_DEVICE
        assert result.metadata["platform"] == sys.platform
        assert result.metadata["source_file"] == NORMALIZED_TEST_PATH

    def test_generate_documentation_when_exception_occurs_then_returns_error_result(
        self,
    ):
        """Test generation with exception returns error result."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()

        # Provide enough time values for all time.time() calls including logging
        with (
            patch(
                "spec_cli.ai.providers.generation.time.time",
                side_effect=[0.0, 0.15, 0.16, 0.17],
            ),
            patch.object(
                generator,
                "_create_documentation_prompt",
                side_effect=Exception("Test error"),
            ),
        ):
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            result = generator.generate_documentation(request)

        assert result.success is False
        assert "Generation failed" in result.error
        assert "Test error" in result.error
        assert result.metadata["processing_time_ms"] == TEST_PROCESSING_TIME_MS

    def test_generate_documentation_when_called_then_increments_generation_count(self):
        """Test that generation count is incremented on each call."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()
        generator.device = TEST_DEVICE

        with (
            patch(
                "spec_cli.ai.providers.generation.normalize_path_separators",
                return_value=NORMALIZED_TEST_PATH,
            ),
            patch.object(generator, "_create_documentation_prompt"),
            patch.object(generator, "_generate_with_model"),
            patch.object(
                generator,
                "_parse_generated_content",
                return_value={"index.md": "content"},
            ),
            patch(
                "spec_cli.ai.providers.generation.time.time",
                side_effect=[0.0, 0.1, 0.2, 0.3],
            ),
        ):
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            # First generation
            result1 = generator.generate_documentation(request)
            assert result1.metadata["generation_count"] == 1

            # Second generation
            result2 = generator.generate_documentation(request)
            assert result2.metadata["generation_count"] == 2


class TestDocumentationGeneratorPromptCreation:
    """Test DocumentationGenerator prompt creation functionality."""

    def test_create_documentation_prompt_when_python_file_then_creates_correct_prompt(
        self,
    ):
        """Test prompt creation for Python file creates correct format."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        with patch(
            "spec_cli.ai.providers.generation.normalize_path_separators",
            return_value=NORMALIZED_TEST_PATH,
        ):
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            prompt = generator._create_documentation_prompt(request)

        assert "python" in prompt.lower()
        assert NORMALIZED_TEST_PATH in prompt
        assert TEST_CONTENT in prompt
        assert "## Purpose" in prompt
        assert "## Key Components" in prompt
        assert "## Dependencies" in prompt
        assert "## Usage Example" in prompt
        assert "## Technical Notes" in prompt

    def test_create_documentation_prompt_when_javascript_file_then_detects_language(
        self,
    ):
        """Test prompt creation detects JavaScript language correctly."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        with patch(
            "spec_cli.ai.providers.generation.normalize_path_separators",
            return_value="test/script.js",
        ):
            request = GenerationRequest(
                source_file=Path("/test/script.js"),
                content="function hello() { return 'world'; }",
            )

            prompt = generator._create_documentation_prompt(request)

        assert "javascript" in prompt.lower()
        assert "script.js" in prompt


class TestDocumentationGeneratorLanguageDetection:
    """Test DocumentationGenerator language detection functionality."""

    def test_detect_language_when_python_extension_then_returns_python(self):
        """Test language detection for Python files."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        language = generator._detect_language(".py")

        assert language == "python"

    def test_detect_language_when_javascript_extension_then_returns_javascript(self):
        """Test language detection for JavaScript files."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        language = generator._detect_language(".js")

        assert language == "javascript"

    def test_detect_language_when_unknown_extension_then_returns_text(self):
        """Test language detection for unknown extensions returns text."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        language = generator._detect_language(".unknown")

        assert language == "text"

    def test_detect_language_when_uppercase_extension_then_handles_correctly(self):
        """Test language detection handles uppercase extensions."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        language = generator._detect_language(".PY")

        assert language == "python"


class TestDocumentationGeneratorModelKwargs:
    """Test DocumentationGenerator model kwargs configuration."""

    def test_get_model_kwargs_when_specific_device_then_sets_device_map(self):
        """Test model kwargs configuration for specific device."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            mock_torch.float32 = "float32"

            kwargs = generator._get_model_kwargs("custom_device")

        assert kwargs["device_map"] == "custom_device"
        assert kwargs["torch_dtype"] == "float32"

    def test_get_model_kwargs_when_cuda_device_then_configures_cuda_settings(self):
        """Test model kwargs configuration for CUDA device."""
        config = LocalModelConfig(use_4bit=True)
        generator = DocumentationGenerator(config)

        with (
            patch(
                "spec_cli.ai.providers.generation.BitsAndBytesConfig"
            ) as mock_config_class,
            patch("spec_cli.ai.providers.generation.torch") as mock_torch,
        ):
            mock_config = Mock()
            mock_config.load_in_4bit = True
            mock_config_class.return_value = mock_config
            mock_torch.float16 = "float16"

            kwargs = generator._get_model_kwargs("cuda")

        assert kwargs["device_map"] == "auto"
        assert "quantization_config" in kwargs
        assert kwargs["quantization_config"] == mock_config

    def test_get_model_kwargs_when_mps_device_then_configures_mps_settings(self):
        """Test model kwargs configuration for MPS device."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        with (
            patch("spec_cli.ai.providers.generation.sys.platform", "darwin"),
            patch("spec_cli.ai.providers.generation.torch") as mock_torch,
        ):
            mock_torch.float32 = "float32"

            kwargs = generator._get_model_kwargs("mps")

        assert kwargs["device_map"] == {"": "mps"}
        assert kwargs["torch_dtype"] == "float32"

    def test_get_model_kwargs_when_cpu_device_then_configures_cpu_settings(self):
        """Test model kwargs configuration for CPU device."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            mock_torch.float32 = "float32"

            kwargs = generator._get_model_kwargs("cpu")

        # CPU should not have device_map
        assert "device_map" not in kwargs
        assert kwargs["torch_dtype"] == "float32"

    def test_get_model_kwargs_when_4bit_disabled_then_uses_dtype_only(self):
        """Test model kwargs when 4bit quantization is disabled."""
        config = LocalModelConfig(use_4bit=False)
        generator = DocumentationGenerator(config)

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            mock_torch.float16 = "float16"

            kwargs = generator._get_model_kwargs("cuda")

        assert "quantization_config" not in kwargs
        assert kwargs["torch_dtype"] == "float16"


class TestDocumentationGeneratorModelGeneration:
    """Test DocumentationGenerator model generation functionality."""

    def test_generate_with_model_when_torch_none_then_raises_runtime_error(self):
        """Test text generation raises RuntimeError when torch is None."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.device = "cpu"
        generator.tokenizer = Mock()
        generator.model = Mock()

        # Mock tokenizer behavior
        mock_tensor = Mock()
        mock_tensor.shape = [1, 10]
        mock_inputs = {"input_ids": mock_tensor}
        generator.tokenizer.return_value = mock_inputs
        generator.tokenizer.eos_token_id = 2

        with patch("spec_cli.ai.providers.generation.torch", None):
            with pytest.raises(RuntimeError, match="PyTorch not available"):
                generator._generate_with_model("test prompt")

    def test_generate_with_model_when_cpu_device_then_generates_correctly(self):
        """Test text generation on CPU device."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.device = "cpu"
        generator.tokenizer = Mock()
        generator.model = Mock()

        # Mock tokenizer behavior - create a proper mock tensor
        mock_tensor = Mock()
        mock_tensor.shape = [1, 10]  # input length = 10
        mock_inputs = {"input_ids": mock_tensor}
        generator.tokenizer.return_value = mock_inputs
        generator.tokenizer.eos_token_id = 2

        # Mock model generation - make it subscriptable
        mock_output_tokens = Mock()
        mock_output_tokens.__getitem__ = Mock(return_value=mock_tensor)
        mock_outputs = [mock_output_tokens]
        generator.model.generate.return_value = mock_outputs

        # Mock tokenizer decode
        generator.tokenizer.decode.return_value = "Generated documentation text"

        with patch("spec_cli.ai.providers.generation.torch") as mock_torch:
            test_prompt = "Generate documentation for this code"
            result = generator._generate_with_model(test_prompt)

        assert result == "Generated documentation text"
        generator.tokenizer.assert_called_once_with(
            test_prompt, return_tensors="pt", truncation=True, max_length=2048
        )
        mock_torch.no_grad.assert_called_once()

    def test_generate_with_model_when_gpu_device_then_moves_inputs_to_device(self):
        """Test text generation moves inputs to GPU device."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.device = "cuda"
        generator.tokenizer = Mock()
        generator.model = Mock()

        # Mock tokenizer behavior
        mock_tensor = Mock()
        mock_tensor.to.return_value = mock_tensor
        mock_tensor.shape = [1, 10]
        mock_inputs = {"input_ids": mock_tensor}
        generator.tokenizer.return_value = mock_inputs
        generator.tokenizer.eos_token_id = 2

        # Mock model generation - make it subscriptable
        mock_output_tokens = Mock()
        mock_output_tokens.__getitem__ = Mock(return_value=mock_tensor)
        mock_outputs = [mock_output_tokens]
        generator.model.generate.return_value = mock_outputs

        generator.tokenizer.decode.return_value = "Generated text"

        with patch("spec_cli.ai.providers.generation.torch"):
            generator._generate_with_model("test prompt")

        # Verify inputs were moved to device
        mock_tensor.to.assert_called_with("cuda")


class TestDocumentationGeneratorContentParsing:
    """Test DocumentationGenerator content parsing functionality."""

    def test_parse_generated_content_when_called_then_creates_structured_content(self):
        """Test parsing generated content creates structured documentation."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        with patch(
            "spec_cli.ai.providers.generation.normalize_path_separators",
            return_value=NORMALIZED_TEST_PATH,
        ):
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )
            generated_text = "# Generated Documentation\n\nThis is the content."

            result = generator._parse_generated_content(generated_text, request)

        assert "index.md" in result
        assert result["index.md"] == generated_text
        assert "history.md" in result
        assert "example.py" in result["history.md"]
        assert config.model_name in result["history.md"]
        assert sys.platform in result["history.md"]
        assert NORMALIZED_TEST_PATH in result["history.md"]


class TestDocumentationGeneratorCacheDirectory:
    """Test DocumentationGenerator cache directory functionality."""

    def test_get_cache_dir_when_cache_disabled_then_returns_none(self):
        """Test cache directory returns None when caching disabled."""
        config = LocalModelConfig(cache_enabled=False)
        generator = DocumentationGenerator(config)

        cache_dir = generator._get_cache_dir()

        assert cache_dir is None

    def test_get_cache_dir_when_custom_cache_dir_configured_then_returns_normalized_path(
        self,
    ):
        """Test cache directory returns normalized custom path when configured."""
        custom_cache = "/custom/cache/path"
        config = LocalModelConfig(cache_enabled=True, cache_dir=custom_cache)
        generator = DocumentationGenerator(config)

        with patch(
            "spec_cli.ai.providers.generation.normalize_path_separators",
            return_value="custom/cache/path",
        ):
            cache_dir = generator._get_cache_dir()

        assert cache_dir == "custom/cache/path"

    def test_get_cache_dir_when_hf_home_set_then_returns_env_cache(self):
        """Test cache directory uses HF_HOME environment variable when set."""
        config = LocalModelConfig(cache_enabled=True)
        generator = DocumentationGenerator(config)

        with (
            patch.dict(os.environ, {"HF_HOME": "/env/hf/cache"}),
            patch(
                "spec_cli.ai.providers.generation.normalize_path_separators",
                return_value="env/hf/cache",
            ),
        ):
            cache_dir = generator._get_cache_dir()

        assert cache_dir == "env/hf/cache"

    def test_get_cache_dir_when_windows_then_uses_windows_default(self):
        """Test cache directory uses Windows default path on Windows."""
        config = LocalModelConfig(cache_enabled=True)
        generator = DocumentationGenerator(config)

        with (
            patch("spec_cli.ai.providers.generation.sys.platform", "win32"),
            patch(
                "spec_cli.ai.providers.generation.os.path.expanduser",
                return_value="C:\\Users\\test",
            ),
            patch(
                "spec_cli.ai.providers.generation.normalize_path_separators",
                return_value="C:/Users/test/.cache/huggingface",
            ),
        ):
            cache_dir = generator._get_cache_dir()

        assert cache_dir == "C:/Users/test/.cache/huggingface"

    def test_get_cache_dir_when_unix_then_uses_unix_default(self):
        """Test cache directory uses Unix default path on Unix-like systems."""
        config = LocalModelConfig(cache_enabled=True)
        generator = DocumentationGenerator(config)

        with (
            patch("spec_cli.ai.providers.generation.sys.platform", "linux"),
            patch(
                "spec_cli.ai.providers.generation.os.path.expanduser",
                return_value="/home/test",
            ),
            patch(
                "spec_cli.ai.providers.generation.normalize_path_separators",
                return_value="/home/test/.cache/huggingface",
            ),
        ):
            cache_dir = generator._get_cache_dir()

        assert cache_dir == "/home/test/.cache/huggingface"

    def test_get_cache_dir_when_no_hf_home_then_uses_platform_default(self):
        """Test cache directory uses platform default when no HF_HOME set."""
        config = LocalModelConfig(cache_enabled=True)
        generator = DocumentationGenerator(config)

        # Clear HF_HOME and test platform-specific default
        with (
            patch.dict(os.environ, {}, clear=True),
            patch(
                "spec_cli.ai.providers.generation.os.path.expanduser",
                return_value="/home/user",
            ),
            patch(
                "spec_cli.ai.providers.generation.normalize_path_separators",
                return_value="/home/user/.cache/huggingface",
            ),
        ):
            cache_dir = generator._get_cache_dir()

        assert cache_dir == "/home/user/.cache/huggingface"


class TestDocumentationGeneratorCleanup:
    """Test DocumentationGenerator cleanup functionality."""

    def test_cleanup_when_cuda_available_then_clears_cuda_cache(self):
        """Test cleanup clears CUDA cache when available."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()

        with (
            patch("spec_cli.ai.providers.generation.torch") as mock_torch,
            patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True),
        ):
            mock_torch.cuda.is_available.return_value = True

            generator.cleanup()

        assert generator.model is None
        assert generator.tokenizer is None
        mock_torch.cuda.empty_cache.assert_called_once()

    def test_cleanup_when_mps_available_then_clears_mps_cache(self):
        """Test cleanup clears MPS cache when available on Darwin."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()

        with (
            patch("spec_cli.ai.providers.generation.torch") as mock_torch,
            patch("spec_cli.ai.providers.generation.sys.platform", "darwin"),
            patch("spec_cli.ai.providers.generation.HF_AVAILABLE", True),
        ):
            mock_torch.cuda.is_available.return_value = False
            mock_torch.backends.mps.is_available.return_value = True

            generator.cleanup()

        assert generator.model is None
        assert generator.tokenizer is None
        mock_torch.mps.empty_cache.assert_called_once()

    def test_cleanup_when_mps_empty_cache_missing_then_handles_gracefully(self):
        """Test cleanup handles missing MPS empty_cache gracefully."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()

        with (
            patch("spec_cli.ai.providers.generation.torch") as mock_torch,
            patch("spec_cli.ai.providers.generation.sys.platform", "darwin"),
        ):
            mock_torch.cuda.is_available.return_value = False
            mock_torch.backends.mps.is_available.return_value = True
            mock_torch.mps.empty_cache.side_effect = AttributeError(
                "empty_cache not available"
            )

            # Should not raise exception
            generator.cleanup()

        assert generator.model is None
        assert generator.tokenizer is None

    def test_cleanup_when_torch_none_then_handles_gracefully(self):
        """Test cleanup handles None torch gracefully."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()

        with patch("spec_cli.ai.providers.generation.torch", None):
            # Should not raise exception
            generator.cleanup()

        assert generator.model is None
        assert generator.tokenizer is None


class TestDocumentationGeneratorCrossPlatformPaths:
    """Test DocumentationGenerator cross-platform path handling."""

    def test_generate_documentation_when_windows_path_then_normalizes_consistently(
        self,
    ):
        """Test generation normalizes Windows paths consistently."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()
        generator.device = TEST_DEVICE

        windows_path = "C:\\test\\example.py"
        normalized_path = "C:/test/example.py"

        with (
            patch(
                "spec_cli.ai.providers.generation.normalize_path_separators",
                return_value=normalized_path,
            ),
            patch.object(generator, "_create_documentation_prompt"),
            patch.object(generator, "_generate_with_model"),
            patch.object(
                generator,
                "_parse_generated_content",
                return_value={"index.md": "content"},
            ),
            patch("spec_cli.ai.providers.generation.time.time", side_effect=[0.0, 0.1]),
        ):
            request = GenerationRequest(
                source_file=Path(windows_path), content=TEST_CONTENT
            )

            result = generator.generate_documentation(request)

        assert result.metadata["source_file"] == normalized_path

    def test_parse_generated_content_when_windows_path_then_normalizes_in_history(self):
        """Test content parsing normalizes Windows paths in history."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)

        windows_path = "C:\\test\\example.py"
        normalized_path = "C:/test/example.py"

        with patch(
            "spec_cli.ai.providers.generation.normalize_path_separators",
            return_value=normalized_path,
        ):
            request = GenerationRequest(
                source_file=Path(windows_path), content=TEST_CONTENT
            )

            result = generator._parse_generated_content("Generated content", request)

        assert normalized_path in result["history.md"]


class TestDocumentationGeneratorPerformanceMetrics:
    """Test DocumentationGenerator performance tracking."""

    def test_generate_documentation_when_called_then_tracks_processing_time(self):
        """Test generation tracks processing time accurately."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()
        generator.device = TEST_DEVICE

        # Mock time to simulate 250ms processing time
        with (
            patch(
                "spec_cli.ai.providers.generation.normalize_path_separators",
                return_value=NORMALIZED_TEST_PATH,
            ),
            patch(
                "spec_cli.ai.providers.generation.time.time",
                side_effect=[1000.0, 1000.25],
            ),
            patch.object(generator, "_create_documentation_prompt"),
            patch.object(generator, "_generate_with_model"),
            patch.object(
                generator,
                "_parse_generated_content",
                return_value={"index.md": "content"},
            ),
        ):
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            result = generator.generate_documentation(request)

        assert result.metadata["processing_time_ms"] == 250

    def test_generate_documentation_when_exception_then_still_tracks_time(self):
        """Test generation tracks time even when exception occurs."""
        config = LocalModelConfig()
        generator = DocumentationGenerator(config)
        generator.model = Mock()
        generator.tokenizer = Mock()

        # Mock time to simulate 100ms before exception (include extra values for logging)
        with (
            patch(
                "spec_cli.ai.providers.generation.time.time",
                side_effect=[2000.0, 2000.1, 2000.2, 2000.3],
            ),
            patch.object(
                generator,
                "_create_documentation_prompt",
                side_effect=Exception("Test error"),
            ),
        ):
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            result = generator.generate_documentation(request)

        assert result.success is False
        # Allow for small timing variations due to precision
        assert abs(result.metadata["processing_time_ms"] - 100) <= 1
