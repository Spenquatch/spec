"""AI-enhanced template processing with backward compatibility.

This module provides enhanced template processing that bridges traditional variable
substitution with AI-powered prompt generation while maintaining 100% backward
compatibility with existing templates.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..ai.providers.base import GenerationRequest
from ..core.context_bridge import debug_logger
from ..exceptions import SpecTemplateError
from ..utils.error_handler import default_error_handler
from ..utils.path_utils import normalize_path
from .loader import TemplateLoader
from .prompt_generator import PromptGenerator, PromptStructure
from .substitution import TemplateSubstitution


@dataclass
class TemplateResult:
    """Result of template processing with both traditional and AI outputs."""

    success: bool
    traditional_content: str = ""
    ai_prompt: PromptStructure | None = None
    variables: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    processing_time_ms: int | None = None

    def __post_init__(self) -> None:
        """Validate template result after initialization."""
        if self.success and not self.traditional_content:
            raise ValueError("Successful result must have traditional_content")
        if not self.success and not self.error:
            raise ValueError("Failed result must have error message")

    def has_ai_enhancement(self) -> bool:
        """Check if result includes AI prompt enhancement."""
        return self.ai_prompt is not None

    def get_content_for_ai(self) -> str:
        """Get content formatted for AI processing."""
        if self.ai_prompt:
            # Combine AI instructions with template content
            if self.ai_prompt.ai_instructions:
                return f"{self.ai_prompt.ai_instructions}\n\n{self.traditional_content}"
            # Return the original template with placeholders, not the substituted version
            return self.ai_prompt.template_content
        return self.traditional_content


class AIEnhancedTemplate:
    """Enhanced template processor with AI prompt generation capabilities."""

    def __init__(self, template_path: Path | None = None):
        """Initialize AI-enhanced template processor.

        Args:
            template_path: Optional path to specific template file
        """
        self.template_path = normalize_path(template_path) if template_path else None
        self.template_loader = TemplateLoader()
        self.prompt_generator = PromptGenerator()
        self.substitution = TemplateSubstitution()

        debug_logger.log(
            "INFO",
            "AIEnhancedTemplate initialized",
            template_path=str(self.template_path) if self.template_path else "default",
        )

    def process_template(
        self,
        template_content: str,
        variables: dict[str, Any],
        ai_enabled: bool = True,
    ) -> TemplateResult:
        """Process template with optional AI enhancement.

        Args:
            template_content: Raw template content
            variables: Variables for template substitution
            ai_enabled: Whether to enable AI prompt generation

        Returns:
            TemplateResult: Processing result with traditional and AI outputs

        Raises:
            SpecTemplateError: If template processing fails
        """
        try:
            # Validate inputs
            if not isinstance(template_content, str):
                raise SpecTemplateError("template_content must be a string")

            if not isinstance(variables, dict):
                raise SpecTemplateError("variables must be a dictionary")

            debug_logger.log(
                "INFO",
                "Processing template",
                content_length=len(template_content),
                variables_count=len(variables),
                ai_enabled=ai_enabled,
            )
            # Start timing
            import time

            start_time = time.time()

            # Traditional template processing (always performed)
            traditional_content = self._process_traditional_template(
                template_content, variables
            )

            ai_prompt = None
            if ai_enabled:
                # AI prompt generation (optional enhancement)
                ai_prompt = self._generate_ai_prompt(template_content, variables)

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            result = TemplateResult(
                success=True,
                traditional_content=traditional_content,
                ai_prompt=ai_prompt,
                variables=variables.copy(),
                processing_time_ms=processing_time,
            )

            debug_logger.log(
                "INFO",
                "Template processing completed",
                processing_time_ms=processing_time,
                has_ai_enhancement=result.has_ai_enhancement(),
                traditional_content_length=len(traditional_content),
            )

            return result

        except SpecTemplateError:
            # Re-raise template errors for proper validation
            raise
        except Exception as e:
            error_msg = f"Template processing failed: {e}"
            debug_logger.log("ERROR", error_msg)
            # Handle case where variables might not be a dict
            safe_variables = variables.copy() if isinstance(variables, dict) else {}
            return TemplateResult(
                success=False,
                error=error_msg,
                variables=safe_variables,
            )

    @default_error_handler.wrap
    def _process_traditional_template(
        self, template_content: str, variables: dict[str, Any]
    ) -> str:
        """Process template using traditional variable substitution.

        Args:
            template_content: Raw template content
            variables: Variables for substitution

        Returns:
            Template content with variables substituted

        Raises:
            SpecTemplateError: If traditional processing fails
        """
        debug_logger.log(
            "DEBUG",
            "Processing traditional template",
            content_length=len(template_content),
            variables_count=len(variables),
        )

        # Use existing substitution logic for backward compatibility
        substituted_content: str = self.substitution.substitute(
            template_content, variables
        )

        debug_logger.log(
            "DEBUG",
            "Traditional template processing completed",
            output_length=len(substituted_content),
        )

        return substituted_content

    @default_error_handler.wrap
    def _generate_ai_prompt(
        self, template_content: str, variables: dict[str, Any]
    ) -> PromptStructure:
        """Generate AI prompt structure from template.

        Args:
            template_content: Raw template content
            variables: Variables for context

        Returns:
            PromptStructure: AI-friendly prompt structure

        Raises:
            SpecTemplateError: If AI prompt generation fails
        """
        debug_logger.log(
            "DEBUG",
            "Generating AI prompt structure",
            content_length=len(template_content),
            variables_count=len(variables),
        )

        # Convert template to prompt structure
        prompt_structure = self.prompt_generator.convert_template_to_prompt(
            template_content
        )

        # Enhance with provided variables
        prompt_structure.variables.update(variables)

        debug_logger.log(
            "DEBUG",
            "AI prompt structure generated",
            placeholders_count=len(prompt_structure.placeholders),
            sections_count=len(prompt_structure.sections),
            variables_count=len(prompt_structure.variables),
        )

        return prompt_structure

    def load_and_process_template(
        self, variables: dict[str, Any], ai_enabled: bool = True
    ) -> TemplateResult:
        """Load template from configured path and process it.

        Args:
            variables: Variables for template substitution
            ai_enabled: Whether to enable AI enhancement

        Returns:
            TemplateResult: Processing result

        Raises:
            SpecTemplateError: If template loading or processing fails
        """
        debug_logger.log(
            "INFO",
            "Loading and processing template",
            template_path=str(self.template_path) if self.template_path else "default",
            variables_count=len(variables),
            ai_enabled=ai_enabled,
        )

        try:
            # Load template configuration
            template_config = self.template_loader.load_template()

            # Process the index template (main content)
            if template_config.index:
                return self.process_template(
                    template_config.index, variables, ai_enabled
                )
            else:
                # No template content available
                return TemplateResult(
                    success=False,
                    error="No template content found in configuration",
                    variables=variables.copy(),
                )

        except Exception as e:
            error_msg = f"Failed to load and process template: {e}"
            debug_logger.log("ERROR", error_msg)
            # Handle case where variables might not be a dict
            safe_variables = variables.copy() if isinstance(variables, dict) else {}
            return TemplateResult(
                success=False,
                error=error_msg,
                variables=safe_variables,
            )

    def validate_template_compatibility(self, template_content: str) -> list[str]:
        """Validate template for AI enhancement compatibility.

        Args:
            template_content: Template content to validate

        Returns:
            List of compatibility issues (empty if compatible)
        """
        debug_logger.log(
            "DEBUG",
            "Validating template compatibility",
            content_length=len(template_content),
        )

        issues: list[str] = []

        # Basic syntax validation
        syntax_issues = self.prompt_generator.validate_template_syntax(template_content)
        issues.extend(syntax_issues)

        # Check for AI-specific constraints
        if len(template_content) > 10000:  # 10KB limit
            issues.append("Template content exceeds recommended size limit (10KB)")

        # Check for complex nested structures that may confuse AI
        if template_content.count("{{") > 20:
            issues.append(
                "Template has many variables (>20) which may affect AI processing"
            )

        debug_logger.log(
            "DEBUG",
            "Template compatibility validation completed",
            issues_found=len(issues),
            issues=issues,
        )

        return issues

    def create_generation_request(
        self,
        source_file: Path,
        content: str,
        template_result: TemplateResult,
        doc_type: str = "comprehensive",
    ) -> GenerationRequest:
        """Create AI generation request from template result.

        Args:
            source_file: Source file being documented
            content: Source file content
            template_result: Processed template result
            doc_type: Type of documentation to generate

        Returns:
            GenerationRequest: Request for AI provider

        Raises:
            SpecTemplateError: If request creation fails
        """
        if not template_result.success:
            raise SpecTemplateError(
                f"Cannot create request from failed template: {template_result.error}"
            )

        debug_logger.log(
            "INFO",
            "Creating AI generation request",
            source_file=str(source_file),
            doc_type=doc_type,
            has_ai_enhancement=template_result.has_ai_enhancement(),
        )

        # Use AI-enhanced content if available, otherwise traditional
        template_content = template_result.get_content_for_ai()

        # Create request with enhanced context
        context = {
            "variables": template_result.variables,
            "has_ai_enhancement": template_result.has_ai_enhancement(),
            "processing_time_ms": template_result.processing_time_ms,
        }

        if template_result.ai_prompt:
            context["ai_placeholders"] = template_result.ai_prompt.placeholders
            context["ai_sections"] = list(template_result.ai_prompt.sections.keys())

        request = GenerationRequest(
            source_file=source_file,
            content=content,
            context=context,
            doc_type=doc_type,
            template_content=template_content,
        )

        debug_logger.log(
            "INFO",
            "AI generation request created",
            source_file=request.get_normalized_path(),
            content_size=request.get_content_size(),
            template_size=len(template_content),
        )

        return request

    def get_enhanced_template_info(self) -> dict[str, Any]:
        """Get information about AI enhancement capabilities.

        Returns:
            Dictionary with enhancement information
        """
        info = {
            "ai_enhancement_available": True,
            "template_path": str(self.template_path)
            if self.template_path
            else "default",
            "supports_traditional_mode": True,
            "supports_ai_mode": True,
            "backward_compatible": True,
        }

        # Add template loader info
        try:
            loader_info = self.template_loader.get_template_info()
            info["template_info"] = loader_info
        except Exception as e:
            info["template_info_error"] = str(e)

        return info


def create_ai_enhanced_template(
    template_path: Path | None = None,
) -> AIEnhancedTemplate:
    """Create AI-enhanced template processor.

    Args:
        template_path: Optional path to specific template file

    Returns:
        AIEnhancedTemplate: Configured template processor
    """
    return AIEnhancedTemplate(template_path)
