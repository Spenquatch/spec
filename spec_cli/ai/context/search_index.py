"""Search index management for file discovery and basic search operations."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from ...utils.path_utils import resolve_project_root
from ...utils.platform_utils import get_environment_info
from ...utils.workflow_utils import create_workflow_result

logger = logging.getLogger(__name__)


class FileIndexManager:
    """Manage file-based search index without embeddings."""

    def __init__(self) -> None:
        """Initialize FileIndexManager with project root resolution."""
        self.project_root = resolve_project_root()
        self.index_path = self.project_root / ".spec" / "search_index.json"

    def build_file_index(self, file_list: list[Path]) -> dict[str, Any]:
        """Build searchable file index with metadata.

        Args:
            file_list: List of file paths to index

        Returns:
            Workflow result with indexed files data or error message

        Raises:
            ValueError: If file_list is empty
        """
        if not file_list:
            raise ValueError("file_list cannot be empty")

        try:
            logger.info(
                "Building file index",
                extra={
                    "total_files": len(file_list),
                    "index_path": str(self.index_path),
                },
            )

            index_data = {
                "files": {},
                "metadata": {
                    "created_time": datetime.now().isoformat(),
                    "total_files": len(file_list),
                    "system_info": get_environment_info(),
                },
            }

            # Process each file
            indexed_count = 0
            for file_path in file_list:
                try:
                    if not file_path.exists():
                        logger.warning(f"File does not exist, skipping: {file_path}")
                        continue

                    file_stats = file_path.stat()
                    file_content = file_path.read_text(encoding="utf-8")

                    index_data["files"][str(file_path)] = {
                        "size": file_stats.st_size,
                        "modified_time": file_stats.st_mtime,
                        "content_preview": file_content[:200],
                        "line_count": len(file_content.splitlines()),
                        "file_type": file_path.suffix,
                    }
                    indexed_count += 1

                except Exception as e:
                    # Skip files that can't be read, don't fail entire index
                    logger.warning(f"Couldn't index file {file_path}: {e}")
                    continue

            # Write index to disk
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.index_path.write_text(json.dumps(index_data, indent=2))

            logger.info(
                "File index built successfully",
                extra={
                    "indexed_files": indexed_count,
                    "skipped_files": len(file_list) - indexed_count,
                },
            )

            return create_workflow_result(
                files=file_list[:indexed_count],
                success=True,
                workflow_id="file_index_build",
            )

        except Exception as e:
            logger.error(f"File index building failed: {str(e)}")
            return create_workflow_result(
                files=[], success=False, workflow_id="file_index_build"
            )

    def index_exists(self) -> bool:
        """Check if file index exists.

        Returns:
            True if index file exists, False otherwise
        """
        return self.index_path.exists()

    def needs_rebuild(self) -> bool:
        """Check if index needs rebuilding based on file modification times.

        Returns:
            True if index needs rebuilding, False otherwise
        """
        if not self.index_exists():
            return True

        try:
            index_data = json.loads(self.index_path.read_text())
            index_time = datetime.fromisoformat(index_data["metadata"]["created_time"])

            # Check if any documentation files are newer than index
            specs_path = self.project_root / ".specs"
            if not specs_path.exists():
                return True

            for file_path in specs_path.rglob("*.md"):
                if file_path.stat().st_mtime > index_time.timestamp():
                    return True

            return False

        except Exception:
            # Rebuild if we can't determine
            return True

    def get_index_metadata(self) -> dict[str, Any] | None:
        """Get index metadata if available.

        Returns:
            Index metadata dictionary or None if index doesn't exist
        """
        if not self.index_exists():
            return None

        try:
            index_data = json.loads(self.index_path.read_text())
            metadata = index_data.get("metadata", {})
            return metadata if metadata else None
        except Exception:
            return None

    def get_indexed_files(self) -> list[str]:
        """Get list of currently indexed files.

        Returns:
            List of file paths that are currently indexed
        """
        if not self.index_exists():
            return []

        try:
            index_data = json.loads(self.index_path.read_text())
            return list(index_data.get("files", {}).keys())
        except Exception:
            return []
