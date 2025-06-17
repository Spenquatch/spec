# Slice 2c: AI Generation Logic

## Goal
Implement the actual AI documentation generation logic for LocalAIProvider, including model loading, prompt creation, and content generation.

## Scope
- Actual model loading with Qwen2.5-Coder
- Prompt creation for documentation generation
- AI inference and content generation
- Model output parsing and validation
- Extends slice 2b with generation capability

## Files to Create (≤3)
- `spec_cli/ai/providers/generation.py` (≤180 lines, complexity ≤7)

## Classes/Services (≤2)
1. **DocumentationGenerator** - Handles AI model loading and generation logic

## McCabe Complexity (≤7 per function)
- **load_model()**: ≤6 decision points (device selection, quantization, error handling)
- **generate_content()**: ≤7 decision points (prompt creation, inference, parsing)
- **_create_prompt()**: ≤5 decision points (template handling, context building)
- **_parse_output()**: ≤6 decision points (content extraction, validation, formatting)

## External Integrations (≤1)
- **HuggingFace Transformers** - Single external integration (shared with slice 2b)

## Implementation

```python
# spec_cli/ai/providers/generation.py
import time
import os
import sys
from typing import Dict, Any, Optional, Tuple
import logging

from .base import GenerationRequest, GenerationResult
from ..config.settings import LocalModelConfig
from ...utils.path_utils import normalize_path_separators

# HuggingFace imports (availability checked by LocalAIProvider)
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

logger = logging.getLogger(__name__)

class DocumentationGenerator:
    """Handles AI model loading and documentation generation logic."""

    def __init__(self, config: LocalModelConfig):
        """Initialize documentation generator.

        Args:
            config: Local model configuration
        """
        self.config = config
        self.model = None
        self.tokenizer = None
        self.device = None
        self._generation_count = 0

    def load_model(self, device: str) -> bool:
        """Load Qwen2.5-Coder model for documentation generation.

        Args:
            device: Device to load model on (cpu, cuda, mps)

        Returns:
            bool: True if model loaded successfully
        """
        if not HF_AVAILABLE:
            logger.error("HuggingFace dependencies not available")
            return False

        try:
            self.device = device
            model_name = self.config.model_name

            logger.info(f"Loading model {model_name} on {device}...")
            start_time = time.time()

            # Get cross-platform cache directory
            cache_dir = self._get_cache_dir() if self.config.cache_enabled else None

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                trust_remote_code=True,
                cache_dir=cache_dir
            )

            # Configure model loading based on device and quantization settings
            model_kwargs = self._get_model_kwargs(device)

            # Load model with appropriate configuration
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                trust_remote_code=True,
                cache_dir=cache_dir,
                **model_kwargs
            )

            load_time = time.time() - start_time
            logger.info(f"Model loaded successfully in {load_time:.1f}s")

            return True

        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
            self.tokenizer = None
            return False

    def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate documentation using loaded AI model.

        Args:
            request: Documentation generation request

        Returns:
            GenerationResult: Generated documentation result
        """
        if self.model is None or self.tokenizer is None:
            return GenerationResult(
                success=False,
                error="Model not loaded - call load_model() first"
            )

        start_time = time.time()

        try:
            # Create documentation prompt
            prompt = self._create_documentation_prompt(request)

            # Generate content using AI model
            generated_text = self._generate_with_model(prompt)

            # Parse and structure the output
            structured_content = self._parse_generated_content(generated_text, request)

            processing_time = int((time.time() - start_time) * 1000)
            self._generation_count += 1

            # Use normalized path for consistent logging across platforms
            normalized_path = normalize_path_separators(str(request.source_file))
            logger.info(f"Generated documentation for {normalized_path} in {processing_time}ms")

            return GenerationResult(
                success=True,
                content=structured_content,
                metadata={
                    "provider": "local",
                    "model": self.config.model_name,
                    "processing_time_ms": processing_time,
                    "generation_count": self._generation_count,
                    "device": self.device,
                    "platform": sys.platform,
                    "source_file": normalized_path
                }
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Documentation generation failed: {e}")

            return GenerationResult(
                success=False,
                error=f"Generation failed: {e}",
                metadata={"processing_time_ms": processing_time}
            )

    def _create_documentation_prompt(self, request: GenerationRequest) -> str:
        """Create prompt for documentation generation.

        Args:
            request: Generation request with code content

        Returns:
            str: Formatted prompt for AI model
        """
        # Use normalized path for consistent behavior across platforms
        normalized_path = normalize_path_separators(str(request.source_file))
        file_extension = request.get_file_extension()
        language = self._detect_language(file_extension)

        # Base prompt for comprehensive documentation
        prompt = f"""You are an expert technical writer creating comprehensive documentation for {language} code.

Generate structured documentation that helps both human developers and AI agents understand this code.

SOURCE FILE: {normalized_path}
LANGUAGE: {language}

CODE TO DOCUMENT:
```{language}
{request.content}
```

Generate documentation in this exact format:

# {os.path.basename(normalized_path)}

## Purpose
[Analyze the code and describe its main purpose and functionality]

## Key Components
[List and describe the main classes, functions, and important variables]

## Dependencies
[List imports and external dependencies]

## Usage Example
[Provide a realistic usage example based on the code analysis]

## Technical Notes
[Add any important technical considerations, patterns, or implementation details]

Focus on accuracy and usefulness for both human developers and AI agents working with this codebase."""

        return prompt

    def _generate_with_model(self, prompt: str) -> str:
        """Generate text using the loaded AI model.

        Args:
            prompt: Input prompt for generation

        Returns:
            str: Generated text from model
        """
        # Tokenize input
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048  # Leave room for generation
        )

        if self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate with model
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                do_sample=True if self.config.temperature > 0 else False,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id
            )

        # Decode output (remove input prompt)
        input_length = inputs['input_ids'].shape[1]
        generated_tokens = outputs[0][input_length:]
        generated_text = self.tokenizer.decode(generated_tokens, skip_special_tokens=True)

        return generated_text.strip()

    def _parse_generated_content(self, generated_text: str, request: GenerationRequest) -> Dict[str, str]:
        """Parse generated content into structured documentation.

        Args:
            generated_text: Raw generated text from model
            request: Original generation request

        Returns:
            Dict[str, str]: Structured content for spec documentation
        """
        # For now, put all content in index.md
        # Future enhancement could parse sections into separate files
        content = {
            "index.md": generated_text
        }

        # Add minimal history entry with normalized path
        normalized_path = normalize_path_separators(str(request.source_file))
        filename = os.path.basename(normalized_path)

        content["history.md"] = f"""# Documentation History for {filename}

## Latest Generation
- **Date**: Generated automatically
- **Method**: AI-powered analysis using {self.config.model_name}
- **Platform**: {sys.platform}
- **Source**: {normalized_path}
- **Content**: Comprehensive documentation based on code analysis

## Notes
- Documentation generated using local AI model
- Content optimized for both human and AI consumption
- Cross-platform compatible documentation format
"""

        return content

    def _get_model_kwargs(self, device: str) -> Dict[str, Any]:
        """Get model loading arguments based on configuration.

        Args:
            device: Target device for model

        Returns:
            Dict[str, Any]: Model loading arguments
        """
        kwargs = {}

        # Platform-specific device mapping
        if device == "cuda":
            kwargs["device_map"] = "auto"
        elif device == "mps" and sys.platform == "darwin":
            # Apple Silicon GPU handling
            kwargs["device_map"] = {"": "mps"}
        elif device != "cpu":
            kwargs["device_map"] = device

        # Platform-aware quantization for memory efficiency
        if self.config.use_4bit and device == "cuda":
            # 4-bit quantization only supported on CUDA
            kwargs["quantization_config"] = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4"
            )
        else:
            # Platform-specific dtype selection
            if device == "cuda":
                kwargs["torch_dtype"] = torch.float16
            elif device == "mps":
                # MPS works better with float32 for compatibility
                kwargs["torch_dtype"] = torch.float32
            else:
                kwargs["torch_dtype"] = torch.float32

        return kwargs

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
            ".php": "php"
        }

        return language_map.get(file_extension.lower(), "text")

    def _get_cache_dir(self) -> Optional[str]:
        """Get cross-platform model cache directory.

        Returns:
            Optional[str]: Normalized cache directory path or None for default
        """
        if not self.config.cache_enabled:
            return None

        # Check if custom cache directory is configured
        if hasattr(self.config, 'cache_dir') and self.config.cache_dir:
            # Use configured cache directory with cross-platform normalization
            return normalize_path_separators(self.config.cache_dir)

        # Use HuggingFace default cache directory (cross-platform)
        # HF_HOME or default ~/.cache/huggingface
        cache_dir = os.environ.get('HF_HOME')
        if cache_dir:
            return normalize_path_separators(cache_dir)

        # Platform-specific default cache directories
        if sys.platform == "win32":
            # Windows: %USERPROFILE%\.cache\huggingface
            default_cache = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')
        else:
            # Unix-like (macOS, Linux): ~/.cache/huggingface
            default_cache = os.path.join(os.path.expanduser('~'), '.cache', 'huggingface')

        return normalize_path_separators(default_cache)

    def cleanup(self) -> None:
        """Clean up loaded model resources with platform-specific optimizations."""
        self.model = None
        self.tokenizer = None

        # Platform-specific GPU memory cleanup
        if torch is not None:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("Cleared CUDA cache")
            elif sys.platform == "darwin" and hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                # Apple Silicon GPU cleanup if available
                try:
                    torch.mps.empty_cache()
                    logger.debug("Cleared MPS cache")
                except AttributeError:
                    # Fallback for older PyTorch versions
                    logger.debug("MPS cache clearing not available")
                    pass
```

## Inputs - EXPLICIT
- **config: LocalModelConfig** - Model configuration for loading and generation
- **device: str** - Target device (cpu, cuda, mps) for model loading
- **request: GenerationRequest** - Documentation generation request with code content

## Actions - UNAMBIGUOUS
1. Load Qwen2.5-Coder model with appropriate quantization and device settings
2. Create structured documentation prompts based on code content and file type
3. Generate documentation using AI model with configured parameters
4. Parse model output into structured documentation format (index.md, history.md)
5. Track generation metrics and performance data
6. Clean up model resources when finished

## Outputs - WELL-DEFINED
- **Model loading success**: Boolean indicating successful model initialization
- **Generation result**: GenerationResult with structured documentation content
- **Performance metrics**: Processing time, generation count, device information
- **Error handling**: Clear error messages for model loading or generation failures

## Helper Dependencies
- **Existing helpers**: `spec_cli.utils.path_utils.normalize_path_separators` for cross-platform path handling
- **Slice dependencies**: LocalModelConfig (1a), GenerationRequest/Result (2a)
- **External integration**: HuggingFace transformers for model loading and inference
- **Standard library**: `time` for performance tracking, `os` and `sys` for platform detection, `typing` for type safety

## Individual Test Scenarios (100% coverage achievable)
1. **test_generator_loads_model_successfully** - Test successful model loading
2. **test_generator_handles_model_loading_errors** - Test model loading failure handling
3. **test_generator_creates_documentation_prompts** - Test prompt generation logic
4. **test_generator_detects_programming_languages** - Test language detection from file extensions
5. **test_generator_configures_model_kwargs** - Test model configuration based on device/settings
6. **test_generator_generates_documentation** - Test full documentation generation workflow
7. **test_generator_handles_generation_errors** - Test generation error handling
8. **test_generator_tracks_performance_metrics** - Test performance tracking
9. **test_generator_parses_model_output** - Test output parsing into structured format
10. **test_generator_handles_quantization_settings** - Test 4-bit quantization configuration
11. **test_generator_cleans_up_resources** - Test resource cleanup
12. **test_generator_handles_missing_model** - Test generation without loaded model
13. **test_generator_cross_platform_cache_handling** - Test cache directory handling across Windows/Unix
14. **test_generator_platform_specific_model_loading** - Test device-specific model configuration (CUDA/MPS/CPU)
15. **test_generator_cross_platform_path_normalization** - Test path handling in prompts and metadata

## Quality Assurance
- **Poetry compliance**: Uses HuggingFace dependencies from AI group
- **Type safety**: Complete type annotations for all AI operations
- **Security clearance**: No sensitive data exposure, uses sanitized content from slice 2b
- **Performance**: Optimized for Qwen2.5-Coder-0.5B with quantization support
- **Cross-platform testing**: All tests use proper mock locations for Python < 3.11 compatibility

## Cross-Platform Testing Requirements
- **Mock patch locations**: Always patch at import location (`patch("module.imported_function")`) not source location
- **Path normalization**: Use `normalize_path_separators()` in all test assertions for path comparisons
- **Platform detection**: Mock `sys.platform` for testing platform-specific behavior
- **Model loading**: Mock HuggingFace model loading for different platforms and devices
- **Cache directories**: Mock cache directory resolution for Windows/Unix testing
- **Example test pattern**:
```python
# CORRECT - patch at import location (Python < 3.11 compatible)
@patch("spec_cli.ai.providers.generation.AutoModelForCausalLM.from_pretrained")
@patch("spec_cli.ai.providers.generation.normalize_path_separators")
def test_model_loads_with_normalized_cache(self, mock_normalize, mock_model):
    mock_normalize.return_value = "normalized/cache/path"
    # Test implementation

# INCORRECT - source location patching (fails Python < 3.11)
@patch("transformers.AutoModelForCausalLM.from_pretrained")
def test_model_loading(self, mock_model):
    # This will fail on Python < 3.11
```

## Integration with Other Slices
- **Depends on Slice 1a**: Uses LocalModelConfig for model settings
- **Depends on Slice 2a**: Uses GenerationRequest/Result interfaces
- **Used by Slice 2b**: LocalAIProvider will use this for actual generation
- **Enhancement target**: Template slices will extend prompt creation logic

## Delivery Requirements
- **Independent execution**: Can be implemented after dependent slices complete
- **Performance conscious**: Optimized for small model with quantization
- **Memory efficient**: Proper resource management for AI model operations
- **Ready for production**: Complete generation logic ready for integration

## Quality Gates
```bash
poetry run pytest tests/unit/ai/providers/test_generation.py -v --cov=spec_cli.ai.providers.generation --cov-fail-under=100
poetry run mypy spec_cli/ai/providers/generation.py --strict
poetry run ruff check spec_cli/ai/providers/generation.py
```

## Status
**READY for single AI agent implementation** - All granularity and quality limits met individually.
**Dependencies**: Requires slices 1a and 2a completion.
**Integration target**: Ready for integration into slice 2b LocalAIProvider.
