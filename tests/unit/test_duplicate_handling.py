"""Unit tests for duplicate detection and handling functionality."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from spec_cli.__main__ import (
    check_existing_specs,
    create_backup,
    handle_spec_conflict,
    process_spec_conflicts,
)


class TestCheckExistingSpecs:
    """Test the check_existing_specs function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.spec_dir = self.temp_dir / "specs" / "src" / "test"
        self.spec_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_check_existing_specs_no_files_exist(self):
        """Test check when no spec files exist."""
        result = check_existing_specs(self.spec_dir)

        assert result == {"index": False, "history": False}

    def test_check_existing_specs_only_index_exists(self):
        """Test check when only index.md exists."""
        (self.spec_dir / "index.md").write_text("# Index content")

        result = check_existing_specs(self.spec_dir)

        assert result == {"index": True, "history": False}

    def test_check_existing_specs_only_history_exists(self):
        """Test check when only history.md exists."""
        (self.spec_dir / "history.md").write_text("# History content")

        result = check_existing_specs(self.spec_dir)

        assert result == {"index": False, "history": True}

    def test_check_existing_specs_both_files_exist(self):
        """Test check when both spec files exist."""
        (self.spec_dir / "index.md").write_text("# Index content")
        (self.spec_dir / "history.md").write_text("# History content")

        result = check_existing_specs(self.spec_dir)

        assert result == {"index": True, "history": True}

    @patch("spec_cli.__main__.DEBUG", True)
    def test_check_existing_specs_debug_output(self, capsys):
        """Test that debug output is produced when DEBUG is True."""
        (self.spec_dir / "index.md").write_text("content")

        check_existing_specs(self.spec_dir)

        captured = capsys.readouterr()
        assert "🔍 Debug: Checking existing specs" in captured.out
        assert "index.md: exists" in captured.out
        assert "history.md: not found" in captured.out

    @patch("spec_cli.__main__.DEBUG", False)
    def test_check_existing_specs_no_debug_output(self, capsys):
        """Test that no debug output when DEBUG is False."""
        check_existing_specs(self.spec_dir)

        captured = capsys.readouterr()
        assert "🔍 Debug:" not in captured.out


class TestCreateBackup:
    """Test the create_backup function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_create_backup_file_exists(self):
        """Test creating backup of existing file."""
        test_file = self.temp_dir / "test.md"
        test_content = "# Test content\nSome data here"
        test_file.write_text(test_content)

        with patch("spec_cli.__main__.datetime") as mock_datetime:
            mock_now = datetime(2023, 12, 1, 14, 30, 45)
            mock_datetime.now.return_value = mock_now

            backup_path = create_backup(test_file)

        # Check backup was created
        assert backup_path is not None
        assert backup_path.name == "test.20231201_143045.backup"
        assert backup_path.exists()

        # Check backup content matches original
        assert backup_path.read_text() == test_content

        # Check original file still exists
        assert test_file.exists()
        assert test_file.read_text() == test_content

    def test_create_backup_file_does_not_exist(self):
        """Test creating backup of non-existent file."""
        nonexistent_file = self.temp_dir / "nonexistent.md"

        backup_path = create_backup(nonexistent_file)

        assert backup_path is None

    def test_create_backup_preserves_file_metadata(self):
        """Test that backup preserves file metadata."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("content")

        # Get original modification time
        original_stat = test_file.stat()

        backup_path = create_backup(test_file)

        # Check that backup has same modification time
        backup_stat = backup_path.stat()
        assert backup_stat.st_mtime == original_stat.st_mtime

    @patch("spec_cli.__main__.DEBUG", True)
    def test_create_backup_debug_output(self, capsys):
        """Test that debug output is produced when DEBUG is True."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("content")

        create_backup(test_file)

        captured = capsys.readouterr()
        assert "🔍 Debug: Created backup:" in captured.out

    @patch("spec_cli.__main__.DEBUG", False)
    def test_create_backup_no_debug_output(self, capsys):
        """Test that no debug output when DEBUG is False."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("content")

        create_backup(test_file)

        captured = capsys.readouterr()
        assert "🔍 Debug:" not in captured.out

    def test_create_backup_permission_error(self):
        """Test create_backup raises OSError when backup fails."""
        test_file = self.temp_dir / "test.md"
        test_file.write_text("content")

        # Mock shutil.copy2 to raise permission error
        with patch("spec_cli.__main__.shutil.copy2") as mock_copy:
            mock_copy.side_effect = OSError("Permission denied")

            with pytest.raises(OSError, match="Failed to create backup"):
                create_backup(test_file)


class TestHandleSpecConflict:
    """Test the handle_spec_conflict function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.spec_dir = self.temp_dir / "specs" / "src" / "test"
        self.spec_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_handle_spec_conflict_no_conflicts(self):
        """Test handle when no conflicts exist."""
        existing_specs = {"index": False, "history": False}

        result = handle_spec_conflict(self.spec_dir, existing_specs)

        assert result == "proceed"

    def test_handle_spec_conflict_force_mode(self):
        """Test handle with force mode enabled."""
        existing_specs = {"index": True, "history": True}

        result = handle_spec_conflict(self.spec_dir, existing_specs, force=True)

        assert result == "overwrite"

    @patch("spec_cli.__main__.DEBUG", True)
    def test_handle_spec_conflict_force_mode_debug(self, capsys):
        """Test force mode produces debug output."""
        existing_specs = {"index": True, "history": False}

        handle_spec_conflict(self.spec_dir, existing_specs, force=True)

        captured = capsys.readouterr()
        assert (
            "🔍 Debug: Force mode - overwriting existing files: ['index']"
            in captured.out
        )

    @patch("builtins.input", return_value="o")
    def test_handle_spec_conflict_user_chooses_overwrite(self, mock_input, capsys):
        """Test user choosing to overwrite."""
        existing_specs = {"index": True, "history": False}
        (self.spec_dir / "index.md").write_text("existing content")

        result = handle_spec_conflict(self.spec_dir, existing_specs)

        assert result == "overwrite"
        captured = capsys.readouterr()
        assert "⚠️  Existing spec files found" in captured.out
        assert "📄 index.md" in captured.out

    @patch("builtins.input", return_value="b")
    def test_handle_spec_conflict_user_chooses_backup(self, mock_input):
        """Test user choosing to backup."""
        existing_specs = {"index": True, "history": True}

        result = handle_spec_conflict(self.spec_dir, existing_specs)

        assert result == "backup"

    @patch("builtins.input", return_value="s")
    def test_handle_spec_conflict_user_chooses_skip(self, mock_input):
        """Test user choosing to skip."""
        existing_specs = {"index": False, "history": True}

        result = handle_spec_conflict(self.spec_dir, existing_specs)

        assert result == "skip"

    @patch("builtins.input", return_value="q")
    def test_handle_spec_conflict_user_chooses_quit(self, mock_input):
        """Test user choosing to quit."""
        existing_specs = {"index": True, "history": True}

        result = handle_spec_conflict(self.spec_dir, existing_specs)

        assert result == "abort"

    @patch("builtins.input", side_effect=["invalid", "x", "o"])
    def test_handle_spec_conflict_invalid_then_valid_choice(self, mock_input, capsys):
        """Test handling invalid input followed by valid choice."""
        existing_specs = {"index": True, "history": False}

        result = handle_spec_conflict(self.spec_dir, existing_specs)

        assert result == "overwrite"
        captured = capsys.readouterr()
        assert "Invalid choice" in captured.out

    @patch("builtins.input", return_value="overwrite")
    def test_handle_spec_conflict_accepts_full_words(self, mock_input):
        """Test that full word choices are accepted."""
        existing_specs = {"index": True, "history": False}

        result = handle_spec_conflict(self.spec_dir, existing_specs)

        assert result == "overwrite"

    @patch("builtins.input", side_effect=KeyboardInterrupt())
    def test_handle_spec_conflict_keyboard_interrupt(self, mock_input, capsys):
        """Test handling KeyboardInterrupt."""
        existing_specs = {"index": True, "history": False}

        with pytest.raises(KeyboardInterrupt, match="User cancelled operation"):
            handle_spec_conflict(self.spec_dir, existing_specs)

        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.out

    @patch("builtins.input", side_effect=EOFError())
    def test_handle_spec_conflict_eof_error(self, mock_input, capsys):
        """Test handling EOFError."""
        existing_specs = {"index": True, "history": False}

        with pytest.raises(KeyboardInterrupt, match="User cancelled operation"):
            handle_spec_conflict(self.spec_dir, existing_specs)

        captured = capsys.readouterr()
        assert "Operation cancelled by user" in captured.out

    def test_handle_spec_conflict_shows_file_info(self, capsys):
        """Test that file information is displayed."""
        existing_specs = {"index": True, "history": True}

        # Create files with specific content
        index_file = self.spec_dir / "index.md"
        history_file = self.spec_dir / "history.md"
        index_file.write_text("Index content here")
        history_file.write_text("History content")

        with patch("builtins.input", return_value="q"):
            handle_spec_conflict(self.spec_dir, existing_specs)

        captured = capsys.readouterr()
        assert "📄 index.md (18 bytes" in captured.out
        assert "📄 history.md (15 bytes" in captured.out
        assert "modified" in captured.out


class TestProcessSpecConflicts:
    """Test the process_spec_conflicts function."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.spec_dir = self.temp_dir / "specs" / "src" / "test"
        self.spec_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil

        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def test_process_spec_conflicts_abort(self, capsys):
        """Test processing abort action."""
        with pytest.raises(KeyboardInterrupt, match="User aborted operation"):
            process_spec_conflicts(self.spec_dir, "abort")

        captured = capsys.readouterr()
        assert "❌ Operation aborted by user" in captured.out

    def test_process_spec_conflicts_skip(self, capsys):
        """Test processing skip action."""
        result = process_spec_conflicts(self.spec_dir, "skip")

        assert result is False
        captured = capsys.readouterr()
        assert "⏭️  Skipping spec generation for src" in captured.out

    def test_process_spec_conflicts_overwrite(self, capsys):
        """Test processing overwrite action."""
        result = process_spec_conflicts(self.spec_dir, "overwrite")

        assert result is True
        captured = capsys.readouterr()
        assert "🔄 Overwriting existing spec files" in captured.out

    def test_process_spec_conflicts_backup_no_existing_files(self, capsys):
        """Test processing backup action when no files exist."""
        result = process_spec_conflicts(self.spec_dir, "backup")

        assert result is True
        captured = capsys.readouterr()
        assert "💾 Creating backups of existing files" in captured.out

    def test_process_spec_conflicts_backup_with_existing_files(self, capsys):
        """Test processing backup action with existing files."""
        # Create existing files
        (self.spec_dir / "index.md").write_text("index content")
        (self.spec_dir / "history.md").write_text("history content")

        with patch("spec_cli.__main__.datetime") as mock_datetime:
            mock_now = datetime(2023, 12, 1, 14, 30, 45)
            mock_datetime.now.return_value = mock_now

            result = process_spec_conflicts(self.spec_dir, "backup")

        assert result is True
        captured = capsys.readouterr()
        assert "💾 Creating backups of existing files" in captured.out
        assert "✅ Backups created:" in captured.out
        assert "📦 " in captured.out

        # Check backups were actually created
        assert (self.spec_dir / "index.20231201_143045.backup").exists()
        assert (self.spec_dir / "history.20231201_143045.backup").exists()

    def test_process_spec_conflicts_backup_failure(self):
        """Test processing backup action when backup creation fails."""
        # Create existing file
        (self.spec_dir / "index.md").write_text("content")

        # Mock create_backup to raise an error
        with patch("spec_cli.__main__.create_backup") as mock_backup:
            mock_backup.side_effect = OSError("Backup failed")

            with pytest.raises(OSError, match="Backup failed"):
                process_spec_conflicts(self.spec_dir, "backup")

    def test_process_spec_conflicts_unknown_action(self):
        """Test processing unknown action (should default to proceed)."""
        result = process_spec_conflicts(self.spec_dir, "unknown_action")

        assert result is True

    def test_process_spec_conflicts_proceed_action(self):
        """Test processing proceed action."""
        result = process_spec_conflicts(self.spec_dir, "proceed")

        assert result is True
