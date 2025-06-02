"""Tests for theme functionality."""

from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.ui.theme import (
    ColorScheme,
    SpecTheme,
    get_current_theme,
    reset_theme,
    set_current_theme,
)


class TestSpecTheme:
    """Test the SpecTheme class."""

    def test_spec_theme_initialization(self) -> None:
        """Test SpecTheme can be initialized with different color schemes."""
        # Test default initialization
        theme = SpecTheme()
        assert theme.color_scheme == ColorScheme.DEFAULT
        assert theme.theme is not None
        assert len(theme._get_theme_styles()) > 0

        # Test with specific color scheme
        dark_theme = SpecTheme(ColorScheme.DARK)
        assert dark_theme.color_scheme == ColorScheme.DARK
        assert dark_theme.theme is not None

    def test_color_scheme_variations(self) -> None:
        """Test different color schemes produce different styling."""
        default_theme = SpecTheme(ColorScheme.DEFAULT)
        dark_theme = SpecTheme(ColorScheme.DARK)
        light_theme = SpecTheme(ColorScheme.LIGHT)
        minimal_theme = SpecTheme(ColorScheme.MINIMAL)

        # Get title styles from each theme
        default_styles = default_theme._get_theme_styles()
        dark_styles = dark_theme._get_theme_styles()
        light_styles = light_theme._get_theme_styles()
        minimal_styles = minimal_theme._get_theme_styles()

        # Verify they are different
        assert default_styles["title"] != dark_styles["title"]
        assert default_styles["title"] != light_styles["title"]
        assert default_styles["success"] != minimal_styles["success"]

        # Verify specific scheme characteristics
        assert "bright_white" in dark_styles["title"]
        assert "black" in light_styles["title"]
        assert minimal_styles["success"] == "bold white"

    def test_theme_style_retrieval(self) -> None:
        """Test getting specific styles by name."""
        theme = SpecTheme()

        # Test getting valid style
        success_style = theme.get_style("success")
        assert success_style != ""
        assert "green" in success_style.lower()

        # Test getting invalid style
        invalid_style = theme.get_style("nonexistent_style")
        assert invalid_style == ""

    def test_emoji_replacements_mapping(self) -> None:
        """Test emoji replacement mappings are complete and valid."""
        theme = SpecTheme()
        replacements = theme.get_emoji_replacements()

        # Verify expected emojis are mapped
        expected_emojis = ["✅", "❌", "⚠️", "ℹ️", "📁", "📄", "🚀", "🎉", "⏳"]
        for emoji in expected_emojis:
            assert emoji in replacements
            replacement = replacements[emoji]
            assert "[" in replacement and "]" in replacement  # Contains Rich markup
            assert "[/" in replacement  # Contains closing tag

        # Verify structure of replacements
        for emoji, replacement in replacements.items():
            assert isinstance(emoji, str)
            assert isinstance(replacement, str)
            assert len(emoji) > 0
            assert len(replacement) > 0

    def test_theme_from_settings(self) -> None:
        """Test creating theme from settings configuration."""
        # Test with mock settings that has ui_color_scheme
        mock_settings = Mock(spec=SpecSettings)
        mock_settings.ui_color_scheme = "dark"

        with patch("spec_cli.ui.theme.get_settings", return_value=mock_settings):
            theme = SpecTheme.from_settings(mock_settings)
            assert theme.color_scheme == ColorScheme.DARK

        # Test with settings that doesn't have ui_color_scheme
        mock_settings_no_color = Mock(spec=SpecSettings)
        # Use getattr default behavior
        with patch(
            "spec_cli.ui.theme.get_settings", return_value=mock_settings_no_color
        ):
            theme = SpecTheme.from_settings(mock_settings_no_color)
            assert theme.color_scheme == ColorScheme.DEFAULT

        # Test with invalid color scheme
        mock_settings_invalid = Mock(spec=SpecSettings)
        mock_settings_invalid.ui_color_scheme = "invalid_scheme"

        with patch(
            "spec_cli.ui.theme.get_settings", return_value=mock_settings_invalid
        ):
            theme = SpecTheme.from_settings(mock_settings_invalid)
            assert theme.color_scheme == ColorScheme.DEFAULT

    def test_global_theme_management(self) -> None:
        """Test global theme management functions."""
        # Reset theme to ensure clean state
        reset_theme()

        # Test get_current_theme creates theme on first call
        with patch("spec_cli.ui.theme.SpecTheme.from_settings") as mock_from_settings:
            mock_theme = Mock(spec=SpecTheme)
            mock_theme.color_scheme = ColorScheme.DEFAULT
            mock_from_settings.return_value = mock_theme

            theme = get_current_theme()
            assert theme is not None
            mock_from_settings.assert_called_once()

        # Test set_current_theme
        custom_theme = SpecTheme(ColorScheme.DARK)
        set_current_theme(custom_theme)

        current = get_current_theme()
        assert current is custom_theme
        assert current.color_scheme == ColorScheme.DARK

        # Test reset_theme
        reset_theme()
        # After reset, next call should create new theme
        with patch("spec_cli.ui.theme.SpecTheme.from_settings") as mock_from_settings:
            mock_theme = Mock(spec=SpecTheme)
            mock_from_settings.return_value = mock_theme

            theme = get_current_theme()
            mock_from_settings.assert_called_once()


class TestThemeColorScheme:
    """Test ColorScheme enum."""

    def test_color_scheme_values(self) -> None:
        """Test ColorScheme enum has expected values."""
        assert ColorScheme.DEFAULT.value == "default"
        assert ColorScheme.DARK.value == "dark"
        assert ColorScheme.LIGHT.value == "light"
        assert ColorScheme.MINIMAL.value == "minimal"

    def test_color_scheme_from_string(self) -> None:
        """Test creating ColorScheme from string values."""
        assert ColorScheme("default") == ColorScheme.DEFAULT
        assert ColorScheme("dark") == ColorScheme.DARK
        assert ColorScheme("light") == ColorScheme.LIGHT
        assert ColorScheme("minimal") == ColorScheme.MINIMAL

        # Test invalid value raises ValueError
        with pytest.raises(ValueError):
            ColorScheme("invalid")


class TestThemeUpdates:
    """Test theme update functionality."""

    def test_update_color_scheme(self) -> None:
        """Test updating color scheme recreates theme."""
        theme = SpecTheme(ColorScheme.DEFAULT)
        original_theme_obj = theme._theme

        # Update to dark scheme
        theme.update_color_scheme(ColorScheme.DARK)

        assert theme.color_scheme == ColorScheme.DARK
        assert theme._theme is not original_theme_obj  # New theme object created

        # Verify the new theme has dark characteristics
        styles = theme._get_theme_styles()
        assert "bright_white" in styles["title"]
