"""Platform-specific utilities for cross-platform compatibility."""

import logging
import os
import platform
import sys
from pathlib import Path
from typing import Any, TypedDict

logger = logging.getLogger(__name__)


class SystemRequirementsResult(TypedDict):
    """Type definition for system requirements validation result."""

    valid: bool
    platform_supported: bool
    python_version_ok: bool
    memory_sufficient: bool
    issues: list[str]
    warnings: list[str]


class GPUCapabilitiesResult(TypedDict):
    """Type definition for GPU capabilities result."""

    cuda_available: bool
    mps_available: bool
    gpu_memory_gb: float
    gpu_count: int
    recommendations: list[str]


def get_platform_info() -> dict[str, Any]:
    """Get comprehensive platform information.

    Returns:
        Dict[str, Any]: Platform information including OS, architecture, and capabilities
    """
    info = {
        "platform": sys.platform,
        "os_name": os.name,
        "architecture": platform.machine(),
        "python_version": platform.python_version(),
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
    }

    # Add platform-specific details
    if sys.platform == "darwin":
        info["macos_version"] = platform.mac_ver()[0]
    elif sys.platform == "win32":
        info["windows_version"] = platform.win32_ver()
    elif sys.platform.startswith("linux"):
        try:
            info["linux_distribution"] = platform.freedesktop_os_release()
        except OSError:
            info["linux_distribution"] = "unknown"

    return info


def is_windows() -> bool:
    """Check if running on Windows."""
    return sys.platform == "win32"


def is_macos() -> bool:
    """Check if running on macOS."""
    return sys.platform == "darwin"


def is_linux() -> bool:
    """Check if running on Linux."""
    return sys.platform.startswith("linux")


def get_default_cache_dir(app_name: str) -> Path:
    """Get platform-appropriate default cache directory.

    Args:
        app_name: Application name for cache directory

    Returns:
        Path: Platform-specific cache directory
    """
    if is_windows():
        # Windows: %USERPROFILE%\AppData\Local\{app_name}\Cache
        cache_base = os.environ.get(
            "LOCALAPPDATA", os.path.expanduser("~/AppData/Local")
        )
        return Path(cache_base) / app_name / "Cache"
    elif is_macos():
        # macOS: ~/Library/Caches/{app_name}
        return Path.home() / "Library" / "Caches" / app_name
    else:
        # Linux/Unix: ~/.cache/{app_name}
        cache_base = os.environ.get("XDG_CACHE_HOME", os.path.expanduser("~/.cache"))
        return Path(cache_base) / app_name


def get_default_config_dir(app_name: str) -> Path:
    """Get platform-appropriate default configuration directory.

    Args:
        app_name: Application name for config directory

    Returns:
        Path: Platform-specific config directory
    """
    if is_windows():
        # Windows: %APPDATA%\{app_name}
        config_base = os.environ.get("APPDATA", os.path.expanduser("~/AppData/Roaming"))
        return Path(config_base) / app_name
    elif is_macos():
        # macOS: ~/Library/Application Support/{app_name}
        return Path.home() / "Library" / "Application Support" / app_name
    else:
        # Linux/Unix: ~/.config/{app_name}
        config_base = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        return Path(config_base) / app_name


def validate_system_requirements() -> SystemRequirementsResult:
    """Validate system meets basic requirements for spec-cli.

    Returns:
        SystemRequirementsResult: Validation results with details
    """
    results: SystemRequirementsResult = {
        "valid": True,
        "platform_supported": True,
        "python_version_ok": True,
        "memory_sufficient": True,
        "issues": [],
        "warnings": [],
    }

    # Check platform support
    supported_platforms = ["darwin", "linux", "win32"]
    if sys.platform not in supported_platforms:
        results["platform_supported"] = False
        results["valid"] = False
        results["issues"].append(f"Unsupported platform: {sys.platform}")

    # Check Python version (3.8+)
    python_version = sys.version_info
    if python_version < (3, 8):
        results["python_version_ok"] = False
        results["valid"] = False
        results["issues"].append(
            f"Python {python_version[0]}.{python_version[1]} is not supported. Requires Python 3.8+"
        )

    # Check available memory (basic check)
    try:
        import psutil

        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 2:
            results["memory_sufficient"] = False
            results["warnings"].append(
                f"Low system memory: {memory_gb:.1f}GB. AI features may be limited."
            )
    except ImportError:
        results["warnings"].append("Cannot check system memory (psutil not available)")

    # Platform-specific checks
    if is_windows():
        # Check for Windows-specific requirements
        if python_version < (3, 9):
            results["warnings"].append(
                "Python 3.9+ recommended on Windows for better performance"
            )
    elif is_macos():
        # Check macOS version for Apple Silicon features
        try:
            macos_version = platform.mac_ver()[0]
            if macos_version and float(macos_version[:4]) < 11.0:
                results["warnings"].append(
                    "macOS 11+ recommended for Apple Silicon GPU support"
                )
        except (ValueError, TypeError):
            pass

    return results


def get_gpu_capabilities() -> GPUCapabilitiesResult:
    """Detect GPU capabilities across platforms.

    Returns:
        GPUCapabilitiesResult: GPU capability information
    """
    capabilities: GPUCapabilitiesResult = {
        "cuda_available": False,
        "mps_available": False,
        "gpu_memory_gb": 0,
        "gpu_count": 0,
        "recommendations": [],
    }

    try:
        import torch  # type: ignore[import-not-found]

        # CUDA detection (Windows/Linux)
        if torch.cuda.is_available():
            capabilities["cuda_available"] = True
            capabilities["gpu_count"] = torch.cuda.device_count()
            try:
                # Get memory of first GPU
                capabilities["gpu_memory_gb"] = torch.cuda.get_device_properties(
                    0
                ).total_memory / (1024**3)
            except Exception:
                pass
            capabilities["recommendations"].append(
                "CUDA GPU detected - local AI models will use GPU acceleration"
            )

        # MPS detection (macOS Apple Silicon)
        if (
            is_macos()
            and hasattr(torch.backends, "mps")
            and torch.backends.mps.is_available()
        ):
            capabilities["mps_available"] = True
            capabilities["recommendations"].append(
                "Apple Silicon GPU detected - local AI models will use Metal Performance Shaders"
            )

        # CPU fallback recommendations
        if not capabilities["cuda_available"] and not capabilities["mps_available"]:
            capabilities["recommendations"].append(
                "No GPU acceleration available - AI models will use CPU (slower)"
            )

    except ImportError:
        capabilities["recommendations"].append(
            "PyTorch not available - GPU detection skipped"
        )

    return capabilities


def get_environment_info() -> dict[str, Any]:
    """Get environment information for debugging.

    Returns:
        Dict[str, Any]: Environment variables and system info
    """
    return {
        "platform_info": get_platform_info(),
        "system_requirements": validate_system_requirements(),
        "gpu_capabilities": get_gpu_capabilities(),
        "relevant_env_vars": {
            "HOME": os.environ.get("HOME"),
            "USERPROFILE": os.environ.get("USERPROFILE"),
            "XDG_CACHE_HOME": os.environ.get("XDG_CACHE_HOME"),
            "XDG_CONFIG_HOME": os.environ.get("XDG_CONFIG_HOME"),
            "APPDATA": os.environ.get("APPDATA"),
            "LOCALAPPDATA": os.environ.get("LOCALAPPDATA"),
            "HF_HOME": os.environ.get("HF_HOME"),
            "TORCH_HOME": os.environ.get("TORCH_HOME"),
        },
    }


def normalize_executable_name(name: str) -> str:
    """Add platform-appropriate executable extension.

    Args:
        name: Base executable name

    Returns:
        str: Executable name with platform-appropriate extension
    """
    if is_windows() and not name.endswith(".exe"):
        return f"{name}.exe"
    return name


def get_shell_command_separator() -> str:
    """Get platform-appropriate command separator for shell commands.

    Returns:
        str: Command separator ("&&" for Unix-like, "&" for Windows cmd)
    """
    if is_windows():
        return " & "
    return " && "


def create_cross_platform_command(commands: list[str]) -> str:
    """Create a cross-platform shell command from a list of commands.

    Args:
        commands: List of shell commands

    Returns:
        str: Platform-appropriate combined command
    """
    separator = get_shell_command_separator()
    return separator.join(commands)
