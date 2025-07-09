"""Prompt generation utilities for AI-enhanced templates.

This module converts traditional template structures to AI-friendly prompt formats
while preserving backward compatibility and variable substitution capabilities.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from ..exceptions import SpecTemplateError
from ..logging.debug import debug_logger


@dataclass
class PromptStructure:
    """Structured prompt format for AI template processing."""

    template_content: str
    variables: dict[str, Any] = field(default_factory=dict)
    placeholders: list[str] = field(default_factory=list)
    sections: dict[str, str] = field(default_factory=dict)
    ai_instructions: str = ""

    def __post_init__(self) -> None:
        """Validate prompt structure after initialization."""
        if not self.template_content.strip():
            raise ValueError("template_content cannot be empty")
        if not isinstance(self.variables, dict):
            raise ValueError("variables must be a dictionary")
        if not isinstance(self.placeholders, list):
            raise ValueError("placeholders must be a list")


class PromptGenerator:
    """Converts template content to AI-friendly prompt structures."""

    # Pattern to match template variables like {{variable_name}}
    VARIABLE_PATTERN = re.compile(r"\{\{([^}]+)\}\}")

    # Common template sections that should be preserved
    SECTION_MARKERS = {
        "title": ["# ", "## ", "### "],
        "description": ["description:", "overview:", "purpose:"],
        "content": ["content:", "body:", "main:"],
        "metadata": ["metadata:", "info:", "details:"],
    }

    def __init__(self) -> None:
        """Initialize prompt generator with logging."""
        debug_logger.log("INFO", "PromptGenerator initialized")

    def convert_template_to_prompt(self, template_content: str) -> PromptStructure:
        """Convert template content to AI prompt structure.

        Args:
            template_content: Raw template content with variables

        Returns:
            PromptStructure: Structured prompt for AI processing

        Raises:
            SpecTemplateError: If template conversion fails
        """
        if not isinstance(template_content, str):
            raise SpecTemplateError("template_content must be a string")

        if not template_content.strip():
            raise SpecTemplateError("template_content cannot be empty")

        try:
            debug_logger.log(
                "INFO",
                "Converting template to prompt structure",
                content_length=len(template_content),
            )

            # Extract placeholders from template
            placeholders = self._extract_placeholders(template_content)

            # Parse template sections
            sections = self._parse_template_sections(template_content)

            # Generate AI instructions
            ai_instructions = self._generate_ai_instructions(placeholders, sections)

            # Create prompt structure
            prompt_structure = PromptStructure(
                template_content=template_content,
                placeholders=placeholders,
                sections=sections,
                ai_instructions=ai_instructions,
            )

            debug_logger.log(
                "INFO",
                "Template conversion completed",
                placeholders_count=len(placeholders),
                sections_count=len(sections),
                instructions_length=len(ai_instructions),
            )

            return prompt_structure

        except Exception as e:
            error_msg = f"Failed to convert template to prompt structure: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e

    def _extract_placeholders(self, template_content: str) -> list[str]:
        """Extract variable placeholders from template content.

        Args:
            template_content: Template content to analyze

        Returns:
            List of unique placeholder names found in template
        """
        matches = self.VARIABLE_PATTERN.findall(template_content)
        placeholders = list({match.strip() for match in matches})

        debug_logger.log(
            "DEBUG",
            "Extracted placeholders from template",
            placeholders=placeholders,
            total_matches=len(matches),
            unique_placeholders=len(placeholders),
        )

        return sorted(placeholders)

    def _parse_template_sections(self, template_content: str) -> dict[str, str]:
        """Parse template content into logical sections.

        Args:
            template_content: Template content to parse

        Returns:
            Dictionary mapping section names to their content
        """
        sections: dict[str, str] = {}
        lines = template_content.split("\n")

        current_section = "main"
        current_content: list[str] = []

        for line in lines:
            line_lower = line.lower().strip()
            section_found = False

            # Check for section markers
            for section_name, markers in self.SECTION_MARKERS.items():
                for marker in markers:
                    if line_lower.startswith(marker.lower()):
                        # Save previous section if it has content
                        if current_content:
                            sections[current_section] = "\n".join(current_content)

                        # Start new section
                        current_section = section_name
                        current_content = [line]
                        section_found = True
                        break
                if section_found:
                    break

            if not section_found:
                current_content.append(line)

        # Save final section
        if current_content:
            sections[current_section] = "\n".join(current_content)

        debug_logger.log(
            "DEBUG",
            "Parsed template sections",
            sections=list(sections.keys()),
            total_sections=len(sections),
        )

        return sections

    def _generate_ai_instructions(
        self, placeholders: list[str], sections: dict[str, str]
    ) -> str:
        """Generate AI instructions based on template structure.

        Args:
            placeholders: List of template placeholders
            sections: Dictionary of template sections

        Returns:
            AI instruction string for prompt context
        """
        instructions = [
            "Generate documentation based on the following template structure:",
            "",
        ]

        # Add placeholder instructions
        if placeholders:
            instructions.append("Template Variables:")
            for placeholder in placeholders:
                instructions.append(
                    f"- {{{{{placeholder}}}}}: {self._get_variable_description(placeholder)}"
                )
            instructions.append("")

        # Add section instructions
        if sections:
            instructions.append("Template Sections:")
            for section_name, content in sections.items():
                if content.strip():
                    line_count = len(content.split("\n"))
                    instructions.append(f"- {section_name}: {line_count} lines")
            instructions.append("")

        # Add generation guidelines
        instructions.extend(
            [
                "Guidelines:",
                "- Maintain the template structure and format",
                "- Fill in all placeholder variables with appropriate content",
                "- Preserve markdown formatting and section organization",
                "- Generate comprehensive and helpful documentation",
            ]
        )

        ai_instructions = "\n".join(instructions)

        debug_logger.log(
            "DEBUG",
            "Generated AI instructions",
            instructions_length=len(ai_instructions),
            placeholder_count=len(placeholders),
            section_count=len(sections),
        )

        return ai_instructions

    def _get_variable_description(self, placeholder: str) -> str:
        """Get descriptive text for a template variable.

        Args:
            placeholder: Variable name from template

        Returns:
            Human-readable description of the variable
        """
        # Common variable descriptions
        descriptions = {
            "filename": "Source file name",
            "purpose": "Primary purpose or function",
            "description": "Detailed description",
            "author": "Author or creator name",
            "date": "Creation or modification date",
            "version": "Version or revision number",
            "content": "Main content or body",
            "summary": "Brief summary",
            "details": "Additional details",
            "notes": "Important notes or comments",
            "examples": "Usage examples",
            "references": "Related references or links",
        }

        # Try exact match first
        if placeholder in descriptions:
            return descriptions[placeholder]

        # Try partial matches for common patterns
        placeholder_lower = placeholder.lower()
        for key, desc in descriptions.items():
            if key in placeholder_lower or placeholder_lower in key:
                return desc

        # Generic description for unknown variables
        return f"Value for {placeholder}"

    def substitute_variables(
        self, prompt_structure: PromptStructure, variables: dict[str, Any]
    ) -> str:
        """Substitute variables in template content.

        Args:
            prompt_structure: Prompt structure with template content
            variables: Dictionary of variable values

        Returns:
            Template content with variables substituted

        Raises:
            SpecTemplateError: If substitution fails
        """
        if not isinstance(variables, dict):
            raise SpecTemplateError("variables must be a dictionary")

        try:
            content = prompt_structure.template_content

            # Substitute each variable
            for placeholder in prompt_structure.placeholders:
                if placeholder in variables:
                    value = str(variables[placeholder])
                    pattern = f"{{{{{placeholder}}}}}"
                    content = content.replace(pattern, value)

            debug_logger.log(
                "DEBUG",
                "Variable substitution completed",
                substituted_variables=len(
                    [p for p in prompt_structure.placeholders if p in variables]
                ),
                total_placeholders=len(prompt_structure.placeholders),
                content_length=len(content),
            )

            return content

        except Exception as e:
            error_msg = f"Failed to substitute template variables: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e

    def validate_template_syntax(self, template_content: str) -> list[str]:
        """Validate template syntax and return any issues found.

        Args:
            template_content: Template content to validate

        Returns:
            List of validation issues (empty if valid)
        """
        issues: list[str] = []

        if not template_content.strip():
            issues.append("Template content is empty")
            return issues

        # Check for unmatched braces
        open_braces = template_content.count("{{")
        close_braces = template_content.count("}}")

        if open_braces != close_braces:
            issues.append(
                f"Unmatched braces: {open_braces} opening, {close_braces} closing"
            )

        # Check for empty placeholders
        empty_placeholders = re.findall(r"\{\{\s*\}\}", template_content)
        if empty_placeholders:
            issues.append(f"Found {len(empty_placeholders)} empty placeholders")

        # Check for nested placeholders
        nested_pattern = re.compile(r"\{\{[^}]*\{\{")
        if nested_pattern.search(template_content):
            issues.append("Nested placeholders are not supported")

        debug_logger.log(
            "DEBUG",
            "Template syntax validation completed",
            issues_found=len(issues),
            issues=issues,
        )

        return issues


def convert_template_to_prompt(template_content: str) -> PromptStructure:
    """Convert template content to prompt structure.

    Args:
        template_content: Template content to convert

    Returns:
        PromptStructure: Converted prompt structure

    Raises:
        SpecTemplateError: If conversion fails
    """
    generator = PromptGenerator()
    return generator.convert_template_to_prompt(template_content)
