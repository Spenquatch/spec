"""Unit tests for AIEnhancedTemplate functionality."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.providers.base import GenerationRequest
from spec_cli.exceptions import SpecTemplateError
from spec_cli.templates.ai_enhanced import (
    AIEnhancedTemplate,
    TemplateResult,
    create_ai_enhanced_template,
)
from spec_cli.templates.prompt_generator import PromptStructure


class TestTemplateResult:
    """Test TemplateResult data class functionality."""

    def test_template_result_successful_creation(self):
        """Test creating successful TemplateResult."""
        result = TemplateResult(
            success=True,
            traditional_content="# Test\nContent here",
            variables={"title": "Test"},
        )

        assert result.success is True
        assert result.traditional_content == "# Test\nContent here"
        assert result.variables == {"title": "Test"}
        assert result.error is None

    def test_template_result_with_ai_enhancement(self):
        """Test TemplateResult with AI prompt enhancement."""
        ai_prompt = PromptStructure(
            template_content="# {{title}}\n{{content}}",
            placeholders=["title", "content"],
        )

        result = TemplateResult(
            success=True,
            traditional_content="# Test\nContent here",
            ai_prompt=ai_prompt,
            variables={"title": "Test"},
        )

        assert result.has_ai_enhancement() is True
        assert result.ai_prompt == ai_prompt

    def test_template_result_failed_creation(self):
        """Test creating failed TemplateResult."""
        result = TemplateResult(
            success=False,
            error="Processing failed",
            variables={"title": "Test"},
        )

        assert result.success is False
        assert result.error == "Processing failed"
        assert result.has_ai_enhancement() is False

    def test_template_result_validation_successful_without_content(self):
        """Test TemplateResult validation for successful result without content."""
        with pytest.raises(ValueError, match="Successful result must have traditional_content"):
            TemplateResult(success=True, traditional_content="")

    def test_template_result_validation_failed_without_error(self):
        """Test TemplateResult validation for failed result without error."""
        with pytest.raises(ValueError, match="Failed result must have error message"):
            TemplateResult(success=False, error=None)

    def test_template_result_get_content_for_ai_with_enhancement(self):
        """Test getting content formatted for AI with enhancement."""
        ai_prompt = PromptStructure(
            template_content="# {{title}}",
            ai_instructions="Instructions for AI",
        )

        result = TemplateResult(
            success=True,
            traditional_content="# Test Title",
            ai_prompt=ai_prompt,
        )

        content = result.get_content_for_ai()

        assert "Instructions for AI" in content
        assert "# Test Title" in content

    def test_template_result_get_content_for_ai_without_enhancement(self):
        """Test getting content formatted for AI without enhancement."""
        result = TemplateResult(
            success=True,
            traditional_content="# Test Title",
        )

        content = result.get_content_for_ai()

        assert content == "# Test Title"


class TestAIEnhancedTemplate:
    """Test AIEnhancedTemplate class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.template = AIEnhancedTemplate()

    def test_ai_enhanced_template_initialization_default(self):
        """Test AIEnhancedTemplate initialization with defaults."""
        template = AIEnhancedTemplate()

        assert template.template_path is None
        assert template.template_loader is not None
        assert template.prompt_generator is not None
        assert template.substitution is not None

    def test_ai_enhanced_template_initialization_with_path(self):
        """Test AIEnhancedTemplate initialization with custom path."""
        custom_path = Path("/test/custom/.spectemplate")
        template = AIEnhancedTemplate(custom_path)

        assert template.template_path == custom_path

    def test_process_template_traditional_only(self):
        """Test processing template in traditional mode only."""
        template_content = "# {{title}}\n{{description}}"
        variables = {"title": "Test", "description": "Test description"}

        result = self.template.process_template(
            template_content, variables, ai_enabled=False
        )

        assert result.success is True
        assert "# Test" in result.traditional_content
        assert "Test description" in result.traditional_content
        assert result.has_ai_enhancement() is False

    def test_process_template_with_ai_enhancement(self):
        """Test processing template with AI enhancement enabled."""
        template_content = "# {{title}}\n{{description}}"
        variables = {"title": "Test", "description": "Test description"}

        result = self.template.process_template(
            template_content, variables, ai_enabled=True
        )

        assert result.success is True
        assert "# Test" in result.traditional_content
        assert result.has_ai_enhancement() is True
        assert result.ai_prompt is not None

    def test_process_template_invalid_content_type(self):
        """Test processing template with invalid content type."""
        with pytest.raises(SpecTemplateError, match="template_content must be a string"):
            self.template.process_template(123, {})  # type: ignore

    def test_process_template_invalid_variables_type(self):
        """Test processing template with invalid variables type."""
        with pytest.raises(SpecTemplateError, match="variables must be a dictionary"):
            self.template.process_template("{{title}}", "invalid")  # type: ignore

    @patch("spec_cli.templates.ai_enhanced.TemplateSubstitution")
    def test_process_traditional_template_error_handling(self, mock_substitution_class):
        """Test traditional template processing error handling."""
        mock_substitution = Mock()
        mock_substitution.substitute_variables.side_effect = Exception("Substitution error")
        mock_substitution_class.return_value = mock_substitution

        template = AIEnhancedTemplate()
        template.substitution = mock_substitution

        result = template.process_template("{{title}}", {"title": "Test"})

        assert result.success is False
        # The error should indicate processing failed due to the mock
        assert result.success is False
        assert "Template processing failed" in result.error

    @patch("spec_cli.templates.ai_enhanced.PromptGenerator")
    def test_generate_ai_prompt_error_handling(self, mock_generator_class):
        """Test AI prompt generation error handling."""
        mock_generator = Mock()
        mock_generator.convert_template_to_prompt.side_effect = Exception("AI error")
        mock_generator_class.return_value = mock_generator

        template = AIEnhancedTemplate()
        template.prompt_generator = mock_generator

        result = template.process_template("{{title}}", {"title": "Test"}, ai_enabled=True)

        assert result.success is False
        assert "AI error" in result.error

    @patch("spec_cli.templates.ai_enhanced.TemplateLoader")
    def test_load_and_process_template_success(self, mock_loader_class):
        """Test successful template loading and processing."""
        mock_config = Mock()
        mock_config.index = "# {{title}}\n{{description}}"

        mock_loader = Mock()
        mock_loader.load_template.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        template = AIEnhancedTemplate()
        template.template_loader = mock_loader

        variables = {"title": "Test", "description": "Test description"}
        result = template.load_and_process_template(variables)

        assert result.success is True
        assert "# Test" in result.traditional_content

    @patch("spec_cli.templates.ai_enhanced.TemplateLoader")
    def test_load_and_process_template_no_content(self, mock_loader_class):
        """Test template loading with no template content."""
        mock_config = Mock()
        mock_config.index = None

        mock_loader = Mock()
        mock_loader.load_template.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        template = AIEnhancedTemplate()
        template.template_loader = mock_loader

        result = template.load_and_process_template({"title": "Test"})

        assert result.success is False
        assert "No template content found" in result.error

    @patch("spec_cli.templates.ai_enhanced.TemplateLoader")
    def test_load_and_process_template_loading_error(self, mock_loader_class):
        """Test template loading error handling."""
        mock_loader = Mock()
        mock_loader.load_template.side_effect = Exception("Loading error")
        mock_loader_class.return_value = mock_loader

        template = AIEnhancedTemplate()
        template.template_loader = mock_loader

        result = template.load_and_process_template({"title": "Test"})

        assert result.success is False
        assert "Loading error" in result.error

    def test_validate_template_compatibility_valid_template(self):
        """Test template compatibility validation with valid template."""
        template_content = "# {{title}}\n{{description}}"

        issues = self.template.validate_template_compatibility(template_content)

        assert issues == []

    def test_validate_template_compatibility_size_limit_exceeded(self):
        """Test template compatibility validation with size limit exceeded."""
        # Create template content larger than 10KB
        large_content = "x" * 10001
        template_content = f"# {{title}}\n{large_content}"

        issues = self.template.validate_template_compatibility(template_content)

        assert any("exceeds recommended size limit" in issue for issue in issues)

    def test_validate_template_compatibility_too_many_variables(self):
        """Test template compatibility validation with too many variables."""
        # Create template with more than 20 variables
        variables = [f"{{{{var{i}}}}}" for i in range(25)]
        template_content = "# Title\n" + " ".join(variables)

        issues = self.template.validate_template_compatibility(template_content)

        assert any("many variables" in issue for issue in issues)

    def test_create_generation_request_successful_template(self):
        """Test creating generation request from successful template result."""
        template_result = TemplateResult(
            success=True,
            traditional_content="# Test\nContent here",
            variables={"title": "Test"},
        )

        source_file = Path("/test/source.py")
        content = "def hello(): pass"

        request = self.template.create_generation_request(
            source_file, content, template_result
        )

        assert isinstance(request, GenerationRequest)
        assert request.source_file == source_file
        assert request.content == content
        assert request.doc_type == "comprehensive"
        assert request.template_content == "# Test\nContent here"

    def test_create_generation_request_with_ai_enhancement(self):
        """Test creating generation request with AI enhancement."""
        ai_prompt = PromptStructure(
            template_content="# {{title}}",
            placeholders=["title"],
            ai_instructions="AI instructions",
        )

        template_result = TemplateResult(
            success=True,
            traditional_content="# Test Title",
            ai_prompt=ai_prompt,
            variables={"title": "Test"},
        )

        source_file = Path("/test/source.py")
        content = "def hello(): pass"

        request = self.template.create_generation_request(
            source_file, content, template_result
        )

        assert "AI instructions" in request.template_content
        assert request.context["has_ai_enhancement"] is True
        assert request.context["ai_placeholders"] == ["title"]

    def test_create_generation_request_failed_template(self):
        """Test creating generation request from failed template result."""
        template_result = TemplateResult(
            success=False,
            error="Template processing failed",
        )

        source_file = Path("/test/source.py")
        content = "def hello(): pass"

        with pytest.raises(SpecTemplateError, match="Cannot create request from failed template"):
            self.template.create_generation_request(source_file, content, template_result)

    def test_get_enhanced_template_info_default(self):
        """Test getting enhanced template information with defaults."""
        info = self.template.get_enhanced_template_info()

        assert info["ai_enhancement_available"] is True
        assert info["template_path"] == "default"
        assert info["supports_traditional_mode"] is True
        assert info["supports_ai_mode"] is True
        assert info["backward_compatible"] is True

    def test_get_enhanced_template_info_with_custom_path(self):
        """Test getting enhanced template information with custom path."""
        custom_path = Path("/test/.spectemplate")
        template = AIEnhancedTemplate(custom_path)

        info = template.get_enhanced_template_info()

        assert info["template_path"] == str(custom_path)

    @patch("spec_cli.templates.ai_enhanced.TemplateLoader")
    def test_get_enhanced_template_info_with_loader_error(self, mock_loader_class):
        """Test getting enhanced template information with loader error."""
        mock_loader = Mock()
        mock_loader.get_template_info.side_effect = Exception("Loader error")
        mock_loader_class.return_value = mock_loader

        template = AIEnhancedTemplate()
        template.template_loader = mock_loader

        info = template.get_enhanced_template_info()

        assert "template_info_error" in info
        assert "Loader error" in info["template_info_error"]


class TestCreateAIEnhancedTemplate:
    """Test factory function for creating AI-enhanced templates."""

    def test_create_ai_enhanced_template_default(self):
        """Test creating AI-enhanced template with defaults."""
        template = create_ai_enhanced_template()

        assert isinstance(template, AIEnhancedTemplate)
        assert template.template_path is None

    def test_create_ai_enhanced_template_with_path(self):
        """Test creating AI-enhanced template with custom path."""
        custom_path = Path("/test/.spectemplate")
        template = create_ai_enhanced_template(custom_path)

        assert isinstance(template, AIEnhancedTemplate)
        assert template.template_path == custom_path


class TestAIEnhancedTemplateEdgeCases:
    """Test edge cases and complex scenarios for AIEnhancedTemplate."""

    def setup_method(self):
        """Set up test fixtures."""
        self.template = AIEnhancedTemplate()

    def test_process_template_with_empty_variables(self):
        """Test processing template with empty variables dictionary."""
        template_content = "# {{title}}\n{{description}}"

        result = self.template.process_template(template_content, {})

        assert result.success is True
        assert "{{title}}" in result.traditional_content  # Unsubstituted
        assert "{{description}}" in result.traditional_content

    def test_process_template_with_complex_content(self):
        """Test processing complex template content."""
        template_content = """# {{project_name}} Documentation

## Overview
{{overview}}

## Features
{{features}}

## Installation
{{installation_instructions}}

## Usage
{{usage_examples}}

## Contributing
{{contributing_guidelines}}"""

        variables = {
            "project_name": "Test Project",
            "overview": "A test project",
            "features": "- Feature 1\n- Feature 2",
        }

        result = self.template.process_template(template_content, variables, ai_enabled=True)

        assert result.success is True
        assert "# Test Project Documentation" in result.traditional_content
        assert result.has_ai_enhancement() is True
        assert len(result.ai_prompt.placeholders) >= 5

    def test_process_template_timing_measurement(self):
        """Test that processing time is measured correctly."""
        template_content = "# {{title}}\n{{description}}"
        variables = {"title": "Test", "description": "Description"}

        result = self.template.process_template(template_content, variables)

        assert result.success is True
        assert result.processing_time_ms is not None
        assert result.processing_time_ms >= 0

    def test_create_generation_request_with_custom_doc_type(self):
        """Test creating generation request with custom doc type."""
        template_result = TemplateResult(
            success=True,
            traditional_content="# Test\nContent here",
        )

        source_file = Path("/test/source.py")
        content = "def hello(): pass"

        request = self.template.create_generation_request(
            source_file, content, template_result, doc_type="brief"
        )

        assert request.doc_type == "brief"

    def test_validate_template_compatibility_multiple_issues(self):
        """Test template compatibility validation with multiple issues."""
        # Create template with multiple issues
        large_content = "x" * 5000
        many_variables = [f"{{{{var{i}}}}}" for i in range(15)]
        template_content = f"# Title\n{large_content}\n" + " ".join(many_variables) + "\n{{}}"

        issues = self.template.validate_template_compatibility(template_content)

        # Should find at least one issue
        assert len(issues) >= 1
        assert any("empty placeholders" in issue for issue in issues)

    @patch("spec_cli.templates.ai_enhanced.TemplateLoader")
    def test_load_and_process_template_with_ai_disabled(self, mock_loader_class):
        """Test loading and processing template with AI disabled."""
        mock_config = Mock()
        mock_config.index = "# {{title}}\n{{description}}"

        mock_loader = Mock()
        mock_loader.load_template.return_value = mock_config
        mock_loader_class.return_value = mock_loader

        template = AIEnhancedTemplate()
        template.template_loader = mock_loader

        variables = {"title": "Test", "description": "Test description"}
        result = template.load_and_process_template(variables, ai_enabled=False)

        assert result.success is True
        assert result.has_ai_enhancement() is False
        assert "# Test" in result.traditional_content
