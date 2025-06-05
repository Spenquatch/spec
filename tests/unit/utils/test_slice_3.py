"""Tests for Slice 3: Architecture dependency validation.

This test module verifies the dependency validator that ensures the codebase
follows the expected architecture hierarchy: Utils → Config → Core → CLI.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from spec_cli.utils.dependency_validator import (
    DependencyValidator,
    ImportViolation,
    LayerDefinition,
    validate_import_hierarchy,
)


class TestLayerDefinition:
    """Test LayerDefinition class."""

    def test_layer_definition_when_initialized_then_stores_attributes(self):
        """Test that LayerDefinition stores name and allowed imports."""
        layer = LayerDefinition("utils", [])

        assert layer.name == "utils"
        assert layer.allowed_imports == []

    def test_layer_definition_when_has_allowed_imports_then_stores_them(self):
        """Test LayerDefinition with allowed imports."""
        layer = LayerDefinition("config", ["utils"])

        assert layer.name == "config"
        assert layer.allowed_imports == ["utils"]


class TestImportViolation:
    """Test ImportViolation class."""

    def test_import_violation_when_initialized_then_stores_attributes(self):
        """Test that ImportViolation stores all violation details."""
        violation = ImportViolation(
            file_path=Path("spec_cli/utils/test.py"),
            importing_layer="utils",
            imported_layer="config",
            line_number=10,
        )

        assert violation.file_path == Path("spec_cli/utils/test.py")
        assert violation.importing_layer == "utils"
        assert violation.imported_layer == "config"
        assert violation.line_number == 10

    def test_import_violation_when_to_dict_then_returns_formatted_dict(self):
        """Test ImportViolation.to_dict() returns proper format."""
        violation = ImportViolation(
            file_path=Path("spec_cli/utils/helper.py"),
            importing_layer="utils",
            imported_layer="core",
            line_number=15,
        )

        result = violation.to_dict()

        assert result["file"] == "spec_cli/utils/helper.py"
        assert result["importing_layer"] == "utils"
        assert result["imported_layer"] == "core"
        assert result["line"] == 15
        assert result["message"] == "utils layer imports from core layer"


class TestDependencyValidator:
    """Test DependencyValidator class."""

    @pytest.fixture
    def validator(self, tmp_path):
        """Create validator with test hierarchy."""
        return DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

    def test_dependency_validator_when_initialized_then_creates_layer_definitions(
        self, validator
    ):
        """Test that validator creates correct layer definitions."""
        assert len(validator.layer_definitions) == 4

        # Utils can't import from anything
        assert validator.layer_definitions["utils"].allowed_imports == []

        # Config can only import from utils
        assert validator.layer_definitions["config"].allowed_imports == ["utils"]

        # Core can import from utils and config
        assert validator.layer_definitions["core"].allowed_imports == [
            "utils",
            "config",
        ]

        # CLI can import from all lower layers
        assert validator.layer_definitions["cli"].allowed_imports == [
            "utils",
            "config",
            "core",
        ]

    def test_get_layer_from_path_when_utils_path_then_returns_utils(self, tmp_path):
        """Test layer detection for utils module."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        # Create test path
        test_path = tmp_path / "spec_cli" / "utils" / "helper.py"

        layer = validator._get_layer_from_path(test_path)

        assert layer == "utils"

    def test_get_layer_from_path_when_config_path_then_returns_config(self, tmp_path):
        """Test layer detection for config module."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        test_path = tmp_path / "spec_cli" / "config" / "settings.py"

        layer = validator._get_layer_from_path(test_path)

        assert layer == "config"

    def test_get_layer_from_path_when_file_processing_then_returns_core(self, tmp_path):
        """Test that file_processing is mapped to core layer."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        test_path = tmp_path / "spec_cli" / "file_processing" / "processor.py"

        layer = validator._get_layer_from_path(test_path)

        assert layer == "core"

    def test_get_layer_from_path_when_ui_module_then_returns_cli(self, tmp_path):
        """Test that ui module is mapped to cli layer."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        test_path = tmp_path / "spec_cli" / "ui" / "console.py"

        layer = validator._get_layer_from_path(test_path)

        assert layer == "cli"

    def test_get_layer_from_path_when_logging_module_then_returns_utils(self, tmp_path):
        """Test that logging module is mapped to utils layer."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        test_path = tmp_path / "spec_cli" / "logging" / "debug.py"

        layer = validator._get_layer_from_path(test_path)

        assert layer == "utils"

    def test_get_layer_from_path_when_outside_spec_cli_then_returns_none(
        self, tmp_path
    ):
        """Test layer detection for files outside spec_cli."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        test_path = tmp_path / "tests" / "test_something.py"

        layer = validator._get_layer_from_path(test_path)

        assert layer is None

    def test_extract_imports_when_valid_python_file_then_extracts_imports(
        self, tmp_path
    ):
        """Test import extraction from Python file."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        # Create test file with imports
        test_file = tmp_path / "test.py"
        test_file.write_text("""
import os
from pathlib import Path
from spec_cli.utils import helper
from spec_cli.config.settings import Settings
import spec_cli.core.workflow
""")

        imports = validator._extract_imports(test_file)

        # Should only extract spec_cli imports
        assert len(imports) == 3
        assert ("spec_cli.utils", 4) in imports
        assert ("spec_cli.config.settings", 5) in imports
        assert ("spec_cli.core.workflow", 6) in imports

    def test_extract_imports_when_file_not_found_then_returns_empty(self, tmp_path):
        """Test import extraction when file doesn't exist."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        test_file = tmp_path / "nonexistent.py"

        imports = validator._extract_imports(test_file)

        assert imports == []

    def test_extract_imports_when_syntax_error_then_returns_empty(self, tmp_path):
        """Test import extraction with invalid Python syntax."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        test_file = tmp_path / "invalid.py"
        test_file.write_text("this is not valid python syntax {[}")

        imports = validator._extract_imports(test_file)

        assert imports == []

    def test_check_import_validity_when_valid_import_then_returns_none(self, tmp_path):
        """Test that valid imports return no violation."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        # Config importing from utils is valid
        importing_file = tmp_path / "spec_cli" / "config" / "settings.py"

        violation = validator._check_import_validity(
            importing_file, "spec_cli.utils.helper", 10
        )

        assert violation is None

    def test_check_import_validity_when_invalid_import_then_returns_violation(
        self, tmp_path
    ):
        """Test that invalid imports return violation."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        # Utils importing from config is invalid
        importing_file = tmp_path / "spec_cli" / "utils" / "helper.py"

        violation = validator._check_import_validity(
            importing_file, "spec_cli.config.settings", 10
        )

        assert violation is not None
        assert violation.importing_layer == "utils"
        assert violation.imported_layer == "config"
        assert violation.line_number == 10

    def test_check_import_validity_when_same_layer_import_then_returns_none(
        self, tmp_path
    ):
        """Test that imports within same layer are allowed."""
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])

        # Utils importing from utils is valid
        importing_file = tmp_path / "spec_cli" / "utils" / "helper.py"

        violation = validator._check_import_validity(
            importing_file, "spec_cli.utils.other_helper", 10
        )

        assert violation is None

    def test_validate_import_hierarchy_when_no_violations_then_returns_empty(
        self, tmp_path
    ):
        """Test validation with clean architecture."""
        # Create directory structure
        spec_cli_dir = tmp_path / "spec_cli"
        utils_dir = spec_cli_dir / "utils"
        config_dir = spec_cli_dir / "config"

        utils_dir.mkdir(parents=True)
        config_dir.mkdir(parents=True)

        # Create files with valid imports
        utils_file = utils_dir / "helper.py"
        utils_file.write_text("# No imports")

        config_file = config_dir / "settings.py"
        config_file.write_text("from spec_cli.utils import helper")

        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])
        violations = validator.validate_import_hierarchy()

        assert violations == []

    def test_validate_import_hierarchy_when_violations_exist_then_returns_messages(
        self, tmp_path
    ):
        """Test validation with architecture violations."""
        # Create directory structure
        spec_cli_dir = tmp_path / "spec_cli"
        utils_dir = spec_cli_dir / "utils"
        config_dir = spec_cli_dir / "config"

        utils_dir.mkdir(parents=True)
        config_dir.mkdir(parents=True)

        # Create file with invalid import
        utils_file = utils_dir / "helper.py"
        utils_file.write_text("from spec_cli.config import settings")

        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])
        violations = validator.validate_import_hierarchy()

        assert len(violations) == 1
        assert "utils imports from config" in violations[0]

    def test_generate_validation_report_when_clean_architecture_then_success(
        self, tmp_path
    ):
        """Test report generation with clean architecture."""
        # Create minimal structure
        spec_cli_dir = tmp_path / "spec_cli"
        utils_dir = spec_cli_dir / "utils"
        utils_dir.mkdir(parents=True)

        utils_file = utils_dir / "helper.py"
        utils_file.write_text("# Clean file")

        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])
        report = validator.generate_validation_report()

        assert report["success"] is True
        assert report["violations"] == []
        assert report["statistics"]["total_violations"] == 0
        assert report["statistics"]["compliance_percentage"] == 100

    def test_generate_validation_report_when_violations_then_includes_details(
        self, tmp_path
    ):
        """Test report generation with violations."""
        # Create structure with violation
        spec_cli_dir = tmp_path / "spec_cli"
        utils_dir = spec_cli_dir / "utils"
        utils_dir.mkdir(parents=True)

        utils_file = utils_dir / "helper.py"
        utils_file.write_text("from spec_cli.config import settings")

        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])
        report = validator.generate_validation_report()

        assert report["success"] is False
        assert len(report["violations"]) == 1
        assert report["statistics"]["total_violations"] == 1
        assert report["statistics"]["compliance_percentage"] < 100


class TestConvenienceFunction:
    """Test the convenience function."""

    def test_validate_import_hierarchy_function_when_called_then_uses_defaults(self):
        """Test convenience function with default parameters."""
        with patch(
            "spec_cli.utils.dependency_validator.DependencyValidator"
        ) as mock_validator_class:
            mock_validator = Mock()
            mock_validator.validate_import_hierarchy.return_value = []
            mock_validator_class.return_value = mock_validator

            result = validate_import_hierarchy()

            # Should use current directory and default hierarchy
            mock_validator_class.assert_called_once()
            call_args = mock_validator_class.call_args[0]
            assert isinstance(call_args[0], Path)
            assert call_args[1] == ["utils", "config", "core", "cli"]

            assert result == []

    def test_validate_import_hierarchy_function_when_custom_params_then_uses_them(self):
        """Test convenience function with custom parameters."""
        with patch(
            "spec_cli.utils.dependency_validator.DependencyValidator"
        ) as mock_validator_class:
            mock_validator = Mock()
            mock_validator.validate_import_hierarchy.return_value = ["violation"]
            mock_validator_class.return_value = mock_validator

            custom_path = Path("/custom/path")
            custom_hierarchy = ["layer1", "layer2", "layer3"]

            result = validate_import_hierarchy(custom_path, custom_hierarchy)

            mock_validator_class.assert_called_once_with(custom_path, custom_hierarchy)
            assert result == ["violation"]


class TestIntegration:
    """Integration tests for the dependency validator."""

    def test_full_validation_workflow_when_mixed_imports_then_detects_violations(
        self, tmp_path
    ):
        """Integration test with realistic codebase structure."""
        # Create realistic directory structure
        spec_cli = tmp_path / "spec_cli"

        # Create all layer directories
        utils_dir = spec_cli / "utils"
        config_dir = spec_cli / "config"
        core_dir = spec_cli / "core"
        cli_dir = spec_cli / "cli"
        file_proc_dir = spec_cli / "file_processing"
        ui_dir = spec_cli / "ui"

        for directory in [
            utils_dir,
            config_dir,
            core_dir,
            cli_dir,
            file_proc_dir,
            ui_dir,
        ]:
            directory.mkdir(parents=True)

        # Create files with various imports

        # Utils file - should not import from higher layers
        (utils_dir / "helper.py").write_text("""
# Valid - no imports from higher layers
def utility_function():
    pass
""")

        # Config file - can import from utils
        (config_dir / "settings.py").write_text("""
from spec_cli.utils import helper  # Valid

class Settings:
    pass
""")

        # Core file - can import from utils and config
        (core_dir / "workflow.py").write_text("""
from spec_cli.utils import helper  # Valid
from spec_cli.config import settings  # Valid

class Workflow:
    pass
""")

        # CLI file - can import from all lower layers
        (cli_dir / "command.py").write_text("""
from spec_cli.utils import helper  # Valid
from spec_cli.config import settings  # Valid
from spec_cli.core import workflow  # Valid
from spec_cli.ui import console  # Valid - same level

class Command:
    pass
""")

        # File processing (maps to core) - introduce violation
        (file_proc_dir / "processor.py").write_text("""
from spec_cli.cli import command  # INVALID - core importing from cli

class Processor:
    pass
""")

        # UI (maps to cli) - valid imports
        (ui_dir / "console.py").write_text("""
from spec_cli.utils import helper  # Valid
from spec_cli.config import settings  # Valid

class Console:
    pass
""")

        # Run validation
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])
        violations = validator.validate_import_hierarchy()

        # Should detect the one violation
        assert len(violations) == 1
        assert "core imports from cli" in violations[0]
        assert "file_processing/processor.py" in violations[0]

    def test_report_generation_with_realistic_codebase_then_provides_statistics(
        self, tmp_path
    ):
        """Integration test for report generation with statistics."""
        # Create structure
        spec_cli = tmp_path / "spec_cli"
        utils_dir = spec_cli / "utils"
        config_dir = spec_cli / "config"

        utils_dir.mkdir(parents=True)
        config_dir.mkdir(parents=True)

        # Create multiple files
        (utils_dir / "helper1.py").write_text("# No imports")
        (utils_dir / "helper2.py").write_text("import os")
        (config_dir / "settings.py").write_text("from spec_cli.utils import helper1")
        (config_dir / "loader.py").write_text("""
from spec_cli.utils import helper1
from spec_cli.utils import helper2
""")

        # Generate report
        validator = DependencyValidator(tmp_path, ["utils", "config", "core", "cli"])
        report = validator.generate_validation_report()

        # Verify statistics
        assert report["success"] is True
        assert report["statistics"]["total_files"] == 4
        assert (
            report["statistics"]["total_imports"] == 3
        )  # Only spec_cli imports counted
        assert report["statistics"]["total_violations"] == 0
        assert report["statistics"]["compliance_percentage"] == 100.0

        # Verify layer statistics
        layer_stats = report["statistics"]["layer_statistics"]
        assert layer_stats["utils"]["files"] == 2
        assert layer_stats["config"]["files"] == 2
        assert layer_stats["config"]["imports"] == 3
