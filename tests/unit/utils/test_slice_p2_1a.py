"""Unit tests for Slice P2.1a Click Framework Pattern Analysis."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.exceptions import SpecValidationError
from spec_cli.utils.click_analysis import (
    ClickPatternReport,
    analyze_click_patterns,
    validate_context_storage_capability,
)

# Test constants
TEST_CLI_DIR_NAME = "test_cli"
VALID_CLICK_FILE_CONTENT = '''
import click

@click.group()
@click.pass_context
def main(ctx):
    """Main CLI group."""
    pass

@click.command()
@click.option("--verbose", is_flag=True)
@click.argument("filename")
def process(verbose, filename):
    """Process a file."""
    pass
'''

CLICK_CONTEXT_FILE_CONTENT = '''
import click

@click.command()
@click.pass_context
def cmd_with_context(ctx: click.Context):
    """Command that uses Click context."""
    ctx.meta["test"] = "value"
    return ctx
'''

NO_CLICK_FILE_CONTENT = '''
def regular_function():
    """Function with no Click usage."""
    return "hello"
'''

INVALID_PYTHON_CONTENT = """
This is not valid Python syntax [[[
"""


class TestClickPatternAnalysis:
    """Test Click pattern analysis functionality."""

    def test_analyze_click_patterns_when_valid_cli_directory_then_returns_pattern_report(
        self,
    ):
        """Test Click pattern analysis with valid CLI directory structure."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create test CLI file with Click patterns
            cli_file = cli_dir / "commands.py"
            cli_file.write_text(VALID_CLICK_FILE_CONTENT)

            result = analyze_click_patterns(cli_dir)

            assert isinstance(result, ClickPatternReport)
            assert "group" in result.commands_found
            assert "command" in result.commands_found
            assert "click_group" in result.decorators_used
            assert "click_command" in result.decorators_used
            assert "click_option" in result.decorators_used
            assert "click_argument" in result.decorators_used
            assert "click_pass_context" in result.decorators_used
            assert len(result.integration_requirements) > 0

    def test_analyze_click_patterns_when_no_click_usage_then_returns_empty_patterns(
        self,
    ):
        """Test Click analysis with files containing no Click usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create file with no Click usage
            regular_file = cli_dir / "regular.py"
            regular_file.write_text(NO_CLICK_FILE_CONTENT)

            result = analyze_click_patterns(cli_dir)

            assert isinstance(result, ClickPatternReport)
            assert len(result.commands_found) == 0
            assert len(result.decorators_used) == 0
            assert len(result.context_usage) == 0
            assert (
                len(result.integration_requirements) > 0
            )  # Always has basic requirements

    def test_analyze_click_patterns_when_context_usage_then_documents_patterns(self):
        """Test analysis of Click context usage patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create file with Click context usage
            context_file = cli_dir / "context_cmd.py"
            context_file.write_text(CLICK_CONTEXT_FILE_CONTENT)

            result = analyze_click_patterns(cli_dir)

            assert len(result.context_usage) == 1
            context_usage = list(result.context_usage.values())[0]
            assert any("context parameter" in usage.lower() for usage in context_usage)
            assert "click_pass_context" in result.decorators_used

    def test_analyze_click_patterns_when_invalid_cli_directory_then_raises_analysis_error(
        self,
    ):
        """Test error handling for invalid CLI directory paths."""
        nonexistent_dir = Path("/nonexistent/cli/directory")

        with pytest.raises(SpecValidationError) as exc_info:
            analyze_click_patterns(nonexistent_dir)

        assert "does not exist" in str(exc_info.value)
        assert str(nonexistent_dir) in str(exc_info.value)

    def test_analyze_click_patterns_when_file_path_then_raises_analysis_error(self):
        """Test error handling when CLI path is a file, not directory."""
        with tempfile.NamedTemporaryFile(suffix=".py") as temp_file:
            file_path = Path(temp_file.name)

            with pytest.raises(SpecValidationError) as exc_info:
                analyze_click_patterns(file_path)

            assert "not a directory" in str(exc_info.value)

    def test_analyze_click_patterns_when_invalid_type_then_raises_analysis_error(self):
        """Test error handling for invalid directory type."""
        with pytest.raises(SpecValidationError) as exc_info:
            analyze_click_patterns("not_a_path")  # String instead of Path

        assert "must be a Path object" in str(exc_info.value)

    def test_analyze_click_patterns_when_invalid_syntax_files_then_skips_gracefully(
        self,
    ):
        """Test analysis skips files with invalid Python syntax."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create valid Click file
            valid_file = cli_dir / "valid.py"
            valid_file.write_text(VALID_CLICK_FILE_CONTENT)

            # Create invalid syntax file
            invalid_file = cli_dir / "invalid.py"
            invalid_file.write_text(INVALID_PYTHON_CONTENT)

            # Should not raise exception, just skip invalid file
            result = analyze_click_patterns(cli_dir)

            # Should still find patterns from valid file
            assert len(result.commands_found) > 0
            assert len(result.decorators_used) > 0

    def test_analyze_click_patterns_when_init_files_then_skips_init_files(self):
        """Test analysis skips __init__.py files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create __init__.py with Click content (should be skipped)
            init_file = cli_dir / "__init__.py"
            init_file.write_text(VALID_CLICK_FILE_CONTENT)

            # Create regular file with no Click content
            regular_file = cli_dir / "regular.py"
            regular_file.write_text(NO_CLICK_FILE_CONTENT)

            result = analyze_click_patterns(cli_dir)

            # Should not find Click patterns since __init__.py is skipped
            assert len(result.commands_found) == 0
            assert len(result.decorators_used) == 0


class TestClickContextStorageValidation:
    """Test Click context storage capability validation."""

    def test_validate_context_storage_capability_when_click_context_then_validates_storage(
        self,
    ):
        """Test Click context storage capability validation."""
        result = validate_context_storage_capability()

        # Click should support context storage
        assert result is True

    @patch("spec_cli.utils.click_analysis.setattr")
    def test_validate_context_storage_capability_when_storage_fails_then_returns_false(
        self, mock_setattr
    ):
        """Test context storage validation when storage fails."""
        # Mock setattr to raise exception
        mock_setattr.side_effect = Exception("Storage failed")

        result = validate_context_storage_capability()

        assert result is False

    @patch("spec_cli.utils.click_analysis.click.Context")
    def test_validate_context_storage_capability_when_meta_fails_then_returns_false(
        self, mock_context
    ):
        """Test context storage validation when meta dictionary fails."""
        # Mock Click context with failing meta access
        mock_ctx = Mock()
        mock_meta = Mock()
        mock_meta.__setitem__ = Mock(side_effect=Exception("Meta storage failed"))
        mock_ctx.meta = mock_meta
        mock_context.return_value = mock_ctx

        result = validate_context_storage_capability()

        assert result is False


class TestClickPatternReport:
    """Test ClickPatternReport data structure."""

    def test_click_pattern_report_when_default_initialization_then_creates_empty_report(
        self,
    ):
        """Test ClickPatternReport default initialization."""
        report = ClickPatternReport()

        assert report.commands_found == []
        assert report.decorators_used == set()
        assert report.context_usage == {}
        assert report.storage_capabilities == {}
        assert report.integration_requirements == []
        assert report.cli_structure == {}

    def test_click_pattern_report_when_custom_data_then_stores_data_correctly(self):
        """Test ClickPatternReport with custom data."""
        commands = ["command", "group"]
        decorators = {"click_command", "click_group"}
        context_usage = {"file1.py": ["usage1", "usage2"]}
        storage_caps = {"custom_storage": True}
        requirements = ["req1", "req2"]
        cli_structure = {"main": "app"}

        report = ClickPatternReport(
            commands_found=commands,
            decorators_used=decorators,
            context_usage=context_usage,
            storage_capabilities=storage_caps,
            integration_requirements=requirements,
            cli_structure=cli_structure,
        )

        assert report.commands_found == commands
        assert report.decorators_used == decorators
        assert report.context_usage == context_usage
        assert report.storage_capabilities == storage_caps
        assert report.integration_requirements == requirements
        assert report.cli_structure == cli_structure


class TestClickDecoratorPatternDetection:
    """Test Click decorator pattern detection functionality."""

    def test_click_decorator_pattern_detection_when_decorators_found_then_documents_usage(
        self,
    ):
        """Test detection of existing Click decorator patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create file with various Click decorators
            decorator_content = '''
import click

@click.group()
def main():
    pass

@click.command()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.option("--count", default=1, help="Count value")
@click.argument("filename", required=True)
@click.pass_context
def process_file(ctx, verbose, count, filename):
    """Process a file with options."""
    pass

@click.command()
@click.pass_obj
def another_cmd(obj):
    """Another command."""
    pass
'''

            cli_file = cli_dir / "decorators.py"
            cli_file.write_text(decorator_content)

            result = analyze_click_patterns(cli_dir)

            # Verify all decorator types detected
            expected_decorators = {
                "click_group",
                "click_command",
                "click_option",
                "click_argument",
                "click_pass_context",
                "click_pass_obj",
            }
            for decorator in expected_decorators:
                assert decorator in result.decorators_used

    def test_click_decorator_detection_when_from_import_then_detects_imports(self):
        """Test detection of 'from click import' patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            from_import_content = """
from click import command, option, argument

@command()
@option("--test")
@argument("name")
def test_cmd(test, name):
    pass
"""

            cli_file = cli_dir / "from_imports.py"
            cli_file.write_text(from_import_content)

            result = analyze_click_patterns(cli_dir)

            # Should detect from_click imports
            assert "from_click_command" in result.decorators_used
            assert "from_click_option" in result.decorators_used
            assert "from_click_argument" in result.decorators_used


class TestIntegrationRequirementsGeneration:
    """Test integration requirements generation based on discovered patterns."""

    def test_integration_requirements_when_click_patterns_then_generates_requirements(
        self,
    ):
        """Test integration requirements generation for Click patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create comprehensive CLI structure
            full_cli_content = '''
import click

@click.group()
@click.pass_context
def main(ctx):
    """Main CLI group."""
    ctx.meta["app"] = "spec"

@click.command()
@click.option("--verbose", is_flag=True)
@click.argument("input_file")
@click.pass_context
def process(ctx, verbose, input_file):
    """Process command with context."""
    app = ctx.meta.get("app")
'''

            cli_file = cli_dir / "full_cli.py"
            cli_file.write_text(full_cli_content)

            result = analyze_click_patterns(cli_dir)

            # Verify key integration requirements are generated
            requirements_text = " ".join(result.integration_requirements)

            assert "Click framework integration required" in requirements_text
            assert "context parameter injection" in requirements_text
            assert "Context storage mechanism" in requirements_text
            assert "Click group context inheritance" in requirements_text
            assert "Click option decorator compatibility" in requirements_text
            assert "Click argument decorator integration" in requirements_text
            assert "storage verified" in requirements_text

    def test_integration_requirements_when_minimal_patterns_then_generates_basic_requirements(
        self,
    ):
        """Test integration requirements for minimal Click usage."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create minimal Click usage
            minimal_content = '''
import click

@click.command()
def simple():
    """Simple command."""
    pass
'''

            cli_file = cli_dir / "minimal.py"
            cli_file.write_text(minimal_content)

            result = analyze_click_patterns(cli_dir)

            # Should still generate basic requirements
            assert len(result.integration_requirements) >= 2
            requirements_text = " ".join(result.integration_requirements)
            assert "Click framework integration" in requirements_text
            assert "storage verified" in requirements_text


class TestClickAnalysisEdgeCases:
    """Test edge cases and branch coverage for Click analysis."""

    def test_analyze_file_patterns_when_context_parameter_variations_then_detects_all(self):
        """Test detection of various context parameter naming patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create file with various context parameter patterns
            context_variations_content = '''
import click

@click.command()
def cmd_with_ctx(ctx):
    """Command with ctx parameter."""
    pass

@click.command()
def cmd_with_context(context):
    """Command with context parameter."""
    pass

@click.command()
def cmd_with_click_context(click_context):
    """Command with click_context parameter."""
    pass
'''

            cli_file = cli_dir / "context_variations.py"
            cli_file.write_text(context_variations_content)

            result = analyze_click_patterns(cli_dir)

            # Should detect all context parameter variations
            assert len(result.context_usage) == 1
            context_usage = list(result.context_usage.values())[0]
            assert len(context_usage) == 3  # Three functions with context params

    def test_analyze_decorator_when_attribute_decorator_without_click_then_ignores(self):
        """Test decorator analysis ignores non-Click attribute decorators."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create file with non-Click decorators
            non_click_content = '''
import other_module

@other_module.decorator
def function_with_other_decorator():
    pass

@some_decorator.command
def function_with_different_decorator():
    pass
'''

            cli_file = cli_dir / "non_click.py"
            cli_file.write_text(non_click_content)

            result = analyze_click_patterns(cli_dir)

            # Should not detect any Click patterns
            assert len(result.decorators_used) == 0
            assert len(result.commands_found) == 0

    def test_analyze_decorator_when_call_decorator_without_click_then_ignores(self):
        """Test decorator analysis ignores non-Click call decorators."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cli_dir = Path(temp_dir) / TEST_CLI_DIR_NAME
            cli_dir.mkdir()

            # Create file with non-Click call decorators
            non_click_call_content = '''
import other

@other.command()
def function_with_other_call():
    pass

@different_module.option("--test")
def function_with_different_option():
    pass
'''

            cli_file = cli_dir / "non_click_calls.py"
            cli_file.write_text(non_click_call_content)

            result = analyze_click_patterns(cli_dir)

            # Should not detect any Click patterns
            assert len(result.decorators_used) == 0
            assert len(result.commands_found) == 0
