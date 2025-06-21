"""Local AI provider using HuggingFace for documentation generation."""

import logging
import sys
import threading

# Optional HuggingFace imports with graceful fallback
from typing import TYPE_CHECKING

from ...utils.error_handler import default_error_handler
from ...utils.platform_utils import get_gpu_capabilities
from ..analysis.sanitizer import CodeSanitizer
from ..config.settings import LocalModelConfig
from .base import AIProvider, GenerationRequest, GenerationResult
from .generation import DocumentationGenerator

try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from transformers.pipelines import pipeline

    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

    if TYPE_CHECKING:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        from transformers.pipelines import pipeline
    else:
        # Set module-level variables to None when imports fail
        torch = None
        AutoTokenizer = None
        AutoModelForCausalLM = None
        pipeline = None

logger = logging.getLogger(__name__)


class LocalAIProvider(AIProvider):
    """Local AI provider using HuggingFace Qwen2.5-Coder for documentation generation."""

    def __init__(
        self,
        config: LocalModelConfig | None = None,
        sanitizer: CodeSanitizer | None = None,
    ):
        """Initialize local AI provider.

        Args:
            config: Local model configuration (uses defaults if None)
            sanitizer: Code sanitizer instance (creates default if None)
        """
        super().__init__()
        self.config = config or LocalModelConfig()
        self.sanitizer = sanitizer or CodeSanitizer()

        # Model loading state
        self._model = None
        self._tokenizer = None
        self._pipeline = None
        self._model_loaded = False
        self._loading_lock = threading.Lock()

        # Resource tracking
        self._resources_allocated = False

        self.logger.info(
            "Initialized LocalAIProvider with model: %s", self.config.model_name
        )

    def is_available(self) -> bool:
        """Check if HuggingFace dependencies are available and provider can run.

        Returns:
            bool: True if provider is ready for use
        """
        if not HF_AVAILABLE:
            self.logger.debug("HuggingFace dependencies not available")
            return False

        # Check if we have sufficient system requirements
        if not self._check_system_requirements():
            self.logger.debug("System requirements not met for local AI provider")
            return False

        self.logger.debug("Local AI provider is available")
        return True

    def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate documentation using AI model.

        Args:
            request: Documentation generation request

        Returns:
            GenerationResult: Documentation generation result
        """
        self.logger.debug("TRACE: LocalAIProvider.generate_documentation() called")
        print("PRINT TRACE: LocalAIProvider.generate_documentation() ACTUALLY CALLED")

        if not self.is_available():
            self.logger.debug("TRACE: Provider not available, returning error")
            return GenerationResult(
                success=False,
                error="Local AI provider is not available - missing dependencies or insufficient resources",
            )

        self.logger.debug("TRACE: Provider is available, proceeding with validation")

        # Validate request
        try:
            self.validate_request(request)
            self.logger.debug("TRACE: Request validation passed")
        except ValueError as e:
            self.logger.debug(f"TRACE: Request validation failed: {e}")
            return GenerationResult(success=False, error=f"Invalid request: {e}")

        # Sanitize content for security
        try:
            self.sanitizer.sanitize(request.content, request.source_file)
            self.logger.debug("TRACE: Content sanitization passed")
        except ValueError as e:
            self.logger.debug(f"TRACE: Content sanitization failed: {e}")
            return GenerationResult(
                success=False, error=f"Content sanitization failed: {e}"
            )

        try:
            # Use helper for device detection
            gpu_capabilities = get_gpu_capabilities()
            if gpu_capabilities["cuda_available"]:
                device = "cuda"
            elif gpu_capabilities["mps_available"]:
                device = "mps"
            else:
                device = "cpu"

            self.logger.debug(f"TRACE: Device selected: {device}")

            # Initialize generator (helper call)
            generator = DocumentationGenerator(self.config)
            self.logger.debug("TRACE: DocumentationGenerator created")

            # Load model with error handling
            self.logger.debug("TRACE: About to call generator.load_model()")
            print(f"PRINT TRACE: About to call generator.load_model({device})")
            load_result = generator.load_model(device)
            print(f"PRINT TRACE: generator.load_model returned: {load_result}")
            if not load_result:
                self.logger.debug("TRACE: Model loading failed")
                print("PRINT TRACE: Model loading failed, returning error")
                return GenerationResult(
                    success=False,
                    error="Failed to load AI model",
                    metadata={"provider": "local", "device": device},
                )

            self.logger.debug(
                "TRACE: Model loading succeeded, calling generate_documentation()"
            )
            print(
                "PRINT TRACE: Model loading succeeded, calling generator.generate_documentation()"
            )
            # Generate documentation
            result = generator.generate_documentation(request)
            print(f"PRINT TRACE: Generator returned result: success={result.success}")
            self.logger.debug(
                f"TRACE: Generator returned result: success={result.success}"
            )
            return result

        except Exception as e:
            # Use error handler helper
            self.logger.debug(f"TRACE: Exception in generate_documentation: {e}")
            error_context = {"provider": "local", "model": self.config.model_name}
            default_error_handler.report(
                e, "AI generation", code_path=request.source_file, **error_context
            )
            return GenerationResult(
                success=False,
                error=f"AI generation failed: {str(e)}",
                metadata=error_context,
            )

    def cleanup(self) -> None:
        """Clean up model resources and release memory."""
        with self._loading_lock:
            if self._resources_allocated:
                try:
                    # Clear model references
                    self._model = None
                    self._tokenizer = None
                    self._pipeline = None

                    # Platform-specific GPU memory cleanup
                    if torch is not None:
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()
                        elif (
                            hasattr(torch.backends, "mps")
                            and torch.backends.mps.is_available()
                        ):
                            # Apple Silicon GPU cleanup if available
                            try:
                                torch.mps.empty_cache()
                            except AttributeError:
                                # Fallback for older PyTorch versions
                                pass

                    self._resources_allocated = False
                    self._model_loaded = False

                    self.logger.info(
                        "Local AI provider resources cleaned up on %s", sys.platform
                    )

                except Exception as e:
                    self.logger.error("Error during cleanup: %s", e)

    def _check_system_requirements(self) -> bool:
        """Check if system meets requirements for local AI processing.

        Returns:
            bool: True if system requirements are met
        """
        if not HF_AVAILABLE or torch is None:
            return False

        try:
            # Basic torch functionality test
            _ = torch.tensor([1.0])

            # Check available device
            device = self._get_device()
            if device is None:
                return False

            self.logger.debug("System requirements met, using device: %s", device)
            return True

        except Exception as e:
            self.logger.debug("System requirements check failed: %s", e)
            return False

    def _get_device(self) -> str | None:
        """Determine appropriate device for model loading with platform-specific detection.

        Returns:
            Optional[str]: Device string or None if no suitable device
        """
        # torch availability already checked by caller
        assert torch is not None

        if self.config.device == "auto":
            # Platform-aware auto-detection of best available device
            try:
                # CUDA detection (Windows/Linux)
                if torch.cuda.is_available():
                    # Test CUDA actually works
                    torch.cuda.device_count()
                    return "cuda"
            except Exception as e:
                self.logger.debug("CUDA detection failed: %s", e)

            try:
                # Apple Silicon GPU detection (macOS only)
                if (
                    sys.platform == "darwin"
                    and hasattr(torch.backends, "mps")
                    and torch.backends.mps.is_available()
                    and torch.backends.mps.is_built()
                ):
                    return "mps"
            except Exception as e:
                self.logger.debug("MPS detection failed: %s", e)

            # Fallback to CPU (available on all platforms)
            return "cpu"
        else:
            # Validate configured device is available on current platform
            device = self.config.device

            if device == "cuda":
                if not torch.cuda.is_available():
                    self.logger.warning(
                        "CUDA device requested but not available on %s", sys.platform
                    )
                    return None
            elif device == "mps":
                if sys.platform != "darwin":
                    self.logger.warning(
                        "MPS device requested but only available on macOS, current: %s",
                        sys.platform,
                    )
                    return None
                if not (
                    hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
                ):
                    self.logger.warning("MPS device requested but not available")
                    return None

            return device

    def get_provider_info(self) -> dict[str, object]:
        """Get detailed provider information.

        Returns:
            dict: Provider information including model and system details
        """
        base_info = super().get_provider_info()

        local_info = {
            "model_name": self.config.model_name,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "use_4bit": self.config.use_4bit,
            "device": self._get_device() if torch is not None else "unavailable",
            "model_loaded": self._model_loaded,
            "resources_allocated": self._resources_allocated,
            "torch_available": torch is not None,
            "platform": sys.platform,
            "cuda_available": torch.cuda.is_available() if torch else False,
            "mps_available": (
                torch is not None
                and sys.platform == "darwin"
                and hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            ),
            "system_requirements_met": self._check_system_requirements(),
        }

        return {**base_info, **local_info}
