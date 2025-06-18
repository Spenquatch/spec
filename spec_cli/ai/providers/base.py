"""Abstract base class and data structures for AI documentation providers."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ...utils.path_utils import normalize_path_separators

logger = logging.getLogger(__name__)


@dataclass
class GenerationRequest:
    """Request for AI-powered documentation generation."""

    source_file: Path
    content: str
    context: dict[str, Any] = field(default_factory=dict)
    doc_type: str = "comprehensive"
    template_content: str | None = None

    def __post_init__(self) -> None:
        """Validate request after initialization with cross-platform path handling."""
        if not self.source_file:
            raise ValueError("source_file is required")
        if not self.content:
            raise ValueError("content cannot be empty")
        if not isinstance(self.context, dict):
            raise ValueError("context must be a dictionary")

        # Normalize source file path for cross-platform compatibility
        self.source_file = Path(normalize_path_separators(str(self.source_file)))

    def get_file_extension(self) -> str:
        """Get file extension for language-specific processing (cross-platform)."""
        # Use normalized path to ensure consistent behavior across platforms
        normalized_path = Path(normalize_path_separators(str(self.source_file)))
        return normalized_path.suffix.lower()

    def get_content_size(self) -> int:
        """Get content size in characters."""
        return len(self.content)

    def get_normalized_path(self) -> str:
        """Get normalized path string for cross-platform compatibility."""
        return normalize_path_separators(str(self.source_file))


@dataclass
class GenerationResult:
    """Result of AI documentation generation."""

    success: bool
    content: dict[str, str] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    processing_time_ms: int | None = None

    def __post_init__(self) -> None:
        """Validate result after initialization."""
        if self.success and not self.content:
            raise ValueError("Successful result must have content")
        if not self.success and not self.error:
            raise ValueError("Failed result must have error message")

    def get_main_content(self) -> str:
        """Get the main documentation content."""
        return self.content.get("index.md", "")

    def get_history_content(self) -> str:
        """Get the history documentation content."""
        return self.content.get("history.md", "")

    def has_complete_documentation(self) -> bool:
        """Check if result contains complete documentation."""
        return "index.md" in self.content and len(self.get_main_content().strip()) > 0


class AIProvider(ABC):
    """Abstract base class for AI documentation providers."""

    def __init__(self) -> None:
        """Initialize provider with logging."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured.

        Returns:
            bool: True if provider can process requests
        """
        pass

    @abstractmethod
    def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate documentation for source code.

        Args:
            request: Documentation generation request

        Returns:
            GenerationResult: Documentation generation result
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up provider resources.

        Should be called when provider is no longer needed.
        """
        pass

    def validate_request(self, request: GenerationRequest) -> None:
        """Validate generation request.

        Args:
            request: Request to validate

        Raises:
            ValueError: If request is invalid
        """
        if not isinstance(request, GenerationRequest):
            raise ValueError("request must be a GenerationRequest instance")

        # Additional validation can be added by subclasses
        # Use normalized path for consistent logging across platforms
        normalized_path = request.get_normalized_path()
        self.logger.debug("Validating request for %s", normalized_path)

    def get_provider_info(self) -> dict[str, Any]:
        """Get provider information.

        Returns:
            Dict[str, Any]: Provider metadata
        """
        return {
            "provider_class": self.__class__.__name__,
            "available": self.is_available(),
            "supports_cleanup": hasattr(self, "cleanup"),
        }
