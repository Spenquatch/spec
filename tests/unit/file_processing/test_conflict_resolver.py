"""Tests for conflict resolution functionality."""

import tempfile
from datetime import datetime
from pathlib import Path
from typing import cast
from unittest.mock import MagicMock, patch

import pytest

from spec_cli.file_processing.conflict_resolver import (
    ConflictInfo,
    ConflictResolutionResult,
    ConflictResolutionStrategy,
    ConflictResolver,
    ConflictType,
)


class TestConflictResolutionStrategy:
    """Test ConflictResolutionStrategy enum."""

    def test_strategy_enumeration(self) -> None:
        """Test all conflict resolution strategies are defined."""
        expected_strategies = {
            "keep_ours",
            "keep_theirs",
            "merge_intelligent",
            "merge_append",
            "merge_prepend",
            "skip",
            "prompt",
            "backup_and_replace",
            "overwrite",
            "fail",
        }

        actual_strategies = {strategy.value for strategy in ConflictResolutionStrategy}
        assert actual_strategies == expected_strategies


class TestConflictType:
    """Test ConflictType enum."""

    def test_conflict_type_enumeration(self) -> None:
        """Test all conflict types are defined."""
        expected_types = {
            "file_exists",
            "content_modified",
            "structure_conflict",
            "permission_denied",
            "size_limit",
        }

        actual_types = {conflict_type.value for conflict_type in ConflictType}
        assert actual_types == expected_types


class TestConflictInfo:
    """Test ConflictInfo class."""

    def test_conflict_info_creation_and_serialization(self) -> None:
        """Test creating and serializing conflict info."""
        file_path = Path("/test/file.py")
        existing_content = "original content"
        new_content = "modified content"
        metadata = {"conflicts": ["heading_level"]}

        conflict = ConflictInfo(
            conflict_type=ConflictType.CONTENT_MODIFIED,
            file_path=file_path,
            existing_content=existing_content,
            new_content=new_content,
            metadata=metadata,
        )

        # Test properties
        assert conflict.conflict_type == ConflictType.CONTENT_MODIFIED
        assert conflict.file_path == file_path
        assert conflict.existing_content == existing_content
        assert conflict.new_content == new_content
        assert conflict.metadata == metadata
        assert isinstance(conflict.detected_at, datetime)

        # Test serialization
        conflict_dict = conflict.to_dict()
        expected_keys = {
            "conflict_type",
            "file_path",
            "existing_content_length",
            "new_content_length",
            "metadata",
            "detected_at",
        }
        assert set(conflict_dict.keys()) == expected_keys
        assert conflict_dict["conflict_type"] == "content_modified"
        assert conflict_dict["file_path"] == str(file_path)
        assert conflict_dict["existing_content_length"] == len(existing_content)
        assert conflict_dict["new_content_length"] == len(new_content)


class TestConflictResolutionResult:
    """Test ConflictResolutionResult class."""

    def test_resolution_result_creation_and_serialization(self) -> None:
        """Test creating and serializing resolution results."""
        strategy = ConflictResolutionStrategy.MERGE_INTELLIGENT
        final_content = "merged content"
        backup_path = Path("/backup/file.py.backup")
        errors = ["error1", "error2"]
        warnings = ["warning1"]

        result = ConflictResolutionResult(
            success=True,
            strategy_used=strategy,
            final_content=final_content,
            backup_path=backup_path,
            errors=errors,
            warnings=warnings,
        )

        # Test properties
        assert result.success is True
        assert result.strategy_used == strategy
        assert result.final_content == final_content
        assert result.backup_path == backup_path
        assert result.errors == errors
        assert result.warnings == warnings
        assert isinstance(result.resolved_at, datetime)

        # Test serialization
        result_dict = result.to_dict()
        expected_keys = {
            "success",
            "strategy_used",
            "final_content_length",
            "backup_path",
            "errors",
            "warnings",
            "resolved_at",
        }
        assert set(result_dict.keys()) == expected_keys
        assert result_dict["success"] is True
        assert result_dict["strategy_used"] == "merge_intelligent"
        assert result_dict["final_content_length"] == len(final_content)


class TestConflictResolver:
    """Test ConflictResolver class."""

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        """Create mock settings."""
        settings = MagicMock()
        settings.max_file_size = 1024 * 1024  # 1MB
        return settings

    @pytest.fixture
    def conflict_resolver(self, mock_settings: MagicMock) -> ConflictResolver:
        """Create conflict resolver with mocked dependencies."""
        with (
            patch("spec_cli.file_processing.conflict_resolver.DirectoryManager"),
            patch("spec_cli.file_processing.conflict_resolver.FileChangeDetector"),
            patch("spec_cli.file_processing.conflict_resolver.ContentMerger"),
        ):
            resolver = ConflictResolver(mock_settings)
            # Replace attributes with properly typed mocks
            resolver.directory_manager = MagicMock()
            resolver.change_detector = MagicMock()
            resolver.content_merger = MagicMock()
            # Ensure mock methods are properly configured
            resolver.content_merger.detect_conflicts = MagicMock()
            resolver.content_merger.merge_markdown_content = MagicMock()
            return resolver

    def test_conflict_detection_various_types(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test detection of different conflict types."""
        new_content = "new file content"

        # Test 1: No conflict for new file
        with tempfile.NamedTemporaryFile(delete=True) as temp_file:
            non_existent_path = Path(temp_file.name)

        conflict = conflict_resolver.detect_conflict(non_existent_path, new_content)
        assert conflict is None

        # Test 2: Permission denied conflict
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("existing content")
            temp_path = Path(temp_file.name)

        try:
            with patch("os.access", return_value=False):
                conflict = conflict_resolver.detect_conflict(temp_path, new_content)
                assert conflict is not None
                assert conflict.conflict_type == ConflictType.PERMISSION_DENIED
                assert "No write permission" in conflict.metadata["reason"]
        finally:
            temp_path.unlink()

        # Test 3: Size limit conflict
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("existing")
            temp_path = Path(temp_file.name)

        try:
            large_content = "x" * (2 * 1024 * 1024)  # 2MB > 1MB limit
            conflict = conflict_resolver.detect_conflict(temp_path, large_content)
            assert conflict is not None
            assert conflict.conflict_type == ConflictType.SIZE_LIMIT
            assert conflict.metadata["size"] == len(large_content)
        finally:
            temp_path.unlink()

    def test_conflict_detection_content_analysis(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test conflict detection based on content analysis."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            temp_file.write("existing content")
            temp_path = Path(temp_file.name)

        try:
            new_content = "different content"

            # Mock content merger to detect high-severity conflicts
            cast(
                MagicMock, conflict_resolver.content_merger.detect_conflicts
            ).return_value = [{"severity": "high", "type": "structure_conflict"}]

            conflict = conflict_resolver.detect_conflict(temp_path, new_content)
            assert conflict is not None
            assert conflict.conflict_type == ConflictType.STRUCTURE_CONFLICT

            # Mock low-severity conflicts for regular content modification
            cast(
                MagicMock, conflict_resolver.content_merger.detect_conflicts
            ).return_value = [{"severity": "medium", "type": "content_change"}]

            conflict = conflict_resolver.detect_conflict(temp_path, new_content)
            assert conflict is not None
            assert conflict.conflict_type == ConflictType.CONTENT_MODIFIED

        finally:
            temp_path.unlink()

    def test_strategy_application_keep_ours_theirs(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test KEEP_OURS and KEEP_THEIRS strategies."""
        existing_content = "original content"
        new_content = "new content"

        conflict = ConflictInfo(
            conflict_type=ConflictType.CONTENT_MODIFIED,
            file_path=Path("/test/file.py"),
            existing_content=existing_content,
            new_content=new_content,
        )

        # Test KEEP_OURS strategy
        result = conflict_resolver._apply_strategy(
            conflict, ConflictResolutionStrategy.KEEP_OURS
        )
        assert result == existing_content

        # Test KEEP_THEIRS strategy
        result = conflict_resolver._apply_strategy(
            conflict, ConflictResolutionStrategy.KEEP_THEIRS
        )
        assert result == new_content

        # Test SKIP strategy
        result = conflict_resolver._apply_strategy(
            conflict, ConflictResolutionStrategy.SKIP
        )
        assert result is None

        # Test BACKUP_AND_REPLACE strategy
        result = conflict_resolver._apply_strategy(
            conflict, ConflictResolutionStrategy.BACKUP_AND_REPLACE
        )
        assert result == new_content

    def test_strategy_application_merge_variants(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test different merge strategies."""
        existing_content = "original content"
        new_content = "new content"
        merged_content = "intelligently merged content"

        conflict = ConflictInfo(
            conflict_type=ConflictType.CONTENT_MODIFIED,
            file_path=Path("/test/file.py"),
            existing_content=existing_content,
            new_content=new_content,
        )

        # Mock content merger responses
        cast(
            MagicMock, conflict_resolver.content_merger.merge_markdown_content
        ).return_value = merged_content

        # Test MERGE_INTELLIGENT
        result = conflict_resolver._apply_strategy(
            conflict, ConflictResolutionStrategy.MERGE_INTELLIGENT
        )
        assert result == merged_content
        cast(
            MagicMock, conflict_resolver.content_merger.merge_markdown_content
        ).assert_called_with(existing_content, new_content, "intelligent")

        # Test MERGE_APPEND
        result = conflict_resolver._apply_strategy(
            conflict, ConflictResolutionStrategy.MERGE_APPEND
        )
        assert result == merged_content
        cast(
            MagicMock, conflict_resolver.content_merger.merge_markdown_content
        ).assert_called_with(existing_content, new_content, "append")

        # Test MERGE_PREPEND
        result = conflict_resolver._apply_strategy(
            conflict, ConflictResolutionStrategy.MERGE_PREPEND
        )
        assert result == merged_content
        cast(
            MagicMock, conflict_resolver.content_merger.merge_markdown_content
        ).assert_called_with(existing_content, new_content, "prepend")

    def test_backup_creation_during_resolution(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test backup creation during conflict resolution."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            existing_content = "existing content"
            temp_file.write(existing_content)
            temp_path = Path(temp_file.name)

        try:
            _conflict = ConflictInfo(
                conflict_type=ConflictType.CONTENT_MODIFIED,
                file_path=temp_path,
                existing_content=existing_content,
                new_content="new content",
            )

            # Test backup creation
            backup_path = conflict_resolver._create_backup(temp_path, existing_content)

            # Verify backup file was created
            assert backup_path.exists()
            assert backup_path.read_text() == existing_content
            assert "backup_" in backup_path.name

            # Clean up backup
            backup_path.unlink()

        finally:
            temp_path.unlink()

    def test_multiple_conflict_resolution(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test resolving multiple conflicts."""
        conflicts = [
            ConflictInfo(
                conflict_type=ConflictType.CONTENT_MODIFIED,
                file_path=Path("/test/file1.py"),
                existing_content="content1",
                new_content="new1",
            ),
            ConflictInfo(
                conflict_type=ConflictType.FILE_EXISTS,
                file_path=Path("/test/file2.py"),
                existing_content="content2",
                new_content="new2",
            ),
        ]

        # Mock successful resolution
        successful_result = ConflictResolutionResult(
            success=True,
            strategy_used=ConflictResolutionStrategy.MERGE_INTELLIGENT,
            final_content="merged",
        )

        with patch.object(
            conflict_resolver, "resolve_conflict", return_value=successful_result
        ):
            results = conflict_resolver.resolve_multiple_conflicts(conflicts)

        assert len(results) == 2
        assert all(result.success for result in results)

    def test_strategy_recommendation_system(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test automatic strategy recommendation."""
        # Test permission denied - should recommend SKIP
        permission_conflict = ConflictInfo(
            conflict_type=ConflictType.PERMISSION_DENIED,
            file_path=Path("/test/file.py"),
        )

        strategy = conflict_resolver.recommend_strategy(permission_conflict)
        assert strategy == ConflictResolutionStrategy.SKIP

        # Test size limit - should recommend SKIP
        size_conflict = ConflictInfo(
            conflict_type=ConflictType.SIZE_LIMIT, file_path=Path("/test/file.py")
        )

        strategy = conflict_resolver.recommend_strategy(size_conflict)
        assert strategy == ConflictResolutionStrategy.SKIP

        # Test content conflict with high similarity
        content_conflict = ConflictInfo(
            conflict_type=ConflictType.CONTENT_MODIFIED,
            file_path=Path("/test/file.py"),
            existing_content="The quick brown fox jumps over the lazy dog",
            new_content="The quick brown fox leaps over the lazy dog",
        )

        # Mock no high-severity conflicts
        cast(
            MagicMock, conflict_resolver.content_merger.detect_conflicts
        ).return_value = [{"severity": "medium"}]

        strategy = conflict_resolver.recommend_strategy(content_conflict)
        assert strategy == ConflictResolutionStrategy.MERGE_INTELLIGENT

    def test_conflict_summary_generation(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test generation of conflict summaries."""
        conflicts = [
            ConflictInfo(
                conflict_type=ConflictType.CONTENT_MODIFIED,
                file_path=Path("/test/file1.py"),
                new_content="content1",
            ),
            ConflictInfo(
                conflict_type=ConflictType.CONTENT_MODIFIED,
                file_path=Path("/test/file2.py"),
                new_content="content2",
            ),
            ConflictInfo(
                conflict_type=ConflictType.PERMISSION_DENIED,
                file_path=Path("/test/file3.py"),
            ),
        ]

        # Mock strategy recommendations
        def mock_recommend(conflict: ConflictInfo) -> ConflictResolutionStrategy:
            if conflict.conflict_type == ConflictType.PERMISSION_DENIED:
                return ConflictResolutionStrategy.SKIP
            else:
                return ConflictResolutionStrategy.MERGE_INTELLIGENT

        with patch.object(
            conflict_resolver, "recommend_strategy", side_effect=mock_recommend
        ):
            summary = conflict_resolver.get_conflict_summary(conflicts)

        assert summary["total_conflicts"] == 3
        assert summary["by_type"]["content_modified"] == 2
        assert summary["by_type"]["permission_denied"] == 1
        assert summary["recommendations"]["merge_intelligent"] == 2
        assert summary["recommendations"]["skip"] == 1
        assert summary["requires_manual_review"] == 0  # None require PROMPT

    def test_strategy_validation(self, conflict_resolver: ConflictResolver) -> None:
        """Test validation of resolution strategies."""
        # Valid strategy map
        valid_strategies = {
            ConflictType.FILE_EXISTS: ConflictResolutionStrategy.MERGE_INTELLIGENT,
            ConflictType.CONTENT_MODIFIED: ConflictResolutionStrategy.MERGE_INTELLIGENT,
            ConflictType.STRUCTURE_CONFLICT: ConflictResolutionStrategy.KEEP_THEIRS,
            ConflictType.PERMISSION_DENIED: ConflictResolutionStrategy.SKIP,
            ConflictType.SIZE_LIMIT: ConflictResolutionStrategy.SKIP,
        }

        issues = conflict_resolver.validate_resolution_strategies(valid_strategies)
        assert len(issues) == 0

        # Invalid strategy map (missing types)
        incomplete_strategies = {
            ConflictType.FILE_EXISTS: ConflictResolutionStrategy.MERGE_INTELLIGENT,
        }

        issues = conflict_resolver.validate_resolution_strategies(incomplete_strategies)
        assert len(issues) > 0
        assert any("No strategy defined" in issue for issue in issues)

        # Invalid combinations
        invalid_strategies = {
            ConflictType.PERMISSION_DENIED: ConflictResolutionStrategy.MERGE_INTELLIGENT,  # Invalid
            ConflictType.SIZE_LIMIT: ConflictResolutionStrategy.MERGE_APPEND,  # Invalid
            ConflictType.FILE_EXISTS: ConflictResolutionStrategy.SKIP,  # Valid
            ConflictType.CONTENT_MODIFIED: ConflictResolutionStrategy.KEEP_OURS,  # Valid
            ConflictType.STRUCTURE_CONFLICT: ConflictResolutionStrategy.PROMPT,  # Valid
        }

        issues = conflict_resolver.validate_resolution_strategies(invalid_strategies)
        assert len(issues) >= 2  # At least 2 invalid combinations
        assert any("not suitable for permission denied" in issue for issue in issues)
        assert any("not suitable for size limit" in issue for issue in issues)

    def test_conflict_resolution_integration(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test full conflict resolution integration."""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as temp_file:
            existing_content = "# Original\nOriginal content"
            temp_file.write(existing_content)
            temp_path = Path(temp_file.name)

        try:
            new_content = "# Modified\nModified content"
            merged_content = "# Merged\nMerged content"

            # Create conflict
            conflict = ConflictInfo(
                conflict_type=ConflictType.CONTENT_MODIFIED,
                file_path=temp_path,
                existing_content=existing_content,
                new_content=new_content,
            )

            # Mock content merger
            cast(
                MagicMock, conflict_resolver.content_merger.merge_markdown_content
            ).return_value = merged_content

            # Resolve conflict
            result = conflict_resolver.resolve_conflict(
                conflict,
                ConflictResolutionStrategy.MERGE_INTELLIGENT,
                create_backup=True,
            )

            # Verify resolution
            assert result.success is True
            assert result.strategy_used == ConflictResolutionStrategy.MERGE_INTELLIGENT
            assert result.final_content == merged_content

            # Verify file was updated
            updated_content = temp_path.read_text()
            assert updated_content == merged_content

            # Verify backup was created
            assert result.backup_path is not None
            assert result.backup_path.exists()
            backup_content = result.backup_path.read_text()
            assert backup_content == existing_content

            # Verify cache was updated
            cast(
                MagicMock, conflict_resolver.change_detector.update_file_cache
            ).assert_called_once_with(temp_path)

            # Clean up backup
            result.backup_path.unlink()

        finally:
            temp_path.unlink()

    def test_error_handling_in_conflict_resolution(
        self, conflict_resolver: ConflictResolver
    ) -> None:
        """Test error handling during conflict resolution."""
        conflict = ConflictInfo(
            conflict_type=ConflictType.CONTENT_MODIFIED,
            file_path=Path("/non/existent/file.py"),
            existing_content="content",
            new_content="new content",
        )

        # Test error during resolution
        result = conflict_resolver.resolve_conflict(
            conflict, ConflictResolutionStrategy.KEEP_THEIRS
        )

        # Should handle error gracefully
        assert result.success is False
        assert len(result.errors) > 0
        assert "Failed to resolve conflict" in result.errors[0]
