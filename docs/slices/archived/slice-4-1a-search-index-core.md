# Slice 4.1a: Search Index & File Discovery

**Goal**: Implement documentation discovery and basic search index without embedding complexity

**Slice Type**: Core Search Infrastructure

**Helper Dependencies & Search Evidence:**
- Helper search performed: `grep -n "def " /Users/spensermcconnell/__Active_Code/spec-cli/spec_cli/utils/*.py | grep -E "(path|platform)"`
- spec_cli/utils/path_utils.py → resolve_project_root(), is_specs_path() for documentation discovery
- spec_cli/utils/platform_utils.py → get_system_info() for index metadata
- spec_cli/utils/workflow_utils.py → create_workflow_result() for result handling
- Create helper: spec_cli/ai/context/search_index.py → build_file_index(docs: List[Path]) → "Build searchable file index with metadata"

**Complexity Analysis:**
- Decision points: 5/7 (docs_found, index_exists, index_needs_rebuild, file_validation, error handling)
- Helper calls: 5 (resolve_project_root, is_specs_path, build_file_index, create_workflow_result, get_system_info)
- McCabe validation: Pass (5 ≤ 7, well under limit)

**Inputs → Action → Outputs:**
- **Inputs**: {rebuild_index: bool, max_files: int, file_patterns: List[str]}
- **Action**:
  1. Discover documentation files using path helpers (decision point + try/except)
  2. Validate discovered files and filter by patterns (decision point)
  3. Check if index exists and needs rebuilding (decision point)
  4. Build file index with metadata using helper (decision point + try/except)
  5. Store index and provide file discovery interface (try/except)
- **Outputs**: {indexed_files: List[Path], index_metadata: Dict[str, Any], file_count: int} or {error_message: str}

**Files to Create/Modify:**
- spec_cli/ai/context/search_index.py (new - file index management helper)
- spec_cli/ai/context/file_discovery.py (new - documentation discovery engine)

**Dependencies**:
- Results passed to Slice 4.1b for embedding generation and semantic search
- Uses existing path utilities for cross-platform file operations
- No external integrations (file system operations only)

**Classes**: 2 (FileIndexManager, DocumentationDiscovery)
**External Integrations**: 0 (internal file system operations only)

**Test Requirements:**
- **Unit Tests**: File discovery with various patterns, index building, metadata extraction, error handling for missing directories
- **Integration Test**: Documentation discovery across different project structures
- **Idempotent Tests**: Consistent file discovery and indexing on repeated runs
- **Mocks/Fixtures**: Sample documentation structures, index scenarios, file permission edge cases

**Quality Gate Validation:**
- poetry run mypy --strict (zero suppressions allowed)
- poetry run ruff check --fix (linting with exit-on-fix)
- poetry run ruff format (code formatting)
- poetry run pydocstyle (documentation check)
- poetry run bandit -r spec_cli/ (security scan - zero high findings)
- poetry run pip-audit (vulnerability scan - zero vulnerabilities)
- poetry run pytest -v --cov=spec_cli --cov-fail-under=90 (strict coverage)
- McCabe complexity ≤ 7 for all functions (achieved: 5/7)
- Performance: File discovery and indexing complete within 3 seconds for large documentation sets

**Integration Validation:**
Discover documentation files in project, build searchable index with metadata, and provide clean interface for semantic search layer (4.1b) to consume.

**Expected Implementation Pattern:**
```python
class DocumentationDiscovery:
    """Discover and catalog documentation files."""

    def __init__(self):
        self.project_root = resolve_project_root()

    def discover_documentation(self, file_patterns: List[str] = None, max_files: int = 1000) -> WorkflowResult:
        """Discover all documentation files for indexing."""
        try:
            specs_path = self.project_root / ".specs"

            # Check if documentation exists (decision point 1)
            if not specs_path.exists():
                return create_workflow_result(
                    success=False,
                    error="No documentation found - run 'spec gen' first"
                )

            # Discover files with patterns (decision point 2 + try/except)
            discovered_files = []
            patterns = file_patterns or ["*.md", "*.txt"]

            for pattern in patterns:
                for file_path in specs_path.rglob(pattern):
                    # Validate file (decision point 3)
                    if is_specs_path(file_path) and file_path.is_file():
                        discovered_files.append(file_path)
                        if len(discovered_files) >= max_files:
                            break

            # Validate discovery results (decision point 4)
            if not discovered_files:
                return create_workflow_result(
                    success=False,
                    error="No documentation files found matching patterns"
                )

            file_metadata = {
                "total_files": len(discovered_files),
                "patterns_used": patterns,
                "discovery_time": datetime.now().isoformat(),
                "project_root": str(self.project_root)
            }

            return create_workflow_result(
                success=True,
                data={
                    "discovered_files": discovered_files,
                    "file_metadata": file_metadata
                },
                message=f"Discovered {len(discovered_files)} documentation files"
            )

        except Exception as e:  # try/except block
            return create_workflow_result(
                success=False,
                error=f"Documentation discovery failed: {str(e)}"
            )

class FileIndexManager:
    """Manage file-based search index without embeddings."""

    def __init__(self):
        self.index_path = resolve_project_root() / ".spec" / "search_index.json"

    def build_file_index(self, file_list: List[Path]) -> WorkflowResult:
        """Build searchable file index with metadata."""
        try:
            index_data = {
                "files": {},
                "metadata": {
                    "created_time": datetime.now().isoformat(),
                    "total_files": len(file_list),
                    "system_info": get_system_info()
                }
            }

            # Process each file (decision point 5)
            for file_path in file_list:
                try:
                    file_stats = file_path.stat()
                    file_content = file_path.read_text(encoding='utf-8')

                    index_data["files"][str(file_path)] = {
                        "size": file_stats.st_size,
                        "modified_time": file_stats.st_mtime,
                        "content_preview": file_content[:200],
                        "line_count": len(file_content.splitlines()),
                        "file_type": file_path.suffix
                    }

                except Exception as e:
                    # Skip files that can't be read, don't fail entire index
                    logger.warning(f"Couldn't index file {file_path}: {e}")
                    continue

            # Write index to disk (try/except)
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.index_path.write_text(json.dumps(index_data, indent=2))

            return create_workflow_result(
                success=True,
                data={
                    "indexed_files": list(index_data["files"].keys()),
                    "index_metadata": index_data["metadata"],
                    "file_count": len(index_data["files"])
                },
                message=f"Built file index with {len(index_data['files'])} files"
            )

        except Exception as e:  # try/except block
            return create_workflow_result(
                success=False,
                error=f"File index building failed: {str(e)}"
            )

    def index_exists(self) -> bool:
        """Check if file index exists."""
        return self.index_path.exists()

    def needs_rebuild(self) -> bool:
        """Check if index needs rebuilding based on file modification times."""
        if not self.index_exists():
            return True

        try:
            index_data = json.loads(self.index_path.read_text())
            index_time = datetime.fromisoformat(index_data["metadata"]["created_time"])

            # Check if any documentation files are newer than index
            specs_path = resolve_project_root() / ".specs"
            for file_path in specs_path.rglob("*.md"):
                if file_path.stat().st_mtime > index_time.timestamp():
                    return True

            return False

        except Exception:
            return True  # Rebuild if we can't determine
```

This sub-slice handles file discovery and basic indexing without ML complexity, preparing a clean foundation for embedding-based semantic search in slice 4.1b.
