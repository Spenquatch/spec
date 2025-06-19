"""Unit tests for Slice 4.1a: Search Index & File Discovery."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.ai.context.file_discovery import DocumentationDiscovery
from spec_cli.ai.context.search_index import FileIndexManager

# Test constants to avoid magic numbers
DEFAULT_MAX_FILES = 1000
TEST_FILE_COUNT = 5
SAMPLE_CONTENT_LENGTH = 200
INDEX_CONTENT_PREVIEW_LENGTH = 200
METADATA_CONTENT_PREVIEW_LENGTH = 300
TEST_CONTENT_SIZE = 150


class TestFileIndexManager:
    """Test cases for FileIndexManager class."""

    def test_init_creates_manager_with_project_root(self):
        """Test FileIndexManager initialization sets project root correctly."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = Path("/test/project")
            manager = FileIndexManager()

            assert manager.project_root == Path("/test/project")
            assert manager.index_path == Path("/test/project/.spec/search_index.json")

    def test_build_file_index_when_empty_list_then_raises_value_error(self):
        """Test build_file_index raises ValueError with empty file list."""
        manager = FileIndexManager()

        with pytest.raises(ValueError, match="file_list cannot be empty"):
            manager.build_file_index([])

    def test_build_file_index_when_valid_files_then_creates_index(self, tmp_path):
        """Test build_file_index creates proper index with valid files."""
        # Create test files
        test_files = []
        for i in range(TEST_FILE_COUNT):
            test_file = tmp_path / f"test_{i}.md"
            test_file.write_text(f"Content for file {i}")
            test_files.append(test_file)

        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            result = manager.build_file_index(test_files)

            assert result["success"] is True
            assert result["workflow_id"] == "file_index_build"
            assert result["total_files"] == TEST_FILE_COUNT
            assert manager.index_path.exists()

    def test_build_file_index_when_nonexistent_file_then_skips_gracefully(
        self, tmp_path
    ):
        """Test build_file_index skips nonexistent files without failing."""
        # Create one real file and one fake path
        real_file = tmp_path / "real.md"
        real_file.write_text("Real content")
        fake_file = tmp_path / "fake.md"  # Don't create this file

        test_files = [real_file, fake_file]

        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            result = manager.build_file_index(test_files)

            # Should still succeed, just with fewer files indexed
            assert result["success"] is True

    def test_build_file_index_when_permission_error_then_handles_gracefully(
        self, tmp_path
    ):
        """Test build_file_index handles permission errors gracefully."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Test content")

        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            # Mock file operations to raise permission error
            with patch.object(
                Path, "read_text", side_effect=PermissionError("Access denied")
            ):
                result = manager.build_file_index([test_file])

                # Should still complete, just with warnings logged
                assert result["success"] is True

    def test_build_file_index_creates_proper_metadata(self, tmp_path):
        """Test build_file_index creates comprehensive metadata."""
        test_file = tmp_path / "test.md"
        test_file.write_text("Test content with multiple\nlines")

        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            manager.build_file_index([test_file])

            # Read the created index
            index_data = json.loads(manager.index_path.read_text())

            assert "files" in index_data
            assert "metadata" in index_data
            assert str(test_file) in index_data["files"]

            file_entry = index_data["files"][str(test_file)]
            assert "size" in file_entry
            assert "modified_time" in file_entry
            assert "content_preview" in file_entry
            assert "line_count" in file_entry
            assert "file_type" in file_entry
            assert file_entry["line_count"] == 2

    def test_index_exists_when_file_present_then_returns_true(self, tmp_path):
        """Test index_exists returns True when index file exists."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            # Create the index file
            manager.index_path.parent.mkdir(parents=True, exist_ok=True)
            manager.index_path.write_text("{}")

            assert manager.index_exists() is True

    def test_index_exists_when_file_missing_then_returns_false(self, tmp_path):
        """Test index_exists returns False when index file missing."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            assert manager.index_exists() is False

    def test_needs_rebuild_when_no_index_then_returns_true(self, tmp_path):
        """Test needs_rebuild returns True when no index exists."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            assert manager.needs_rebuild() is True

    def test_needs_rebuild_when_newer_files_exist_then_returns_true(self, tmp_path):
        """Test needs_rebuild returns True when documentation files are newer than index."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            # Create old index
            old_time = datetime.now().replace(year=2020)
            index_data = {"metadata": {"created_time": old_time.isoformat()}}
            manager.index_path.parent.mkdir(parents=True, exist_ok=True)
            manager.index_path.write_text(json.dumps(index_data))

            # Create newer documentation file
            specs_dir = tmp_path / ".specs"
            specs_dir.mkdir()
            new_file = specs_dir / "new.md"
            new_file.write_text("New content")

            assert manager.needs_rebuild() is True

    def test_needs_rebuild_when_index_newer_then_returns_false(self, tmp_path):
        """Test needs_rebuild returns False when index is newer than all files."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            # Create specs directory with old file
            specs_dir = tmp_path / ".specs"
            specs_dir.mkdir()
            old_file = specs_dir / "old.md"
            old_file.write_text("Old content")

            # Create newer index
            future_time = datetime.now().replace(year=2030)
            index_data = {"metadata": {"created_time": future_time.isoformat()}}
            manager.index_path.parent.mkdir(parents=True, exist_ok=True)
            manager.index_path.write_text(json.dumps(index_data))

            assert manager.needs_rebuild() is False

    def test_get_index_metadata_when_index_exists_then_returns_metadata(self, tmp_path):
        """Test get_index_metadata returns metadata when index exists."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            test_metadata = {
                "created_time": "2023-01-01T00:00:00",
                "test_key": "test_value",
            }
            index_data = {"metadata": test_metadata}

            manager.index_path.parent.mkdir(parents=True, exist_ok=True)
            manager.index_path.write_text(json.dumps(index_data))

            result = manager.get_index_metadata()
            assert result == test_metadata

    def test_get_index_metadata_when_no_index_then_returns_none(self, tmp_path):
        """Test get_index_metadata returns None when index doesn't exist."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            result = manager.get_index_metadata()
            assert result is None

    def test_get_indexed_files_when_index_exists_then_returns_file_list(self, tmp_path):
        """Test get_indexed_files returns list of indexed files."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            test_files = {"/path/to/file1.md": {}, "/path/to/file2.md": {}}
            index_data = {"files": test_files}

            manager.index_path.parent.mkdir(parents=True, exist_ok=True)
            manager.index_path.write_text(json.dumps(index_data))

            result = manager.get_indexed_files()
            assert set(result) == set(test_files.keys())

    def test_get_indexed_files_when_no_index_then_returns_empty_list(self, tmp_path):
        """Test get_indexed_files returns empty list when no index exists."""
        with patch(
            "spec_cli.ai.context.search_index.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            manager = FileIndexManager()

            result = manager.get_indexed_files()
            assert result == []


class TestDocumentationDiscovery:
    """Test cases for DocumentationDiscovery class."""

    def test_init_creates_discovery_with_project_root(self):
        """Test DocumentationDiscovery initialization sets project root correctly."""
        with patch(
            "spec_cli.ai.context.file_discovery.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = Path("/test/project")
            discovery = DocumentationDiscovery()

            assert discovery.project_root == Path("/test/project")

    def test_discover_documentation_when_invalid_max_files_then_raises_value_error(
        self,
    ):
        """Test discover_documentation raises ValueError with invalid max_files."""
        discovery = DocumentationDiscovery()

        with pytest.raises(ValueError, match="max_files must be at least 1"):
            discovery.discover_documentation(max_files=0)

    def test_discover_documentation_when_no_specs_directory_then_returns_failure(
        self, tmp_path
    ):
        """Test discover_documentation returns failure when .specs directory missing."""
        with patch(
            "spec_cli.ai.context.file_discovery.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            discovery = DocumentationDiscovery()

            result = discovery.discover_documentation()

            assert result["success"] is False
            assert result["workflow_id"] == "documentation_discovery"
            assert result["total_files"] == 0

    def test_discover_documentation_when_valid_files_then_returns_success(
        self, tmp_path
    ):
        """Test discover_documentation finds and returns valid documentation files."""
        # Create .specs directory with test files
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()

        test_files = []
        for i in range(TEST_FILE_COUNT):
            test_file = specs_dir / f"doc_{i}.md"
            test_file.write_text(f"Documentation content {i}")
            test_files.append(test_file)

        with patch(
            "spec_cli.ai.context.file_discovery.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            discovery = DocumentationDiscovery()

            result = discovery.discover_documentation()

            assert result["success"] is True
            assert result["workflow_id"] == "documentation_discovery"
            assert result["total_files"] == TEST_FILE_COUNT

    def test_discover_documentation_when_max_files_exceeded_then_limits_results(
        self, tmp_path
    ):
        """Test discover_documentation respects max_files limit."""
        # Create .specs directory with more files than limit
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()

        max_limit = 3
        for i in range(TEST_FILE_COUNT):  # Create 5 files
            test_file = specs_dir / f"doc_{i}.md"
            test_file.write_text(f"Documentation content {i}")

        with patch(
            "spec_cli.ai.context.file_discovery.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            discovery = DocumentationDiscovery()

            result = discovery.discover_documentation(max_files=max_limit)

            assert result["success"] is True
            assert result["total_files"] == max_limit

    def test_discover_documentation_when_custom_patterns_then_uses_patterns(
        self, tmp_path
    ):
        """Test discover_documentation uses custom file patterns."""
        # Create .specs directory with different file types
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()

        # Create files with different extensions
        (specs_dir / "doc.md").write_text("Markdown content")
        (specs_dir / "doc.txt").write_text("Text content")
        (specs_dir / "doc.rst").write_text("RestructuredText content")

        with patch(
            "spec_cli.ai.context.file_discovery.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            discovery = DocumentationDiscovery()

            # Only look for .rst files
            result = discovery.discover_documentation(file_patterns=["*.rst"])

            assert result["success"] is True
            assert result["total_files"] == 1

    def test_discover_documentation_when_no_matching_files_then_returns_failure(
        self, tmp_path
    ):
        """Test discover_documentation returns failure when no files match patterns."""
        # Create .specs directory with non-matching files
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        (specs_dir / "doc.pdf").write_text("PDF content")

        with patch(
            "spec_cli.ai.context.file_discovery.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            discovery = DocumentationDiscovery()

            result = discovery.discover_documentation()

            assert result["success"] is False
            assert result["total_files"] == 0

    def test_get_file_metadata_when_file_exists_then_returns_complete_metadata(
        self, tmp_path
    ):
        """Test get_file_metadata returns comprehensive metadata for existing file."""
        with patch(
            "spec_cli.ai.context.file_discovery.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            discovery = DocumentationDiscovery()

            test_file = tmp_path / "test.md"
            test_content = "Line 1\nLine 2\nLine 3"
            test_file.write_text(test_content)

            metadata = discovery.get_file_metadata(test_file)

            assert metadata["file_path"] == str(test_file)
            assert metadata["line_count"] == 3
            assert metadata["character_count"] == len(test_content)
            assert metadata["file_extension"] == ".md"
            assert metadata["file_name"] == "test.md"
            assert metadata["is_empty"] is False
            assert "size_bytes" in metadata
            assert "modified_time" in metadata

    def test_get_file_metadata_when_file_missing_then_raises_value_error(
        self, tmp_path
    ):
        """Test get_file_metadata raises ValueError for nonexistent file."""
        discovery = DocumentationDiscovery()
        nonexistent_file = tmp_path / "missing.md"

        with pytest.raises(ValueError, match="File does not exist"):
            discovery.get_file_metadata(nonexistent_file)

    def test_get_file_metadata_when_read_error_then_returns_error_metadata(
        self, tmp_path
    ):
        """Test get_file_metadata handles read errors gracefully."""
        with patch(
            "spec_cli.ai.context.file_discovery.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            discovery = DocumentationDiscovery()

            test_file = tmp_path / "test.md"
            test_file.write_text("Test content")

            # Mock read_text to raise an error
            with patch.object(
                Path, "read_text", side_effect=PermissionError("Access denied")
            ):
                metadata = discovery.get_file_metadata(test_file)

                assert "error" in metadata
                assert metadata["metadata_extraction_failed"] is True

    def test_validate_discovered_files_when_all_valid_then_returns_valid_list(
        self, tmp_path
    ):
        """Test validate_discovered_files returns all files when valid."""
        test_files = []
        for i in range(3):
            test_file = tmp_path / f"valid_{i}.md"
            test_file.write_text(f"Valid content {i}")
            test_files.append(test_file)

        discovery = DocumentationDiscovery()
        result = discovery.validate_discovered_files(test_files)

        assert result["total_valid"] == 3
        assert result["total_invalid"] == 0
        assert len(result["validation_errors"]) == 0

    def test_validate_discovered_files_when_mixed_validity_then_filters_appropriately(
        self, tmp_path
    ):
        """Test validate_discovered_files properly filters mixed valid/invalid files."""
        # Create one valid file
        valid_file = tmp_path / "valid.md"
        valid_file.write_text("Valid content")

        # Create reference to nonexistent file
        invalid_file = tmp_path / "missing.md"

        test_files = [valid_file, invalid_file]
        discovery = DocumentationDiscovery()
        result = discovery.validate_discovered_files(test_files)

        assert result["total_valid"] == 1
        assert result["total_invalid"] == 1
        assert len(result["validation_errors"]) == 1

    def test_get_discovery_summary_when_empty_list_then_returns_empty_summary(self):
        """Test get_discovery_summary handles empty file list."""
        discovery = DocumentationDiscovery()
        summary = discovery.get_discovery_summary([])

        assert summary["total_files"] == 0
        assert summary["file_types"] == {}
        assert summary["total_size_bytes"] == 0
        assert "discovery_time" in summary

    def test_get_discovery_summary_when_files_present_then_returns_complete_summary(
        self, tmp_path
    ):
        """Test get_discovery_summary provides comprehensive statistics."""
        with patch(
            "spec_cli.ai.context.file_discovery.resolve_project_root"
        ) as mock_resolve:
            mock_resolve.return_value = tmp_path
            discovery = DocumentationDiscovery()

            # Create files with different extensions
            test_files = []
            extensions = [".md", ".md", ".txt"]
            for i, ext in enumerate(extensions):
                test_file = tmp_path / f"file_{i}{ext}"
                test_file.write_text("A" * TEST_CONTENT_SIZE)  # Fixed size content
                test_files.append(test_file)

            summary = discovery.get_discovery_summary(test_files)

            assert summary["total_files"] == 3
            assert summary["file_types"][".md"] == 2
            assert summary["file_types"][".txt"] == 1
            assert summary["total_size_bytes"] == TEST_CONTENT_SIZE * 3
            assert "discovery_time" in summary
            assert summary["project_root"] == str(tmp_path)
