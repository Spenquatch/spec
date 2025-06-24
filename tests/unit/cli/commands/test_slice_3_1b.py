"""Unit tests for Slice 3.1b: Template Fallback & Enhancement in GenCommand."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.gen_command import GenCommand
from spec_cli.config.settings import SpecSettings
from spec_cli.exceptions import SpecError

# Test constants
DEFAULT_TARGET_PATH = Path("test_file.py")
DEFAULT_DOC_TYPE = "standard"
DEFAULT_TEMPLATE_PATH = None
DEFAULT_NO_AI = False
EXPECTED_SUCCESS_RESULT = True
EXPECTED_FAILURE_RESULT = False
AI_DISABLED_REASON = "AI disabled by user"
AI_FALLBACK_REASON = "AI fallback: Test AI error"
ENHANCED_TEMPLATE_METHOD = "ai_enhanced_template"
TRADITIONAL_TEMPLATE_METHOD = "traditional_template"
DEFAULT_METADATA_KEYS = [
    "generation_method",
    "files_generated",
    "generation_reason",
    "generation_time",
    "target_path",
]


class TestSlice3_1bGenCommandInitialization:
    """Test GenCommand initialization with enhanced features."""

    def test_init_with_default_settings_creates_command_with_console(self):
        """Test GenCommand initialization with default settings."""
        command = GenCommand()

        assert command.settings is not None
        assert command.console is not None

    def test_init_with_custom_settings_uses_provided_settings(self):
        """Test GenCommand initialization with custom settings."""
        custom_settings = Mock(spec=SpecSettings)
        custom_settings.root_path = Path(
            "/test/project"
        )  # BaseCommand expects root_path
        command = GenCommand(custom_settings)

        assert command.settings is custom_settings
        assert command.console is not None


class TestSlice3_1bExecuteSingleFileAIFirst:
    """Test _execute_single_file method with AI-first logic."""

    @pytest.fixture
    def mock_command(self):
        """Create mock GenCommand with all dependencies mocked."""
        with (
            patch.object(GenCommand, "_generate_with_ai_templates") as mock_ai_gen,
            patch(
                "spec_cli.cli.commands.gen_command.AIEnhancedTemplate"
            ) as mock_template,
            patch(
                "spec_cli.cli.commands.gen_command.create_workflow_result"
            ) as mock_result,
            patch("spec_cli.cli.commands.gen_command.debug_logger") as mock_logger,
            patch("spec_cli.cli.commands.gen_command.normalize_path") as mock_normalize,
        ):
            command = GenCommand()
            command._generate_with_templates = Mock()
            command._finalize_ai_results = Mock()
            command._traditional_template_generation = Mock()
            command._create_template_variables = Mock()

            yield {
                "command": command,
                "mock_ai_gen": mock_ai_gen,
                "mock_template": mock_template,
                "mock_result": mock_result,
                "mock_logger": mock_logger,
                "mock_normalize": mock_normalize,
            }

    def test_execute_single_file_when_no_ai_flag_then_uses_traditional_templates(
        self, mock_command
    ):
        """Test _execute_single_file when --no-ai flag is set."""
        mock_command["command"]._generate_with_templates.return_value = {
            "success": EXPECTED_SUCCESS_RESULT,
            "data": {"generation_method": TRADITIONAL_TEMPLATE_METHOD},
        }

        result = mock_command["command"]._execute_single_file(
            target_path=DEFAULT_TARGET_PATH,
            doc_type=DEFAULT_DOC_TYPE,
            template_path=DEFAULT_TEMPLATE_PATH,
            no_ai=True,
        )

        # Verify traditional template generation was called
        mock_command["command"]._generate_with_templates.assert_called_once_with(
            target_path=DEFAULT_TARGET_PATH,
            template_path=DEFAULT_TEMPLATE_PATH,
            ai_enhanced=EXPECTED_FAILURE_RESULT,
            reason=AI_DISABLED_REASON,
        )

        # Verify AI generation was not attempted
        mock_command["mock_ai_gen"].assert_not_called()

        assert result["success"] == EXPECTED_SUCCESS_RESULT

    def test_execute_single_file_when_ai_succeeds_then_returns_ai_results(
        self, mock_command
    ):
        """Test _execute_single_file when AI generation succeeds."""
        # Setup successful AI result
        ai_success_result = {
            "success": EXPECTED_SUCCESS_RESULT,
            "data": {"generated_docs": {"test.py": "AI content"}},
            "message": "AI generation successful",
        }
        mock_command["mock_ai_gen"].return_value = ai_success_result
        mock_command["command"]._finalize_ai_results.return_value = ai_success_result

        result = mock_command["command"]._execute_single_file(
            target_path=DEFAULT_TARGET_PATH,
            doc_type=DEFAULT_DOC_TYPE,
            template_path=DEFAULT_TEMPLATE_PATH,
            no_ai=DEFAULT_NO_AI,
        )

        # Verify AI generation was attempted
        mock_command["mock_ai_gen"].assert_called_once_with(
            DEFAULT_TARGET_PATH, DEFAULT_DOC_TYPE, DEFAULT_TEMPLATE_PATH
        )

        # Verify AI results were finalized
        mock_command["command"]._finalize_ai_results.assert_called_once_with(
            ai_success_result, DEFAULT_TARGET_PATH
        )

        # Verify template fallback was not called
        mock_command["command"]._generate_with_templates.assert_not_called()

        assert result["success"] == EXPECTED_SUCCESS_RESULT

    def test_execute_single_file_when_ai_fails_with_fallback_then_uses_enhanced_templates(
        self, mock_command
    ):
        """Test _execute_single_file when AI fails and signals fallback needed."""
        # Setup failed AI result with fallback signal
        ai_failure_result = {
            "success": EXPECTED_FAILURE_RESULT,
            "error": "Test AI error",
            "data": {"fallback_needed": True},
        }
        mock_command["mock_ai_gen"].return_value = ai_failure_result

        enhanced_template_result = {
            "success": EXPECTED_SUCCESS_RESULT,
            "data": {"generation_method": ENHANCED_TEMPLATE_METHOD},
        }
        mock_command[
            "command"
        ]._generate_with_templates.return_value = enhanced_template_result

        result = mock_command["command"]._execute_single_file(
            target_path=DEFAULT_TARGET_PATH,
            doc_type=DEFAULT_DOC_TYPE,
            template_path=DEFAULT_TEMPLATE_PATH,
            no_ai=DEFAULT_NO_AI,
        )

        # Verify AI generation was attempted
        mock_command["mock_ai_gen"].assert_called_once_with(
            DEFAULT_TARGET_PATH, DEFAULT_DOC_TYPE, DEFAULT_TEMPLATE_PATH
        )

        # Verify enhanced template generation was called as fallback
        mock_command["command"]._generate_with_templates.assert_called_once_with(
            target_path=DEFAULT_TARGET_PATH,
            template_path=DEFAULT_TEMPLATE_PATH,
            ai_enhanced=EXPECTED_SUCCESS_RESULT,
            reason=AI_FALLBACK_REASON,
        )

        # Verify debug logging for fallback
        mock_command["mock_logger"].log.assert_called_with(
            "INFO",
            "AI generation failed, falling back to enhanced templates",
            target_path=str(DEFAULT_TARGET_PATH),
            error="Test AI error",
        )

        assert result["success"] == EXPECTED_SUCCESS_RESULT

    def test_execute_single_file_when_ai_fails_without_fallback_then_returns_ai_error(
        self, mock_command
    ):
        """Test _execute_single_file when AI fails without fallback signal."""
        # Setup failed AI result without fallback signal
        ai_failure_result = {
            "success": EXPECTED_FAILURE_RESULT,
            "error": "Test AI error",
            "data": {"fallback_needed": False},
        }
        mock_command["mock_ai_gen"].return_value = ai_failure_result

        result = mock_command["command"]._execute_single_file(
            target_path=DEFAULT_TARGET_PATH,
            doc_type=DEFAULT_DOC_TYPE,
            template_path=DEFAULT_TEMPLATE_PATH,
            no_ai=DEFAULT_NO_AI,
        )

        # Verify AI generation was attempted
        mock_command["mock_ai_gen"].assert_called_once_with(
            DEFAULT_TARGET_PATH, DEFAULT_DOC_TYPE, DEFAULT_TEMPLATE_PATH
        )

        # Verify template fallback was not called
        mock_command["command"]._generate_with_templates.assert_not_called()

        # Return the original AI failure result
        assert result == ai_failure_result

    def test_execute_single_file_when_exception_occurs_then_returns_error_result(
        self, mock_command
    ):
        """Test _execute_single_file when exception occurs during processing."""
        # Setup AI generation to raise exception
        mock_command["mock_ai_gen"].side_effect = Exception("Test exception")

        error_result = {
            "success": EXPECTED_FAILURE_RESULT,
            "error": "Documentation generation failed: Test exception",
        }
        mock_command["mock_result"].return_value = error_result

        result = mock_command["command"]._execute_single_file(
            target_path=DEFAULT_TARGET_PATH,
            doc_type=DEFAULT_DOC_TYPE,
            template_path=DEFAULT_TEMPLATE_PATH,
            no_ai=DEFAULT_NO_AI,
        )

        # Verify error was logged
        mock_command["mock_logger"].log.assert_called_with(
            "ERROR",
            "Single file execution failed",
            target_path=str(DEFAULT_TARGET_PATH),
            error="Test exception",
        )

        # Verify error result was created
        mock_command["mock_result"].assert_called_with(
            success=EXPECTED_FAILURE_RESULT,
            error="Documentation generation failed: Test exception",
        )

        assert result == error_result


class TestSlice3_1bGenerateWithTemplates:
    """Test _generate_with_templates method for both AI-enhanced and traditional modes."""

    @pytest.fixture
    def mock_command_templates(self):
        """Create mock GenCommand for template testing."""
        with (
            patch(
                "spec_cli.cli.commands.gen_command.AIEnhancedTemplate"
            ) as mock_ai_template,
            patch(
                "spec_cli.cli.commands.gen_command.create_workflow_result"
            ) as mock_result,
            patch("spec_cli.cli.commands.gen_command.debug_logger") as mock_logger,
            patch("spec_cli.cli.commands.gen_command.datetime") as mock_datetime,
        ):
            command = GenCommand()
            command._traditional_template_generation = Mock()
            command._create_template_variables = Mock()

            # Setup datetime mock
            mock_datetime.now.return_value.isoformat.return_value = (
                "2024-01-01T12:00:00"
            )

            yield {
                "command": command,
                "mock_ai_template": mock_ai_template,
                "mock_result": mock_result,
                "mock_logger": mock_logger,
                "mock_datetime": mock_datetime,
            }

    def test_generate_with_templates_when_ai_enhanced_true_then_uses_ai_enhanced_template(
        self, mock_command_templates
    ):
        """Test _generate_with_templates with ai_enhanced=True."""
        # Setup AI-enhanced template mock
        mock_template_instance = Mock()
        mock_template_result = Mock()
        mock_template_result.success = EXPECTED_SUCCESS_RESULT
        mock_template_instance.load_and_process_template.return_value = (
            mock_template_result
        )
        mock_command_templates["mock_ai_template"].return_value = mock_template_instance

        # Setup template variables
        test_variables = {"filename": "test.py", "filepath": "/test/test.py"}
        mock_command_templates[
            "command"
        ]._create_template_variables.return_value = test_variables

        # Setup successful result
        success_result = {
            "success": EXPECTED_SUCCESS_RESULT,
            "data": {
                "generated_files": [str(DEFAULT_TARGET_PATH)],
                "generation_method": ENHANCED_TEMPLATE_METHOD,
                "metadata": {},
            },
        }
        mock_command_templates["mock_result"].return_value = success_result

        result = mock_command_templates["command"]._generate_with_templates(
            target_path=DEFAULT_TARGET_PATH,
            template_path=DEFAULT_TEMPLATE_PATH,
            ai_enhanced=EXPECTED_SUCCESS_RESULT,
            reason="Test reason",
        )

        # Verify AI-enhanced template was created
        mock_command_templates["mock_ai_template"].assert_called_once_with(
            DEFAULT_TEMPLATE_PATH
        )

        # Verify template variables were created
        mock_command_templates[
            "command"
        ]._create_template_variables.assert_called_once_with(DEFAULT_TARGET_PATH)

        # Verify template processing was called
        mock_template_instance.load_and_process_template.assert_called_once_with(
            variables=test_variables, ai_enabled=EXPECTED_SUCCESS_RESULT
        )

        assert result == success_result

    def test_generate_with_templates_when_ai_enhanced_false_then_uses_traditional_template(
        self, mock_command_templates
    ):
        """Test _generate_with_templates with ai_enhanced=False."""
        # Setup traditional template generation
        generated_files = [DEFAULT_TARGET_PATH]
        mock_command_templates[
            "command"
        ]._traditional_template_generation.return_value = generated_files

        # Setup successful result
        success_result = {
            "success": EXPECTED_SUCCESS_RESULT,
            "data": {
                "generated_files": [str(DEFAULT_TARGET_PATH)],
                "generation_method": TRADITIONAL_TEMPLATE_METHOD,
                "metadata": {},
            },
        }
        mock_command_templates["mock_result"].return_value = success_result

        result = mock_command_templates["command"]._generate_with_templates(
            target_path=DEFAULT_TARGET_PATH,
            template_path=DEFAULT_TEMPLATE_PATH,
            ai_enhanced=EXPECTED_FAILURE_RESULT,
            reason="Test reason",
        )

        # Verify traditional template generation was called
        mock_command_templates[
            "command"
        ]._traditional_template_generation.assert_called_once_with(
            target_path=DEFAULT_TARGET_PATH, template_path=DEFAULT_TEMPLATE_PATH
        )

        # Verify AI-enhanced template was not used
        mock_command_templates["mock_ai_template"].assert_not_called()

        assert result == success_result

    def test_generate_with_templates_when_ai_template_fails_then_returns_error_result(
        self, mock_command_templates
    ):
        """Test _generate_with_templates when AI-enhanced template processing fails."""
        # Setup failing AI-enhanced template
        mock_template_instance = Mock()
        mock_template_result = Mock()
        mock_template_result.success = EXPECTED_FAILURE_RESULT
        mock_template_result.error = "Template processing error"
        mock_template_instance.load_and_process_template.return_value = (
            mock_template_result
        )
        mock_command_templates["mock_ai_template"].return_value = mock_template_instance

        # Setup template variables
        test_variables = {"filename": "test.py"}
        mock_command_templates[
            "command"
        ]._create_template_variables.return_value = test_variables

        # Setup error result
        error_result = {
            "success": EXPECTED_FAILURE_RESULT,
            "error": "AI-enhanced template processing failed: Template processing error",
        }
        mock_command_templates["mock_result"].return_value = error_result

        result = mock_command_templates["command"]._generate_with_templates(
            target_path=DEFAULT_TARGET_PATH,
            template_path=DEFAULT_TEMPLATE_PATH,
            ai_enhanced=EXPECTED_SUCCESS_RESULT,
            reason="Test reason",
        )

        # Verify error result was returned
        assert result == error_result

    def test_generate_with_templates_when_no_files_generated_then_returns_error_result(
        self, mock_command_templates
    ):
        """Test _generate_with_templates when no files are generated."""
        # Setup traditional template generation returning empty list
        mock_command_templates[
            "command"
        ]._traditional_template_generation.return_value = []

        # Setup error result
        error_result = {
            "success": EXPECTED_FAILURE_RESULT,
            "error": "Template generation produced no output files",
        }
        mock_command_templates["mock_result"].return_value = error_result

        result = mock_command_templates["command"]._generate_with_templates(
            target_path=DEFAULT_TARGET_PATH,
            template_path=DEFAULT_TEMPLATE_PATH,
            ai_enhanced=EXPECTED_FAILURE_RESULT,
            reason="Test reason",
        )

        assert result == error_result

    def test_generate_with_templates_when_exception_occurs_then_returns_error_result(
        self, mock_command_templates
    ):
        """Test _generate_with_templates when exception occurs during processing."""
        # Setup AI-enhanced template to raise exception
        mock_command_templates["mock_ai_template"].side_effect = Exception(
            "Template creation error"
        )

        # Setup error result
        error_result = {
            "success": EXPECTED_FAILURE_RESULT,
            "error": "Template generation failed: Template creation error",
        }
        mock_command_templates["mock_result"].return_value = error_result

        result = mock_command_templates["command"]._generate_with_templates(
            target_path=DEFAULT_TARGET_PATH,
            template_path=DEFAULT_TEMPLATE_PATH,
            ai_enhanced=EXPECTED_SUCCESS_RESULT,
            reason="Test reason",
        )

        # Verify error was logged
        mock_command_templates["mock_logger"].log.assert_called_with(
            "ERROR",
            "Template generation failed",
            target_path=str(DEFAULT_TARGET_PATH),
            ai_enhanced=EXPECTED_SUCCESS_RESULT,
            error="Template creation error",
        )

        assert result == error_result


class TestSlice3_1bFinalizeAIResults:
    """Test _finalize_ai_results method."""

    @pytest.fixture
    def mock_command_finalize(self):
        """Create mock GenCommand for finalization testing."""
        with (
            patch(
                "spec_cli.cli.commands.gen_command.create_workflow_result"
            ) as mock_result,
            patch("spec_cli.cli.commands.gen_command.datetime") as mock_datetime,
        ):
            command = GenCommand()

            # Setup datetime mock
            mock_datetime.now.return_value.isoformat.return_value = (
                "2024-01-01T12:00:00"
            )

            yield {
                "command": command,
                "mock_result": mock_result,
                "mock_datetime": mock_datetime,
            }

    def test_finalize_ai_results_when_valid_result_then_adds_command_metadata(
        self, mock_command_finalize
    ):
        """Test _finalize_ai_results adds command-level metadata."""
        # Setup AI result with existing metadata
        ai_result = {
            "success": EXPECTED_SUCCESS_RESULT,
            "data": {
                "generated_docs": {"test.py": "content"},
                "metadata": {"provider": "test_provider"},
            },
            "message": "AI generation successful",
        }

        # Setup finalized result
        finalized_result = {
            "success": EXPECTED_SUCCESS_RESULT,
            "data": ai_result["data"],
            "message": "Generated and wrote 2 files using AI",
        }
        mock_command_finalize["mock_result"].return_value = finalized_result

        result = mock_command_finalize["command"]._finalize_ai_results(
            ai_result, DEFAULT_TARGET_PATH
        )

        # Verify metadata was enhanced
        expected_data = ai_result["data"].copy()
        expected_data["metadata"]["command_execution_time"] = "2024-01-01T12:00:00"
        expected_data["metadata"]["target_path"] = str(DEFAULT_TARGET_PATH)

        mock_command_finalize["mock_result"].assert_called_once_with(
            success=EXPECTED_SUCCESS_RESULT,
            data=expected_data,
            message="Generated and wrote 2 files using AI",
        )

        assert result == finalized_result

    def test_finalize_ai_results_when_no_existing_metadata_then_creates_metadata(
        self, mock_command_finalize
    ):
        """Test _finalize_ai_results creates metadata when none exists."""
        # Setup AI result without metadata
        ai_result = {
            "success": EXPECTED_SUCCESS_RESULT,
            "data": {"generated_docs": {"test.py": "content"}},
            "message": "Success",
        }

        finalized_result = {"success": EXPECTED_SUCCESS_RESULT}
        mock_command_finalize["mock_result"].return_value = finalized_result

        result = mock_command_finalize["command"]._finalize_ai_results(
            ai_result, DEFAULT_TARGET_PATH
        )

        # Verify metadata was created
        expected_data = ai_result["data"].copy()
        expected_data["metadata"] = {
            "command_execution_time": "2024-01-01T12:00:00",
            "target_path": str(DEFAULT_TARGET_PATH),
            "files_written": 2,
        }

        mock_command_finalize["mock_result"].assert_called_once_with(
            success=EXPECTED_SUCCESS_RESULT,
            data=expected_data,
            message="Generated and wrote 2 files using AI",
        )

        assert result == finalized_result


class TestSlice3_1bValidateArguments:
    """Test validate_arguments method with new parameters."""

    def test_validate_arguments_when_no_ai_valid_boolean_then_passes(self):
        """Test validate_arguments accepts valid no_ai boolean values."""
        command = GenCommand()

        # Test with True
        command.validate_arguments(
            files=[Path("test.py")],
            template="default",
            conflict_strategy="backup",
            no_ai=EXPECTED_SUCCESS_RESULT,
            doc_type="standard",
        )

        # Test with False
        command.validate_arguments(
            files=[Path("test.py")],
            template="default",
            conflict_strategy="backup",
            no_ai=EXPECTED_FAILURE_RESULT,
            doc_type="standard",
        )

    def test_validate_arguments_when_no_ai_invalid_type_then_raises_error(self):
        """Test validate_arguments raises error for invalid no_ai type."""
        command = GenCommand()

        with pytest.raises(SpecError, match="Invalid no_ai flag type"):
            command.validate_arguments(
                files=[Path("test.py")],
                template="default",
                conflict_strategy="backup",
                no_ai="invalid",  # Should be boolean
                doc_type="standard",
            )

    def test_validate_arguments_when_doc_type_valid_then_passes(self):
        """Test validate_arguments accepts valid doc_type values."""
        command = GenCommand()

        valid_doc_types = ["standard", "comprehensive", "minimal", "api", "tutorial"]

        for doc_type in valid_doc_types:
            command.validate_arguments(
                files=[Path("test.py")],
                template="default",
                conflict_strategy="backup",
                no_ai=EXPECTED_FAILURE_RESULT,
                doc_type=doc_type,
            )

    def test_validate_arguments_when_doc_type_invalid_then_raises_error(self):
        """Test validate_arguments raises error for invalid doc_type."""
        command = GenCommand()

        with pytest.raises(SpecError, match="Invalid doc_type: invalid_type"):
            command.validate_arguments(
                files=[Path("test.py")],
                template="default",
                conflict_strategy="backup",
                no_ai=EXPECTED_FAILURE_RESULT,
                doc_type="invalid_type",
            )

    def test_validate_arguments_when_doc_type_wrong_type_then_raises_error(self):
        """Test validate_arguments raises error for wrong doc_type type."""
        command = GenCommand()

        with pytest.raises(SpecError, match="Invalid doc_type type"):
            command.validate_arguments(
                files=[Path("test.py")],
                template="default",
                conflict_strategy="backup",
                no_ai=EXPECTED_FAILURE_RESULT,
                doc_type=123,  # Should be string
            )


class TestSlice3_1bCreateTemplateVariables:
    """Test _create_template_variables helper method."""

    @pytest.fixture
    def mock_normalize_path(self):
        """Mock normalize_path function."""
        with patch(
            "spec_cli.cli.commands.gen_command.normalize_path"
        ) as mock_normalize:
            mock_normalize.return_value = Path("/normalized/test.py")
            yield mock_normalize

    def test_create_template_variables_when_valid_path_then_returns_complete_variables(
        self, mock_normalize_path
    ):
        """Test _create_template_variables returns all expected variables."""
        command = GenCommand()
        test_path = Path("/test/directory/sample.py")

        with patch("spec_cli.cli.commands.gen_command.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = (
                "2024-01-01T12:00:00"
            )

            variables = command._create_template_variables(test_path)

        # Verify all expected variables are present
        expected_variables = {
            "filename": "sample.py",
            "filepath": "/normalized/test.py",
            "parent_dir": "directory",
            "file_ext": ".py",
            "timestamp": "2024-01-01T12:00:00",
        }

        assert variables == expected_variables
        mock_normalize_path.assert_called_once_with(test_path)

    def test_create_template_variables_when_path_without_extension_then_handles_gracefully(
        self, mock_normalize_path
    ):
        """Test _create_template_variables handles files without extensions."""
        command = GenCommand()
        test_path = Path("/test/README")

        with patch("spec_cli.cli.commands.gen_command.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = (
                "2024-01-01T12:00:00"
            )

            variables = command._create_template_variables(test_path)

        assert variables["filename"] == "README"
        assert variables["file_ext"] == ""  # No extension
        assert variables["parent_dir"] == "test"


class TestSlice3_1bTraditionalTemplateGeneration:
    """Test _traditional_template_generation method."""

    def test_traditional_template_generation_when_called_then_logs_and_returns_path(
        self,
    ):
        """Test _traditional_template_generation logs operation and returns file path."""
        command = GenCommand()

        with patch("spec_cli.cli.commands.gen_command.debug_logger") as mock_logger:
            result = command._traditional_template_generation(
                target_path=DEFAULT_TARGET_PATH, template_path=DEFAULT_TEMPLATE_PATH
            )

        # Verify both start and completion logs occurred
        assert mock_logger.log.call_count == 2
        mock_logger.log.assert_any_call(
            "INFO",
            "Traditional template generation",
            target_path=str(DEFAULT_TARGET_PATH),
            template_path="default",
        )

        # Verify returns generated spec files
        assert len(result) == 2
        assert any("index.md" in str(f) for f in result)
        assert any("history.md" in str(f) for f in result)

    def test_traditional_template_generation_when_custom_template_then_logs_template_path(
        self,
    ):
        """Test _traditional_template_generation logs custom template path."""
        command = GenCommand()
        custom_template = Path("/custom/template.md")

        with patch("spec_cli.cli.commands.gen_command.debug_logger") as mock_logger:
            result = command._traditional_template_generation(
                target_path=DEFAULT_TARGET_PATH, template_path=custom_template
            )

        # Verify both start and completion logs occurred
        assert mock_logger.log.call_count == 2
        mock_logger.log.assert_any_call(
            "INFO",
            "Traditional template generation",
            target_path=str(DEFAULT_TARGET_PATH),
            template_path=str(custom_template),
        )

        # Verify returns generated spec files
        assert len(result) == 2
        assert any("index.md" in str(f) for f in result)
        assert any("history.md" in str(f) for f in result)


class TestSlice3_1bBackwardCompatibility:
    """Test backward compatibility with existing gen command functionality."""

    def test_execute_when_traditional_parameters_then_maintains_compatibility(self):
        """Test execute method maintains backward compatibility with traditional parameters."""
        command = GenCommand()

        # Mock all the dependencies to test parameter handling
        with (
            patch.object(command, "validate_repository_state"),
            patch.object(command, "_expand_source_files") as mock_expand,
            patch.object(command, "_execute_single_file") as mock_single_file,
            patch.object(command, "create_result") as mock_create_result,
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input"
            ) as mock_validate,
            patch("spec_cli.cli.commands.gen_command.show_message"),
        ):
            # Setup mocks
            mock_expand.return_value = [Path("test.py")]
            mock_validate.return_value = {"valid": True, "warnings": []}
            mock_single_file.return_value = {
                "success": True,
                "data": {"generated_files": ["test.py"]},
            }
            mock_create_result.return_value = {"success": True}

            # Call with traditional parameters (no new parameters)
            result = command.execute(
                files=[Path("test.py")],
                template="default",
                conflict_strategy="backup",
                commit=False,
                message=None,
                interactive=False,
                force=False,
                dry_run=False,
            )

            # Verify single file execution was called with defaults
            mock_single_file.assert_called_once_with(
                target_path=Path("test.py"),
                doc_type="standard",  # Default value
                template_path=None,  # Default template
                no_ai=False,  # Default no_ai
            )

            assert result["success"]

    def test_execute_when_new_parameters_provided_then_uses_them(self):
        """Test execute method uses new parameters when provided."""
        command = GenCommand()

        # Mock all the dependencies
        with (
            patch.object(command, "validate_repository_state"),
            patch.object(command, "_expand_source_files") as mock_expand,
            patch.object(command, "_execute_single_file") as mock_single_file,
            patch.object(command, "create_result") as mock_create_result,
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input"
            ) as mock_validate,
            patch("spec_cli.cli.commands.gen_command.show_message"),
        ):
            # Setup mocks
            mock_expand.return_value = [Path("test.py")]
            mock_validate.return_value = {"valid": True, "warnings": []}
            mock_single_file.return_value = {
                "success": True,
                "data": {"generated_files": ["test.py"]},
            }
            mock_create_result.return_value = {"success": True}

            # Call with new parameters
            result = command.execute(
                files=[Path("test.py")],
                template="custom",
                no_ai=True,
                doc_type="comprehensive",
            )

            # Verify single file execution was called with new parameters
            mock_single_file.assert_called_once_with(
                target_path=Path("test.py"),
                doc_type="comprehensive",  # Custom doc_type
                template_path=Path("custom"),  # Custom template
                no_ai=True,  # AI disabled
            )

            assert result["success"]
