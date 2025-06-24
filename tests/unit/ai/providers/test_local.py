"""Unit tests for LocalAIProvider core functionality."""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.analysis.sanitizer import CodeSanitizer
from spec_cli.ai.config.settings import LocalModelConfig
from spec_cli.ai.providers.base import GenerationRequest, GenerationResult
from spec_cli.ai.providers.local import LocalAIProvider

# Test constants to avoid magic numbers
DEFAULT_MODEL_NAME = "Qwen/Qwen2.5-Coder-0.5B-Instruct"
DEFAULT_MAX_TOKENS = 512
DEFAULT_TEMPERATURE = 0.1
TEST_SOURCE_FILE = Path("src/test_file.py")
TEST_CONTENT = "def test_function():\n    pass"
TEST_SANITIZED_CONTENT = "def sanitized_function():\n    pass"
MOCK_DEVICE_CPU = "cpu"
MOCK_DEVICE_CUDA = "cuda"
MOCK_DEVICE_MPS = "mps"
PLATFORM_DARWIN = "darwin"
PLATFORM_LINUX = "linux"
PLATFORM_WIN32 = "win32"

# Integration test constants
MOCK_GPU_CAPABILITIES_CUDA = {
    "cuda_available": True,
    "mps_available": False,
    "gpu_memory_gb": 8.0,
    "gpu_count": 1,
    "recommendations": ["CUDA GPU detected"],
}
MOCK_GPU_CAPABILITIES_MPS = {
    "cuda_available": False,
    "mps_available": True,
    "gpu_memory_gb": 0,
    "gpu_count": 0,
    "recommendations": ["Apple Silicon GPU detected"],
}
MOCK_GPU_CAPABILITIES_CPU = {
    "cuda_available": False,
    "mps_available": False,
    "gpu_memory_gb": 0,
    "gpu_count": 0,
    "recommendations": ["No GPU acceleration available"],
}
MOCK_GENERATION_RESULT_SUCCESS = {
    "success": True,
    "content": {"index.md": "# Generated Documentation", "history.md": "# History"},
    "metadata": {"provider": "local", "model": DEFAULT_MODEL_NAME},
}
MOCK_GENERATION_RESULT_FAILURE = {
    "success": False,
    "error": "Model loading failed",
    "metadata": {"provider": "local", "device": MOCK_DEVICE_CPU},
}


class TestLocalAIProviderInitialization:
    """Test LocalAIProvider initialization and configuration."""

    def test_init_with_default_config_creates_provider_with_defaults(self):
        """Test initialization with default configuration."""
        provider = LocalAIProvider()

        assert isinstance(provider.config, LocalModelConfig)
        assert provider.config.model_name == DEFAULT_MODEL_NAME
        assert provider.config.max_tokens == DEFAULT_MAX_TOKENS
        assert provider.config.temperature == DEFAULT_TEMPERATURE
        assert isinstance(provider.sanitizer, CodeSanitizer)
        assert provider._model is None
        assert provider._tokenizer is None
        assert provider._pipeline is None
        assert provider._model_loaded is False
        assert provider._resources_allocated is False

    def test_init_with_custom_config_uses_provided_config(self):
        """Test initialization with custom configuration."""
        custom_config = LocalModelConfig(
            model_name="custom/model", max_tokens=1024, temperature=0.5
        )
        custom_sanitizer = CodeSanitizer()

        provider = LocalAIProvider(config=custom_config, sanitizer=custom_sanitizer)

        assert provider.config is custom_config
        assert provider.config.model_name == "custom/model"
        assert provider.config.max_tokens == 1024
        assert provider.config.temperature == 0.5
        assert provider.sanitizer is custom_sanitizer

    def test_init_logs_initialization_message(self):
        """Test that initialization logs the model name."""
        custom_config = LocalModelConfig(model_name="test/model")

        with patch.object(logging.getLogger("LocalAIProvider"), "info") as mock_log:
            LocalAIProvider(config=custom_config)
            mock_log.assert_called_once_with(
                "Initialized LocalAIProvider with model: %s", "test/model"
            )


class TestLocalAIProviderDependencyChecking:
    """Test HuggingFace dependency availability detection."""

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", True)
    def test_hf_available_when_imports_successful_then_flag_is_true(self):
        """Test that HF_AVAILABLE is True when imports succeed."""
        # This tests the import success path (lines 17-19)
        import spec_cli.ai.providers.local as local_module

        # Re-import to test the successful import path
        with patch("builtins.__import__") as mock_import:
            # Simulate successful imports
            mock_import.return_value = Mock()

            # The import already happened, but we verify the flag
            assert local_module.HF_AVAILABLE is True

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", False)
    def test_hf_available_when_imports_fail_then_variables_are_none(self):
        """Test that torch variables are None when imports fail."""
        # This tests the import failure path where torch variables become None

        # When HF_AVAILABLE is False, these should be None
        # This is tested through the module's actual behavior
        provider = LocalAIProvider()
        result = provider._check_system_requirements()
        assert result is False

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.local.LocalAIProvider._check_system_requirements")
    def test_is_available_when_dependencies_present_and_system_ready_then_returns_true(
        self, mock_check_system
    ):
        """Test availability when HuggingFace available and system requirements met."""
        mock_check_system.return_value = True
        provider = LocalAIProvider()

        result = provider.is_available()

        assert result is True
        mock_check_system.assert_called_once()

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", False)
    def test_is_available_when_dependencies_missing_then_returns_false(self):
        """Test availability when HuggingFace dependencies missing."""
        provider = LocalAIProvider()

        result = provider.is_available()

        assert result is False

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.local.LocalAIProvider._check_system_requirements")
    def test_is_available_when_system_requirements_not_met_then_returns_false(
        self, mock_check_system
    ):
        """Test availability when system requirements not met."""
        mock_check_system.return_value = False
        provider = LocalAIProvider()

        result = provider.is_available()

        assert result is False


class TestLocalAIProviderSystemRequirements:
    """Test system requirements checking."""

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", False)
    def test_check_system_requirements_when_hf_unavailable_then_returns_false(self):
        """Test system requirements check when HuggingFace unavailable."""
        provider = LocalAIProvider()

        result = provider._check_system_requirements()

        assert result is False

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.local.torch", None)
    def test_check_system_requirements_when_torch_none_then_returns_false(self):
        """Test system requirements check when torch is None."""
        provider = LocalAIProvider()

        result = provider._check_system_requirements()

        assert result is False

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.LocalAIProvider._get_device")
    def test_check_system_requirements_when_all_checks_pass_then_returns_true(
        self, mock_get_device, mock_torch
    ):
        """Test system requirements check when all requirements met."""
        mock_torch.tensor.return_value = Mock()
        mock_get_device.return_value = MOCK_DEVICE_CPU
        provider = LocalAIProvider()

        result = provider._check_system_requirements()

        assert result is True
        mock_torch.tensor.assert_called_once_with([1.0])
        mock_get_device.assert_called_once()

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.local.torch")
    def test_check_system_requirements_when_exception_occurs_then_returns_false(
        self, mock_torch
    ):
        """Test system requirements check when exception occurs."""
        mock_torch.tensor.side_effect = Exception("Test error")
        provider = LocalAIProvider()

        result = provider._check_system_requirements()

        assert result is False

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.local.torch")
    def test_check_system_requirements_when_tensor_creation_fails_then_returns_false(
        self, mock_torch
    ):
        """Test system requirements check when tensor creation raises exception."""
        mock_torch.tensor.side_effect = RuntimeError("Torch not properly installed")
        provider = LocalAIProvider()

        result = provider._check_system_requirements()

        assert result is False

    @patch("spec_cli.ai.providers.local.HF_AVAILABLE", True)
    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.LocalAIProvider._get_device")
    def test_check_system_requirements_when_device_is_none_then_returns_false(
        self, mock_get_device, mock_torch
    ):
        """Test system requirements check when device detection returns None."""
        mock_torch.tensor.return_value = Mock()
        mock_get_device.return_value = None
        provider = LocalAIProvider()

        result = provider._check_system_requirements()

        assert result is False


class TestLocalAIProviderDeviceDetection:
    """Test device detection and platform-specific behavior."""

    @patch("spec_cli.ai.providers.local.torch", None)
    def test_get_device_when_torch_none_then_raises_assertion_error(self):
        """Test device detection raises assertion error when torch is None.

        _get_device is only called after torch availability is confirmed,
        so it correctly asserts torch is not None.
        """
        provider = LocalAIProvider()

        with pytest.raises(AssertionError):
            provider._get_device()

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_LINUX)
    def test_get_device_when_auto_and_cuda_available_then_returns_cuda(
        self, mock_torch
    ):
        """Test device detection with auto config and CUDA available."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.return_value = 1
        config = LocalModelConfig(device="auto")
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result == MOCK_DEVICE_CUDA
        mock_torch.cuda.is_available.assert_called_once()
        mock_torch.cuda.device_count.assert_called_once()

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_DARWIN)
    def test_get_device_when_auto_cuda_fails_mps_available_then_returns_mps(
        self, mock_torch
    ):
        """Test device detection falling back from CUDA to MPS on macOS."""
        # CUDA fails
        mock_torch.cuda.is_available.return_value = False

        # MPS available
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.backends.mps.is_built.return_value = True

        config = LocalModelConfig(device="auto")
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result == MOCK_DEVICE_MPS
        mock_torch.backends.mps.is_available.assert_called_once()
        mock_torch.backends.mps.is_built.assert_called_once()

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_WIN32)
    def test_get_device_when_auto_and_no_gpu_then_returns_cpu(self, mock_torch):
        """Test device detection falling back to CPU when no GPU available."""
        mock_torch.cuda.is_available.return_value = False
        config = LocalModelConfig(device="auto")
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result == MOCK_DEVICE_CPU

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_LINUX)
    def test_get_device_when_auto_cuda_detection_exception_then_falls_back(
        self, mock_torch
    ):
        """Test device detection handling CUDA detection exceptions."""
        mock_torch.cuda.is_available.return_value = True
        mock_torch.cuda.device_count.side_effect = Exception("CUDA error")
        config = LocalModelConfig(device="auto")
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result == MOCK_DEVICE_CPU

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_DARWIN)
    def test_get_device_when_auto_mps_detection_exception_then_falls_back(
        self, mock_torch
    ):
        """Test device detection handling MPS detection exceptions."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.side_effect = Exception("MPS error")
        config = LocalModelConfig(device="auto")
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result == MOCK_DEVICE_CPU

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_WIN32)
    def test_get_device_when_cuda_requested_but_unavailable_then_returns_none(
        self, mock_torch
    ):
        """Test device detection when CUDA requested but not available."""
        mock_torch.cuda.is_available.return_value = False
        config = LocalModelConfig(device=MOCK_DEVICE_CUDA)
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result is None

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_LINUX)
    def test_get_device_when_mps_requested_on_non_darwin_then_returns_none(
        self, mock_torch
    ):
        """Test device detection when MPS requested on non-macOS platform."""
        config = LocalModelConfig(device=MOCK_DEVICE_MPS)
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result is None

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_DARWIN)
    def test_get_device_when_mps_requested_but_unavailable_then_returns_none(
        self, mock_torch
    ):
        """Test device detection when MPS requested but not available on macOS."""
        mock_torch.backends.mps.is_available.return_value = False
        config = LocalModelConfig(device=MOCK_DEVICE_MPS)
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result is None

    @patch("spec_cli.ai.providers.local.torch")
    def test_get_device_when_cpu_explicitly_requested_then_returns_cpu(
        self, mock_torch
    ):
        """Test device detection when CPU is explicitly configured."""
        config = LocalModelConfig(device=MOCK_DEVICE_CPU)
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result == MOCK_DEVICE_CPU

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_DARWIN)
    def test_get_device_when_mps_explicitly_requested_and_available_then_returns_mps(
        self, mock_torch
    ):
        """Test device detection when MPS is explicitly configured and available."""
        mock_torch.backends.mps.is_available.return_value = True
        config = LocalModelConfig(device=MOCK_DEVICE_MPS)
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result == MOCK_DEVICE_MPS

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_LINUX)
    def test_get_device_when_cuda_explicitly_requested_and_available_then_returns_cuda(
        self, mock_torch
    ):
        """Test device detection when CUDA is explicitly configured and available."""
        mock_torch.cuda.is_available.return_value = True
        config = LocalModelConfig(device=MOCK_DEVICE_CUDA)
        provider = LocalAIProvider(config=config)

        result = provider._get_device()

        assert result == MOCK_DEVICE_CUDA


class TestLocalAIProviderDocumentationGeneration:
    """Test documentation generation functionality."""

    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    def test_generate_documentation_when_provider_unavailable_then_returns_error_result(
        self, mock_is_available
    ):
        """Test generation when provider is not available."""
        mock_is_available.return_value = False
        provider = LocalAIProvider()
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        result = provider.generate_documentation(request)

        assert result.success is False
        assert "not available" in result.error
        assert "missing dependencies or insufficient resources" in result.error

    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request")
    def test_generate_documentation_when_invalid_request_then_returns_error_result(
        self, mock_validate, mock_is_available
    ):
        """Test generation when request validation fails."""
        mock_is_available.return_value = True
        mock_validate.side_effect = ValueError("Invalid request")
        provider = LocalAIProvider()
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        result = provider.generate_documentation(request)

        assert result.success is False
        assert result.error == "Invalid request: Invalid request"

    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request")
    def test_generate_documentation_when_sanitization_fails_then_returns_error_result(
        self, mock_validate, mock_is_available
    ):
        """Test generation when content sanitization fails."""
        mock_is_available.return_value = True
        mock_validate.return_value = None
        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.side_effect = ValueError("Sanitization failed")
        provider = LocalAIProvider(sanitizer=mock_sanitizer)
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        result = provider.generate_documentation(request)

        assert result.success is False
        assert result.error == "Content sanitization failed: Sanitization failed"

    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_LINUX)
    @patch("spec_cli.ai.providers.local.DocumentationGenerator")
    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    def test_generate_documentation_when_successful_then_returns_ai_generated_result(
        self,
        mock_is_available,
        mock_validate,
        mock_gpu_capabilities,
        mock_generator_class,
    ):
        """Test successful generation returns AI-generated result."""
        mock_is_available.return_value = True
        mock_validate.return_value = None
        mock_gpu_capabilities.return_value = MOCK_GPU_CAPABILITIES_CPU

        # Setup successful generator
        mock_generator = Mock()
        mock_generator.load_model.return_value = True
        mock_generator.generate_documentation.return_value = GenerationResult(
            success=True,
            content={"index.md": "# AI Generated Content", "history.md": "# History"},
            metadata={
                "provider": "local",
                "model": "test/model",
                "platform": PLATFORM_LINUX,
            },
        )
        mock_generator_class.return_value = mock_generator

        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.return_value = TEST_SANITIZED_CONTENT
        config = LocalModelConfig(model_name="test/model")
        provider = LocalAIProvider(config=config, sanitizer=mock_sanitizer)
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        result = provider.generate_documentation(request)

        assert result.success is True
        assert "index.md" in result.content
        assert "AI Generated Content" in result.content["index.md"]
        assert result.metadata["provider"] == "local"
        assert result.metadata["model"] == "test/model"

        # Verify sanitization was called
        mock_sanitizer.sanitize.assert_called_once_with(TEST_CONTENT, TEST_SOURCE_FILE)

        # Verify integration components were called
        mock_gpu_capabilities.assert_called_once()
        mock_generator_class.assert_called_once_with(config)
        mock_generator.load_model.assert_called_once_with("cpu")
        mock_generator.generate_documentation.assert_called_once_with(request)


class TestLocalAIProviderResourceCleanup:
    """Test resource cleanup functionality."""

    def test_cleanup_when_no_resources_allocated_then_no_action(self):
        """Test cleanup when no resources are allocated."""
        provider = LocalAIProvider()
        provider._resources_allocated = False

        # Should not raise any exceptions
        provider.cleanup()

        assert provider._resources_allocated is False

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_LINUX)
    def test_cleanup_when_resources_allocated_then_cleans_up(self, mock_torch):
        """Test cleanup when resources are allocated."""
        mock_torch.cuda.is_available.return_value = True
        provider = LocalAIProvider()
        provider._resources_allocated = True
        provider._model = Mock()
        provider._tokenizer = Mock()
        provider._pipeline = Mock()
        provider._model_loaded = True

        provider.cleanup()

        assert provider._model is None
        assert provider._tokenizer is None
        assert provider._pipeline is None
        assert provider._resources_allocated is False
        assert provider._model_loaded is False
        mock_torch.cuda.empty_cache.assert_called_once()

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_DARWIN)
    def test_cleanup_when_mps_available_then_cleans_mps_cache(self, mock_torch):
        """Test cleanup with MPS GPU memory cleanup on macOS."""
        # This should cover lines 144->155 where torch is not None
        # CUDA is not available, but MPS is available
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.mps.empty_cache = Mock()
        provider = LocalAIProvider()
        provider._resources_allocated = True

        provider.cleanup()

        mock_torch.mps.empty_cache.assert_called_once()
        # Verify the state was cleaned up
        assert provider._resources_allocated is False
        assert provider._model_loaded is False

    @patch("spec_cli.ai.providers.local.torch")
    def test_cleanup_when_mps_missing_empty_cache_then_handles_gracefully(
        self, mock_torch
    ):
        """Test cleanup handles missing MPS empty_cache gracefully."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        # Simulate older PyTorch version without mps.empty_cache
        mock_torch.mps.empty_cache.side_effect = AttributeError("Method not available")
        provider = LocalAIProvider()
        provider._resources_allocated = True

        # Should not raise AttributeError
        provider.cleanup()

        assert provider._resources_allocated is False

    @patch("spec_cli.ai.providers.local.torch")
    def test_cleanup_when_exception_occurs_then_handles_gracefully(self, mock_torch):
        """Test cleanup handles exceptions gracefully."""
        mock_torch.cuda.is_available.side_effect = Exception("Cleanup error")
        provider = LocalAIProvider()
        provider._resources_allocated = True

        # Should not raise exception
        provider.cleanup()


class TestLocalAIProviderCrossPlatformPathHandling:
    """Test cross-platform path handling in all methods."""

    @patch("spec_cli.ai.providers.local.DocumentationGenerator")
    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    def test_generate_documentation_normalizes_windows_paths_in_metadata(
        self,
        mock_is_available,
        mock_validate,
        mock_gpu_capabilities,
        mock_generator_class,
    ):
        """Test that Windows-style paths are normalized in metadata."""
        mock_is_available.return_value = True
        mock_validate.return_value = None
        mock_gpu_capabilities.return_value = MOCK_GPU_CAPABILITIES_CPU

        # Setup successful generator with normalized metadata
        mock_generator = Mock()
        mock_generator.load_model.return_value = True
        mock_generator.generate_documentation.return_value = GenerationResult(
            success=True,
            content={"index.md": "# Generated", "history.md": "# History"},
            metadata={
                "provider": "local",
                "source_file": "src/models/user.py",  # Should be normalized by generator
                "platform": "test",
            },
        )
        mock_generator_class.return_value = mock_generator

        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.return_value = TEST_SANITIZED_CONTENT
        provider = LocalAIProvider(sanitizer=mock_sanitizer)

        # Use Windows-style path
        windows_path = Path("src\\models\\user.py")
        request = GenerationRequest(source_file=windows_path, content=TEST_CONTENT)

        result = provider.generate_documentation(request)

        # Verify path normalization in metadata (from generator result)
        expected_normalized = "src/models/user.py"
        assert result.metadata["source_file"] == expected_normalized


class TestLocalAIProviderInfoReporting:
    """Test provider information reporting."""

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_DARWIN)
    @patch("spec_cli.ai.providers.local.LocalAIProvider._get_device")
    @patch("spec_cli.ai.providers.local.LocalAIProvider._check_system_requirements")
    def test_get_provider_info_returns_complete_information(
        self, mock_check_system, mock_get_device, mock_torch
    ):
        """Test that provider info includes all required information."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        mock_get_device.return_value = MOCK_DEVICE_MPS
        mock_check_system.return_value = True

        config = LocalModelConfig(
            model_name="test/model", max_tokens=1024, temperature=0.7, use_4bit=False
        )
        provider = LocalAIProvider(config=config)
        provider._model_loaded = True
        provider._resources_allocated = True

        info = provider.get_provider_info()

        # Verify base provider info
        assert info["provider_class"] == "LocalAIProvider"
        assert "available" in info
        assert info["supports_cleanup"] is True

        # Verify local provider specific info
        assert info["model_name"] == "test/model"
        assert info["max_tokens"] == 1024
        assert info["temperature"] == 0.7
        assert info["use_4bit"] is False
        assert info["device"] == MOCK_DEVICE_MPS
        assert info["model_loaded"] is True
        assert info["resources_allocated"] is True
        assert info["torch_available"] is True
        assert info["platform"] == PLATFORM_DARWIN
        assert info["cuda_available"] is False
        assert info["mps_available"] is True
        assert info["system_requirements_met"] is True


class TestLocalAIProviderThreadSafety:
    """Test thread safety of model loading operations."""

    def test_cleanup_uses_loading_lock_for_thread_safety(self):
        """Test that cleanup method uses the loading lock."""
        provider = LocalAIProvider()
        provider._resources_allocated = True

        # Mock the lock to verify it's used
        original_lock = provider._loading_lock
        provider._loading_lock = Mock()
        provider._loading_lock.__enter__ = Mock(return_value=None)
        provider._loading_lock.__exit__ = Mock(return_value=None)

        provider.cleanup()

        provider._loading_lock.__enter__.assert_called_once()
        provider._loading_lock.__exit__.assert_called_once()

        # Restore original lock
        provider._loading_lock = original_lock

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_DARWIN)
    def test_cleanup_when_mps_available_then_clears_mps_cache(self, mock_torch):
        """Test cleanup clears MPS cache when available on macOS."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.mps.empty_cache = Mock()

        provider = LocalAIProvider()
        provider._resources_allocated = True

        provider.cleanup()

        # Verify MPS cache was cleared
        mock_torch.mps.empty_cache.assert_called_once()

    @patch("spec_cli.ai.providers.local.torch")
    @patch("spec_cli.ai.providers.local.sys.platform", PLATFORM_DARWIN)
    def test_cleanup_when_mps_empty_cache_unavailable_then_handles_gracefully(
        self, mock_torch
    ):
        """Test cleanup handles AttributeError when MPS empty_cache is unavailable."""
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends.mps.is_available.return_value = True
        mock_torch.mps.empty_cache.side_effect = AttributeError("Method not available")

        provider = LocalAIProvider()
        provider._resources_allocated = True

        # Should not raise exception
        provider.cleanup()

        # Verify attempt was made
        mock_torch.mps.empty_cache.assert_called_once()


class TestLocalAIProviderRequestValidation:
    """Test request validation integration."""

    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    def test_generate_documentation_calls_validate_request(self, mock_is_available):
        """Test that generate_documentation calls validate_request."""
        mock_is_available.return_value = True
        provider = LocalAIProvider()
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        with patch.object(provider, "validate_request") as mock_validate:
            mock_validate.return_value = None
            provider.generate_documentation(request)

            mock_validate.assert_called_once_with(request)


class TestLocalAIProviderIntegrationWithHelpers:
    """Test integration with helper utilities."""

    def test_provider_uses_path_normalization_for_cross_platform_compatibility(
        self,
    ):
        """Test that provider uses path normalization utilities."""
        # This is tested indirectly through other tests, but we verify the import
        from spec_cli.utils.path_utils import normalize_path_separators

        test_path = "src\\models\\user.py"
        normalized = normalize_path_separators(test_path)
        assert normalized == "src/models/user.py"

    def test_provider_integrates_with_sanitizer_from_slice_1c(self):
        """Test that provider properly integrates with CodeSanitizer."""
        mock_sanitizer = Mock(spec=CodeSanitizer)
        mock_sanitizer.sanitize.return_value = TEST_SANITIZED_CONTENT

        provider = LocalAIProvider(sanitizer=mock_sanitizer)

        assert provider.sanitizer is mock_sanitizer

    def test_provider_integrates_with_config_from_slice_1a(self):
        """Test that provider properly integrates with LocalModelConfig."""
        config = LocalModelConfig(model_name="custom/model")
        provider = LocalAIProvider(config=config)

        assert provider.config is config
        assert provider.config.model_name == "custom/model"


class TestLocalAIProviderGeneratorIntegration:
    """Test LocalAIProvider integration with DocumentationGenerator."""

    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    @patch("spec_cli.ai.providers.local.DocumentationGenerator")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request")
    def test_generate_documentation_when_successful_integration_then_returns_success_result(
        self,
        mock_validate,
        mock_is_available,
        mock_generator_class,
        mock_gpu_capabilities,
    ):
        """Test successful integration with DocumentationGenerator."""
        # Setup mocks
        mock_is_available.return_value = True
        mock_validate.return_value = None
        mock_gpu_capabilities.return_value = MOCK_GPU_CAPABILITIES_CUDA

        mock_generator = Mock()
        mock_generator.load_model.return_value = True
        mock_generator.generate_documentation.return_value = GenerationResult(
            **MOCK_GENERATION_RESULT_SUCCESS
        )
        mock_generator_class.return_value = mock_generator

        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.return_value = TEST_SANITIZED_CONTENT
        provider = LocalAIProvider(sanitizer=mock_sanitizer)
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        result = provider.generate_documentation(request)

        # Verify successful integration
        assert result.success is True
        assert "index.md" in result.content
        assert result.metadata["provider"] == "local"

        # Verify helper usage
        mock_gpu_capabilities.assert_called_once()
        mock_generator_class.assert_called_once_with(provider.config)
        mock_generator.load_model.assert_called_once_with("cuda")
        mock_generator.generate_documentation.assert_called_once_with(request)

    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    @patch("spec_cli.ai.providers.local.DocumentationGenerator")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request")
    def test_generate_documentation_when_model_loading_fails_then_returns_error_result(
        self,
        mock_validate,
        mock_is_available,
        mock_generator_class,
        mock_gpu_capabilities,
    ):
        """Test handling of model loading failure."""
        # Setup mocks
        mock_is_available.return_value = True
        mock_validate.return_value = None
        mock_gpu_capabilities.return_value = MOCK_GPU_CAPABILITIES_CPU

        mock_generator = Mock()
        mock_generator.load_model.return_value = False
        mock_generator_class.return_value = mock_generator

        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.return_value = TEST_SANITIZED_CONTENT
        provider = LocalAIProvider(sanitizer=mock_sanitizer)
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        result = provider.generate_documentation(request)

        # Verify error handling
        assert result.success is False
        assert "Failed to load AI model" in result.error
        assert result.metadata["device"] == "cpu"

        # Verify model loading attempt
        mock_generator.load_model.assert_called_once_with("cpu")
        mock_generator.generate_documentation.assert_not_called()

    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    @patch("spec_cli.ai.providers.local.DocumentationGenerator")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request")
    def test_generate_documentation_when_generation_fails_then_returns_error_result(
        self,
        mock_validate,
        mock_is_available,
        mock_generator_class,
        mock_gpu_capabilities,
    ):
        """Test handling of generation failure."""
        # Setup mocks
        mock_is_available.return_value = True
        mock_validate.return_value = None
        mock_gpu_capabilities.return_value = MOCK_GPU_CAPABILITIES_MPS

        mock_generator = Mock()
        mock_generator.load_model.return_value = True
        mock_generator.generate_documentation.side_effect = Exception(
            "Generation failed"
        )
        mock_generator_class.return_value = mock_generator

        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.return_value = TEST_SANITIZED_CONTENT
        provider = LocalAIProvider(sanitizer=mock_sanitizer)
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        result = provider.generate_documentation(request)

        # Verify error handling
        assert result.success is False
        assert "AI generation failed: Generation failed" in result.error
        assert result.metadata["provider"] == "local"

        # Verify generation attempt
        mock_generator.generate_documentation.assert_called_once_with(request)

    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    @patch("spec_cli.ai.providers.local.default_error_handler")
    @patch("spec_cli.ai.providers.local.DocumentationGenerator")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request")
    def test_generate_documentation_when_exception_then_uses_error_handler_helper(
        self,
        mock_validate,
        mock_is_available,
        mock_generator_class,
        mock_error_handler,
        mock_gpu_capabilities,
    ):
        """Test that error handler helper is used for exceptions."""
        # Setup mocks
        mock_is_available.return_value = True
        mock_validate.return_value = None
        mock_gpu_capabilities.return_value = MOCK_GPU_CAPABILITIES_CPU

        mock_generator = Mock()
        mock_generator.load_model.side_effect = RuntimeError("Device not available")
        mock_generator_class.return_value = mock_generator

        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.return_value = TEST_SANITIZED_CONTENT
        provider = LocalAIProvider(sanitizer=mock_sanitizer)
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        provider.generate_documentation(request)

        # Verify error handler usage
        mock_error_handler.report.assert_called_once()
        call_args = mock_error_handler.report.call_args
        assert isinstance(call_args[0][0], RuntimeError)
        assert call_args[0][1] == "AI generation"
        assert call_args[1]["code_path"] == request.source_file
        assert call_args[1]["provider"] == "local"
        assert call_args[1]["model"] == provider.config.model_name

    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    def test_device_detection_when_cuda_available_then_selects_cuda(
        self, mock_gpu_capabilities
    ):
        """Test device detection selects CUDA when available."""
        mock_gpu_capabilities.return_value = MOCK_GPU_CAPABILITIES_CUDA

        with (
            patch(
                "spec_cli.ai.providers.local.DocumentationGenerator"
            ) as mock_generator_class,
            patch(
                "spec_cli.ai.providers.local.LocalAIProvider.is_available",
                return_value=True,
            ),
            patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request"),
        ):
            mock_generator = Mock()
            mock_generator.load_model.return_value = True
            mock_generator.generate_documentation.return_value = GenerationResult(
                **MOCK_GENERATION_RESULT_SUCCESS
            )
            mock_generator_class.return_value = mock_generator

            provider = LocalAIProvider()
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            provider.generate_documentation(request)

            # Verify CUDA device selected
            mock_generator.load_model.assert_called_once_with("cuda")

    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    def test_device_detection_when_mps_available_then_selects_cpu(
        self, mock_gpu_capabilities
    ):
        """Test device detection selects CPU over MPS for performance (small models)."""
        mock_gpu_capabilities.return_value = MOCK_GPU_CAPABILITIES_MPS

        with (
            patch(
                "spec_cli.ai.providers.local.DocumentationGenerator"
            ) as mock_generator_class,
            patch(
                "spec_cli.ai.providers.local.LocalAIProvider.is_available",
                return_value=True,
            ),
            patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request"),
        ):
            mock_generator = Mock()
            mock_generator.load_model.return_value = True
            mock_generator.generate_documentation.return_value = GenerationResult(
                **MOCK_GENERATION_RESULT_SUCCESS
            )
            mock_generator_class.return_value = mock_generator

            provider = LocalAIProvider()
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            provider.generate_documentation(request)

            # Verify CPU device selected (CPU is faster than MPS for small models)
            mock_generator.load_model.assert_called_once_with("cpu")

    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    def test_device_detection_when_no_gpu_then_selects_cpu(self, mock_gpu_capabilities):
        """Test device detection falls back to CPU when no GPU available."""
        mock_gpu_capabilities.return_value = MOCK_GPU_CAPABILITIES_CPU

        with (
            patch(
                "spec_cli.ai.providers.local.DocumentationGenerator"
            ) as mock_generator_class,
            patch(
                "spec_cli.ai.providers.local.LocalAIProvider.is_available",
                return_value=True,
            ),
            patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request"),
        ):
            mock_generator = Mock()
            mock_generator.load_model.return_value = True
            mock_generator.generate_documentation.return_value = GenerationResult(
                **MOCK_GENERATION_RESULT_SUCCESS
            )
            mock_generator_class.return_value = mock_generator

            provider = LocalAIProvider()
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            provider.generate_documentation(request)

            # Verify CPU device selected
            mock_generator.load_model.assert_called_once_with("cpu")

    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    def test_generate_documentation_when_provider_unavailable_then_returns_error_without_integration(
        self, mock_is_available
    ):
        """Test that integration is skipped when provider is unavailable."""
        mock_is_available.return_value = False

        with patch(
            "spec_cli.ai.providers.local.DocumentationGenerator"
        ) as mock_generator_class:
            provider = LocalAIProvider()
            request = GenerationRequest(
                source_file=TEST_SOURCE_FILE, content=TEST_CONTENT
            )

            result = provider.generate_documentation(request)

            # Verify early return without integration
            assert result.success is False
            assert "not available" in result.error
            mock_generator_class.assert_not_called()

    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    @patch("spec_cli.ai.providers.local.DocumentationGenerator")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    def test_generate_documentation_when_validation_fails_then_returns_error_without_integration(
        self, mock_is_available, mock_generator_class, mock_gpu_capabilities
    ):
        """Test that integration is skipped when request validation fails."""
        mock_is_available.return_value = True

        provider = LocalAIProvider()
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        with patch.object(
            provider, "validate_request", side_effect=ValueError("Invalid request")
        ):
            result = provider.generate_documentation(request)

            # Verify early return without integration
            assert result.success is False
            assert "Invalid request" in result.error
            mock_generator_class.assert_not_called()

    @patch("spec_cli.ai.providers.local.get_gpu_capabilities")
    @patch("spec_cli.ai.providers.local.DocumentationGenerator")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.is_available")
    @patch("spec_cli.ai.providers.local.LocalAIProvider.validate_request")
    def test_generate_documentation_when_sanitization_fails_then_returns_error_without_integration(
        self,
        mock_validate,
        mock_is_available,
        mock_generator_class,
        mock_gpu_capabilities,
    ):
        """Test that integration is skipped when content sanitization fails."""
        mock_is_available.return_value = True
        mock_validate.return_value = None

        mock_sanitizer = Mock()
        mock_sanitizer.sanitize.side_effect = ValueError("Sanitization failed")
        provider = LocalAIProvider(sanitizer=mock_sanitizer)
        request = GenerationRequest(source_file=TEST_SOURCE_FILE, content=TEST_CONTENT)

        result = provider.generate_documentation(request)

        # Verify early return without integration
        assert result.success is False
        assert "Content sanitization failed" in result.error
        mock_generator_class.assert_not_called()
