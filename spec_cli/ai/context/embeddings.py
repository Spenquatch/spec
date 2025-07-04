"""Qwen3-Emb-0.6B embeddings generation for semantic search.

This module provides text embedding generation using the Qwen3-Emb-0.6B model
for semantic similarity search in documentation.
"""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from spec_cli.ai.config.loader import AIConfigLoader
from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.providers.manager import create_workflow_result
from spec_cli.utils.platform_utils import get_gpu_capabilities
from spec_cli.utils.workflow_utils import WorkflowResult

# Import dependencies at module level for proper testing and type checking
if TYPE_CHECKING:
    import torch as torch_module
    from transformers import AutoModel, AutoTokenizer

    TRANSFORMERS_AVAILABLE = True
else:
    try:
        import torch as torch_module
        from transformers import AutoModel, AutoTokenizer

        TRANSFORMERS_AVAILABLE = True
    except ImportError:
        # These will be None if transformers not available
        AutoModel = None  # type: ignore[misc,assignment]
        AutoTokenizer = None  # type: ignore[misc,assignment]
        torch_module = None  # type: ignore[assignment]
        TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate text embeddings using Qwen3-Emb-0.6B model."""

    def __init__(self, ai_config: AIConfig) -> None:
        """Initialize embedding generator with AI configuration.

        Args:
            ai_config: AI configuration settings
        """
        self.ai_config = ai_config
        self.device = self._select_device()
        self.model_name = "Qwen/Qwen3-Emb-0.6B"
        self.model: Any | None = None
        self.tokenizer: Any | None = None
        logger.info("Initialized EmbeddingGenerator with device: %s", self.device)

    def _select_device(self) -> str:
        """Select best available device for embedding generation.

        Returns:
            Device string: "cuda", "mps", or "cpu"
        """
        # Check GPU availability (decision point 1)
        gpu_info = get_gpu_capabilities()
        if gpu_info.get("cuda_available", False):
            logger.info("CUDA GPU detected, using GPU acceleration")
            return "cuda"
        elif gpu_info.get("mps_available", False):  # Apple Silicon
            logger.info("Apple Silicon GPU detected, using MPS acceleration")
            return "mps"
        else:
            logger.info("No GPU detected, using CPU for embeddings")
            return "cpu"

    def _load_model(self) -> bool:
        """Load Qwen3-Emb-0.6B model if not already loaded.

        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            if self.model is None:
                logger.info("Loading %s model on %s", self.model_name, self.device)

                # Check if transformers library is available
                if (
                    not TRANSFORMERS_AVAILABLE
                    or AutoTokenizer is None
                    or AutoModel is None
                ):
                    logger.error("Missing required dependencies: transformers")
                    logger.error("Install with: pip install transformers torch")
                    return False

                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                self.model = AutoModel.from_pretrained(  # type: ignore[no-untyped-call]
                    self.model_name,
                    trust_remote_code=True,
                    device_map=self.device if self.device != "cpu" else None,
                )
                if self.device == "cpu":
                    self.model = self.model.to("cpu")
                logger.info("Successfully loaded %s model", self.model_name)
            return True
        except Exception as e:
            logger.error("Failed to load embedding model: %s", e)
            return False

    def generate_embeddings(self, text: str) -> WorkflowResult:
        """Generate vector embeddings for text content using Qwen3-Emb-0.6B.

        Args:
            text: Input text to generate embeddings for

        Returns:
            WorkflowResult containing embeddings or error information
        """
        try:
            # Validate AI configuration (decision point 2)
            if not self.ai_config.enabled:
                return create_workflow_result(
                    success=False, error="AI embeddings disabled in configuration"
                )

            # Validate input
            if not text or not text.strip():
                return create_workflow_result(
                    success=False, error="Empty text provided for embedding generation"
                )

            # Load model if needed (decision point 3 + try/except)
            if not self._load_model():
                return create_workflow_result(
                    success=False, error="Failed to load Qwen3-Emb-0.6B embedding model"
                )

            # Check torch availability (imported at module level)
            if not TRANSFORMERS_AVAILABLE or torch_module is None:
                return create_workflow_result(
                    success=False,
                    error="PyTorch not available - install with: pip install torch",
                )

            # Generate embeddings using Qwen3-Emb-0.6B
            start_time = datetime.now()

            # Type check to ensure model and tokenizer are loaded
            if self.tokenizer is None or self.model is None:
                return create_workflow_result(
                    success=False, error="Model or tokenizer not loaded"
                )

            inputs = self.tokenizer(
                text, return_tensors="pt", truncation=True, max_length=512
            )
            if self.device != "cpu":
                inputs = {k: v.to(self.device) for k, v in inputs.items()}

            with torch_module.no_grad():
                outputs = self.model(**inputs)
                # Use mean pooling of last hidden states for sentence embedding
                embeddings = (
                    outputs.last_hidden_state.mean(dim=1).squeeze().cpu().numpy()
                )

            generation_time = (datetime.now() - start_time).total_seconds()

            return create_workflow_result(
                success=True,
                data={
                    "embeddings": embeddings.tolist(),
                    "text_length": len(text),
                    "device_used": self.device,
                    "model_name": self.model_name,
                    "embedding_dimension": len(embeddings),
                    "generation_time": generation_time,
                    "timestamp": datetime.now().isoformat(),
                },
                message=f"Generated embeddings on {self.device} using {self.model_name}",
            )

        except Exception as e:  # try/except block
            logger.error("Embedding generation failed: %s", e)
            return create_workflow_result(
                success=False, error=f"Embedding generation failed: {str(e)}"
            )


def generate_embeddings(text: str, ai_config: AIConfig | None = None) -> WorkflowResult:
    """Generate embeddings for text using default configuration.

    Args:
        text: Input text to generate embeddings for
        ai_config: Optional AI configuration, will load default if not provided

    Returns:
        WorkflowResult containing embeddings or error information
    """
    try:
        if ai_config is None:
            # Load default AI configuration
            config_loader = AIConfigLoader()
            ai_config = config_loader.load_ai_config()

        generator = EmbeddingGenerator(ai_config)
        return generator.generate_embeddings(text)

    except Exception as e:
        logger.error("Failed to initialize embedding generation: %s", e)
        return create_workflow_result(
            success=False, error=f"Failed to initialize embedding generation: {str(e)}"
        )
