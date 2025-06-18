"""Integration tests for AI-enhanced template system.

This module tests the complete workflow of loading templates, processing them
with AI enhancement, and generating documentation requests.
"""

import tempfile
from pathlib import Path

import pytest

from spec_cli.ai.providers.base import GenerationRequest
from spec_cli.templates.ai_enhanced import AIEnhancedTemplate, create_ai_enhanced_template
from spec_cli.templates.config import TemplateConfig
from spec_cli.templates.loader import TemplateLoader


class TestAIEnhancedTemplateIntegration:
    """Integration tests for the complete AI-enhanced template workflow."""

    def setup_method(self):
        """Set up test fixtures with temporary files."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.template_file = self.temp_dir / ".spectemplate"
        self.test_source_file = self.temp_dir / "test_source.py"

        # Create test source file
        self.test_source_file.write_text(
            """def hello_world():
    \"\"\"A simple hello world function.\"\"\"
    return "Hello, World!"

class TestClass:
    \"\"\"A test class for demonstration.\"\"\"

    def __init__(self, name: str):
        self.name = name

    def greet(self) -> str:
        return f"Hello, {self.name}!"
"""
        )

    def teardown_method(self):
        """Clean up temporary files."""
        import shutil
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_end_to_end_template_processing_with_direct_template(self):
        """Test complete workflow with direct template content."""
        # Use direct template content instead of YAML file
        template_content = """# {{filename}} Documentation

## Overview
{{overview}}

## Purpose
{{purpose}}

## Implementation Details
{{implementation_details}}

## Usage Examples
{{usage_examples}}

## Notes
{{notes}}"""

        # Test variables
        variables = {
            "filename": "test_source.py",
            "overview": "A test Python module with hello world functionality",
            "purpose": "Demonstrate basic Python functions and classes",
            "implementation_details": "Uses simple function and class definitions",
            "usage_examples": "Call hello_world() for a greeting",
            "notes": "This is a test module for integration testing",
        }

        # Create AI-enhanced template
        template = AIEnhancedTemplate()

        # Process the template directly
        result = template.process_template(template_content, variables, ai_enabled=True)

        # Verify successful processing
        assert result.success is True
        assert result.has_ai_enhancement() is True
        assert result.ai_prompt is not None

        # Verify traditional content has substituted variables
        traditional_content = result.traditional_content
        assert "# test_source.py Documentation" in traditional_content
        assert "A test Python module" in traditional_content
        assert "Demonstrate basic Python" in traditional_content

        # Verify AI prompt structure
        ai_prompt = result.ai_prompt
        assert len(ai_prompt.placeholders) > 0
        assert "filename" in ai_prompt.placeholders
        assert "overview" in ai_prompt.placeholders
        assert len(ai_prompt.sections) > 0
        assert ai_prompt.ai_instructions != ""

        # Verify all variables were used
        for var_name in variables:
            assert var_name in ai_prompt.placeholders or var_name in ai_prompt.variables

    def test_end_to_end_generation_request_creation(self):
        """Test creating AI generation request from processed template."""
        # Create a simple template file
        template_content = """# {{filename}} Documentation

## Description
{{description}}

## Implementation
{{implementation}}

## Usage
```python
{{usage_code}}
```

## Notes
{{notes}}
"""

        # Write template directly (simulating default behavior)
        variables = {
            "filename": "test_source.py",
            "description": "Test module with hello world function",
            "implementation": "Simple function and class definitions",
            "usage_code": "print(hello_world())",
            "notes": "Integration test example",
        }

        # Create AI-enhanced template
        template = AIEnhancedTemplate()

        # Process template content directly
        result = template.process_template(template_content, variables, ai_enabled=True)

        # Verify processing succeeded
        assert result.success is True
        assert result.has_ai_enhancement() is True

        # Create generation request
        source_content = self.test_source_file.read_text()
        generation_request = template.create_generation_request(
            self.test_source_file,
            source_content,
            result,
            doc_type="comprehensive"
        )

        # Verify generation request
        assert isinstance(generation_request, GenerationRequest)
        assert generation_request.source_file == self.test_source_file
        assert generation_request.content == source_content
        assert generation_request.doc_type == "comprehensive"
        assert generation_request.template_content is not None

        # Verify request context includes AI enhancement info
        assert generation_request.context["has_ai_enhancement"] is True
        assert "ai_placeholders" in generation_request.context
        assert "ai_sections" in generation_request.context

        # Verify template content includes AI instructions
        template_content_for_ai = generation_request.template_content
        assert "Generate documentation" in template_content_for_ai
        assert "# test_source.py Documentation" in template_content_for_ai

    def test_backward_compatibility_with_traditional_templates(self):
        """Test that traditional templates work unchanged."""
        # Use direct template content for backward compatibility test
        traditional_template = """# {{filename}}

{{description}}

Author: {{author}}
Date: {{date}}"""

        variables = {
            "filename": "legacy_module.py",
            "description": "A legacy module description",
            "author": "Legacy Author",
            "date": "2023-01-01",
        }

        # Process with AI enhancement disabled
        template = AIEnhancedTemplate()
        result = template.process_template(traditional_template, variables, ai_enabled=False)

        # Verify traditional processing works
        assert result.success is True
        assert result.has_ai_enhancement() is False
        assert result.ai_prompt is None

        # Verify content is correctly substituted
        content = result.traditional_content
        assert "# legacy_module.py" in content
        assert "A legacy module description" in content
        assert "Legacy Author" in content
        assert "2023-01-01" in content

    def test_template_validation_and_compatibility_check(self):
        """Test template validation and compatibility checking."""
        # Create template with some potential issues
        problematic_template = """# {{title}}

{{'malformed'}}  <!-- This should be flagged -->

{{}}  <!-- Empty placeholder -->

""" + "x" * 5000 + """  <!-- Very long content -->

""" + " ".join([f"{{{{var{i}}}}}" for i in range(15)]) + """  <!-- Many variables -->
"""

        template = AIEnhancedTemplate()

        # Check compatibility
        issues = template.validate_template_compatibility(problematic_template)

        # Should find multiple issues
        assert len(issues) > 0

        # Check specific issues are detected
        issue_text = " ".join(issues)
        assert "empty placeholders" in issue_text

    def test_factory_function_integration(self):
        """Test using the factory function for template creation."""
        # Use factory function
        template = create_ai_enhanced_template()

        # Process template with direct content
        template_content = "# {{name}}\n{{content}}"
        variables = {"name": "Factory Test", "content": "Content from factory"}
        result = template.process_template(template_content, variables)

        assert result.success is True
        assert "# Factory Test" in result.traditional_content
        assert "Content from factory" in result.traditional_content

    def test_template_with_no_variables(self):
        """Test template processing with static content only."""
        static_template = """# Static Documentation

This template has no variables and should work fine.

## Features
- Static content only
- No variable substitution needed
- Should still work with AI enhancement

## Notes
This is useful for templates that provide structure but no dynamic content.
"""

        template = AIEnhancedTemplate()
        result = template.process_template(static_template, {}, ai_enabled=True)

        assert result.success is True
        assert result.traditional_content == static_template
        assert result.has_ai_enhancement() is True
        assert len(result.ai_prompt.placeholders) == 0  # No variables to extract

    def test_template_with_complex_markdown_structure(self):
        """Test template processing with complex markdown structure."""
        complex_template = """# {{project_name}} API Documentation

## Overview
{{overview}}

## Installation

### Prerequisites
{{prerequisites}}

### Setup
```bash
{{setup_commands}}
```

## API Reference

### Classes

#### {{main_class}}
{{class_description}}

**Methods:**
{{methods_list}}

### Functions

#### {{main_function}}
{{function_description}}

**Parameters:**
{{parameters}}

**Returns:**
{{returns}}

## Examples

### Basic Usage
```python
{{basic_example}}
```

### Advanced Usage
```python
{{advanced_example}}
```

## Configuration

| Option | Default | Description |
|--------|---------|-------------|
| {{config_option_1}} | {{default_1}} | {{description_1}} |
| {{config_option_2}} | {{default_2}} | {{description_2}} |

## Contributing
{{contributing_info}}

## License
{{license_info}}
"""

        variables = {
            "project_name": "TestAPI",
            "overview": "A comprehensive API for testing",
            "prerequisites": "Python 3.8+",
            "setup_commands": "pip install testapi",
            "main_class": "TestClient",
            "class_description": "Main client for API interaction",
            "methods_list": "- connect()\n- query()\n- disconnect()",
            "main_function": "process_data",
            "function_description": "Processes input data",
            "parameters": "data: str, format: str = 'json'",
            "returns": "ProcessedData object",
            "basic_example": "client = TestClient()\nresult = client.query('test')",
            "advanced_example": "with TestClient() as client:\n    result = client.process_data(data, 'xml')",
            "config_option_1": "timeout",
            "default_1": "30",
            "description_1": "Request timeout in seconds",
            "config_option_2": "retries",
            "default_2": "3",
            "description_2": "Number of retry attempts",
            "contributing_info": "Please see CONTRIBUTING.md",
            "license_info": "MIT License",
        }

        template = AIEnhancedTemplate()
        result = template.process_template(complex_template, variables, ai_enabled=True)

        assert result.success is True
        assert result.has_ai_enhancement() is True

        # Verify complex structure is preserved
        content = result.traditional_content
        assert "# TestAPI API Documentation" in content
        assert "## Installation" in content
        assert "### Prerequisites" in content
        assert "Python 3.8+" in content
        assert "```bash" in content
        assert "pip install testapi" in content
        assert "| timeout | 30 |" in content

        # Verify AI prompt captures the complexity
        assert len(result.ai_prompt.placeholders) >= 15  # Should capture many variables
        assert len(result.ai_prompt.sections) >= 1  # Should identify sections

    def test_template_processing_performance(self):
        """Test that template processing completes within reasonable time."""
        # Create moderately complex template
        template_content = "# {{title}}\n" + "\n".join([
            f"## Section {i}\n{{{{content_{i}}}}}" for i in range(10)
        ])

        variables = {
            "title": "Performance Test",
            **{f"content_{i}": f"Content for section {i}" for i in range(10)}
        }

        template = AIEnhancedTemplate()
        result = template.process_template(template_content, variables, ai_enabled=True)

        assert result.success is True
        assert result.processing_time_ms is not None
        assert result.processing_time_ms < 1000  # Should complete within 1 second
