"""Tests for history package initialization."""

import pytest


class TestHistoryPackageImports:
    """Test cases for history package imports."""

    def test_import_history_package(self) -> None:
        """Test that history package can be imported."""
        try:
            import spec_cli.cli.commands.history

            assert spec_cli.cli.commands.history is not None
        except ImportError as e:
            pytest.fail(f"Failed to import history package: {e}")

    def test_import_formatters(self) -> None:
        """Test importing formatters from history package."""
        try:
            from spec_cli.cli.commands.history import (
                CommitFormatter,
                GitDiffFormatter,
                GitLogFormatter,
                format_commit_info,
                format_commit_log,
                format_diff_output,
            )

            # Test that classes can be instantiated
            log_formatter = GitLogFormatter()
            diff_formatter = GitDiffFormatter()
            commit_formatter = CommitFormatter()

            assert log_formatter is not None
            assert diff_formatter is not None
            assert commit_formatter is not None

            # Test that functions exist
            assert callable(format_commit_log)
            assert callable(format_diff_output)
            assert callable(format_commit_info)

        except ImportError as e:
            pytest.fail(f"Failed to import formatters: {e}")

    def test_import_diff_viewer(self) -> None:
        """Test importing diff viewer from history package."""
        try:
            from spec_cli.cli.commands.history import (
                DiffViewer,
                create_diff_view,
                display_file_diff,
                display_unified_diff,
            )

            # Test that class can be instantiated
            diff_viewer = DiffViewer()
            assert diff_viewer is not None

            # Test that functions exist
            assert callable(create_diff_view)
            assert callable(display_file_diff)
            assert callable(display_unified_diff)

        except ImportError as e:
            pytest.fail(f"Failed to import diff viewer: {e}")

    def test_import_content_viewer(self) -> None:
        """Test importing content viewer from history package."""
        try:
            from spec_cli.cli.commands.history import (
                ContentViewer,
                create_content_display,
                display_file_content,
                display_spec_content,
            )

            # Test that class can be instantiated
            content_viewer = ContentViewer()
            assert content_viewer is not None

            # Test that functions exist
            assert callable(display_spec_content)
            assert callable(display_file_content)
            assert callable(create_content_display)

        except ImportError as e:
            pytest.fail(f"Failed to import content viewer: {e}")

    def test_all_exports(self) -> None:
        """Test that all expected exports are in __all__."""
        from spec_cli.cli.commands.history import __all__

        expected_exports = [
            "GitLogFormatter",
            "GitDiffFormatter",
            "CommitFormatter",
            "format_commit_log",
            "format_diff_output",
            "format_commit_info",
            "DiffViewer",
            "create_diff_view",
            "display_file_diff",
            "display_unified_diff",
            "ContentViewer",
            "display_spec_content",
            "display_file_content",
            "create_content_display",
        ]

        for export in expected_exports:
            assert export in __all__, f"Expected export '{export}' not found in __all__"
