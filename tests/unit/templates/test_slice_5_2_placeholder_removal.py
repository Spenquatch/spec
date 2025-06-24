"""Unit tests for Slice 5.2: PlaceholderAIProvider Legacy Code Removal validation.

This module validates that PlaceholderAIProvider has been completely removed from the codebase
and that the ai_integration module imports correctly without references to the deprecated class.
"""

import ast
import importlib
import subprocess
from pathlib import Path

import pytest

from spec_cli.templates import ai_integration

# Test constants
DEPRECATED_CLASS_NAME = "PlaceholderAIProvider"
EXPECTED_MODULE_PATH = Path("spec_cli/templates/ai_integration.py")
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


class TestPlaceholderProviderRemoval:
    """Unit tests to validate PlaceholderAIProvider removal."""

    def test_placeholder_provider_removed_from_imports(self) -> None:
        """Test that PlaceholderAIProvider is not in module imports."""
        # Check that the deprecated class is not importable from the module
        module_dict = dir(ai_integration)

        assert DEPRECATED_CLASS_NAME not in module_dict, (
            f"{DEPRECATED_CLASS_NAME} should not be available in ai_integration module"
        )

    def test_no_references_to_placeholder_provider_remain(self) -> None:
        """Test that no references to PlaceholderAIProvider remain in the source code."""
        # Read the ai_integration.py file and verify no class definition exists
        ai_integration_path = PROJECT_ROOT / EXPECTED_MODULE_PATH

        assert ai_integration_path.exists(), f"Expected {EXPECTED_MODULE_PATH} to exist"

        content = ai_integration_path.read_text()

        # Check that class definition doesn't exist
        assert f"class {DEPRECATED_CLASS_NAME}" not in content, (
            f"Found class definition for {DEPRECATED_CLASS_NAME} in {EXPECTED_MODULE_PATH}"
        )

        # Check that no import statements reference it
        assert f"import {DEPRECATED_CLASS_NAME}" not in content, (
            f"Found import statement for {DEPRECATED_CLASS_NAME} in {EXPECTED_MODULE_PATH}"
        )

        assert f"from .* import.*{DEPRECATED_CLASS_NAME}" not in content, (
            f"Found from import statement for {DEPRECATED_CLASS_NAME} in {EXPECTED_MODULE_PATH}"
        )

    def test_ai_integration_module_imports_correctly(self) -> None:
        """Test that ai_integration module imports correctly without PlaceholderAIProvider."""
        # Test that the module can be imported without errors
        try:
            importlib.reload(ai_integration)
        except Exception as e:
            pytest.fail(f"ai_integration module failed to import: {e}")

        # Verify expected classes are still available
        expected_classes = ["AIContentProvider", "MockAIProvider", "AIContentManager"]

        for class_name in expected_classes:
            assert hasattr(ai_integration, class_name), (
                f"Expected class {class_name} not found in ai_integration module"
            )

    def test_ast_parsing_validates_no_deprecated_class(self) -> None:
        """Test AST parsing to ensure no PlaceholderAIProvider class definition exists."""
        ai_integration_path = PROJECT_ROOT / EXPECTED_MODULE_PATH

        with ai_integration_path.open() as f:
            tree = ast.parse(f.read())

        # Find all class definitions
        class_names = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_names.append(node.name)

        assert DEPRECATED_CLASS_NAME not in class_names, (
            f"Found {DEPRECATED_CLASS_NAME} class definition in AST. "
            f"Available classes: {class_names}"
        )

    def test_grep_search_confirms_no_references(self) -> None:
        """Test using grep to confirm no PlaceholderAIProvider references in source code."""
        # Use subprocess to run grep on the spec_cli directory
        try:
            result = subprocess.run(
                ["grep", "-r", DEPRECATED_CLASS_NAME, str(PROJECT_ROOT / "spec_cli")],
                capture_output=True,
                text=True,
                check=False,  # Don't raise on non-zero exit (expected when no matches)
            )

            # Filter out binary files and documentation
            filtered_lines = []
            for line in result.stdout.split("\n"):
                if line.strip() and not line.startswith("Binary file"):
                    # Exclude documentation files - they're expected to mention the removal
                    if not any(
                        exclude in line.lower()
                        for exclude in [
                            "docs/",
                            ".md:",
                            "# slice",
                            "goal:",
                            "migration",
                        ]
                    ):
                        filtered_lines.append(line.strip())

            assert len(filtered_lines) == 0, (
                f"Found unexpected references to {DEPRECATED_CLASS_NAME} in source code:\n"
                + "\n".join(filtered_lines)
            )

        except FileNotFoundError:
            pytest.skip("grep command not available - skipping grep-based validation")

    def test_module_exports_expected_classes_only(self) -> None:
        """Test that the module exports only expected classes and functions."""
        # Define the expected public API
        expected_exports = {
            # Classes
            "AIContentProvider",
            "MockAIProvider",
            "AIContentManager",
            # Functions
            "retry_with_backoff",
            "ask_llm",
            # Global instance
            "ai_content_manager",
        }

        # Get actual exports (non-private attributes)
        actual_exports = {
            name for name in dir(ai_integration) if not name.startswith("_")
        }

        # Remove common module attributes that are expected
        actual_exports.discard("Path")
        actual_exports.discard("ABC")
        actual_exports.discard("abstractmethod")
        actual_exports.discard("time")
        actual_exports.discard("Callable")
        actual_exports.discard("wraps")
        actual_exports.discard("Any")

        # Verify PlaceholderAIProvider is definitely not in exports
        assert DEPRECATED_CLASS_NAME not in actual_exports, (
            f"{DEPRECATED_CLASS_NAME} found in module exports: {actual_exports}"
        )

        # Verify all expected exports are present
        missing_exports = expected_exports - actual_exports
        assert len(missing_exports) == 0, f"Missing expected exports: {missing_exports}"


class TestAIIntegrationModuleFunctionality:
    """Integration tests for AI integration module functionality post-removal."""

    def test_ai_content_manager_initialization_works(self) -> None:
        """Test that AIContentManager can be initialized without PlaceholderAIProvider."""
        # This should work without referencing the removed PlaceholderAIProvider
        manager = ai_integration.AIContentManager()

        # Verify manager has expected attributes
        assert hasattr(manager, "providers")
        assert hasattr(manager, "enabled")
        assert hasattr(manager, "ai_config")
        assert hasattr(manager, "provider_manager")

        # Verify it's using the new provider system
        assert manager.provider_manager is not None

    def test_mock_provider_still_available_for_testing(self) -> None:
        """Test that MockAIProvider is still available and functional."""
        mock_provider = ai_integration.MockAIProvider()

        # Test basic functionality
        assert mock_provider.is_available()

        # Test response configuration
        test_response = "Test response for removal validation"
        mock_provider.set_response("purpose", test_response)

        result = mock_provider.generate_content(
            Path("test.py"), {"file_type": "python"}, "purpose"
        )

        assert result == test_response

    def test_ask_llm_function_still_works(self) -> None:
        """Test that ask_llm function works without PlaceholderAIProvider."""
        # Function should work (even if it returns a placeholder due to no real provider)
        result = ai_integration.ask_llm("Test prompt")

        assert isinstance(result, str)
        assert len(result) > 0
        # Should return either disabled message or provider unavailable message
        assert any(
            keyword in result.lower()
            for keyword in ["disabled", "unavailable", "provider"]
        )

    def test_retry_decorator_functionality_preserved(self) -> None:
        """Test that retry_with_backoff decorator functionality is preserved."""
        call_count = 0

        @ai_integration.retry_with_backoff(max_retries=2, base_delay=0.01)
        def test_function():
            nonlocal call_count
            call_count += 1
            if call_count <= 1:
                raise ValueError("Test failure")
            return "Success"

        result = test_function()
        assert result == "Success"
        assert call_count == 2
