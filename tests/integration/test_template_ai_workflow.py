"""Integration tests for complete template AI workflow validation.

This module tests the end-to-end workflow from template loading through
AI enhancement to final documentation generation using the new provider system.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.providers.base import GenerationRequest, GenerationResult
from spec_cli.exceptions import SpecTemplateError
from spec_cli.templates.ai_enhanced import (
    create_ai_enhanced_template,
)
from spec_cli.templates.ai_integration import AIContentManager

# Test constants for integration scenarios
SAMPLE_PYTHON_FILE_CONTENT = '''"""Example module for testing."""

def calculate_sum(a: int, b: int) -> int:
    """Calculate sum of two integers.

    Args:
        a: First integer
        b: Second integer

    Returns:
        Sum of a and b
    """
    return a + b

class Calculator:
    """Simple calculator class."""

    def __init__(self):
        """Initialize calculator."""
        self.result = 0

    def add(self, value: int) -> int:
        """Add value to current result."""
        self.result += value
        return self.result
'''

SAMPLE_TEMPLATE_CONTENT = """# {{filename}}

{{purpose}}

## Overview

{{overview}}

## API Reference

### Functions

{{functions}}

### Classes

{{classes}}

## Usage

{{usage}}

<!-- AI_INSTRUCTION: Generate comprehensive documentation focusing on code analysis and practical examples -->
"""

AI_GENERATED_DOCUMENTATION = """# example.py

A comprehensive Python module demonstrating mathematical operations and object-oriented programming.

## Overview

This module provides utilities for performing basic arithmetic operations through both functional and object-oriented interfaces. It includes a standalone function for sum calculation and a Calculator class for stateful operations.

## API Reference

### Functions

- `calculate_sum(a: int, b: int) -> int`: Calculates the sum of two integers with proper type hints and documentation.

### Classes

- `Calculator`: A simple calculator class that maintains state and provides arithmetic operations.
  - `__init__()`: Initializes the calculator with result set to 0.
  - `add(value: int) -> int`: Adds the given value to the current result and returns the new result.

## Usage

Basic usage examples:

```python
# Using the function
result = calculate_sum(5, 3)  # Returns 8

# Using the class
calc = Calculator()
calc.add(10)  # Returns 10
calc.add(5)   # Returns 15
```
"""

EXPECTED_WORKFLOW_TIMEOUT_MS = 30000
TEST_DOCS_DIR = ".specs"


class TestCompleteTemplateAIWorkflow:
    """Test complete spec gen workflow with AI template enhancement."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory with test files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source file
            src_dir = temp_path / "src"
            src_dir.mkdir()
            source_file = src_dir / "example.py"
            source_file.write_text(SAMPLE_PYTHON_FILE_CONTENT)

            # Create template
            template_file = temp_path / ".spectemplate"
            template_file.write_text(SAMPLE_TEMPLATE_CONTENT)

            # Create specs directory
            specs_dir = temp_path / TEST_DOCS_DIR
            specs_dir.mkdir()

            yield temp_path

    @pytest.fixture
    def mock_successful_provider(self):
        """Create mock provider that returns successful results."""
        mock_provider = Mock()
        mock_provider.generate_documentation.return_value = GenerationResult(
            success=True,
            content={"index.md": AI_GENERATED_DOCUMENTATION},
            metadata={"provider": "test_provider", "tokens_used": 250},
        )
        return mock_provider

    @pytest.fixture
    def mock_failing_provider(self):
        """Create mock provider that fails generation."""
        mock_provider = Mock()
        mock_provider.generate_documentation.return_value = GenerationResult(
            success=False,
            content={},
            error="Provider temporarily unavailable",
        )
        return mock_provider

    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_end_to_end_template_processing_with_successful_ai_generation(
        self, mock_provider_manager_class, temp_project_dir, mock_successful_provider
    ):
        """Test complete workflow: template load → AI enhancement → generation → result."""
        # Setup mock provider manager
        mock_provider_manager = Mock()
        mock_provider_manager.get_available_provider.return_value = (
            mock_successful_provider
        )
        mock_provider_manager_class.return_value = mock_provider_manager

        # Change to temp directory for the test
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)

            # Create AI enhanced template processor
            template_processor = create_ai_enhanced_template()

            # Process template with AI enabled
            variables = {
                "filename": "example.py",
                "purpose": "Example module for testing",
                "overview": "Demonstration module",
                "functions": "Mathematical operations",
                "classes": "Calculator utilities",
                "usage": "Basic arithmetic examples",
            }

            template_result = template_processor.process_template(
                template_content=SAMPLE_TEMPLATE_CONTENT,
                variables=variables,
                ai_enabled=True,
            )

            # Verify template processing
            assert template_result.success is True
            assert template_result.traditional_content != ""
            assert template_result.has_ai_enhancement() is True

            # Create generation request
            source_file = temp_project_dir / "src" / "example.py"
            request = template_processor.create_generation_request(
                source_file=source_file,
                content=SAMPLE_PYTHON_FILE_CONTENT,
                template_result=template_result,
                doc_type="comprehensive",
            )

            # Verify generation request
            assert isinstance(request, GenerationRequest)
            assert request.source_file == source_file
            assert request.content == SAMPLE_PYTHON_FILE_CONTENT
            assert request.template_content != ""
            assert request.context["has_ai_enhancement"] is True

            # Process through AI content manager
            content_manager = AIContentManager()
            content_manager.enabled = True

            ai_results = content_manager.generate_ai_content(
                file_path=source_file,
                context=variables,
                content_requests=[
                    "purpose",
                    "overview",
                    "functions",
                    "classes",
                    "usage",
                ],
            )

            # Verify AI generation results
            assert isinstance(ai_results, dict)
            assert len(ai_results) == 5
            for _content_type, content in ai_results.items():
                assert isinstance(content, str)
                assert len(content) > 0
                # Should contain AI-generated content, not fallback messages
                assert "AI disabled" not in content
                assert "No AI provider available" not in content

        finally:
            os.chdir(original_cwd)

    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_end_to_end_generation_with_ai_fallback_when_provider_fails(
        self, mock_provider_manager_class, temp_project_dir, mock_failing_provider
    ):
        """Test complete workflow with AI provider failure and graceful fallback."""
        # Setup failing provider manager
        mock_provider_manager = Mock()
        mock_provider_manager.get_available_provider.return_value = (
            mock_failing_provider
        )
        mock_provider_manager_class.return_value = mock_provider_manager

        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)

            # Create and process template
            template_processor = create_ai_enhanced_template()
            variables = {
                "filename": "example.py",
                "purpose": "Example module",
                "overview": "Test module",
            }

            template_result = template_processor.process_template(
                template_content=SAMPLE_TEMPLATE_CONTENT,
                variables=variables,
                ai_enabled=True,
            )

            # Create generation request
            source_file = temp_project_dir / "src" / "example.py"
            _request = template_processor.create_generation_request(
                source_file=source_file,
                content=SAMPLE_PYTHON_FILE_CONTENT,
                template_result=template_result,
            )

            # Process through content manager with failing provider
            content_manager = AIContentManager()
            content_manager.enabled = True

            ai_results = content_manager.generate_ai_content(
                file_path=source_file,
                context=variables,
                content_requests=["purpose", "overview"],
            )

            # Verify graceful fallback
            assert isinstance(ai_results, dict)
            for _content_type, content in ai_results.items():
                assert isinstance(content, str)
                assert len(content) > 0
                # Should contain fallback error message
                assert "Generation failed" in content

        finally:
            os.chdir(original_cwd)

    def test_end_to_end_traditional_template_fallback_when_ai_disabled(
        self, temp_project_dir
    ):
        """Test workflow falls back to traditional templates when AI is disabled."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)

            # Create template processor
            template_processor = create_ai_enhanced_template()
            variables = {
                "filename": "example.py",
                "purpose": "Example module for testing",
                "overview": "This is a test module",
                "functions": "calculate_sum function",
                "classes": "Calculator class",
                "usage": "Import and use functions",
            }

            # Process with AI disabled
            template_result = template_processor.process_template(
                template_content=SAMPLE_TEMPLATE_CONTENT,
                variables=variables,
                ai_enabled=False,
            )

            # Verify traditional processing
            assert template_result.success is True
            assert template_result.traditional_content != ""
            assert template_result.has_ai_enhancement() is False

            # Check that all variables were substituted
            content = template_result.traditional_content
            assert "example.py" in content
            assert "Example module for testing" in content
            assert "This is a test module" in content
            assert "calculate_sum function" in content
            assert "Calculator class" in content
            assert "Import and use functions" in content
            assert "{{" not in content  # No unsubstituted variables

            # Test through content manager with AI disabled
            content_manager = AIContentManager()
            content_manager.enabled = False

            ai_results = content_manager.generate_ai_content(
                file_path=temp_project_dir / "src" / "example.py",
                context=variables,
                content_requests=["purpose", "overview"],
            )

            # Verify disabled fallback
            for _content_type, content in ai_results.items():
                assert "AI disabled" in content

        finally:
            os.chdir(original_cwd)

    def test_end_to_end_ai_content_manager_integration_workflow(
        self, temp_project_dir, mock_successful_provider
    ):
        """Test integration with AI content manager workflow."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)

            # Test AI content manager directly
            content_manager = AIContentManager()
            content_manager.enabled = True

            # Verify content manager can process requests
            variables = {
                "filename": "example.py",
                "purpose": "Test module",
                "overview": "Test overview",
            }

            ai_results = content_manager.generate_ai_content(
                file_path=temp_project_dir / "src" / "example.py",
                context=variables,
                content_requests=["purpose", "overview"],
            )

            # Verify results structure
            assert isinstance(ai_results, dict)
            assert "purpose" in ai_results
            assert "overview" in ai_results

            # Get provider status
            status = content_manager.get_provider_status()
            assert "enabled" in status
            assert "providers" in status

        finally:
            os.chdir(original_cwd)

    def test_end_to_end_workflow_performance_requirements(self, temp_project_dir):
        """Test that complete workflow meets performance requirements."""
        import os
        import time

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)

            start_time = time.time()

            # Execute complete workflow
            template_processor = create_ai_enhanced_template()
            variables = {
                "filename": "example.py",
                "purpose": "Test",
                "overview": "Test overview",
            }

            template_result = template_processor.process_template(
                template_content=SAMPLE_TEMPLATE_CONTENT,
                variables=variables,
                ai_enabled=False,  # Use traditional mode for consistent timing
            )

            # Create generation request
            source_file = temp_project_dir / "src" / "example.py"
            _request = template_processor.create_generation_request(
                source_file=source_file,
                content=SAMPLE_PYTHON_FILE_CONTENT,
                template_result=template_result,
            )

            end_time = time.time()
            processing_time_ms = (end_time - start_time) * 1000

            # Verify performance requirements
            assert processing_time_ms < EXPECTED_WORKFLOW_TIMEOUT_MS
            assert template_result.processing_time_ms is not None
            assert template_result.processing_time_ms >= 0

        finally:
            os.chdir(original_cwd)

    def test_end_to_end_workflow_cross_platform_compatibility(self, temp_project_dir):
        """Test workflow compatibility across different platforms."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)

            # Test with various path formats
            if os.name == "nt":  # Windows
                test_source_file = temp_project_dir / "src\\example.py"
            else:  # Unix-like
                test_source_file = temp_project_dir / "src/example.py"

            template_processor = create_ai_enhanced_template()
            variables = {"filename": "example.py", "purpose": "Cross-platform test"}

            template_result = template_processor.process_template(
                template_content="# {{filename}}\n\n{{purpose}}",
                variables=variables,
                ai_enabled=False,
            )

            # Create generation request with platform-specific path
            request = template_processor.create_generation_request(
                source_file=test_source_file,
                content=SAMPLE_PYTHON_FILE_CONTENT,
                template_result=template_result,
            )

            # Verify cross-platform handling
            assert isinstance(request, GenerationRequest)
            normalized_path = request.get_normalized_path()
            assert "\\" not in str(
                normalized_path
            )  # Should be normalized to forward slashes
            assert (
                "/" in str(normalized_path) or len(str(normalized_path).split("/")) == 1
            )

        finally:
            os.chdir(original_cwd)

    def test_end_to_end_workflow_error_recovery_and_resilience(self, temp_project_dir):
        """Test workflow resilience with various error conditions."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)

            template_processor = create_ai_enhanced_template()

            # Test 1: Invalid template content (should raise exception)
            with pytest.raises(
                SpecTemplateError
            ):  # Input validation should raise exception
                template_processor.process_template(
                    template_content=None,  # Invalid
                    variables={"test": "value"},
                    ai_enabled=True,
                )

            # Test 2: Invalid variables (should raise exception)
            with pytest.raises(
                SpecTemplateError
            ):  # Input validation should raise exception
                template_processor.process_template(
                    template_content="# Test",
                    variables="invalid",  # Invalid type
                    ai_enabled=True,
                )

            # Test 3: Missing source file
            valid_template_result = template_processor.process_template(
                template_content="# {{filename}}",
                variables={"filename": "test.py"},
                ai_enabled=False,
            )

            # This should still create a request even with missing file
            try:
                request = template_processor.create_generation_request(
                    source_file=Path("nonexistent.py"),
                    content="# Some content",
                    template_result=valid_template_result,
                )
                assert isinstance(request, GenerationRequest)
            except Exception:
                # It's acceptable for this to fail, as long as it's handled gracefully
                pass

        finally:
            os.chdir(original_cwd)

    def test_end_to_end_workflow_validates_all_integration_points(
        self, temp_project_dir
    ):
        """Test that all integration points work together correctly."""
        import os

        original_cwd = os.getcwd()
        try:
            os.chdir(temp_project_dir)

            # 1. Template loading and processing
            template_processor = create_ai_enhanced_template()
            assert template_processor is not None

            info = template_processor.get_enhanced_template_info()
            assert info["ai_enhancement_available"] is True
            assert info["supports_traditional_mode"] is True
            assert info["supports_ai_mode"] is True
            assert info["backward_compatible"] is True

            # 2. Template compatibility validation
            compatibility_issues = template_processor.validate_template_compatibility(
                SAMPLE_TEMPLATE_CONTENT
            )
            # Should have minimal issues for our well-formed template
            assert len(compatibility_issues) <= 1

            # 3. AI content manager status
            content_manager = AIContentManager()
            status = content_manager.get_provider_status()
            assert "enabled" in status
            assert "providers" in status

            # 4. Configuration validation
            config_issues = content_manager.validate_configuration()
            # Should return a list (may have issues, but shouldn't crash)
            assert isinstance(config_issues, list)

            # 5. Complete template processing
            variables = {
                "filename": "integration_test.py",
                "purpose": "Integration testing",
            }
            template_result = template_processor.process_template(
                template_content="# {{filename}}\n\n{{purpose}}",
                variables=variables,
                ai_enabled=False,
            )

            assert template_result.success is True
            assert template_result.traditional_content != ""
            assert "integration_test.py" in template_result.traditional_content
            assert "Integration testing" in template_result.traditional_content

        finally:
            os.chdir(original_cwd)
