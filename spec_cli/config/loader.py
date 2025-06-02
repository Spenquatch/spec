import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

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

    def load_configuration(self) -> Dict[str, Any]:
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
                    raise SpecConfigurationError(
                        f"Failed to load configuration from {source}: {e}",
                        {"source_file": str(source), "error_type": type(e).__name__},
                    ) from e

        if not config:
            debug_logger.log("INFO", "No configuration files found, using defaults")

        return config

    def _load_from_file(self, file_path: Path) -> Dict[str, Any]:
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

    def _load_from_yaml(self, file_path: Path) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data or {}
        except yaml.YAMLError as e:
            raise SpecConfigurationError(
                f"Invalid YAML syntax in {file_path}: {e}",
                {"file_path": str(file_path), "yaml_error": str(e)},
            ) from e
        except UnicodeDecodeError as e:
            raise SpecConfigurationError(
                f"Unable to read {file_path} - file encoding issue: {e}",
                {"file_path": str(file_path), "encoding_error": str(e)},
            ) from e

    def _load_from_pyproject_toml(self, file_path: Path) -> Dict[str, Any]:
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
            raise SpecConfigurationError(
                f"Invalid TOML syntax in {file_path}: {e}",
                {"file_path": str(file_path), "toml_error": str(e)},
            ) from e
        except UnicodeDecodeError as e:
            raise SpecConfigurationError(
                f"Unable to read {file_path} - file encoding issue: {e}",
                {"file_path": str(file_path), "encoding_error": str(e)},
            ) from e

    def get_available_sources(self) -> List[Path]:
        """Get list of available configuration sources."""
        return [source for source in self.config_sources if source.exists()]

    def validate_source_syntax(self, source_path: Path) -> bool:
        """Validate syntax of configuration source without loading."""
        try:
            self._load_from_file(source_path)
            return True
        except SpecConfigurationError:
            return False
