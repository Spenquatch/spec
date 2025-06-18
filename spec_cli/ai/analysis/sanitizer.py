"""Code sanitization for AI processing with configurable security patterns."""

import logging
import re
from pathlib import Path
from typing import Any

from ...utils.path_utils import is_subpath, normalize_path_separators
from ..config.settings import SecurityConfig

logger = logging.getLogger(__name__)


class CodeSanitizer:
    """Sanitize code content before AI processing to remove sensitive information."""

    def __init__(self, security_config: SecurityConfig | None = None):
        """Initialize with security configuration.

        Args:
            security_config: Security configuration (uses defaults if None)
        """
        self.security_config = security_config or SecurityConfig()
        self._compiled_patterns = self._compile_patterns()

    def sanitize(self, content: str, file_path: Path | None = None) -> str:
        """Sanitize code content by removing sensitive patterns.

        Args:
            content: Source code content to sanitize
            file_path: Optional file path for logging and validation (normalized for cross-platform)

        Returns:
            str: Sanitized content safe for AI processing

        Raises:
            ValueError: If content fails security validation
        """
        if not self.security_config.sanitize_code:
            logger.debug("Code sanitization disabled, returning content unchanged")
            return content

        # Normalize file path for cross-platform compatibility
        normalized_path = None
        if file_path is not None:
            normalized_path = Path(normalize_path_separators(str(file_path)))

        # Validate content before processing
        self._validate_content(content, normalized_path)

        # Apply security pattern replacements
        sanitized_content = self._apply_security_patterns(content)

        # Log sanitization results with normalized path
        display_path = normalized_path or "content"
        if sanitized_content != content:
            logger.info("Sanitized sensitive content in %s", display_path)
        else:
            logger.debug("No sensitive patterns found in %s", display_path)

        return sanitized_content

    def _validate_content(self, content: str, file_path: Path | None = None) -> None:
        """Validate content meets security requirements.

        Args:
            content: Content to validate
            file_path: Optional file path for error messages

        Raises:
            ValueError: If content fails validation
        """
        # Validate content is valid UTF-8 first
        try:
            encoded_content = content.encode("utf-8")
        except UnicodeEncodeError as e:
            raise ValueError(f"Content contains invalid UTF-8 encoding: {e}") from e

        # Check file size limits using already encoded content
        content_size_kb = len(encoded_content) / 1024
        if content_size_kb > self.security_config.max_file_size_kb:
            raise ValueError(
                f"File {file_path or 'content'} size {content_size_kb:.1f}KB exceeds "
                f"maximum {self.security_config.max_file_size_kb}KB"
            )

    def _apply_security_patterns(self, content: str) -> str:
        """Apply security pattern replacements to content.

        Args:
            content: Original content

        Returns:
            str: Content with sensitive patterns replaced
        """
        sanitized = content
        replacements_made = 0

        for pattern_regex in self._compiled_patterns:
            # Replace sensitive patterns with safe placeholder
            matches = pattern_regex.findall(sanitized)
            if matches:
                # Use a clear placeholder that indicates sanitization
                sanitized = pattern_regex.sub("[SANITIZED_SECRET]", sanitized)
                replacements_made += len(matches)

        if replacements_made > 0:
            logger.debug("Replaced %d sensitive patterns", replacements_made)

        return sanitized

    def _compile_patterns(self) -> list[re.Pattern[str]]:
        """Compile security patterns for efficient matching.

        Returns:
            List[re.Pattern[str]]: Compiled regex patterns
        """
        compiled_patterns = []

        for pattern_str in self.security_config.blocked_patterns:
            try:
                # Compile with case-insensitive and multiline flags
                compiled_pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                compiled_patterns.append(compiled_pattern)
            except re.error as e:
                logger.warning("Invalid regex pattern '%s': %s", pattern_str, e)

        logger.debug("Compiled %d security patterns", len(compiled_patterns))
        return compiled_patterns

    def is_file_allowed(self, file_path: Path) -> bool:
        """Check if file type is allowed for processing (cross-platform).

        Args:
            file_path: Path to check (normalized for cross-platform compatibility)

        Returns:
            bool: True if file is allowed for AI processing
        """
        if not self.security_config.allowed_file_patterns:
            return True  # No restrictions if no patterns specified

        # Normalize path for cross-platform compatibility
        normalized_path = Path(normalize_path_separators(str(file_path)))
        file_name = normalized_path.name

        for pattern in self.security_config.allowed_file_patterns:
            # Convert glob pattern to regex for matching
            regex_pattern = pattern.replace("*", ".*").replace("?", ".")
            if re.match(regex_pattern, file_name, re.IGNORECASE):
                return True

        return False

    def validate_file_security(
        self, file_path: Path, project_root: Path | None = None
    ) -> bool:
        """Validate file meets security requirements for processing.

        Args:
            file_path: Path to validate
            project_root: Optional project root for path validation

        Returns:
            bool: True if file is safe for processing

        Raises:
            ValueError: If file fails security validation
        """
        # Normalize paths for cross-platform compatibility
        normalized_file = Path(normalize_path_separators(str(file_path)))

        # Validate file is within project boundaries if project_root provided
        if project_root is not None:
            normalized_root = Path(normalize_path_separators(str(project_root)))
            if not is_subpath(normalized_file, normalized_root):
                raise ValueError(
                    f"File {normalized_file} is outside project root {normalized_root}"
                )

        # Check file type is allowed
        if not self.is_file_allowed(normalized_file):
            return False

        return True

    def get_sanitization_summary(self) -> dict[str, Any]:
        """Get summary of sanitization configuration.

        Returns:
            Dict[str, Any]: Summary of current sanitization settings
        """
        return {
            "sanitization_enabled": self.security_config.sanitize_code,
            "max_file_size_kb": self.security_config.max_file_size_kb,
            "allowed_patterns": self.security_config.allowed_file_patterns,
            "blocked_patterns_count": len(self.security_config.blocked_patterns),
            "compiled_patterns_count": len(self._compiled_patterns),
        }
