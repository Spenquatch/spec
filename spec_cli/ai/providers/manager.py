"""AI provider management for selecting and configuring providers."""

import logging
from datetime import datetime
from typing import Any

from ..config.settings import AIConfig
from .base import AIProvider
from .local import LocalAIProvider

logger = logging.getLogger(__name__)


def create_workflow_result(
    success: bool,
    data: dict[str, Any] | None = None,
    error: str | None = None,
    message: str | None = None,
) -> dict[str, Any]:
    """Create standardized workflow result for AI operations.

    Args:
        success: Whether the operation succeeded
        data: Optional data payload for successful operations
        error: Optional error message for failed operations
        message: Optional success message

    Returns:
        Dictionary containing standardized workflow result

    Example:
        >>> result = create_workflow_result(True, {"docs": {"file.py": "content"}})
        >>> print(result["success"])  # True
    """
    result: dict[str, Any] = {
        "success": success,
        "timestamp": datetime.now().isoformat(),
    }

    if success:
        result["data"] = data or {}
        if message:
            result["message"] = message
    else:
        result["error"] = error or "Unknown error"
        result["data"] = data or {}

    return result


class ProviderManager:
    """Manage AI provider selection and availability."""

    def __init__(self, ai_config: AIConfig):
        """Initialize provider manager with AI configuration.

        Args:
            ai_config: AI configuration for provider selection
        """
        self.ai_config = ai_config
        self.logger = logging.getLogger(__name__)

    def get_available_provider(self) -> AIProvider | None:
        """Get best available AI provider with configuration validation.

        Returns:
            AIProvider instance if available, None otherwise

        The selection process:
        1. Check if AI is enabled in configuration
        2. Validate provider type configuration
        3. Check provider availability
        4. Return configured provider or None
        """
        try:
            # Validate configuration (decision point 1)
            if not self.ai_config.enabled:
                self.logger.debug("AI provider disabled in configuration")
                return None

            # Check provider availability (decision point 2)
            if self.ai_config.provider == "local":
                provider = LocalAIProvider(self.ai_config.local)
                if provider.is_available():
                    self.logger.info(
                        "Local AI provider available with model: %s",
                        self.ai_config.local.model_name,
                    )
                    return provider
                else:
                    self.logger.warning("Local AI provider not available")

            return None

        except Exception as e:  # try/except block
            self.logger.warning("Provider selection failed: %s", e)
            return None

    def get_provider_info(self) -> dict[str, Any]:
        """Get information about available providers.

        Returns:
            Dictionary with provider configuration and availability
        """
        info = {
            "ai_enabled": self.ai_config.enabled,
            "configured_provider": self.ai_config.provider,
            "provider_available": False,
            "provider_details": {},
        }

        provider = self.get_available_provider()
        if provider:
            info["provider_available"] = True
            info["provider_details"] = provider.get_provider_info()

        return info
