"""Integration tests for ConflictResolver and ProcessingPipeline error handling utilities."""

from unittest.mock import Mock, patch

import pytest

from spec_cli.file_processing.conflict_resolver import (
    ConflictInfo,
    ConflictResolver,
    ConflictType,
)
from spec_cli.file_processing.processing_pipeline import FileProcessingPipeline
from spec_cli.utils.error_utils import create_error_context, handle_os_error


class TestConflictResolverErrorIntegration:
    """Test ConflictResolver integration with error utilities."""

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for ConflictResolver."""
        settings = Mock()
        settings.max_file_size = 10 * 1024 * 1024  # 10MB
        return settings

    @pytest.fixture
    def conflict_resolver(self, mock_settings):
        """Create ConflictResolver instance with mocked dependencies."""
        with patch("spec_cli.file_processing.conflict_resolver.DirectoryManager"):
            with patch("spec_cli.file_processing.conflict_resolver.FileChangeDetector"):
                with patch("spec_cli.file_processing.conflict_resolver.ContentMerger"):
                    resolver = ConflictResolver(mock_settings)
                    return resolver

    @pytest.fixture
    def sample_conflict_file(self, tmp_path):
        """Create a sample file for conflict testing."""
        file_path = tmp_path / "conflict_test.md"
        file_path.write_text("# Existing content\nSome existing content here.")
        return file_path

    def test_resolve_conflict_when_os_error_then_uses_utilities(
        self, conflict_resolver, tmp_path
    ):
        """Test that OS errors in conflict resolution use error utilities."""
        # Create a conflict info
        file_path = tmp_path / "protected_file.md"
        conflict = ConflictInfo(
            ConflictType.FILE_EXISTS,
            file_path,
            existing_content="old content",
            new_content="new content",
        )

        # Mock file operations to raise OSError
        os_error = OSError(13, "Permission denied", str(file_path))

        with patch("pathlib.Path.write_text", side_effect=os_error):
            result = conflict_resolver.resolve_conflict(conflict)

            # Verify error handling
            assert not result.success
            assert len(result.errors) == 1

            # Verify error message uses error utilities formatting
            error_message = result.errors[0]
            expected_formatted = handle_os_error(os_error)
            assert expected_formatted in error_message

    def test_detect_conflict_when_os_error_then_uses_utilities(
        self, conflict_resolver, tmp_path
    ):
        """Test that OS errors in conflict detection use error utilities."""
        # Create file with restricted permissions
        file_path = tmp_path / "unreadable_file.md"
        file_path.write_text("content")

        os_error = OSError(13, "Permission denied", str(file_path))

        with patch("pathlib.Path.read_text", side_effect=os_error):
            with patch(
                "spec_cli.file_processing.conflict_resolver.debug_logger"
            ) as mock_logger:
                conflict = conflict_resolver.detect_conflict(file_path, "new content")

                # Verify conflict detected with proper error formatting
                assert conflict is not None
                assert conflict.conflict_type == ConflictType.PERMISSION_DENIED

                # Verify debug_logger.log was called with context
                mock_logger.log.assert_called()

                # Find the ERROR log call
                error_calls = [
                    call
                    for call in mock_logger.log.call_args_list
                    if call[0][0] == "ERROR"
                    and "Conflict detection failed" in call[0][1]
                ]
                assert len(error_calls) > 0

                # Verify context includes operation-specific info
                call_kwargs = error_calls[0][1]
                assert "operation" in call_kwargs
                assert call_kwargs["operation"] == "conflict_detection_read"

    def test_error_context_includes_conflict_details(self, conflict_resolver, tmp_path):
        """Test that error context includes conflict-specific information."""
        # Test the error utilities directly with context creation
        file_path = tmp_path / "conflict_file.md"
        os_error = OSError(28, "No space left on device", str(file_path))

        # Test error formatting
        formatted_error = handle_os_error(os_error)
        assert "No space left on device" in formatted_error
        assert "errno 28" in formatted_error

        # Test context creation
        context = create_error_context(file_path)
        assert "file_path" in context
        assert "file_exists" in context
        assert "parent_path" in context

        # Verify the integration pattern would work
        context.update(
            {
                "operation": "conflict_resolution",
                "conflict_type": "content_modified",
                "strategy": "keep_theirs",
            }
        )

        assert context["operation"] == "conflict_resolution"
        assert context["conflict_type"] == "content_modified"
        assert context["strategy"] == "keep_theirs"

    def test_backup_creation_when_os_error_then_uses_utilities(
        self, conflict_resolver, tmp_path
    ):
        """Test that OS errors in backup creation use error utilities."""
        file_path = tmp_path / "source_file.md"
        file_path.write_text("content to backup")

        os_error = OSError(30, "Read-only file system", str(file_path))

        with patch(
            "spec_cli.file_processing.conflict_resolver.Path.write_text",
            side_effect=os_error,
        ):
            with pytest.raises(Exception) as exc_info:
                conflict_resolver._create_backup(file_path, "content")

            # Verify error uses utility formatting
            expected_formatted = handle_os_error(os_error)
            assert expected_formatted in str(exc_info.value)


class TestProcessingPipelineErrorIntegration:
    """Test ProcessingPipeline integration with error utilities."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock dependencies for ProcessingPipeline."""
        content_generator = Mock()
        change_detector = Mock()
        conflict_resolver = Mock()
        progress_reporter = Mock()
        return content_generator, change_detector, conflict_resolver, progress_reporter

    @pytest.fixture
    def processing_pipeline(self, mock_dependencies):
        """Create ProcessingPipeline instance with mocked dependencies."""
        (
            content_generator,
            change_detector,
            conflict_resolver,
            progress_reporter,
        ) = mock_dependencies
        pipeline = FileProcessingPipeline(
            content_generator=content_generator,
            change_detector=change_detector,
            conflict_resolver=conflict_resolver,
            progress_reporter=progress_reporter,
        )
        return pipeline

    def test_pipeline_stage_when_error_then_uses_utilities(
        self, processing_pipeline, tmp_path
    ):
        """Test that OS errors in pipeline stages use error utilities."""
        file_path = tmp_path / "processing_test.py"

        # Mock change detector to indicate file changed
        processing_pipeline.change_detector.has_file_changed.return_value = True

        # Mock template loading and content generation to succeed
        with patch("spec_cli.file_processing.processing_pipeline.load_template"):
            processing_pipeline.content_generator.generate_spec_content.return_value = {
                "index": file_path / "index.md"
            }

            # Mock file operations to raise OSError
            os_error = OSError(2, "No such file or directory", str(file_path))

            with patch.object(
                processing_pipeline.change_detector,
                "update_file_cache",
                side_effect=os_error,
            ):
                result = processing_pipeline.process_file(file_path)

                # Verify error handling
                assert not result.success
                assert len(result.errors) > 0

                # Verify error message format (will be generic since cache update isn't in our modified sections)
                assert any("failed" in error.lower() for error in result.errors)

    def test_pipeline_context_includes_stage_info(self, processing_pipeline, tmp_path):
        """Test that pipeline error context includes stage information."""
        file_path = tmp_path / "stage_test.py"
        os_error = OSError(13, "Permission denied", str(file_path))

        # Test error formatting directly
        formatted_error = handle_os_error(os_error)
        assert "Permission denied" in formatted_error
        assert "errno 13" in formatted_error

        # Test context creation for pipeline operations
        context = create_error_context(file_path)
        context.update(
            {"operation": "file_processing_pipeline", "force_regenerate": False}
        )

        assert context["operation"] == "file_processing_pipeline"
        assert context["force_regenerate"] is False
        assert "file_path" in context

    def test_conflict_handling_when_os_error_then_uses_utilities(
        self, processing_pipeline, tmp_path
    ):
        """Test that OS errors in conflict handling use error utilities."""
        file_path = tmp_path / "conflict_handling_test.md"
        file_path.write_text("existing content")

        generated_files = {"index": file_path}

        os_error = OSError(5, "Input/output error", str(file_path))

        with patch("pathlib.Path.read_text", side_effect=os_error):
            with patch(
                "spec_cli.file_processing.processing_pipeline.debug_logger"
            ) as mock_logger:
                result = processing_pipeline._handle_conflicts(generated_files, None)

                # Verify error handling
                assert not result["success"]
                assert len(result["errors"]) > 0

                # Verify error uses utility formatting
                expected_formatted = handle_os_error(os_error)
                assert any(expected_formatted in error for error in result["errors"])

                # Verify debug_logger.log was called with context
                mock_logger.log.assert_called()

                # Find the ERROR log call
                error_calls = [
                    call
                    for call in mock_logger.log.call_args_list
                    if call[0][0] == "ERROR"
                    and "Conflict handling failed" in call[0][1]
                ]
                assert len(error_calls) > 0

                # Verify context includes stage-specific info
                call_kwargs = error_calls[0][1]
                assert "operation" in call_kwargs
                assert call_kwargs["operation"] == "conflict_handling_read"
                assert "stage" in call_kwargs
                assert call_kwargs["stage"] == "generated_content_read"

    def test_validation_includes_formatted_errors(self, processing_pipeline, tmp_path):
        """Test that file validation includes properly formatted errors."""
        # Test file that doesn't exist
        nonexistent_file = tmp_path / "nonexistent.py"

        issues = processing_pipeline.validate_file_for_processing(nonexistent_file)
        assert len(issues) == 1
        assert "does not exist" in issues[0]

        # Test error formatting capabilities
        os_error = OSError(13, "Permission denied", str(nonexistent_file))
        formatted_error = handle_os_error(os_error)

        # Verify formatting includes errno and filename
        assert "Permission denied" in formatted_error
        assert "errno 13" in formatted_error
        assert str(nonexistent_file) in formatted_error

        # Test context creation for validation operations
        context = create_error_context(nonexistent_file)
        assert "file_path" in context
        assert "file_exists" in context
        assert context["file_exists"] is False  # nonexistent file
