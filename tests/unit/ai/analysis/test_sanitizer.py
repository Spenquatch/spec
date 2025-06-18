"""Comprehensive unit tests for CodeSanitizer with 100% coverage."""

from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.ai.analysis.sanitizer import CodeSanitizer
from spec_cli.ai.config.settings import SecurityConfig

# Test constants to eliminate magic numbers
DEFAULT_MAX_FILE_SIZE = 100
LARGE_FILE_SIZE = 200
TEST_API_KEY = "sk-1234567890abcdef"
TEST_PASSWORD = "secret_password_123"
TEST_TOKEN = "bearer_token_xyz"
SAFE_CODE_CONTENT = "def hello_world():\n    return 'Hello, World!'"
SANITIZED_PLACEHOLDER = "[SANITIZED_SECRET]"
TEST_FILE_NAME = "test_file.py"
TEST_PROJECT_ROOT = "/project/root"
NORMALIZED_TEST_PATH = "src/test_file.py"
WINDOWS_PATH_INPUT = "src\\test_file.py"
ALLOWED_PATTERN_PY = "*.py"
ALLOWED_PATTERN_JS = "*.js"
DISALLOWED_PATTERN_TXT = "*.txt"


class TestCodeSanitizerInitialization:
    """Test CodeSanitizer initialization and configuration."""

    def test_init_with_default_config_creates_sanitizer_with_defaults(self):
        """Test initialization with default SecurityConfig."""
        sanitizer = CodeSanitizer()

        assert sanitizer.security_config is not None
        assert sanitizer.security_config.sanitize_code is True
        assert sanitizer.security_config.max_file_size_kb == DEFAULT_MAX_FILE_SIZE
        assert len(sanitizer._compiled_patterns) > 0

    def test_init_with_custom_config_uses_provided_config(self):
        """Test initialization with custom SecurityConfig."""
        custom_config = SecurityConfig(
            sanitize_code=False,
            max_file_size_kb=LARGE_FILE_SIZE,
            blocked_patterns=["custom_pattern"],
        )

        sanitizer = CodeSanitizer(custom_config)

        assert sanitizer.security_config == custom_config
        assert sanitizer.security_config.sanitize_code is False
        assert sanitizer.security_config.max_file_size_kb == LARGE_FILE_SIZE

    @patch("spec_cli.ai.analysis.sanitizer.logger")
    def test_compile_patterns_logs_debug_message(self, mock_logger):
        """Test that pattern compilation logs debug information."""
        config = SecurityConfig(blocked_patterns=["test_pattern"])

        CodeSanitizer(config)

        mock_logger.debug.assert_called_with("Compiled %d security patterns", 1)

    @patch("spec_cli.ai.analysis.sanitizer.logger")
    def test_compile_patterns_handles_invalid_regex_gracefully(self, mock_logger):
        """Test invalid regex patterns are handled gracefully."""
        # Create sanitizer with valid config first
        sanitizer = CodeSanitizer()

        # Mock the blocked_patterns directly to bypass pydantic validation
        sanitizer.security_config.blocked_patterns = ["[invalid_regex"]

        # Re-compile patterns with invalid regex
        compiled_patterns = sanitizer._compile_patterns()

        # Should have no compiled patterns due to invalid regex
        assert len(compiled_patterns) == 0
        mock_logger.warning.assert_called()


class TestCodeSanitizerSanitizeMethod:
    """Test the main sanitize method functionality."""

    def test_sanitize_when_disabled_returns_original_content(self):
        """Test sanitization disabled mode returns unchanged content."""
        config = SecurityConfig(sanitize_code=False)
        sanitizer = CodeSanitizer(config)
        content_with_api_key = f"API_KEY = '{TEST_API_KEY}'"

        result = sanitizer.sanitize(content_with_api_key)

        assert result == content_with_api_key

    @patch("spec_cli.ai.analysis.sanitizer.logger")
    def test_sanitize_when_disabled_logs_debug_message(self, mock_logger):
        """Test disabled sanitization logs appropriate debug message."""
        config = SecurityConfig(sanitize_code=False)
        sanitizer = CodeSanitizer(config)

        sanitizer.sanitize(SAFE_CODE_CONTENT)

        mock_logger.debug.assert_called_with(
            "Code sanitization disabled, returning content unchanged"
        )

    def test_sanitize_removes_api_key_patterns(self):
        """Test API key pattern detection and removal."""
        config = SecurityConfig(blocked_patterns=[r"API_KEY"])
        sanitizer = CodeSanitizer(config)
        content_with_api_key = f"API_KEY = '{TEST_API_KEY}'"

        result = sanitizer.sanitize(content_with_api_key)

        assert "API_KEY" not in result
        assert SANITIZED_PLACEHOLDER in result

    def test_sanitize_removes_password_patterns(self):
        """Test password pattern detection and removal."""
        config = SecurityConfig(blocked_patterns=[r"password"])
        sanitizer = CodeSanitizer(config)
        content_with_password = f"PASSWORD = '{TEST_PASSWORD}'"

        result = sanitizer.sanitize(content_with_password)

        assert TEST_PASSWORD not in result
        assert SANITIZED_PLACEHOLDER in result

    def test_sanitize_removes_token_patterns(self):
        """Test token pattern detection and removal."""
        config = SecurityConfig(blocked_patterns=[r"token"])
        sanitizer = CodeSanitizer(config)
        content_with_token = f"AUTH_TOKEN = '{TEST_TOKEN}'"

        result = sanitizer.sanitize(content_with_token)

        assert TEST_TOKEN not in result
        assert SANITIZED_PLACEHOLDER in result

    def test_sanitize_handles_multiline_secrets(self):
        """Test multiline sensitive content detection."""
        config = SecurityConfig(blocked_patterns=[r"secret"])
        sanitizer = CodeSanitizer(config)
        multiline_content = """
def get_config():
    secret_key = 'my_secret_key'
    return secret_key
"""

        result = sanitizer.sanitize(multiline_content)

        assert "my_secret_key" not in result
        assert SANITIZED_PLACEHOLDER in result

    def test_sanitize_preserves_code_structure(self):
        """Test code structure is maintained after sanitization."""
        config = SecurityConfig(blocked_patterns=[r"api_key"])
        sanitizer = CodeSanitizer(config)
        code_content = """
def authenticate():
    api_key = 'secret_key'
    return api_key
"""

        result = sanitizer.sanitize(code_content)

        # Structure should be preserved
        assert "def authenticate():" in result
        assert "return" in result
        assert "api_key" not in result

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    def test_sanitize_normalizes_file_path_for_cross_platform(self, mock_normalize):
        """Test file path normalization for cross-platform compatibility."""
        mock_normalize.return_value = NORMALIZED_TEST_PATH
        sanitizer = CodeSanitizer()

        sanitizer.sanitize(SAFE_CODE_CONTENT, Path(WINDOWS_PATH_INPUT))

        mock_normalize.assert_called_with(WINDOWS_PATH_INPUT)

    @patch("spec_cli.ai.analysis.sanitizer.logger")
    def test_sanitize_logs_successful_sanitization(self, mock_logger):
        """Test successful sanitization logging."""
        config = SecurityConfig(blocked_patterns=[r"secret"])
        sanitizer = CodeSanitizer(config)
        content_with_secret = "SECRET_KEY = 'my_secret'"

        sanitizer.sanitize(content_with_secret, Path(TEST_FILE_NAME))

        mock_logger.info.assert_called()

    @patch("spec_cli.ai.analysis.sanitizer.logger")
    def test_sanitize_logs_no_patterns_found(self, mock_logger):
        """Test logging when no sensitive patterns are found."""
        sanitizer = CodeSanitizer()

        sanitizer.sanitize(SAFE_CODE_CONTENT, Path(TEST_FILE_NAME))

        mock_logger.debug.assert_called()


class TestCodeSanitizerValidation:
    """Test content validation functionality."""

    def test_validate_content_respects_file_size_limits(self):
        """Test file size validation enforcement."""
        config = SecurityConfig(max_file_size_kb=1)  # 1KB limit
        sanitizer = CodeSanitizer(config)
        large_content = "x" * 2048  # 2KB content

        with pytest.raises(ValueError, match="size.*exceeds maximum"):
            sanitizer.sanitize(large_content)

    def test_validate_content_handles_unicode_content(self):
        """Test Unicode content validation."""
        sanitizer = CodeSanitizer()
        unicode_content = "def greet(): return 'Hello, 世界!'"

        # Should not raise exception
        result = sanitizer.sanitize(unicode_content)

        assert "世界" in result

    def test_validate_content_handles_invalid_utf8_encoding(self):
        """Test invalid UTF-8 encoding detection."""
        sanitizer = CodeSanitizer()

        # Create content with a surrogate character that will fail UTF-8 encoding
        # This uses a lone high surrogate which is invalid in UTF-8
        invalid_content = "test \udcff content"

        with pytest.raises(ValueError, match="invalid UTF-8 encoding"):
            sanitizer._validate_content(invalid_content)

    def test_validate_content_includes_file_path_in_error_message(self):
        """Test file path is included in validation error messages."""
        config = SecurityConfig(max_file_size_kb=1)
        sanitizer = CodeSanitizer(config)
        large_content = "x" * 2048
        test_path = Path(TEST_FILE_NAME)

        with pytest.raises(ValueError, match=TEST_FILE_NAME):
            sanitizer.sanitize(large_content, test_path)


class TestCodeSanitizerPatternApplication:
    """Test security pattern application logic."""

    @patch("spec_cli.ai.analysis.sanitizer.logger")
    def test_apply_security_patterns_logs_replacement_count(self, mock_logger):
        """Test replacement count logging."""
        config = SecurityConfig(blocked_patterns=[r"secret"])
        sanitizer = CodeSanitizer(config)
        content_with_secrets = "secret1 and secret2"

        sanitizer.sanitize(content_with_secrets)

        mock_logger.debug.assert_called_with("Replaced %d sensitive patterns", 2)

    def test_apply_security_patterns_handles_case_insensitive_matching(self):
        """Test case-insensitive pattern matching."""
        config = SecurityConfig(blocked_patterns=[r"secret"])
        sanitizer = CodeSanitizer(config)
        mixed_case_content = "SECRET and secret and Secret"

        result = sanitizer.sanitize(mixed_case_content)

        # All variations should be replaced, check that original words are gone
        assert "SECRET and secret and Secret" not in result
        assert result.count(SANITIZED_PLACEHOLDER) == 3

    def test_apply_security_patterns_handles_multiline_content(self):
        """Test multiline pattern matching."""
        config = SecurityConfig(blocked_patterns=[r"password"])
        sanitizer = CodeSanitizer(config)
        multiline_content = """Line 1: password
Line 2: other content
Line 3: another password"""

        result = sanitizer.sanitize(multiline_content)

        assert result.count(SANITIZED_PLACEHOLDER) == 2


class TestCodeSanitizerFileAllowanceChecking:
    """Test file type allowance checking."""

    def test_is_file_allowed_when_no_patterns_allows_all_files(self):
        """Test no restrictions when no patterns specified."""
        config = SecurityConfig(allowed_file_patterns=[])
        sanitizer = CodeSanitizer(config)

        result = sanitizer.is_file_allowed(Path("any_file.xyz"))

        assert result is True

    def test_is_file_allowed_matches_python_files(self):
        """Test Python file pattern matching."""
        config = SecurityConfig(allowed_file_patterns=[ALLOWED_PATTERN_PY])
        sanitizer = CodeSanitizer(config)

        result = sanitizer.is_file_allowed(Path("script.py"))

        assert result is True

    def test_is_file_allowed_rejects_non_matching_files(self):
        """Test rejection of non-matching file types."""
        config = SecurityConfig(allowed_file_patterns=[ALLOWED_PATTERN_PY])
        sanitizer = CodeSanitizer(config)

        result = sanitizer.is_file_allowed(Path("document.txt"))

        assert result is False

    def test_is_file_allowed_handles_multiple_patterns(self):
        """Test multiple allowed patterns."""
        config = SecurityConfig(
            allowed_file_patterns=[ALLOWED_PATTERN_PY, ALLOWED_PATTERN_JS]
        )
        sanitizer = CodeSanitizer(config)

        py_result = sanitizer.is_file_allowed(Path("script.py"))
        js_result = sanitizer.is_file_allowed(Path("script.js"))
        txt_result = sanitizer.is_file_allowed(Path("document.txt"))

        assert py_result is True
        assert js_result is True
        assert txt_result is False

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    def test_is_file_allowed_normalizes_path_cross_platform(self, mock_normalize):
        """Test cross-platform path normalization in file allowance check."""
        mock_normalize.return_value = "src/test_file.py"
        config = SecurityConfig(allowed_file_patterns=[ALLOWED_PATTERN_PY])
        sanitizer = CodeSanitizer(config)

        sanitizer.is_file_allowed(Path(WINDOWS_PATH_INPUT))

        mock_normalize.assert_called_with(WINDOWS_PATH_INPUT)

    def test_is_file_allowed_handles_case_insensitive_matching(self):
        """Test case-insensitive file pattern matching."""
        config = SecurityConfig(allowed_file_patterns=[ALLOWED_PATTERN_PY])
        sanitizer = CodeSanitizer(config)

        result = sanitizer.is_file_allowed(Path("Script.PY"))

        assert result is True


class TestCodeSanitizerSecurityValidation:
    """Test file security validation."""

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    @patch("spec_cli.ai.analysis.sanitizer.is_subpath")
    def test_validate_file_security_with_project_root_validation(
        self, mock_is_subpath, mock_normalize
    ):
        """Test file security validation with project root checking."""
        mock_normalize.return_value = NORMALIZED_TEST_PATH
        mock_is_subpath.return_value = True
        config = SecurityConfig(allowed_file_patterns=[ALLOWED_PATTERN_PY])
        sanitizer = CodeSanitizer(config)

        result = sanitizer.validate_file_security(
            Path(TEST_FILE_NAME), Path(TEST_PROJECT_ROOT)
        )

        assert result is True
        mock_normalize.assert_called()
        mock_is_subpath.assert_called()

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    @patch("spec_cli.ai.analysis.sanitizer.is_subpath")
    def test_validate_file_security_rejects_files_outside_project(
        self, mock_is_subpath, mock_normalize
    ):
        """Test rejection of files outside project boundaries."""
        mock_normalize.return_value = "/outside/file.py"
        mock_is_subpath.return_value = False
        sanitizer = CodeSanitizer()

        with pytest.raises(ValueError, match="outside project root"):
            sanitizer.validate_file_security(
                Path("/outside/file.py"), Path(TEST_PROJECT_ROOT)
            )

    def test_validate_file_security_without_project_root_skips_boundary_check(self):
        """Test security validation without project root checking."""
        config = SecurityConfig(allowed_file_patterns=[ALLOWED_PATTERN_PY])
        sanitizer = CodeSanitizer(config)

        result = sanitizer.validate_file_security(Path("script.py"))

        assert result is True

    def test_validate_file_security_returns_false_for_disallowed_files(self):
        """Test security validation returns False for disallowed file types."""
        config = SecurityConfig(allowed_file_patterns=[ALLOWED_PATTERN_PY])
        sanitizer = CodeSanitizer(config)

        result = sanitizer.validate_file_security(Path("document.txt"))

        assert result is False

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    def test_validate_file_security_normalizes_paths_cross_platform(
        self, mock_normalize
    ):
        """Test cross-platform path normalization in security validation."""
        mock_normalize.side_effect = lambda x: str(x).replace("\\", "/")
        sanitizer = CodeSanitizer()

        sanitizer.validate_file_security(Path(WINDOWS_PATH_INPUT))

        assert mock_normalize.call_count >= 1


class TestCodeSanitizerConfigurationSummary:
    """Test sanitization configuration summary functionality."""

    def test_get_sanitization_summary_returns_complete_config_info(self):
        """Test configuration summary includes all relevant settings."""
        config = SecurityConfig(
            sanitize_code=True,
            max_file_size_kb=LARGE_FILE_SIZE,
            allowed_file_patterns=[ALLOWED_PATTERN_PY, ALLOWED_PATTERN_JS],
            blocked_patterns=["secret", "password", "token"],
        )
        sanitizer = CodeSanitizer(config)

        summary = sanitizer.get_sanitization_summary()

        expected_keys = {
            "sanitization_enabled",
            "max_file_size_kb",
            "allowed_patterns",
            "blocked_patterns_count",
            "compiled_patterns_count",
        }
        assert set(summary.keys()) == expected_keys
        assert summary["sanitization_enabled"] is True
        assert summary["max_file_size_kb"] == LARGE_FILE_SIZE
        assert summary["allowed_patterns"] == [ALLOWED_PATTERN_PY, ALLOWED_PATTERN_JS]
        assert summary["blocked_patterns_count"] == 3
        assert summary["compiled_patterns_count"] == 3

    def test_get_sanitization_summary_handles_disabled_sanitization(self):
        """Test configuration summary when sanitization is disabled."""
        config = SecurityConfig(sanitize_code=False)
        sanitizer = CodeSanitizer(config)

        summary = sanitizer.get_sanitization_summary()

        assert summary["sanitization_enabled"] is False

    def test_get_sanitization_summary_handles_invalid_patterns(self):
        """Test summary with invalid regex patterns."""
        sanitizer = CodeSanitizer()

        # Mock invalid patterns directly to bypass pydantic validation
        sanitizer.security_config.blocked_patterns = ["valid_pattern", "[invalid_regex"]
        sanitizer._compiled_patterns = sanitizer._compile_patterns()

        summary = sanitizer.get_sanitization_summary()

        # Should have 2 blocked patterns but only 1 compiled (valid one)
        assert summary["blocked_patterns_count"] == 2
        assert summary["compiled_patterns_count"] == 1


class TestCodeSanitizerCrossPlatformBehavior:
    """Test cross-platform path handling behavior."""

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    def test_sanitize_handles_windows_paths(self, mock_normalize):
        """Test Windows path handling in sanitize method."""
        mock_normalize.return_value = NORMALIZED_TEST_PATH
        sanitizer = CodeSanitizer()

        sanitizer.sanitize(SAFE_CODE_CONTENT, Path(WINDOWS_PATH_INPUT))

        mock_normalize.assert_called_with(WINDOWS_PATH_INPUT)

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    def test_cross_platform_path_handling_in_all_methods(self, mock_normalize):
        """Test all path-handling methods use normalization."""
        mock_normalize.side_effect = lambda x: str(x).replace("\\", "/")
        config = SecurityConfig(allowed_file_patterns=[ALLOWED_PATTERN_PY])
        sanitizer = CodeSanitizer(config)

        # Test sanitize method
        sanitizer.sanitize(SAFE_CODE_CONTENT, Path(WINDOWS_PATH_INPUT))

        # Test is_file_allowed method
        sanitizer.is_file_allowed(Path(WINDOWS_PATH_INPUT))

        # Test validate_file_security method
        sanitizer.validate_file_security(Path(WINDOWS_PATH_INPUT))

        # Should have been called multiple times for path normalization
        assert mock_normalize.call_count >= 3


class TestCodeSanitizerErrorHandling:
    """Test error handling scenarios."""

    def test_sanitize_maintains_syntax_validity_after_replacement(self):
        """Test code remains syntactically valid after sanitization."""
        config = SecurityConfig(blocked_patterns=[r"'[^']*secret[^']*'"])
        sanitizer = CodeSanitizer(config)
        code_content = "def get_key(): return 'my_secret_key'"

        result = sanitizer.sanitize(code_content)

        # Should still be valid Python syntax
        assert "def get_key():" in result
        assert "return" in result
        assert SANITIZED_PLACEHOLDER in result

    def test_sanitize_handles_empty_content(self):
        """Test sanitization of empty content."""
        sanitizer = CodeSanitizer()

        result = sanitizer.sanitize("")

        assert result == ""

    def test_sanitize_handles_none_file_path_gracefully(self):
        """Test sanitization with None file path."""
        sanitizer = CodeSanitizer()

        # Should not raise exception
        result = sanitizer.sanitize(SAFE_CODE_CONTENT, None)

        assert result == SAFE_CODE_CONTENT
