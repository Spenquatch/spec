"""Unit tests for Slice 4.1b: Embeddings generation with Qwen3-Emb-0.6B."""

from unittest.mock import Mock, patch

import numpy as np
import pytest

from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.context.embeddings import EmbeddingGenerator, generate_embeddings

# Test constants
TEST_TEXT = "This is a test document for embedding generation"
DEFAULT_MODEL_NAME = "Qwen/Qwen3-Emb-0.6B"
EXPECTED_EMBEDDING_DIMENSION = 768
MOCK_EMBEDDING_VECTOR = [0.1, 0.2, 0.3, 0.4, 0.5]
TEST_DEVICE_CPU = "cpu"
TEST_DEVICE_CUDA = "cuda"
TEST_DEVICE_MPS = "mps"


@pytest.fixture
def mock_ai_config():
    """Create mock AI configuration for testing."""
    config = Mock(spec=AIConfig)
    config.enabled = True
    return config


@pytest.fixture
def mock_ai_config_disabled():
    """Create mock AI configuration with embeddings disabled."""
    config = Mock(spec=AIConfig)
    config.enabled = False
    return config


@pytest.fixture
def mock_gpu_capabilities_cuda():
    """Mock GPU capabilities with CUDA available."""
    return {"cuda_available": True, "mps_available": False}


@pytest.fixture
def mock_gpu_capabilities_mps():
    """Mock GPU capabilities with MPS available."""
    return {"cuda_available": False, "mps_available": True}


@pytest.fixture
def mock_gpu_capabilities_cpu():
    """Mock GPU capabilities with only CPU available."""
    return {"cuda_available": False, "mps_available": False}


@pytest.fixture
def mock_tokenizer():
    """Mock transformers tokenizer."""
    tokenizer = Mock()
    tokenizer.return_value = {"input_ids": Mock(), "attention_mask": Mock()}
    return tokenizer


@pytest.fixture
def mock_model():
    """Mock transformers model."""
    model = Mock()
    model.to.return_value = model
    # Mock the forward pass output
    output = Mock()
    output.last_hidden_state = Mock()
    # Create a mock tensor that supports mean and squeeze operations
    mock_tensor = Mock()
    mock_tensor.mean.return_value.squeeze.return_value.cpu.return_value.numpy.return_value = np.array(
        MOCK_EMBEDDING_VECTOR
    )
    output.last_hidden_state = mock_tensor
    model.return_value = output
    return model


class TestEmbeddingGeneratorInitialization:
    """Test EmbeddingGenerator initialization and device selection."""

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_init_with_cuda_available_then_selects_cuda_device(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_cuda
    ):
        """Test initialization selects CUDA when available."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cuda

        generator = EmbeddingGenerator(mock_ai_config)

        assert generator.device == TEST_DEVICE_CUDA
        assert generator.model_name == DEFAULT_MODEL_NAME
        assert generator.model is None
        assert generator.tokenizer is None
        mock_get_gpu.assert_called_once()

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_init_with_mps_available_then_selects_mps_device(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_mps
    ):
        """Test initialization selects MPS when CUDA unavailable but MPS available."""
        mock_get_gpu.return_value = mock_gpu_capabilities_mps

        generator = EmbeddingGenerator(mock_ai_config)

        assert generator.device == TEST_DEVICE_MPS
        assert generator.model_name == DEFAULT_MODEL_NAME

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_init_with_cpu_only_then_selects_cpu_device(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_cpu
    ):
        """Test initialization selects CPU when no GPU available."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cpu

        generator = EmbeddingGenerator(mock_ai_config)

        assert generator.device == TEST_DEVICE_CPU


class TestEmbeddingGeneratorModelLoading:
    """Test model loading functionality."""

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_load_model_when_transformers_available_then_loads_successfully(
        self,
        mock_get_gpu,
        mock_ai_config,
        mock_gpu_capabilities_cpu,
        mock_tokenizer,
        mock_model,
    ):
        """Test successful model loading with transformers available."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cpu

        with (
            patch(
                "spec_cli.ai.context.embeddings.AutoTokenizer"
            ) as mock_auto_tokenizer,
            patch("spec_cli.ai.context.embeddings.AutoModel") as mock_auto_model,
        ):
            mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer
            mock_auto_model.from_pretrained.return_value = mock_model

            generator = EmbeddingGenerator(mock_ai_config)
            result = generator._load_model()

            assert result is True
            assert generator.tokenizer == mock_tokenizer
            assert generator.model == mock_model
            mock_auto_tokenizer.from_pretrained.assert_called_once_with(
                DEFAULT_MODEL_NAME
            )
            mock_auto_model.from_pretrained.assert_called_once()

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_load_model_when_transformers_missing_then_returns_false(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_cpu
    ):
        """Test model loading failure when transformers not available."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cpu

        with patch(
            "spec_cli.ai.context.embeddings.AutoTokenizer"
        ) as mock_auto_tokenizer:
            mock_auto_tokenizer.from_pretrained.side_effect = ImportError(
                "transformers not installed"
            )

            generator = EmbeddingGenerator(mock_ai_config)
            result = generator._load_model()

            assert result is False
            assert generator.model is None
            assert generator.tokenizer is None

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_load_model_when_gpu_device_then_uses_device_map(
        self,
        mock_get_gpu,
        mock_ai_config,
        mock_gpu_capabilities_cuda,
        mock_tokenizer,
        mock_model,
    ):
        """Test model loading with GPU device mapping."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cuda

        with (
            patch(
                "spec_cli.ai.context.embeddings.AutoTokenizer"
            ) as mock_auto_tokenizer,
            patch("spec_cli.ai.context.embeddings.AutoModel") as mock_auto_model,
        ):
            mock_auto_tokenizer.from_pretrained.return_value = mock_tokenizer
            mock_auto_model.from_pretrained.return_value = mock_model

            generator = EmbeddingGenerator(mock_ai_config)
            generator._load_model()

            # Verify device_map is used for non-CPU devices
            call_args = mock_auto_model.from_pretrained.call_args
            assert call_args[1]["device_map"] == TEST_DEVICE_CUDA


class TestEmbeddingGeneratorEmbeddingGeneration:
    """Test embedding generation functionality."""

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_generate_embeddings_when_ai_disabled_then_returns_error(
        self, mock_get_gpu, mock_ai_config_disabled, mock_gpu_capabilities_cpu
    ):
        """Test embedding generation with AI disabled returns error."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cpu

        generator = EmbeddingGenerator(mock_ai_config_disabled)
        result = generator.generate_embeddings(TEST_TEXT)

        assert result["success"] is False
        assert "AI embeddings disabled" in result["error"]

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_generate_embeddings_when_empty_text_then_returns_error(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_cpu
    ):
        """Test embedding generation with empty text returns error."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cpu

        generator = EmbeddingGenerator(mock_ai_config)
        result = generator.generate_embeddings("")

        assert result["success"] is False
        assert "Empty text provided" in result["error"]

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_generate_embeddings_when_model_load_fails_then_returns_error(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_cpu
    ):
        """Test embedding generation when model loading fails."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cpu

        generator = EmbeddingGenerator(mock_ai_config)
        # Mock _load_model to return False
        generator._load_model = Mock(return_value=False)

        result = generator.generate_embeddings(TEST_TEXT)

        assert result["success"] is False
        assert "Failed to load Qwen3-Emb-0.6B" in result["error"]

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_generate_embeddings_when_successful_then_returns_embeddings(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_cpu
    ):
        """Test successful embedding generation."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cpu

        generator = EmbeddingGenerator(mock_ai_config)

        # Mock the model loading and inference
        with patch("spec_cli.ai.context.embeddings.torch_module") as mock_torch:
            mock_torch.no_grad.return_value.__enter__ = Mock()
            mock_torch.no_grad.return_value.__exit__ = Mock()

            # Mock tokenizer and model
            generator.tokenizer = Mock()
            generator.model = Mock()

            # Mock tokenization output
            mock_inputs = {"input_ids": Mock(), "attention_mask": Mock()}
            generator.tokenizer.return_value = mock_inputs

            # Mock model output
            mock_outputs = Mock()
            mock_tensor = Mock()
            mock_tensor.mean.return_value.squeeze.return_value.cpu.return_value.numpy.return_value = np.array(
                MOCK_EMBEDDING_VECTOR
            )
            mock_outputs.last_hidden_state = mock_tensor
            generator.model.return_value = mock_outputs

            result = generator.generate_embeddings(TEST_TEXT)

            assert result["success"] is True
            assert result["data"]["embeddings"] == MOCK_EMBEDDING_VECTOR
            assert result["data"]["text_length"] == len(TEST_TEXT)
            assert result["data"]["device_used"] == TEST_DEVICE_CPU
            assert result["data"]["model_name"] == DEFAULT_MODEL_NAME
            assert "generation_time" in result["data"]
            assert "timestamp" in result["data"]

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_generate_embeddings_when_gpu_available_then_moves_inputs_to_device(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_cuda
    ):
        """Test embedding generation moves inputs to GPU when available."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cuda

        generator = EmbeddingGenerator(mock_ai_config)

        with patch("spec_cli.ai.context.embeddings.torch_module") as mock_torch:
            mock_torch.no_grad.return_value.__enter__ = Mock()
            mock_torch.no_grad.return_value.__exit__ = Mock()

            generator.tokenizer = Mock()
            generator.model = Mock()

            # Mock tokenization with tensors that have .to() method
            mock_tensor = Mock()
            mock_tensor.to.return_value = mock_tensor
            mock_inputs = {"input_ids": mock_tensor, "attention_mask": mock_tensor}
            generator.tokenizer.return_value = mock_inputs

            # Mock model output
            mock_outputs = Mock()
            mock_output_tensor = Mock()
            mock_output_tensor.mean.return_value.squeeze.return_value.cpu.return_value.numpy.return_value = np.array(
                MOCK_EMBEDDING_VECTOR
            )
            mock_outputs.last_hidden_state = mock_output_tensor
            generator.model.return_value = mock_outputs

            result = generator.generate_embeddings(TEST_TEXT)

            assert result["success"] is True
            # Verify tensors were moved to CUDA device
            mock_tensor.to.assert_called_with(TEST_DEVICE_CUDA)


class TestGenerateEmbeddingsConvenienceFunction:
    """Test the convenience function for embedding generation."""

    @patch("spec_cli.ai.context.embeddings.AIConfigLoader")
    @patch("spec_cli.ai.context.embeddings.EmbeddingGenerator")
    def test_generate_embeddings_function_when_no_config_provided_then_loads_default(
        self, mock_generator_class, mock_config_loader_class
    ):
        """Test convenience function loads default config when none provided."""
        mock_config_loader = Mock()
        mock_config = Mock()
        mock_config_loader.load_ai_config.return_value = mock_config
        mock_config_loader_class.return_value = mock_config_loader

        mock_generator = Mock()
        mock_result = {"success": True, "data": {"embeddings": MOCK_EMBEDDING_VECTOR}}
        mock_generator.generate_embeddings.return_value = mock_result
        mock_generator_class.return_value = mock_generator

        result = generate_embeddings(TEST_TEXT)

        assert result == mock_result
        mock_config_loader_class.assert_called_once()
        mock_config_loader.load_ai_config.assert_called_once()
        mock_generator_class.assert_called_once_with(mock_config)
        mock_generator.generate_embeddings.assert_called_once_with(TEST_TEXT)

    @patch("spec_cli.ai.context.embeddings.EmbeddingGenerator")
    def test_generate_embeddings_function_when_config_provided_then_uses_provided_config(
        self, mock_generator_class, mock_ai_config
    ):
        """Test convenience function uses provided config."""
        mock_generator = Mock()
        mock_result = {"success": True, "data": {"embeddings": MOCK_EMBEDDING_VECTOR}}
        mock_generator.generate_embeddings.return_value = mock_result
        mock_generator_class.return_value = mock_generator

        result = generate_embeddings(TEST_TEXT, mock_ai_config)

        assert result == mock_result
        mock_generator_class.assert_called_once_with(mock_ai_config)

    @patch("spec_cli.ai.context.embeddings.AIConfigLoader")
    def test_generate_embeddings_function_when_initialization_fails_then_returns_error(
        self, mock_config_loader_class
    ):
        """Test convenience function handles initialization failures."""
        mock_config_loader_class.side_effect = Exception("Config loading failed")

        result = generate_embeddings(TEST_TEXT)

        assert result["success"] is False
        assert "Failed to initialize embedding generation" in result["error"]


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility requirements."""

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_device_selection_handles_different_gpu_types_correctly(
        self, mock_get_gpu, mock_ai_config
    ):
        """Test device selection works across different GPU types."""
        # Test CUDA preference
        mock_get_gpu.return_value = {"cuda_available": True, "mps_available": True}
        generator = EmbeddingGenerator(mock_ai_config)
        assert generator.device == TEST_DEVICE_CUDA

        # Test MPS fallback
        mock_get_gpu.return_value = {"cuda_available": False, "mps_available": True}
        generator = EmbeddingGenerator(mock_ai_config)
        assert generator.device == TEST_DEVICE_MPS

        # Test CPU fallback
        mock_get_gpu.return_value = {"cuda_available": False, "mps_available": False}
        generator = EmbeddingGenerator(mock_ai_config)
        assert generator.device == TEST_DEVICE_CPU


class TestErrorHandling:
    """Test comprehensive error handling scenarios."""

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_generate_embeddings_when_exception_during_inference_then_handles_gracefully(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_cpu
    ):
        """Test embedding generation handles inference exceptions gracefully."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cpu

        generator = EmbeddingGenerator(mock_ai_config)
        generator.tokenizer = Mock()
        generator.model = Mock()

        # Mock exception during inference
        generator.tokenizer.side_effect = RuntimeError("CUDA out of memory")

        result = generator.generate_embeddings(TEST_TEXT)

        assert result["success"] is False
        assert "Embedding generation failed" in result["error"]
        assert "CUDA out of memory" in result["error"]

    @patch("spec_cli.ai.context.embeddings.get_gpu_capabilities")
    def test_model_loading_when_model_not_found_then_returns_false(
        self, mock_get_gpu, mock_ai_config, mock_gpu_capabilities_cpu
    ):
        """Test model loading handles model not found errors."""
        mock_get_gpu.return_value = mock_gpu_capabilities_cpu

        with patch(
            "spec_cli.ai.context.embeddings.AutoTokenizer"
        ) as mock_auto_tokenizer:
            mock_auto_tokenizer.from_pretrained.side_effect = OSError("Model not found")

            generator = EmbeddingGenerator(mock_ai_config)
            result = generator._load_model()

            assert result is False
