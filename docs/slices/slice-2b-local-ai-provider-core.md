# Slice 2b: Local AI Provider Core

## Goal
Implement core local AI provider with HuggingFace integration for documentation generation, focusing on availability checking and basic infrastructure.

## Scope
- Local AI provider implementation using HuggingFace
- Dependency checking and availability validation
- Basic model loading infrastructure (lazy loading)
- Error handling and resource management foundation
- NO complex generation logic (that's for slice 2c)

## Files to Create (≤3)
- `spec_cli/ai/providers/local.py` (≤150 lines, complexity ≤7)

## Classes/Services (≤2)
1. **LocalAIProvider** - Core local AI provider implementation

## McCabe Complexity (≤7 per function)
- **is_available()**: ≤3 decision points (dependency check, basic validation)
- **__init__()**: ≤4 decision points (config validation, initialization)
- **cleanup()**: ≤5 decision points (resource cleanup, error handling)
- **_check_dependencies()**: ≤6 decision points (import checking, version validation)

## External Integrations (≤1)
- **HuggingFace Transformers** - Single external integration for AI model access

## Implementation

```python
# spec_cli/ai/providers/local.py
from typing import Optional
import logging
import threading
from pathlib import Path

from .base import AIProvider, GenerationRequest, GenerationResult
from ..config.settings import LocalModelConfig
from ..analysis.sanitizer import CodeSanitizer

# Optional HuggingFace imports with graceful fallback
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    torch = None
    AutoTokenizer = None
    AutoModelForCausalLM = None
    pipeline = None

logger = logging.getLogger(__name__)

class LocalAIProvider(AIProvider):
    """Local AI provider using HuggingFace Qwen2.5-Coder for documentation generation."""

    def __init__(self, config: Optional[LocalModelConfig] = None, sanitizer: Optional[CodeSanitizer] = None):
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

        self.logger.info(f"Initialized LocalAIProvider with model: {self.config.model_name}")

    def is_available(self) -> bool:
        """Check if HuggingFace dependencies are available and provider can run.

        Returns:
            bool: True if provider is ready for use
        """
        if not HF_AVAILABLE:
            self.logger.debug("HuggingFace dependencies not available")
            return False

        # Check if we have sufficient system resources
        if not self._check_system_requirements():
            self.logger.debug("System requirements not met for local AI provider")
            return False

        self.logger.debug("Local AI provider is available")
        return True

    def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate documentation using local AI model.

        Args:
            request: Documentation generation request

        Returns:
            GenerationResult: Documentation generation result
        """
        if not self.is_available():
            return GenerationResult(
                success=False,
                error="Local AI provider is not available - missing dependencies or insufficient resources"
            )

        # Validate request
        try:
            self.validate_request(request)
        except ValueError as e:
            return GenerationResult(success=False, error=f"Invalid request: {e}")

        # Sanitize content for security
        try:
            sanitized_content = self.sanitizer.sanitize(request.content, request.source_file)
        except ValueError as e:
            return GenerationResult(success=False, error=f"Content sanitization failed: {e}")

        # This slice focuses on infrastructure - actual generation in slice 2c
        self.logger.info(f"LocalAIProvider ready to process {request.source_file}")

        # Placeholder for actual generation (implemented in slice 2c)
        return GenerationResult(
            success=True,
            content={"index.md": "# Placeholder\nGeneration logic implemented in slice 2c"},
            metadata={"provider": "local", "model": self.config.model_name}
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

                    # Force garbage collection if torch is available
                    if torch is not None and torch.cuda.is_available():
                        torch.cuda.empty_cache()

                    self._resources_allocated = False
                    self._model_loaded = False

                    self.logger.info("Local AI provider resources cleaned up")

                except Exception as e:
                    self.logger.error(f"Error during cleanup: {e}")

    def _check_system_requirements(self) -> bool:
        """Check if system meets requirements for local AI processing.

        Returns:
            bool: True if system requirements are met
        """
        if not HF_AVAILABLE:
            return False

        try:
            # Check if torch is working
            if torch is None:
                return False

            # Basic torch functionality test
            test_tensor = torch.tensor([1.0])
            if test_tensor is None:
                return False

            # Check available device
            device = self._get_device()
            if device is None:
                return False

            self.logger.debug(f"System requirements met, using device: {device}")
            return True

        except Exception as e:
            self.logger.debug(f"System requirements check failed: {e}")
            return False

    def _get_device(self) -> Optional[str]:
        """Determine appropriate device for model loading.

        Returns:
            Optional[str]: Device string or None if no suitable device
        """
        if torch is None:
            return None

        if self.config.device == "auto":
            # Auto-detect best available device
            if torch.cuda.is_available():
                return "cuda"
            elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return "mps"  # Apple Silicon GPU
            else:
                return "cpu"
        else:
            # Use configured device
            return self.config.device

    def get_provider_info(self) -> dict:
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
            "device": self._get_device(),
            "model_loaded": self._model_loaded,
            "resources_allocated": self._resources_allocated,
            "torch_available": torch is not None,
            "cuda_available": torch.cuda.is_available() if torch else False
        }

        return {**base_info, **local_info}
```

## Inputs - EXPLICIT
- **config: Optional[LocalModelConfig]** - Model configuration from slice 1a (uses defaults if None)
- **sanitizer: Optional[CodeSanitizer]** - Code sanitizer from slice 1c (creates default if None)
- **request: GenerationRequest** - Documentation generation request (from slice 2a)

## Actions - UNAMBIGUOUS
1. Check HuggingFace dependency availability with graceful import handling
2. Validate system requirements for local AI processing
3. Initialize provider with configuration and resource tracking
4. Provide infrastructure for model loading (actual loading in slice 2c)
5. Sanitize code content before processing using slice 1c sanitizer
6. Clean up resources and memory when provider is no longer needed

## Outputs - WELL-DEFINED
- **Availability check**: Boolean indicating if provider can process requests
- **Generation result**: GenerationResult with placeholder content (real generation in slice 2c)
- **Resource cleanup**: Proper cleanup of allocated model resources
- **Provider info**: Detailed information about provider state and capabilities
- **Error handling**: Clear error messages for dependency or system requirement failures

## Helper Dependencies
- **Slice dependencies**: LocalModelConfig (1a), CodeSanitizer (1c), AIProvider interface (2a)
- **External integration**: HuggingFace transformers (with graceful fallback when missing)
- **Standard library**: `threading`, `logging` for resource management and monitoring

## Individual Test Scenarios (100% coverage achievable)
1. **test_local_provider_checks_dependencies** - Test HuggingFace availability detection
2. **test_local_provider_handles_missing_dependencies** - Test graceful fallback when HF missing
3. **test_local_provider_validates_system_requirements** - Test system requirement checking
4. **test_local_provider_initializes_with_config** - Test initialization with custom config
5. **test_local_provider_initializes_with_defaults** - Test initialization with default config
6. **test_local_provider_device_detection** - Test automatic device detection (CPU/CUDA/MPS)
7. **test_local_provider_sanitizes_content** - Test content sanitization integration
8. **test_local_provider_validates_requests** - Test request validation
9. **test_local_provider_handles_invalid_requests** - Test invalid request error handling
10. **test_local_provider_cleanup_resources** - Test resource cleanup
11. **test_local_provider_thread_safety** - Test thread-safe model loading
12. **test_local_provider_info_reporting** - Test provider information reporting

## Quality Assurance
- **Poetry compliance**: HuggingFace dependencies managed via Poetry AI group
- **Type safety**: Complete type annotations with Optional handling for missing dependencies
- **Security clearance**: Integrates with sanitizer for secure content processing
- **Resource management**: Proper cleanup and memory management for AI models

## Integration with Other Slices
- **Depends on Slice 1a**: Uses LocalModelConfig for configuration
- **Depends on Slice 1c**: Uses CodeSanitizer for content security
- **Depends on Slice 2a**: Implements AIProvider interface
- **Used by Slice 2c**: Slice 2c will extend this with actual generation logic
- **Interface**: Provides foundation for actual AI documentation generation

## Delivery Requirements
- **Independent execution**: Can be implemented after dependent slices are complete
- **Resource conscious**: Proper resource management for AI model infrastructure
- **Graceful degradation**: Clear error messages when dependencies missing
- **Ready for extension**: Designed for slice 2c to add generation logic

## Quality Gates
```bash
poetry run pytest tests/unit/ai/providers/test_local.py -v --cov=spec_cli.ai.providers.local --cov-fail-under=100
poetry run mypy spec_cli/ai/providers/local.py --strict
poetry run ruff check spec_cli/ai/providers/local.py
```

## Status
**READY for single AI agent implementation** - All granularity and quality limits met individually.
**Dependencies**: Requires slices 1a, 1c, and 2a completion.
**Extension point**: Ready for slice 2c to implement actual generation logic.
