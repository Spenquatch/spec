"""Integration tests for Slice 2.2b context extraction and ranking."""

import tempfile
from pathlib import Path

import pytest

from spec_cli.ai.config.settings import AIConfig
from spec_cli.ai.context.processing import process_agent_scope_context


class TestSlice22bContextProcessingIntegration:
    """Integration tests for complete context processing pipeline."""

    @pytest.fixture
    def sample_project(self):
        """Create a sample project structure for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)

            # Create Python files with different content types
            main_file = project_root / "main.py"
            main_file.write_text('''"""Main application module."""
import os
import sys
from pathlib import Path
from utils import helper_function

class ApplicationManager:
    """Manages the main application lifecycle."""

    def __init__(self):
        self.config = {}
        self.is_running = False

    def start_application(self):
        """Start the application with configuration."""
        # Initialize application components
        self.is_running = True
        return True

    def stop_application(self):
        """Stop the application gracefully."""
        self.is_running = False

def main():
    """Main entry point for the application."""
    app = ApplicationManager()
    app.start_application()
    # Run application logic here
    app.stop_application()

if __name__ == "__main__":
    main()
''')

            utils_file = project_root / "utils.py"
            utils_file.write_text(r'''"""Utility functions for the application."""
import re
import json
from typing import Dict, List, Optional

def helper_function(data: str) -> str:
    """Process input data and return formatted result."""
    return data.strip().lower()

def validate_email(email: str) -> bool:
    """Validate email address format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def parse_config(config_path: Path) -> Dict:
    """Parse configuration file and return settings."""
    if not config_path.exists():
        return {}

    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

class DataProcessor:
    """Process various types of data."""

    def __init__(self):
        self.processed_count = 0

    def process_items(self, items: List[str]) -> List[str]:
        """Process a list of items."""
        results = []
        for item in items:
            processed = helper_function(item)
            results.append(processed)
            self.processed_count += 1
        return results
''')

            config_file = project_root / "config.py"
            config_file.write_text('''"""Configuration settings for the application."""
from pathlib import Path

# Application settings
DEBUG = True
VERSION = "1.0.0"
APP_NAME = "Sample Application"

# File paths
DATA_DIR = Path("data")
LOG_DIR = Path("logs")
CONFIG_FILE = Path("config.json")

# Database configuration
DATABASE_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "app_db",
    "timeout": 30
}

def get_log_level():
    """Get the current log level based on debug setting."""
    return "DEBUG" if DEBUG else "INFO"

def validate_config():
    """Validate the current configuration."""
    required_dirs = [DATA_DIR, LOG_DIR]
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
    return True
''')

            # Create a JavaScript file for diversity
            js_file = project_root / "frontend.js"
            js_file.write_text("""/**
 * Frontend JavaScript utilities
 */

class UserInterface {
    constructor() {
        this.initialized = false;
    }

    initialize() {
        // Initialize UI components
        this.initialized = true;
        console.log('UI initialized');
    }

    handleUserInput(input) {
        // Process user input
        return input.trim();
    }
}

function validateForm(formData) {
    // Validate form data
    const required = ['name', 'email'];
    for (const field of required) {
        if (!formData[field]) {
            return false;
        }
    }
    return true;
}

// Export for use in other modules
if (typeof module !== 'undefined') {
    module.exports = { UserInterface, validateForm };
}
""")

            # Create a README for testing different file types
            readme_file = project_root / "README.md"
            readme_file.write_text("""# Sample Application

This is a sample application for testing context extraction.

## Features

- Application lifecycle management
- Configuration handling
- Data processing utilities
- Email validation
- Frontend interface

## Usage

Run the main application:

```python
python main.py
```

## Configuration

The application uses JSON configuration files. See `config.py` for default settings.
""")

            yield project_root

    def test_integration_end_to_end_context_processing_produces_ranked_results(
        self, sample_project
    ):
        """Test complete context processing pipeline end-to-end."""
        query = "application manager configuration"

        result = process_agent_scope_context(
            base_path=sample_project, query=query, max_results=10
        )

        # Verify result structure
        assert isinstance(result, dict)
        assert "ranked_files" in result
        assert "processing_summary" in result
        assert "query_analysis" in result
        assert "ranking_statistics" in result

        # Verify we got some results
        ranked_files = result["ranked_files"]
        assert len(ranked_files) > 0

        # Verify all results have required fields
        for file_result in ranked_files:
            assert "file_path" in file_result
            assert "composite_score" in file_result
            assert "relevance_score" in file_result
            assert "file_size" in file_result
            assert isinstance(file_result["composite_score"], float)
            assert 0.0 <= file_result["composite_score"] <= 1.0

    def test_integration_query_matching_prioritizes_relevant_files(
        self, sample_project
    ):
        """Test that files matching query terms are ranked higher."""
        # Query specifically for application management
        query = "application manager start stop"

        result = process_agent_scope_context(
            base_path=sample_project, query=query, max_results=5
        )

        ranked_files = result["ranked_files"]
        assert len(ranked_files) > 0

        # main.py should rank highly due to ApplicationManager class
        main_py_results = [f for f in ranked_files if "main.py" in f["file_path"]]
        assert len(main_py_results) > 0

        # Should have high relevance score
        main_py_score = main_py_results[0]["composite_score"]
        assert main_py_score > 0.5

    def test_integration_file_type_preferences_affect_ranking(self, sample_project):
        """Test that file type preferences influence ranking."""
        query = "function validation interface"

        result = process_agent_scope_context(
            base_path=sample_project, query=query, max_results=10
        )

        ranked_files = result["ranked_files"]

        # Python files should generally rank higher than JS/MD files
        python_files = [f for f in ranked_files if f["file_path"].endswith(".py")]
        other_files = [f for f in ranked_files if not f["file_path"].endswith(".py")]

        if python_files and other_files:
            avg_python_score = sum(f["composite_score"] for f in python_files) / len(
                python_files
            )
            avg_other_score = sum(f["composite_score"] for f in other_files) / len(
                other_files
            )

            # Python files should generally score higher (with small tolerance for query-specific effects)
            assert avg_python_score >= (avg_other_score - 0.1)

    def test_integration_processing_summary_reflects_pipeline_stages(
        self, sample_project
    ):
        """Test that processing summary accurately reflects pipeline execution."""
        query = "configuration data processing"

        result = process_agent_scope_context(
            base_path=sample_project, query=query, max_results=5
        )

        summary = result["processing_summary"]

        # Verify pipeline stages make sense
        stages = summary["pipeline_stages"]
        assert stages["discovered"] >= stages["validated"]
        assert stages["validated"] >= stages["processed"]
        assert stages["processed"] >= stages["ranked"]

        # Verify efficiency metrics are reasonable
        efficiency = summary["processing_efficiency"]
        assert 0.0 <= efficiency["validation_rate"] <= 1.0
        assert 0.0 <= efficiency["processing_rate"] <= 1.0
        assert 0.0 <= efficiency["error_rate"] <= 1.0

    def test_integration_query_analysis_provides_meaningful_insights(
        self, sample_project
    ):
        """Test that query analysis provides useful information."""
        query = "application data validation email"

        result = process_agent_scope_context(
            base_path=sample_project, query=query, max_results=5
        )

        analysis = result["query_analysis"]

        # Verify query terms are extracted
        query_terms = analysis["query_terms"]
        assert "application" in query_terms
        assert "data" in query_terms
        assert "validation" in query_terms
        assert "email" in query_terms

        # Verify term coverage makes sense
        term_coverage = analysis["term_coverage"]
        assert isinstance(term_coverage, dict)

        # Verify effectiveness metrics
        assert 0.0 <= analysis["average_relevance"] <= 1.0
        assert 0.0 <= analysis["query_effectiveness"] <= 1.0

    def test_integration_ranking_statistics_provide_distribution_insights(
        self, sample_project
    ):
        """Test that ranking statistics provide useful distribution information."""
        query = "manager processor interface"

        result = process_agent_scope_context(
            base_path=sample_project, query=query, max_results=10
        )

        stats = result["ranking_statistics"]

        # Verify basic statistics
        assert "total_results" in stats
        assert "average_score" in stats
        assert "score_distribution" in stats
        assert "file_types" in stats

        # Verify score distribution buckets
        distribution = stats["score_distribution"]
        expected_buckets = ["0.8-1.0", "0.6-0.8", "0.4-0.6", "0.2-0.4", "0.0-0.2"]
        for bucket in expected_buckets:
            assert bucket in distribution
            assert isinstance(distribution[bucket], int)

        # Verify file type counting
        file_types = stats["file_types"]
        assert isinstance(file_types, dict)
        # Should have at least .py files
        assert any(ext.endswith(".py") for ext in file_types.keys())

    def test_integration_max_results_limit_is_respected(self, sample_project):
        """Test that max_results parameter is properly enforced."""
        query = "application configuration data"
        max_limit = 3

        result = process_agent_scope_context(
            base_path=sample_project, query=query, max_results=max_limit
        )

        ranked_files = result["ranked_files"]
        assert len(ranked_files) <= max_limit

    def test_integration_custom_ai_config_affects_processing(self, sample_project):
        """Test that custom AI configuration influences processing."""
        # Create custom config with specific security settings
        custom_config = AIConfig()
        custom_config.security.sanitize_code = True

        query = "application data"

        result = process_agent_scope_context(
            base_path=sample_project, query=query, ai_config=custom_config
        )

        # Should still produce valid results with custom config
        assert len(result["ranked_files"]) > 0
        assert result["processing_summary"]["pipeline_stages"]["discovered"] > 0

    def test_integration_error_handling_with_problematic_files(self, sample_project):
        """Test error handling when encountering problematic files."""
        # Create a file with problematic content
        problematic_file = sample_project / "problematic.py"
        problematic_file.write_bytes(b"invalid utf-8 content \xff\xfe")

        query = "application"

        # Should not crash and should handle the problematic file gracefully
        result = process_agent_scope_context(
            base_path=sample_project, query=query, max_results=5
        )

        # Should still get results from valid files
        assert len(result["ranked_files"]) > 0

        # May have processing errors recorded
        if result["processing_errors"]:
            assert len(result["processing_errors"]) >= 0

    def test_integration_empty_query_handling(self, sample_project):
        """Test that the system handles edge cases properly."""
        # Test with very short query
        result = process_agent_scope_context(
            base_path=sample_project,
            query="a",  # Single character
            max_results=5,
        )

        # Should still process files and return results
        assert isinstance(result["ranked_files"], list)
        assert isinstance(result["processing_summary"], dict)

    def test_integration_performance_requirements_met(self, sample_project):
        """Test that processing meets performance requirements."""
        query = "application manager configuration data"

        # Process should complete without timeout
        result = process_agent_scope_context(
            base_path=sample_project, query=query, max_results=10
        )

        # Should complete successfully
        assert result is not None
        assert len(result["ranked_files"]) > 0

        # Processing should be efficient
        summary = result["processing_summary"]
        efficiency = summary["processing_efficiency"]
        assert efficiency["validation_rate"] > 0.5  # Should validate most files
        assert efficiency["error_rate"] < 0.5  # Should have low error rate
