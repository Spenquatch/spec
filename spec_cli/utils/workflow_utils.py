"""Workflow utilities for creating standardized workflow results."""

from pathlib import Path
from typing import Any

from spec_cli.file_system.path_utils import normalize_path_separators


def create_workflow_result(
    files: list[Path], success: bool, workflow_id: str | None = None
) -> dict[str, Any]:
    """Create standardized workflow result dictionary.

    Args:
        files: List of files that were processed
        success: Whether the workflow completed successfully
        workflow_id: Optional workflow identifier

    Returns:
        Dictionary containing standardized workflow result

    Example:
        >>> from pathlib import Path
        >>> files = [Path("src/main.py"), Path("src/utils.py")]
        >>> result = create_workflow_result(files, True, "batch-001")
        >>> print(result["success"])  # True
        >>> print(result["total_files"])  # 2
    """
    result: dict[str, Any] = {
        "success": success,
        "total_files": len(files),
        "successful_files": [normalize_path_separators(f) for f in files]
        if success
        else [],
        "failed_files": []
        if success
        else [normalize_path_separators(f) for f in files],
        "generated_files": {},
        "commit_info": None,
        "backup_info": None,
    }

    if workflow_id:
        result["workflow_id"] = workflow_id

    return result
