import sys
from pathlib import Path
from typing import Any

import yaml

from ..core.error_handler import ErrorHandler
from ..exceptions import SpecConfigurationError
from ..logging.debug import debug_logger

# Handle tomllib import for multiple Python versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]


class ConfigurationLoader:
    """Loads configuration from various sources with precedence handling."""

    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.config_sources = [
            root_path / ".specconfig.yaml",
            root_path / "pyproject.toml",
        ]
        self.error_handler = ErrorHandler({"component": "config_loader"})

    def load_configuration(self) -> dict[str, Any]:
        """Load configuration from available sources with precedence.

        Precedence order (later overrides earlier):
        1. .specconfig.yaml
        2. pyproject.toml [tool.spec] section
        3. Environment variables (handled in SpecSettings)
        """
        config = {}

        debug_logger.log(
            "INFO",
            "Loading configuration",
            sources=len(self.config_sources),
            root_path=str(self.root_path),
        )

        # Load from each source in order (later sources override earlier ones)
        for source in self.config_sources:
            if source.exists():
                try:
                    source_config = self._load_from_file(source)
                    if source_config:
                        config.update(source_config)
                        debug_logger.log(
                            "INFO",
                            "Loaded config from file",
                            source=str(source),
                            keys=list(source_config.keys()),
                        )
                except Exception as e:
                    self.error_handler.log_and_raise(
                        e,
                        "load configuration file",
                        reraise_as=SpecConfigurationError,
                        config_path=str(source),
                        config_loading="configuration_loading",
                    )

        if not config:
            debug_logger.log("INFO", "No configuration files found, using defaults")

        return config

    def _load_from_file(self, file_path: Path) -> dict[str, Any]:
        """Load configuration from a specific file."""
        if file_path.name == "pyproject.toml":
            return self._load_from_pyproject_toml(file_path)
        elif file_path.suffix in [".yaml", ".yml"]:
            return self._load_from_yaml(file_path)
        else:
            debug_logger.log(
                "WARNING", "Unknown config file type", file_path=str(file_path)
            )
            return {}

    def _load_from_yaml(self, file_path: Path) -> dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data or {}
        except yaml.YAMLError as e:
            self.error_handler.log_and_raise(
                e,
                "parse YAML configuration",
                reraise_as=SpecConfigurationError,
                file_path=str(file_path),
                yaml_parsing="yaml_syntax_error",
            )
            return {}  # This line will never be reached but satisfies mypy
        except UnicodeDecodeError as e:
            self.error_handler.log_and_raise(
                e,
                "read YAML configuration file",
                reraise_as=SpecConfigurationError,
                file_path=str(file_path),
                encoding_issue="unicode_decode_error",
            )
            return {}  # This line will never be reached but satisfies mypy

    def _load_from_pyproject_toml(self, file_path: Path) -> dict[str, Any]:
        """Load configuration from pyproject.toml [tool.spec] section."""
        if tomllib is None:
            debug_logger.log(  # type: ignore[unreachable]
                "WARNING", "No TOML parser available, skipping pyproject.toml"
            )
            return {}

        assert tomllib is not None  # For mypy

        try:
            with file_path.open("rb") as f:
                data = tomllib.load(f)

            # Extract [tool.spec] section
            tool_spec = data.get("tool", {}).get("spec", {})
            return tool_spec if isinstance(tool_spec, dict) else {}

        except tomllib.TOMLDecodeError as e:
            self.error_handler.log_and_raise(
                e,
                "parse TOML configuration",
                reraise_as=SpecConfigurationError,
                file_path=str(file_path),
                toml_parsing="toml_syntax_error",
            )
            return {}  # This line will never be reached but satisfies mypy
        except UnicodeDecodeError as e:
            self.error_handler.log_and_raise(
                e,
                "read TOML configuration file",
                reraise_as=SpecConfigurationError,
                file_path=str(file_path),
                encoding_issue="unicode_decode_error",
            )
            return {}  # This line will never be reached but satisfies mypy

    def get_available_sources(self) -> list[Path]:
        """Get list of available configuration sources."""
        return [source for source in self.config_sources if source.exists()]

    def validate_source_syntax(self, source_path: Path) -> bool:
        """Validate syntax of configuration source without loading."""
        try:
            self._load_from_file(source_path)
            return True
        except SpecConfigurationError:
            return False
