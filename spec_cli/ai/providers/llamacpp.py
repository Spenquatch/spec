"""LlamaCpp AI provider using llama-cpp-python for high-performance inference."""

import logging
import os
import sys
import time
import warnings
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ...utils.error_handler import default_error_handler
from ..analysis.sanitizer import CodeSanitizer
from ..config.settings import LlamaCppConfig
from .base import AIProvider, GenerationRequest, GenerationResult

# Optional llama-cpp-python import with graceful fallback
if TYPE_CHECKING:
    from llama_cpp import Llama

try:
    from llama_cpp import Llama

    LLAMA_CPP_AVAILABLE = True
except ImportError:
    LLAMA_CPP_AVAILABLE = False
    if not TYPE_CHECKING:
        Llama = Any  # Type placeholder when llama-cpp-python is not available

logger = logging.getLogger(__name__)


class LlamaCppProvider(AIProvider):
    """High-performance AI provider using llama.cpp for documentation generation."""

    def __init__(
        self,
        config: LlamaCppConfig | None = None,
        sanitizer: CodeSanitizer | None = None,
    ):
        """Initialize llama.cpp provider.

        Suppresses noisy logs from PyTorch and llama.cpp for cleaner output.

        Args:
            config: Llama.cpp configuration (uses defaults if None)
            sanitizer: Code sanitizer instance (creates default if None)
        """
        super().__init__()
        self.config = config or LlamaCppConfig()
        self.sanitizer = sanitizer or CodeSanitizer()

        # Suppress noisy logs for cleaner output
        self._suppress_noisy_logs()

        # Model instance (loaded on first use)
        self._model: Llama | None = None
        self._model_loaded = False

        # Auto-detect optimal thread count if set to default value
        if self.config.n_threads == 1:
            self.config.n_threads = min(os.cpu_count() or 4, 6)

        self.logger.info(
            "Initialized LlamaCppProvider with model: %s", self.config.model_path
        )

    def _suppress_noisy_logs(self) -> None:
        """Suppress noisy logs from PyTorch and related libraries."""
        # Suppress PyTorch distributed elastic warnings (both stderr and logging)
        os.environ["TORCH_DISTRIBUTED_DETAIL"] = "ERROR"
        os.environ["NCCL_BLOCKING_WAIT"] = "1"

        # Suppress Python module import warnings
        warnings.filterwarnings("ignore", category=RuntimeWarning, module="runpy")
        warnings.filterwarnings(
            "ignore", message=".*found in sys.modules.*", category=RuntimeWarning
        )

        # Suppress torch distributed logging at the source
        try:
            import torch.distributed.elastic.multiprocessing.redirects

            redirect_logger = getattr(
                torch.distributed.elastic.multiprocessing.redirects,
                "_redirect_logger",
                None,
            )
            if redirect_logger:
                redirect_logger.setLevel(logging.CRITICAL)
        except (ImportError, AttributeError):
            pass

        # Set PyTorch verbosity to reduce warnings
        try:
            import torch

            if hasattr(torch, "_C") and hasattr(torch._C, "_set_print_handler"):
                torch._C._set_print_handler(lambda x: None)  # Suppress C++ prints
        except (ImportError, AttributeError):
            pass  # PyTorch not available or different version

    def is_available(self) -> bool:
        """Check if llama-cpp-python is available and model exists.

        Returns:
            bool: True if provider is ready for use
        """
        if not LLAMA_CPP_AVAILABLE:
            self.logger.debug("llama-cpp-python not available")
            return False

        # Check if model file exists
        model_path = Path(self.config.model_path)
        if not model_path.exists():
            self.logger.debug(f"Model file not found: {model_path}")
            return False

        self.logger.debug("LlamaCpp provider is available")
        return True

    def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate documentation using llama.cpp model.

        Args:
            request: Documentation generation request

        Returns:
            GenerationResult: Documentation generation result
        """
        if not self.is_available():
            return GenerationResult(
                success=False,
                error="LlamaCpp provider is not available - missing dependencies or model file",
            )

        # Validate request
        try:
            self.validate_request(request)
        except ValueError as e:
            return GenerationResult(success=False, error=f"Invalid request: {e}")

        # Sanitize content for security
        try:
            self.sanitizer.sanitize(request.content, request.source_file)
        except ValueError as e:
            return GenerationResult(
                success=False, error=f"Content sanitization failed: {e}"
            )

        try:
            # Load model if needed
            if not self._model_loaded:
                load_result = self._load_model()
                if not load_result:
                    return GenerationResult(
                        success=False,
                        error="Failed to load llama.cpp model",
                    )

            # Generate documentation
            start_time = time.time()

            # Create prompt
            prompt = self._create_documentation_prompt(request)

            # Generate with llama.cpp
            self.logger.info(f"Generating documentation for {request.source_file}")

            if self._model is None:
                return GenerationResult(
                    success=False,
                    error="Model not loaded",
                )

            response = self._model(
                prompt,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                stop=["<|im_end|>"],  # Use Qwen2.5-Coder's natural end token only
                echo=False,  # Don't include prompt in response
            )

            # Safely extract response text
            generated_text = ""
            if hasattr(response, "__iter__") and not isinstance(response, dict):
                # Handle streaming response (iterator)
                response_text = ""
                for chunk in response:
                    if (
                        isinstance(chunk, dict)
                        and "choices" in chunk
                        and chunk["choices"]
                    ):
                        choice = chunk["choices"][0]
                        if isinstance(choice, dict):
                            delta = choice.get("delta", {})
                            if isinstance(delta, dict) and "content" in delta:
                                response_text += str(delta["content"])
                            elif "text" in choice:
                                response_text += str(choice["text"])
                generated_text = response_text.strip()
            elif (
                isinstance(response, dict)
                and "choices" in response
                and response["choices"]
            ):
                # Handle non-streaming response
                choice = response["choices"][0]
                # Try to extract text from various response formats
                # Try text field first
                text_value = choice.get("text") if isinstance(choice, dict) else None
                if text_value is not None:
                    generated_text = str(text_value).strip()
                else:
                    # Try message.content format
                    message = (
                        choice.get("message") if isinstance(choice, dict) else None
                    )
                    if isinstance(message, dict) and "content" in message:
                        generated_text = str(message["content"]).strip()
                    else:
                        return GenerationResult(
                            success=False,
                            error="No text content in response",
                        )
            else:
                return GenerationResult(
                    success=False,
                    error="Invalid response format from model",
                )

            # Structure the output
            structured_content = self._parse_generated_content(generated_text, request)

            processing_time = int((time.time() - start_time) * 1000)

            # Extract usage information safely
            tokens_generated = 0
            if isinstance(response, dict) and "usage" in response:
                usage = response["usage"]
                if isinstance(usage, dict) and "completion_tokens" in usage:
                    tokens_generated = usage["completion_tokens"]

            return GenerationResult(
                success=True,
                content=structured_content,
                metadata={
                    "provider": "llamacpp",
                    "model": self.config.model_path,
                    "processing_time_ms": processing_time,
                    "tokens_generated": tokens_generated,
                    "tokens_per_sec": tokens_generated / (processing_time / 1000)
                    if processing_time > 0 and tokens_generated > 0
                    else 0,
                    "platform": sys.platform,
                },
            )

        except Exception as e:
            error_context = {"provider": "llamacpp", "model": self.config.model_path}
            default_error_handler.report(
                e, "AI generation", code_path=request.source_file, **error_context
            )
            return GenerationResult(
                success=False,
                error=f"AI generation failed: {str(e)}",
                metadata=error_context,
            )

    def cleanup(self) -> None:
        """Clean up model resources."""
        if self._model is not None:
            del self._model
            self._model = None
            self._model_loaded = False
            self.logger.info("LlamaCpp provider resources cleaned up")

    def _load_model(self) -> bool:
        """Load the llama.cpp model.

        Returns:
            bool: True if model loaded successfully
        """
        if not LLAMA_CPP_AVAILABLE:
            return False

        try:
            self.logger.info(f"Loading llama.cpp model from {self.config.model_path}")
            start_time = time.time()

            # Suppress Metal GPU initialization logs during model loading
            stderr_buffer = StringIO()
            with redirect_stderr(stderr_buffer):
                self._model = Llama(
                    model_path=self.config.model_path,
                    n_ctx=self.config.n_ctx,
                    n_threads=self.config.n_threads,
                    n_gpu_layers=self.config.n_gpu_layers,
                    n_batch=self.config.n_batch,
                    use_mlock=self.config.use_mlock,
                    verbose=False,  # Always suppress verbose output
                )

            load_time = time.time() - start_time
            self._model_loaded = True

            self.logger.info(f"Model loaded successfully in {load_time:.1f}s")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            self._model = None
            self._model_loaded = False
            return False

    def _create_documentation_prompt(self, request: GenerationRequest) -> str:
        """Create prompt for documentation generation.

        Args:
            request: Generation request with code content

        Returns:
            str: Formatted prompt for llama.cpp model
        """
        file_extension = request.get_file_extension()
        language = self._detect_language(file_extension)

        # Use efficient prompt format for llama.cpp
        prompt = f"""<|im_start|>system
You are an expert code documentation generator. Create comprehensive markdown documentation for the provided code.<|im_end|>
<|im_start|>user
Generate documentation for this {language} code:

```{language}
{request.content}
```

Create well-structured markdown documentation including:
- Purpose and functionality
- Key components (classes, functions, important variables)
- Dependencies and imports
- Usage examples if relevant
- Technical notes

Documentation:<|im_end|>
<|im_start|>assistant
"""

        return prompt

    def _parse_generated_content(
        self, generated_text: str, request: GenerationRequest
    ) -> dict[str, str]:
        """Parse generated content into structured documentation.

        Args:
            generated_text: Raw generated text from model
            request: Original generation request

        Returns:
            Dict[str, str]: Structured content for spec documentation
        """
        content = {"index.md": generated_text}

        # Add minimal history entry
        filename = os.path.basename(str(request.source_file))

        content["history.md"] = f"""# Documentation History for {filename}

## Latest Generation
- **Date**: Generated automatically
- **Method**: AI-powered analysis using llama.cpp
- **Model**: {os.path.basename(self.config.model_path)}
- **Platform**: {sys.platform}
- **Performance**: High-speed inference with llama.cpp

## Notes
- Documentation generated using quantized GGUF model
- Optimized for speed and quality
- Cross-platform compatible
"""

        return content

    def _detect_language(self, file_extension: str) -> str:
        """Detect programming language from file extension.

        Args:
            file_extension: File extension (e.g., '.py', '.js')

        Returns:
            str: Programming language name
        """
        language_map = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".cpp": "cpp",
            ".c": "c",
            ".rs": "rust",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
        }

        return language_map.get(file_extension.lower(), "text")

    def get_provider_info(self) -> dict[str, object]:
        """Get detailed provider information.

        Returns:
            dict: Provider information
        """
        base_info = super().get_provider_info()

        llama_info = {
            "model_path": self.config.model_path,
            "model_exists": Path(self.config.model_path).exists(),
            "n_ctx": self.config.n_ctx,
            "n_threads": self.config.n_threads,
            "n_gpu_layers": self.config.n_gpu_layers,
            "n_batch": self.config.n_batch,
            "max_tokens": self.config.max_tokens,
            "model_loaded": self._model_loaded,
            "llama_cpp_available": LLAMA_CPP_AVAILABLE,
            "platform": sys.platform,
        }

        return {**base_info, **llama_info}
