"""Integration tests for ErrorHandler usage in configuration modules."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.config.loader import ConfigurationLoader
from spec_cli.config.validation import ConfigurationValidator
from spec_cli.exceptions import SpecConfigurationError
from spec_cli.utils.error_handler import ErrorHandler


class TestConfigLoaderErrorIntegration:
    """Test ErrorHandler integration in ConfigurationLoader."""

    def test_config_loader_when_initialized_then_has_error_handler(self):
        """Test that ConfigurationLoader initializes with ErrorHandler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            loader = ConfigurationLoader(root_path)

            assert hasattr(loader, "error_handler")
            assert isinstance(loader.error_handler, ErrorHandler)
            assert loader.error_handler.default_context["component"] == "config_loader"

    def test_config_loading_when_yaml_error_then_uses_error_handler(self):
        """Test YAML parsing errors use ErrorHandler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            config_file = root_path / ".specconfig.yaml"

            # Create invalid YAML
            config_file.write_text("invalid: yaml: content: [")

            loader = ConfigurationLoader(root_path)

            with patch.object(
                loader.error_handler, "log_and_raise"
            ) as mock_log_and_raise:
                mock_log_and_raise.side_effect = SpecConfigurationError("YAML error")

                with pytest.raises(SpecConfigurationError):
                    loader.load_configuration()

                # Should use ErrorHandler
                assert mock_log_and_raise.called
                call_args = mock_log_and_raise.call_args
                assert "load configuration file" in call_args[0][1]
                assert "config_path" in call_args[1]
                assert "config_loading" in call_args[1]

    def test_config_loading_when_toml_error_then_uses_error_handler(self):
        """Test TOML parsing errors use ErrorHandler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            config_file = root_path / "pyproject.toml"

            # Create invalid TOML
            config_file.write_text("[tool.spec\ninvalid toml content")

            loader = ConfigurationLoader(root_path)

            with patch.object(
                loader.error_handler, "log_and_raise"
            ) as mock_log_and_raise:
                mock_log_and_raise.side_effect = SpecConfigurationError("TOML error")

                with pytest.raises(SpecConfigurationError):
                    loader.load_configuration()

                # Should use ErrorHandler for TOML parsing
                assert mock_log_and_raise.called
                call_args = mock_log_and_raise.call_args
                assert "load configuration file" in call_args[0][1]
                assert "config_path" in call_args[1]
                assert "config_loading" in call_args[1]

    def test_config_loading_when_encoding_error_then_uses_error_handler(self):
        """Test encoding errors use ErrorHandler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            config_file = root_path / ".specconfig.yaml"

            # Create file with invalid encoding
            config_file.write_bytes(b"\xff\xfe\x00invalid yaml content")

            loader = ConfigurationLoader(root_path)

            with patch.object(
                loader.error_handler, "log_and_raise"
            ) as mock_log_and_raise:
                mock_log_and_raise.side_effect = SpecConfigurationError(
                    "Encoding error"
                )

                with pytest.raises(SpecConfigurationError):
                    loader.load_configuration()

                # Should use ErrorHandler for encoding issues
                assert mock_log_and_raise.called

    def test_config_loading_when_using_error_handler_then_structured_errors(self):
        """Test that ConfigurationLoader provides structured errors through ErrorHandler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            loader = ConfigurationLoader(root_path)

            # ErrorHandler should have proper context
            assert loader.error_handler.default_context["component"] == "config_loader"

    def test_config_loading_when_file_operation_fails_then_proper_context(self):
        """Test that file operation failures include proper context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            config_file = root_path / ".specconfig.yaml"
            config_file.write_text("debug:\n  enabled: true")

            loader = ConfigurationLoader(root_path)

            # Mock file operations to fail
            with patch(
                "spec_cli.config.loader.yaml.safe_load",
                side_effect=Exception("File error"),
            ):
                with patch.object(
                    loader.error_handler, "log_and_raise"
                ) as mock_log_and_raise:
                    mock_log_and_raise.side_effect = SpecConfigurationError(
                        "File error"
                    )

                    with pytest.raises(SpecConfigurationError):
                        loader.load_configuration()

                    # Should include proper context
                    call_args = mock_log_and_raise.call_args
                    assert "config_path" in call_args[1]
                    assert "config_loading" in call_args[1]


class TestConfigValidatorErrorIntegration:
    """Test ErrorHandler integration in ConfigurationValidator."""

    def test_config_validator_when_initialized_then_has_error_handler(self):
        """Test that ConfigurationValidator initializes with ErrorHandler."""
        validator = ConfigurationValidator()

        assert hasattr(validator, "error_handler")
        assert isinstance(validator.error_handler, ErrorHandler)
        assert (
            validator.error_handler.default_context["component"] == "config_validator"
        )

    def test_config_validation_when_using_error_handler_then_consistent_format(self):
        """Test that validation failures use ErrorHandler for consistent formatting."""
        validator = ConfigurationValidator()

        # Invalid configuration
        config = {"debug": {"level": "INVALID_LEVEL", "enabled": "not_a_boolean"}}

        with patch.object(
            validator.error_handler, "log_and_raise"
        ) as mock_log_and_raise:
            mock_log_and_raise.side_effect = SpecConfigurationError("Validation failed")

            with pytest.raises(SpecConfigurationError):
                validator.validate_and_raise(config)

            # Should use ErrorHandler
            assert mock_log_and_raise.called
            call_args = mock_log_and_raise.call_args
            assert "validate configuration" in call_args[0][1]
            assert "validation_errors" in call_args[1]
            assert "config_keys" in call_args[1]
            assert "validation_stage" in call_args[1]

    def test_validation_error_context_when_multiple_errors_then_structured_info(self):
        """Test that validation errors include structured context information."""
        validator = ConfigurationValidator()

        config = {
            "debug": {"level": 123},  # Should be string
            "terminal": {"use_color": "invalid"},  # Should be boolean
        }

        with patch.object(
            validator.error_handler, "log_and_raise"
        ) as mock_log_and_raise:
            mock_log_and_raise.side_effect = SpecConfigurationError("Validation failed")

            with pytest.raises(SpecConfigurationError):
                validator.validate_and_raise(config)

            # Should include structured validation context
            call_args = mock_log_and_raise.call_args
            assert call_args[1]["config_keys"] == ["debug", "terminal"]
            assert call_args[1]["validation_stage"] == "configuration_validation"
            assert isinstance(call_args[1]["validation_errors"], list)

    def test_validation_success_when_valid_config_then_no_error_handler_calls(self):
        """Test that valid configurations don't trigger ErrorHandler."""
        validator = ConfigurationValidator()

        # Valid configuration
        config = {"debug": {"level": "INFO", "enabled": True}}

        with patch.object(
            validator.error_handler, "log_and_raise"
        ) as mock_log_and_raise:
            # Should not raise any exception
            validator.validate_and_raise(config)

            # ErrorHandler should not be called for valid configs
            assert not mock_log_and_raise.called


class TestConfigErrorHandlerUsagePatterns:
    """Test ErrorHandler usage patterns across config modules."""

    def test_all_config_classes_when_initialized_then_have_error_handler(self):
        """Test that all config classes properly initialize ErrorHandler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)

            # ConfigurationLoader
            loader = ConfigurationLoader(root_path)
            assert hasattr(loader, "error_handler")
            assert loader.error_handler.default_context["component"] == "config_loader"

            # ConfigurationValidator
            validator = ConfigurationValidator()
            assert hasattr(validator, "error_handler")
            assert (
                validator.error_handler.default_context["component"]
                == "config_validator"
            )

    def test_error_handler_context_when_different_components_then_proper_identification(
        self,
    ):
        """Test that different config components have proper ErrorHandler context."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)

            loader = ConfigurationLoader(root_path)
            validator = ConfigurationValidator()

            # Each should have unique component identification
            contexts = [
                loader.error_handler.default_context["component"],
                validator.error_handler.default_context["component"],
            ]

            assert len(set(contexts)) == 2  # All unique
            assert "config_loader" in contexts
            assert "config_validator" in contexts

    def test_config_operations_when_errors_occur_then_structured_context(self):
        """Test that config operations provide structured context through ErrorHandler."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            loader = ConfigurationLoader(root_path)
            validator = ConfigurationValidator()

            # Both should have proper ErrorHandler context
            assert loader.error_handler.default_context["component"] == "config_loader"
            assert (
                validator.error_handler.default_context["component"]
                == "config_validator"
            )

            # Context should be unique for debugging
            assert (
                loader.error_handler.default_context["component"]
                != validator.error_handler.default_context["component"]
            )

    def test_error_handling_consistency_when_config_errors_then_centralized_patterns(
        self,
    ):
        """Test that config error handling follows centralized patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            root_path = Path(temp_dir)
            config_file = root_path / ".specconfig.yaml"
            config_file.write_text("invalid: yaml: [")

            loader = ConfigurationLoader(root_path)
            validator = ConfigurationValidator()

            # Both use ErrorHandler for consistent error handling
            assert isinstance(loader.error_handler, ErrorHandler)
            assert isinstance(validator.error_handler, ErrorHandler)

            # Both should re-raise as SpecConfigurationError
            with patch.object(loader.error_handler, "log_and_raise") as mock_loader:
                mock_loader.side_effect = SpecConfigurationError("Loader error")
                with pytest.raises(SpecConfigurationError):
                    loader.load_configuration()

            invalid_config = {"debug": {"level": 123}}
            with patch.object(
                validator.error_handler, "log_and_raise"
            ) as mock_validator:
                mock_validator.side_effect = SpecConfigurationError("Validator error")
                with pytest.raises(SpecConfigurationError):
                    validator.validate_and_raise(invalid_config)
