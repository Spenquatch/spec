"""AI documentation generation implementation using local models.

This module provides the DocumentationGenerator class for loading and running
local AI models to generate documentation from source code. It handles model
loading, prompt creation, inference, and output parsing with cross-platform
support and memory optimization.
"""

import logging
import os
import sys
import time
from datetime import datetime
from typing import Any

from ...utils.path_utils import normalize_path_separators
from ..config.settings import LocalModelConfig
from .base import GenerationRequest, GenerationResult

# HuggingFace imports (availability checked by LocalAIProvider)
try:
    import torch

    # Import BitsAndBytesConfig separately to avoid mypy attr-defined error
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    BitsAndBytesConfig = transformers.BitsAndBytesConfig  # type: ignore[attr-defined]

    HF_AVAILABLE = True
except ImportError:
    # Type stubs for optional dependencies
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:
        from typing import Any

        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        # BitsAndBytesConfig already defined above
    else:
        torch = None  # type: ignore[assignment]
        AutoTokenizer = None  # type: ignore[assignment]
        AutoModelForCausalLM = None  # type: ignore[assignment]
        BitsAndBytesConfig = None  # type: ignore[assignment]

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
        self.device: str | None = None
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

        # Optimize PyTorch threading for CPU performance on Apple Silicon
        if device == "cpu" and torch is not None:
            # Set optimal thread count for Apple Silicon (fewer fat cores)
            optimal_threads = min(os.cpu_count() or 4, 6)
            torch.set_num_threads(optimal_threads)

            # Set environment variables for MKL/OpenMP
            os.environ["OMP_NUM_THREADS"] = str(optimal_threads)
            os.environ["MKL_NUM_THREADS"] = str(optimal_threads)

            logger.info(f"Optimized CPU threading: {optimal_threads} threads")

        logger.info(f"Loading model {self.config.model_name} on {device}...")
        try:
            self.device = device
            model_name = self.config.model_name

            start_time = time.time()

            # Get cross-platform cache directory
            cache_dir = self._get_cache_dir() if self.config.cache_enabled else None

            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name, trust_remote_code=True, cache_dir=cache_dir
            )

            # Configure model loading based on device and quantization settings
            model_kwargs = self._get_model_kwargs(device)

            # Load model with appropriate configuration
            self.model = AutoModelForCausalLM.from_pretrained(  # type: ignore[no-untyped-call]
                model_name, trust_remote_code=True, cache_dir=cache_dir, **model_kwargs
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
            logger.error("Model not loaded - call load_model() first")
            return GenerationResult(
                success=False, error="Model not loaded - call load_model() first"
            )

        start_time = time.time()

        try:
            # Create documentation prompt
            normalized_path = normalize_path_separators(str(request.source_file))
            logger.info(f"📝 GENERATION START for {normalized_path}")

            prompt_start = time.time()
            prompt = self._create_documentation_prompt(request)
            prompt_time = time.time() - prompt_start
            logger.info(
                f"📋 PROMPT READY - Length: {len(prompt)} chars, Time: {prompt_time:.2f}s"
            )

            # Generate content using AI model
            generated_text = self._generate_with_model(prompt)

            # Parse and structure the output
            structured_content = self._parse_generated_content(generated_text, request)

            # Validate template completion if template was provided
            template_validation_warnings = []
            if request.template_content and request.template_content.strip():
                main_content = structured_content.get("index.md", "")
                is_valid, missing_placeholders = self._validate_template_completion(
                    request.template_content, main_content
                )

                if not is_valid:
                    template_validation_warnings = [
                        f"Template placeholders not filled: {', '.join(missing_placeholders)}"
                    ]
                    logger.warning(
                        f"Template validation failed for {normalized_path}: missing {missing_placeholders}"
                    )
                else:
                    logger.info(f"Template validation passed for {normalized_path}")

            processing_time = int((time.time() - start_time) * 1000)
            self._generation_count += 1

            # Use normalized path for consistent logging across platforms
            logger.info(
                f"Generated documentation for {normalized_path} in {processing_time}ms"
            )

            metadata = {
                "provider": "local",
                "model": self.config.model_name,
                "processing_time_ms": processing_time,
                "generation_count": self._generation_count,
                "device": self.device,
                "platform": sys.platform,
                "source_file": normalized_path,
            }

            # Add validation warnings if any
            if template_validation_warnings:
                metadata["template_validation_warnings"] = template_validation_warnings

            return GenerationResult(
                success=True,
                content=structured_content,
                metadata=metadata,
            )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"Documentation generation failed: {e}")

            return GenerationResult(
                success=False,
                error=f"Generation failed: {e}",
                metadata={"processing_time_ms": processing_time},
            )

    def _create_documentation_prompt(self, request: GenerationRequest) -> str:
        """Create prompt for documentation generation.

        Args:
            request: Generation request with code content and optional template

        Returns:
            str: Formatted prompt for AI model
        """
        # Use normalized path for consistent behavior across platforms
        normalized_path = normalize_path_separators(str(request.source_file))
        file_extension = request.get_file_extension()
        language = self._detect_language(file_extension)

        # If template content is provided, use it as the primary prompt structure
        if request.template_content and request.template_content.strip():
            # Extract placeholders from template
            import re

            placeholders = re.findall(r"\{\{(\w+)\}\}", request.template_content)

            # Use much more content - Qwen2.5-Coder supports 32k context
            # Reserve ~2000 tokens for prompt and output, use ~14k chars for code
            max_code_chars = 14000
            code_content = request.content[:max_code_chars]

            # Create prompt with template structure
            prompt = f"""You are a technical documentation expert. Your task is to fill in a documentation template by replacing placeholder variables with appropriate content.

CODE TO ANALYZE:
```python
{code_content}
```

DOCUMENTATION TEMPLATE (COPY THIS EXACTLY AND FILL IN THE PLACEHOLDERS):
{request.template_content}

CRITICAL INSTRUCTIONS:
1. COPY the template structure exactly as shown above
2. Replace ONLY the placeholder variables {{{{variable_name}}}} with appropriate content
3. Do NOT change the markdown structure, headers, or formatting
4. Do NOT add new sections or remove existing ones
5. Do NOT use your own documentation format - use ONLY the template provided
6. Analyze the code to generate accurate content for each placeholder

Placeholder meanings:
{chr(10).join(f"- {{{{{p}}}}}: {self._get_field_description(p)}" for p in placeholders)}

IMPORTANT: Your response must be the completed template with all {{{{placeholders}}}} replaced by actual content. Do not include any other text or explanations."""

            # Reduce debug logging for speed
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(
                    f"Using template-based prompt for {normalized_path} with {len(placeholders)} placeholders"
                )
            return prompt

        # Fallback to default prompt if no template provided
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

        logger.info(f"Using default prompt for {normalized_path}")
        return prompt

    def _generate_with_model(self, prompt: str) -> str:
        """Generate text using the loaded AI model.

        Args:
            prompt: Input prompt for generation

        Returns:
            str: Generated text from model
        """
        # Tokenize input
        if self.tokenizer is None:
            raise RuntimeError("Tokenizer not loaded")

        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            truncation=True,
            max_length=16384,  # Increased for larger context - leave room for generation
        )

        if self.device != "cpu":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

        # Generate with model
        if torch is not None and self.model is not None:
            inference_start = time.time()

            with torch.no_grad():
                # Use optimized generation for speed
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=self.config.max_tokens,
                    do_sample=False,  # Use greedy decoding for speed
                    pad_token_id=self.tokenizer.eos_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    use_cache=True,  # Enable KV cache for faster generation
                )

            inference_time = time.time() - inference_start
            output_tokens = outputs[0].shape[0] - inputs["input_ids"].shape[1]

            # Reduce logging for speed
            if logger.isEnabledFor(logging.INFO):
                logger.info(
                    f"Generated {output_tokens} tokens in {inference_time:.1f}s ({output_tokens / inference_time:.1f} tok/s)"
                )
        else:
            # This should not happen in normal operation since model loading checks HF_AVAILABLE
            raise RuntimeError("PyTorch not available for model generation")

        # Decode output (remove input prompt)
        input_length = inputs["input_ids"].shape[1]
        generated_tokens = outputs[0][input_length:]

        # Decode generated tokens
        generated_text = self.tokenizer.decode(
            generated_tokens, skip_special_tokens=True
        )

        return generated_text.strip()

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
        # For now, put all content in index.md
        # Future enhancement could parse sections into separate files
        content = {"index.md": generated_text}

        # Generate history.md using template system
        normalized_path = normalize_path_separators(str(request.source_file))
        filename = os.path.basename(normalized_path)

        # Create simple history content for basic tracking
        content["history.md"] = f"""# Documentation History for {filename}

**Location**: {normalized_path}

## {datetime.now().strftime("%Y-%m-%d")} - Initial Creation

**Purpose**: AI-powered analysis using local model
**Context**: File documented with spec-cli
**Model**: {self.config.model_name}
**Platform**: {sys.platform}
"""

        return content

    def _get_model_kwargs(self, device: str) -> dict[str, Any]:
        """Get model loading arguments based on configuration.

        Args:
            device: Target device for model

        Returns:
            Dict[str, Any]: Model loading arguments
        """
        kwargs: dict[str, Any] = {}

        # Platform-specific device mapping
        if device == "cuda":
            kwargs["device_map"] = "auto"
        elif device == "mps" and sys.platform == "darwin":
            # Apple Silicon GPU handling
            kwargs["device_map"] = {"": "mps"}
        elif device != "cpu":
            kwargs["device_map"] = device

        # Platform-aware quantization for memory efficiency
        if self.config.use_4bit and device == "cuda" and BitsAndBytesConfig is not None:
            # 4-bit quantization only supported on CUDA
            kwargs["quantization_config"] = BitsAndBytesConfig(  # type: ignore[no-untyped-call]
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.float16,
                bnb_4bit_use_double_quant=True,
                bnb_4bit_quant_type="nf4",
            )
        elif torch is not None:
            # Platform-specific dtype selection with performance optimization
            if device == "cuda":
                kwargs["torch_dtype"] = torch.float16
            elif device == "mps":
                # MPS works better with float32 for compatibility
                kwargs["torch_dtype"] = torch.float32
            else:
                # CPU optimization: Use FP16 for significant speed improvement (73% faster)
                # 0.5B models benefit greatly from FP16 on CPU
                kwargs["torch_dtype"] = torch.float16

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
            ".php": "php",
        }

        return language_map.get(file_extension.lower(), "text")

    def _get_field_description(self, placeholder: str) -> str:
        """Get descriptive text for a template placeholder.

        Args:
            placeholder: Variable name from template

        Returns:
            Human-readable description of the variable
        """
        # Common variable descriptions
        descriptions = {
            "filename": "Source file name",
            "filepath": "File path location",
            "purpose": "Primary purpose or function of the code",
            "overview": "High-level overview of functionality",
            "description": "Detailed description",
            "author": "Author or creator name",
            "date": "Creation or modification date",
            "version": "Version or revision number",
            "content": "Main content or body",
            "summary": "Brief summary",
            "details": "Additional details",
            "notes": "Important notes or comments",
            "examples": "Usage examples",
            "example_usage": "Code usage examples",
            "references": "Related references or links",
            "related_docs": "Related documentation",
            "responsibilities": "Key responsibilities and capabilities",
            "dependencies": "Required dependencies and imports",
            "api_interface": "Public API and interface details",
            "configuration": "Configuration options and settings",
            "error_handling": "Error handling and exception management",
            "testing_notes": "Testing approaches and considerations",
            "performance_notes": "Performance characteristics and optimizations",
            "security_notes": "Security considerations and requirements",
            "future_enhancements": "Planned improvements and future features",
            "file_type": "Type of file or component",
            "file_extension": "File extension for code blocks",
        }

        # Try exact match first
        if placeholder in descriptions:
            return descriptions[placeholder]

        # Try partial matches for common patterns
        placeholder_lower = placeholder.lower()
        for key, desc in descriptions.items():
            if key in placeholder_lower or placeholder_lower in key:
                return desc

        # Generic description for unknown variables
        return f"Content for {placeholder.replace('_', ' ')}"

    def _validate_template_completion(
        self, template_content: str, generated_content: str
    ) -> tuple[bool, list[str]]:
        """Validate that AI output properly filled template placeholders.

        Args:
            template_content: Original template with placeholders
            generated_content: AI-generated content

        Returns:
            Tuple of (is_valid, list_of_missing_placeholders)
        """
        import re

        # Extract placeholders from original template
        template_placeholders = set(re.findall(r"\{\{(\w+)\}\}", template_content))

        # Find any remaining placeholders in generated content
        remaining_placeholders = set(re.findall(r"\{\{(\w+)\}\}", generated_content))

        # Check if all placeholders were filled
        unfilled_placeholders = template_placeholders.intersection(
            remaining_placeholders
        )

        is_valid = len(unfilled_placeholders) == 0
        missing_list = list(unfilled_placeholders)

        return is_valid, missing_list

    def _get_cache_dir(self) -> str | None:
        """Get cross-platform model cache directory.

        Returns:
            Optional[str]: Normalized cache directory path or None for default
        """
        if not self.config.cache_enabled:
            return None

        # Check if custom cache directory is configured
        if hasattr(self.config, "cache_dir") and self.config.cache_dir:
            # Use configured cache directory with cross-platform normalization
            return normalize_path_separators(self.config.cache_dir)

        # Use HuggingFace default cache directory (cross-platform)
        # HF_HOME or default ~/.cache/huggingface
        cache_dir = os.environ.get("HF_HOME")
        if cache_dir:
            return normalize_path_separators(cache_dir)

        # Platform-specific default cache directories
        if sys.platform == "win32":
            # Windows: %USERPROFILE%\.cache\huggingface
            default_cache = os.path.join(
                os.path.expanduser("~"), ".cache", "huggingface"
            )
        else:
            # Unix-like (macOS, Linux): ~/.cache/huggingface
            default_cache = os.path.join(
                os.path.expanduser("~"), ".cache", "huggingface"
            )

        return normalize_path_separators(default_cache)

    def cleanup(self) -> None:
        """Clean up loaded model resources with platform-specific optimizations."""
        self.model = None
        self.tokenizer = None

        # Platform-specific GPU memory cleanup
        if torch is not None and HF_AVAILABLE:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                logger.debug("Cleared CUDA cache")
            elif (
                sys.platform == "darwin"
                and hasattr(torch.backends, "mps")
                and torch.backends.mps.is_available()
            ):
                # Apple Silicon GPU cleanup if available
                try:
                    torch.mps.empty_cache()
                    logger.debug("Cleared MPS cache")
                except AttributeError:
                    # Fallback for older PyTorch versions
                    logger.debug("MPS cache clearing not available")
                    pass
