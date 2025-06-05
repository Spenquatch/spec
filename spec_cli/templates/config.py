"""Template configuration management for spec generation.

This module provides configuration classes for template validation, AI integration
settings, and template behavior configuration. It includes comprehensive validation
for template syntax and placeholder management.
"""

import re
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..exceptions import SpecTemplateError
from ..logging.debug import debug_logger


class TemplateConfig(BaseModel):
    """Configuration for spec template generation with comprehensive validation."""

    index: str = Field(description="Template for index.md file content", min_length=10)

    history: str = Field(
        description="Template for history.md file content", min_length=10
    )

    # Template metadata
    version: str = Field(default="1.0", description="Template version")
    description: str | None = Field(default=None, description="Template description")
    author: str | None = Field(default=None, description="Template author")

    # AI integration settings (extension points)
    ai_enabled: bool = Field(default=False, description="Enable AI content generation")
    ai_model: str | None = Field(default=None, description="AI model to use")
    ai_temperature: float = Field(
        default=0.3, ge=0.0, le=1.0, description="AI creativity level"
    )
    ai_max_tokens: int = Field(
        default=1000, ge=100, le=4000, description="Maximum AI tokens"
    )

    # Template behavior settings
    preserve_manual_edits: bool = Field(
        default=True, description="Preserve manual edits during regeneration"
    )
    include_timestamp: bool = Field(
        default=True, description="Include generation timestamp"
    )
    include_metadata: bool = Field(default=True, description="Include file metadata")

    model_config = ConfigDict(
        validate_assignment=True,
        extra="forbid",  # Reject unknown fields
    )

    @field_validator("index", "history")
    @classmethod
    def validate_template_syntax(cls, v: str, info: Any) -> str:
        """Validate template syntax and required placeholders."""
        field_name = info.field_name
        if not v.strip():
            raise ValueError(f"{field_name} template cannot be empty")

        # Check for balanced braces
        open_count = v.count("{{")
        close_count = v.count("}}")
        if open_count != close_count:
            raise ValueError(f"{field_name} template has unmatched braces ({{ vs }})")

        # Check for required placeholders
        required_placeholders = ["{{filename}}"]
        for placeholder in required_placeholders:
            if placeholder not in v:
                raise ValueError(
                    f"{field_name} template must contain {placeholder} placeholder"
                )

        # Validate placeholder syntax - look for single braces that aren't part of double braces
        # This pattern finds single { or } that aren't immediately preceded/followed by another brace
        single_braces = re.findall(r"(?<!\{)\{(?!\{)|(?<!\})\}(?!\})", v)
        if single_braces:
            raise ValueError(
                f"{field_name} template has malformed single braces (use {{{{ }}}} for placeholders): {single_braces}"
            )

        return v

    @field_validator("ai_model")
    @classmethod
    def validate_ai_model(cls, v: str | None, info: Any) -> str | None:
        """Validate AI model specification."""
        # In Pydantic V2, we need to check the context differently
        # For now, we'll validate the model itself, and the ai_enabled check
        # will be handled at the model level if needed
        if v is not None:
            if not v.strip():
                raise ValueError("AI model cannot be empty")
        return v

    def get_available_variables(self) -> dict[str, str]:
        """Get all available template variables with descriptions.

        Returns:
            Dictionary mapping variable names to descriptions
        """
        return {
            # File information
            "filename": "Name of the source file",
            "filepath": "Full path to the source file relative to project root",
            "file_extension": "File extension without the dot (e.g., 'py', 'js')",
            "file_type": "Detected file type category (e.g., 'python', 'javascript')",
            # Timestamps
            "date": "Current date in YYYY-MM-DD format",
            "datetime": "Current date and time in ISO format",
            "timestamp": "Unix timestamp of generation",
            # Content placeholders (for AI or manual filling)
            "purpose": "Purpose and role of the file",
            "overview": "High-level overview of the file",
            "responsibilities": "Key responsibilities of the file",
            "dependencies": "Dependencies and requirements",
            "api_interface": "API or interface definition",
            "example_usage": "Example usage code",
            "configuration": "Configuration details",
            "error_handling": "Error handling approach",
            "testing_notes": "Testing guidelines and notes",
            "performance_notes": "Performance considerations",
            "security_notes": "Security considerations",
            "future_enhancements": "Planned future enhancements",
            "related_docs": "Links to related documentation",
            "notes": "Additional notes and comments",
            # History-specific placeholders
            "context": "Context for creation or changes",
            "initial_purpose": "Initial purpose when file was created",
            "decisions": "Key decisions made",
            "implementation_notes": "Implementation details and notes",
            # Advanced placeholders (for comprehensive templates)
            "architecture": "Architectural details",
            "design_patterns": "Design patterns used",
            "code_quality": "Code quality metrics and notes",
            "monitoring": "Monitoring and observability",
            "troubleshooting": "Troubleshooting guide",
            "migration_guide": "Migration and upgrade guide",
            "architecture_evolution": "How the architecture has evolved over time",
            "performance_impact": "Performance implications of changes",
            "security_implications": "Security impact and considerations",
            "technical_debt": "Accumulated technical debt and plans",
            "future_planning": "Future development and enhancement plans",
        }

    def get_placeholders_in_templates(self) -> set[str]:
        """Extract all placeholders used in the templates.

        Returns:
            Set of placeholder names found in templates
        """
        placeholders = set()

        # Find all {{variable}} patterns
        pattern = re.compile(r"\{\{(\w+)\}\}")

        for template_content in [self.index, self.history]:
            matches = pattern.findall(template_content)
            placeholders.update(matches)

        return placeholders

    def validate_placeholders(self) -> list[str]:
        """Validate that all placeholders in templates are recognized.

        Returns:
            List of validation issues (empty if all valid)
        """
        used_placeholders = self.get_placeholders_in_templates()
        available_placeholders = set(self.get_available_variables().keys())

        issues = []

        # Check for unknown placeholders
        unknown = used_placeholders - available_placeholders
        if unknown:
            issues.append(f"Unknown placeholders: {', '.join(sorted(unknown))}")

        # Check for missing critical placeholders
        critical_placeholders = {"filename", "filepath"}
        for template_name, template_content in [
            ("index", self.index),
            ("history", self.history),
        ]:
            template_placeholders = set(re.findall(r"\{\{(\w+)\}\}", template_content))
            missing_critical = critical_placeholders - template_placeholders
            if missing_critical:
                issues.append(
                    f"{template_name} template missing critical placeholders: {', '.join(sorted(missing_critical))}"
                )

        return issues

    def to_dict(self) -> dict[str, Any]:
        """Convert template config to dictionary for serialization."""
        return {
            "index": self.index,
            "history": self.history,
            "version": self.version,
            "description": self.description,
            "author": self.author,
            "ai_enabled": self.ai_enabled,
            "ai_model": self.ai_model,
            "ai_temperature": self.ai_temperature,
            "ai_max_tokens": self.ai_max_tokens,
            "preserve_manual_edits": self.preserve_manual_edits,
            "include_timestamp": self.include_timestamp,
            "include_metadata": self.include_metadata,
        }


class TemplateValidator:
    """Validates template configuration and provides detailed feedback."""

    def __init__(self) -> None:
        """Initialize the template validator.

        Sets up validation infrastructure and logs initialization.
        """
        debug_logger.log("INFO", "TemplateValidator initialized")

    def validate_config(self, config: TemplateConfig) -> list[str]:
        """Validate template configuration and return list of issues.

        Args:
            config: TemplateConfig to validate

        Returns:
            List of validation error messages
        """
        debug_logger.log("INFO", "Validating template configuration")
        issues = []

        try:
            # Validate placeholders
            placeholder_issues = config.validate_placeholders()
            issues.extend(placeholder_issues)

            # Validate template content structure
            structure_issues = self._validate_template_structure(config)
            issues.extend(structure_issues)

            # Validate AI configuration if enabled
            if config.ai_enabled:
                ai_issues = self._validate_ai_config(config)
                issues.extend(ai_issues)

            debug_logger.log(
                "INFO", "Template validation complete", issue_count=len(issues)
            )

        except Exception as e:
            debug_logger.log("ERROR", "Template validation failed", error=str(e))
            issues.append(f"Validation error: {e}")

        return issues

    def _validate_template_structure(self, config: TemplateConfig) -> list[str]:
        """Validate template structure and content."""
        issues = []

        # Check for reasonable template length
        if len(config.index) < 50:
            issues.append("Index template is too short (less than 50 characters)")
        if len(config.history) < 50:
            issues.append("History template is too short (less than 50 characters)")

        # Check for basic sections in index template
        index_lower = config.index.lower()
        recommended_sections = ["purpose", "overview", "usage", "example"]
        missing_sections = [
            section for section in recommended_sections if section not in index_lower
        ]
        if len(missing_sections) > 2:
            issues.append(
                f"Index template missing recommended sections: {', '.join(missing_sections)}"
            )

        # Check for proper markdown structure
        if not config.index.startswith("#"):
            issues.append("Index template should start with a markdown header")
        if not config.history.startswith("#"):
            issues.append("History template should start with a markdown header")

        return issues

    def _validate_ai_config(self, config: TemplateConfig) -> list[str]:
        """Validate AI configuration settings."""
        issues = []

        if config.ai_enabled and not config.ai_model:
            issues.append("AI model must be specified when AI is enabled")

        if config.ai_temperature < 0.1:
            issues.append(
                "AI temperature is very low (< 0.1), may produce repetitive content"
            )
        elif config.ai_temperature > 0.8:
            issues.append(
                "AI temperature is very high (> 0.8), may produce inconsistent content"
            )

        if config.ai_max_tokens < 200:
            issues.append(
                "AI max tokens is very low (< 200), may produce incomplete content"
            )

        return issues

    def validate_and_raise(self, config: TemplateConfig) -> None:
        """Validate configuration and raise exception if invalid.

        Args:
            config: TemplateConfig to validate

        Raises:
            SpecTemplateError: If configuration is invalid
        """
        issues = self.validate_config(config)
        if issues:
            error_msg = "Template configuration validation failed:\n" + "\n".join(
                f"  - {issue}" for issue in issues
            )
            raise SpecTemplateError(error_msg)

        debug_logger.log("INFO", "Template configuration validation passed")
