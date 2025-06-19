"""Integration tests for Slice 4.1a: Search Index & File Discovery integration."""

import json
import tempfile
from pathlib import Path

import pytest

from spec_cli.ai.context.file_discovery import DocumentationDiscovery
from spec_cli.ai.context.search_index import FileIndexManager

# Test constants
INTEGRATION_FILE_COUNT = 10
SAMPLE_CONTENT_BASE = "Sample documentation content for file"


class TestSlice4_1aSearchIndexFileDiscoveryIntegration:
    """Integration tests for documentation discovery and file indexing."""

    def test_integration_end_to_end_documentation_discovery_and_indexing(self):
        """Test complete workflow from discovery through indexing."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Set up project structure
            specs_dir = tmp_path / ".specs"
            specs_dir.mkdir()

            # Create nested documentation structure
            (specs_dir / "api").mkdir()
            (specs_dir / "guides").mkdir()
            (specs_dir / "api" / "users").mkdir()

            test_files = [
                specs_dir / "README.md",
                specs_dir / "api" / "overview.md",
                specs_dir / "api" / "users" / "authentication.md",
                specs_dir / "guides" / "getting_started.md",
                specs_dir / "guides" / "advanced.md",
            ]

            # Create files with realistic content
            for i, file_path in enumerate(test_files):
                content = f"{SAMPLE_CONTENT_BASE} {i}\n\nThis is detailed documentation.\n\n## Section 1\nContent here."
                file_path.write_text(content)

            # Patch project root resolution for both components
            with (
                pytest.MonkeyPatch().context() as m,
            ):
                m.setattr(
                    "spec_cli.ai.context.file_discovery.resolve_project_root",
                    lambda: tmp_path,
                )
                m.setattr(
                    "spec_cli.ai.context.search_index.resolve_project_root",
                    lambda: tmp_path,
                )

                # Step 1: Discover documentation
                discovery = DocumentationDiscovery()
                discovery_result = discovery.discover_documentation()

                assert discovery_result["success"] is True
                assert discovery_result["total_files"] == len(test_files)

                discovered_files = discovery_result["successful_files"]
                assert len(discovered_files) == len(test_files)

                # Step 2: Validate discovered files
                file_paths = [Path(f) for f in discovered_files]
                validation_result = discovery.validate_discovered_files(file_paths)

                assert validation_result["total_valid"] == len(test_files)
                assert validation_result["total_invalid"] == 0

                # Step 3: Build search index
                index_manager = FileIndexManager()
                index_result = index_manager.build_file_index(
                    validation_result["valid_files"]
                )

                assert index_result["success"] is True
                assert index_result["total_files"] == len(test_files)

                # Step 4: Verify index was created properly
                assert index_manager.index_exists() is True

                # Step 5: Verify index contents
                index_data = json.loads(index_manager.index_path.read_text())
                assert len(index_data["files"]) == len(test_files)
                assert "metadata" in index_data
                assert index_data["metadata"]["total_files"] == len(test_files)

                # Step 6: Verify file metadata in index
                for file_path in test_files:
                    file_key = str(file_path)
                    assert file_key in index_data["files"]
                    file_entry = index_data["files"][file_key]
                    assert "size" in file_entry
                    assert "modified_time" in file_entry
                    assert "content_preview" in file_entry
                    assert "line_count" in file_entry
                    assert file_entry["file_type"] == ".md"

    def test_integration_discovery_across_different_project_structures(self):
        """Test discovery works across various project structures."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)

            # Create complex nested structure
            structure_paths = [
                ".specs/core/models/user.md",
                ".specs/core/services/auth.md",
                ".specs/api/v1/endpoints.md",
                ".specs/api/v2/endpoints.md",
                ".specs/docs/development/setup.md",
                ".specs/docs/deployment/production.md",
                ".specs/tests/integration/notes.md",
            ]

            created_files = []
            for path_str in structure_paths:
                file_path = tmp_path / path_str
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(f"Documentation for {path_str}")
                created_files.append(file_path)

            with pytest.MonkeyPatch().context() as m:
                m.setattr(
                    "spec_cli.ai.context.file_discovery.resolve_project_root",
                    lambda: tmp_path,
                )

                discovery = DocumentationDiscovery()
                result = discovery.discover_documentation()

                assert result["success"] is True
                assert result["total_files"] == len(structure_paths)

                # Verify all nested files were found
                discovered_paths = {Path(f).name for f in result["successful_files"]}
                expected_names = {Path(p).name for p in structure_paths}
                assert discovered_paths == expected_names

    def test_integration_handles_mixed_file_types_and_patterns(self):
        """Test integration handles different file types and patterns correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            specs_dir = tmp_path / ".specs"
            specs_dir.mkdir()

            # Create files with different extensions
            test_files = [
                specs_dir / "README.md",
                specs_dir / "notes.txt",
                specs_dir / "guide.rst",
                specs_dir / "config.json",  # Should be ignored by default patterns
                specs_dir / "image.png",  # Should be ignored by default patterns
            ]

            for file_path in test_files:
                file_path.write_text(f"Content for {file_path.name}")

            with pytest.MonkeyPatch().context() as m:
                m.setattr(
                    "spec_cli.ai.context.file_discovery.resolve_project_root",
                    lambda: tmp_path,
                )

                discovery = DocumentationDiscovery()

                # Test default patterns (should find .md and .txt files)
                result = discovery.discover_documentation()
                assert result["success"] is True
                assert result["total_files"] == 2  # Only .md and .txt files

                # Test custom patterns
                custom_result = discovery.discover_documentation(
                    file_patterns=["*.rst"]
                )
                assert custom_result["success"] is True
                assert custom_result["total_files"] == 1  # Only .rst file

    def test_integration_error_handling_with_problematic_files(self):
        """Test integration handles problematic files gracefully."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            specs_dir = tmp_path / ".specs"
            specs_dir.mkdir()

            # Create normal files
            good_files = []
            for i in range(3):
                good_file = specs_dir / f"good_{i}.md"
                good_file.write_text(f"Good content {i}")
                good_files.append(good_file)

            # Create a file that we'll make unreadable (permission error)
            problematic_file = specs_dir / "unreadable.md"
            problematic_file.write_text("This will be unreadable")

            with pytest.MonkeyPatch().context() as m:
                m.setattr(
                    "spec_cli.ai.context.file_discovery.resolve_project_root",
                    lambda: tmp_path,
                )
                m.setattr(
                    "spec_cli.ai.context.search_index.resolve_project_root",
                    lambda: tmp_path,
                )

                discovery = DocumentationDiscovery()
                index_manager = FileIndexManager()

                # Discovery should find all .md files (including problematic one)
                discovery_result = discovery.discover_documentation()

                # Manually create a validation scenario by adding a nonexistent file
                all_paths = [Path(f) for f in discovery_result["successful_files"]]
                all_paths.append(
                    specs_dir / "nonexistent.md"
                )  # Add fake file for validation test

                validation_result = discovery.validate_discovered_files(all_paths)

                # Should have valid files plus one invalid (nonexistent)
                assert validation_result["total_valid"] >= 3
                assert validation_result["total_invalid"] >= 1  # The nonexistent file

                # Indexing should work with valid files only
                index_result = index_manager.build_file_index(
                    validation_result["valid_files"]
                )
                assert index_result["success"] is True

    def test_integration_performance_requirements_met(self):
        """Test integration meets performance requirements for large file sets."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            specs_dir = tmp_path / ".specs"
            specs_dir.mkdir()

            # Create larger number of files to test performance
            large_file_count = 100
            test_files = []

            for i in range(large_file_count):
                test_file = specs_dir / f"doc_{i:03d}.md"
                content = (
                    f"# Document {i}\n\n" + "Content line\n" * 50
                )  # Realistic file size
                test_file.write_text(content)
                test_files.append(test_file)

            with pytest.MonkeyPatch().context() as m:
                m.setattr(
                    "spec_cli.ai.context.file_discovery.resolve_project_root",
                    lambda: tmp_path,
                )
                m.setattr(
                    "spec_cli.ai.context.search_index.resolve_project_root",
                    lambda: tmp_path,
                )

                import time

                start_time = time.time()

                # Full workflow should complete within performance threshold
                discovery = DocumentationDiscovery()
                discovery_result = discovery.discover_documentation()

                file_paths = [Path(f) for f in discovery_result["successful_files"]]
                validation_result = discovery.validate_discovered_files(file_paths)

                index_manager = FileIndexManager()
                index_result = index_manager.build_file_index(
                    validation_result["valid_files"]
                )

                end_time = time.time()
                total_time = end_time - start_time

                # Should complete within 3 seconds for large documentation sets
                assert total_time < 3.0, (
                    f"Integration took {total_time:.2f}s, expected < 3.0s"
                )

                # Verify all operations succeeded
                assert discovery_result["success"] is True
                assert index_result["success"] is True
                assert validation_result["total_valid"] == large_file_count

    def test_integration_index_rebuild_detection_works_correctly(self):
        """Test integration properly detects when index needs rebuilding."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            specs_dir = tmp_path / ".specs"
            specs_dir.mkdir()

            # Create initial files
            initial_file = specs_dir / "initial.md"
            initial_file.write_text("Initial content")

            with pytest.MonkeyPatch().context() as m:
                m.setattr(
                    "spec_cli.ai.context.file_discovery.resolve_project_root",
                    lambda: tmp_path,
                )
                m.setattr(
                    "spec_cli.ai.context.search_index.resolve_project_root",
                    lambda: tmp_path,
                )

                # Initial indexing
                discovery = DocumentationDiscovery()
                index_manager = FileIndexManager()

                discovery_result = discovery.discover_documentation()
                file_paths = [Path(f) for f in discovery_result["successful_files"]]
                index_manager.build_file_index(file_paths)

                # Should not need rebuild immediately
                assert index_manager.needs_rebuild() is False

                # Add new file
                new_file = specs_dir / "new_file.md"
                new_file.write_text("New content")

                # Should now need rebuild
                assert index_manager.needs_rebuild() is True

                # Rebuild index
                new_discovery_result = discovery.discover_documentation()
                new_file_paths = [
                    Path(f) for f in new_discovery_result["successful_files"]
                ]
                index_manager.build_file_index(new_file_paths)

                # Should not need rebuild again
                assert index_manager.needs_rebuild() is False

                # Verify new file is indexed
                indexed_files = index_manager.get_indexed_files()
                assert str(new_file) in indexed_files

    def test_integration_cross_platform_path_handling(self):
        """Test integration handles cross-platform path operations correctly."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            specs_dir = tmp_path / ".specs"
            specs_dir.mkdir()

            # Create files with paths that test cross-platform handling
            test_file = specs_dir / "path" / "to" / "deep" / "file.md"
            test_file.parent.mkdir(parents=True, exist_ok=True)
            test_file.write_text("Cross-platform test content")

            with pytest.MonkeyPatch().context() as m:
                m.setattr(
                    "spec_cli.ai.context.file_discovery.resolve_project_root",
                    lambda: tmp_path,
                )
                m.setattr(
                    "spec_cli.ai.context.search_index.resolve_project_root",
                    lambda: tmp_path,
                )

                discovery = DocumentationDiscovery()
                index_manager = FileIndexManager()

                # Full workflow
                discovery_result = discovery.discover_documentation()
                file_paths = [Path(f) for f in discovery_result["successful_files"]]
                validation_result = discovery.validate_discovered_files(file_paths)
                index_result = index_manager.build_file_index(
                    validation_result["valid_files"]
                )

                # All operations should succeed regardless of platform
                assert discovery_result["success"] is True
                assert validation_result["total_valid"] == 1
                assert index_result["success"] is True

                # Verify file can be found in index
                indexed_files = index_manager.get_indexed_files()
                assert len(indexed_files) == 1
                assert str(test_file) in indexed_files

    def test_integration_summary_generation_provides_meaningful_insights(self):
        """Test integration generates meaningful summary data."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            specs_dir = tmp_path / ".specs"
            specs_dir.mkdir()

            # Create diverse file set
            files_data = [
                ("api.md", "# API Documentation\n\nDetailed API info."),
                ("guide.md", "# User Guide\n\nStep by step guide."),
                ("notes.txt", "Quick notes and reminders."),
                ("changelog.md", "# Changelog\n\n## v1.0\n- Initial release"),
            ]

            for filename, content in files_data:
                file_path = specs_dir / filename
                file_path.write_text(content)

            with pytest.MonkeyPatch().context() as m:
                m.setattr(
                    "spec_cli.ai.context.file_discovery.resolve_project_root",
                    lambda: tmp_path,
                )

                discovery = DocumentationDiscovery()
                discovery_result = discovery.discover_documentation()

                file_paths = [Path(f) for f in discovery_result["successful_files"]]
                summary = discovery.get_discovery_summary(file_paths)

                # Verify meaningful summary data
                assert summary["total_files"] == len(files_data)
                assert summary["file_types"][".md"] == 3
                assert summary["file_types"][".txt"] == 1
                assert summary["total_size_bytes"] > 0
                assert "discovery_time" in summary
                assert summary["project_root"] == str(tmp_path)
                assert summary["specs_directory"] == str(specs_dir)
