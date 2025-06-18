"""Integration tests for Slice 3.1a: AI Provider Integration."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Test constants
SAMPLE_PYTHON_CODE = '''"""Sample Python module for AI documentation generation."""

def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number.

    Args:
        n: The position in the Fibonacci sequence

    Returns:
        The nth Fibonacci number

    Raises:
        ValueError: If n is negative
    """
    if n < 0:
        raise ValueError("n must be non-negative")
    elif n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)


class MathUtils:
    """Utility class for mathematical operations."""

    @staticmethod
    def is_prime(num: int) -> bool:
        """Check if a number is prime."""
        if num < 2:
            return False
        for i in range(2, int(num ** 0.5) + 1):
            if num % i == 0:
                return False
        return True
'''

EXPECTED_AI_CONTENT = """# Fibonacci Module Documentation

This module provides mathematical utilities including Fibonacci number calculation and prime number checking.

## Functions

### fibonacci(n: int) -> int
Calculates the nth Fibonacci number using recursive approach.

### MathUtils.is_prime(num: int) -> bool
Checks if a given number is prime.
"""


class TestSlice31aAIProviderIntegration:
    """Integration tests for AI provider integration with real workflow."""

    @pytest.fixture
    def sample_source_file(self, tmp_path):
        """Create a sample source file for testing."""
        source_file = tmp_path / "math_utils.py"
        source_file.write_text(SAMPLE_PYTHON_CODE)
        return source_file

    @pytest.fixture
    def mock_ai_config(self):
        """Create mock AI configuration."""
        config = Mock()
        config.enabled = True
        config.provider = "local"
        config.local = Mock()
        config.local.model_name = "test-model"
        config.local.max_tokens = 2000
        config.local.temperature = 0.3
        return config

    @pytest.fixture
    def mock_successful_provider(self):
        """Create mock AI provider that returns successful results."""
        provider = Mock()
        provider.__class__.__name__ = "LocalAIProvider"
        provider.provider_type = "local"
        provider.is_available.return_value = True

        # Mock successful generation result
        result = Mock()
        result.success = True
        result.content = {"index.md": EXPECTED_AI_CONTENT}
        result.error = None
        result.metadata = {
            "tokens_used": 150,
            "generation_time_ms": 2500,
            "model_name": "test-model",
        }
        provider.generate_documentation.return_value = result
        provider.get_provider_info.return_value = {
            "provider_type": "local",
            "model_name": "test-model",
            "available": True,
        }
        return provider

    def test_integration_end_to_end_ai_generation_produces_documentation(
        self, sample_source_file, mock_ai_config, mock_successful_provider
    ):
        """Test complete AI generation workflow from file to documentation."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        with (
            patch(
                "spec_cli.ai.generation.ai_generator.AIConfigLoader"
            ) as mock_loader_class,
            patch(
                "spec_cli.ai.generation.ai_generator.ProviderManager"
            ) as mock_manager_class,
        ):
            # Setup configuration loading
            mock_loader = Mock()
            mock_loader.load_ai_config.return_value = mock_ai_config
            mock_loader_class.return_value = mock_loader

            # Setup provider management
            mock_manager = Mock()
            mock_manager.get_available_provider.return_value = mock_successful_provider
            mock_manager_class.return_value = mock_manager

            # Execute AI generation
            result = generate_with_ai(sample_source_file, "index")

            # Verify successful generation
            assert result["success"] is True
            assert "data" in result
            assert "generated_docs" in result["data"]
            assert "generation_metadata" in result["data"]

            # Verify generated content
            generated_docs = result["data"]["generated_docs"]
            assert str(sample_source_file) in generated_docs
            assert generated_docs[str(sample_source_file)] == EXPECTED_AI_CONTENT

            # Verify metadata structure
            metadata = result["data"]["generation_metadata"]
            required_metadata_fields = {
                "provider_type",
                "generation_time",
                "files_generated",
                "doc_type",
                "source_file",
                "content_length",
            }
            assert all(field in metadata for field in required_metadata_fields)

            # Verify metadata values
            assert metadata["provider_type"] == "LocalAIProvider"
            assert metadata["doc_type"] == "index"
            assert metadata["files_generated"] == 1
            assert metadata["source_file"] == str(sample_source_file)
            assert metadata["content_length"] == len(EXPECTED_AI_CONTENT)

    def test_integration_when_ai_provider_unavailable_then_signals_fallback(
        self, sample_source_file, mock_ai_config
    ):
        """Test workflow when AI provider is not available."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        with (
            patch(
                "spec_cli.ai.generation.ai_generator.AIConfigLoader"
            ) as mock_loader_class,
            patch(
                "spec_cli.ai.generation.ai_generator.ProviderManager"
            ) as mock_manager_class,
        ):
            # Setup configuration loading
            mock_loader = Mock()
            mock_loader.load_ai_config.return_value = mock_ai_config
            mock_loader_class.return_value = mock_loader

            # Setup provider management - no provider available
            mock_manager = Mock()
            mock_manager.get_available_provider.return_value = None
            mock_manager_class.return_value = mock_manager

            # Execute AI generation
            result = generate_with_ai(sample_source_file, "index")

            # Verify fallback signaling
            assert result["success"] is False
            assert "No AI provider available" in result["error"]
            assert result["data"]["fallback_needed"] is True

    def test_integration_when_ai_generation_fails_then_signals_fallback(
        self, sample_source_file, mock_ai_config
    ):
        """Test workflow when AI generation fails."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        # Create failing provider
        failing_provider = Mock()
        failing_provider.provider_type = "local"
        failing_provider.is_available.return_value = True

        # Mock failed generation result
        failed_result = Mock()
        failed_result.success = False
        failed_result.content = None
        failed_result.error = "Model generation failed: out of memory"
        failing_provider.generate_documentation.return_value = failed_result

        with (
            patch(
                "spec_cli.ai.generation.ai_generator.AIConfigLoader"
            ) as mock_loader_class,
            patch(
                "spec_cli.ai.generation.ai_generator.ProviderManager"
            ) as mock_manager_class,
        ):
            # Setup configuration loading
            mock_loader = Mock()
            mock_loader.load_ai_config.return_value = mock_ai_config
            mock_loader_class.return_value = mock_loader

            # Setup provider management - failing provider
            mock_manager = Mock()
            mock_manager.get_available_provider.return_value = failing_provider
            mock_manager_class.return_value = mock_manager

            # Execute AI generation
            result = generate_with_ai(sample_source_file, "index")

            # Verify fallback signaling
            assert result["success"] is False
            assert "Model generation failed" in result["error"]
            assert result["data"]["fallback_needed"] is True

    def test_integration_configuration_override_affects_provider_selection(
        self, sample_source_file
    ):
        """Test that configuration overrides are properly applied."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        # Base configuration with AI enabled
        base_config = Mock()
        base_config.enabled = True
        base_config.provider = "local"

        # Override to disable AI
        config_override = {"enabled": False}

        with (
            patch(
                "spec_cli.ai.generation.ai_generator.AIConfigLoader"
            ) as mock_loader_class,
            patch(
                "spec_cli.ai.generation.ai_generator.ProviderManager"
            ) as mock_manager_class,
        ):
            # Setup configuration loading
            mock_loader = Mock()
            mock_loader.load_ai_config.return_value = base_config
            mock_loader_class.return_value = mock_loader

            # Setup provider management
            mock_manager = Mock()
            mock_manager.get_available_provider.return_value = None
            mock_manager_class.return_value = mock_manager

            # Execute AI generation with override
            result = generate_with_ai(sample_source_file, "index", config_override)

            # Verify override was applied (AI should be disabled)
            assert base_config.enabled is False
            assert result["success"] is False

    def test_integration_handles_file_reading_errors_gracefully(
        self, tmp_path, mock_ai_config, mock_successful_provider
    ):
        """Test integration handles file reading errors gracefully."""
        from spec_cli.ai.generation.ai_generator import (
            generate_with_ai,
        )

        # Create a file that will cause reading errors
        problem_file = tmp_path / "problem.py"
        problem_file.write_text("test content")

        with (
            patch(
                "spec_cli.ai.generation.ai_generator.AIConfigLoader"
            ) as mock_loader_class,
            patch(
                "spec_cli.ai.generation.ai_generator.ProviderManager"
            ) as mock_manager_class,
        ):
            # Setup mocks
            mock_loader = Mock()
            mock_loader.load_ai_config.return_value = mock_ai_config
            mock_loader_class.return_value = mock_loader

            mock_manager = Mock()
            mock_manager.get_available_provider.return_value = mock_successful_provider
            mock_manager_class.return_value = mock_manager

            # Mock file reading to fail
            with patch.object(Path, "read_text") as mock_read:
                mock_read.side_effect = [
                    UnicodeDecodeError("utf-8", b"", 0, 1, "invalid"),
                    Exception("File read failed"),
                ]

                result = generate_with_ai(problem_file, "index")

                # Should handle error gracefully and signal fallback
                assert result["success"] is False
                assert "Failed to read file content" in result["error"]
                assert result["data"]["fallback_needed"] is True

    def test_integration_directory_processing_workflow(
        self, tmp_path, mock_ai_config, mock_successful_provider
    ):
        """Test AI generation workflow for directories."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        # Create a test directory
        test_dir = tmp_path / "test_package"
        test_dir.mkdir()
        (test_dir / "__init__.py").write_text("# Package init")
        (test_dir / "module.py").write_text(SAMPLE_PYTHON_CODE)

        with (
            patch(
                "spec_cli.ai.generation.ai_generator.AIConfigLoader"
            ) as mock_loader_class,
            patch(
                "spec_cli.ai.generation.ai_generator.ProviderManager"
            ) as mock_manager_class,
        ):
            # Setup mocks
            mock_loader = Mock()
            mock_loader.load_ai_config.return_value = mock_ai_config
            mock_loader_class.return_value = mock_loader

            mock_manager = Mock()
            mock_manager.get_available_provider.return_value = mock_successful_provider
            mock_manager_class.return_value = mock_manager

            # Execute AI generation on directory
            result = generate_with_ai(test_dir, "index")

            # Verify successful processing
            assert result["success"] is True
            assert str(test_dir) in result["data"]["generated_docs"]
            assert result["data"]["generation_metadata"]["doc_type"] == "index"

    def test_integration_performance_requirements_met(
        self, sample_source_file, mock_ai_config, mock_successful_provider
    ):
        """Test that AI generation meets performance requirements."""
        import time

        from spec_cli.ai.generation.ai_generator import generate_with_ai

        with (
            patch(
                "spec_cli.ai.generation.ai_generator.AIConfigLoader"
            ) as mock_loader_class,
            patch(
                "spec_cli.ai.generation.ai_generator.ProviderManager"
            ) as mock_manager_class,
        ):
            # Setup mocks
            mock_loader = Mock()
            mock_loader.load_ai_config.return_value = mock_ai_config
            mock_loader_class.return_value = mock_loader

            mock_manager = Mock()
            mock_manager.get_available_provider.return_value = mock_successful_provider
            mock_manager_class.return_value = mock_manager

            # Measure generation time
            start_time = time.time()
            result = generate_with_ai(sample_source_file, "index")
            end_time = time.time()

            # Verify performance requirement (20 seconds per file)
            generation_time = end_time - start_time
            assert generation_time < 20.0, (
                f"Generation took {generation_time:.2f}s, should be < 20s"
            )
            assert result["success"] is True

    def test_integration_provider_manager_integration_with_real_config_loading(
        self, mock_ai_config
    ):
        """Test provider manager integration with configuration loading."""
        from spec_cli.ai.config.loader import AIConfigLoader
        from spec_cli.ai.providers.manager import ProviderManager

        # Test real integration between components
        with patch.object(
            AIConfigLoader, "load_ai_config", return_value=mock_ai_config
        ):
            config_loader = AIConfigLoader()
            loaded_config = config_loader.load_ai_config()

            # Test provider manager with loaded config
            provider_manager = ProviderManager(loaded_config)

            # This should work without errors even if no provider is available
            provider_info = provider_manager.get_provider_info()

            assert "ai_enabled" in provider_info
            assert "configured_provider" in provider_info
            assert "provider_available" in provider_info

    def test_integration_error_handling_preserves_context(self, sample_source_file):
        """Test that error handling preserves context for debugging."""
        from spec_cli.ai.generation.ai_generator import generate_with_ai

        # Force an exception during configuration loading
        with patch(
            "spec_cli.ai.generation.ai_generator.AIConfigLoader"
        ) as mock_loader_class:
            mock_loader_class.side_effect = Exception("Configuration system failure")

            result = generate_with_ai(sample_source_file, "index")

            # Verify error context is preserved
            assert result["success"] is False
            assert "AI generation initialization failed" in result["error"]
            assert "Configuration system failure" in result["error"]
            assert result["data"]["fallback_needed"] is True

    def test_integration_cross_platform_path_handling(
        self, mock_ai_config, mock_successful_provider
    ):
        """Test cross-platform path handling in integration workflow."""
        from pathlib import Path

        from spec_cli.ai.generation.ai_generator import generate_with_ai

        # Test with different path styles
        test_paths = [
            Path("/unix/style/path.py"),
            Path("relative/path.py"),
        ]

        for test_path in test_paths:
            with (
                patch(
                    "spec_cli.ai.generation.ai_generator.AIConfigLoader"
                ) as mock_loader_class,
                patch(
                    "spec_cli.ai.generation.ai_generator.ProviderManager"
                ) as mock_manager_class,
                patch.object(Path, "exists", return_value=True),
                patch.object(Path, "is_file", return_value=True),
                patch.object(Path, "read_text", return_value=SAMPLE_PYTHON_CODE),
            ):
                # Setup mocks
                mock_loader = Mock()
                mock_loader.load_ai_config.return_value = mock_ai_config
                mock_loader_class.return_value = mock_loader

                mock_manager = Mock()
                mock_manager.get_available_provider.return_value = (
                    mock_successful_provider
                )
                mock_manager_class.return_value = mock_manager

                # Execute generation
                result = generate_with_ai(test_path, "index")

                # Verify path handling
                assert result["success"] is True
                assert str(test_path) in result["data"]["generated_docs"]
