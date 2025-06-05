"""Template variable substitution engine with configurable delimiters.

This module handles the substitution of variables in template content, providing
built-in variable generators for dates and timestamps, template syntax validation,
and comprehensive substitution preview and statistics capabilities.
"""

import re
from collections.abc import Callable
from datetime import datetime
from typing import Any

from ..config.settings import SpecSettings, get_settings
from ..exceptions import SpecTemplateError
from ..logging.debug import debug_logger


class TemplateSubstitution:
    """Handles variable substitution in template content with configurable delimiters."""

    def __init__(
        self,
        open_delimiter: str = "{{",
        close_delimiter: str = "}}",
        settings: SpecSettings | None = None,
    ):
        """Initialize the template substitution engine.

        Args:
            open_delimiter: Opening delimiter for variables (default: '{{')
            close_delimiter: Closing delimiter for variables (default: '}}')
            settings: Optional spec settings (uses global settings if None)
        """
        self.settings = settings or get_settings()
        self.open_delimiter = open_delimiter
        self.close_delimiter = close_delimiter

        # Escape delimiters for regex
        escaped_open = re.escape(open_delimiter)
        escaped_close = re.escape(close_delimiter)

        # Pattern for finding template variables
        self.variable_pattern = re.compile(f"{escaped_open}(\\w+){escaped_close}")

        # Built-in variable generators
        self.builtin_generators = {
            "date": self._generate_date,
            "datetime": self._generate_datetime,
            "timestamp": self._generate_timestamp,
            "year": self._generate_year,
            "month": self._generate_month,
            "day": self._generate_day,
        }

        debug_logger.log(
            "INFO",
            "TemplateSubstitution initialized",
            open_delimiter=open_delimiter,
            close_delimiter=close_delimiter,
        )

    def substitute(self, template: str, variables: dict[str, Any]) -> str:
        """Substitute variables in template content.

        Args:
            template: Template content with variable placeholders
            variables: Dictionary of variable values

        Returns:
            Template content with variables substituted

        Raises:
            SpecTemplateError: If substitution fails
        """
        debug_logger.log(
            "INFO",
            "Performing template substitution",
            template_length=len(template),
            variable_count=len(variables),
        )

        try:
            with debug_logger.timer("template_substitution"):
                # Find all variables in the template
                found_variables = set(self.variable_pattern.findall(template))
                debug_logger.log(
                    "DEBUG",
                    "Found template variables",
                    variables=sorted(found_variables),
                )

                # Prepare complete variable context
                substitution_context = self._prepare_substitution_context(
                    variables, found_variables
                )

                # Perform substitution
                result = template
                substitutions_made = 0

                for variable_name in found_variables:
                    placeholder = (
                        f"{self.open_delimiter}{variable_name}{self.close_delimiter}"
                    )

                    if variable_name in substitution_context:
                        value = str(substitution_context[variable_name])
                        result = result.replace(placeholder, value)
                        substitutions_made += 1
                        debug_logger.log(
                            "DEBUG",
                            "Substituted variable",
                            variable=variable_name,
                            value_length=len(value),
                        )
                    else:
                        # Leave unresolved variables as placeholders
                        debug_logger.log(
                            "WARNING",
                            "Unresolved template variable",
                            variable=variable_name,
                        )

                debug_logger.log(
                    "INFO",
                    "Template substitution complete",
                    substitutions_made=substitutions_made,
                    result_length=len(result),
                )

                return result

        except Exception as e:
            error_msg = f"Template substitution failed: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e

    def _prepare_substitution_context(
        self, variables: dict[str, Any], found_variables: set[str]
    ) -> dict[str, str]:
        """Prepare complete substitution context with built-in and provided variables.

        Args:
            variables: User-provided variables
            found_variables: Variables found in the template

        Returns:
            Complete substitution context
        """
        context = {}

        # Add user-provided variables first (higher precedence)
        for key, value in variables.items():
            context[key] = self._format_variable_value(value)

        # Generate built-in variables that are needed and not already provided
        for variable_name in found_variables:
            if (
                variable_name in self.builtin_generators
                and variable_name not in context
            ):
                try:
                    generated_value = self.builtin_generators[variable_name]()
                    context[variable_name] = self._format_variable_value(
                        generated_value
                    )
                    debug_logger.log(
                        "DEBUG",
                        "Generated built-in variable",
                        variable=variable_name,
                        value=generated_value,
                    )
                except Exception as e:
                    debug_logger.log(
                        "WARNING",
                        "Failed to generate built-in variable",
                        variable=variable_name,
                        error=str(e),
                    )

        return context

    def _format_variable_value(self, value: Any) -> str:
        """Format a variable value for substitution."""
        if value is None:
            return "[To be filled]"
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, list | tuple):
            if not value:
                return "[None specified]"
            return "\\n".join(f"- {item}" for item in value)
        elif isinstance(value, dict):
            if not value:
                return "[None specified]"
            return "\\n".join(f"- **{key}**: {val}" for key, val in value.items())
        else:
            return str(value)

    def _generate_date(self) -> str:
        """Generate current date in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")

    def _generate_datetime(self) -> str:
        """Generate current datetime in ISO format."""
        return datetime.now().isoformat()

    def _generate_timestamp(self) -> str:
        """Generate current Unix timestamp."""
        return str(int(datetime.now().timestamp()))

    def _generate_year(self) -> str:
        """Generate current year."""
        return str(datetime.now().year)

    def _generate_month(self) -> str:
        """Generate current month."""
        return datetime.now().strftime("%B")

    def _generate_day(self) -> str:
        """Generate current day."""
        return str(datetime.now().day)

    def get_variables_in_template(self, template: str) -> set[str]:
        """Extract all variable names from a template.

        Args:
            template: Template content to analyze

        Returns:
            Set of variable names found in template
        """
        return set(self.variable_pattern.findall(template))

    def validate_template_syntax(self, template: str) -> list[str]:
        """Validate template syntax and return issues.

        Args:
            template: Template content to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues = []

        # Check for unmatched delimiters
        open_count = template.count(self.open_delimiter)
        close_count = template.count(self.close_delimiter)

        if open_count != close_count:
            issues.append(
                f"Mismatched delimiters: {open_count} open vs {close_count} close"
            )

        # Check for nested delimiters
        nested_pattern = re.compile(
            f"{re.escape(self.open_delimiter)}[^{re.escape(self.close_delimiter)}]*{re.escape(self.open_delimiter)}"
        )
        if nested_pattern.search(template):
            issues.append("Nested delimiters detected")

        # Check for empty variables
        empty_vars = re.findall(
            f"{re.escape(self.open_delimiter)}\\s*{re.escape(self.close_delimiter)}",
            template,
        )
        if empty_vars:
            issues.append(f"Found {len(empty_vars)} empty variable placeholders")

        # Check for invalid variable names
        all_matches = re.findall(
            f"{re.escape(self.open_delimiter)}([^{re.escape(self.close_delimiter)}]*){re.escape(self.close_delimiter)}",
            template,
        )
        invalid_vars = [
            match for match in all_matches if not re.match(r"^\w+$", match.strip())
        ]
        if invalid_vars:
            issues.append(f"Invalid variable names: {invalid_vars}")

        return issues

    def preview_substitution(
        self, template: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Preview what substitution would produce without actually doing it.

        Args:
            template: Template content
            variables: Variables for substitution

        Returns:
            Dictionary with preview information
        """
        found_variables = self.get_variables_in_template(template)
        context = self._prepare_substitution_context(variables, found_variables)

        preview = {
            "template_length": len(template),
            "variables_found": sorted(found_variables),
            "variables_provided": sorted(variables.keys()),
            "variables_resolved": sorted([v for v in found_variables if v in context]),
            "variables_unresolved": sorted(
                [v for v in found_variables if v not in context]
            ),
            "builtin_variables_used": sorted(
                [
                    v
                    for v in found_variables
                    if v in self.builtin_generators and v not in variables
                ]
            ),
            "substitution_context": {
                k: v[:50] + "..." if len(v) > 50 else v for k, v in context.items()
            },
            "syntax_issues": self.validate_template_syntax(template),
        }

        return preview

    def get_builtin_variables(self) -> list[str]:
        """Get list of available built-in variables.

        Returns:
            List of built-in variable names
        """
        return sorted(self.builtin_generators.keys())

    def test_variable_substitution(self, variable_name: str, value: Any) -> str:
        """Test how a single variable would be formatted.

        Args:
            variable_name: Name of the variable
            value: Value to format

        Returns:
            Formatted value string
        """
        return self._format_variable_value(value)

    def change_delimiters(self, open_delimiter: str, close_delimiter: str) -> None:
        """Change the delimiters used for variable recognition.

        Args:
            open_delimiter: New opening delimiter
            close_delimiter: New closing delimiter
        """
        self.open_delimiter = open_delimiter
        self.close_delimiter = close_delimiter

        # Update regex pattern
        escaped_open = re.escape(open_delimiter)
        escaped_close = re.escape(close_delimiter)
        self.variable_pattern = re.compile(f"{escaped_open}(\\w+){escaped_close}")

        debug_logger.log(
            "INFO",
            "Template delimiters changed",
            open_delimiter=open_delimiter,
            close_delimiter=close_delimiter,
        )

    def add_builtin_generator(self, name: str, generator: Callable[[], str]) -> None:
        """Add a custom built-in variable generator.

        Args:
            name: Variable name
            generator: Function that returns a string value
        """
        self.builtin_generators[name] = generator
        debug_logger.log("INFO", "Added custom builtin generator", variable_name=name)

    def remove_builtin_generator(self, name: str) -> bool:
        """Remove a built-in variable generator.

        Args:
            name: Variable name to remove

        Returns:
            True if generator was removed, False if it didn't exist
        """
        if name in self.builtin_generators:
            del self.builtin_generators[name]
            debug_logger.log("INFO", "Removed builtin generator", variable_name=name)
            return True
        return False

    def get_substitution_stats(
        self, template: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        """Get detailed statistics about substitution process.

        Args:
            template: Template content
            variables: Variables for substitution

        Returns:
            Dictionary with substitution statistics
        """
        found_variables = self.get_variables_in_template(template)
        context = self._prepare_substitution_context(variables, found_variables)

        stats = {
            "template_length": len(template),
            "variable_placeholder_count": len(found_variables),
            "unique_variables": len(found_variables),
            "provided_variables": len(variables),
            "builtin_variables_needed": len(
                [
                    v
                    for v in found_variables
                    if v in self.builtin_generators and v not in variables
                ]
            ),
            "resolvable_variables": len([v for v in found_variables if v in context]),
            "unresolvable_variables": len(
                [v for v in found_variables if v not in context]
            ),
            "substitution_coverage": (
                len([v for v in found_variables if v in context])
                / len(found_variables)
                * 100
                if found_variables
                else 100
            ),
            "syntax_valid": len(self.validate_template_syntax(template)) == 0,
        }

        return stats
