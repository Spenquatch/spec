# Slice 1c: Code Sanitization System

## Goal
Implement secure code sanitization for AI processing using configurable patterns and file size limits.

## Scope
- Code sanitization for security before AI processing
- Configurable pattern matching for sensitive content
- File size and content validation
- Integration with SecurityConfig from slice 1a

## Files to Create (≤3)
- `spec_cli/ai/analysis/sanitizer.py` (≤130 lines, complexity ≤7)

## Classes/Services (≤2)
1. **CodeSanitizer** - Handles code sanitization with configurable security patterns

## McCabe Complexity (≤7 per function)
- **sanitize()**: ≤6 decision points (file size check, pattern matching, encoding handling)
- **_apply_security_patterns()**: ≤5 decision points (pattern iteration, replacement logic)
- **_validate_content()**: ≤4 decision points (size check, encoding validation)

## External Integrations (≤1)
- **0 external integrations** - Pure text processing and validation

## Implementation

```python
# spec_cli/ai/analysis/sanitizer.py
import re
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from ..config.settings import SecurityConfig

logger = logging.getLogger(__name__)

class CodeSanitizer:
    """Sanitize code content before AI processing to remove sensitive information."""

    def __init__(self, security_config: Optional[SecurityConfig] = None):
        """Initialize with security configuration.

        Args:
            security_config: Security configuration (uses defaults if None)
        """
        self.security_config = security_config or SecurityConfig()
        self._compiled_patterns = self._compile_patterns()

    def sanitize(self, content: str, file_path: Optional[Path] = None) -> str:
        """Sanitize code content by removing sensitive patterns.

        Args:
            content: Source code content to sanitize
            file_path: Optional file path for logging and validation

        Returns:
            str: Sanitized content safe for AI processing

        Raises:
            ValueError: If content fails security validation
        """
        if not self.security_config.sanitize_code:
            logger.debug("Code sanitization disabled, returning content unchanged")
            return content

        # Validate content before processing
        self._validate_content(content, file_path)

        # Apply security pattern replacements
        sanitized_content = self._apply_security_patterns(content)

        # Log sanitization results
        if sanitized_content != content:
            logger.info(f"Sanitized sensitive content in {file_path or 'content'}")
        else:
            logger.debug(f"No sensitive patterns found in {file_path or 'content'}")

        return sanitized_content

    def _validate_content(self, content: str, file_path: Optional[Path] = None) -> None:
        """Validate content meets security requirements.

        Args:
            content: Content to validate
            file_path: Optional file path for error messages

        Raises:
            ValueError: If content fails validation
        """
        # Check file size limits
        content_size_kb = len(content.encode('utf-8')) / 1024
        if content_size_kb > self.security_config.max_file_size_kb:
            raise ValueError(
                f"File {file_path or 'content'} size {content_size_kb:.1f}KB exceeds "
                f"maximum {self.security_config.max_file_size_kb}KB"
            )

        # Validate content is valid UTF-8
        try:
            content.encode('utf-8')
        except UnicodeEncodeError as e:
            raise ValueError(f"Content contains invalid UTF-8 encoding: {e}")

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
            logger.debug(f"Replaced {replacements_made} sensitive patterns")

        return sanitized

    def _compile_patterns(self) -> List[re.Pattern]:
        """Compile security patterns for efficient matching.

        Returns:
            List[re.Pattern]: Compiled regex patterns
        """
        compiled_patterns = []

        for pattern_str in self.security_config.blocked_patterns:
            try:
                # Compile with case-insensitive and multiline flags
                compiled_pattern = re.compile(pattern_str, re.IGNORECASE | re.MULTILINE)
                compiled_patterns.append(compiled_pattern)
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern_str}': {e}")

        logger.debug(f"Compiled {len(compiled_patterns)} security patterns")
        return compiled_patterns

    def is_file_allowed(self, file_path: Path) -> bool:
        """Check if file type is allowed for processing.

        Args:
            file_path: Path to check

        Returns:
            bool: True if file is allowed for AI processing
        """
        if not self.security_config.allowed_file_patterns:
            return True  # No restrictions if no patterns specified

        file_name = file_path.name

        for pattern in self.security_config.allowed_file_patterns:
            # Convert glob pattern to regex for matching
            regex_pattern = pattern.replace("*", ".*").replace("?", ".")
            if re.match(regex_pattern, file_name, re.IGNORECASE):
                return True

        return False

    def get_sanitization_summary(self) -> Dict[str, Any]:
        """Get summary of sanitization configuration.

        Returns:
            Dict[str, Any]: Summary of current sanitization settings
        """
        return {
            "sanitization_enabled": self.security_config.sanitize_code,
            "max_file_size_kb": self.security_config.max_file_size_kb,
            "allowed_patterns": self.security_config.allowed_file_patterns,
            "blocked_patterns_count": len(self.security_config.blocked_patterns),
            "compiled_patterns_count": len(self._compiled_patterns)
        }
```

## Inputs - EXPLICIT
- **content: str** - Source code content to sanitize (required)
- **file_path: Optional[Path]** - File path for logging and validation context
- **security_config: Optional[SecurityConfig]** - Configuration from slice 1a (uses defaults if None)

## Actions - UNAMBIGUOUS
1. Validate content meets security requirements (file size, encoding)
2. Apply configured security pattern replacements using compiled regex patterns
3. Replace sensitive patterns with clear "[SANITIZED_SECRET]" placeholder
4. Log sanitization activity for security audit trail
5. Provide file type filtering based on allowed patterns

## Outputs - WELL-DEFINED
- **Success**: Sanitized content string safe for AI processing
- **Validation failure**: ValueError with specific validation failure reason
- **Logging**: Info/debug messages about sanitization activity for security audit
- **Summary data**: Dictionary with sanitization configuration details

## Helper Dependencies
- **Existing helpers**: None required (uses standard library for regex and file operations)
- **Slice dependencies**: SecurityConfig from slice 1a for configuration
- **Standard library**: `re`, `logging`, `pathlib` for pattern matching and file handling

## Individual Test Scenarios (100% coverage achievable)
1. **test_sanitizer_removes_api_keys** - Test API key pattern detection and removal
2. **test_sanitizer_removes_passwords** - Test password pattern detection
3. **test_sanitizer_handles_multiline_secrets** - Test multiline sensitive content
4. **test_sanitizer_preserves_code_structure** - Verify code structure maintained after sanitization
5. **test_sanitizer_respects_file_size_limits** - Test file size validation
6. **test_sanitizer_handles_unicode_content** - Test Unicode text handling
7. **test_sanitizer_maintains_syntax_validity** - Verify code remains syntactically valid
8. **test_sanitizer_handles_disabled_mode** - Test when sanitization is disabled
9. **test_sanitizer_validates_allowed_file_patterns** - Test file type filtering
10. **test_sanitizer_handles_invalid_regex_patterns** - Test invalid pattern handling
11. **test_sanitizer_provides_configuration_summary** - Test configuration reporting
12. **test_sanitizer_logs_sanitization_activity** - Test security audit logging

## Quality Assurance
- **Poetry compliance**: No new dependencies, uses standard library
- **Type safety**: Complete type annotations for all functions
- **Security clearance**: Designed specifically for security - removes sensitive content
- **Performance**: Compiled regex patterns for efficient repeated use

## Integration with Other Slices
- **Depends on Slice 1a**: Uses SecurityConfig for configuration
- **Used by AI provider slices**: All AI providers will use this for content sanitization
- **Interface**: Provides CodeSanitizer class for import by AI processing components

## Delivery Requirements
- **Independent execution**: Can be implemented after slice 1a completion
- **Security focused**: Primary purpose is to enhance AI processing security
- **Audit trail**: Comprehensive logging for security compliance
- **Configurable**: Respects all SecurityConfig settings from slice 1a

## Quality Gates
```bash
poetry run pytest tests/unit/ai/analysis/test_sanitizer.py -v --cov=spec_cli.ai.analysis.sanitizer --cov-fail-under=100
poetry run mypy spec_cli/ai/analysis/sanitizer.py --strict
poetry run ruff check spec_cli/ai/analysis/sanitizer.py
```

## Status
**READY for single AI agent implementation** - All granularity and quality limits met individually.
**Dependency**: Requires slice 1a completion (SecurityConfig models).
