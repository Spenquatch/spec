"""Unit tests for Slice P1.1b - SpecContext core implementation.

Tests comprehensive SpecContext functionality including immutable dataclass
creation, dependency validation, context modification methods, and hash generation.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.core.context import (
    SpecConsoleInterface,
    SpecContext,
    SpecContextError,
    SpecProgressInterface,
    SpecSettingsInterface,
)

# Test constants
DEFAULT_CONSOLE_WIDTH = 80
DEFAULT_DEBUG_ENABLED = False
SAMPLE_ROOT_PATH = "/test/path"
SAMPLE_OPERATION_ID = "op_001"
SAMPLE_HASH_LENGTH = 64  # SHA-256 hex length
IMMUTABILITY_ERROR_MESSAGE = "SpecContext must be immutable"
SETTINGS_REQUIRED_MESSAGE = "SpecContext requires settings dependency"
CONSOLE_REQUIRED_MESSAGE = "SpecContext requires console dependency"
PROGRESS_REQUIRED_MESSAGE = "SpecContext requires progress dependency"


class TestSpecContextCreation:
    """Test SpecContext creation with valid dependencies."""

    def test_spec_context_creation_when_valid_dependencies_then_creates_immutable_context(
        self,
    ):
        """Test SpecContext creation with valid dependency inputs."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context = SpecContext(settings=settings, console=console, progress=progress)

        assert context.settings is settings
        assert context.console is console
        assert context.progress is progress
        assert context.__dataclass_params__.frozen is True

    def test_spec_context_creation_when_all_interfaces_then_provides_expected_methods(
        self,
    ):
        """Test that all dependency interfaces provide expected methods."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context = SpecContext(settings=settings, console=console, progress=progress)

        # Test settings interface
        assert hasattr(context.settings, "debug_enabled")
        assert hasattr(context.settings, "get_setting")
        assert hasattr(context.settings, "validate_configuration")

        # Test console interface
        assert hasattr(context.console, "print_message")
        assert hasattr(context.console, "print_error")
        assert hasattr(context.console, "get_width")

        # Test progress interface
        assert hasattr(context.progress, "show_progress")
        assert hasattr(context.progress, "update_status")
        assert hasattr(context.progress, "start_operation")


class TestSpecContextImmutability:
    """Test SpecContext immutability enforcement."""

    def test_spec_context_immutability_when_attribute_modification_then_raises_frozen_error(
        self,
    ):
        """Test frozen dataclass prevents attribute modification."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context = SpecContext(settings=settings, console=console, progress=progress)

        with pytest.raises(AttributeError):
            context.settings = Mock()  # type: ignore

        with pytest.raises(AttributeError):
            context.console = Mock()  # type: ignore

        with pytest.raises(AttributeError):
            context.progress = Mock()  # type: ignore

    @patch("spec_cli.core.context.validate_context_immutability")
    def test_spec_context_immutability_when_validation_fails_then_raises_context_error(
        self, mock_validate
    ):
        """Test that immutability validation failure raises SpecContextError."""
        mock_validate.return_value = False

        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        with pytest.raises(SpecContextError, match=IMMUTABILITY_ERROR_MESSAGE):
            SpecContext(settings=settings, console=console, progress=progress)


class TestSpecContextValidation:
    """Test SpecContext dependency validation."""

    def test_spec_context_validation_when_valid_dependencies_then_passes_validation(self):
        """Test that valid dependencies pass validation."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        # This should not raise any exceptions
        context = SpecContext(settings=settings, console=console, progress=progress)
        assert context.settings is settings
        assert context.console is console
        assert context.progress is progress


class TestSpecContextModification:
    """Test SpecContext modification methods."""

    def test_spec_context_with_settings_when_overrides_then_creates_new_context(self):
        """Test with_settings creates new context with overrides."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        original_context = SpecContext(
            settings=settings, console=console, progress=progress
        )

        new_context = original_context.with_settings(
            debug_enabled=True, console_width=120
        )

        assert new_context is not original_context
        assert new_context.settings is not original_context.settings
        assert new_context.console is original_context.console
        assert new_context.progress is original_context.progress
        assert new_context.settings.debug_enabled is True
        assert new_context.settings.console_width == 120

    def test_spec_context_with_console_when_replacement_then_creates_new_context(self):
        """Test with_console creates new context with console replacement."""
        settings = SpecSettingsInterface()
        original_console = SpecConsoleInterface()
        progress = SpecProgressInterface()
        new_console = SpecConsoleInterface()

        original_context = SpecContext(
            settings=settings, console=original_console, progress=progress
        )

        new_context = original_context.with_console(new_console)

        assert new_context is not original_context
        assert new_context.settings is original_context.settings
        assert new_context.console is new_console
        assert new_context.progress is original_context.progress

    def test_spec_context_with_console_when_valid_replacement_then_succeeds(self):
        """Test with_console succeeds with valid console replacement."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()
        new_console = SpecConsoleInterface()

        context = SpecContext(settings=settings, console=console, progress=progress)
        new_context = context.with_console(new_console)

        assert new_context.console is new_console
        assert new_context.settings is settings
        assert new_context.progress is progress

    def test_spec_context_with_progress_when_replacement_then_creates_new_context(self):
        """Test with_progress creates new context with progress replacement."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        original_progress = SpecProgressInterface()
        new_progress = SpecProgressInterface()

        original_context = SpecContext(
            settings=settings, console=console, progress=original_progress
        )

        new_context = original_context.with_progress(new_progress)

        assert new_context is not original_context
        assert new_context.settings is original_context.settings
        assert new_context.console is original_context.console
        assert new_context.progress is new_progress

    def test_spec_context_with_progress_when_valid_replacement_then_succeeds(self):
        """Test with_progress succeeds with valid progress replacement."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()
        new_progress = SpecProgressInterface()

        context = SpecContext(settings=settings, console=console, progress=progress)
        new_context = context.with_progress(new_progress)

        assert new_context.progress is new_progress
        assert new_context.settings is settings
        assert new_context.console is console


class TestSpecContextHashing:
    """Test SpecContext hash generation and equality."""

    def test_spec_context_hash_when_same_dependencies_then_generates_consistent_hash(
        self,
    ):
        """Test context hash generation for equality comparison."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context1 = SpecContext(settings=settings, console=console, progress=progress)

        context2 = SpecContext(settings=settings, console=console, progress=progress)

        hash1 = context1.get_context_hash()
        hash2 = context2.get_context_hash()

        assert hash1 == hash2
        assert isinstance(hash1, str)
        assert len(hash1) == SAMPLE_HASH_LENGTH

    def test_spec_context_hash_when_different_dependencies_then_generates_different_hash(
        self,
    ):
        """Test that different dependencies generate different hashes."""
        settings1 = SpecSettingsInterface()
        settings2 = SpecSettingsInterface()
        settings2.debug_enabled = True

        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context1 = SpecContext(settings=settings1, console=console, progress=progress)

        context2 = SpecContext(settings=settings2, console=console, progress=progress)

        hash1 = context1.get_context_hash()
        hash2 = context2.get_context_hash()

        assert hash1 != hash2

    @patch("spec_cli.core.context.create_context_hash")
    def test_spec_context_hash_when_generation_fails_then_raises_context_error(
        self, mock_create_hash
    ):
        """Test that hash generation failure raises SpecContextError."""
        mock_create_hash.side_effect = ValueError("Hash generation failed")

        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context = SpecContext(settings=settings, console=console, progress=progress)

        with pytest.raises(SpecContextError, match="Failed to generate context hash"):
            context.get_context_hash()

    def test_spec_context_equality_when_same_hash_then_returns_true(self):
        """Test SpecContext equality using hash comparison."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context1 = SpecContext(settings=settings, console=console, progress=progress)

        context2 = SpecContext(settings=settings, console=console, progress=progress)

        assert context1 == context2

    def test_spec_context_equality_when_different_type_then_returns_false(self):
        """Test SpecContext equality with non-SpecContext objects."""
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context = SpecContext(settings=settings, console=console, progress=progress)

        assert context != "not a context"
        assert context is not None
        assert context != Mock()

    @patch.object(SpecContext, "get_context_hash")
    def test_spec_context_equality_when_hash_fails_then_returns_false(
        self, mock_get_hash
    ):
        """Test SpecContext equality when hash generation fails."""
        mock_get_hash.side_effect = SpecContextError("Hash failed")

        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context1 = SpecContext(settings=settings, console=console, progress=progress)

        context2 = SpecContext(settings=settings, console=console, progress=progress)

        assert context1 != context2


class TestSpecContextInterfaceDefaults:
    """Test default behavior of SpecContext interfaces."""

    def test_settings_interface_when_defaults_then_provides_expected_values(self):
        """Test SpecSettingsInterface provides expected default values."""
        settings = SpecSettingsInterface()

        assert settings.debug_enabled is False
        assert settings.console_width == DEFAULT_CONSOLE_WIDTH
        assert settings.use_color is True
        assert isinstance(settings.root_path, Path)
        assert settings.get_setting("debug_enabled") is False
        assert settings.validate_configuration() == {}

    def test_console_interface_when_defaults_then_provides_expected_methods(self):
        """Test SpecConsoleInterface provides expected default methods."""
        console = SpecConsoleInterface()

        # These should not raise exceptions
        console.print_message("test")
        console.print_error("test error")
        console.print_success("test success")
        console.print_warning("test warning")

        assert console.get_width() == DEFAULT_CONSOLE_WIDTH
        assert console.supports_color() is True

        # Test capture output context manager
        with console.capture_output() as captured:
            assert isinstance(captured, str)

    def test_progress_interface_when_defaults_then_provides_expected_methods(self):
        """Test SpecProgressInterface provides expected default methods."""
        progress = SpecProgressInterface()

        # These should not raise exceptions
        progress.show_progress(50, 100, "test progress")
        progress.update_status("test status")

        operation_id = progress.start_operation("test operation", 100)
        assert operation_id == SAMPLE_OPERATION_ID

        progress.finish_operation(operation_id)

        # Test spinner context manager
        with progress.create_spinner("test spinner"):
            pass  # Should not raise exception
