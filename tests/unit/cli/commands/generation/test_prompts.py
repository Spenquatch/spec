"""Tests for generation prompts module."""

from pathlib import Path
from unittest.mock import Mock, patch

from spec_cli.cli.commands.generation.prompts import (
    ConflictResolver,
    GenerationPrompts,
    TemplateSelector,
    confirm_generation,
    resolve_conflicts,
    select_template,
)
from spec_cli.file_processing.conflict_resolver import ConflictResolutionStrategy


class TestTemplateSelector:
    """Test the TemplateSelector class."""

    def test_template_selector_initialization_then_creates_console(self):
        """Test that TemplateSelector initializes with console."""
        selector = TemplateSelector()

        assert hasattr(selector, "console")
        assert selector.console is not None

    def test_get_template_description_when_known_template_then_returns_description(
        self
    ):
        """Test that known templates return proper descriptions."""
        selector = TemplateSelector()

        result = selector._get_template_description("default")

        assert result == "Standard documentation template with index and history"

    def test_get_template_description_when_unknown_template_then_returns_custom(self):
        """Test that unknown templates return custom description."""
        selector = TemplateSelector()

        result = selector._get_template_description("unknown")

        assert result == "Custom template"


class TestConflictResolver:
    """Test the ConflictResolver class."""

    def test_conflict_resolver_initialization_then_creates_console(self):
        """Test that ConflictResolver initializes with console."""
        resolver = ConflictResolver()

        assert hasattr(resolver, "console")
        assert resolver.console is not None

    def test_name_to_strategy_when_valid_name_then_returns_correct_strategy(self):
        """Test that strategy names map to correct enum values."""
        resolver = ConflictResolver()

        result = resolver._name_to_strategy("backup")

        assert result == ConflictResolutionStrategy.BACKUP_AND_REPLACE

    def test_name_to_strategy_when_invalid_name_then_returns_default_strategy(self):
        """Test that invalid names return default backup strategy."""
        resolver = ConflictResolver()

        result = resolver._name_to_strategy("invalid")

        assert result == ConflictResolutionStrategy.BACKUP_AND_REPLACE


class TestGenerationPrompts:
    """Test the GenerationPrompts class."""

    @patch("spec_cli.cli.commands.generation.prompts.click.confirm")
    @patch("spec_cli.cli.commands.generation.prompts.get_console")
    def test_confirm_generation_when_few_files_then_shows_all_files(
        self, mock_console, mock_confirm
    ):
        """Test that confirmation with few files shows all files."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        mock_confirm.return_value = True

        prompts = GenerationPrompts()
        source_files = [Path("file1.py"), Path("file2.py")]
        template_name = "default"
        conflict_strategy = ConflictResolutionStrategy.BACKUP_AND_REPLACE

        result = prompts.confirm_generation(
            source_files, template_name, conflict_strategy
        )

        assert result is True
        # Should show summary and all files
        assert mock_console_instance.print.call_count >= 5
        mock_confirm.assert_called_once_with("\nProceed with generation?", default=True)

    @patch("spec_cli.cli.commands.generation.prompts.click.confirm")
    @patch("spec_cli.cli.commands.generation.prompts.get_console")
    def test_confirm_generation_when_many_files_then_shows_truncated_list(
        self, mock_console, mock_confirm
    ):
        """Test that confirmation with many files shows truncated list."""
        mock_console_instance = Mock()
        mock_console.return_value = mock_console_instance
        mock_confirm.return_value = False

        prompts = GenerationPrompts()
        source_files = [Path(f"file{i}.py") for i in range(10)]  # 10 files
        template_name = "custom"
        conflict_strategy = ConflictResolutionStrategy.SKIP

        result = prompts.confirm_generation(
            source_files, template_name, conflict_strategy
        )

        assert result is False
        # Should show summary and truncated file list
        calls = mock_console_instance.print.call_args_list
        truncated_call = [call for call in calls if "and 7 more" in str(call)]
        assert len(truncated_call) >= 1

    def test_generation_prompts_initialization_then_creates_components(self):
        """Test that GenerationPrompts initializes its components."""
        prompts = GenerationPrompts()

        assert hasattr(prompts, "template_selector")
        assert hasattr(prompts, "conflict_resolver")
        assert hasattr(prompts, "console")
        assert isinstance(prompts.template_selector, TemplateSelector)
        assert isinstance(prompts.conflict_resolver, ConflictResolver)


class TestConvenienceFunctions:
    """Test the standalone convenience functions."""

    @patch("spec_cli.cli.commands.generation.prompts.TemplateSelector.select_template")
    def test_select_template_function_when_called_then_creates_selector_and_calls_method(
        self, mock_select
    ):
        """Test the select_template convenience function."""
        mock_select.return_value = "default"

        result = select_template("current")

        mock_select.assert_called_once_with("current")
        assert result == "default"

    @patch(
        "spec_cli.cli.commands.generation.prompts.ConflictResolver.resolve_conflicts"
    )
    def test_resolve_conflicts_function_when_called_then_creates_resolver_and_calls_method(
        self, mock_resolve
    ):
        """Test the resolve_conflicts convenience function."""
        mock_resolve.return_value = ConflictResolutionStrategy.SKIP
        source_file = Path("test.py")
        existing_files = [Path("existing.md")]

        result = resolve_conflicts(
            source_file, existing_files, ConflictResolutionStrategy.BACKUP_AND_REPLACE
        )

        mock_resolve.assert_called_once_with(
            source_file, existing_files, ConflictResolutionStrategy.BACKUP_AND_REPLACE
        )
        assert result == ConflictResolutionStrategy.SKIP

    @patch(
        "spec_cli.cli.commands.generation.prompts.GenerationPrompts.confirm_generation"
    )
    def test_confirm_generation_function_when_called_then_creates_prompts_and_calls_method(
        self, mock_confirm
    ):
        """Test the confirm_generation convenience function."""
        mock_confirm.return_value = True
        source_files = [Path("test.py")]
        template_name = "default"
        conflict_strategy = ConflictResolutionStrategy.BACKUP_AND_REPLACE

        result = confirm_generation(source_files, template_name, conflict_strategy)

        mock_confirm.assert_called_once_with(
            source_files, template_name, conflict_strategy
        )
        assert result is True
