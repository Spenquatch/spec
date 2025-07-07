"""Unit tests for CLI Gen Command - Micro-Agent cli_003 Implementation.

Tests cover:
- CLI interface (gen.py) with click options and argument validation
- GenCommand class methods with AI integration and template fallback
- AI mocking and timeout scenarios
- Template processing and error handling
- Edge cases and boundary conditions
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner

from spec_cli.cli.commands.gen import gen_command
from spec_cli.cli.commands.gen_command import GenCommand, generate_with_ai
from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecError


class TestGenCommandCLI:
    """Test the CLI interface for gen command."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.runner = CliRunner()

    def test_gen_command_when_valid_file_then_executes_successfully(self):
        """Test gen command with valid file path executes successfully."""
        with self.runner.isolated_filesystem():
            # Create test file
            test_file = Path("test.py")
            test_file.write_text("print('hello')")

            # Mock the GenCommand.safe_execute to return success
            with patch(
                "spec_cli.cli.commands.gen.GenCommand.safe_execute"
            ) as mock_execute:
                mock_execute.return_value = {
                    "success": True,
                    "message": "Generation completed",
                }

                # Mock validate_file_paths
                with patch(
                    "spec_cli.cli.commands.gen.validate_file_paths"
                ) as mock_validate:
                    mock_validate.return_value = [test_file]

                    result = self.runner.invoke(gen_command, ["test.py"])

                    assert result.exit_code == 0
                    mock_execute.assert_called_once()

    def test_gen_command_when_no_files_then_raises_bad_parameter(self):
        """Test gen command with no files raises BadParameter."""
        with patch("spec_cli.cli.commands.gen.validate_file_paths") as mock_validate:
            mock_validate.return_value = []

            result = self.runner.invoke(gen_command, ["dummy_file"])

            assert result.exit_code != 0
            assert "No valid source files provided" in result.output

    def test_gen_command_when_command_fails_then_exits_with_error(self):
        """Test gen command exits with error when command execution fails."""
        with self.runner.isolated_filesystem():
            test_file = Path("test.py")
            test_file.write_text("print('hello')")

            with patch(
                "spec_cli.cli.commands.gen.GenCommand.safe_execute"
            ) as mock_execute:
                mock_execute.return_value = {
                    "success": False,
                    "message": "Generation failed",
                }

                with patch(
                    "spec_cli.cli.commands.gen.validate_file_paths"
                ) as mock_validate:
                    mock_validate.return_value = [test_file]

                    result = self.runner.invoke(gen_command, ["test.py"])

                    assert result.exit_code != 0
                    assert "Generation failed" in result.output

    def test_gen_command_when_all_options_provided_then_passes_to_command(self):
        """Test gen command passes all options correctly to GenCommand."""
        with self.runner.isolated_filesystem():
            test_file = Path("test.py")
            test_file.write_text("print('hello')")

            with patch(
                "spec_cli.cli.commands.gen.GenCommand.safe_execute"
            ) as mock_execute:
                mock_execute.return_value = {
                    "success": True,
                    "message": "Generation completed",
                }

                with patch(
                    "spec_cli.cli.commands.gen.validate_file_paths"
                ) as mock_validate:
                    mock_validate.return_value = [test_file]

                    result = self.runner.invoke(
                        gen_command,
                        [
                            "test.py",
                            "--template",
                            "custom",
                            "--conflict-strategy",
                            "overwrite",
                            "--commit",
                            "--message",
                            "Test commit",
                            "--interactive",
                            "--force",
                            "--dry-run",
                        ],
                    )

                    assert result.exit_code == 0

                    # Verify all options were passed
                    call_args = mock_execute.call_args[1]
                    assert call_args["template"] == "custom"
                    assert call_args["conflict_strategy"] == "overwrite"
                    assert call_args["commit"] is True
                    assert call_args["message"] == "Test commit"
                    assert call_args["interactive"] is True
                    assert call_args["force"] is True
                    assert call_args["dry_run"] is True

    def test_gen_command_when_exception_raised_then_converts_to_click_exception(self):
        """Test gen command converts exceptions to ClickException."""
        with self.runner.isolated_filesystem():
            test_file = Path("test.py")
            test_file.write_text("print('hello')")

            with patch(
                "spec_cli.cli.commands.gen.GenCommand.safe_execute"
            ) as mock_execute:
                mock_execute.side_effect = Exception("Unexpected error")

                with patch(
                    "spec_cli.cli.commands.gen.validate_file_paths"
                ) as mock_validate:
                    mock_validate.return_value = [test_file]

                    result = self.runner.invoke(gen_command, ["test.py"])

                    assert result.exit_code != 0
                    assert "Generation failed: Unexpected error" in result.output


class TestGenCommandClass:
    """Test the GenCommand class methods."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test")
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/.specs")
        self.command = GenCommand(self.mock_settings)

    def test_init_when_no_settings_then_uses_default(self):
        """Test GenCommand initialization without settings."""
        with patch("spec_cli.cli.commands.gen_command.get_console") as mock_console:
            command = GenCommand()
            assert command.settings is not None
            mock_console.assert_called_once()

    def test_validate_arguments_when_valid_inputs_then_succeeds(self):
        """Test validate_arguments with valid inputs."""
        kwargs = {
            "files": [Path("test.py")],
            "template": "default",
            "conflict_strategy": "backup",
            "no_ai": False,
            "doc_type": "standard",
        }

        # Should not raise any exception
        self.command.validate_arguments(**kwargs)

    def test_validate_arguments_when_no_files_then_raises_spec_error(self):
        """Test validate_arguments raises SpecError when no files provided."""
        kwargs = {"files": []}

        with pytest.raises(SpecError, match="No source files provided"):
            self.command.validate_arguments(**kwargs)

    def test_validate_arguments_when_invalid_conflict_strategy_then_raises_spec_error(
        self,
    ):
        """Test validate_arguments raises SpecError for invalid conflict strategy."""
        kwargs = {
            "files": [Path("test.py")],
            "template": "default",
            "conflict_strategy": "invalid_strategy",
            "no_ai": False,
            "doc_type": "standard",
        }

        with pytest.raises(SpecError, match="Invalid conflict strategy"):
            self.command.validate_arguments(**kwargs)

    def test_validate_arguments_when_invalid_doc_type_then_raises_spec_error(self):
        """Test validate_arguments raises SpecError for invalid doc_type."""
        kwargs = {
            "files": [Path("test.py")],
            "template": "default",
            "conflict_strategy": "backup",
            "no_ai": False,
            "doc_type": "invalid_type",
        }

        with pytest.raises(SpecError, match="Invalid doc_type"):
            self.command.validate_arguments(**kwargs)

    @patch("spec_cli.cli.commands.gen_command.show_message")
    def test_execute_when_no_files_found_then_returns_success_with_warning(
        self, mock_show
    ):
        """Test execute method when no processable files are found."""
        with patch.object(self.command, "validate_repository_state"):
            with patch.object(self.command, "_expand_source_files", return_value=[]):
                result = self.command.execute(files=[Path("nonexistent")])

                assert result["success"] is True
                assert "No files to process" in result["message"]
                mock_show.assert_called_with(
                    "No processable files found in the specified paths", "warning"
                )

    @patch("spec_cli.cli.commands.gen_command.show_message")
    def test_execute_when_dry_run_then_shows_preview_and_returns_success(
        self, mock_show
    ):
        """Test execute method in dry run mode."""
        test_file = Path("test.py")

        with patch.object(self.command, "validate_repository_state"):
            with patch.object(
                self.command, "_expand_source_files", return_value=[test_file]
            ):
                with patch.object(self.command, "_show_dry_run_preview"):
                    with patch(
                        "spec_cli.cli.commands.gen_command.validate_generation_input",
                        return_value={"valid": True, "errors": [], "warnings": []},
                    ):
                        result = self.command.execute(files=[test_file], dry_run=True)

                    assert result["success"] is True
                    assert "Dry run completed" in result["message"]

    def test_create_template_variables_when_valid_path_then_returns_variables(self):
        """Test _create_template_variables returns correct variable dictionary."""
        test_path = Path("/test/dir/example.py")

        with patch(
            "spec_cli.cli.commands.gen_command.normalize_path", return_value=test_path
        ):
            with patch("spec_cli.cli.commands.gen_command.datetime") as mock_datetime:
                mock_datetime.now.return_value.isoformat.return_value = (
                    "2023-01-01T00:00:00"
                )

                variables = self.command._create_template_variables(test_path)

                assert variables["filename"] == "example.py"
                assert variables["filepath"] == str(test_path)
                assert variables["parent_dir"] == "dir"
                assert variables["file_ext"] == ".py"
                assert variables["timestamp"] == "2023-01-01T00:00:00"


class TestGenCommandExecuteSingleFile:
    """Test the _execute_single_file method and AI integration."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test")
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/.specs")
        self.command = GenCommand(self.mock_settings)
        self.test_path = Path("/test/example.py")

    def test_execute_single_file_when_no_ai_flag_then_uses_templates(self):
        """Test _execute_single_file uses templates when no_ai=True."""
        expected_result = {"success": True, "data": {"generated_files": ["test.md"]}}

        with patch.object(
            self.command, "_generate_with_templates", return_value=expected_result
        ) as mock_template:
            result = self.command._execute_single_file(
                target_path=self.test_path,
                doc_type="standard",
                template_path=None,
                no_ai=True,
            )

            assert result == expected_result
            mock_template.assert_called_once_with(
                target_path=self.test_path,
                template_path=None,
                ai_enhanced=False,
                reason="AI disabled by user",
            )

    def test_execute_single_file_when_ai_succeeds_then_returns_ai_result(self):
        """Test _execute_single_file returns AI result when AI generation succeeds."""
        ai_result = {
            "success": True,
            "data": {"generated_docs": {"content": "AI generated"}},
        }
        finalized_result = {
            "success": True,
            "data": {"generated_files": ["ai_result.md"]},
        }

        with patch.object(
            self.command, "_generate_with_ai_templates", return_value=ai_result
        ):
            with patch.object(
                self.command, "_finalize_ai_results", return_value=finalized_result
            ) as mock_finalize:
                result = self.command._execute_single_file(
                    target_path=self.test_path,
                    doc_type="standard",
                    template_path=None,
                    no_ai=False,
                )

                assert result == finalized_result
                mock_finalize.assert_called_once_with(ai_result, self.test_path)

    def test_execute_single_file_when_ai_fails_with_fallback_then_uses_enhanced_templates(
        self,
    ):
        """Test _execute_single_file falls back to enhanced templates when AI fails."""
        ai_result = {
            "success": False,
            "error": "AI timeout",
            "data": {"fallback_needed": True},
        }
        fallback_result = {
            "success": True,
            "data": {"generated_files": ["fallback.md"]},
        }

        with patch.object(
            self.command, "_generate_with_ai_templates", return_value=ai_result
        ):
            with patch.object(
                self.command, "_generate_with_templates", return_value=fallback_result
            ) as mock_template:
                result = self.command._execute_single_file(
                    target_path=self.test_path,
                    doc_type="standard",
                    template_path=None,
                    no_ai=False,
                )

                assert result == fallback_result
                mock_template.assert_called_once_with(
                    target_path=self.test_path,
                    template_path=None,
                    ai_enhanced=True,
                    reason="AI fallback: AI timeout",
                )

    def test_execute_single_file_when_ai_fails_without_fallback_then_returns_error(
        self,
    ):
        """Test _execute_single_file returns AI error when no fallback needed."""
        ai_result = {"success": False, "error": "AI model unavailable", "data": {}}

        with patch.object(
            self.command, "_generate_with_ai_templates", return_value=ai_result
        ):
            result = self.command._execute_single_file(
                target_path=self.test_path,
                doc_type="standard",
                template_path=None,
                no_ai=False,
            )

            assert result == ai_result

    def test_execute_single_file_when_exception_then_returns_error_result(self):
        """Test _execute_single_file handles exceptions gracefully."""
        with patch.object(
            self.command,
            "_generate_with_ai_templates",
            side_effect=Exception("Network error"),
        ):
            result = self.command._execute_single_file(
                target_path=self.test_path,
                doc_type="standard",
                template_path=None,
                no_ai=False,
            )

            assert result["success"] is False
            assert "Documentation generation failed: Network error" in result["error"]


class TestGenCommandAIMocking:
    """Test AI integration with proper mocking."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test")
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/.specs")
        self.command = GenCommand(self.mock_settings)
        self.test_path = Path("/test/example.py")

    def test_generate_with_ai_templates_when_successful_then_returns_ai_content(self):
        """Test _generate_with_ai_templates with successful AI generation."""
        # Mock the AI template processing
        mock_template_result = Mock()
        mock_template_result.success = True
        mock_template_result.has_ai_enhancement.return_value = True

        mock_ai_template = Mock()
        mock_ai_template.load_and_process_template.return_value = mock_template_result
        mock_ai_template.create_generation_request.return_value = Mock(
            template_content="template content"
        )

        ai_response = {
            "success": True,
            "data": {"generated_docs": {"main": "AI content"}},
        }

        with patch(
            "spec_cli.cli.commands.gen_command.AIEnhancedTemplate",
            return_value=mock_ai_template,
        ):
            with patch.object(
                self.command, "_create_template_variables", return_value={}
            ):
                with patch(
                    "spec_cli.ai.generation.ai_generator.generate_with_ai_request",
                    return_value=ai_response,
                ):
                    with patch("pathlib.Path.read_text", return_value="test content"):
                        result = self.command._generate_with_ai_templates(
                            self.test_path, "standard", None
                        )

                        assert result == ai_response

    def test_generate_with_ai_templates_when_template_fails_then_fallback_to_direct_ai(
        self,
    ):
        """Test _generate_with_ai_templates falls back to direct AI when template fails."""
        # Mock template failure
        mock_template_result = Mock()
        mock_template_result.success = False
        mock_template_result.error = "Template parsing error"

        mock_ai_template = Mock()
        mock_ai_template.load_and_process_template.return_value = mock_template_result

        direct_ai_result = {"success": True, "data": {"content": "Direct AI result"}}

        with patch(
            "spec_cli.cli.commands.gen_command.AIEnhancedTemplate",
            return_value=mock_ai_template,
        ):
            with patch.object(
                self.command, "_create_template_variables", return_value={}
            ):
                with patch(
                    "spec_cli.cli.commands.gen_command.generate_with_ai",
                    return_value=direct_ai_result,
                ):
                    result = self.command._generate_with_ai_templates(
                        self.test_path, "standard", None
                    )

                    assert result == direct_ai_result

    def test_generate_with_ai_templates_when_file_read_fails_then_returns_error_with_fallback(
        self,
    ):
        """Test _generate_with_ai_templates handles file read errors with fallback signal."""
        with patch(
            "pathlib.Path.read_text", side_effect=Exception("File access denied")
        ):
            result = self.command._generate_with_ai_templates(
                self.test_path, "standard", None
            )

            assert result["success"] is False
            assert "Failed to read source file" in result["error"]
            assert result["data"]["fallback_needed"] is True

    def test_generate_with_ai_templates_when_exception_then_returns_error_with_fallback(
        self,
    ):
        """Test _generate_with_ai_templates handles exceptions with fallback signal."""
        with patch(
            "spec_cli.cli.commands.gen_command.AIEnhancedTemplate",
            side_effect=Exception("AI service unavailable"),
        ):
            result = self.command._generate_with_ai_templates(
                self.test_path, "standard", None
            )

            assert result["success"] is False
            assert (
                "Template-based AI generation failed: AI service unavailable"
                in result["error"]
            )
            assert result["data"]["fallback_needed"] is True


class TestGenCommandTemplateGeneration:
    """Test template generation methods."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test")
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/.specs")
        self.command = GenCommand(self.mock_settings)
        self.test_path = Path("/test/example.py")

    def test_generate_with_templates_when_ai_enhanced_then_uses_ai_enhanced_template(
        self,
    ):
        """Test _generate_with_templates uses AI enhanced templates correctly."""
        mock_template_result = Mock()
        mock_template_result.success = True

        mock_ai_template = Mock()
        mock_ai_template.load_and_process_template.return_value = mock_template_result

        with patch(
            "spec_cli.cli.commands.gen_command.AIEnhancedTemplate",
            return_value=mock_ai_template,
        ):
            with patch.object(
                self.command, "_create_template_variables", return_value={}
            ):
                result = self.command._generate_with_templates(
                    target_path=self.test_path,
                    template_path=None,
                    ai_enhanced=True,
                    reason="AI fallback",
                )

                assert result["success"] is True
                assert result["data"]["generation_method"] == "ai_enhanced_template"

    def test_generate_with_templates_when_traditional_then_uses_traditional_generation(
        self,
    ):
        """Test _generate_with_templates uses traditional template generation."""
        generated_files = [Path("/test/.specs/example/index.md")]

        with patch.object(
            self.command,
            "_traditional_template_generation",
            return_value=generated_files,
        ):
            result = self.command._generate_with_templates(
                target_path=self.test_path,
                template_path=None,
                ai_enhanced=False,
                reason="AI disabled",
            )

            assert result["success"] is True
            assert result["data"]["generation_method"] == "traditional_template"
            assert len(result["data"]["generated_files"]) == 1

    def test_generate_with_templates_when_ai_enhanced_fails_then_returns_error(self):
        """Test _generate_with_templates handles AI enhanced template failures."""
        mock_template_result = Mock()
        mock_template_result.success = False
        mock_template_result.error = "AI template processing failed"

        mock_ai_template = Mock()
        mock_ai_template.load_and_process_template.return_value = mock_template_result

        with patch(
            "spec_cli.cli.commands.gen_command.AIEnhancedTemplate",
            return_value=mock_ai_template,
        ):
            with patch.object(
                self.command, "_create_template_variables", return_value={}
            ):
                result = self.command._generate_with_templates(
                    target_path=self.test_path,
                    template_path=None,
                    ai_enhanced=True,
                    reason="AI fallback",
                )

                assert result["success"] is False
                assert "AI-enhanced template processing failed" in result["error"]

    def test_generate_with_templates_when_no_files_generated_then_returns_error(self):
        """Test _generate_with_templates handles empty generation results."""
        with patch.object(
            self.command, "_traditional_template_generation", return_value=[]
        ):
            result = self.command._generate_with_templates(
                target_path=self.test_path,
                template_path=None,
                ai_enhanced=False,
                reason="AI disabled",
            )

            assert result["success"] is False
            assert "Template generation produced no output files" in result["error"]

    def test_generate_with_templates_when_exception_then_returns_error(self):
        """Test _generate_with_templates handles exceptions during generation."""
        with patch.object(
            self.command,
            "_traditional_template_generation",
            side_effect=Exception("Template error"),
        ):
            result = self.command._generate_with_templates(
                target_path=self.test_path,
                template_path=None,
                ai_enhanced=False,
                reason="AI disabled",
            )

            assert result["success"] is False
            assert "Template generation failed: Template error" in result["error"]


class TestGenCommandFinalizeResults:
    """Test AI result finalization methods."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test")
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/.specs")
        self.mock_settings.ignore_file = Path("/test/.specignore")
        self.command = GenCommand(self.mock_settings)
        self.test_path = Path("/test/example.py")

    def test_finalize_ai_results_when_successful_then_writes_files(self, tmp_path):
        """Test _finalize_ai_results writes AI content to spec files."""
        ai_result = {
            "success": True,
            "data": {
                "generated_docs": {
                    "main": "# AI Generated Content\n\nThis is AI content."
                },
                "metadata": {},
            },
        }

        spec_dir = tmp_path / ".specs" / "example"
        spec_dir.mkdir(parents=True)

        mock_spec_files = {
            "index": spec_dir / "index.md",
            "history": spec_dir / "history.md",
        }

        mock_path_resolver = Mock()
        mock_path_resolver.get_spec_files_for_source.return_value = mock_spec_files

        mock_directory_manager = Mock()
        mock_directory_manager.create_spec_directory.return_value = spec_dir

        with patch(
            "spec_cli.cli.commands.gen_command.PathResolver",
            return_value=mock_path_resolver,
        ):
            with patch(
                "spec_cli.cli.commands.gen_command.DirectoryManager",
                return_value=mock_directory_manager,
            ):
                with patch(
                    "spec_cli.cli.commands.gen_command.load_template"
                ) as mock_load_template:
                    with patch(
                        "spec_cli.cli.commands.gen_command.TemplateSubstitution"
                    ) as mock_substitution:
                        # Mock template loading
                        mock_template_config = Mock()
                        mock_template_config.history = (
                            "# History\n{{date}}: {{context}}"
                        )
                        mock_load_template.return_value = mock_template_config

                        # Mock substitution
                        mock_substitution_instance = Mock()
                        mock_substitution_instance.substitute.return_value = (
                            "# History\n2023-01-01: AI generation"
                        )
                        mock_substitution.return_value = mock_substitution_instance

                        result = self.command._finalize_ai_results(
                            ai_result, self.test_path
                        )

                        assert result["success"] is True
                        assert "generated_files" in result["data"]
                        assert (
                            len(result["data"]["generated_files"]) == 2
                        )  # index.md and history.md

    def test_finalize_ai_results_when_no_content_then_returns_error(self):
        """Test _finalize_ai_results handles empty AI content."""
        ai_result = {"success": True, "data": {"generated_docs": {}}}

        result = self.command._finalize_ai_results(ai_result, self.test_path)

        assert result["success"] is False
        assert "AI generation returned no content to write" in result["error"]

    def test_finalize_ai_results_when_template_fails_then_uses_fallback_history(
        self, tmp_path
    ):
        """Test _finalize_ai_results uses fallback history when template fails."""
        ai_result = {
            "success": True,
            "data": {"generated_docs": {"main": "# AI Content"}, "metadata": {}},
        }

        spec_dir = tmp_path / ".specs" / "example"
        spec_dir.mkdir(parents=True)

        mock_spec_files = {
            "index": spec_dir / "index.md",
            "history": spec_dir / "history.md",
        }

        mock_path_resolver = Mock()
        mock_path_resolver.get_spec_files_for_source.return_value = mock_spec_files

        mock_directory_manager = Mock()
        mock_directory_manager.create_spec_directory.return_value = spec_dir

        with patch(
            "spec_cli.cli.commands.gen_command.PathResolver",
            return_value=mock_path_resolver,
        ):
            with patch(
                "spec_cli.cli.commands.gen_command.DirectoryManager",
                return_value=mock_directory_manager,
            ):
                with patch(
                    "spec_cli.cli.commands.gen_command.load_template",
                    side_effect=Exception("Template error"),
                ):
                    result = self.command._finalize_ai_results(
                        ai_result, self.test_path
                    )

                    assert result["success"] is True
                    # Should still write index.md and fallback history.md
                    assert len(result["data"]["generated_files"]) == 2

    def test_finalize_ai_results_when_write_fails_then_returns_error(self):
        """Test _finalize_ai_results handles file write errors."""
        ai_result = {
            "success": True,
            "data": {"generated_docs": {"main": "# AI Content"}},
        }

        with patch(
            "spec_cli.cli.commands.gen_command.PathResolver",
            side_effect=Exception("Write error"),
        ):
            result = self.command._finalize_ai_results(ai_result, self.test_path)

            assert result["success"] is False
            assert "Failed to write AI-generated files" in result["error"]


class TestGenerateWithAIFunction:
    """Test the standalone generate_with_ai function."""

    def test_generate_with_ai_when_called_then_returns_not_implemented(self):
        """Test generate_with_ai function returns not implemented error."""
        result = generate_with_ai(Path("/test/file.py"), "standard", None)

        assert result["success"] is False
        assert "AI generation not yet implemented" in result["error"]


class TestGenCommandEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test environment for each test."""
        self.mock_settings = Mock(spec=SpecSettings)
        self.mock_settings.root_path = Path("/test")
        self.mock_settings.spec_dir = Path("/test/.spec")
        self.mock_settings.specs_dir = Path("/test/.specs")
        self.mock_settings.ignore_file = Path("/test/.specignore")
        self.command = GenCommand(self.mock_settings)

    def test_expand_source_files_when_file_and_directory_then_returns_all_processable(
        self,
    ):
        """Test _expand_source_files handles mixed file and directory inputs."""
        test_file = Path("/test/file.py")
        test_dir = Path("/test/src")

        mock_validator = Mock()
        mock_validator._is_processable_file.return_value = True
        mock_validator._get_processable_files_in_directory.return_value = [
            Path("/test/src/module1.py"),
            Path("/test/src/module2.py"),
        ]

        with patch(
            "spec_cli.cli.commands.generation.validation.GenerationValidator",
            return_value=mock_validator,
        ):
            with patch("pathlib.Path.is_file", lambda self: self == test_file):
                with patch("pathlib.Path.is_dir", lambda self: self == test_dir):
                    result = self.command._expand_source_files([test_file, test_dir])

                    assert len(result) == 3  # 1 file + 2 from directory

    def test_expand_source_files_when_no_processable_files_then_returns_empty(self):
        """Test _expand_source_files returns empty list when no files are processable."""
        test_file = Path("/test/binary.exe")

        mock_validator = Mock()
        mock_validator._is_processable_file.return_value = False

        with patch(
            "spec_cli.cli.commands.generation.validation.GenerationValidator",
            return_value=mock_validator,
        ):
            with patch("pathlib.Path.is_file", return_value=True):
                with patch("pathlib.Path.is_dir", return_value=False):
                    result = self.command._expand_source_files([test_file])

                    assert result == []

    def test_show_dry_run_preview_when_called_then_displays_preview(self, capsys):
        """Test _show_dry_run_preview displays correct preview information."""
        test_files = [Path("/test/file1.py"), Path("/test/file2.py")]
        template = "default"
        from spec_cli.file_processing.conflict_resolver import (
            ConflictResolutionStrategy,
        )

        conflict_strategy = ConflictResolutionStrategy.BACKUP_AND_REPLACE

        mock_spec_files = {
            "index": Path("/test/.specs/file1/index.md"),
            "history": Path("/test/.specs/file1/history.md"),
        }

        mock_path_resolver = Mock()
        mock_path_resolver.get_spec_files_for_source.return_value = mock_spec_files

        with patch(
            "spec_cli.file_system.path_resolver.PathResolver",
            return_value=mock_path_resolver,
        ):
            with patch(
                "pathlib.Path.exists",
                lambda self: str(self) == "/test/.specs/file1/history.md",
            ):
                with patch("spec_cli.cli.commands.gen_command.show_message"):
                    self.command._show_dry_run_preview(
                        test_files, template, conflict_strategy
                    )

                    # Should complete without error (detailed output testing would require console mocking)

    def test_traditional_template_generation_when_successful_then_returns_file_paths(
        self,
    ):
        """Test _traditional_template_generation calls correct methods and returns paths."""
        test_path = Path("/test/example.py")
        generated_files = {
            "index": Path("/test/.specs/example/index.md"),
            "history": Path("/test/.specs/example/history.md"),
        }

        mock_generator = Mock()
        mock_generator.generate_spec_content.return_value = generated_files

        mock_template_config = Mock()

        with patch(
            "spec_cli.cli.commands.gen_command.SpecContentGenerator",
            return_value=mock_generator,
        ):
            with patch(
                "spec_cli.cli.commands.gen_command.load_template",
                return_value=mock_template_config,
            ):
                result = self.command._traditional_template_generation(test_path, None)

                assert result == list(generated_files.values())
                mock_generator.generate_spec_content.assert_called_once_with(
                    test_path, mock_template_config
                )

    def test_traditional_template_generation_when_fails_then_raises_exception(self):
        """Test _traditional_template_generation re-raises exceptions."""
        test_path = Path("/test/example.py")

        with patch(
            "spec_cli.cli.commands.gen_command.SpecContentGenerator",
            side_effect=Exception("Generator error"),
        ):
            with pytest.raises(Exception, match="Generator error"):
                self.command._traditional_template_generation(test_path, None)
