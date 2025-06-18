"""AI-powered documentation generator using configured providers."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ..config.loader import AIConfigLoader
from ..providers.base import AIProvider, GenerationRequest
from ..providers.manager import ProviderManager, create_workflow_result

logger = logging.getLogger(__name__)


class AIDocumentationGenerator:
    """Generate documentation using AI providers with fallback handling."""

    def __init__(self, provider: AIProvider):
        """Initialize generator with AI provider.

        Args:
            provider: AI provider for documentation generation
        """
        self.provider = provider
        self.logger = logging.getLogger(__name__)

    def generate_documentation(
        self, target_path: Path, doc_type: str
    ) -> dict[str, Any]:
        """Generate documentation using AI provider.

        Args:
            target_path: Path to source file or directory
            doc_type: Type of documentation to generate

        Returns:
            Workflow result with generated documentation or error

        The generation process:
        1. Validate target path exists
        2. Read and prepare source content
        3. Generate documentation using AI provider
        4. Validate generation results
        5. Return structured results with metadata
        """
        try:
            # Validate target path (decision point 1)
            if not target_path.exists():
                return create_workflow_result(
                    success=False,
                    error=f"Target path does not exist: {target_path}",
                    data={"fallback_needed": True},
                )

            # Prepare source content for AI generation (decision point 2)
            if target_path.is_file():
                try:
                    content = target_path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    # Try with latin-1 fallback
                    try:
                        content = target_path.read_text(encoding="latin-1")
                    except Exception as e:
                        return create_workflow_result(
                            success=False,
                            error=f"Failed to read file content: {e}",
                            data={"fallback_needed": True},
                        )
            else:
                # For directories, create summary content
                content = f"Directory documentation request for: {target_path}"

            # Generate documentation using AI provider (decision point 3 + try/except)
            request = GenerationRequest(
                content=content,
                source_file=target_path,
                doc_type=doc_type,
                context={"generator": "ai", "doc_type": doc_type},
            )

            generation_result = self.provider.generate_documentation(request)

            # Validate generation results (decision point 4)
            if not generation_result.success or not generation_result.content:
                return create_workflow_result(
                    success=False,
                    error=(
                        generation_result.error
                        or "AI generation returned empty results"
                    ),
                    data={"fallback_needed": True},
                )

            # Structure generated content with metadata
            # Content is a dict mapping file types to content
            main_content = generation_result.content.get("index.md", "")
            generated_docs = {
                str(target_path): main_content,
            }
            content_length = len(main_content)

            generation_metadata = {
                "provider_type": self.provider.__class__.__name__,
                "generation_time": datetime.now().isoformat(),
                "files_generated": len(generated_docs),
                "doc_type": doc_type,
                "source_file": str(target_path),
                "content_length": content_length,
            }

            if generation_result.metadata:
                generation_metadata.update(generation_result.metadata)

            return create_workflow_result(
                success=True,
                data={
                    "generated_docs": generated_docs,
                    "generation_metadata": generation_metadata,
                },
                message=f"Generated {len(generated_docs)} documentation files using AI",
            )

        except Exception as e:  # try/except block
            self.logger.error("AI documentation generation failed: %s", e)
            return create_workflow_result(
                success=False,
                error=f"AI documentation generation failed: {str(e)}",
                data={"fallback_needed": True},
            )


def generate_with_ai(
    target_path: Path,
    doc_type: str,
    ai_config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Primary AI generation function with complete workflow management.

    Args:
        target_path: Path to source file or directory
        doc_type: Type of documentation to generate
        ai_config_override: Optional configuration overrides

    Returns:
        Workflow result with generated documentation or error signal

    This is the main entry point for AI-powered documentation generation.
    It handles configuration loading, provider selection, and generation
    with proper error handling and fallback signaling.
    """
    try:
        # Load configuration (decision point + try/except)
        config_loader = AIConfigLoader()
        ai_config = config_loader.load_ai_config()

        if ai_config_override:
            # Apply overrides to configuration
            for key, value in ai_config_override.items():
                if hasattr(ai_config, key):
                    setattr(ai_config, key, value)

        # Get available provider (decision point)
        provider_manager = ProviderManager(ai_config)
        provider = provider_manager.get_available_provider()

        if not provider:
            return create_workflow_result(
                success=False,
                error="No AI provider available",
                data={"fallback_needed": True},
            )

        # Generate documentation (decision point + try/except)
        generator = AIDocumentationGenerator(provider)
        result = generator.generate_documentation(target_path, doc_type)

        # Log successful generation
        if result["success"]:
            logger.info(
                "AI documentation generation completed",
                extra={
                    "target_path": str(target_path),
                    "doc_type": doc_type,
                    "files_generated": result["data"]["generation_metadata"][
                        "files_generated"
                    ],
                },
            )

        return result

    except Exception as e:  # try/except block
        logger.error("AI generation initialization failed: %s", e)
        return create_workflow_result(
            success=False,
            error=f"AI generation initialization failed: {str(e)}",
            data={"fallback_needed": True},
        )
