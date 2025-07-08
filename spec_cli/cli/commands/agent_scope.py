"""Agent scope command implementation."""

from pathlib import Path
from typing import Any

import click

from ...core.context import SpecContext
from ...logging.debug import debug_logger
from ...utils.path_utils import resolve_project_root, safe_relative_to
from ...utils.platform_utils import get_environment_info
from ..decorators import context_injection


@click.command()
@click.option(
    "--query", "-q", required=True, help="Search query to find relevant code context"
)
@click.option(
    "--context-window",
    "-c",
    default=8000,
    type=int,
    help="Maximum context window size in tokens (1-32000)",
)
@click.option(
    "--exclude", "-e", multiple=True, help="Patterns to exclude from file discovery"
)
@context_injection
def agent_scope_command(
    context: SpecContext,
    query: str,
    context_window: int,
    exclude: tuple[str, ...],
) -> None:
    """Extract and export relevant codebase context for AI agents.

    Discovers and validates files based on query and exclusion patterns,
    preparing context for AI agent consumption.

    Args:
        context: SpecContext providing console and settings access
        query: Search query for relevant context
        context_window: Token limit for context window
        exclude: File patterns to exclude from discovery
    """
    try:
        agent_scope = AgentScopeCommand()
        result = agent_scope.execute(
            query=query, context_window=context_window, exclude=list(exclude)
        )

        if result["success"]:
            context.console.print_status(f"✓ {result['message']}", "success")
            if context.settings.verbose and result.get("data"):
                metadata = result["data"].get("project_metadata", {})
                context.console.print_status(
                    f"  Project root: {metadata.get('project_root', 'Unknown')}", "info"
                )
                context.console.print_status(
                    f"  Files discovered: {metadata.get('total_files_discovered', 0)}",
                    "info",
                )
        else:
            context.console.print_status(f"✗ {result['error']}", "error")
            raise click.ClickException(result["error"])

    except Exception as e:
        debug_logger.log("ERROR", f"Agent scope command failed: {e}")
        raise click.ClickException(f"Agent scope command failed: {e}") from e


class AgentScopeCommand:
    """Extract and export relevant codebase context for AI agents."""

    def execute(
        self, query: str, context_window: int = 8000, exclude: list[str] | None = None
    ) -> dict[str, Any]:
        """Execute agent scope command with validation and file discovery.

        Args:
            query: Search query for relevant context
            context_window: Token limit for context window
            exclude: File patterns to exclude from discovery

        Returns:
            Dictionary with validation and discovery results
        """
        try:
            # Validate query (decision point 1)
            if not query or not query.strip():
                return {"success": False, "error": "Query cannot be empty"}

            # Validate context window (decision point 2)
            if context_window <= 0 or context_window > 32000:
                return {
                    "success": False,
                    "error": "Context window must be between 1 and 32000 tokens",
                }

            # Resolve project root (decision point 3 + try/except)
            project_root = resolve_project_root()
            if not project_root.exists():
                return {
                    "success": False,
                    "error": f"Project root not found: {project_root}",
                }

            # Discover files with exclusions (decision point 4)
            file_list = self._discover_files(project_root, exclude or [])
            if not file_list:
                return {"success": False, "error": "No relevant files found in project"}

            # Prepare validated parameters for context extraction
            validated_params = {
                "query": query.strip(),
                "context_window": context_window,
                "exclude_patterns": exclude or [],
                "project_root": project_root,
            }

            project_metadata = {
                "project_root": str(project_root),
                "total_files_discovered": len(file_list),
                "environment": get_environment_info(),
            }

            debug_logger.log(
                "INFO",
                "Agent scope command completed successfully",
                query=query.strip(),
                context_window=context_window,
                files_discovered=len(file_list),
                project_root=str(project_root),
            )

            return {
                "success": True,
                "data": {
                    "validated_params": validated_params,
                    "file_list": file_list,
                    "project_metadata": project_metadata,
                },
                "message": f"Discovered {len(file_list)} files for query '{query}'",
            }

        except Exception as e:  # try/except block (decision point 5)
            debug_logger.log(
                "ERROR",
                "Agent scope command failed with exception",
                error=str(e),
                query=query if query else "None",
                context_window=context_window,
            )
            return {"success": False, "error": f"Agent scope command failed: {str(e)}"}

    def _discover_files(
        self, project_root: Path, exclude_patterns: list[str]
    ) -> list[Path]:
        """Discover relevant files using path helpers.

        Args:
            project_root: Root directory to search from
            exclude_patterns: Patterns to exclude from discovery

        Returns:
            List of discovered file paths
        """
        discovered_files = []

        # Default exclude patterns for common non-source files
        default_excludes: set[str] = {
            "*.pyc",
            "*.pyo",
            "*.pyd",
            "__pycache__",
            ".git",
            ".spec",
            ".venv",
            "venv",
            "node_modules",
            ".pytest_cache",
            ".mypy_cache",
            "*.log",
            "*.tmp",
            ".DS_Store",
            "*.egg-info",
        }

        # Combine user patterns with defaults
        all_excludes: set[str] = set(exclude_patterns) | default_excludes

        try:
            # Simple file discovery - walk through project files
            for file_path in project_root.rglob("*"):
                if file_path.is_file():
                    # Check if file matches any exclude pattern
                    relative_path = safe_relative_to(file_path, project_root)

                    # Skip if matches exclude patterns
                    if self._matches_exclude_patterns(str(relative_path), all_excludes):
                        continue

                    # Include source files (.py, .js, .ts, .md, .txt, .yaml, .json)
                    if self._is_source_file(file_path):
                        discovered_files.append(file_path)

        except Exception as e:
            debug_logger.log(
                "ERROR",
                "File discovery failed",
                error=str(e),
                project_root=str(project_root),
            )

        debug_logger.log(
            "INFO",
            "File discovery completed",
            files_found=len(discovered_files),
            exclude_patterns=len(all_excludes),
        )

        return discovered_files

    def _matches_exclude_patterns(self, file_path: str, patterns: set[str]) -> bool:
        """Check if file path matches any exclude pattern.

        Args:
            file_path: File path to check
            patterns: Set of exclude patterns

        Returns:
            True if file matches any exclude pattern
        """
        import fnmatch

        for pattern in patterns:
            # Handle directory/path patterns
            if pattern in file_path:
                return True

            # Extract filename for pattern matching
            filename = Path(file_path).name

            # Use fnmatch for wildcard pattern matching
            if fnmatch.fnmatch(filename, pattern):
                return True

        return False

    def _is_source_file(self, file_path: Path) -> bool:
        """Check if file is a source file worth including.

        Args:
            file_path: Path to check

        Returns:
            True if file is a source file
        """
        source_extensions = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".md",
            ".txt",
            ".yaml",
            ".yml",
            ".json",
            ".toml",
            ".cfg",
            ".ini",
            ".sh",
            ".bash",
            ".zsh",
            ".fish",
            ".ps1",
            ".bat",
            ".html",
            ".css",
            ".scss",
            ".less",
            ".sql",
            ".go",
            ".rs",
            ".java",
            ".cpp",
            ".c",
            ".h",
            ".hpp",
            ".cs",
            ".php",
            ".rb",
            ".swift",
            ".kt",
            ".scala",
            ".r",
            ".m",
            ".mm",
            ".pl",
            ".lua",
            ".vim",
            ".dockerfile",
        }

        return file_path.suffix.lower() in source_extensions
