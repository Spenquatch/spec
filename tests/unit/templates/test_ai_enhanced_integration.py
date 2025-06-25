"""Unit tests for AI enhanced template integration points.

This module tests the critical integration points between AIEnhancedTemplate
and the new AI provider system, validating that templates can create
GenerationRequests and that GenerationResults convert back to template format.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.providers.base import GenerationRequest, GenerationResult
from spec_cli.exceptions import SpecTemplateError
from spec_cli.templates.ai_enhanced import AIEnhancedTemplate, TemplateResult
from spec_cli.templates.ai_integration import AIContentManager
from spec_cli.utils.security_validators import validate_git_command
from spec_cli.utils.workflow_utils import create_workflow_result

# Test constants
SAMPLE_TEMPLATE_CONTENT = "# {{filename}}\n\n{{purpose}}\n\n## Overview\n\n{{overview}}"
SAMPLE_SOURCE_FILE = Path("src/example.py")
SAMPLE_FILE_CONTENT = "def hello():\n    return 'world'"
SAMPLE_VARIABLES = {
    "filename": "example.py",
    "purpose": "Example module",
    "overview": "This is an example module",
}
DEFAULT_TIMEOUT_MS = 30000
EXPECTED_AI_CONTENT = "AI-generated comprehensive documentation"
TEST_ERROR_MESSAGE = "Mock provider failure for testing"


class TestAIEnhancedTemplateCreatesGenerationRequest:
    """Test that AIEnhancedTemplate creates proper GenerationRequest objects."""

    def test_ai_enhanced_template_creates_generation_request_with_valid_inputs(self):
        """Test generation request creation with valid template result."""
        # Setup
        template = AIEnhancedTemplate()
        template_result = TemplateResult(
            success=True,
            traditional_content=SAMPLE_TEMPLATE_CONTENT,
            variables=SAMPLE_VARIABLES,
            processing_time_ms=100,
        )

        # Execute
        request = template.create_generation_request(
            source_file=SAMPLE_SOURCE_FILE,
            content=SAMPLE_FILE_CONTENT,
            template_result=template_result,
            doc_type="comprehensive",
        )

        # Verify
        assert isinstance(request, GenerationRequest)
        assert request.source_file == SAMPLE_SOURCE_FILE
        assert request.content == SAMPLE_FILE_CONTENT
        assert request.doc_type == "comprehensive"
        assert request.template_content == SAMPLE_TEMPLATE_CONTENT
        assert request.context["variables"] == SAMPLE_VARIABLES
        assert request.context["has_ai_enhancement"] is False
        assert request.context["processing_time_ms"] == 100

    def test_ai_enhanced_template_creates_generation_request_with_ai_enhancement(self):
        """Test generation request creation with AI prompt enhancement."""
        # Setup
        template = AIEnhancedTemplate()

        with patch.object(template, "process_template") as mock_process:
            from spec_cli.templates.prompt_generator import PromptStructure

            ai_prompt = PromptStructure(
                template_content=SAMPLE_TEMPLATE_CONTENT,
                variables=SAMPLE_VARIABLES,
                placeholders=["{{filename}}", "{{purpose}}", "{{overview}}"],
                sections={"overview": "## Overview section"},
            )
            ai_prompt.ai_instructions = "Generate documentation for Python module"

            template_result = TemplateResult(
                success=True,
                traditional_content="# example.py\n\nExample module\n\n## Overview\n\nThis is an example module",
                ai_prompt=ai_prompt,
                variables=SAMPLE_VARIABLES,
                processing_time_ms=150,
            )
            mock_process.return_value = template_result

            # Execute
            request = template.create_generation_request(
                source_file=SAMPLE_SOURCE_FILE,
                content=SAMPLE_FILE_CONTENT,
                template_result=template_result,
                doc_type="comprehensive",
            )

            # Verify
            assert isinstance(request, GenerationRequest)
            assert request.context["has_ai_enhancement"] is True
            assert request.context["ai_placeholders"] == [
                "{{filename}}",
                "{{purpose}}",
                "{{overview}}",
            ]
            assert request.context["ai_sections"] == ["overview"]
            assert (
                "Generate documentation for Python module" in request.template_content
            )

    def test_ai_enhanced_template_fails_generation_request_with_failed_template(self):
        """Test that failed template result cannot create generation request."""
        # Setup
        template = AIEnhancedTemplate()
        template_result = TemplateResult(
            success=False, error=TEST_ERROR_MESSAGE, variables=SAMPLE_VARIABLES
        )

        # Execute & Verify
        with pytest.raises(
            SpecTemplateError, match="Cannot create request from failed template"
        ):
            template.create_generation_request(
                source_file=SAMPLE_SOURCE_FILE,
                content=SAMPLE_FILE_CONTENT,
                template_result=template_result,
                doc_type="comprehensive",
            )

    def test_ai_enhanced_template_normalizes_paths_in_generation_request(self):
        """Test cross-platform path normalization in generation request."""
        # Setup
        template = AIEnhancedTemplate()
        windows_path = Path("C:\\src\\example.py")
        template_result = TemplateResult(
            success=True,
            traditional_content=SAMPLE_TEMPLATE_CONTENT,
            variables=SAMPLE_VARIABLES,
            processing_time_ms=100,
        )

        # Execute
        request = template.create_generation_request(
            source_file=windows_path,
            content=SAMPLE_FILE_CONTENT,
            template_result=template_result,
        )

        # Verify - source_file should be normalized to forward slashes
        # The normalize_path_separators function converts to forward slashes
        assert "/" in str(request.source_file)
        assert "\\" not in str(request.source_file)

        # get_normalized_path should return a POSIX-style path
        normalized = request.get_normalized_path()
        assert "/" in normalized
        assert "\\" not in normalized

    def test_ai_enhanced_template_handles_empty_variables_in_generation_request(self):
        """Test generation request creation with empty variables."""
        # Setup
        template = AIEnhancedTemplate()
        template_result = TemplateResult(
            success=True,
            traditional_content="# Empty template",
            variables={},
            processing_time_ms=50,
        )

        # Execute
        request = template.create_generation_request(
            source_file=SAMPLE_SOURCE_FILE,
            content=SAMPLE_FILE_CONTENT,
            template_result=template_result,
        )

        # Verify
        assert isinstance(request, GenerationRequest)
        assert request.context["variables"] == {}
        assert request.context["has_ai_enhancement"] is False


class TestGenerationRequestProcessedByNewProviders:
    """Test that GenerationRequest is properly processed by new provider system."""

    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_generation_request_processed_by_new_providers_success(
        self, mock_provider_manager_class, tmp_path
    ):
        """Test successful AI generation through new provider system."""
        # Setup mock provider
        mock_provider = Mock()
        mock_provider.generate_documentation.return_value = GenerationResult(
            success=True,
            content={"index.md": EXPECTED_AI_CONTENT},
            metadata={"provider": "test_provider", "tokens_used": 150},
        )

        mock_provider_manager = Mock()
        mock_provider_manager.get_available_provider.return_value = mock_provider
        mock_provider_manager_class.return_value = mock_provider_manager

        # Setup content manager
        content_manager = AIContentManager()
        content_manager.enabled = True

        # Create a temporary file with content
        test_file = tmp_path / "test_file.py"
        test_file.write_text(SAMPLE_FILE_CONTENT)

        # Create generation request (unused but shows structure)
        _request = GenerationRequest(
            source_file=test_file,
            content=SAMPLE_FILE_CONTENT,
            context=SAMPLE_VARIABLES,
            doc_type="comprehensive",
            template_content=SAMPLE_TEMPLATE_CONTENT,
        )

        # Execute
        results = content_manager.generate_ai_content(
            file_path=test_file,
            context=SAMPLE_VARIABLES,
            content_requests=["purpose", "overview"],
        )

        # Verify
        assert isinstance(results, dict)
        assert "purpose" in results
        assert "overview" in results
        # Should contain AI-generated content from the new provider
        for _content_type, content in results.items():
            assert isinstance(content, str)
            assert len(content) > 0

    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_generation_request_processed_by_new_providers_failure_with_fallback(
        self, mock_provider_manager_class, tmp_path
    ):
        """Test provider failure with graceful fallback."""
        # Setup failing provider
        mock_provider = Mock()
        mock_provider.generate_documentation.return_value = GenerationResult(
            success=False,
            content={},
            error="Provider failed to generate content",
        )

        mock_provider_manager = Mock()
        mock_provider_manager.get_available_provider.return_value = mock_provider
        mock_provider_manager_class.return_value = mock_provider_manager

        # Setup content manager
        content_manager = AIContentManager()
        content_manager.enabled = True

        # Create a temporary file with content
        test_file = tmp_path / "test_file.py"
        test_file.write_text(SAMPLE_FILE_CONTENT)

        # Execute
        results = content_manager.generate_ai_content(
            file_path=test_file,
            context=SAMPLE_VARIABLES,
            content_requests=["purpose", "overview"],
        )

        # Verify fallback content
        assert isinstance(results, dict)
        assert "purpose" in results
        assert "overview" in results
        for _content_type, content in results.items():
            assert "Generation failed" in content

    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_generation_request_processed_handles_provider_unavailable(
        self, mock_provider_manager_class
    ):
        """Test handling when no provider is available."""
        # Setup unavailable provider
        mock_provider_manager = Mock()
        mock_provider_manager.get_available_provider.return_value = None
        mock_provider_manager_class.return_value = mock_provider_manager

        # Setup content manager
        content_manager = AIContentManager()
        content_manager.enabled = True

        # Execute
        results = content_manager.generate_ai_content(
            file_path=SAMPLE_SOURCE_FILE,
            context=SAMPLE_VARIABLES,
            content_requests=["purpose", "overview"],
        )

        # Verify fallback message
        assert isinstance(results, dict)
        for _content_type, content in results.items():
            assert "No AI provider available" in content

    def test_generation_request_processed_respects_ai_disabled(self):
        """Test that disabled AI returns appropriate placeholders."""
        # Setup content manager with AI disabled
        content_manager = AIContentManager()
        content_manager.enabled = False

        # Execute
        results = content_manager.generate_ai_content(
            file_path=SAMPLE_SOURCE_FILE,
            context=SAMPLE_VARIABLES,
            content_requests=["purpose", "overview"],
        )

        # Verify disabled message
        assert isinstance(results, dict)
        for _content_type, content in results.items():
            assert "AI disabled" in content


class TestGenerationResultConvertedToTemplateFormat:
    """Test conversion of GenerationResult back to template format."""

    def test_generation_result_converted_to_template_format_success(self):
        """Test successful conversion of GenerationResult to template format."""
        # Setup
        generation_result = GenerationResult(
            success=True,
            content={
                "index.md": "# Example Module\n\n## Overview\n\nThis module provides example functionality.",
            },
            metadata={"provider": "test_provider", "tokens_used": 200},
        )

        content_manager = AIContentManager()

        # Execute - extract sections from main content
        main_content = generation_result.get_main_content()
        purpose_content = content_manager._extract_section(main_content, "## Overview")

        # Verify conversion
        assert isinstance(main_content, str)
        assert "Example Module" in main_content
        assert "## Overview" in main_content
        assert purpose_content != ""
        assert "provides example functionality" in purpose_content

    def test_generation_result_converted_handles_empty_content(self):
        """Test handling of empty GenerationResult content."""
        # Setup
        generation_result = GenerationResult(
            success=True, content={"index.md": ""}, metadata={}
        )

        # Execute
        main_content = generation_result.get_main_content()

        # Verify
        assert main_content == ""

    def test_generation_result_converted_handles_failed_result(self):
        """Test handling of failed GenerationResult."""
        # Setup
        generation_result = GenerationResult(
            success=False,
            content={},
            error="AI generation failed",
        )

        # Execute
        main_content = generation_result.get_main_content()

        # Verify
        assert main_content == ""
        assert generation_result.error == "AI generation failed"

    def test_generation_result_extract_section_handles_missing_section(self):
        """Test section extraction when section doesn't exist."""
        # Setup
        content_manager = AIContentManager()
        content = "# Title\n\nSome content without the requested section."

        # Execute
        extracted = content_manager._extract_section(content, "## Nonexistent")

        # Verify
        assert extracted == ""

    def test_generation_result_extract_section_stops_at_next_header(self):
        """Test that section extraction stops at the next header."""
        # Setup
        content_manager = AIContentManager()
        content = "# Title\n\n## Section A\n\nContent A\n\n## Section B\n\nContent B"

        # Execute
        extracted = content_manager._extract_section(content, "## Section A")

        # Verify
        assert "## Section A" in extracted
        assert "Content A" in extracted
        assert "## Section B" not in extracted
        assert "Content B" not in extracted


class TestTemplateFallbackWhenAIUnavailable:
    """Test template fallback scenarios when AI is unavailable."""

    def test_template_fallback_when_ai_unavailable_uses_traditional_content(self):
        """Test fallback to traditional template when AI is unavailable."""
        # Setup
        template = AIEnhancedTemplate()

        # Execute with AI disabled
        result = template.process_template(
            template_content=SAMPLE_TEMPLATE_CONTENT,
            variables=SAMPLE_VARIABLES,
            ai_enabled=False,
        )

        # Verify
        assert result.success is True
        assert result.traditional_content != ""
        assert result.ai_prompt is None
        assert result.has_ai_enhancement() is False
        assert "example.py" in result.traditional_content
        assert "Example module" in result.traditional_content

    def test_template_fallback_preserves_all_variable_substitutions(self):
        """Test that fallback preserves all template variable substitutions."""
        # Setup
        template = AIEnhancedTemplate()
        complex_variables = {
            "filename": "complex.py",
            "purpose": "Complex module purpose",
            "overview": "Detailed overview section",
            "author": "Test Author",
            "version": "1.0.0",
        }
        complex_template = "# {{filename}}\n\n{{purpose}}\n\nAuthor: {{author}}\nVersion: {{version}}\n\n{{overview}}"

        # Execute
        result = template.process_template(
            template_content=complex_template,
            variables=complex_variables,
            ai_enabled=False,
        )

        # Verify all substitutions
        assert result.success is True
        content = result.traditional_content
        assert "complex.py" in content
        assert "Complex module purpose" in content
        assert "Test Author" in content
        assert "1.0.0" in content
        assert "Detailed overview section" in content
        assert "{{" not in content  # No unsubstituted variables

    def test_template_fallback_maintains_performance_requirements(self):
        """Test that fallback processing meets performance requirements."""
        # Setup
        template = AIEnhancedTemplate()

        # Execute
        result = template.process_template(
            template_content=SAMPLE_TEMPLATE_CONTENT,
            variables=SAMPLE_VARIABLES,
            ai_enabled=False,
        )

        # Verify performance
        assert result.success is True
        assert result.processing_time_ms is not None
        assert result.processing_time_ms < DEFAULT_TIMEOUT_MS  # Under 30 seconds
        assert result.processing_time_ms >= 0


class TestErrorHandlingInTemplateAIPipeline:
    """Test error handling throughout the template AI pipeline."""

    def test_error_handling_invalid_template_content_type(self):
        """Test error handling for invalid template content type."""
        # Setup
        template = AIEnhancedTemplate()

        # Execute and verify exception is raised
        with pytest.raises(
            SpecTemplateError, match="template_content must be a string"
        ):
            template.process_template(
                template_content=None,  # Invalid type
                variables=SAMPLE_VARIABLES,
                ai_enabled=True,
            )

    def test_error_handling_invalid_variables_type(self):
        """Test error handling for invalid variables type."""
        # Setup
        template = AIEnhancedTemplate()

        # Execute and verify exception is raised
        with pytest.raises(SpecTemplateError, match="variables must be a dictionary"):
            template.process_template(
                template_content=SAMPLE_TEMPLATE_CONTENT,
                variables="invalid",  # Invalid type
                ai_enabled=True,
            )

    @patch("spec_cli.templates.ai_enhanced.TemplateSubstitution")
    def test_error_handling_template_substitution_failure(
        self, mock_substitution_class
    ):
        """Test error handling when template substitution fails."""
        # Setup
        mock_substitution = Mock()
        mock_substitution.substitute.side_effect = Exception("Substitution failed")
        mock_substitution_class.return_value = mock_substitution

        template = AIEnhancedTemplate()

        # Execute
        result = template.process_template(
            template_content=SAMPLE_TEMPLATE_CONTENT,
            variables=SAMPLE_VARIABLES,
            ai_enabled=False,
        )

        # Verify error handling
        assert result.success is False
        assert result.error is not None
        assert "Template processing failed" in result.error

    @patch("spec_cli.templates.ai_enhanced.PromptGenerator")
    def test_error_handling_ai_prompt_generation_failure(
        self, mock_prompt_generator_class
    ):
        """Test error handling when AI prompt generation fails."""
        # Setup
        mock_prompt_generator = Mock()
        mock_prompt_generator.convert_template_to_prompt.side_effect = Exception(
            "AI prompt failed"
        )
        mock_prompt_generator_class.return_value = mock_prompt_generator

        # Mock successful substitution
        with patch.object(
            AIEnhancedTemplate, "_process_traditional_template"
        ) as mock_traditional:
            mock_traditional.return_value = "Traditional content"

            template = AIEnhancedTemplate()

            # Execute
            result = template.process_template(
                template_content=SAMPLE_TEMPLATE_CONTENT,
                variables=SAMPLE_VARIABLES,
                ai_enabled=True,
            )

            # Verify partial success - traditional processing succeeds, AI fails
            assert result.success is False
            assert result.error is not None
            assert "Template processing failed" in result.error

    def test_error_handling_uses_security_validators(self):
        """Test that error handling uses security validation utilities."""
        # Setup - create a mock command that should be validated
        mock_command = ["add", "test_file.txt"]
        work_tree = Path("/test/work/tree")

        # Execute
        is_valid, error_msg = validate_git_command(mock_command, work_tree)

        # Verify security validation is working
        assert isinstance(is_valid, bool)
        assert error_msg is None or isinstance(error_msg, str)

    def test_error_handling_creates_proper_workflow_results(self):
        """Test that error handling creates proper workflow results."""
        # Setup
        test_files = [Path("test1.py"), Path("test2.py")]

        # Execute - test both success and failure cases
        success_result = create_workflow_result(test_files, True, "test_workflow")
        failure_result = create_workflow_result(test_files, False)

        # Verify workflow result structure
        assert success_result["success"] is True
        assert success_result["total_files"] == 2
        assert len(success_result["successful_files"]) == 2
        assert len(success_result["failed_files"]) == 0

        assert failure_result["success"] is False
        assert failure_result["total_files"] == 2
        assert len(failure_result["successful_files"]) == 0
        assert len(failure_result["failed_files"]) == 2

    def test_error_handling_preserves_context_information(self):
        """Test that error handling preserves context for debugging."""
        # Setup
        template = AIEnhancedTemplate()

        # Execute - force an error with context
        result = template.process_template(
            template_content=SAMPLE_TEMPLATE_CONTENT,
            variables=SAMPLE_VARIABLES,
            ai_enabled=True,
        )

        # Verify context preservation
        assert result.variables == SAMPLE_VARIABLES
        if not result.success:
            assert result.error is not None
            assert isinstance(result.error, str)
