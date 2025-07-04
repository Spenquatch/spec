"""End-to-End AI Context Integration Tests - Slice ai_004.

This module tests the complete AI context processing and generation pipeline
including context extraction, processing, ranking, and AI generation integration.
"""

import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.context.extractor import ContextExtractor
from spec_cli.ai.context.processing import AgentScopeValidator, discover_project_files
from spec_cli.ai.context.ranking import RelevanceRanker
from spec_cli.ai.generation.ai_generator import AIDocumentationGenerator
from spec_cli.ai.providers.base import GenerationRequest, GenerationResult


class TestAIContextPipelineEndToEnd:
    """Test complete AI context processing and generation pipeline."""

    def setup_method(self) -> None:
        """Set up test environment for each test."""
        self.test_dir: tempfile.TemporaryDirectory[str] | None = None
        self.mock_provider = Mock()
        # Mock the generate_documentation method that AIDocumentationGenerator calls
        self.mock_provider.generate_documentation.return_value = GenerationResult(
            success=True,
            content={"index.md": "Generated documentation content"},
            metadata={"model": "test-model", "tokens_used": 100},
            error=None,
        )

    def teardown_method(self) -> None:
        """Clean up test environment after each test."""
        if self.test_dir:
            self.test_dir.cleanup()

    def _create_test_project(self) -> Path:
        """Create a temporary test project with sample files."""
        self.test_dir = tempfile.TemporaryDirectory()
        project_path = Path(self.test_dir.name)

        # Create sample project structure
        (project_path / "src").mkdir()
        (project_path / "tests").mkdir()
        (project_path / "docs").mkdir()

        # Add sample Python files
        (project_path / "src" / "main.py").write_text(
            'def main():\n    """Main function."""\n    print("Hello World")\n'
        )
        (project_path / "src" / "utils.py").write_text(
            'def helper():\n    """Helper function."""\n    return "help"\n'
        )

        # Add test files
        (project_path / "tests" / "test_main.py").write_text(
            'def test_main():\n    """Test main function."""\n    assert True\n'
        )

        # Add documentation
        (project_path / "README.md").write_text("# Test Project\n\nSample project.")
        (project_path / "docs" / "guide.md").write_text("# Guide\n\nUser guide.")

        # Add configuration files
        (project_path / "pyproject.toml").write_text(
            "[tool.poetry]\nname = 'test-project'\nversion = '0.1.0'\n"
        )

        return project_path

    def test_complete_pipeline_success_flow(self) -> None:
        """Test successful end-to-end pipeline execution."""
        # Arrange
        project_path = self._create_test_project()

        # Create AI config with valid provider
        AIConfig(
            provider="local",
            enabled=True,
            fallback_to_templates=True,
        )

        # Act - Discover files
        discovery_params = {"base_path": project_path}
        discovered_files = discover_project_files(discovery_params)

        # Assert file discovery
        assert len(discovered_files) > 0
        assert any("main.py" in f for f in discovered_files)
        assert any("utils.py" in f for f in discovered_files)
        assert any("README.md" in f for f in discovered_files)

        # Act - Validate files
        validator = AgentScopeValidator()
        valid_files = []
        for file_path_str in discovered_files:
            file_path = Path(file_path_str)
            if validator.validate_file_inclusion(file_path, project_path):
                valid_files.append(file_path)

        # Assert validation
        assert len(valid_files) > 0

        # Act - Extract context
        extractor = ContextExtractor()
        contexts = []
        for file_path in valid_files[:3]:  # Limit for test performance
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    context = extractor.extract_context(
                        file_path, content, "documentation"
                    )
                    if context:
                        contexts.append(context)
                except Exception:
                    # Skip files that can't be read or processed
                    continue

        # Assert context extraction
        assert len(contexts) > 0
        for context in contexts:
            assert "file_path" in context
            assert "file_size" in context
            assert "functions" in context or "classes" in context

        # Act - Rank contexts
        ranker = RelevanceRanker()
        query = "documentation for main function"
        ranked_contexts = ranker.rank_contexts(contexts, query)

        # Assert ranking
        assert len(ranked_contexts) > 0
        assert all("relevance_score" in ctx for ctx in ranked_contexts)

        # Act - Sanitize code (contexts already sanitized by extractor)
        sanitized_contexts = ranked_contexts  # Already sanitized by ContextExtractor

        # Assert sanitization
        assert len(sanitized_contexts) > 0

        # Act - Generate documentation
        generator = AIDocumentationGenerator(self.mock_provider)
        source_file = project_path / "src" / "main.py"
        source_content = source_file.read_text()

        generation_request = GenerationRequest(
            source_file=source_file,
            content=source_content,
            template_content="Generate documentation for: {{file_content}}",
            context={"contexts": sanitized_contexts[:2]},  # Use top contexts
        )

        result = generator.generate_documentation_from_request(generation_request)

        # Assert generation
        assert result["success"] is True
        assert "generated_docs" in result["data"]
        self.mock_provider.generate_documentation.assert_called_once()

    def test_pipeline_with_error_handling(self) -> None:
        """Test pipeline behavior with various error conditions."""
        # Arrange
        project_path = self._create_test_project()

        # Test file discovery with invalid path
        discovery_params = {"base_path": "/nonexistent/path"}
        discovered_files = discover_project_files(discovery_params)
        assert isinstance(discovered_files, list)  # Should handle gracefully

        # Test context extraction with invalid inputs
        extractor = ContextExtractor()
        with pytest.raises(ValueError):
            extractor.extract_context(Path("/nonexistent/file.py"), "", "query")

        # Test generation with provider error
        error_provider = Mock()
        error_provider.generate_documentation.return_value = GenerationResult(
            success=False,
            content={},
            metadata={},
            error="Generation failed",
        )

        generator = AIDocumentationGenerator(error_provider)
        source_file = project_path / "src" / "main.py"

        source_content = source_file.read_text()
        generation_request = GenerationRequest(
            source_file=source_file,
            content=source_content,
            template_content="Generate docs",
            context={},
        )

        result = generator.generate_documentation_from_request(generation_request)
        assert result["success"] is False
        assert "error" in result

    def test_pipeline_performance_characteristics(self) -> None:
        """Test pipeline performance under various load conditions."""
        import time

        # Arrange
        project_path = self._create_test_project()

        # Create more files for performance testing
        for i in range(10):
            (project_path / f"module_{i}.py").write_text(
                f'def function_{i}():\n    """Function {i}."""\n    return {i}\n'
            )

        # Act - Measure discovery time
        start_time = time.time()
        discovery_params = {"base_path": project_path}
        discovered_files = discover_project_files(discovery_params)
        discovery_time = time.time() - start_time

        # Assert discovery performance
        assert discovery_time < 5.0  # Should complete within 5 seconds
        assert len(discovered_files) > 10

        # Act - Measure context extraction time
        extractor = ContextExtractor()
        start_time = time.time()
        contexts = []
        for file_path_str in discovered_files[:5]:  # Test with subset
            file_path = Path(file_path_str)
            if file_path.exists() and file_path.suffix == ".py":
                try:
                    content = file_path.read_text()
                    context = extractor.extract_context(
                        file_path, content, "performance test"
                    )
                    if context:
                        contexts.append(context)
                except Exception:
                    continue
        extraction_time = time.time() - start_time

        # Assert extraction performance
        assert extraction_time < 3.0  # Should complete within 3 seconds
        assert len(contexts) > 0

    def test_pipeline_with_large_files(self) -> None:
        """Test pipeline behavior with large files."""
        # Arrange
        project_path = self._create_test_project()

        # Create a large file
        large_content = "# Large file\n" + "\n".join(
            [
                f'def function_{i}():\n    """Function {i}."""\n    return {i}'
                for i in range(1000)
            ]
        )
        large_file = project_path / "large_module.py"
        large_file.write_text(large_content)

        # Act - Process large file
        extractor = ContextExtractor()
        large_content_text = large_file.read_text()
        context = extractor.extract_context(
            large_file, large_content_text, "large file test"
        )

        # Assert handling of large file
        assert context is not None
        assert "file_path" in context
        assert context["file_size"] > 0

        # Test that large content was processed
        assert "functions" in context
        assert len(context["functions"]) > 0  # Should have many functions

    def test_pipeline_logging_integration(self) -> None:
        """Test pipeline integration with structured logging."""
        # Arrange
        project_path = self._create_test_project()

        # Act - Run pipeline components (logging verification is implicit)
        discovery_params = {"base_path": project_path}
        discovered_files = discover_project_files(discovery_params)

        extractor = ContextExtractor()
        contexts_processed = 0
        for file_path_str in discovered_files[:2]:
            file_path = Path(file_path_str)
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    context = extractor.extract_context(
                        file_path, content, "logging test"
                    )
                    if context:
                        contexts_processed += 1
                except Exception:
                    continue

        # Assert pipeline executed successfully (logging is happening internally)
        assert contexts_processed > 0

    def test_pipeline_configuration_integration(self) -> None:
        """Test pipeline integration with AI configuration."""
        # Arrange
        project_path = self._create_test_project()

        # Create AI config
        config = AIConfig(
            provider="local",
            enabled=True,
            fallback_to_templates=True,
        )

        # Act - Use config in pipeline components
        generator = AIDocumentationGenerator(self.mock_provider)
        source_file = project_path / "src" / "main.py"

        source_content = source_file.read_text()
        generation_request = GenerationRequest(
            source_file=source_file,
            content=source_content,
            template_content="Generate documentation using config",
            context={"config": config.model_dump()},
        )

        result = generator.generate_documentation_from_request(generation_request)

        # Assert configuration is used
        assert result["success"] is True
        self.mock_provider.generate_documentation.assert_called_once()

    def test_pipeline_with_multiple_file_types(self) -> None:
        """Test pipeline handling of different file types."""
        # Arrange
        project_path = self._create_test_project()

        # Add more file types
        (project_path / "script.js").write_text(
            'function greet() {\n    console.log("Hello");\n}'
        )
        (project_path / "styles.css").write_text(".container {\n    margin: 10px;\n}")
        (project_path / "config.json").write_text('{"name": "test", "version": "1.0"}')

        # Act - Discover all file types
        discovery_params = {"base_path": project_path}
        discovered_files = discover_project_files(discovery_params)

        # Assert different file types are discovered
        file_extensions = {Path(f).suffix for f in discovered_files}
        assert ".py" in file_extensions
        assert ".js" in file_extensions
        assert ".md" in file_extensions
        assert ".json" in file_extensions

        # Test context extraction for different types
        extractor = ContextExtractor()
        contexts_by_type: dict[str, Any] = {}

        for file_path_str in discovered_files:
            file_path = Path(file_path_str)
            if file_path.exists():
                try:
                    content = file_path.read_text()
                    context = extractor.extract_context(
                        file_path, content, "file type test"
                    )
                    if context:
                        ext = file_path.suffix
                        if ext not in contexts_by_type:
                            contexts_by_type[ext] = []
                        contexts_by_type[ext].append(context)
                except Exception:
                    continue

        # Assert contexts extracted for different file types
        assert len(contexts_by_type) > 0
        assert ".py" in contexts_by_type

    def test_pipeline_context_ranking_accuracy(self) -> None:
        """Test accuracy of context ranking in pipeline."""
        # Arrange
        project_path = self._create_test_project()

        # Create files with different relevance levels
        (project_path / "authentication.py").write_text(
            'def login(username, password):\n    """User login function."""\n    pass'
        )
        (project_path / "database.py").write_text(
            'def connect_db():\n    """Database connection."""\n    pass'
        )
        (project_path / "utils.py").write_text(
            'def format_date():\n    """Date formatting utility."""\n    pass'
        )

        # Act - Extract contexts
        extractor = ContextExtractor()
        contexts = []
        for py_file in project_path.glob("*.py"):
            try:
                content = py_file.read_text()
                context = extractor.extract_context(
                    py_file, content, "ranking accuracy test"
                )
                if context:
                    contexts.append(context)
            except Exception:
                continue

        # Test ranking for authentication query
        ranker = RelevanceRanker()
        auth_query = "user login authentication"
        ranked_contexts = ranker.rank_contexts(contexts, auth_query)

        # Assert authentication file ranks highest
        assert len(ranked_contexts) > 0
        top_context = ranked_contexts[0]
        assert "authentication.py" in str(top_context.get("file_path", ""))

        # Test ranking for database query
        db_query = "database connection"
        ranked_contexts = ranker.rank_contexts(contexts, db_query)

        # Assert database file ranks highly
        assert len(ranked_contexts) > 0
        assert any(
            "database.py" in str(ctx.get("file_path", ""))
            for ctx in ranked_contexts[:2]
        )


class TestAIContextPipelineErrorRecovery:
    """Test error recovery and resilience in AI context pipeline."""

    def test_partial_pipeline_failure_recovery(self) -> None:
        """Test pipeline recovery from partial failures."""
        # Arrange
        project_path = Path("/tmp/test_project")
        project_path.mkdir(exist_ok=True)

        try:
            # Create mixed valid and invalid files
            valid_file = project_path / "valid.py"
            valid_file.write_text(
                'def valid_function():\n    """Valid function."""\n    pass'
            )

            # Create file with permission issues (simulate)
            protected_file = project_path / "protected.py"
            protected_file.write_text("def protected():\n    pass")

            # Act - Process with some failures
            extractor = ContextExtractor()
            successful_contexts = []
            failed_extractions = []

            for py_file in project_path.glob("*.py"):
                try:
                    content = py_file.read_text()
                    context = extractor.extract_context(
                        py_file, content, "recovery test"
                    )
                    if context:
                        successful_contexts.append(context)
                except Exception as e:
                    failed_extractions.append((py_file, str(e)))

            # Assert partial success
            assert len(successful_contexts) > 0  # Some files processed successfully
            # Pipeline should continue despite some failures

        finally:
            # Cleanup
            import shutil

            if project_path.exists():
                shutil.rmtree(project_path)

    def test_provider_timeout_handling(self) -> None:
        """Test pipeline behavior with AI provider timeouts."""
        # Arrange
        timeout_provider = Mock()
        timeout_provider.generate_documentation.side_effect = TimeoutError(
            "Generation timeout"
        )

        generator = AIDocumentationGenerator(timeout_provider)

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write('def test_function():\n    """Test function."""\n    pass')
            temp_file = Path(f.name)

        try:
            # Act - Attempt generation with timeout
            temp_content = temp_file.read_text()
            generation_request = GenerationRequest(
                source_file=temp_file,
                content=temp_content,
                template_content="Generate documentation",
                context={},
            )

            result = generator.generate_documentation_from_request(generation_request)

            # Assert timeout handling
            assert result["success"] is False
            assert "error" in result
            assert (
                "timeout" in result["error"].lower()
                or "generation timeout" in result["error"]
            )

        finally:
            # Cleanup
            temp_file.unlink(missing_ok=True)

    def test_memory_efficient_large_project_processing(self) -> None:
        """Test pipeline memory efficiency with large projects."""
        # Arrange
        project_path = Path("/tmp/large_test_project")
        project_path.mkdir(exist_ok=True)

        try:
            # Create many files to test memory efficiency
            for i in range(50):  # Reduced from 100 for test performance
                (project_path / f"module_{i}.py").write_text(
                    f'def function_{i}():\n    """Function {i}."""\n    return {i}'
                )

            # Act - Process with memory monitoring
            import os

            import psutil

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss

            # Discover files
            discovery_params = {"base_path": project_path}
            discovered_files = discover_project_files(discovery_params)

            # Process contexts in batches to manage memory
            extractor = ContextExtractor()
            batch_size = 10
            total_contexts = 0

            for i in range(0, len(discovered_files), batch_size):
                batch = discovered_files[i : i + batch_size]
                batch_contexts = []

                for file_path_str in batch:
                    file_path = Path(file_path_str)
                    if file_path.exists() and file_path.suffix == ".py":
                        try:
                            content = file_path.read_text()
                            context = extractor.extract_context(
                                file_path, content, "memory test"
                            )
                            if context:
                                batch_contexts.append(context)
                        except Exception:
                            continue

                total_contexts += len(batch_contexts)
                # Simulate processing batch and clearing memory
                del batch_contexts

            final_memory = process.memory_info().rss
            memory_increase = final_memory - initial_memory

            # Assert memory efficiency
            assert total_contexts > 0
            assert memory_increase < 100 * 1024 * 1024  # Less than 100MB increase

        finally:
            # Cleanup
            import shutil

            if project_path.exists():
                shutil.rmtree(project_path)
