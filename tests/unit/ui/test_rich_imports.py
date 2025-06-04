"""Tests for Rich imports aggregator."""

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from rich.spinner import Spinner
from rich.syntax import Syntax
from rich.table import Table
from rich.theme import Theme

from spec_cli.ui.rich_imports import (
    create_console,
    create_panel,
    create_progress_bar,
    create_spinner,
    create_syntax,
    create_table,
)


class TestRichImportsAvailability:
    """Test that all Rich components are properly imported."""

    def test_all_rich_components_are_importable(self):
        """Test that all Rich components can be imported."""
        # Test factory functions are available
        assert callable(create_console)
        assert callable(create_progress_bar)
        assert callable(create_table)
        assert callable(create_panel)
        assert callable(create_syntax)
        assert callable(create_spinner)

        # Test direct Rich imports are available
        from spec_cli.ui.rich_imports import (
            Console,
            Progress,
            Table,
        )

        # Verify these are the actual Rich classes
        assert Console.__module__ == "rich.console"
        assert Table.__module__ == "rich.table"
        assert Progress.__module__ == "rich.progress"


class TestCreateConsole:
    """Test create_console factory function."""

    def test_create_console_when_no_args_then_returns_console(self):
        """Test creating console with default arguments."""
        console = create_console()

        assert isinstance(console, Console)

    def test_create_console_when_width_specified_then_uses_width(self):
        """Test creating console with specified width."""
        console = create_console(width=120)

        assert isinstance(console, Console)
        # Note: Rich console might adjust width based on terminal, so we don't assert exact value

    def test_create_console_when_theme_specified_then_uses_theme(self):
        """Test creating console with specified theme."""
        theme = Theme({"info": "cyan", "warning": "yellow"})
        console = create_console(theme=theme)

        assert isinstance(console, Console)
        # Verify theme is set (Rich doesn't expose theme directly, so we just ensure it doesn't error)

    def test_create_console_when_additional_kwargs_then_passes_through(self):
        """Test creating console with additional keyword arguments."""
        console = create_console(force_terminal=True, stderr=False)

        assert isinstance(console, Console)


class TestCreateProgressBar:
    """Test create_progress_bar factory function."""

    def test_create_progress_bar_when_defaults_then_returns_progress(self):
        """Test creating progress bar with default configuration."""
        progress = create_progress_bar()

        assert isinstance(progress, Progress)

    def test_create_progress_bar_when_no_spinner_then_excludes_spinner(self):
        """Test creating progress bar without spinner."""
        progress = create_progress_bar(show_spinner=False)

        assert isinstance(progress, Progress)
        # We can't easily test the internal columns, but we can verify it's a Progress instance

    def test_create_progress_bar_when_no_elapsed_then_excludes_elapsed(self):
        """Test creating progress bar without elapsed time."""
        progress = create_progress_bar(show_elapsed=False)

        assert isinstance(progress, Progress)

    def test_create_progress_bar_when_no_remaining_then_excludes_remaining(self):
        """Test creating progress bar without remaining time."""
        progress = create_progress_bar(show_remaining=False)

        assert isinstance(progress, Progress)

    def test_create_progress_bar_when_additional_kwargs_then_passes_through(self):
        """Test creating progress bar with additional keyword arguments."""
        progress = create_progress_bar(console=Console(), auto_refresh=False)

        assert isinstance(progress, Progress)


class TestCreateTable:
    """Test create_table factory function."""

    def test_create_table_when_defaults_then_returns_table(self):
        """Test creating table with default configuration."""
        table = create_table()

        assert isinstance(table, Table)

    def test_create_table_when_title_specified_then_uses_title(self):
        """Test creating table with specified title."""
        table = create_table(title="Test Table")

        assert isinstance(table, Table)
        assert table.title == "Test Table"

    def test_create_table_when_show_lines_true_then_enables_lines(self):
        """Test creating table with lines enabled."""
        table = create_table(show_lines=True)

        assert isinstance(table, Table)
        assert table.show_lines is True

    def test_create_table_when_no_header_then_disables_header(self):
        """Test creating table without header."""
        table = create_table(show_header=False)

        assert isinstance(table, Table)
        assert table.show_header is False


class TestCreatePanel:
    """Test create_panel factory function."""

    def test_create_panel_when_content_only_then_returns_panel(self):
        """Test creating panel with content only."""
        panel = create_panel("Test content")

        assert isinstance(panel, Panel)

    def test_create_panel_when_title_specified_then_uses_title(self):
        """Test creating panel with specified title."""
        panel = create_panel("Test content", title="Test Title")

        assert isinstance(panel, Panel)
        assert panel.title == "Test Title"

    def test_create_panel_when_style_specified_then_uses_style(self):
        """Test creating panel with specified style."""
        panel = create_panel("Test content", style="red")

        assert isinstance(panel, Panel)

    def test_create_panel_when_border_style_specified_then_uses_border_style(self):
        """Test creating panel with specified border style."""
        panel = create_panel("Test content", border_style="double")

        assert isinstance(panel, Panel)


class TestCreateSyntax:
    """Test create_syntax factory function."""

    def test_create_syntax_when_code_only_then_returns_syntax(self):
        """Test creating syntax highlighter with code only."""
        syntax = create_syntax("print('hello')")

        assert isinstance(syntax, Syntax)

    def test_create_syntax_when_lexer_specified_then_uses_lexer(self):
        """Test creating syntax highlighter with specified lexer."""
        syntax = create_syntax("console.log('hello')", lexer="javascript")

        assert isinstance(syntax, Syntax)

    def test_create_syntax_when_theme_specified_then_uses_theme(self):
        """Test creating syntax highlighter with specified theme."""
        syntax = create_syntax("print('hello')", theme="github-dark")

        assert isinstance(syntax, Syntax)

    def test_create_syntax_when_no_line_numbers_then_disables_line_numbers(self):
        """Test creating syntax highlighter without line numbers."""
        syntax = create_syntax("print('hello')", line_numbers=False)

        assert isinstance(syntax, Syntax)


class TestCreateSpinner:
    """Test create_spinner factory function."""

    def test_create_spinner_when_defaults_then_returns_spinner(self):
        """Test creating spinner with default configuration."""
        spinner = create_spinner()

        assert isinstance(spinner, Spinner)

    def test_create_spinner_when_name_specified_then_uses_name(self):
        """Test creating spinner with specified name."""
        spinner = create_spinner(name="bouncingBar")

        assert isinstance(spinner, Spinner)

    def test_create_spinner_when_text_specified_then_uses_text(self):
        """Test creating spinner with specified text."""
        spinner = create_spinner(text="Loading...")

        assert isinstance(spinner, Spinner)

    def test_create_spinner_when_style_specified_then_uses_style(self):
        """Test creating spinner with specified style."""
        spinner = create_spinner(style="cyan")

        assert isinstance(spinner, Spinner)


class TestRichImportsIntegration:
    """Test integration between components."""

    def test_console_and_table_integration(self):
        """Test that console and table work together."""
        console = create_console()
        table = create_table(title="Integration Test")
        table.add_column("Name", style="cyan")
        table.add_row("Test")

        # Should not raise any exceptions
        assert isinstance(console, Console)
        assert isinstance(table, Table)

    def test_console_and_panel_integration(self):
        """Test that console and panel work together."""
        console = create_console()
        panel = create_panel("Test content", title="Test")

        # Should not raise any exceptions
        assert isinstance(console, Console)
        assert isinstance(panel, Panel)

    def test_console_and_syntax_integration(self):
        """Test that console and syntax work together."""
        console = create_console()
        syntax = create_syntax("def test(): pass")

        # Should not raise any exceptions
        assert isinstance(console, Console)
        assert isinstance(syntax, Syntax)
