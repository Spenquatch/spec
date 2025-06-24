"""AI integration framework for template content generation.

This module provides the infrastructure for AI-powered content generation,
including abstract provider interfaces, retry mechanisms, placeholder providers
for testing, and a content manager for provider coordination.
"""

import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any

from ..ai.config.loader import AIConfigLoader
from ..ai.providers.base import GenerationRequest
from ..ai.providers.manager import ProviderManager
from ..config.loader import ConfigurationLoader
from ..config.settings import SpecSettings, get_settings
from ..exceptions import SpecTemplateError
from ..logging.debug import debug_logger


# Retry decorator with exponential backoff
def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
) -> Callable[..., Any]:
    """Retry AI API calls with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == max_retries:
                        debug_logger.log(
                            "ERROR",
                            "Max retries reached for AI call",
                            function=func.__name__,
                            attempts=attempt + 1,
                            error=str(e),
                        )
                        break

                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base**attempt), max_delay)

                    if jitter:
                        import random

                        delay *= 0.5 + random.random() * 0.5  # Add ±25% jitter

                    debug_logger.log(
                        "WARNING",
                        "AI call failed, retrying",
                        function=func.__name__,
                        attempt=attempt + 1,
                        delay=delay,
                        error=str(e),
                    )

                    time.sleep(delay)

            # Re-raise the last exception if all retries failed
            if last_exception:
                raise last_exception

        return wrapper

    return decorator


class AIContentProvider(ABC):
    """Abstract interface for AI content generation providers."""

    @abstractmethod
    def generate_content(
        self,
        file_path: Path,
        context: dict[str, Any],
        content_type: str,
        max_tokens: int = 1000,
    ) -> str:
        """Generate content for a specific context.

        Args:
            file_path: Path to the file being documented
            context: Context information about the file
            content_type: Type of content to generate (e.g., 'purpose', 'overview')
            max_tokens: Maximum tokens to generate

        Returns:
            Generated content string

        Raises:
            SpecTemplateError: If content generation fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if AI provider is available and configured."""
        pass

    @abstractmethod
    def get_supported_content_types(self) -> list[str]:
        """Get list of supported content types."""
        pass

    @abstractmethod
    def get_provider_info(self) -> dict[str, Any]:
        """Get information about this provider."""
        pass

    def validate_configuration(self) -> list[str]:
        """Validate provider configuration.

        Returns:
            List of configuration issues (empty if valid)
        """
        return []


# DEPRECATED: PlaceholderAIProvider removed - using new AI system in spec_cli/ai/


class MockAIProvider(AIContentProvider):
    """Mock AI provider for testing that can be configured with responses."""

    def __init__(self) -> None:
        """Initialize the mock AI provider.

        Sets up mock response storage and failure simulation capabilities.
        """
        self.responses: dict[str, str] = {}
        self.call_count = 0
        self.should_fail = False
        self.failure_message = "Mock AI provider failure"
        debug_logger.log("INFO", "MockAIProvider initialized")

    def set_response(self, content_type: str, response: str) -> None:
        """Set a mock response for a content type."""
        self.responses[content_type] = response
        debug_logger.log(
            "DEBUG",
            "Mock response set",
            content_type=content_type,
            response_length=len(response),
        )

    def set_failure(self, should_fail: bool, message: str = "Mock failure") -> None:
        """Configure the provider to simulate failures."""
        self.should_fail = should_fail
        self.failure_message = message
        debug_logger.log(
            "DEBUG",
            "Mock failure configured",
            should_fail=should_fail,
            failure_message=message,
        )

    @retry_with_backoff(max_retries=2, base_delay=0.1)  # Fast retries for testing
    def generate_content(
        self,
        file_path: Path,
        context: dict[str, Any],
        content_type: str,
        max_tokens: int = 1000,
    ) -> str:
        """Generate mock content or simulate failure."""
        self.call_count += 1

        debug_logger.log(
            "DEBUG",
            "Mock AI content generation",
            file_path=str(file_path),
            content_type=content_type,
            call_count=self.call_count,
        )

        if self.should_fail:
            raise SpecTemplateError(self.failure_message)

        if content_type in self.responses:
            return self.responses[content_type]

        # Default mock response
        return f"Mock AI generated content for {content_type} in {file_path.name}"

    def is_available(self) -> bool:
        """Mock provider availability."""
        return not self.should_fail

    def get_supported_content_types(self) -> list[str]:
        """Return supported types (all types for testing)."""
        return (
            list(self.responses.keys()) if self.responses else ["purpose", "overview"]
        )

    def get_provider_info(self) -> dict[str, Any]:
        """Get mock provider information."""
        return {
            "name": "MockProvider",
            "type": "mock",
            "description": "Mock provider for testing",
            "version": "1.0.0",
            "supports_async": False,
            "requires_api_key": False,
            "call_count": self.call_count,
        }

    def reset(self) -> None:
        """Reset mock state."""
        self.responses.clear()
        self.call_count = 0
        self.should_fail = False
        self.failure_message = "Mock AI provider failure"
        debug_logger.log("DEBUG", "Mock provider reset")


class AIContentManager:
    """Manages AI content generation with provider registration and fallback strategies."""

    def __init__(self, settings: SpecSettings | None = None):
        """Initialize the AI content manager.

        Args:
            settings: Optional spec settings (uses global settings if None)
        """
        self.settings = settings or get_settings()
        self.providers: dict[str, AIContentProvider] = {}

        # Load AI configuration
        try:
            # Use current working directory as root_path
            root_path = Path.cwd()
            config_loader = ConfigurationLoader(root_path)
            ai_config_loader = AIConfigLoader(config_loader)
            self.ai_config = ai_config_loader.load_ai_config()

            # Initialize ProviderManager
            self.provider_manager = ProviderManager(self.ai_config)

            # Enable AI if configured
            self.enabled = self.ai_config.enabled
        except Exception as e:
            # Fallback if AI config loading fails
            debug_logger.log(
                "WARNING",
                "Failed to load AI configuration, using defaults",
                error=str(e),
            )
            # Create minimal AI config
            from ..ai.config.settings import AIConfig

            self.ai_config = AIConfig(enabled=False, provider="disabled")
            self.provider_manager = ProviderManager(self.ai_config)
            self.enabled = False

        self.preferred_provider: str | None = None

        debug_logger.log(
            "INFO",
            "AIContentManager initialized with new AI system",
            enabled=self.enabled,
            provider=self.ai_config.provider if self.enabled else "disabled",
        )

    def register_provider(self, name: str, provider: AIContentProvider) -> None:
        """Register an AI content provider.

        Args:
            name: Name of the provider
            provider: AIContentProvider instance
        """
        self.providers[name] = provider
        debug_logger.log(
            "INFO",
            "AI provider registered",
            provider_name=name,
            provider_type=provider.get_provider_info().get("type", "unknown"),
        )

        # Set as preferred if it's the first available provider
        if self.preferred_provider is None and provider.is_available():
            self.preferred_provider = name
            debug_logger.log("INFO", "Set preferred AI provider", provider_name=name)

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable AI content generation."""
        self.enabled = enabled
        debug_logger.log("INFO", "AI content generation toggled", enabled=enabled)

    def set_preferred_provider(self, provider_name: str | None) -> bool:
        """Set the preferred AI provider.

        Args:
            provider_name: Name of the provider to prefer (None for auto-selection)

        Returns:
            True if provider was set, False if provider not found
        """
        if provider_name is None:
            self.preferred_provider = None
            debug_logger.log("INFO", "Cleared preferred AI provider")
            return True

        if provider_name in self.providers:
            self.preferred_provider = provider_name
            debug_logger.log(
                "INFO", "Set preferred AI provider", provider_name=provider_name
            )
            return True

        debug_logger.log(
            "WARNING",
            "Attempted to set unknown AI provider",
            provider_name=provider_name,
        )
        return False

    def generate_ai_content(
        self,
        file_path: Path,
        context: dict[str, Any],
        content_requests: list[str],
        max_tokens_per_request: int = 1000,
    ) -> dict[str, str]:
        """Generate AI content for multiple content types.

        Args:
            file_path: Path to the file being documented
            context: Context information
            content_requests: List of content types to generate
            max_tokens_per_request: Maximum tokens per content generation

        Returns:
            Dictionary mapping content types to generated content
        """
        debug_logger.log(
            "INFO",
            "Generating AI content",
            file_path=str(file_path),
            content_types=content_requests,
            enabled=self.enabled,
        )

        if not self.enabled:
            return {
                content_type: f"[{content_type.replace('_', ' ').title()} - AI disabled]"
                for content_type in content_requests
            }

        # Get available provider from ProviderManager or legacy providers
        provider = self.provider_manager.get_available_provider()
        legacy_provider = None

        debug_logger.log(
            "DEBUG",
            "Generate AI content start",
            enabled=self.enabled,
            provider_manager_result=bool(provider),
            legacy_provider_count=len(self.providers),
        )

        # Fall back to legacy providers if new system unavailable
        if not provider:
            legacy_provider = self._get_available_provider()
            debug_logger.log(
                "DEBUG",
                "Provider fallback check",
                has_new_provider=bool(provider),
                has_legacy_provider=bool(legacy_provider),
                legacy_provider_count=len(self.providers),
            )

            # If no available legacy providers but we have registered providers,
            # try them anyway and let them fail gracefully with fallback content
            if not legacy_provider and self.providers:
                legacy_provider = next(iter(self.providers.values()), None)
                debug_logger.log(
                    "DEBUG",
                    "Trying unavailable provider for fallback",
                    provider_count=len(self.providers),
                )

        if not provider and not legacy_provider:
            debug_logger.log(
                "WARNING", "No AI providers available, using template fallback"
            )
            return {
                content_type: f"[{content_type.replace('_', ' ').title()} - No AI provider available]"
                for content_type in content_requests
            }

        results = {}

        with debug_logger.timer("ai_content_generation"):
            # Read file content for the request
            try:
                file_content = file_path.read_text()
            except Exception as e:
                debug_logger.log(
                    "ERROR",
                    "Failed to read file content",
                    file_path=str(file_path),
                    error=str(e),
                )
                file_content = ""

            # Create GenerationRequest
            request = GenerationRequest(
                source_file=file_path,
                content=file_content,
                context=context,
                doc_type="comprehensive",
                template_content=None,
            )

            # Generate documentation using available provider
            try:
                if legacy_provider:
                    # Use legacy provider system
                    for content_type in content_requests:
                        try:
                            content = legacy_provider.generate_content(
                                file_path, context, content_type, max_tokens_per_request
                            )
                            results[content_type] = content
                        except Exception as e:
                            debug_logger.log(
                                "WARNING",
                                "Legacy AI content generation failed",
                                content_type=content_type,
                                error=str(e),
                            )
                            # Fallback to template placeholder content
                            results[content_type] = (
                                f"[{content_type.replace('_', ' ').title()} - AI-generated fallback content]"
                            )
                    return results

                # Use new provider system (provider is guaranteed to be non-None here)
                assert provider is not None  # For type checking
                result = provider.generate_documentation(request)

                if result.success:
                    # Convert GenerationResult to expected format
                    for content_type in content_requests:
                        if content_type == "purpose":
                            # Extract purpose from main content
                            main_content = result.get_main_content()
                            # Simple heuristic: first paragraph after overview
                            lines = main_content.split("\n")
                            purpose = ""
                            for i, line in enumerate(lines):
                                if line.strip().startswith("## Overview"):
                                    # Get next non-empty line
                                    for j in range(i + 1, len(lines)):
                                        if lines[j].strip():
                                            purpose = lines[j].strip()
                                            break
                                    break
                            results[content_type] = (
                                purpose or "Documentation generated by AI"
                            )
                        elif content_type == "overview":
                            # Extract overview section
                            main_content = result.get_main_content()
                            results[content_type] = (
                                self._extract_section(main_content, "## Overview")
                                or "## Overview\n\nAI-generated documentation"
                            )
                        else:
                            # For other content types, use main content
                            results[content_type] = result.get_main_content()

                    debug_logger.log(
                        "DEBUG",
                        "AI content generated successfully",
                        content_types_generated=len(results),
                    )
                else:
                    # Fallback for failed generation
                    debug_logger.log(
                        "WARNING",
                        "AI generation failed, using template fallback",
                        error=result.error,
                    )
                    results = {
                        content_type: f"[{content_type.replace('_', ' ').title()} - Generation failed: {result.error}]"
                        for content_type in content_requests
                    }

            except Exception as e:
                # Fallback to template for any errors
                debug_logger.log(
                    "WARNING",
                    "AI content generation failed with exception",
                    error=str(e),
                )
                results = {
                    content_type: f"[{content_type.replace('_', ' ').title()} - Error: {str(e)}]"
                    for content_type in content_requests
                }

        debug_logger.log(
            "INFO",
            "AI content generation complete",
            content_types_generated=len(results),
        )

        return results

    def _extract_section(self, content: str, section_header: str) -> str:
        """Extract a section from markdown content.

        Args:
            content: The full markdown content
            section_header: The section header to find (e.g., "## Overview")

        Returns:
            The section content or empty string if not found
        """
        lines = content.split("\n")
        section_lines = []
        in_section = False

        for line in lines:
            if line.strip() == section_header:
                in_section = True
                section_lines.append(line)
            elif in_section and line.strip().startswith("#"):
                # Stop at next section
                break
            elif in_section:
                section_lines.append(line)

        return "\n".join(section_lines) if section_lines else ""

    def _get_available_provider(self) -> AIContentProvider | None:
        """Get the best available AI provider."""
        # Try preferred provider first
        if self.preferred_provider and self.preferred_provider in self.providers:
            provider = self.providers[self.preferred_provider]
            if provider.is_available():
                return provider
            else:
                debug_logger.log(
                    "WARNING",
                    "Preferred provider not available",
                    provider_name=self.preferred_provider,
                )

        # Try any available provider
        for name, provider in self.providers.items():
            if provider.is_available():
                debug_logger.log(
                    "DEBUG", "Using available AI provider", provider_name=name
                )
                return provider

        return None

    def get_provider_status(self) -> dict[str, Any]:
        """Get status of all registered providers."""
        status: dict[str, Any] = {
            "enabled": self.enabled,
            "ai_provider": self.ai_config.provider if self.enabled else "disabled",
            "preferred_provider": self.preferred_provider,
            "providers": {},
        }

        # Get status from new provider system
        current_provider = self.provider_manager.get_available_provider()
        if current_provider:
            status["providers"]["current"] = {
                "available": True,
                "type": self.ai_config.provider,
                "name": current_provider.__class__.__name__,
            }
        else:
            status["providers"]["current"] = {
                "available": False,
                "type": self.ai_config.provider if self.enabled else "none",
            }

        # Legacy providers if any registered
        for name, legacy_provider in self.providers.items():
            try:
                provider_info = legacy_provider.get_provider_info()
                status["providers"][f"legacy_{name}"] = {
                    "available": legacy_provider.is_available(),
                    "info": provider_info,
                    "supported_types": len(
                        legacy_provider.get_supported_content_types()
                    ),
                }
            except Exception as e:
                status["providers"][f"legacy_{name}"] = {
                    "available": False,
                    "error": str(e),
                }

        return status

    def validate_configuration(self) -> list[str]:
        """Validate AI configuration and providers."""
        issues = []

        # Check new provider system
        if self.enabled:
            provider = self.provider_manager.get_available_provider()
            legacy_provider_available = any(
                p.is_available() for p in self.providers.values()
            )

            # Only report issues if neither new nor legacy providers are available
            if not provider and not legacy_provider_available:
                if not self.providers:
                    issues.append("No AI providers registered")
                else:
                    issues.append(
                        f"AI enabled but no provider available (configured: {self.ai_config.provider})"
                    )

        # Check legacy providers if any
        if self.providers:
            available_providers = []
            for name, legacy_provider in self.providers.items():
                try:
                    if legacy_provider.is_available():
                        available_providers.append(name)
                    else:
                        # Check for configuration issues
                        if hasattr(legacy_provider, "validate_configuration"):
                            provider_issues = legacy_provider.validate_configuration()
                            if provider_issues:
                                issues.extend(
                                    [
                                        f"legacy_{name}: {issue}"
                                        for issue in provider_issues
                                    ]
                                )
                except Exception as e:
                    issues.append(f"legacy_{name}: Error checking availability - {e}")

        # Check preferred provider specifically
        if self.enabled and self.preferred_provider:
            if self.preferred_provider in self.providers:
                preferred_provider = self.providers[self.preferred_provider]
                if not preferred_provider.is_available():
                    issues.append(
                        f"Preferred provider '{self.preferred_provider}' is not available"
                    )

        return issues

    def clear_providers(self) -> None:
        """Clear all registered providers (useful for testing)."""
        self.providers.clear()
        self.preferred_provider = None
        debug_logger.log("INFO", "All AI providers cleared")


# Global AI content manager instance
ai_content_manager = AIContentManager()


# Convenience function for ask_llm pattern
@retry_with_backoff(max_retries=3, base_delay=1.0)
def ask_llm(
    prompt: str,
    context: dict[str, Any] | None = None,
    max_tokens: int = 1000,
    provider_name: str | None = None,
) -> str:
    """Ask LLM a question with retry logic using new AI system.

    This function provides backwards compatibility for the ask_llm pattern
    while using the new provider system under the hood.

    Args:
        prompt: The prompt/question to send to the LLM
        context: Optional context information
        max_tokens: Maximum tokens to generate
        provider_name: Specific provider to use (None for default)

    Returns:
        Generated response string

    Raises:
        SpecTemplateError: If generation fails after retries
    """
    debug_logger.log(
        "INFO",
        "LLM query requested",
        prompt_length=len(prompt),
        context_provided=context is not None,
        provider=provider_name,
    )

    try:
        if not ai_content_manager.enabled:
            return "[LLM query disabled - enable AI to get generated responses]"

        # Get provider from new system
        provider = ai_content_manager.provider_manager.get_available_provider()
        if not provider:
            return "[No AI provider available - check configuration]"

        # Create a minimal GenerationRequest for the prompt
        # We'll use a dummy file path since this is a general query
        dummy_path = Path("query.txt")
        request = GenerationRequest(
            source_file=dummy_path,
            content=prompt,
            context=context or {},
            doc_type="query",
            template_content=None,
        )

        # Generate response using the provider
        result = provider.generate_documentation(request)

        if result.success:
            # Return the main content as the response
            return result.get_main_content() or "[AI generated empty response]"
        else:
            # Return error as placeholder
            return f"[AI query failed: {result.error}]"

    except Exception as e:
        error_msg = f"LLM query failed: {e}"
        debug_logger.log("ERROR", error_msg)
        raise SpecTemplateError(error_msg) from e
