"""Integration tests for BatchProcessor error handling utilities."""

import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.file_processing.batch_processor import (
    BatchFileProcessor,
    BatchProcessingOptions,
)
from spec_cli.utils.error_utils import create_error_context, handle_os_error


class TestBatchProcessorErrorIntegration:
    """Test BatchProcessor integration with error utilities."""

    @pytest.fixture
    def mock_progress_reporter(self):
        """Mock progress reporter."""
        return Mock()

    @pytest.fixture
    def mock_pipeline(self):
        """Mock processing pipeline."""
        return Mock()

    @pytest.fixture
    def batch_processor(self, mock_progress_reporter):
        """Create BatchProcessor instance with mocked dependencies."""
        with patch(
            "spec_cli.file_processing.batch_processor.progress_reporter",
            mock_progress_reporter,
        ):
            processor = BatchFileProcessor()
            return processor

    @pytest.fixture
    def sample_files(self, tmp_path):
        """Create sample files for testing."""
        files = []
        for i in range(3):
            file_path = tmp_path / f"test_file_{i}.py"
            file_path.write_text(f"# Test file {i}")
            files.append(file_path)
        return files

    def test_process_batch_when_os_error_then_uses_error_utils(
        self, batch_processor, sample_files
    ):
        """Test that OS errors in batch processing use error utilities."""
        # Mock pipeline to raise OSError
        os_error = OSError(2, "No such file or directory", "missing_file.py")

        with patch.object(
            batch_processor.pipeline, "process_file", side_effect=os_error
        ):
            result = batch_processor.process_files(sample_files[:1])

            # Verify error handling
            assert not result.success
            assert len(result.failed_files) == 1
            assert len(result.errors) == 1

            # Verify error message uses error utilities formatting
            error_message = result.errors[0]
            expected_formatted = handle_os_error(os_error)
            assert expected_formatted in error_message

    def test_auto_commit_when_os_error_then_uses_error_utils(
        self, batch_processor, sample_files
    ):
        """Test that OS errors in auto-commit use error utilities."""
        options = BatchProcessingOptions(auto_commit=True)

        # Mock successful file processing but failing auto-commit
        mock_file_result = Mock()
        mock_file_result.success = True
        mock_file_result.errors = []
        mock_file_result.warnings = []

        os_error = OSError(13, "Permission denied", "/restricted/path")

        with patch.object(
            batch_processor.pipeline, "process_file", return_value=mock_file_result
        ):
            with patch("spec_cli.git.repository.SpecGitRepository") as mock_repo_class:
                mock_repo = Mock()
                mock_repo_class.return_value = mock_repo
                # Mock SpecGitRepository constructor to raise OS error
                mock_repo_class.side_effect = os_error

                result = batch_processor.process_files(sample_files[:1], options)

                # Verify warning includes formatted error
                assert len(result.warnings) > 0
                warning_message = result.warnings[0]
                expected_formatted = handle_os_error(os_error)
                assert expected_formatted in warning_message

    def test_error_context_includes_batch_specific_info(
        self, batch_processor, sample_files
    ):
        """Test that error context includes batch-specific information."""
        os_error = OSError(2, "No such file or directory", "missing_file.py")

        with patch.object(
            batch_processor.pipeline, "process_file", side_effect=os_error
        ):
            with patch(
                "spec_cli.file_processing.batch_processor.debug_logger"
            ) as mock_logger:
                batch_processor.process_files(sample_files)

                # Verify debug_logger.log was called with context
                mock_logger.log.assert_called()

                # Find the ERROR log call
                error_calls = [
                    call
                    for call in mock_logger.log.call_args_list
                    if call[0][0] == "ERROR" and "Batch processing failed" in call[0][1]
                ]
                assert len(error_calls) > 0

                # Verify context includes batch-specific info
                call_kwargs = error_calls[0][1]
                assert "operation" in call_kwargs
                assert call_kwargs["operation"] == "batch_file_processing"
                assert "batch_size" in call_kwargs
                assert "current_index" in call_kwargs

    def test_error_messages_consistent_with_utilities(
        self, batch_processor, sample_files
    ):
        """Test that error messages are consistent with utility formatting."""
        # Test various error types
        errors_to_test = [
            OSError(2, "No such file or directory", "missing.py"),
            OSError(13, "Permission denied", "/restricted/file.py"),
            subprocess.CalledProcessError(
                1, ["git", "status"], "fatal: not a git repository"
            ),
        ]

        for error in errors_to_test:
            with patch.object(
                batch_processor.pipeline, "process_file", side_effect=error
            ):
                result = batch_processor.process_files([sample_files[0]])

                if isinstance(error, OSError):
                    # For OS errors, verify utility formatting is used
                    expected_formatted = handle_os_error(error)
                    assert any(
                        expected_formatted in err_msg for err_msg in result.errors
                    )
                else:
                    # For other errors, verify generic handling
                    assert len(result.errors) > 0

    def test_context_creation_includes_file_info(self, tmp_path):
        """Test that error context includes proper file information."""
        # Create test file
        test_file = tmp_path / "test_context.py"
        test_file.write_text("# Test file for context")

        # Test context creation
        context = create_error_context(test_file)

        # Verify required context fields
        assert "file_path" in context
        assert "file_exists" in context
        assert context["file_exists"] is True
        assert "is_file" in context
        assert context["is_file"] is True
        assert "parent_path" in context
        assert "parent_exists" in context

    def test_batch_processor_handles_nonexistent_files(self, batch_processor):
        """Test batch processor handles nonexistent files gracefully."""
        nonexistent_files = [
            Path("/nonexistent/file1.py"),
            Path("/nonexistent/file2.py"),
        ]

        result = batch_processor.process_files(nonexistent_files)

        # Should handle gracefully without crashing
        assert isinstance(result.success, bool)
        assert isinstance(result.errors, list)
        assert isinstance(result.warnings, list)
