"""Unit tests for cmd_gen function."""

import os
import tempfile
from unittest.mock import MagicMock, patch

from spec_cli.__main__ import COMMANDS, cmd_gen


class TestCmdGen:
    """Test the cmd_gen function."""

    def test_cmd_gen_with_no_args_shows_error(self, capsys):
        """Test that cmd_gen with no arguments shows error message."""
        cmd_gen([])

        captured = capsys.readouterr()
        assert (
            "❌ Please specify a file or directory to generate specs for"
            in captured.out
        )

    def test_cmd_gen_with_nonexistent_path_shows_error(self, capsys):
        """Test that cmd_gen with non-existent path shows error."""
        cmd_gen(["nonexistent_file.py"])

        captured = capsys.readouterr()
        assert "❌ Path not found:" in captured.out
        assert "nonexistent_file.py" in captured.out

    def test_cmd_gen_with_file_path_calls_handler(self, capsys):
        """Test that cmd_gen with valid file path calls the file handler."""
        # Import ROOT to create file in project directory
        from spec_cli.__main__ import ROOT
        
        test_file = ROOT / "test_cmd_gen.py"
        test_file.write_text("# test")

        try:
            cmd_gen(["test_cmd_gen.py"])

            captured = capsys.readouterr()
            assert "📝 Generating spec for file:" in captured.out
            assert "test_cmd_gen.py" in captured.out
        finally:
            test_file.unlink()

    def test_cmd_gen_with_directory_path_calls_handler(self, capsys):
        """Test that cmd_gen with valid directory path calls the directory handler."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cmd_gen([tmp_dir])

            captured = capsys.readouterr()
            assert "📁 Generating specs for directory:" in captured.out
            assert tmp_dir in captured.out

    def test_cmd_gen_with_dot_calls_handler(self, capsys):
        """Test that cmd_gen with '.' calls the directory handler for current directory."""
        cmd_gen(["."])

        captured = capsys.readouterr()
        assert "📁 Generating specs for directory:" in captured.out

    def test_cmd_gen_command_is_registered(self):
        """Test that the gen command is properly registered in COMMANDS."""
        assert "gen" in COMMANDS
        assert COMMANDS["gen"] == cmd_gen

    @patch("spec_cli.__main__.Path")
    def test_cmd_gen_handles_path_that_is_neither_file_nor_directory(
        self, mock_path, capsys
    ):
        """Test that cmd_gen handles paths that are neither files nor directories."""
        # Mock a path that exists but is neither file nor directory
        mock_path_instance = MagicMock()
        mock_path_instance.exists.return_value = True
        mock_path_instance.is_file.return_value = False
        mock_path_instance.is_dir.return_value = False
        mock_path_instance.__str__ = lambda self: "special_path"
        mock_path.return_value = mock_path_instance

        cmd_gen(["special_path"])

        captured = capsys.readouterr()
        assert "❌ Path is neither a file nor directory:" in captured.out
