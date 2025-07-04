"""Unit tests for AI Template Integration - template_001 slice.

Tests AITemplateIntegrator.enhance_template, process_ai_variables, and validate_enhancement
functions with comprehensive coverage including edge cases, error scenarios, and integration paths.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Mock problematic imports before importing our modules
with patch.dict(
    "sys.modules",
    {
        "torch": Mock(),
        "llama_cpp": Mock(),
        "transformers": Mock(),
    },
):
    from spec_cli.exceptions import SpecTemplateError
    from spec_cli.templates.ai_integration import (
        AIContentManager,
        AITemplateIntegrator,
        MockAIProvider,
        process_ai_variables,
        validate_enhancement,
    )


class TestAITemplateIntegrator:
    """Unit tests for AITemplateIntegrator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_ai_manager = Mock(spec=AIContentManager)
        self.mock_ai_manager.enabled = True
        self.integrator = AITemplateIntegrator(self.mock_ai_manager)

    def test_integrator_initialization_with_manager(self):
        """Test AITemplateIntegrator initialization with provided manager."""
        ai_manager = Mock(spec=AIContentManager)
        integrator = AITemplateIntegrator(ai_manager)

        assert integrator.ai_manager is ai_manager

    def test_integrator_initialization_default_manager(self):
        """Test AITemplateIntegrator initialization with default manager."""
        integrator = AITemplateIntegrator()

        # Should use global ai_content_manager
        assert integrator.ai_manager is not None

    def test_enhance_template_success_standard_level(self):
        """Test successful template enhancement with standard level."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def test_function():\n    pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            template_content = "# {{filename}}\n{{ai_purpose}}\n{{ai_overview}}"
            context = {"file_size": 1024, "line_count": 2}

            # Mock AI content generation
            self.mock_ai_manager.generate_ai_content.return_value = {
                "purpose": "Test function implementation",
                "overview": "## Overview\nSimple test function",
            }

            result = self.integrator.enhance_template(
                template_content, file_path, context, "standard"
            )

            assert f"# {file_path.name}" in result
            assert "Test function implementation" in result
            assert "## Overview" in result
            self.mock_ai_manager.generate_ai_content.assert_called_once()

        finally:
            file_path.unlink()

    def test_enhance_template_success_basic_level(self):
        """Test successful template enhancement with basic level."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def basic_function():\n    return True")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            template_content = "# {{filename}}\n{{ai_purpose}}"
            context = {"file_size": 512}

            self.mock_ai_manager.generate_ai_content.return_value = {
                "purpose": "Basic function implementation"
            }

            result = self.integrator.enhance_template(
                template_content, file_path, context, "basic"
            )

            assert f"# {file_path.name}" in result
            assert "Basic function implementation" in result

            # Should only request purpose for basic level
            call_args = self.mock_ai_manager.generate_ai_content.call_args
            assert call_args[0][2] == ["purpose"]

        finally:
            file_path.unlink()

    def test_enhance_template_success_comprehensive_level(self):
        """Test successful template enhancement with comprehensive level."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("class ComplexClass:\n    def method(self):\n        pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            template_content = "# {{filename}}\n{{ai_purpose}}\n{{ai_overview}}\n{{ai_architecture}}\n{{ai_examples}}"
            context = {"file_size": 2048, "complexity": "high"}

            self.mock_ai_manager.generate_ai_content.return_value = {
                "purpose": "Complex class implementation",
                "overview": "## Overview\nComplex class with methods",
                "architecture": "## Architecture\nClass-based design",
                "examples": "## Examples\nUsage examples",
            }

            result = self.integrator.enhance_template(
                template_content, file_path, context, "comprehensive"
            )

            assert "Complex class implementation" in result
            assert "## Overview" in result
            assert "## Architecture" in result
            assert "## Examples" in result

            # Should request all content types for comprehensive level
            call_args = self.mock_ai_manager.generate_ai_content.call_args
            expected_types = ["purpose", "overview", "architecture", "examples"]
            assert call_args[0][2] == expected_types

        finally:
            file_path.unlink()

    def test_enhance_template_ai_disabled(self):
        """Test template enhancement when AI is disabled."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def function():\n    pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            template_content = "# {{filename}}\nContent"
            context = {}

            # Disable AI
            self.mock_ai_manager.enabled = False

            result = self.integrator.enhance_template(
                template_content, file_path, context
            )

            assert f"# {file_path.name}" in result
            assert "Content" in result
            # Should not call AI generation when disabled
            self.mock_ai_manager.generate_ai_content.assert_not_called()

        finally:
            file_path.unlink()

    def test_enhance_template_empty_content_error(self):
        """Test template enhancement with empty template content."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            template_content = ""
            context = {}

            with pytest.raises(
                SpecTemplateError, match="Template content cannot be empty"
            ):
                self.integrator.enhance_template(template_content, file_path, context)

        finally:
            file_path.unlink()

    def test_enhance_template_file_not_exists_error(self):
        """Test template enhancement with non-existent file."""
        template_content = "# {{filename}}"
        context = {}
        non_existent_path = Path("/non/existent/file.py")

        with pytest.raises(SpecTemplateError, match="Source file does not exist"):
            self.integrator.enhance_template(
                template_content, non_existent_path, context
            )

    def test_enhance_template_unknown_enhancement_level(self):
        """Test template enhancement with unknown enhancement level."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def function():\n    pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            template_content = "# {{filename}}\n{{ai_purpose}}"
            context = {}

            self.mock_ai_manager.generate_ai_content.return_value = {
                "purpose": "Function implementation"
            }

            # Should default to purpose for unknown level
            result = self.integrator.enhance_template(
                template_content, file_path, context, "unknown_level"
            )

            assert f"# {file_path.name}" in result

            # Should request only purpose (default for unknown level)
            call_args = self.mock_ai_manager.generate_ai_content.call_args
            assert call_args[0][2] == ["purpose"]

        finally:
            file_path.unlink()

    def test_enhance_template_ai_generation_error(self):
        """Test template enhancement when AI generation fails."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def function():\n    pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            template_content = "# {{filename}}"
            context = {}

            # Simulate AI generation failure
            self.mock_ai_manager.generate_ai_content.side_effect = Exception(
                "AI generation failed"
            )

            with pytest.raises(SpecTemplateError, match="Template enhancement failed"):
                self.integrator.enhance_template(template_content, file_path, context)

        finally:
            file_path.unlink()

    def test_enhance_template_validation_warnings(self):
        """Test template enhancement with validation warnings."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def function():\n    pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            template_content = "# {{filename}}\nShort"  # Will trigger length warning
            context = {"min_content_length": 100}

            self.mock_ai_manager.generate_ai_content.return_value = {}

            # Should not raise error but log warnings
            result = self.integrator.enhance_template(
                template_content, file_path, context
            )

            assert f"# {file_path.name}" in result
            assert "Short" in result

        finally:
            file_path.unlink()

    def test_get_content_requests_for_level_basic(self):
        """Test content request generation for basic level."""
        requests = self.integrator._get_content_requests_for_level("basic")
        assert requests == ["purpose"]

    def test_get_content_requests_for_level_standard(self):
        """Test content request generation for standard level."""
        requests = self.integrator._get_content_requests_for_level("standard")
        assert requests == ["purpose", "overview"]

    def test_get_content_requests_for_level_comprehensive(self):
        """Test content request generation for comprehensive level."""
        requests = self.integrator._get_content_requests_for_level("comprehensive")
        assert requests == ["purpose", "overview", "architecture", "examples"]

    def test_get_content_requests_for_level_unknown(self):
        """Test content request generation for unknown level."""
        requests = self.integrator._get_content_requests_for_level("unknown")
        assert requests == ["purpose"]

    def test_insert_ai_content_success(self):
        """Test successful AI content insertion."""
        template_content = "# Title\n{{ai_purpose}}\n{{ai_overview}}"
        ai_content = {
            "purpose": "Function purpose description",
            "overview": "## Overview\nDetailed overview",
        }

        result = self.integrator._insert_ai_content(template_content, ai_content)

        assert "Function purpose description" in result
        assert "## Overview\nDetailed overview" in result
        assert "{{ai_purpose}}" not in result
        assert "{{ai_overview}}" not in result

    def test_insert_ai_content_no_placeholders(self):
        """Test AI content insertion with no matching placeholders."""
        template_content = "# Title\nStatic content"
        ai_content = {"purpose": "Function purpose"}

        result = self.integrator._insert_ai_content(template_content, ai_content)

        assert result == template_content
        assert "Function purpose" not in result

    def test_insert_ai_content_empty_ai_content(self):
        """Test AI content insertion with empty AI content."""
        template_content = "# Title\n{{ai_purpose}}"
        ai_content = {}

        result = self.integrator._insert_ai_content(template_content, ai_content)

        assert result == template_content
        assert "{{ai_purpose}}" in result  # Placeholder remains


class TestProcessAIVariables:
    """Unit tests for process_ai_variables function."""

    def test_process_ai_variables_success(self):
        """Test successful AI variable processing."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def test_function():\n    pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            context = {
                "file_size": 1024,
                "line_count": 2,
                "complexity": "medium",
                "functions": ["test_function", "helper_function"],
                "classes": ["TestClass"],
            }

            result = process_ai_variables(file_path, context)

            # File-based variables
            assert result["filename"] == file_path.name
            assert result["file_stem"] == file_path.stem
            assert result["file_extension"] == file_path.suffix
            assert file_path.name in result["relative_path"]

            # Context-based variables
            assert result["file_size"] == 1024
            assert result["line_count"] == 2
            assert result["complexity"] == "medium"

            # AI enhancement metadata
            assert result["ai_enhanced"] == "true"
            assert "enhancement_timestamp" in result

            # Code analysis variables
            assert result["function_count"] == "2"
            assert result["main_functions"] == "test_function, helper_function"
            assert result["class_count"] == "1"
            assert result["main_classes"] == "TestClass"

        finally:
            file_path.unlink()

    def test_process_ai_variables_minimal_context(self):
        """Test AI variable processing with minimal context."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            context = {}

            result = process_ai_variables(file_path, context)

            # Should have default values
            assert result["filename"] == file_path.name
            assert result["file_size"] == "unknown"
            assert result["line_count"] == 0
            assert result["complexity"] == "unknown"
            assert result["ai_enhanced"] == "true"

        finally:
            file_path.unlink()

    def test_process_ai_variables_with_timestamp(self):
        """Test AI variable processing with provided timestamp."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            context = {"timestamp": "2023-01-01 12:00:00"}

            result = process_ai_variables(file_path, context)

            assert result["enhancement_timestamp"] == "2023-01-01 12:00:00"

        finally:
            file_path.unlink()

    def test_process_ai_variables_many_functions_classes(self):
        """Test AI variable processing with many functions and classes."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            context = {
                "functions": ["func1", "func2", "func3", "func4", "func5"],
                "classes": ["Class1", "Class2", "Class3", "Class4"],
            }

            result = process_ai_variables(file_path, context)

            # Should only include first 3 functions and classes
            assert result["function_count"] == "5"
            assert result["main_functions"] == "func1, func2, func3"
            assert result["class_count"] == "4"
            assert result["main_classes"] == "Class1, Class2, Class3"

        finally:
            file_path.unlink()

    def test_process_ai_variables_no_functions_classes(self):
        """Test AI variable processing with no functions or classes."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            context = {}

            result = process_ai_variables(file_path, context)

            # Should not have function/class keys
            assert "function_count" not in result
            assert "main_functions" not in result
            assert "class_count" not in result
            assert "main_classes" not in result

        finally:
            file_path.unlink()

    def test_process_ai_variables_relative_path_fallback(self):
        """Test AI variable processing with relative path fallback."""
        # Use an absolute path that's not under current working directory
        file_path = Path("/absolute/path/outside/cwd/file.py")
        context = {}

        result = process_ai_variables(file_path, context)

        # Should use filename as fallback when relative_to fails
        assert result["relative_path"] == "file.py"
        assert result["filename"] == "file.py"

    def test_process_ai_variables_exception_handling(self):
        """Test AI variable processing with context processing error."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            # Mock file_path.relative_to to raise an exception (after the try/except)
            with patch.object(Path, "name", new_callable=Mock) as mock_name:
                mock_name.side_effect = Exception("Path processing error")
                context = {}

                with pytest.raises(
                    SpecTemplateError, match="AI variable processing failed"
                ):
                    process_ai_variables(file_path, context)

        finally:
            file_path.unlink()


class TestValidateEnhancement:
    """Unit tests for validate_enhancement function."""

    def test_validate_enhancement_success_valid_content(self):
        """Test validation of valid enhanced content."""
        enhanced_content = "# Header\n\nThis is valid content with sufficient length."
        context = {"min_content_length": 20}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is True
        assert result["issues"] == []

    def test_validate_enhancement_empty_content(self):
        """Test validation of empty enhanced content."""
        enhanced_content = ""
        context = {}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is False
        assert "Enhanced content is empty" in result["issues"]

    def test_validate_enhancement_whitespace_only_content(self):
        """Test validation of whitespace-only enhanced content."""
        enhanced_content = "   \n\t  \n  "
        context = {}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is False
        assert "Enhanced content is empty" in result["issues"]

    def test_validate_enhancement_unresolved_placeholders(self):
        """Test validation with unresolved placeholders."""
        enhanced_content = "# Title\n{{unresolved_var}} and {{another_var}}"
        context = {}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is False
        unresolved_issue = next(
            issue
            for issue in result["issues"]
            if "Unresolved placeholders found" in issue
        )
        assert "{{unresolved_var}}" in unresolved_issue
        assert "{{another_var}}" in unresolved_issue

    def test_validate_enhancement_content_too_short(self):
        """Test validation with content below minimum length."""
        enhanced_content = "Short"
        context = {"min_content_length": 100}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is True  # Not critical issue
        length_issue = next(
            issue for issue in result["issues"] if "Content length" in issue
        )
        assert "below minimum (100)" in length_issue

    def test_validate_enhancement_no_ai_content_when_required(self):
        """Test validation when AI content is required but missing."""
        enhanced_content = "Regular content without AI markers"
        context = {"require_ai_content": True}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is True  # Not critical issue
        assert "No AI-generated content detected" in result["issues"]

    def test_validate_enhancement_has_ai_content_markers(self):
        """Test validation when AI content markers are present."""
        enhanced_content = "[AI-generated content] and [Purpose] section"
        context = {"require_ai_content": True}

        result = validate_enhancement(enhanced_content, context)

        # Should not have the "No AI-generated content" issue
        ai_content_issues = [
            issue
            for issue in result["issues"]
            if "No AI-generated content detected" in issue
        ]
        assert len(ai_content_issues) == 0

    def test_validate_enhancement_no_markdown_headers(self):
        """Test validation with no markdown headers."""
        enhanced_content = "Content without any headers just plain text"
        context = {}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is True  # Not critical issue
        assert "No markdown headers found" in result["issues"]

    def test_validate_enhancement_has_markdown_headers(self):
        """Test validation with markdown headers present."""
        enhanced_content = "# Main Header\n\n## Sub Header\n\nContent"
        context = {}

        result = validate_enhancement(enhanced_content, context)

        # Should not have the "No markdown headers" issue
        header_issues = [
            issue for issue in result["issues"] if "No markdown headers found" in issue
        ]
        assert len(header_issues) == 0

    def test_validate_enhancement_default_min_length(self):
        """Test validation with default minimum length."""
        enhanced_content = "Short content"  # 13 characters
        context = {}  # No min_content_length specified

        result = validate_enhancement(enhanced_content, context)

        # Default min_length is 50, so should have length issue
        length_issues = [
            issue for issue in result["issues"] if "Content length" in issue
        ]
        assert len(length_issues) == 1
        assert "below minimum (50)" in length_issues[0]

    def test_validate_enhancement_multiple_issues_non_critical(self):
        """Test validation with multiple non-critical issues."""
        enhanced_content = "Short"  # Too short, no headers
        context = {"min_content_length": 100, "require_ai_content": True}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is True  # All issues are non-critical
        assert len(result["issues"]) == 3
        issue_text = " ".join(result["issues"])
        assert "Content length" in issue_text
        assert "No markdown headers found" in issue_text
        assert "No AI-generated content detected" in issue_text

    def test_validate_enhancement_critical_and_non_critical_issues(self):
        """Test validation with both critical and non-critical issues."""
        enhanced_content = (
            "{{unresolved}}"  # Critical: unresolved placeholder, also short
        )
        context = {"min_content_length": 100}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is False  # Has critical issue
        assert len(result["issues"]) >= 2

        # Should have critical unresolved placeholder issue
        critical_issues = [
            issue for issue in result["issues"] if "unresolved" in issue.lower()
        ]
        assert len(critical_issues) == 1

    def test_validate_enhancement_exception_handling(self):
        """Test validation with processing error."""
        # Use invalid regex that would cause an error
        enhanced_content = "Valid content"
        context = {}

        # Mock re.findall to raise an exception
        with patch("re.findall", side_effect=Exception("Regex error")):
            with pytest.raises(SpecTemplateError, match="Template validation failed"):
                validate_enhancement(enhanced_content, context)

    def test_validate_enhancement_complex_placeholders(self):
        """Test validation with complex placeholder patterns."""
        enhanced_content = (
            "Content with {{var1}} and {{complex_variable_name}} and {{var2}}"
        )
        context = {}

        result = validate_enhancement(enhanced_content, context)

        assert result["valid"] is False
        unresolved_issue = next(
            issue
            for issue in result["issues"]
            if "Unresolved placeholders found" in issue
        )
        assert "{{var1}}" in unresolved_issue
        assert "{{complex_variable_name}}" in unresolved_issue
        assert "{{var2}}" in unresolved_issue

    def test_validate_enhancement_ai_markers_case_variants(self):
        """Test validation with different AI marker variations."""
        test_cases = [
            "[AI-generated documentation]",
            "[Purpose: Function description]",
            "[Overview section follows]",
        ]

        for enhanced_content in test_cases:
            context = {"require_ai_content": True}
            result = validate_enhancement(enhanced_content, context)

            # Should not have "No AI-generated content" issue
            ai_content_issues = [
                issue
                for issue in result["issues"]
                if "No AI-generated content detected" in issue
            ]
            assert len(ai_content_issues) == 0


class TestIntegrationScenarios:
    """Integration tests for AI template components working together."""

    def test_full_enhancement_workflow_success(self):
        """Test complete enhancement workflow from start to finish."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def example_function():\n    return 'hello world'")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            # Create mock AI manager
            mock_ai_manager = Mock(spec=AIContentManager)
            mock_ai_manager.enabled = True
            mock_ai_manager.generate_ai_content.return_value = {
                "purpose": "Example function for demonstration",
                "overview": "## Overview\nReturns a greeting string",
            }

            integrator = AITemplateIntegrator(mock_ai_manager)

            # Template with variables and AI placeholders
            template_content = """# {{filename}}

## Purpose
{{ai_purpose}}

{{ai_overview}}

**File**: {{relative_path}}
**Enhanced**: {{ai_enhanced}}
**Functions**: {{function_count}}
"""

            context = {
                "file_size": 1024,
                "line_count": 2,
                "functions": ["example_function"],
                "classes": [],
            }

            # Enhance template
            result = integrator.enhance_template(
                template_content, file_path, context, "standard"
            )

            # Verify all components worked
            assert f"# {file_path.name}" in result
            assert "Example function for demonstration" in result
            assert "## Overview\nReturns a greeting string" in result
            assert file_path.name in result
            assert "true" in result  # ai_enhanced
            assert "1" in result  # function_count

            # Verify validation passes
            validation_result = validate_enhancement(result, context)
            assert validation_result["valid"] is True

        finally:
            file_path.unlink()

    def test_enhancement_with_ai_disabled_workflow(self):
        """Test enhancement workflow when AI is disabled."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def function():\n    pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            # Create disabled AI manager
            mock_ai_manager = Mock(spec=AIContentManager)
            mock_ai_manager.enabled = False

            integrator = AITemplateIntegrator(mock_ai_manager)

            template_content = "# {{filename}}\n\n**Path**: {{relative_path}}"
            context = {}

            result = integrator.enhance_template(template_content, file_path, context)

            # Should process variables but not call AI
            assert f"# {file_path.name}" in result
            assert file_path.name in result
            mock_ai_manager.generate_ai_content.assert_not_called()

            # Validation should pass
            validation_result = validate_enhancement(result, context)
            assert validation_result["valid"] is True

        finally:
            file_path.unlink()

    def test_error_recovery_workflow(self):
        """Test error handling and recovery in enhancement workflow."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def function():\n    pass")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            # Create AI manager that fails
            mock_ai_manager = Mock(spec=AIContentManager)
            mock_ai_manager.enabled = True
            mock_ai_manager.generate_ai_content.side_effect = Exception(
                "AI service unavailable"
            )

            integrator = AITemplateIntegrator(mock_ai_manager)

            template_content = "# {{filename}}"
            context = {}

            # Should raise SpecTemplateError with proper context
            with pytest.raises(SpecTemplateError) as exc_info:
                integrator.enhance_template(template_content, file_path, context)

            assert "Template enhancement failed" in str(exc_info.value)
            assert "AI service unavailable" in str(exc_info.value)

        finally:
            file_path.unlink()

    def test_mock_ai_provider_integration(self):
        """Test integration with MockAIProvider."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as temp_file:
            temp_file.write("def test_func():\n    return True")
            temp_file.flush()
            file_path = Path(temp_file.name)

        try:
            # Create real AI content manager with mock provider
            ai_manager = AIContentManager()
            ai_manager.enabled = True

            # Register mock provider
            mock_provider = MockAIProvider()
            mock_provider.set_response("purpose", "Mock purpose content")
            mock_provider.set_response("overview", "Mock overview content")
            ai_manager.register_provider("mock", mock_provider)
            ai_manager.set_preferred_provider("mock")

            integrator = AITemplateIntegrator(ai_manager)

            template_content = "# {{filename}}\n{{ai_purpose}}\n{{ai_overview}}"
            context = {}

            result = integrator.enhance_template(
                template_content, file_path, context, "standard"
            )

            assert f"# {file_path.name}" in result
            assert "Mock purpose content" in result
            assert "Mock overview content" in result

        finally:
            file_path.unlink()
