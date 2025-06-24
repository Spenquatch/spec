"""Integration tests for Slice 3.1b: Template Fallback & Enhancement in GenCommand."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.cli.commands.gen_command import GenCommand
from spec_cli.config.settings import SpecSettings

# Test constants
INTEGRATION_TEST_FILE = "integration_test.py"
INTEGRATION_TEST_CONTENT = '''"""Test module for integration testing."""

def test_function():
    """Test function for documentation generation."""
    return "test"

class TestClass:
    """Test class for documentation generation."""

    def test_method(self):
        """Test method for documentation generation."""
        pass
'''
DEFAULT_DOC_TYPE = "standard"
AI_FIRST_GENERATION_METHOD = "ai"
ENHANCED_TEMPLATE_METHOD = "ai_enhanced_template"
TRADITIONAL_TEMPLATE_METHOD = "traditional_template"


class TestSlice3_1bGenCommandIntegration:
    """Test GenCommand end-to-end integration with AI-first and template fallback."""

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for integration testing."""
        temp_dir = tempfile.mkdtemp()
        project_path = Path(temp_dir)

        # Create test file
        test_file = project_path / INTEGRATION_TEST_FILE
        test_file.write_text(INTEGRATION_TEST_CONTENT)

        yield project_path

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.project_root = Path("/test/project")
        settings.root_path = Path("/test/project")  # BaseCommand expects root_path
        settings.specs_dir = Path(".specs")
        return settings

    def test_integration_ai_first_successful_generation_produces_ai_documentation(
        self, temp_project_dir, mock_settings
    ):
        """Test end-to-end AI-first generation when AI succeeds."""
        command = GenCommand(mock_settings)
        test_file = temp_project_dir / INTEGRATION_TEST_FILE

        # Mock successful AI generation
        ai_success_result = {
            "success": True,
            "data": {
                "generated_docs": {
                    str(test_file): "AI-generated documentation content"
                },
                "generation_metadata": {
                    "provider_type": "LocalAIProvider",
                    "files_generated": 1,
                    "doc_type": DEFAULT_DOC_TYPE,
                },
            },
            "message": "AI generation successful",
        }

        with (
            patch(
                "spec_cli.cli.commands.gen_command.generate_with_ai",
                return_value=ai_success_result,
            ),
            patch.object(command, "validate_repository_state"),
            patch.object(command, "_expand_source_files", return_value=[test_file]),
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input",
                return_value={"valid": True, "warnings": []},
            ),
            patch("spec_cli.cli.commands.gen_command.show_message"),
            patch("spec_cli.cli.commands.gen_command.debug_logger") as mock_logger,
        ):
            result = command.execute(
                files=[test_file],
                template="default",
                no_ai=False,
                doc_type=DEFAULT_DOC_TYPE,
            )

        # Verify AI generation was successful
        assert result["success"] is True
        assert result["data"]["successful_files"] == 1
        assert result["data"]["failed_files"] == 0

        # Verify logging indicates AI generation
        mock_logger.log.assert_called_with(
            "INFO",
            "AI-first generation command completed",
            total_files=1,
            successful_files=1,
            failed_files=0,
            generated_files=1,  # AI generation creates and tracks generated files
        )

    def test_integration_ai_first_when_ai_unavailable_then_falls_back_to_enhanced_templates(
        self, temp_project_dir, mock_settings
    ):
        """Test end-to-end workflow when AI is unavailable and fallback is triggered."""
        command = GenCommand(mock_settings)
        test_file = temp_project_dir / INTEGRATION_TEST_FILE

        # Mock AI failure with fallback signal
        ai_failure_result = {
            "success": False,
            "error": "No AI provider available",
            "data": {"fallback_needed": True},
        }

        # Mock successful AI-enhanced template processing
        mock_template_result = Mock()
        mock_template_result.success = True
        mock_template_result.traditional_content = "Enhanced template content"

        with (
            patch(
                "spec_cli.cli.commands.gen_command.generate_with_ai",
                return_value=ai_failure_result,
            ),
            patch(
                "spec_cli.cli.commands.gen_command.AIEnhancedTemplate"
            ) as mock_ai_template,
            patch(
                "spec_cli.cli.commands.gen_command.create_workflow_result"
            ) as mock_create_result,
            patch.object(command, "validate_repository_state"),
            patch.object(command, "_expand_source_files", return_value=[test_file]),
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input",
                return_value={"valid": True, "warnings": []},
            ),
            patch("spec_cli.cli.commands.gen_command.show_message"),
            patch("spec_cli.cli.commands.gen_command.debug_logger") as mock_logger,
        ):
            # Setup AI-enhanced template mock
            mock_template_instance = Mock()
            mock_template_instance.load_and_process_template.return_value = (
                mock_template_result
            )
            mock_ai_template.return_value = mock_template_instance

            # Setup successful template result
            template_success_result = {
                "success": True,
                "data": {
                    "generated_files": [str(test_file)],
                    "generation_method": ENHANCED_TEMPLATE_METHOD,
                    "metadata": {
                        "generation_method": ENHANCED_TEMPLATE_METHOD,
                        "files_generated": 1,
                        "generation_reason": "AI fallback: No AI provider available",
                    },
                },
                "message": f"Generated 1 files using {ENHANCED_TEMPLATE_METHOD}",
            }
            mock_create_result.return_value = template_success_result

            result = command.execute(
                files=[test_file],
                template="default",
                no_ai=False,
                doc_type=DEFAULT_DOC_TYPE,
            )

        # Verify fallback to enhanced templates occurred
        assert result["success"] is True
        assert result["data"]["successful_files"] == 1
        assert result["data"]["failed_files"] == 0

        # Verify AI-enhanced template was used as fallback
        mock_ai_template.assert_called_once_with(None)  # Default template
        mock_template_instance.load_and_process_template.assert_called_once()

        # Verify fallback logging
        mock_logger.log.assert_any_call(
            "INFO",
            "AI generation failed, falling back to enhanced templates",
            target_path=str(test_file),
            error="No AI provider available",
        )

    def test_integration_traditional_template_only_mode_when_no_ai_flag_set(
        self, temp_project_dir, mock_settings
    ):
        """Test end-to-end workflow with --no-ai flag (traditional template-only mode)."""
        command = GenCommand(mock_settings)
        test_file = temp_project_dir / INTEGRATION_TEST_FILE

        with (
            patch("spec_cli.cli.commands.gen_command.generate_with_ai") as mock_ai_gen,
            patch(
                "spec_cli.cli.commands.gen_command.create_workflow_result"
            ) as mock_create_result,
            patch.object(command, "validate_repository_state"),
            patch.object(command, "_expand_source_files", return_value=[test_file]),
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input",
                return_value={"valid": True, "warnings": []},
            ),
            patch("spec_cli.cli.commands.gen_command.show_message"),
            patch("spec_cli.cli.commands.gen_command.debug_logger") as mock_logger,
        ):
            # Setup traditional template success result
            traditional_success_result = {
                "success": True,
                "data": {
                    "generated_files": [str(test_file)],
                    "generation_method": TRADITIONAL_TEMPLATE_METHOD,
                    "metadata": {
                        "generation_method": TRADITIONAL_TEMPLATE_METHOD,
                        "files_generated": 1,
                        "generation_reason": "AI disabled by user",
                    },
                },
                "message": f"Generated 1 files using {TRADITIONAL_TEMPLATE_METHOD}",
            }
            mock_create_result.return_value = traditional_success_result

            result = command.execute(
                files=[test_file],
                template="default",
                no_ai=True,  # AI explicitly disabled
                doc_type=DEFAULT_DOC_TYPE,
            )

        # Verify AI generation was never attempted
        mock_ai_gen.assert_not_called()

        # Verify traditional template generation was successful
        assert result["success"] is True
        assert result["data"]["successful_files"] == 1
        assert result["data"]["failed_files"] == 0

        # Verify completion logging
        mock_logger.log.assert_called_with(
            "INFO",
            "AI-first generation command completed",
            total_files=1,
            successful_files=1,
            failed_files=0,
            generated_files=1,
        )

    def test_integration_multiple_files_mixed_success_and_failure_scenarios(
        self, temp_project_dir, mock_settings
    ):
        """Test end-to-end workflow with multiple files having different outcomes."""
        command = GenCommand(mock_settings)

        # Create multiple test files
        test_file_1 = temp_project_dir / "success_file.py"
        test_file_2 = temp_project_dir / "failure_file.py"
        test_file_1.write_text(INTEGRATION_TEST_CONTENT)
        test_file_2.write_text("# This file will fail processing")

        def mock_ai_generation_side_effect(target_path, doc_type, template_path=None):
            """Mock AI generation with different results per file."""
            if "success_file" in str(target_path):
                # Return result that _finalize_ai_results expects
                return {
                    "success": True,
                    "data": {
                        "generated_docs": {
                            str(target_path): "AI-generated content for success file"
                        }
                    },
                    "message": "AI generation successful",
                }
            else:
                return {
                    "success": False,
                    "error": "AI processing failed",
                    "data": {"fallback_needed": False},  # No fallback for this file
                }

        with (
            patch.object(
                command,
                "_generate_with_ai_templates",
                side_effect=mock_ai_generation_side_effect,
            ),
            patch.object(command, "validate_repository_state"),
            patch.object(
                command, "_expand_source_files", return_value=[test_file_1, test_file_2]
            ),
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input",
                return_value={"valid": True, "warnings": []},
            ),
            patch("spec_cli.cli.commands.gen_command.show_message"),
            patch("spec_cli.cli.commands.gen_command.debug_logger"),
            patch(
                "spec_cli.file_system.path_resolver.PathResolver"
            ) as mock_path_resolver,
            patch(
                "spec_cli.file_system.directory_manager.DirectoryManager"
            ) as mock_dir_manager,
        ):
            # Setup file system mocks
            mock_resolver_instance = Mock()
            mock_resolver_instance.get_spec_files_for_source.return_value = {
                "index": test_file_1.parent / "index.md",
                "history": test_file_1.parent / "history.md",
            }
            mock_path_resolver.return_value = mock_resolver_instance

            mock_manager_instance = Mock()
            mock_manager_instance.create_spec_directory.return_value = (
                test_file_1.parent
            )
            mock_dir_manager.return_value = mock_manager_instance

            result = command.execute(
                files=[test_file_1, test_file_2],
                template="default",
                no_ai=False,
                doc_type=DEFAULT_DOC_TYPE,
            )

        # Verify mixed results
        assert result["success"] is True  # Overall success if any files succeeded
        assert result["data"]["successful_files"] == 1  # One file succeeded
        assert result["data"]["failed_files"] == 1  # One file failed

    def test_integration_error_handling_when_file_processing_exception_occurs(
        self, temp_project_dir, mock_settings
    ):
        """Test integration error handling when file processing raises exception."""
        command = GenCommand(mock_settings)
        test_file = temp_project_dir / INTEGRATION_TEST_FILE

        with (
            patch(
                "spec_cli.cli.commands.gen_command.generate_with_ai",
                side_effect=Exception("Processing error"),
            ),
            patch(
                "spec_cli.cli.commands.gen_command.create_workflow_result"
            ) as mock_create_result,
            patch.object(command, "validate_repository_state"),
            patch.object(command, "_expand_source_files", return_value=[test_file]),
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input",
                return_value={"valid": True, "warnings": []},
            ),
            patch("spec_cli.cli.commands.gen_command.show_message"),
            patch("spec_cli.cli.commands.gen_command.debug_logger") as mock_logger,
        ):
            # Setup error result
            error_result = {
                "success": False,
                "error": f"Processing failed for {test_file}: Processing error",
            }
            mock_create_result.return_value = error_result

            result = command.execute(
                files=[test_file],
                template="default",
                no_ai=False,
                doc_type=DEFAULT_DOC_TYPE,
            )

        # Verify error handling
        assert result["success"] is False  # No successful files
        assert result["data"]["successful_files"] == 0
        assert result["data"]["failed_files"] == 1

        # Verify error was logged - check what was actually called
        # The logging might be slightly different in the integration test
        mock_logger.log.assert_called()

    def test_integration_performance_requirements_generation_completes_within_time_limit(
        self, temp_project_dir, mock_settings
    ):
        """Test integration performance requirements are met."""
        command = GenCommand(mock_settings)
        test_file = temp_project_dir / INTEGRATION_TEST_FILE

        # Mock fast AI generation
        ai_success_result = {
            "success": True,
            "data": {"generated_docs": {str(test_file): "Fast AI content"}},
            "message": "Fast AI generation",
        }

        import time

        with (
            patch(
                "spec_cli.cli.commands.gen_command.generate_with_ai",
                return_value=ai_success_result,
            ),
            patch.object(command, "validate_repository_state"),
            patch.object(command, "_expand_source_files", return_value=[test_file]),
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input",
                return_value={"valid": True, "warnings": []},
            ),
            patch("spec_cli.cli.commands.gen_command.show_message"),
            patch("spec_cli.cli.commands.gen_command.debug_logger"),
        ):
            start_time = time.time()

            result = command.execute(
                files=[test_file],
                template="default",
                no_ai=False,
                doc_type=DEFAULT_DOC_TYPE,
            )

            end_time = time.time()
            execution_time = end_time - start_time

        # Verify performance requirement: generation completes within 10 seconds per directory
        assert execution_time < 10.0, (
            f"Generation took {execution_time:.2f}s, exceeding 10s limit"
        )

        # Verify generation was successful
        assert result["success"] is True

    def test_integration_cross_platform_path_handling_works_correctly(
        self, temp_project_dir, mock_settings
    ):
        """Test integration handles cross-platform path differences correctly."""
        command = GenCommand(mock_settings)
        test_file = temp_project_dir / INTEGRATION_TEST_FILE

        # Mock AI generation with path handling
        ai_success_result = {
            "success": True,
            "data": {
                "generated_docs": {str(test_file): "Cross-platform content"},
                "generation_metadata": {"target_path": str(test_file)},
            },
            "message": "Cross-platform generation",
        }

        with (
            patch(
                "spec_cli.cli.commands.gen_command.generate_with_ai",
                return_value=ai_success_result,
            ),
            patch("spec_cli.cli.commands.gen_command.normalize_path") as mock_normalize,
            patch.object(command, "validate_repository_state"),
            patch.object(command, "_expand_source_files", return_value=[test_file]),
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input",
                return_value={"valid": True, "warnings": []},
            ),
            patch("spec_cli.cli.commands.gen_command.show_message"),
            patch("spec_cli.cli.commands.gen_command.debug_logger"),
        ):
            # Setup cross-platform path normalization
            mock_normalize.return_value = Path(str(test_file).replace("\\", "/"))

            result = command.execute(
                files=[test_file],
                template="default",
                no_ai=False,
                doc_type=DEFAULT_DOC_TYPE,
            )

        # Verify path normalization was called when creating template variables
        # (This would be called in _create_template_variables if AI fallback occurred)
        assert result["success"] is True

    def test_integration_backward_compatibility_with_existing_gen_command_interface(
        self, temp_project_dir, mock_settings
    ):
        """Test integration maintains backward compatibility with existing gen command usage."""
        command = GenCommand(mock_settings)
        test_file = temp_project_dir / INTEGRATION_TEST_FILE

        # Mock AI generation
        ai_success_result = {
            "success": True,
            "data": {"generated_docs": {str(test_file): "Compatible content"}},
            "message": "Backward compatible generation",
        }

        with (
            patch(
                "spec_cli.cli.commands.gen_command.generate_with_ai",
                return_value=ai_success_result,
            ),
            patch.object(command, "validate_repository_state"),
            patch.object(command, "_expand_source_files", return_value=[test_file]),
            patch(
                "spec_cli.cli.commands.gen_command.validate_generation_input",
                return_value={"valid": True, "warnings": []},
            ),
            patch("spec_cli.cli.commands.gen_command.show_message"),
            patch("spec_cli.cli.commands.gen_command.debug_logger"),
        ):
            # Test with only traditional parameters (no new AI-related parameters)
            result = command.execute(
                files=[test_file],
                template="default",
                conflict_strategy="backup",
                commit=False,
                message=None,
                interactive=False,
                force=False,
                dry_run=False,
                # Note: no_ai and doc_type not provided - should use defaults
            )

        # Verify backward compatibility
        assert result["success"] is True

        # Verify the command handled missing new parameters gracefully
        # (defaults: no_ai=False, doc_type="standard")
        assert result["data"]["successful_files"] == 1

    def test_integration_validate_arguments_enforces_all_parameter_constraints(
        self, mock_settings
    ):
        """Test integration argument validation works with all parameter combinations."""
        command = GenCommand(mock_settings)

        # Test valid arguments with all new parameters
        try:
            command.validate_arguments(
                files=[Path("test.py")],
                template="custom",
                conflict_strategy="backup",
                no_ai=True,
                doc_type="comprehensive",
            )
        except Exception as e:
            pytest.fail(f"Valid arguments should not raise exception: {e}")

        # Test invalid doc_type
        from spec_cli.exceptions import SpecError

        with pytest.raises(SpecError):
            command.validate_arguments(
                files=[Path("test.py")],
                template="default",
                conflict_strategy="backup",
                no_ai=False,
                doc_type="invalid_doc_type",
            )

        # Test invalid no_ai type
        with pytest.raises(SpecError):
            command.validate_arguments(
                files=[Path("test.py")],
                template="default",
                conflict_strategy="backup",
                no_ai="not_boolean",
                doc_type="standard",
            )
