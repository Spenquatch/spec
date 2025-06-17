"""Tests for platform utilities."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from spec_cli.utils.platform_utils import (
    create_cross_platform_command,
    get_default_cache_dir,
    get_default_config_dir,
    get_environment_info,
    get_gpu_capabilities,
    get_platform_info,
    get_shell_command_separator,
    is_linux,
    is_macos,
    is_windows,
    normalize_executable_name,
    validate_system_requirements,
)


class TestPlatformDetection:
    """Test platform detection functions."""

    def test_get_platform_info_returns_dict(self):
        """Test that platform info returns expected structure."""
        info = get_platform_info()

        assert isinstance(info, dict)
        assert "platform" in info
        assert "os_name" in info
        assert "architecture" in info
        assert "python_version" in info
        assert "system" in info

    @patch("spec_cli.utils.platform_utils.sys.platform", "win32")
    def test_is_windows_detection(self):
        """Test Windows platform detection."""
        assert is_windows() is True
        assert is_macos() is False
        assert is_linux() is False

    @patch("spec_cli.utils.platform_utils.sys.platform", "darwin")
    def test_is_macos_detection(self):
        """Test macOS platform detection."""
        assert is_windows() is False
        assert is_macos() is True
        assert is_linux() is False

    @patch("spec_cli.utils.platform_utils.sys.platform", "linux")
    def test_is_linux_detection(self):
        """Test Linux platform detection."""
        assert is_windows() is False
        assert is_macos() is False
        assert is_linux() is True


class TestDirectoryUtils:
    """Test platform-specific directory utilities."""

    @patch("spec_cli.utils.platform_utils.sys.platform", "win32")
    @patch(
        "spec_cli.utils.platform_utils.os.environ",
        {"LOCALAPPDATA": "C:/Users/test/AppData/Local"},
    )
    def test_get_default_cache_dir_windows(self):
        """Test Windows cache directory."""
        cache_dir = get_default_cache_dir("test-app")
        expected = Path("C:/Users/test/AppData/Local/test-app/Cache")
        assert cache_dir == expected

    @patch("spec_cli.utils.platform_utils.sys.platform", "darwin")
    @patch("spec_cli.utils.platform_utils.Path.home")
    def test_get_default_cache_dir_macos(self, mock_home):
        """Test macOS cache directory."""
        mock_home.return_value = Path("/Users/test")
        cache_dir = get_default_cache_dir("test-app")
        expected = Path("/Users/test/Library/Caches/test-app")
        assert cache_dir == expected

    @patch("spec_cli.utils.platform_utils.sys.platform", "linux")
    @patch("spec_cli.utils.platform_utils.os.environ", {})
    @patch("spec_cli.utils.platform_utils.os.path.expanduser")
    def test_get_default_cache_dir_linux(self, mock_expanduser):
        """Test Linux cache directory."""
        mock_expanduser.return_value = "/home/test/.cache"
        cache_dir = get_default_cache_dir("test-app")
        expected = Path("/home/test/.cache/test-app")
        assert cache_dir == expected

    @patch("spec_cli.utils.platform_utils.sys.platform", "win32")
    @patch(
        "spec_cli.utils.platform_utils.os.environ",
        {"APPDATA": "C:/Users/test/AppData/Roaming"},
    )
    def test_get_default_config_dir_windows(self):
        """Test Windows config directory."""
        config_dir = get_default_config_dir("test-app")
        expected = Path("C:/Users/test/AppData/Roaming/test-app")
        assert config_dir == expected


class TestSystemValidation:
    """Test system requirements validation."""

    def test_validate_system_requirements_returns_dict(self):
        """Test that system validation returns expected structure."""
        results = validate_system_requirements()

        assert isinstance(results, dict)
        assert "valid" in results
        assert "platform_supported" in results
        assert "python_version_ok" in results
        assert "issues" in results
        assert "warnings" in results

    @patch("spec_cli.utils.platform_utils.sys.platform", "unsupported")
    def test_validate_system_requirements_unsupported_platform(self):
        """Test validation with unsupported platform."""
        results = validate_system_requirements()

        assert results["valid"] is False
        assert results["platform_supported"] is False
        assert any("Unsupported platform" in issue for issue in results["issues"])

    @patch("spec_cli.utils.platform_utils.sys.version_info", (3, 7, 0))
    def test_validate_system_requirements_old_python(self):
        """Test validation with old Python version."""
        results = validate_system_requirements()

        assert results["valid"] is False
        assert results["python_version_ok"] is False
        assert any("Python 3.7" in issue for issue in results["issues"])


class TestGPUCapabilities:
    """Test GPU capability detection."""

    def test_get_gpu_capabilities_no_torch(self):
        """Test GPU capabilities when torch is not available."""
        with patch.dict("sys.modules", {"torch": None}):
            capabilities = get_gpu_capabilities()

        assert capabilities["cuda_available"] is False
        assert capabilities["mps_available"] is False
        assert "PyTorch not available" in capabilities["recommendations"][0]

    def test_get_gpu_capabilities_with_mock_torch(self):
        """Test GPU capabilities with mocked torch."""
        mock_torch = MagicMock()
        mock_torch.cuda.is_available.return_value = False
        mock_torch.backends = MagicMock()
        mock_torch.backends.mps = MagicMock()
        mock_torch.backends.mps.is_available.return_value = False

        with patch.dict("sys.modules", {"torch": mock_torch}):
            capabilities = get_gpu_capabilities()

        assert isinstance(capabilities, dict)
        assert "cuda_available" in capabilities
        assert "mps_available" in capabilities


class TestExecutableUtils:
    """Test executable and command utilities."""

    @patch("spec_cli.utils.platform_utils.sys.platform", "win32")
    def test_normalize_executable_name_windows(self):
        """Test executable name normalization on Windows."""
        assert normalize_executable_name("python") == "python.exe"
        assert normalize_executable_name("python.exe") == "python.exe"

    @patch("spec_cli.utils.platform_utils.sys.platform", "linux")
    def test_normalize_executable_name_unix(self):
        """Test executable name normalization on Unix."""
        assert normalize_executable_name("python") == "python"
        assert normalize_executable_name("python.exe") == "python.exe"

    @patch("spec_cli.utils.platform_utils.sys.platform", "win32")
    def test_get_shell_command_separator_windows(self):
        """Test command separator on Windows."""
        assert get_shell_command_separator() == " & "

    @patch("spec_cli.utils.platform_utils.sys.platform", "linux")
    def test_get_shell_command_separator_unix(self):
        """Test command separator on Unix."""
        assert get_shell_command_separator() == " && "

    @patch("spec_cli.utils.platform_utils.sys.platform", "linux")
    def test_create_cross_platform_command_unix(self):
        """Test cross-platform command creation on Unix."""
        commands = ["echo hello", "echo world"]
        result = create_cross_platform_command(commands)
        assert result == "echo hello && echo world"

    @patch("spec_cli.utils.platform_utils.sys.platform", "win32")
    def test_create_cross_platform_command_windows(self):
        """Test cross-platform command creation on Windows."""
        commands = ["echo hello", "echo world"]
        result = create_cross_platform_command(commands)
        assert result == "echo hello & echo world"


class TestEnvironmentInfo:
    """Test environment information gathering."""

    def test_get_environment_info_returns_dict(self):
        """Test that environment info returns expected structure."""
        info = get_environment_info()

        assert isinstance(info, dict)
        assert "platform_info" in info
        assert "system_requirements" in info
        assert "gpu_capabilities" in info
        assert "relevant_env_vars" in info

        # Check that relevant environment variables are included
        env_vars = info["relevant_env_vars"]
        assert isinstance(env_vars, dict)
        # At least some environment variables should be present (even if None)
        assert "HOME" in env_vars or "USERPROFILE" in env_vars
