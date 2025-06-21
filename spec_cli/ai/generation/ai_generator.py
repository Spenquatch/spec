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

    def generate_documentation_from_request(
        self, request: GenerationRequest
    ) -> dict[str, Any]:
        """Generate documentation using a pre-configured GenerationRequest.

        Args:
            request: Generation request with template content and context

        Returns:
            Workflow result with generated documentation or error

        This method uses the template_content from the request as the AI prompt,
        allowing templates to directly control the AI generation process.
        """
        try:
            print("DEBUG: generate_documentation_from_request called")
            # Validate request has required content
            if not request.source_file.exists():
                return create_workflow_result(
                    success=False,
                    error=f"Target path does not exist: {request.source_file}",
                    data={"fallback_needed": True},
                )

            # Use template content as prompt if available, otherwise create default
            if request.template_content and request.template_content.strip():
                # Template-driven AI generation
                print(
                    "DEBUG: Using template-driven generation, calling provider.generate_documentation"
                )
                print(
                    f"DEBUG: About to call: {self.provider.__class__.__module__}.{self.provider.__class__.__name__}.generate_documentation"
                )
                generation_result = self.provider.generate_documentation(request)
                print(
                    f"DEBUG: Provider result: success={generation_result.success}, error={generation_result.error}"
                )
            else:
                # Fall back to default AI generation
                self.logger.warning(
                    "No template content provided, using default generation for %s",
                    request.get_normalized_path(),
                )
                generation_result = self.provider.generate_documentation(request)

            # Validate generation results
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
            main_content = generation_result.content.get("index.md", "")
            generated_docs = {
                str(request.source_file): main_content,
            }

            generation_metadata = {
                "provider_type": self.provider.__class__.__name__,
                "generation_time": datetime.now().isoformat(),
                "files_generated": len(generated_docs),
                "doc_type": request.doc_type,
                "source_file": request.get_normalized_path(),
                "content_length": len(main_content),
                "used_template_prompt": bool(request.template_content),
                "template_size": len(request.template_content or ""),
            }

            if generation_result.metadata:
                generation_metadata.update(generation_result.metadata)

            return create_workflow_result(
                success=True,
                data={
                    "generated_docs": generated_docs,
                    "generation_metadata": generation_metadata,
                },
                message=f"Generated {len(generated_docs)} documentation files using template-guided AI",
            )

        except Exception as e:
            self.logger.error(
                "Template-guided AI documentation generation failed: %s", e
            )
            return create_workflow_result(
                success=False,
                error=f"Template-guided AI generation failed: {str(e)}",
                data={"fallback_needed": True},
            )

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
            self.logger.info(
                f"AI generation result: success={generation_result.success}, content_keys={list(generation_result.content.keys()) if generation_result.content else None}, error={generation_result.error}"
            )

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


def generate_with_ai_request(
    request: GenerationRequest,
    ai_config_override: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate documentation using a pre-configured GenerationRequest.

    Args:
        request: Pre-configured generation request with template content
        ai_config_override: Optional configuration overrides

    Returns:
        Workflow result with generated documentation or error signal
    """
    try:
        # Load configuration (decision point + try/except)
        print("DEBUG: Loading AI configuration...")
        config_loader = AIConfigLoader()
        ai_config = config_loader.load_ai_config()
        print(
            f"DEBUG: AI config loaded: enabled={ai_config.enabled}, provider={ai_config.provider}"
        )

        if ai_config_override:
            # Apply overrides to configuration
            for key, value in ai_config_override.items():
                if hasattr(ai_config, key):
                    setattr(ai_config, key, value)

        # Get available provider (decision point)
        print("DEBUG: Creating ProviderManager...")
        provider_manager = ProviderManager(ai_config)
        print("DEBUG: Getting available provider...")
        provider = provider_manager.get_available_provider()
        print(
            f"DEBUG: Selected AI provider: {provider.__class__.__name__ if provider else 'None'}"
        )

        if not provider:
            return create_workflow_result(
                success=False,
                error="No AI provider available",
                data={"fallback_needed": True},
            )

        # Generate documentation using the request (decision point + try/except)
        print("DEBUG: Creating AIDocumentationGenerator...")
        print(
            f"DEBUG: Provider details: {provider.__class__.__module__}.{provider.__class__.__name__}"
        )
        generator = AIDocumentationGenerator(provider)
        print("DEBUG: Calling generate_documentation_from_request...")
        result = generator.generate_documentation_from_request(request)
        print(f"DEBUG: Generation result: success={result.get('success', False)}")

        # Log successful generation
        if result["success"]:
            logger.info(
                "AI documentation generation completed using template prompts",
                extra={
                    "target_path": request.get_normalized_path(),
                    "doc_type": request.doc_type,
                    "template_size": len(request.template_content or ""),
                    "has_template": request.template_content is not None,
                },
            )

        return result

    except Exception as e:  # try/except block
        logger.error("AI generation with template failed: %s", e)
        return create_workflow_result(
            success=False,
            error=f"AI generation with template failed: {str(e)}",
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
