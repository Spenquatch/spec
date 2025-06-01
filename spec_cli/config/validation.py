from pathlib import Path
from typing import Any, Dict, List

from ..exceptions import SpecConfigurationError


class ConfigurationValidator:
    """Validates configuration values and provides helpful error messages."""

    def validate_configuration(self, config: Dict[str, Any]) -> List[str]:
        """Validate configuration and return list of validation errors."""
        errors = []

        # Validate debug settings
        debug_config = config.get("debug", {})
        if debug_config:
            errors.extend(self._validate_debug_config(debug_config))

        # Validate terminal settings
        terminal_config = config.get("terminal", {})
        if terminal_config:
            errors.extend(self._validate_terminal_config(terminal_config))

        # Validate path settings
        path_config = config.get("paths", {})
        if path_config:
            errors.extend(self._validate_path_config(path_config))

        # Validate template settings
        template_config = config.get("template", {})
        if template_config:
            errors.extend(self._validate_template_config(template_config))

        return errors

    def _validate_debug_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate debug configuration section."""
        errors = []

        # Check debug level
        level = config.get("level")
        if level is not None:
            if not isinstance(level, str):
                errors.append(
                    f"debug.level must be a string, got {type(level).__name__}"
                )
            elif level.upper() not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
                errors.append(
                    f"Invalid debug level '{level}'. Must be one of: DEBUG, INFO, WARNING, ERROR"
                )

        # Check boolean values
        for key in ["enabled", "timing"]:
            value = config.get(key)
            if value is not None and not isinstance(value, bool):
                errors.append(
                    f"debug.{key} must be a boolean value, got {type(value).__name__}"
                )

        return errors

    def _validate_terminal_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate terminal configuration section."""
        errors = []

        # Check use_color
        use_color = config.get("use_color")
        if use_color is not None and not isinstance(use_color, bool):
            errors.append(
                f"terminal.use_color must be a boolean value, got {type(use_color).__name__}"
            )

        # Check console width
        width = config.get("console_width")
        if width is not None:
            if not isinstance(width, int):
                errors.append(
                    f"terminal.console_width must be an integer, got {type(width).__name__}"
                )
            elif width < 40:
                errors.append(
                    f"terminal.console_width must be at least 40, got {width}"
                )
            elif width > 1000:
                errors.append(
                    f"terminal.console_width must be at most 1000, got {width}"
                )

        return errors

    def _validate_path_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate path configuration section."""
        errors = []

        # Check root_path if specified
        root_path = config.get("root_path")
        if root_path is not None:
            if not isinstance(root_path, str):
                errors.append(
                    f"paths.root_path must be a string, got {type(root_path).__name__}"
                )
            else:
                path_obj = Path(root_path)
                if not path_obj.exists():
                    errors.append(f"Specified root_path does not exist: {root_path}")
                elif not path_obj.is_dir():
                    errors.append(
                        f"Specified root_path is not a directory: {root_path}"
                    )

        # Check template_file if specified
        template_file = config.get("template_file")
        if template_file is not None:
            if not isinstance(template_file, str):
                errors.append(
                    f"paths.template_file must be a string, got {type(template_file).__name__}"
                )

        return errors

    def _validate_template_config(self, config: Dict[str, Any]) -> List[str]:
        """Validate template configuration section."""
        errors = []

        # Check template sections
        for section in ["index", "history"]:
            value = config.get(section)
            if value is not None:
                if not isinstance(value, str):
                    errors.append(
                        f"template.{section} must be a string, got {type(value).__name__}"
                    )
                elif not value.strip():
                    errors.append(f"template.{section} cannot be empty")
                elif "{{filename}}" not in value:
                    errors.append(
                        f"template.{section} must contain {{{{filename}}}} placeholder"
                    )

        return errors

    def validate_and_raise(self, config: Dict[str, Any]) -> None:
        """Validate configuration and raise exception if invalid."""
        errors = self.validate_configuration(config)
        if errors:
            error_msg = "Configuration validation failed:\n" + "\n".join(
                f"  - {error}" for error in errors
            )
            raise SpecConfigurationError(
                error_msg,
                {"validation_errors": errors, "config_keys": list(config.keys())},
            )

    def get_validation_schema(self) -> Dict[str, Any]:
        """Get the expected configuration schema for documentation."""
        return {
            "debug": {
                "enabled": "boolean - Enable debug logging",
                "level": "string - One of: DEBUG, INFO, WARNING, ERROR",
                "timing": "boolean - Enable timing measurements",
            },
            "terminal": {
                "use_color": "boolean - Enable colored output",
                "console_width": "integer - Console width (40-1000)",
            },
            "paths": {
                "root_path": "string - Project root directory path",
                "template_file": "string - Custom template file path",
            },
            "template": {
                "index": "string - Template for index.md files",
                "history": "string - Template for history.md files",
            },
        }
