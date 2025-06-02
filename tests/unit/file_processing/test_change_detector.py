"""Tests for file change detection functionality."""

import hashlib
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from spec_cli.file_processing.change_detector import FileChangeDetector
from spec_cli.file_processing.file_cache import FileCacheEntry
from spec_cli.exceptions import SpecFileError


class TestFileChangeDetector:
    """Test FileChangeDetector class."""
    
    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = MagicMock()
        settings.spec_git_dir = Path("/tmp/test_spec")
        return settings
    
    @pytest.fixture
    def change_detector(self, mock_settings):
        """Create change detector with mocked dependencies."""
        with patch('spec_cli.file_processing.change_detector.FileCacheManager'), \
             patch('spec_cli.file_processing.change_detector.FileMetadataExtractor'), \
             patch('spec_cli.file_processing.change_detector.IgnorePatternMatcher'):
            detector = FileChangeDetector(mock_settings)
            detector.cache_manager = MagicMock()
            detector.metadata_extractor = MagicMock()
            detector.ignore_matcher = MagicMock()
            return detector
    
    def test_file_hash_calculation_md5_sha256(self, change_detector):
        """Test MD5 and SHA256 hash calculation."""
        test_content = "Hello, World!"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = Path(temp_file.name)
        
        try:
            md5_hash, sha256_hash = change_detector.calculate_file_hashes(temp_path)
            
            # Calculate expected hashes
            expected_md5 = hashlib.md5(test_content.encode()).hexdigest()
            expected_sha256 = hashlib.sha256(test_content.encode()).hexdigest()
            
            assert md5_hash == expected_md5
            assert sha256_hash == expected_sha256
            assert len(md5_hash) == 32
            assert len(sha256_hash) == 64
            
        finally:
            temp_path.unlink()
    
    def test_file_hash_calculation_large_files(self, change_detector):
        """Test hash calculation for large files (chunked reading)."""
        # Create a larger test file (10KB)
        test_content = "A" * 10240
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = Path(temp_file.name)
        
        try:
            md5_hash, sha256_hash = change_detector.calculate_file_hashes(temp_path)
            
            # Calculate expected hashes
            expected_md5 = hashlib.md5(test_content.encode()).hexdigest()
            expected_sha256 = hashlib.sha256(test_content.encode()).hexdigest()
            
            assert md5_hash == expected_md5
            assert sha256_hash == expected_sha256
            
        finally:
            temp_path.unlink()
    
    def test_file_hash_calculation_error_handling(self, change_detector):
        """Test error handling in hash calculation."""
        # Test with non-existent file
        non_existent_path = Path("/non/existent/file.txt")
        
        with pytest.raises(SpecFileError, match="Failed to calculate hashes"):
            change_detector.calculate_file_hashes(non_existent_path)
    
    def test_get_file_info(self, change_detector):
        """Test comprehensive file information extraction."""
        test_content = "print('Hello')"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = Path(temp_file.name)
        
        try:
            # Mock metadata extractor
            change_detector.metadata_extractor.extract_metadata.return_value = {
                "language": "python",
                "type": "script"
            }
            
            file_info = change_detector.get_file_info(temp_path)
            
            # Verify file info structure
            required_keys = {
                "file_path", "size", "mtime", "hash_md5", 
                "hash_sha256", "metadata", "last_checked"
            }
            assert set(file_info.keys()) == required_keys
            
            # Verify content
            assert file_info["file_path"] == str(temp_path)
            assert file_info["size"] == len(test_content.encode())
            assert file_info["metadata"]["language"] == "python"
            assert len(file_info["hash_md5"]) == 32
            assert len(file_info["hash_sha256"]) == 64
            
        finally:
            temp_path.unlink()
    
    def test_file_change_detection_stats_based(self, change_detector):
        """Test file change detection using file stats."""
        test_content = "test content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = Path(temp_file.name)
        
        try:
            file_path_str = str(temp_path)
            
            # Test 1: File not in cache (should be considered changed)
            change_detector.cache_manager.get_entry.return_value = None
            assert change_detector.has_file_changed(temp_path) is True
            
            # Test 2: File in cache but stats unchanged (should not be changed)
            stat = temp_path.stat()
            cached_entry = FileCacheEntry(
                file_path=file_path_str,
                hash_md5="dummy",
                hash_sha256="dummy",
                size=stat.st_size,
                mtime=stat.st_mtime,
                last_processed=time.time()
            )
            change_detector.cache_manager.get_entry.return_value = cached_entry
            assert change_detector.has_file_changed(temp_path) is False
            
            # Test 3: File in cache but stats changed (should be changed)
            cached_entry.mtime = stat.st_mtime - 1  # Different mtime
            assert change_detector.has_file_changed(temp_path) is True
            
        finally:
            temp_path.unlink()
    
    def test_file_change_detection_hash_based(self, change_detector):
        """Test deep hash-based change detection."""
        test_content = "initial content"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = Path(temp_file.name)
        
        try:
            file_path_str = str(temp_path)
            
            # Calculate actual hashes
            md5_hash = hashlib.md5(test_content.encode()).hexdigest()
            sha256_hash = hashlib.sha256(test_content.encode()).hexdigest()
            
            # Test 1: File not in cache (should be changed)
            change_detector.cache_manager.get_entry.return_value = None
            assert change_detector.has_file_changed_deep(temp_path) is True
            
            # Test 2: File in cache with same hashes (should not be changed)
            cached_entry = FileCacheEntry(
                file_path=file_path_str,
                hash_md5=md5_hash,
                hash_sha256=sha256_hash,
                size=len(test_content),
                mtime=time.time(),
                last_processed=time.time()
            )
            change_detector.cache_manager.get_entry.return_value = cached_entry
            assert change_detector.has_file_changed_deep(temp_path) is False
            
            # Test 3: File in cache with different hashes (should be changed)
            cached_entry.hash_md5 = "different_hash"
            assert change_detector.has_file_changed_deep(temp_path) is True
            
        finally:
            temp_path.unlink()
    
    def test_file_change_detection_new_files(self, change_detector):
        """Test change detection for new files."""
        # Test with non-existent file
        non_existent = Path("/tmp/non_existent_file.txt")
        
        # No cached entry, file doesn't exist
        change_detector.cache_manager.get_entry.return_value = None
        assert change_detector.has_file_changed(non_existent) is False
        
        # Has cached entry but file doesn't exist (deleted)
        cached_entry = FileCacheEntry(
            file_path=str(non_existent),
            hash_md5="dummy",
            hash_sha256="dummy",
            size=100,
            mtime=time.time(),
            last_processed=time.time()
        )
        change_detector.cache_manager.get_entry.return_value = cached_entry
        assert change_detector.has_file_changed(non_existent) is True
        
        # Should remove entry for deleted file
        change_detector.cache_manager.remove_entry.assert_called_with(str(non_existent))
    
    def test_file_change_detection_deleted_files(self, change_detector):
        """Test detection of deleted files."""
        # Create a temporary file path that will be "deleted"
        deleted_file_path = Path("/tmp/deleted_file.py")
        
        # Mock that file exists in cache but not on disk
        cached_entry = FileCacheEntry(
            file_path=str(deleted_file_path),
            hash_md5="hash",
            hash_sha256="longhash",
            size=100,
            mtime=time.time(),
            last_processed=time.time()
        )
        
        change_detector.cache_manager.get_entry.return_value = cached_entry
        
        # File doesn't exist but has cache entry
        result = change_detector.has_file_changed(deleted_file_path)
        assert result is True
        
        # Should remove the cache entry
        change_detector.cache_manager.remove_entry.assert_called_with(str(deleted_file_path))
    
    def test_update_file_cache(self, change_detector):
        """Test updating file cache after processing."""
        test_content = "cache update test"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = Path(temp_file.name)
        
        try:
            # Mock dependencies
            change_detector.metadata_extractor.extract_metadata.return_value = {
                "type": "test"
            }
            
            # Update cache
            cache_entry = change_detector.update_file_cache(temp_path)
            
            # Verify cache entry was created
            assert isinstance(cache_entry, FileCacheEntry)
            assert cache_entry.file_path == str(temp_path)
            assert len(cache_entry.hash_md5) == 32
            assert len(cache_entry.hash_sha256) == 64
            assert cache_entry.size > 0
            
            # Verify cache manager was called
            change_detector.cache_manager.set_entry.assert_called_once()
            
        finally:
            temp_path.unlink()
    
    def test_directory_change_detection(self, change_detector):
        """Test change detection for entire directories."""
        # Create temporary directory with test files
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "file1.py").write_text("content1")
            (temp_path / "file2.py").write_text("content2")
            (temp_path / "subdir").mkdir()
            (temp_path / "subdir" / "file3.py").write_text("content3")
            
            # Mock ignore matcher to not ignore any files
            change_detector.ignore_matcher.should_ignore.return_value = False
            
            # Mock cache manager responses
            change_detector.cache_manager.get_entry.return_value = None  # All files are new
            change_detector.cache_manager.get_all_entries.return_value = {}
            
            # Mock file change detection to return True for all files
            with patch.object(change_detector, 'has_file_changed', return_value=True):
                changes = change_detector.detect_changes_in_directory(temp_path)
            
            # Verify results structure
            assert "changed" in changes
            assert "unchanged" in changes
            assert "new" in changes
            assert "deleted" in changes
            
            # Should find new files (since cache returns None for all)
            assert len(changes["new"]) == 3  # 3 Python files
            assert len(changes["changed"]) == 0
            assert len(changes["unchanged"]) == 0
            assert len(changes["deleted"]) == 0
    
    def test_files_needing_processing_determination(self, change_detector):
        """Test determining which files need processing."""
        # Create test file paths
        file_paths = [
            Path("file1.py"),
            Path("file2.py"),
            Path("file3.py")
        ]
        
        # Test force_all=True
        result = change_detector.get_files_needing_processing(file_paths, force_all=True)
        assert result == file_paths
        
        # Test selective processing
        def mock_has_changed(path):
            return str(path).endswith("file1.py") or str(path).endswith("file3.py")
        
        with patch.object(change_detector, 'has_file_changed', side_effect=mock_has_changed):
            result = change_detector.get_files_needing_processing(file_paths, force_all=False)
        
        assert len(result) == 2
        assert Path("file1.py") in result
        assert Path("file3.py") in result
        assert Path("file2.py") not in result
    
    def test_change_detection_with_ignore_patterns(self, change_detector):
        """Test change detection respects ignore patterns."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "important.py").write_text("important")
            (temp_path / "ignored.pyc").write_text("bytecode")
            
            # Mock ignore matcher
            def mock_should_ignore(path):
                return str(path).endswith(".pyc")
            
            change_detector.ignore_matcher.should_ignore.side_effect = mock_should_ignore
            change_detector.cache_manager.get_entry.return_value = None
            change_detector.cache_manager.get_all_entries.return_value = {}
            
            with patch.object(change_detector, 'has_file_changed', return_value=True):
                changes = change_detector.detect_changes_in_directory(temp_path)
            
            # Should only find .py file, not .pyc file
            new_files = [str(f) for f in changes["new"]]
            assert any("important.py" in f for f in new_files)
            assert not any("ignored.pyc" in f for f in new_files)
    
    def test_change_summary_generation(self, change_detector):
        """Test generating change summary."""
        changes = {
            "changed": [Path("changed1.py"), Path("changed2.py")],
            "new": [Path("new1.py")],
            "unchanged": [Path("unchanged1.py"), Path("unchanged2.py"), Path("unchanged3.py")],
            "deleted": [Path("deleted1.py")]
        }
        
        summary = change_detector.get_change_summary(changes)
        
        assert summary["total_files"] == 7
        assert summary["changed_count"] == 2
        assert summary["new_count"] == 1
        assert summary["unchanged_count"] == 3
        assert summary["deleted_count"] == 1
        assert summary["change_percentage"] == (3 / 7) * 100  # (changed + new) / total
        assert summary["needs_processing"] is True
    
    def test_cache_cleanup(self, change_detector):
        """Test cache cleanup functionality."""
        # Mock current files
        with patch('pathlib.Path.cwd') as mock_cwd, \
             patch('pathlib.Path.rglob') as mock_rglob:
            
            mock_cwd.return_value = Path("/test")
            mock_file = MagicMock()
            mock_file.is_file.return_value = True
            mock_file.relative_to.return_value = Path("test.py")
            mock_rglob.return_value = [mock_file]
            
            change_detector.ignore_matcher.should_ignore.return_value = False
            change_detector.cache_manager.cleanup_stale_entries.return_value = 5
            change_detector.cache_manager.save_cache = MagicMock()
            
            removed_count = change_detector.cleanup_cache(max_age_days=30)
            
            assert removed_count == 5
            change_detector.cache_manager.cleanup_stale_entries.assert_called_once()
            change_detector.cache_manager.save_cache.assert_called_once()
    
    def test_error_handling_in_change_detection(self, change_detector):
        """Test error handling in various change detection scenarios."""
        # Test get_file_info error handling
        with patch.object(change_detector, 'calculate_file_hashes', side_effect=Exception("Hash error")):
            non_existent = Path("/tmp/error_test.py")
            with pytest.raises(SpecFileError, match="Failed to get file info"):
                change_detector.get_file_info(non_existent)
        
        # Test directory detection error handling
        with patch('pathlib.Path.rglob', side_effect=Exception("Directory error")):
            with pytest.raises(SpecFileError, match="Failed to detect changes"):
                change_detector.detect_changes_in_directory(Path("/tmp"))
    
    def test_save_cache_delegation(self, change_detector):
        """Test that save_cache delegates to cache manager."""
        change_detector.save_cache()
        change_detector.cache_manager.save_cache.assert_called_once()