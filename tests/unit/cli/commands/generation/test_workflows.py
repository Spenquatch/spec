"""Tests for generation workflows module."""

from pathlib import Path

from spec_cli.cli.commands.generation.workflows import (
    AddWorkflow,
    GenerationResult,
    GenerationWorkflow,
    create_add_workflow,
    create_generation_workflow,
    create_regeneration_workflow,
)


class TestGenerationResult:
    """Test the GenerationResult dataclass."""

    def test_summary_when_empty_result_then_returns_zero_counts(self) -> None:
        """Test that empty generation result returns zero counts in summary."""
        result = GenerationResult(
            generated_files=[],
            skipped_files=[],
            failed_files=[],
            conflicts_resolved=[],
            total_processing_time=1.23,
            success=True,
        )

        summary = result.summary

        assert summary["generated"] == 0
        assert summary["skipped"] == 0
        assert summary["failed"] == 0
        assert summary["conflicts"] == 0
        assert summary["time"] == "1.23s"
        assert summary["success"] is True

    def test_summary_when_files_processed_then_returns_correct_counts(self) -> None:
        """Test that generation result with files returns correct counts."""
        result = GenerationResult(
            generated_files=[Path("file1.md"), Path("file2.md")],
            skipped_files=[Path("skip1.md")],
            failed_files=[{"file": "fail1.md", "error": "test error"}],
            conflicts_resolved=[{"file": "conflict1.md", "action": "backup"}],
            total_processing_time=5.67,
            success=False,
        )

        summary = result.summary

        assert summary["generated"] == 2
        assert summary["skipped"] == 1
        assert summary["failed"] == 1
        assert summary["conflicts"] == 1
        assert summary["time"] == "5.67s"
        assert summary["success"] is False


class TestGenerationWorkflow:
    """Test the GenerationWorkflow class utility methods."""

    def test_get_spec_files_for_source_when_relative_path_then_creates_correct_spec_paths(
        self,
    ) -> None:
        """Test that relative source file creates correct spec file paths."""
        workflow = GenerationWorkflow()
        source_file = Path("src/module.py")

        result = workflow._get_spec_files_for_source(source_file)

        # Path resolver returns absolute paths
        assert result["index"].parts[-4:] == (".specs", "src", "module", "index.md")
        assert result["history"].parts[-4:] == (".specs", "src", "module", "history.md")

    def test_get_spec_files_for_source_when_absolute_path_then_creates_relative_spec_paths(
        self,
    ) -> None:
        """Test that absolute source file creates relative spec file paths."""
        workflow = GenerationWorkflow()
        # Create an absolute path relative to current working directory
        current_dir = Path.cwd()
        source_file = current_dir / "src" / "module.py"

        result = workflow._get_spec_files_for_source(source_file)

        # Path resolver returns absolute paths
        assert result["index"].parts[-4:] == (".specs", "src", "module", "index.md")
        assert result["history"].parts[-4:] == (".specs", "src", "module", "history.md")


class TestAddWorkflow:
    """Test the AddWorkflow class utility methods."""

    def test_is_spec_file_when_file_in_specs_directory_then_returns_true(self) -> None:
        """Test that files in .specs directory are detected as spec files."""
        workflow = AddWorkflow()
        spec_file = Path(".specs/src/module/index.md")

        result = workflow._is_spec_file(spec_file)

        assert result is True

    def test_is_spec_file_when_file_outside_specs_directory_then_returns_false(
        self,
    ) -> None:
        """Test that files outside .specs directory are not detected as spec files."""
        workflow = AddWorkflow()
        non_spec_file = Path("src/module.py")

        result = workflow._is_spec_file(non_spec_file)

        assert result is False


class TestFactoryFunctions:
    """Test the workflow factory functions."""

    def test_create_generation_workflow_when_no_args_then_returns_generation_workflow(
        self,
    ) -> None:
        """Test that create_generation_workflow returns GenerationWorkflow instance."""
        result = create_generation_workflow()

        assert isinstance(result, GenerationWorkflow)

    def test_create_generation_workflow_when_kwargs_provided_then_passes_to_constructor(
        self,
    ) -> None:
        """Test that create_generation_workflow passes kwargs to constructor."""
        result = create_generation_workflow(template_name="custom", auto_commit=True)

        assert isinstance(result, GenerationWorkflow)
        assert result.template_name == "custom"
        assert result.auto_commit is True

    def test_create_regeneration_workflow_when_called_then_returns_regeneration_workflow(
        self,
    ) -> None:
        """Test that create_regeneration_workflow returns RegenerationWorkflow instance."""
        from spec_cli.cli.commands.generation.workflows import RegenerationWorkflow

        result = create_regeneration_workflow()

        assert isinstance(result, RegenerationWorkflow)

    def test_create_add_workflow_when_called_then_returns_add_workflow(self) -> None:
        """Test that create_add_workflow returns AddWorkflow instance."""
        result = create_add_workflow()

        assert isinstance(result, AddWorkflow)

    def test_create_add_workflow_when_force_provided_then_passes_to_constructor(
        self,
    ) -> None:
        """Test that create_add_workflow passes force parameter to constructor."""
        result = create_add_workflow(force=True)

        assert isinstance(result, AddWorkflow)
        assert result.force is True
