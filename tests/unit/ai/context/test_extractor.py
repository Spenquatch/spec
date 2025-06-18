"""Unit tests for ContextExtractor class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.ai.analysis.sanitizer import CodeSanitizer
from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.context.extractor import ContextExtractor


class TestContextExtractorInitialization:
    """Test ContextExtractor initialization."""

    def test_init_with_defaults_creates_extractor_with_default_config(self):
        """Test initialization with default parameters."""
        extractor = ContextExtractor()

        assert isinstance(extractor.ai_config, AIConfig)
        assert isinstance(extractor.sanitizer, CodeSanitizer)
        assert extractor.debug_logger is not None
        assert hasattr(extractor, "import_pattern")
        assert hasattr(extractor, "class_pattern")
        assert hasattr(extractor, "function_pattern")

    def test_init_with_custom_components_uses_provided_components(self):
        """Test initialization with custom components."""
        mock_config = Mock(spec=AIConfig)
        mock_sanitizer = Mock(spec=CodeSanitizer)
        mock_logger = Mock()

        extractor = ContextExtractor(
            ai_config=mock_config, sanitizer=mock_sanitizer, debug_logger=mock_logger
        )

        assert extractor.ai_config is mock_config
        assert extractor.sanitizer is mock_sanitizer
        assert extractor.debug_logger is mock_logger

    def test_compile_patterns_creates_working_regex_patterns(self):
        """Test that regex patterns are properly compiled."""
        extractor = ContextExtractor()

        # Test import pattern
        test_content = "import os\nfrom pathlib import Path"
        imports = extractor.import_pattern.findall(test_content)
        assert len(imports) == 2
        assert "import os" in imports

        # Test class pattern
        test_content = "class TestClass:\n    pass"
        classes = extractor.class_pattern.findall(test_content)
        assert classes == ["TestClass"]

        # Test function pattern
        test_content = "def test_function():\n    pass"
        functions = extractor.function_pattern.findall(test_content)
        assert functions == ["test_function"]


class TestContextExtractorExtractContext:
    """Test ContextExtractor extract_context method."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with mocked dependencies."""
        mock_sanitizer = Mock(spec=CodeSanitizer)
        mock_sanitizer.sanitize.side_effect = lambda content, path: content
        mock_logger = Mock()

        return ContextExtractor(sanitizer=mock_sanitizer, debug_logger=mock_logger)

    @pytest.fixture
    def sample_python_content(self):
        """Sample Python file content for testing."""
        return '''"""Module docstring."""
import os
import sys
from pathlib import Path

class SampleClass:
    """Class docstring."""
    def method_one(self):
        # Method comment
        pass

def function_one():
    """Function docstring."""
    return True

# Standalone comment
def function_two():
    pass
'''

    def test_extract_context_when_valid_inputs_then_returns_complete_context(
        self, extractor, sample_python_content
    ):
        """Test context extraction with valid inputs."""
        file_path = Path("/test/sample.py")
        query = "sample class method"

        result = extractor.extract_context(file_path, sample_python_content, query)

        assert isinstance(result, dict)
        assert "file_path" in result
        assert "file_size" in result
        assert "imports" in result
        assert "classes" in result
        assert "functions" in result
        assert "comments" in result
        assert "docstrings" in result
        assert "relevance_score" in result
        assert "sanitized" in result

        # Verify extracted content
        assert len(result["imports"]) == 3
        assert "SampleClass" in result["classes"]
        assert "function_one" in result["functions"]
        assert "function_two" in result["functions"]

    def test_extract_context_when_empty_file_path_then_raises_value_error(
        self, extractor
    ):
        """Test extraction with empty file path."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            extractor.extract_context(Path(""), "content", "query")

    def test_extract_context_when_empty_content_then_raises_value_error(
        self, extractor
    ):
        """Test extraction with empty content."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            extractor.extract_context(Path("/test.py"), "", "query")

    def test_extract_context_when_none_file_path_then_raises_value_error(
        self, extractor
    ):
        """Test extraction with None file path."""
        with pytest.raises(ValueError, match="File path cannot be empty"):
            extractor.extract_context(None, "content", "query")

    def test_extract_context_when_called_then_sanitizes_content(
        self, extractor, sample_python_content
    ):
        """Test that content is sanitized during extraction."""
        file_path = Path("/test/sample.py")
        query = "test"

        extractor.extract_context(file_path, sample_python_content, query)

        # Verify sanitizer was called
        extractor.sanitizer.sanitize.assert_called_once()
        call_args = extractor.sanitizer.sanitize.call_args
        assert call_args[0][0] == sample_python_content
        assert "test/sample.py" in str(call_args[0][1])

    def test_extract_context_when_called_then_logs_debug_information(
        self, extractor, sample_python_content
    ):
        """Test that debug information is logged."""
        file_path = Path("/test/sample.py")
        query = "test"

        extractor.extract_context(file_path, sample_python_content, query)

        # Verify debug logging
        extractor.debug_logger.log.assert_called_once()
        call_args = extractor.debug_logger.log.call_args
        assert call_args[0][0] == "DEBUG"
        assert call_args[0][1] == "Context extracted"

    @patch("spec_cli.ai.context.extractor.normalize_path_separators")
    def test_extract_context_when_windows_path_then_normalizes_path(
        self, mock_normalize, extractor, sample_python_content
    ):
        """Test path normalization for cross-platform compatibility."""
        mock_normalize.return_value = "normalized/path/test.py"
        file_path = Path("C:\\test\\sample.py")
        query = "test"

        result = extractor.extract_context(file_path, sample_python_content, query)

        mock_normalize.assert_called()
        assert result["file_path"] == "normalized/path/test.py"


class TestContextExtractorElementExtraction:
    """Test element extraction methods."""

    @pytest.fixture
    def extractor(self):
        """Create basic extractor for testing."""
        return ContextExtractor()

    def test_extract_imports_when_multiple_import_styles_then_extracts_all(
        self, extractor
    ):
        """Test import extraction with different styles."""
        content = """import os
import sys
from pathlib import Path
from typing import Dict, List
from .local import helper
"""
        imports = extractor._extract_imports(content)

        assert len(imports) >= 4  # At least 4 imports should be found
        assert any("import os" in imp for imp in imports)
        assert any("import sys" in imp for imp in imports)
        assert any("from pathlib import Path" in imp for imp in imports)

    def test_extract_classes_when_multiple_classes_then_extracts_names(self, extractor):
        """Test class name extraction."""
        content = """
class FirstClass:
    pass

class SecondClass(BaseClass):
    pass

class ThirdClass:
    def method(self):
        pass
"""
        classes = extractor._extract_classes(content)

        assert "FirstClass" in classes
        assert "SecondClass" in classes
        assert "ThirdClass" in classes
        assert len(classes) == 3

    def test_extract_functions_when_multiple_functions_then_extracts_names(
        self, extractor
    ):
        """Test function name extraction."""
        content = """
def function_one():
    pass

def function_two(param):
    return param

def _private_function():
    pass
"""
        functions = extractor._extract_functions(content)

        assert "function_one" in functions
        assert "function_two" in functions
        assert "_private_function" in functions
        assert len(functions) == 3

    def test_extract_comments_when_multiple_comment_styles_then_extracts_content(
        self, extractor
    ):
        """Test comment extraction."""
        content = """# This is a comment
def function():
    # Inline comment
    pass
    # Another comment
"""
        comments = extractor._extract_comments(content)

        assert len(comments) >= 2
        assert any("This is a comment" in comment for comment in comments)

    def test_extract_docstrings_when_multiple_docstrings_then_extracts_content(
        self, extractor
    ):
        """Test docstring extraction."""
        content = '''"""Module docstring."""

class TestClass:
    """Class docstring."""

    def method(self):
        """Method docstring."""
        pass
'''
        docstrings = extractor._extract_docstrings(content)

        assert len(docstrings) >= 2
        assert any("Module docstring" in doc for doc in docstrings)
        assert any("Class docstring" in doc for doc in docstrings)


class TestContextExtractorRelevanceCalculation:
    """Test relevance calculation methods."""

    @pytest.fixture
    def extractor(self):
        """Create basic extractor for testing."""
        return ContextExtractor()

    def test_calculate_relevance_when_empty_query_then_returns_neutral_score(
        self, extractor
    ):
        """Test relevance calculation with empty query."""
        score = extractor._calculate_relevance("content", "", [], [], [])
        assert score == 0.5

    def test_calculate_relevance_when_matching_terms_then_returns_higher_score(
        self, extractor
    ):
        """Test relevance calculation with matching terms."""
        content = "This function processes user data efficiently"
        query = "function user data"

        score = extractor._calculate_relevance(
            content, query, [], ["function"], ["process_user"]
        )

        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should be above neutral

    def test_calculate_relevance_when_no_matches_then_returns_low_score(
        self, extractor
    ):
        """Test relevance calculation with no matches."""
        content = "This function does something"
        query = "database connection error"

        score = extractor._calculate_relevance(content, query, [], [], [])

        assert 0.0 <= score <= 1.0
        assert score < 0.5  # Should be below neutral

    def test_extract_query_terms_when_complex_query_then_extracts_meaningful_terms(
        self, extractor
    ):
        """Test query term extraction."""
        query = "find the user authentication function for database"
        terms = extractor._extract_query_terms(query)

        assert "find" in terms
        assert "user" in terms
        assert "authentication" in terms
        assert "function" in terms
        assert "database" in terms
        # Common words should be filtered out
        assert "the" not in terms
        assert "for" not in terms

    def test_score_content_matches_when_all_terms_match_then_returns_one(
        self, extractor
    ):
        """Test content scoring with all matching terms."""
        content = "user authentication database function"
        query_terms = {"user", "authentication", "database", "function"}

        score = extractor._score_content_matches(content, query_terms)
        assert score == 1.0

    def test_score_content_matches_when_no_terms_match_then_returns_zero(
        self, extractor
    ):
        """Test content scoring with no matching terms."""
        content = "completely different content here"
        query_terms = {"user", "authentication", "database", "function"}

        score = extractor._score_content_matches(content, query_terms)
        assert score == 0.0

    def test_score_structure_matches_when_terms_in_structure_then_scores_correctly(
        self, extractor
    ):
        """Test structural element scoring."""
        query_terms = {"user", "authenticate"}
        imports = ["from auth import user_auth"]
        classes = ["UserManager"]
        functions = ["authenticate_user"]

        score = extractor._score_structure_matches(
            query_terms, imports, classes, functions
        )

        assert 0.0 <= score <= 1.0
        assert score > 0.0  # Should find some matches


class TestContextExtractorConfigurationSummary:
    """Test configuration summary method."""

    def test_get_extraction_summary_when_called_then_returns_complete_summary(self):
        """Test extraction summary generation."""
        mock_sanitizer = Mock(spec=CodeSanitizer)
        mock_sanitizer.config = Mock()
        mock_sanitizer.config.enabled = True
        mock_config = Mock(spec=AIConfig)

        extractor = ContextExtractor(ai_config=mock_config, sanitizer=mock_sanitizer)

        summary = extractor.get_extraction_summary()

        assert isinstance(summary, dict)
        assert "sanitizer_enabled" in summary
        assert "ai_config_loaded" in summary
        assert "patterns_compiled" in summary
        assert "supported_extractions" in summary
        assert summary["sanitizer_enabled"] is True
        assert summary["ai_config_loaded"] is True
        assert summary["patterns_compiled"] is True
        assert isinstance(summary["supported_extractions"], list)


class TestContextExtractorErrorHandling:
    """Test error handling in ContextExtractor."""

    @pytest.fixture
    def extractor(self):
        """Create extractor with mocked dependencies."""
        return ContextExtractor()

    def test_extract_context_when_sanitizer_fails_then_handles_gracefully(self):
        """Test handling of sanitizer failures."""
        mock_sanitizer = Mock(spec=CodeSanitizer)
        mock_sanitizer.sanitize.side_effect = Exception("Sanitizer error")

        extractor = ContextExtractor(sanitizer=mock_sanitizer)

        # Should raise exception when sanitizer fails
        with pytest.raises(Exception, match="Sanitizer error"):
            extractor.extract_context(Path("/test.py"), "content", "query")

    def test_regex_patterns_when_malformed_content_then_handle_gracefully(
        self, extractor
    ):
        """Test regex patterns with malformed content."""
        malformed_content = "def \n class \n import"

        # Should not crash on malformed content
        imports = extractor._extract_imports(malformed_content)
        classes = extractor._extract_classes(malformed_content)
        functions = extractor._extract_functions(malformed_content)

        # Should return empty lists for malformed content
        assert isinstance(imports, list)
        assert isinstance(classes, list)
        assert isinstance(functions, list)


class TestContextExtractorCrossPlatformCompatibility:
    """Test cross-platform compatibility."""

    @patch("spec_cli.ai.context.extractor.normalize_path_separators")
    def test_extract_context_when_different_path_separators_then_normalizes(
        self, mock_normalize
    ):
        """Test path normalization across platforms."""
        mock_normalize.return_value = "normalized/path.py"
        mock_sanitizer = Mock(spec=CodeSanitizer)
        mock_sanitizer.sanitize.return_value = "content"

        extractor = ContextExtractor(sanitizer=mock_sanitizer)

        # Test with Windows-style path
        windows_path = Path("C:\\project\\file.py")
        result = extractor.extract_context(windows_path, "content", "query")

        # Should normalize path separators
        mock_normalize.assert_called()
        assert result["file_path"] == "normalized/path.py"
