"""Unit tests for AI Provider Manager - Provider Coordination.

Tests for slice ai_003: AI Provider Manager Unit Tests - Provider Coordination
Target coverage: 85% for ProviderManager.get_available_provider and related functionality
"""

import logging
from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.config.settings import AIConfig, LlamaCppConfig, LocalModelConfig
from spec_cli.ai.providers.base import AIProvider
from spec_cli.ai.providers.manager import ProviderManager, create_workflow_result
from spec_cli.utils.test_helpers.ai_test_doubles import (
    MockGenerationProvider,
    MockLlamaCppProvider,
)


class TestCreateWorkflowResult:
    """Unit tests for create_workflow_result helper function."""

    def test_create_workflow_result_success_with_data(self) -> None:
        """Test successful workflow result creation with data payload."""
        data = {"docs": {"file.py": "content"}}
        message = "Documentation generated successfully"

        result = create_workflow_result(True, data=data, message=message)

        assert result["success"] is True
        assert result["data"] == data
        assert result["message"] == message
        assert "timestamp" in result
        assert isinstance(result["timestamp"], str)
        # Verify timestamp is ISO format
        datetime.fromisoformat(result["timestamp"])

    def test_create_workflow_result_success_minimal(self) -> None:
        """Test successful workflow result with minimal parameters."""
        result = create_workflow_result(True)

        assert result["success"] is True
        assert result["data"] == {}
        assert "message" not in result
        assert "timestamp" in result

    def test_create_workflow_result_failure_with_error(self) -> None:
        """Test failed workflow result creation with error message."""
        error_msg = "Provider initialization failed"
        data = {"attempted_provider": "llamacpp"}

        result = create_workflow_result(False, data=data, error=error_msg)

        assert result["success"] is False
        assert result["error"] == error_msg
        assert result["data"] == data
        assert "timestamp" in result

    def test_create_workflow_result_failure_minimal(self) -> None:
        """Test failed workflow result with minimal parameters."""
        result = create_workflow_result(False)

        assert result["success"] is False
        assert result["error"] == "Unknown error"
        assert result["data"] == {}
        assert "timestamp" in result

    def test_create_workflow_result_none_parameters(self) -> None:
        """Test workflow result creation with None parameters."""
        result = create_workflow_result(True, data=None, message=None)

        assert result["success"] is True
        assert result["data"] == {}
        assert "message" not in result


class TestProviderManager:
    """Unit tests for ProviderManager class - Provider Coordination."""

    def setup_method(self) -> None:
        """Set up test fixtures for each test method."""
        # Create minimal AI config for testing
        self.ai_config = AIConfig(
            enabled=True,
            provider="local",
            local=LocalModelConfig(model_name="test-model"),
            llamacpp=LlamaCppConfig(model_path="test.gguf"),
        )
        self.manager = ProviderManager(self.ai_config)

    def test_init_with_valid_config(self) -> None:
        """Test ProviderManager initialization with valid configuration."""
        manager = ProviderManager(self.ai_config)

        assert manager.ai_config == self.ai_config
        assert manager.logger is not None
        assert isinstance(manager.logger, logging.Logger)

    def test_get_available_provider_ai_disabled(self) -> None:
        """Test get_available_provider when AI is disabled in configuration."""
        # Disable AI in configuration
        self.ai_config.enabled = False
        manager = ProviderManager(self.ai_config)

        with patch.object(manager.logger, "debug") as mock_debug:
            result = manager.get_available_provider()

            assert result is None
            mock_debug.assert_called_once_with("AI provider disabled in configuration")

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    def test_get_available_provider_local_available(
        self, mock_local_provider_class: Any
    ) -> None:
        """Test get_available_provider with available local provider."""
        # Set up mock local provider
        mock_provider = Mock(spec=AIProvider)
        mock_provider.is_available.return_value = True
        mock_local_provider_class.return_value = mock_provider

        # Configure for local provider
        self.ai_config.provider = "local"
        manager = ProviderManager(self.ai_config)

        with patch.object(manager.logger, "info") as mock_info:
            result = manager.get_available_provider()

            assert result == mock_provider
            mock_local_provider_class.assert_called_once_with(self.ai_config.local)
            mock_provider.is_available.assert_called_once()
            mock_info.assert_called_once_with(
                "Local AI provider available with model: %s",
                self.ai_config.local.model_name,
            )

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    def test_get_available_provider_local_unavailable(
        self, mock_local_provider_class: Any
    ) -> None:
        """Test get_available_provider with unavailable local provider."""
        # Set up mock local provider that's not available
        mock_provider = Mock(spec=AIProvider)
        mock_provider.is_available.return_value = False
        mock_local_provider_class.return_value = mock_provider

        # Configure for local provider
        self.ai_config.provider = "local"
        manager = ProviderManager(self.ai_config)

        with patch.object(manager.logger, "warning") as mock_warning:
            result = manager.get_available_provider()

            assert result is None
            mock_local_provider_class.assert_called_once_with(self.ai_config.local)
            mock_provider.is_available.assert_called_once()
            mock_warning.assert_called_once_with("Local AI provider not available")

    @patch("spec_cli.ai.providers.manager.LlamaCppProvider")
    def test_get_available_provider_llamacpp_available(
        self, mock_llamacpp_provider_class: Any
    ) -> None:
        """Test get_available_provider with available LlamaCpp provider."""
        # Set up mock LlamaCpp provider
        mock_provider = Mock(spec=AIProvider)
        mock_provider.is_available.return_value = True
        mock_provider.config = self.ai_config.llamacpp
        mock_llamacpp_provider_class.return_value = mock_provider

        # Configure for LlamaCpp provider
        self.ai_config.provider = "llamacpp"
        manager = ProviderManager(self.ai_config)

        with patch.object(manager.logger, "info") as mock_info:
            result = manager.get_available_provider()

            assert result == mock_provider
            mock_llamacpp_provider_class.assert_called_once_with(
                self.ai_config.llamacpp
            )
            mock_provider.is_available.assert_called_once()
            mock_info.assert_called_once_with(
                "LlamaCpp provider available with model: %s",
                mock_provider.config.model_path,
            )

    @patch("spec_cli.ai.providers.manager.LlamaCppProvider")
    def test_get_available_provider_llamacpp_unavailable(
        self, mock_llamacpp_provider_class: Any
    ) -> None:
        """Test get_available_provider with unavailable LlamaCpp provider."""
        # Set up mock LlamaCpp provider that's not available
        mock_provider = Mock(spec=AIProvider)
        mock_provider.is_available.return_value = False
        mock_llamacpp_provider_class.return_value = mock_provider

        # Configure for LlamaCpp provider
        self.ai_config.provider = "llamacpp"
        manager = ProviderManager(self.ai_config)

        with patch.object(manager.logger, "warning") as mock_warning:
            result = manager.get_available_provider()

            assert result is None
            mock_llamacpp_provider_class.assert_called_once_with(
                self.ai_config.llamacpp
            )
            mock_provider.is_available.assert_called_once()
            mock_warning.assert_called_once_with("LlamaCpp provider not available")

    def test_get_available_provider_unknown_provider(self) -> None:
        """Test get_available_provider with unknown provider type."""
        # Configure for unknown provider
        self.ai_config.provider = "unknown"
        manager = ProviderManager(self.ai_config)

        result = manager.get_available_provider()

        assert result is None

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    def test_get_available_provider_exception_handling(
        self, mock_local_provider_class: Any
    ) -> None:
        """Test get_available_provider handles exceptions gracefully."""
        # Set up mock to raise exception
        mock_local_provider_class.side_effect = Exception(
            "Provider initialization failed"
        )

        # Configure for local provider
        self.ai_config.provider = "local"
        manager = ProviderManager(self.ai_config)

        with patch.object(manager.logger, "warning") as mock_warning:
            result = manager.get_available_provider()

            assert result is None
            mock_warning.assert_called_once_with(
                "Provider selection failed: %s", mock_local_provider_class.side_effect
            )

    def test_get_provider_info_no_provider_available(self) -> None:
        """Test get_provider_info when no provider is available."""
        # Disable AI to ensure no provider is available
        self.ai_config.enabled = False
        manager = ProviderManager(self.ai_config)

        info = manager.get_provider_info()

        expected_info = {
            "ai_enabled": False,
            "configured_provider": "local",
            "provider_available": False,
            "provider_details": {},
        }
        assert info == expected_info

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    def test_get_provider_info_provider_available(
        self, mock_local_provider_class: Any
    ) -> None:
        """Test get_provider_info when provider is available."""
        # Set up mock local provider with provider info
        mock_provider = Mock(spec=AIProvider)
        mock_provider.is_available.return_value = True
        provider_details = {
            "provider_class": "LocalAIProvider",
            "model_name": "test-model",
            "available": True,
        }
        mock_provider.get_provider_info.return_value = provider_details
        mock_local_provider_class.return_value = mock_provider

        # Configure for local provider
        self.ai_config.provider = "local"
        manager = ProviderManager(self.ai_config)

        info = manager.get_provider_info()

        expected_info = {
            "ai_enabled": True,
            "configured_provider": "local",
            "provider_available": True,
            "provider_details": provider_details,
        }
        assert info == expected_info
        mock_provider.get_provider_info.assert_called_once()

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    @patch("spec_cli.ai.providers.manager.LlamaCppProvider")
    def test_provider_selection_order_local_first(
        self, mock_llamacpp_class: Any, mock_local_class: Any
    ) -> None:
        """Test that local provider is checked first when both configured."""
        # Both providers available
        mock_local = Mock(spec=AIProvider)
        mock_local.is_available.return_value = True
        mock_local_class.return_value = mock_local

        mock_llamacpp = Mock(spec=AIProvider)
        mock_llamacpp.is_available.return_value = True
        mock_llamacpp_class.return_value = mock_llamacpp

        # Configure for local provider
        self.ai_config.provider = "local"
        manager = ProviderManager(self.ai_config)

        result = manager.get_available_provider()

        # Should return local provider and not check LlamaCpp
        assert result == mock_local
        mock_local_class.assert_called_once()
        mock_llamacpp_class.assert_not_called()

    def test_logger_configuration(self) -> None:
        """Test that ProviderManager logger is properly configured."""
        manager = ProviderManager(self.ai_config)

        assert manager.logger.name == "spec_cli.ai.providers.manager"
        assert isinstance(manager.logger, logging.Logger)

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    def test_provider_coordination_with_real_config_objects(
        self, mock_local_provider_class: Any
    ) -> None:
        """Test provider coordination with real configuration objects."""
        # Use real config objects instead of mocks
        local_config = LocalModelConfig(
            model_name="Qwen/Qwen2.5-Coder-0.5B-Instruct",
            max_tokens=1024,
            temperature=0.2,
        )

        llamacpp_config = LlamaCppConfig(
            model_path="models/test.gguf", max_tokens=2048, temperature=0.1
        )

        ai_config = AIConfig(
            enabled=True, provider="local", local=local_config, llamacpp=llamacpp_config
        )

        # Set up mock provider
        mock_provider = Mock(spec=AIProvider)
        mock_provider.is_available.return_value = True
        mock_local_provider_class.return_value = mock_provider

        manager = ProviderManager(ai_config)

        result = manager.get_available_provider()

        assert result == mock_provider
        mock_local_provider_class.assert_called_once_with(local_config)

    def test_edge_case_empty_provider_string(self) -> None:
        """Test behavior with empty provider string."""
        self.ai_config.provider = ""
        manager = ProviderManager(self.ai_config)

        result = manager.get_available_provider()

        assert result is None

    def test_get_provider_info_integration_consistency(self) -> None:
        """Test that get_provider_info calls get_available_provider consistently."""
        manager = ProviderManager(self.ai_config)

        # Mock get_available_provider to return None
        with patch.object(
            manager, "get_available_provider", return_value=None
        ) as mock_get:
            info = manager.get_provider_info()

            mock_get.assert_called_once()
            assert info["provider_available"] is False
            assert info["provider_details"] == {}


class TestProviderManagerEdgeCases:
    """Additional edge case tests for ProviderManager."""

    def test_provider_manager_with_none_config(self) -> None:
        """Test ProviderManager behavior with None configuration values."""
        # This tests defensive programming - what happens with malformed config
        ai_config = AIConfig()
        ai_config.provider = None  # type: ignore  # Intentional for testing

        manager = ProviderManager(ai_config)

        result = manager.get_available_provider()

        assert result is None

    @patch("spec_cli.ai.providers.manager.LocalAIProvider")
    def test_provider_exception_during_availability_check(
        self, mock_local_provider_class: Any
    ) -> None:
        """Test provider coordination when availability check raises exception."""
        # Provider creation succeeds but availability check fails
        mock_provider = Mock(spec=AIProvider)
        mock_provider.is_available.side_effect = Exception("Availability check failed")
        mock_local_provider_class.return_value = mock_provider

        ai_config = AIConfig(enabled=True, provider="local")
        manager = ProviderManager(ai_config)

        with patch.object(manager.logger, "warning") as mock_warning:
            result = manager.get_available_provider()

            assert result is None
            mock_warning.assert_called_once()
            assert "Provider selection failed" in str(mock_warning.call_args)

    def test_get_provider_info_exception_in_get_available_provider(self) -> None:
        """Test get_provider_info when get_available_provider raises exception."""
        ai_config = AIConfig(enabled=True, provider="local")
        manager = ProviderManager(ai_config)

        # Mock get_available_provider to raise exception
        with patch.object(
            manager, "get_available_provider", side_effect=Exception("Test error")
        ):
            # The actual implementation doesn't catch the exception, so we expect it to propagate
            with pytest.raises(Exception, match="Test error"):
                manager.get_provider_info()


class TestProviderManagerIntegrationWithMockDoubles:
    """Integration tests using AI test doubles from test helpers."""

    def setup_method(self) -> None:
        """Set up test fixtures using AI test doubles."""
        self.ai_config = AIConfig(
            enabled=True,
            provider="llamacpp",
            llamacpp=LlamaCppConfig(model_path="test.gguf"),
        )
        self.manager = ProviderManager(self.ai_config)
        self.mock_llamacpp = MockLlamaCppProvider()
        self.mock_generation = MockGenerationProvider()

    def test_provider_coordination_with_mock_llamacpp(self) -> None:
        """Test provider coordination using MockLlamaCppProvider."""
        # Add the config attribute that the manager expects
        self.mock_llamacpp.config = self.ai_config.llamacpp

        # Test successful provider coordination
        with patch(
            "spec_cli.ai.providers.manager.LlamaCppProvider",
            return_value=self.mock_llamacpp,
        ):
            # Mock provider is available by default
            result = self.manager.get_available_provider()

            # Type narrowing assertion to satisfy mypy
            assert result is not None
            # We know this is our mock, but mypy sees it as AIProvider
            assert hasattr(result, "_model_exists")  # MockLlamaCppProvider attribute
            assert result.is_available() is True

    def test_provider_coordination_with_unavailable_mock(self) -> None:
        """Test provider coordination when mock provider is unavailable."""
        # Set mock to unavailable state
        self.mock_llamacpp.set_failure_mode("unavailable")

        with patch(
            "spec_cli.ai.providers.manager.LlamaCppProvider",
            return_value=self.mock_llamacpp,
        ):
            result = self.manager.get_available_provider()

            assert result is None

    def test_fallback_behavior_with_test_doubles(self) -> None:
        """Test fallback behavior between providers using test doubles."""
        local_config = LocalModelConfig(model_name="test-model")
        ai_config = AIConfig(enabled=True, provider="local", local=local_config)
        manager = ProviderManager(ai_config)

        # Create unavailable mock local provider
        mock_local = Mock(spec=AIProvider)
        mock_local.is_available.return_value = False

        with patch(
            "spec_cli.ai.providers.manager.LocalAIProvider", return_value=mock_local
        ):
            result = manager.get_available_provider()

            # Should return None since local provider is unavailable
            assert result is None
