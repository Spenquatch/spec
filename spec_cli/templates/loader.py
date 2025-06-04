import os
from pathlib import Path
from typing import Any

import yaml

from ..config.settings import SpecSettings, get_settings
from ..exceptions import SpecTemplateError
from ..logging.debug import debug_logger
from ..utils.path_utils import ensure_directory, normalize_path
from .config import TemplateConfig, TemplateValidator
from .defaults import get_default_template_config


class TemplateLoader:
    """Loads template configuration from files with fallback to defaults."""

    def __init__(self, settings: SpecSettings | None = None):
        self.settings = settings or get_settings()
        self.validator = TemplateValidator()
        debug_logger.log(
            "INFO",
            "TemplateLoader initialized",
            template_file=str(self.settings.template_file),
        )

    def load_template(self) -> TemplateConfig:
        """Load template configuration from .spectemplate file or use defaults.

        Returns:
            TemplateConfig instance

        Raises:
            SpecTemplateError: If template loading or validation fails
        """
        debug_logger.log("INFO", "Loading template configuration")

        template_file = self.settings.template_file

        # Use defaults if no template file exists
        if not template_file.exists():
            debug_logger.log(
                "INFO",
                "No .spectemplate file found, using defaults",
                template_file=str(template_file),
            )
            return get_default_template_config()

        # Load from file
        try:
            with debug_logger.timer("load_template_file"):
                config = self._load_from_file(template_file)

            # Validate loaded configuration
            with debug_logger.timer("validate_template_config"):
                self.validator.validate_and_raise(config)

            debug_logger.log(
                "INFO",
                "Template configuration loaded successfully",
                template_file=str(template_file),
                version=config.version,
                ai_enabled=config.ai_enabled,
            )

            return config

        except SpecTemplateError:
            # Re-raise template errors
            raise
        except Exception as e:
            error_msg = (
                f"Failed to load template configuration from {template_file}: {e}"
            )
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e

    def _load_from_file(self, template_file: Path) -> TemplateConfig:
        """Load template configuration from YAML file."""
        try:
            with template_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # Handle empty YAML file
            if data is None:
                debug_logger.log("WARNING", "Empty template file, using defaults")
                return get_default_template_config()

            # Validate data structure
            if not isinstance(data, dict):
                raise SpecTemplateError(
                    f"Template file must contain a YAML dictionary, got {type(data)}"
                )

            # Create TemplateConfig with validation
            config = TemplateConfig(**data)

            debug_logger.log(
                "INFO",
                "Template data loaded from file",
                keys=list(data.keys()),
                has_index=bool(data.get("index")),
                has_history=bool(data.get("history")),
            )

            return config

        except yaml.YAMLError as e:
            raise SpecTemplateError(
                f"Invalid YAML in template file {template_file}: {e}"
            ) from e
        except Exception as e:
            raise SpecTemplateError(
                f"Error reading template file {template_file}: {e}"
            ) from e

    def save_template(
        self, config: TemplateConfig, backup_existing: bool = True
    ) -> None:
        """Save template configuration to .spectemplate file.

        Args:
            config: TemplateConfig to save
            backup_existing: Whether to backup existing file

        Raises:
            SpecTemplateError: If save operation fails
        """
        debug_logger.log(
            "INFO",
            "Saving template configuration",
            template_file=str(self.settings.template_file),
            backup=backup_existing,
        )

        # Validate before saving
        self.validator.validate_and_raise(config)

        template_file = self.settings.template_file

        try:
            # Normalize template file path for consistent handling
            normalized_template_file = normalize_path(template_file)

            # Backup existing file if requested
            if backup_existing and normalized_template_file.exists():
                self._backup_existing_file(normalized_template_file)

            # Prepare data for saving
            template_data = self._prepare_save_data(config)

            # Ensure template directory exists
            ensure_directory(normalized_template_file.parent)
            debug_logger.log(
                "DEBUG",
                "Template directory ensured",
                template_file=str(normalized_template_file),
                template_dir=str(normalized_template_file.parent),
                operation="template_file_creation",
            )

            # Write to file
            with normalized_template_file.open("w", encoding="utf-8") as f:
                yaml.dump(
                    template_data,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    allow_unicode=True,
                    width=120,
                )

            debug_logger.log(
                "INFO", "Template configuration saved", template_file=str(template_file)
            )

        except Exception as e:
            error_msg = f"Failed to save template configuration to {template_file}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e

    def _backup_existing_file(self, template_file: Path) -> None:
        """Create backup of existing template file."""
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = template_file.with_suffix(f".backup_{timestamp}.yaml")

        try:
            import shutil

            shutil.copy2(template_file, backup_file)
            debug_logger.log(
                "INFO",
                "Created template backup",
                original=str(template_file),
                backup=str(backup_file),
            )
        except Exception as e:
            debug_logger.log(
                "WARNING", "Could not create template backup", error=str(e)
            )

    def _prepare_save_data(self, config: TemplateConfig) -> dict[str, Any]:
        """Prepare template data for saving to YAML."""
        data: dict[str, Any] = {
            "version": config.version,
        }

        # Add description and author if present
        if config.description:
            data["description"] = config.description
        if config.author:
            data["author"] = config.author

        # Template content
        data["index"] = config.index
        data["history"] = config.history

        # Behavior settings
        data["preserve_manual_edits"] = config.preserve_manual_edits
        data["include_timestamp"] = config.include_timestamp
        data["include_metadata"] = config.include_metadata

        # AI settings (only if AI is enabled)
        if config.ai_enabled:
            data["ai_enabled"] = config.ai_enabled
            data["ai_model"] = config.ai_model
            data["ai_temperature"] = config.ai_temperature
            data["ai_max_tokens"] = config.ai_max_tokens

        return data

    def get_template_info(self) -> dict[str, Any]:
        """Get information about the current template configuration.

        Returns:
            Dictionary with template information
        """
        template_file = self.settings.template_file
        info = {
            "template_file": str(template_file),
            "file_exists": template_file.exists(),
            "using_defaults": not template_file.exists(),
        }

        if template_file.exists():
            try:
                stat = template_file.stat()
                info.update(
                    {
                        "file_size": stat.st_size,
                        "modified_time": stat.st_mtime,
                        "is_readable": template_file.is_file()
                        and os.access(template_file, os.R_OK),
                    }
                )

                # Try to load and get basic info
                config = self.load_template()
                info.update(
                    {
                        "version": config.version,
                        "has_description": bool(config.description),
                        "ai_enabled": config.ai_enabled,
                        "placeholder_count": len(
                            config.get_placeholders_in_templates()
                        ),
                    }
                )

            except Exception as e:
                info["error"] = str(e)

        return info


# Convenience function for backward compatibility
def load_template(settings: SpecSettings | None = None) -> TemplateConfig:
    """Load template configuration (convenience function).

    Args:
        settings: Optional SpecSettings instance

    Returns:
        TemplateConfig instance
    """
    loader = TemplateLoader(settings)
    return loader.load_template()
