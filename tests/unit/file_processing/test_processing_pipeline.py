"""Tests for file processing pipeline functionality."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spec_cli.file_processing.processing_pipeline import (
    FileProcessingPipeline,
    FileProcessingResult
)
from spec_cli.file_processing.conflict_resolver import ConflictInfo, ConflictType, ConflictResolutionStrategy
from spec_cli.file_processing.progress_events import ProcessingStage


class TestFileProcessingResult:
    """Test FileProcessingResult class."""
    
    def test_processing_result_creation_and_serialization(self):
        """Test creating and serializing processing results."""
        file_path = Path("/test/file.py")
        generated_files = {"index": Path("/specs/file/index.md"), "history": Path("/specs/file/history.md")}
        conflict_info = MagicMock()
        conflict_info.conflict_type.value = "content_modified"
        resolution_strategy = ConflictResolutionStrategy.MERGE_INTELLIGENT
        errors = ["error1", "error2"]
        warnings = ["warning1"]
        metadata = {"processing_time": 2.5}
        
        result = FileProcessingResult(
            file_path=file_path,
            success=True,
            generated_files=generated_files,
            conflict_info=conflict_info,
            resolution_strategy=resolution_strategy,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
        
        # Test properties
        assert result.file_path == file_path
        assert result.success is True
        assert result.generated_files == generated_files
        assert result.conflict_info == conflict_info
        assert result.resolution_strategy == resolution_strategy
        assert result.errors == errors
        assert result.warnings == warnings
        assert result.metadata == metadata
        
        # Test serialization
        result_dict = result.to_dict()
        expected_keys = {
            "file_path", "success", "generated_files", "has_conflict",
            "conflict_type", "resolution_strategy", "errors", "warnings", "metadata"
        }
        assert set(result_dict.keys()) == expected_keys
        assert result_dict["success"] is True
        assert result_dict["has_conflict"] is True
        assert result_dict["conflict_type"] == "content_modified"
        assert result_dict["resolution_strategy"] == "merge_intelligent"
    
    def test_processing_result_without_conflicts(self):
        """Test processing result without conflicts."""
        result = FileProcessingResult(
            file_path=Path("/test/file.py"),
            success=True
        )
        
        # Default values
        assert result.generated_files == {}
        assert result.conflict_info is None
        assert result.resolution_strategy is None
        assert result.errors == []
        assert result.warnings == []
        assert result.metadata == {}
        
        # Serialization
        result_dict = result.to_dict()
        assert result_dict["has_conflict"] is False
        assert result_dict["conflict_type"] is None
        assert result_dict["resolution_strategy"] is None


class TestFileProcessingPipeline:
    """Test FileProcessingPipeline class."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Create mock dependencies for pipeline."""
        content_generator = MagicMock()
        change_detector = MagicMock()
        conflict_resolver = MagicMock()
        progress_reporter = MagicMock()
        
        return {
            "content_generator": content_generator,
            "change_detector": change_detector,
            "conflict_resolver": conflict_resolver,
            "progress_reporter": progress_reporter
        }
    
    @pytest.fixture
    def pipeline(self, mock_dependencies):
        """Create pipeline with mock dependencies."""
        return FileProcessingPipeline(**mock_dependencies)
    
    def test_file_processing_pipeline_complete_flow(self, pipeline, mock_dependencies):
        """Test complete file processing pipeline flow."""
        file_path = Path("/test/file.py")
        custom_variables = {"author": "test"}
        conflict_strategy = ConflictResolutionStrategy.MERGE_INTELLIGENT
        
        # Mock dependencies
        change_detector = mock_dependencies["change_detector"]
        content_generator = mock_dependencies["content_generator"]
        conflict_resolver = mock_dependencies["conflict_resolver"]
        progress_reporter = mock_dependencies["progress_reporter"]
        
        # Setup mocks
        change_detector.has_file_changed.return_value = True
        change_detector.update_file_cache.return_value = MagicMock()
        
        # Mock template loading
        with patch('spec_cli.file_processing.processing_pipeline.load_template') as mock_load_template:
            mock_template = MagicMock()
            mock_load_template.return_value = mock_template
            
            # Mock content generation
            generated_files = {"index": Path("/specs/file/index.md")}
            content_generator.generate_spec_content.return_value = generated_files
            
            # Mock no conflicts
            conflict_resolver.detect_conflict.return_value = None
            
            # Process file
            result = pipeline.process_file(
                file_path=file_path,
                custom_variables=custom_variables,
                conflict_strategy=conflict_strategy,
                force_regenerate=False
            )
        
        # Verify result
        assert result.success is True
        assert result.file_path == file_path
        assert result.generated_files == generated_files
        assert len(result.errors) == 0
        
        # Verify method calls
        change_detector.has_file_changed.assert_called_once_with(file_path)
        content_generator.generate_spec_content.assert_called_once()
        change_detector.update_file_cache.assert_called_once_with(file_path)
        
        # Verify progress reporting
        assert progress_reporter.emit_stage_update.call_count >= 3  # Multiple stages
        stage_calls = [call[0][1] for call in progress_reporter.emit_stage_update.call_args_list]
        assert ProcessingStage.CHANGE_DETECTION in stage_calls
        assert ProcessingStage.CONTENT_GENERATION in stage_calls
        assert ProcessingStage.CACHE_UPDATE in stage_calls
    
    def test_pipeline_change_detection_integration(self, pipeline, mock_dependencies):
        """Test pipeline integration with change detection."""
        file_path = Path("/test/unchanged_file.py")
        change_detector = mock_dependencies["change_detector"]
        
        # Mock file as unchanged
        change_detector.has_file_changed.return_value = False
        
        # Process file without force regenerate
        result = pipeline.process_file(file_path, force_regenerate=False)
        
        # Should skip processing
        assert result.success is True
        assert "unchanged" in result.warnings[0].lower()
        
        # Should not call content generator
        mock_dependencies["content_generator"].generate_spec_content.assert_not_called()
        
        # Test force regenerate
        change_detector.reset_mock()
        result = pipeline.process_file(file_path, force_regenerate=True)
        
        # Should not check for changes when force regenerate
        change_detector.has_file_changed.assert_not_called()
    
    def test_pipeline_conflict_resolution_integration(self, pipeline, mock_dependencies):
        """Test pipeline integration with conflict resolution."""
        file_path = Path("/test/file.py")
        
        # Setup mocks
        change_detector = mock_dependencies["change_detector"]
        content_generator = mock_dependencies["content_generator"]
        conflict_resolver = mock_dependencies["conflict_resolver"]
        
        change_detector.has_file_changed.return_value = True
        
        # Mock content generation
        generated_files = {"index": Path("/specs/file/index.md")}
        content_generator.generate_spec_content.return_value = generated_files
        
        # Mock conflict detection and resolution
        conflict_info = ConflictInfo(
            conflict_type=ConflictType.CONTENT_MODIFIED,
            file_path=Path("/specs/file/index.md"),
            existing_content="old",
            new_content="new"
        )
        conflict_resolver.detect_conflict.return_value = conflict_info
        
        resolution_result = MagicMock()
        resolution_result.success = True
        resolution_result.strategy_used = ConflictResolutionStrategy.MERGE_INTELLIGENT
        resolution_result.warnings = ["merged content"]
        resolution_result.errors = []
        conflict_resolver.resolve_conflict.return_value = resolution_result
        
        # Mock template loading and file existence
        with patch('spec_cli.file_processing.processing_pipeline.load_template'), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'read_text', return_value="new content"):
            # Process file
            result = pipeline.process_file(file_path)
        
        # Verify conflict handling
        assert result.success is True
        assert result.conflict_info == conflict_info
        assert result.resolution_strategy == ConflictResolutionStrategy.MERGE_INTELLIGENT
        assert "merged content" in result.warnings
        
        # Verify conflict resolution was called
        conflict_resolver.resolve_conflict.assert_called_once_with(
            conflict_info, None, create_backup=True
        )
    
    def test_pipeline_content_generation_integration(self, pipeline, mock_dependencies):
        """Test pipeline integration with content generation."""
        file_path = Path("/test/file.py")
        custom_variables = {"author": "test", "version": "1.0"}
        
        # Setup mocks
        change_detector = mock_dependencies["change_detector"]
        content_generator = mock_dependencies["content_generator"]
        conflict_resolver = mock_dependencies["conflict_resolver"]
        
        change_detector.has_file_changed.return_value = True
        
        # Mock successful content generation
        generated_files = {
            "index": Path("/specs/file/index.md"),
            "history": Path("/specs/file/history.md")
        }
        content_generator.generate_spec_content.return_value = generated_files
        
        # Mock no conflicts
        conflict_resolver.detect_conflict.return_value = None
        
        # Mock template loading
        with patch('spec_cli.file_processing.processing_pipeline.load_template') as mock_load_template:
            mock_template = MagicMock()
            mock_load_template.return_value = mock_template
            
            # Process file
            result = pipeline.process_file(file_path, custom_variables=custom_variables)
        
        # Verify content generation call
        content_generator.generate_spec_content.assert_called_once_with(
            file_path=file_path,
            template=mock_template,
            custom_variables=custom_variables,
            backup_existing=False
        )
        
        # Verify result
        assert result.success is True
        assert result.generated_files == generated_files
    
    def test_pipeline_error_handling(self, pipeline, mock_dependencies):
        """Test pipeline error handling."""
        file_path = Path("/test/file.py")
        
        # Setup mocks
        change_detector = mock_dependencies["change_detector"]
        content_generator = mock_dependencies["content_generator"]
        
        change_detector.has_file_changed.return_value = True
        
        # Mock content generation failure
        content_generator.generate_spec_content.side_effect = Exception("Generation failed")
        
        # Mock template loading
        with patch('spec_cli.file_processing.processing_pipeline.load_template'):
            # Process file
            result = pipeline.process_file(file_path)
        
        # Should handle error gracefully
        assert result.success is False
        assert len(result.errors) > 0
        assert "Generation failed" in result.errors[0]
    
    def test_pipeline_validation_and_estimation(self, pipeline, mock_dependencies):
        """Test pipeline validation and estimation functionality."""
        # Test file validation
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write("test content")
            temp_path = Path(temp_file.name)
        
        try:
            # Valid file should have no issues
            issues = pipeline.validate_file_for_processing(temp_path)
            assert len(issues) == 0
            
        finally:
            temp_path.unlink()
        
        # Test validation of non-existent file
        non_existent = Path("/non/existent/file.py")
        issues = pipeline.validate_file_for_processing(non_existent)
        assert len(issues) > 0
        assert "does not exist" in issues[0]
        
        # Test processing estimation
        test_files = [Path(f"/test/file{i}.py") for i in range(3)]
        
        # Mock change detector for estimation
        change_detector = mock_dependencies["change_detector"]
        change_detector.has_file_changed.return_value = True
        
        estimate = pipeline.get_processing_estimate(test_files)
        
        # Should have estimation structure
        expected_keys = {
            "total_files", "processable_files", "files_needing_processing",
            "estimated_duration_seconds", "validation_issues"
        }
        assert set(estimate.keys()) == expected_keys
        assert estimate["total_files"] == 3
    
    def test_pipeline_large_file_handling(self, pipeline):
        """Test pipeline handling of large files."""
        # Create a large temporary file (over 10MB limit)
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # Write more than 10MB
            large_content = "x" * (11 * 1024 * 1024)
            temp_file.write(large_content.encode())
            temp_path = Path(temp_file.name)
        
        try:
            # Should detect size issue in validation
            issues = pipeline.validate_file_for_processing(temp_path)
            assert len(issues) > 0
            assert any("too large" in issue.lower() for issue in issues)
            
        finally:
            temp_path.unlink()
    
    def test_pipeline_with_custom_conflict_strategy(self, pipeline, mock_dependencies):
        """Test pipeline with custom conflict resolution strategy."""
        file_path = Path("/test/file.py")
        custom_strategy = ConflictResolutionStrategy.KEEP_THEIRS
        
        # Setup mocks
        change_detector = mock_dependencies["change_detector"]
        content_generator = mock_dependencies["content_generator"]
        conflict_resolver = mock_dependencies["conflict_resolver"]
        
        change_detector.has_file_changed.return_value = True
        content_generator.generate_spec_content.return_value = {"index": Path("/specs/file/index.md")}
        
        # Mock conflict
        conflict_info = ConflictInfo(
            conflict_type=ConflictType.FILE_EXISTS,
            file_path=Path("/specs/file/index.md")
        )
        conflict_resolver.detect_conflict.return_value = conflict_info
        
        resolution_result = MagicMock()
        resolution_result.success = True
        resolution_result.strategy_used = custom_strategy
        resolution_result.warnings = []
        resolution_result.errors = []
        conflict_resolver.resolve_conflict.return_value = resolution_result
        
        # Mock template loading and file existence
        with patch('spec_cli.file_processing.processing_pipeline.load_template'), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'read_text', return_value="new content"):
            # Process with custom strategy
            result = pipeline.process_file(file_path, conflict_strategy=custom_strategy)
        
        # Verify custom strategy was used
        conflict_resolver.resolve_conflict.assert_called_once_with(
            conflict_info, custom_strategy, create_backup=True
        )
        assert result.resolution_strategy == custom_strategy
    
    def test_pipeline_conflict_resolution_failure(self, pipeline, mock_dependencies):
        """Test pipeline handling of conflict resolution failures."""
        file_path = Path("/test/file.py")
        
        # Setup mocks
        change_detector = mock_dependencies["change_detector"]
        content_generator = mock_dependencies["content_generator"]
        conflict_resolver = mock_dependencies["conflict_resolver"]
        
        change_detector.has_file_changed.return_value = True
        content_generator.generate_spec_content.return_value = {"index": Path("/specs/file/index.md")}
        
        # Mock conflict with failed resolution
        conflict_info = ConflictInfo(
            conflict_type=ConflictType.PERMISSION_DENIED,
            file_path=Path("/specs/file/index.md")
        )
        conflict_resolver.detect_conflict.return_value = conflict_info
        
        resolution_result = MagicMock()
        resolution_result.success = False
        resolution_result.errors = ["Permission denied"]
        conflict_resolver.resolve_conflict.return_value = resolution_result
        
        # Mock template loading and file existence
        with patch('spec_cli.file_processing.processing_pipeline.load_template'), \
             patch.object(Path, 'exists', return_value=True), \
             patch.object(Path, 'read_text', return_value="new content"):
            # Process file
            result = pipeline.process_file(file_path)
        
        # Should fail due to conflict resolution failure
        assert result.success is False
        assert "Permission denied" in result.errors