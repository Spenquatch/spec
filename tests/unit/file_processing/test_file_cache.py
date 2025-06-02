"""Tests for file cache functionality."""

import json
import tempfile
import time
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch

import pytest

from spec_cli.exceptions import SpecFileError
from spec_cli.file_processing.file_cache import FileCacheEntry, FileCacheManager


class TestFileCacheEntry:
    """Test FileCacheEntry class."""

    def test_cache_entry_creation_and_serialization(self) -> None:
        """Test creating and serializing cache entries."""
        timestamp = time.time()
        metadata = {"language": "python", "type": "module"}

        entry = FileCacheEntry(
            file_path="test/file.py",
            hash_md5="abc123",
            hash_sha256="def456",
            size=1024,
            mtime=timestamp,
            last_processed=timestamp,
            metadata=metadata,
        )

        # Test basic properties
        assert entry.file_path == "test/file.py"
        assert entry.hash_md5 == "abc123"
        assert entry.hash_sha256 == "def456"
        assert entry.size == 1024
        assert entry.mtime == timestamp
        assert entry.last_processed == timestamp
        assert entry.metadata == metadata

        # Test serialization
        entry_dict = entry.to_dict()
        expected_keys = {
            "file_path",
            "hash_md5",
            "hash_sha256",
            "size",
            "mtime",
            "last_processed",
            "metadata",
        }
        assert set(entry_dict.keys()) == expected_keys
        assert entry_dict["metadata"] == metadata

        # Test deserialization
        restored_entry = FileCacheEntry.from_dict(entry_dict)
        assert restored_entry.file_path == entry.file_path
        assert restored_entry.hash_md5 == entry.hash_md5
        assert restored_entry.metadata == entry.metadata

    def test_cache_entry_is_stale(self) -> None:
        """Test stale detection logic."""
        timestamp = time.time()

        entry = FileCacheEntry(
            file_path="test.py",
            hash_md5="abc",
            hash_sha256="def",
            size=1000,
            mtime=timestamp,
            last_processed=timestamp,
        )

        # Same mtime and size - not stale
        assert not entry.is_stale(timestamp, 1000)

        # Different mtime - stale
        assert entry.is_stale(timestamp + 1, 1000)

        # Different size - stale
        assert entry.is_stale(timestamp, 1001)

        # Both different - stale
        assert entry.is_stale(timestamp + 1, 1001)

    def test_cache_entry_age_calculation(self) -> None:
        """Test age calculation in hours."""
        old_timestamp = time.time() - 3600  # 1 hour ago

        entry = FileCacheEntry(
            file_path="test.py",
            hash_md5="abc",
            hash_sha256="def",
            size=1000,
            mtime=old_timestamp,
            last_processed=old_timestamp,
        )

        age_hours = entry.age_hours()
        # Should be approximately 1 hour (allowing for test execution time)
        assert 0.9 < age_hours < 1.1


class TestFileCacheManager:
    """Test FileCacheManager class."""

    @pytest.fixture
    def temp_cache_manager(self) -> Generator[FileCacheManager, None, None]:
        """Create a cache manager with temporary cache file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock settings to use temp directory
            mock_settings = MagicMock()
            mock_settings.spec_dir = Path(temp_dir)

            manager = FileCacheManager(mock_settings)
            yield manager

    def test_cache_manager_load_save_cycle(
        self, temp_cache_manager: FileCacheManager
    ) -> None:
        """Test loading and saving cache data."""
        manager = temp_cache_manager

        # Initially empty
        assert len(manager.get_all_entries()) == 0

        # Add some entries
        entry1 = FileCacheEntry(
            file_path="file1.py",
            hash_md5="hash1",
            hash_sha256="longhash1",
            size=100,
            mtime=time.time(),
            last_processed=time.time(),
        )

        entry2 = FileCacheEntry(
            file_path="file2.py",
            hash_md5="hash2",
            hash_sha256="longhash2",
            size=200,
            mtime=time.time(),
            last_processed=time.time(),
        )

        manager.set_entry(entry1)
        manager.set_entry(entry2)

        # Save cache
        manager.save_cache(force=True)

        # Create new manager with same cache file
        new_manager = FileCacheManager(manager.settings)
        new_manager.load_cache()

        # Should have same entries
        all_entries = new_manager.get_all_entries()
        assert len(all_entries) == 2
        assert "file1.py" in all_entries
        assert "file2.py" in all_entries

        # Verify entry data
        retrieved_entry1 = new_manager.get_entry("file1.py")
        assert retrieved_entry1 is not None
        assert retrieved_entry1.hash_md5 == "hash1"
        assert retrieved_entry1.size == 100

    def test_cache_manager_entry_crud_operations(
        self, temp_cache_manager: FileCacheManager
    ) -> None:
        """Test CRUD operations on cache entries."""
        manager = temp_cache_manager

        # Create entry
        entry = FileCacheEntry(
            file_path="test.py",
            hash_md5="testhash",
            hash_sha256="longtesthash",
            size=500,
            mtime=time.time(),
            last_processed=time.time(),
        )

        # Set entry
        manager.set_entry(entry)

        # Get entry
        retrieved = manager.get_entry("test.py")
        assert retrieved is not None
        assert retrieved.file_path == "test.py"
        assert retrieved.hash_md5 == "testhash"

        # Update entry
        updated_entry = FileCacheEntry(
            file_path="test.py",
            hash_md5="updatedhash",
            hash_sha256="longupdatedhash",
            size=600,
            mtime=time.time(),
            last_processed=time.time(),
        )
        manager.set_entry(updated_entry)

        retrieved_updated = manager.get_entry("test.py")
        assert retrieved_updated is not None
        assert retrieved_updated.hash_md5 == "updatedhash"
        assert retrieved_updated.size == 600

        # Remove entry
        removed = manager.remove_entry("test.py")
        assert removed is True

        # Entry should be gone
        assert manager.get_entry("test.py") is None

        # Removing non-existent entry
        removed_again = manager.remove_entry("test.py")
        assert removed_again is False

    def test_cache_cleanup_stale_entries(
        self, temp_cache_manager: FileCacheManager
    ) -> None:
        """Test cleanup of stale cache entries."""
        manager = temp_cache_manager

        # Add some entries with different ages
        old_time = time.time() - (40 * 24 * 3600)  # 40 days ago
        recent_time = time.time() - (10 * 24 * 3600)  # 10 days ago

        old_entry = FileCacheEntry(
            file_path="old_file.py",
            hash_md5="old",
            hash_sha256="longold",
            size=100,
            mtime=old_time,
            last_processed=old_time,
        )

        recent_entry = FileCacheEntry(
            file_path="recent_file.py",
            hash_md5="recent",
            hash_sha256="longrecent",
            size=200,
            mtime=recent_time,
            last_processed=recent_time,
        )

        manager.set_entry(old_entry)
        manager.set_entry(recent_entry)

        # Cleanup with 30 day limit (old entry should be removed)
        existing_files = {"recent_file.py"}  # old_file.py doesn't exist
        removed_count = manager.cleanup_stale_entries(existing_files, max_age_days=30)

        # old_file.py should be removed for not existing, but recent_file.py should remain
        assert removed_count == 1  # Only old entry removed (not in existing_files)
        assert len(manager.get_all_entries()) == 1  # recent_file.py should remain

        # Now cleanup with shorter age limit to remove the remaining entry
        removed_count = manager.cleanup_stale_entries(
            set(), max_age_days=5
        )  # No existing files
        assert removed_count == 1  # recent_file.py removed (not in existing_files)
        assert len(manager.get_all_entries()) == 0

    def test_cache_statistics_and_validation(
        self, temp_cache_manager: FileCacheManager
    ) -> None:
        """Test cache statistics and validation."""
        manager = temp_cache_manager

        # Empty cache statistics
        stats = manager.get_cache_statistics()
        assert stats["total_entries"] == 0
        assert stats["cache_size_bytes"] == 0

        # Add entries
        timestamp = time.time()

        entry1 = FileCacheEntry(
            file_path="file1.py",
            hash_md5="a" * 32,  # Valid MD5
            hash_sha256="b" * 64,  # Valid SHA256
            size=100,
            mtime=timestamp,
            last_processed=timestamp - 3600,  # 1 hour ago
        )

        entry2 = FileCacheEntry(
            file_path="file2.py",
            hash_md5="c" * 32,
            hash_sha256="d" * 64,
            size=200,
            mtime=timestamp,
            last_processed=timestamp - 7200,  # 2 hours ago
        )

        manager.set_entry(entry1)
        manager.set_entry(entry2)

        # Check statistics
        stats = manager.get_cache_statistics()
        assert stats["total_entries"] == 2
        assert stats["oldest_entry"]["file_path"] == "file2.py"
        assert stats["newest_entry"]["file_path"] == "file1.py"
        assert 1.0 < stats["average_age_hours"] < 2.0

        # Validate cache integrity (should be valid)
        issues = manager.validate_cache_integrity()
        assert len(issues) == 0

        # Add invalid entry to test validation
        invalid_entry = FileCacheEntry(
            file_path="invalid.py",
            hash_md5="short",  # Invalid MD5 (too short)
            hash_sha256="toolong" * 20,  # Invalid SHA256 (too long)
            size=-1,  # Invalid size
            mtime=0,  # Invalid mtime
            last_processed=0,  # Invalid timestamp
        )
        manager.set_entry(invalid_entry)

        issues = manager.validate_cache_integrity()
        assert len(issues) > 0
        assert any("Invalid MD5" in issue for issue in issues)
        assert any("Invalid SHA256" in issue for issue in issues)
        assert any("Invalid file size" in issue for issue in issues)
        assert any("Invalid timestamps" in issue for issue in issues)

    def test_cache_export_functionality(
        self, temp_cache_manager: FileCacheManager
    ) -> None:
        """Test cache export functionality."""
        manager = temp_cache_manager

        # Add some entries
        entry = FileCacheEntry(
            file_path="export_test.py",
            hash_md5="export" * 5 + "ab",  # 32 chars
            hash_sha256="export" * 10 + "abcd",  # 64 chars
            size=300,
            mtime=time.time(),
            last_processed=time.time(),
        )
        manager.set_entry(entry)

        # Export cache
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        ) as export_file:
            export_path = Path(export_file.name)

        try:
            manager.export_cache(export_path)

            # Verify export file was created and contains expected data
            assert export_path.exists()

            with export_path.open("r") as f:
                export_data = json.load(f)

            assert "exported_at" in export_data
            assert "statistics" in export_data
            assert "entries" in export_data
            assert "export_test.py" in export_data["entries"]

            # Verify entry data in export
            exported_entry = export_data["entries"]["export_test.py"]
            assert exported_entry["hash_md5"] == entry.hash_md5
            assert exported_entry["size"] == entry.size

        finally:
            export_path.unlink()

    def test_cache_clear_functionality(
        self, temp_cache_manager: FileCacheManager
    ) -> None:
        """Test cache clearing."""
        manager = temp_cache_manager

        # Add entries
        entry = FileCacheEntry(
            file_path="clear_test.py",
            hash_md5="clear" * 6 + "ab",
            hash_sha256="clear" * 12 + "abcd",
            size=100,
            mtime=time.time(),
            last_processed=time.time(),
        )
        manager.set_entry(entry)

        assert len(manager.get_all_entries()) == 1

        # Clear cache
        manager.clear_cache()

        assert len(manager.get_all_entries()) == 0

    def test_cache_file_error_handling(
        self, temp_cache_manager: FileCacheManager
    ) -> None:
        """Test error handling for cache file operations."""
        manager = temp_cache_manager

        # Test save error by making cache directory read-only
        with patch("pathlib.Path.open") as mock_open:
            mock_open.side_effect = OSError("Permission denied")

            with pytest.raises(SpecFileError, match="Failed to save file cache"):
                manager.save_cache(force=True)

        # Test export error
        with patch("pathlib.Path.open") as mock_open:
            mock_open.side_effect = OSError("Export failed")

            export_path = Path("/tmp/test_export.json")
            with pytest.raises(SpecFileError, match="Failed to export cache"):
                manager.export_cache(export_path)
