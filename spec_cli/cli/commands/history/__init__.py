"""History and version control utilities.

This package provides utilities for displaying Git history, diffs,
and content with Rich formatting.
"""

from .content_viewer import (
    ContentViewer,
    create_content_display,
    display_file_content,
    display_spec_content,
)
from .diff_viewer import (
    DiffViewer,
    create_diff_view,
    display_file_diff,
    display_unified_diff,
)
from .formatters import (
    CommitFormatter,
    GitDiffFormatter,
    GitLogFormatter,
    format_commit_info,
    format_commit_log,
    format_diff_output,
)

__all__ = [
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
