"""Configuration management for spec CLI.

This package provides centralized settings management with environment variable
support, file loading, and Rich terminal console integration.
"""

from .settings import (
    SpecSettings,
    SettingsManager,
    get_settings,
    get_console,
)
from .loader import ConfigurationLoader
from .validation import ConfigurationValidator

__all__ = [
    "SpecSettings",
    "SettingsManager",
    "get_settings",
    "get_console",
    "ConfigurationLoader",
    "ConfigurationValidator",
]