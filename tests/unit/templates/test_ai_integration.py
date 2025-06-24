import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.providers.base import GenerationRequest, GenerationResult
from spec_cli.exceptions import SpecTemplateError
from spec_cli.templates.ai_integration import (
    AIContentManager,
    MockAIProvider,
    ai_content_manager,
    ask_llm,
    retry_with_backoff,
)


class TestAIContentManagerWithNewProviders:
    """Test AIContentManager with new provider system integration."""

    @patch("spec_cli.templates.ai_integration.ConfigurationLoader")
    @patch("spec_cli.templates.ai_integration.AIConfigLoader")
    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_ai_content_manager_connects_to_provider_manager(
        self, mock_provider_manager_class, mock_config_loader_class, mock_config_class
    ):
        """Test that AIContentManager connects to ProviderManager."""
        # Setup mocks
        mock_ai_config = Mock()
        mock_ai_config.enabled = True
        mock_ai_config.provider = "llamacpp"

        mock_ai_config_loader = Mock()
        mock_ai_config_loader.load_ai_config.return_value = mock_ai_config
        mock_config_loader_class.return_value = mock_ai_config_loader

        # Create manager
        manager = AIContentManager()

        # Verify initialization
        assert manager.enabled is True
        assert manager.ai_config == mock_ai_config
        mock_provider_manager_class.assert_called_once_with(mock_ai_config)

    @patch("spec_cli.templates.ai_integration.ConfigurationLoader")
    @patch("spec_cli.templates.ai_integration.AIConfigLoader")
    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_generate_ai_content_uses_new_providers(
        self, mock_provider_manager_class, mock_config_loader_class, mock_config_class
    ):
        """Test that generate_ai_content uses new provider system."""
        # Setup mocks
        mock_ai_config = Mock()
        mock_ai_config.enabled = True
        mock_ai_config.provider = "llamacpp"

        mock_ai_config_loader = Mock()
        mock_ai_config_loader.load_ai_config.return_value = mock_ai_config
        mock_config_loader_class.return_value = mock_ai_config_loader

        # Mock provider
        mock_provider = Mock()
        mock_result = GenerationResult(
            success=True,
            content={"index.md": "## Overview\n\nThis is test documentation."},
            metadata={"provider": "test"},
        )
        mock_provider.generate_documentation.return_value = mock_result

        mock_provider_manager = Mock()
        mock_provider_manager.get_available_provider.return_value = mock_provider
        mock_provider_manager_class.return_value = mock_provider_manager

        # Create manager and test
        manager = AIContentManager()
        file_path = Path("test.py")

        # Mock the file reading
        with patch.object(Path, "read_text", return_value="test content"):
            results = manager.generate_ai_content(
                file_path,
                {"test": "context"},
                ["purpose", "overview"],
                max_tokens_per_request=1000,
            )

        # Verify results
        assert "purpose" in results
        assert "overview" in results
        assert "## Overview" in results["overview"]

        # Verify provider was called
        mock_provider.generate_documentation.assert_called_once()
        call_args = mock_provider.generate_documentation.call_args[0][0]
        assert isinstance(call_args, GenerationRequest)
        assert call_args.source_file == file_path
        assert call_args.content == "test content"

    @patch("spec_cli.templates.ai_integration.ConfigurationLoader")
    @patch("spec_cli.templates.ai_integration.AIConfigLoader")
    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_provider_fallback_chain_works(
        self, mock_provider_manager_class, mock_config_loader_class, mock_config_class
    ):
        """Test fallback when provider is not available."""
        # Setup mocks
        mock_ai_config = Mock()
        mock_ai_config.enabled = True
        mock_ai_config.provider = "llamacpp"

        mock_ai_config_loader = Mock()
        mock_ai_config_loader.load_ai_config.return_value = mock_ai_config
        mock_config_loader_class.return_value = mock_ai_config_loader

        # No provider available
        mock_provider_manager = Mock()
        mock_provider_manager.get_available_provider.return_value = None
        mock_provider_manager_class.return_value = mock_provider_manager

        # Create manager and test
        manager = AIContentManager()
        file_path = Path("test.py")

        results = manager.generate_ai_content(
            file_path,
            {"test": "context"},
            ["purpose", "overview"],
        )

        # Should get fallback content
        assert "purpose" in results
        assert "No AI provider available" in results["purpose"]
        assert "overview" in results
        assert "No AI provider available" in results["overview"]

    @patch("spec_cli.templates.ai_integration.ConfigurationLoader")
    @patch("spec_cli.templates.ai_integration.AIConfigLoader")
    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_disabled_ai_returns_placeholder_content(
        self, mock_provider_manager_class, mock_config_loader_class, mock_config_class
    ):
        """Test that disabled AI returns placeholder content."""
        # Setup mocks
        mock_ai_config = Mock()
        mock_ai_config.enabled = False
        mock_ai_config.provider = "disabled"

        mock_ai_config_loader = Mock()
        mock_ai_config_loader.load_ai_config.return_value = mock_ai_config
        mock_config_loader_class.return_value = mock_ai_config_loader

        # Create manager and test
        manager = AIContentManager()
        file_path = Path("test.py")

        results = manager.generate_ai_content(
            file_path,
            {"test": "context"},
            ["purpose", "overview"],
        )

        # Should get disabled placeholders
        assert "purpose" in results
        assert "AI disabled" in results["purpose"]
        assert "overview" in results
        assert "AI disabled" in results["overview"]

    @patch("spec_cli.templates.ai_integration.ConfigurationLoader")
    @patch("spec_cli.templates.ai_integration.AIConfigLoader")
    @patch("spec_cli.templates.ai_integration.ProviderManager")
    def test_generation_result_conversion_to_content_dict(
        self, mock_provider_manager_class, mock_config_loader_class, mock_config_class
    ):
        """Test conversion of GenerationResult to content dict."""
        # Setup mocks
        mock_ai_config = Mock()
        mock_ai_config.enabled = True
        mock_ai_config.provider = "llamacpp"

        mock_ai_config_loader = Mock()
        mock_ai_config_loader.load_ai_config.return_value = mock_ai_config
        mock_config_loader_class.return_value = mock_ai_config_loader

        # Mock provider with complex result
        mock_provider = Mock()
        mock_result = GenerationResult(
            success=True,
            content={
                "index.md": "# Test Documentation\n\n## Overview\n\nThis is a test component for validation.\n\n## Details\n\nMore content here.",
                "history.md": "# History\n\nCreated for testing.",
            },
            metadata={"provider": "test", "tokens": 100},
        )
        mock_provider.generate_documentation.return_value = mock_result

        mock_provider_manager = Mock()
        mock_provider_manager.get_available_provider.return_value = mock_provider
        mock_provider_manager_class.return_value = mock_provider_manager

        # Create manager and test
        manager = AIContentManager()
        file_path = Path("test.py")

        # Mock the file reading
        with patch.object(Path, "read_text", return_value="test content"):
            results = manager.generate_ai_content(
                file_path,
                {"test": "context"},
                ["purpose", "overview", "full_content"],
            )

        # Verify conversion
        assert "purpose" in results
        assert "test component for validation" in results["purpose"]
        assert "overview" in results
        assert "## Overview" in results["overview"]
        assert "test component for validation" in results["overview"]
        assert "full_content" in results
        assert "# Test Documentation" in results["full_content"]


class TestMockProvider:
    """Test MockAIProvider functionality."""

    def test_mock_provider_configurable_responses(self) -> None:
        """Test that mock provider can be configured with custom responses."""
        provider = MockAIProvider()
        file_path = Path("test.py")
        context = {"file_type": "python"}

        # Set custom response
        custom_response = "This is a custom mock response"
        provider.set_response("purpose", custom_response)

        # Test configured response
        result = provider.generate_content(file_path, context, "purpose")
        assert result == custom_response
        assert provider.call_count == 1

        # Test default response for unconfigured type
        default_result = provider.generate_content(file_path, context, "overview")
        assert "Mock AI generated content" in default_result
        assert "overview" in default_result
        assert provider.call_count == 2

    def test_mock_provider_failure_simulation(self) -> None:
        """Test that mock provider can simulate failures."""
        provider = MockAIProvider()
        file_path = Path("test.py")
        context = {"file_type": "python"}

        # Configure to fail
        failure_message = "Simulated API failure"
        provider.set_failure(True, failure_message)

        # Test failure
        with pytest.raises(SpecTemplateError) as exc_info:
            provider.generate_content(file_path, context, "purpose")

        assert failure_message in str(exc_info.value)
        assert provider.is_available() is False

        # Test reset
        provider.reset()
        assert provider.call_count == 0
        assert provider.is_available() is True

    def test_mock_provider_reset_functionality(self) -> None:
        """Test mock provider reset functionality."""
        provider = MockAIProvider()

        # Set some state
        provider.set_response("purpose", "Test response")
        provider.set_failure(True, "Test failure")
        provider.call_count = 5

        # Reset
        provider.reset()

        assert len(provider.responses) == 0
        assert provider.call_count == 0
        assert provider.should_fail is False
        assert provider.is_available() is True

    def test_mock_provider_info(self) -> None:
        """Test mock provider information."""
        provider = MockAIProvider()
        provider.set_response("purpose", "Test")
        provider.set_response("overview", "Test2")

        # Test provider info includes call count
        info = provider.get_provider_info()
        assert info["name"] == "MockProvider"
        assert info["type"] == "mock"
        assert info["call_count"] == 0

        # Generate content to increase call count
        provider.generate_content(Path("test.py"), {}, "purpose")
        info = provider.get_provider_info()
        assert info["call_count"] == 1

        # Test supported types
        types = provider.get_supported_content_types()
        assert "purpose" in types
        assert "overview" in types


class TestAIContentManager:
    """Test AIContentManager functionality."""

    @pytest.fixture
    def clean_manager(self) -> AIContentManager:
        """Create a clean AIContentManager for testing."""
        manager = AIContentManager()
        manager.clear_providers()
        return manager

    # Commented out - PlaceholderAIProvider removed in favor of new provider system
    # def test_ai_manager_registers_providers(
    #     self, clean_manager: AIContentManager
    # ) -> None:
    #     """Test that AI manager can register providers."""
    #     # PlaceholderAIProvider removed - using MockAIProvider instead
    #     mock_placeholder = MockAIProvider()

    #     mock = MockAIProvider()
    #
    #     # Register providers
    #     clean_manager.register_provider("placeholder", placeholder)
    #     clean_manager.register_provider("mock", mock)
    #
    #     # Check registration
    #     status = clean_manager.get_provider_status()
    #     assert len(status["providers"]) == 2
    #     assert "placeholder" in status["providers"]
    #     assert "mock" in status["providers"]
    #
    #     # Check preferred provider is set automatically
    #     assert clean_manager.preferred_provider is not None

    def test_ai_manager_handles_disabled_state(
        self, clean_manager: AIContentManager
    ) -> None:
        """Test AI manager behavior when disabled."""
        # PlaceholderAIProvider removed - using MockAIProvider instead
        mock = MockAIProvider()
        clean_manager.register_provider("mock", mock)

        # Test disabled state (default)
        assert clean_manager.enabled is False

        content = clean_manager.generate_ai_content(
            Path("test.py"), {"file_type": "python"}, ["purpose", "overview"]
        )

        # Should return disabled messages
        assert "AI disabled" in content["purpose"]
        assert "AI disabled" in content["overview"]

        # Enable and test
        clean_manager.set_enabled(True)
        assert clean_manager.enabled is True

        content = clean_manager.generate_ai_content(
            Path("test.py"), {"file_type": "python"}, ["purpose"]
        )

        # Should return actual content
        assert "AI disabled" not in content["purpose"]
        assert "python" in content["purpose"]

    def test_ai_manager_fallback_on_provider_failure(
        self, clean_manager: AIContentManager
    ) -> None:
        """Test fallback behavior when provider fails."""
        mock = MockAIProvider()
        mock.set_failure(True, "Provider failed")

        clean_manager.register_provider("failing_mock", mock)
        clean_manager.set_enabled(True)

        # Generate content - should fallback to placeholder
        content = clean_manager.generate_ai_content(
            Path("test.py"), {"file_type": "python"}, ["purpose"]
        )

        # Should receive fallback content, not failure
        assert "purpose" in content
        assert "AI-generated" in content["purpose"]  # Placeholder signature

    def test_ai_manager_preferred_provider_selection(
        self, clean_manager: AIContentManager
    ) -> None:
        """Test preferred provider selection."""
        # PlaceholderAIProvider removed - using MockAIProvider instead
        mock_placeholder = MockAIProvider()
        mock = MockAIProvider()
        mock.set_response("purpose", "Mock response")

        clean_manager.register_provider("placeholder", mock_placeholder)
        clean_manager.register_provider("mock", mock)
        clean_manager.set_enabled(True)

        # Set preferred provider
        result = clean_manager.set_preferred_provider("mock")
        assert result is True
        assert clean_manager.preferred_provider == "mock"

        # Generate content - should use mock
        content = clean_manager.generate_ai_content(
            Path("test.py"), {"file_type": "python"}, ["purpose"]
        )

        assert content["purpose"] == "Mock response"

        # Test setting non-existent provider
        result = clean_manager.set_preferred_provider("nonexistent")
        assert result is False
        assert clean_manager.preferred_provider == "mock"  # Should remain unchanged

        # Test clearing preferred provider
        result = clean_manager.set_preferred_provider(None)
        assert result is True
        assert clean_manager.preferred_provider is None

    def test_ai_manager_provider_status_reporting(
        self, clean_manager: AIContentManager
    ) -> None:
        """Test comprehensive provider status reporting."""
        # PlaceholderAIProvider removed - using MockAIProvider instead
        mock_placeholder = MockAIProvider()
        mock = MockAIProvider()

        clean_manager.register_provider("placeholder", mock_placeholder)
        clean_manager.register_provider("mock", mock)
        clean_manager.set_preferred_provider("mock")
        clean_manager.set_enabled(True)

        status = clean_manager.get_provider_status()

        # Check overall status
        assert status["enabled"] is True
        assert status["preferred_provider"] == "mock"
        assert len(status["providers"]) == 2

        # Check individual provider status
        placeholder_status = status["providers"]["placeholder"]
        assert placeholder_status["available"] is True
        assert placeholder_status["supported_types"] > 0
        assert "info" in placeholder_status

        mock_status = status["providers"]["mock"]
        assert mock_status["available"] is True
        assert "info" in mock_status

    def test_ai_manager_configuration_validation(
        self, clean_manager: AIContentManager
    ) -> None:
        """Test configuration validation."""
        # Test with no providers
        issues = clean_manager.validate_configuration()
        assert any("No AI providers registered" in issue for issue in issues)

        # Add providers
        # PlaceholderAIProvider removed - using MockAIProvider instead
        mock_placeholder = MockAIProvider()
        mock = MockAIProvider()

        clean_manager.register_provider("placeholder", mock_placeholder)
        clean_manager.register_provider("mock", mock)

        # Test with providers but AI disabled
        issues = clean_manager.validate_configuration()
        assert len(issues) == 0  # Should be valid when disabled

        # Enable AI
        clean_manager.set_enabled(True)
        issues = clean_manager.validate_configuration()
        assert len(issues) == 0  # Should be valid with available providers

        # Set unavailable preferred provider
        mock.set_failure(True)
        clean_manager.set_preferred_provider("mock")
        issues = clean_manager.validate_configuration()
        assert any("not available" in issue for issue in issues)


class TestRetryLogic:
    """Test retry logic and backoff functionality."""

    def test_retry_decorator_exponential_backoff(self) -> None:
        """Test retry decorator with exponential backoff."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01, jitter=False)
        def flaky_function() -> str:
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception(f"Failure {call_count}")
            return f"Success after {call_count} attempts"

        start_time = time.time()
        result = flaky_function()
        elapsed = time.time() - start_time

        assert result == "Success after 3 attempts"
        assert call_count == 3
        assert elapsed > 0.02  # Should have some delay from retries

    def test_retry_decorator_max_retries_exceeded(self) -> None:
        """Test retry decorator when max retries is exceeded."""
        call_count = 0

        @retry_with_backoff(max_retries=2, base_delay=0.01)
        def always_fail() -> str:
            nonlocal call_count
            call_count += 1
            raise Exception(f"Failure {call_count}")

        with pytest.raises(Exception) as exc_info:
            always_fail()

        assert "Failure 3" in str(exc_info.value)  # Should be final attempt
        assert call_count == 3  # Initial + 2 retries

    def test_retry_decorator_immediate_success(self) -> None:
        """Test retry decorator with immediate success."""
        call_count = 0

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def immediate_success() -> str:
            nonlocal call_count
            call_count += 1
            return "Success"

        result = immediate_success()
        assert result == "Success"
        assert call_count == 1


class TestAskLLMFunction:
    """Test ask_llm function."""

    def test_ask_llm_function_with_placeholders(self) -> None:
        """Test ask_llm function returns appropriate placeholders."""
        # Test with disabled AI (default)
        response = ask_llm("What is the purpose of this file?")
        assert "disabled" in response

        # Enable AI for testing
        ai_content_manager.set_enabled(True)

        try:
            # Test purpose-related queries
            response = ask_llm("What is the purpose of this component?")
            assert "purpose" in response.lower()
            assert "AI would analyze" in response

            # Test overview-related queries
            response = ask_llm("Give me an overview of this module")
            assert "## Overview" in response

            # Test how-related queries
            response = ask_llm("How does this function work?")
            assert "This works by" in response

            # Test generic queries
            response = ask_llm("Explain this code structure")
            assert "AI response to:" in response
            assert "Explain this code" in response

        finally:
            # Reset to disabled state
            ai_content_manager.set_enabled(False)

    def test_ask_llm_with_context(self) -> None:
        """Test ask_llm function with context information."""
        ai_content_manager.set_enabled(True)

        try:
            context = {"file_type": "python", "module_name": "test_module"}

            response = ask_llm("What is the purpose?", context=context, max_tokens=500)

            assert isinstance(response, str)
            assert len(response) > 0

        finally:
            ai_content_manager.set_enabled(False)


class TestAIIntegrationComprehensive:
    """Comprehensive AI integration workflow tests."""

    def test_ai_integration_comprehensive_workflow(self) -> None:
        """Test complete AI integration workflow."""
        # Create clean manager
        manager = AIContentManager()
        manager.clear_providers()

        # Register multiple providers
        # PlaceholderAIProvider removed - using MockAIProvider instead
        mock_placeholder = MockAIProvider()
        mock = MockAIProvider()

        # Configure mock with specific responses
        mock.set_response("purpose", "Mock purpose response")
        mock.set_response("overview", "Mock overview response")

        manager.register_provider("placeholder", mock_placeholder)
        manager.register_provider("mock", mock)
        manager.set_preferred_provider("mock")
        manager.set_enabled(True)

        # Test content generation workflow
        file_path = Path("src/models/user.py")
        context = {"file_type": "python", "file_category": "model", "size": 1024}
        content_requests = ["purpose", "overview", "dependencies"]

        # Generate content
        results = manager.generate_ai_content(file_path, context, content_requests)

        # Verify results
        assert len(results) == 3
        assert results["purpose"] == "Mock purpose response"
        assert results["overview"] == "Mock overview response"
        assert "dependencies" in results  # Should get default mock response

        # Test provider status
        status = manager.get_provider_status()
        assert status["enabled"] is True
        assert status["preferred_provider"] == "mock"
        assert len(status["providers"]) == 2

        # Test validation
        issues = manager.validate_configuration()
        assert len(issues) == 0

        # Test fallback when preferred provider fails
        mock.set_failure(True)

        fallback_results = manager.generate_ai_content(file_path, context, ["purpose"])

        # Should get placeholder content as fallback
        assert "AI-generated" in fallback_results["purpose"]

    def test_multiple_provider_coordination(self) -> None:
        """Test coordination between multiple providers."""
        manager = AIContentManager()
        manager.clear_providers()

        # Create providers with different capabilities
        provider1 = MockAIProvider()
        provider1.set_response("purpose", "Provider 1 purpose")

        provider2 = MockAIProvider()
        provider2.set_response("overview", "Provider 2 overview")

        manager.register_provider("provider1", provider1)
        manager.register_provider("provider2", provider2)
        manager.set_enabled(True)

        # Without preferred provider, should use first available
        content = manager.generate_ai_content(
            Path("test.py"), {"file_type": "python"}, ["purpose"]
        )

        # Should use provider1 as it was registered first and is available
        assert content["purpose"] == "Provider 1 purpose"

        # Set unavailable provider as preferred
        provider1.set_failure(True)
        manager.set_preferred_provider("provider1")

        # Should fallback to provider2
        content = manager.generate_ai_content(
            Path("test.py"), {"file_type": "python"}, ["overview"]
        )

        # Should get provider2's configured response
        assert content["overview"] == "Provider 2 overview"
