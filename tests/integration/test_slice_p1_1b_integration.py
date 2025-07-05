"""Integration test for Slice P1.1b - SpecContext implementation.

End-to-end test using actual dependency requirements from P1.1a analysis
to validate SpecContext works with real dependency objects and scenarios.
"""

from pathlib import Path
from unittest.mock import Mock

import pytest

from spec_cli.core.context import (
    SpecConsoleInterface,
    SpecContext,
    SpecContextError,
    SpecProgressInterface,
    SpecSettingsInterface,
)
from spec_cli.utils.dependency_analysis import (
    DependencyReport,
    DependencyUsage,
)

# Integration test constants
TEST_CODEBASE_PATH = Path("spec_cli")
EXPECTED_DEPENDENCY_COUNT = 3
SETTINGS_DEPENDENCY_NAME = "settings"
CONSOLE_DEPENDENCY_NAME = "console"
PROGRESS_DEPENDENCY_NAME = "progress"
EXPECTED_CONTEXT_ATTRIBUTES = ["settings", "console", "progress"]


class TestSpecContextIntegration:
    """Integration test for SpecContext with P1.1a dependency requirements."""

    def test_spec_context_integration_when_p1_1a_requirements_then_implements_complete_context(
        self,
    ):
        """End-to-end test using actual dependency requirements from P1.1a analysis."""
        # Create dependency instances based on P1.1a interface requirements
        settings = SpecSettingsInterface()
        settings.debug_enabled = True
        settings.console_width = 120
        settings.use_color = True
        settings.root_path = Path("/test/project")
        settings.spec_dir = Path("/test/project/.spec")
        settings.specs_dir = Path("/test/project/.specs")

        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        # Create SpecContext with all P1.1a required dependencies
        context = SpecContext(settings=settings, console=console, progress=progress)

        # Validate context structure matches P1.1a requirements
        assert hasattr(context, "settings")
        assert hasattr(context, "console")
        assert hasattr(context, "progress")

        # Validate settings interface matches P1.1a specification
        assert context.settings.debug_enabled is True
        assert context.settings.console_width == 120
        assert context.settings.use_color is True
        assert isinstance(context.settings.root_path, Path)
        assert isinstance(context.settings.spec_dir, Path)
        assert isinstance(context.settings.specs_dir, Path)

        # Test settings interface methods from P1.1a
        setting_value = context.settings.get_setting("debug_enabled")
        assert setting_value is True

        validation_result = context.settings.validate_configuration()
        assert isinstance(validation_result, dict)

        # Test console interface methods from P1.1a
        assert context.console.get_width() == 80  # Default implementation
        assert context.console.supports_color() is True

        # These should not raise exceptions (P1.1a interface compliance)
        context.console.print_message("Integration test message")
        context.console.print_error("Integration test error")
        context.console.print_success("Integration test success")
        context.console.print_warning("Integration test warning")

        # Test progress interface methods from P1.1a
        context.progress.show_progress(50, 100, "Integration test progress")
        context.progress.update_status("Integration test status")

        operation_id = context.progress.start_operation(
            "Integration test operation", 100
        )
        assert isinstance(operation_id, str)

        context.progress.finish_operation(operation_id)

        # Test immutability (critical P1.1a requirement)
        with pytest.raises(AttributeError):
            context.settings = Mock()  # type: ignore

        # Test context modification methods (P1.1a pattern requirements)
        new_context = context.with_settings(debug_enabled=False)
        assert new_context.settings.debug_enabled is False
        assert context.settings.debug_enabled is True  # Original unchanged

        # Test context hashing for equality (P1.1a requirement)
        context_hash = context.get_context_hash()
        assert isinstance(context_hash, str)
        assert len(context_hash) == 64  # SHA-256

        # Test context equality
        identical_context = SpecContext(
            settings=settings, console=console, progress=progress
        )
        assert context == identical_context

    def test_spec_context_integration_when_dependency_analysis_then_validates_requirements(
        self,
    ):
        """Test SpecContext implementation against actual dependency analysis."""
        # Use dependency analysis to validate our implementation
        # This simulates the P1.1a analysis process
        dependency_names = [
            SETTINGS_DEPENDENCY_NAME,
            CONSOLE_DEPENDENCY_NAME,
            PROGRESS_DEPENDENCY_NAME,
        ]

        # Create mock dependency report (simulating P1.1a analysis results)
        mock_reports = {}
        for dep_name in dependency_names:
            mock_reports[dep_name] = DependencyReport(
                dependency_name=dep_name,
                exists=True,
                usage_patterns=[
                    DependencyUsage(
                        file_path=f"/test/{dep_name}_usage.py",
                        line_number=10,
                        usage_type="reference",
                        context=f"File references {dep_name}",
                    )
                ],
                import_paths={f"spec_cli.{dep_name}"},
                requirements={
                    "name": dep_name,
                    "required": True,
                    "usage_count": 1,
                    "interface_requirements": [],
                    "injection_points": [],
                },
                analysis_errors=[],
            )

        # Validate that our SpecContext can fulfill all dependency requirements
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context = SpecContext(settings=settings, console=console, progress=progress)

        # Verify context provides all required dependencies from analysis
        assert len(mock_reports) == EXPECTED_DEPENDENCY_COUNT
        for dep_name, report in mock_reports.items():
            assert report.exists is True
            assert report.requirements["required"] is True

            # Verify context has corresponding attribute
            if dep_name == SETTINGS_DEPENDENCY_NAME:
                assert hasattr(context, "settings")
                assert context.settings is not None
            elif dep_name == CONSOLE_DEPENDENCY_NAME:
                assert hasattr(context, "console")
                assert context.console is not None
            elif dep_name == PROGRESS_DEPENDENCY_NAME:
                assert hasattr(context, "progress")
                assert context.progress is not None

    def test_spec_context_integration_when_real_world_scenario_then_handles_workflow(
        self,
    ):
        """Test SpecContext in realistic workflow scenario."""
        # Simulate a real workflow that would use SpecContext
        # This represents how P1.1b will be used in actual CLI operations

        # Create context with specific configuration for workflow
        settings = SpecSettingsInterface()
        settings.debug_enabled = True
        settings.console_width = 100
        settings.root_path = Path("/test/project")

        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        workflow_context = SpecContext(
            settings=settings, console=console, progress=progress
        )

        # Simulate workflow steps using context dependencies

        # Step 1: Configuration validation
        validation_result = workflow_context.settings.validate_configuration()
        assert isinstance(validation_result, dict)

        # Step 2: Console output
        workflow_context.console.print_message("Starting workflow")
        assert workflow_context.console.supports_color()

        # Step 3: Progress tracking
        operation_id = workflow_context.progress.start_operation(
            "Workflow operation", 100
        )
        workflow_context.progress.show_progress(25, 100, "Processing files")
        workflow_context.progress.update_status("Halfway complete")
        workflow_context.progress.show_progress(100, 100, "Complete")
        workflow_context.progress.finish_operation(operation_id)

        # Step 4: Context modification for different workflow phase
        production_context = workflow_context.with_settings(
            debug_enabled=False, console_width=80
        )

        assert production_context.settings.debug_enabled is False
        assert production_context.settings.console_width == 80
        assert workflow_context.settings.debug_enabled is True  # Original unchanged

        # Step 5: Context comparison
        assert production_context != workflow_context
        assert (
            production_context.get_context_hash() != workflow_context.get_context_hash()
        )

        # Step 6: Validate immutability throughout workflow
        with pytest.raises(AttributeError):
            workflow_context.settings = Mock()  # type: ignore

        with pytest.raises(AttributeError):
            production_context.console = Mock()  # type: ignore

    def test_spec_context_integration_when_error_scenarios_then_handles_gracefully(
        self,
    ):
        """Test SpecContext error handling in integration scenarios."""
        # Test construction with invalid dependencies
        with pytest.raises(
            SpecContextError, match="SpecContext requires settings dependency"
        ):
            SpecContext(
                settings=None,  # type: ignore
                console=SpecConsoleInterface(),
                progress=SpecProgressInterface(),
            )

        # Test modification with invalid inputs
        valid_context = SpecContext(
            settings=SpecSettingsInterface(),
            console=SpecConsoleInterface(),
            progress=SpecProgressInterface(),
        )

        with pytest.raises(
            SpecContextError, match="Console replacement cannot be None"
        ):
            valid_context.with_console(None)  # type: ignore

        with pytest.raises(
            SpecContextError, match="Progress replacement cannot be None"
        ):
            valid_context.with_progress(None)  # type: ignore

        # Verify context remains valid after error scenarios
        assert valid_context.settings is not None
        assert valid_context.console is not None
        assert valid_context.progress is not None

    def test_spec_context_integration_when_interface_compliance_then_meets_p1_1a_specification(
        self,
    ):
        """Test that SpecContext interfaces meet P1.1a specification requirements."""
        # Create context and verify all P1.1a interface requirements are met
        settings = SpecSettingsInterface()
        console = SpecConsoleInterface()
        progress = SpecProgressInterface()

        context = SpecContext(settings=settings, console=console, progress=progress)

        # P1.1a SpecSettingsInterface requirements
        required_settings_attrs = [
            "debug_enabled",
            "console_width",
            "use_color",
            "root_path",
            "spec_dir",
            "specs_dir",
        ]
        for attr in required_settings_attrs:
            assert hasattr(context.settings, attr), (
                f"Missing settings attribute: {attr}"
            )

        required_settings_methods = ["get_setting", "validate_configuration"]
        for method in required_settings_methods:
            assert hasattr(context.settings, method), (
                f"Missing settings method: {method}"
            )
            assert callable(getattr(context.settings, method))

        # P1.1a SpecConsoleInterface requirements
        required_console_methods = [
            "print_message",
            "print_error",
            "print_success",
            "print_warning",
            "get_width",
            "supports_color",
            "capture_output",
        ]
        for method in required_console_methods:
            assert hasattr(context.console, method), f"Missing console method: {method}"
            assert callable(getattr(context.console, method))

        # P1.1a SpecProgressInterface requirements
        required_progress_methods = [
            "show_progress",
            "update_status",
            "start_operation",
            "finish_operation",
            "create_spinner",
        ]
        for method in required_progress_methods:
            assert hasattr(context.progress, method), (
                f"Missing progress method: {method}"
            )
            assert callable(getattr(context.progress, method))

        # Test all methods are callable without exceptions
        context.settings.get_setting("test_key")
        context.settings.validate_configuration()

        context.console.print_message("test")
        context.console.get_width()
        context.console.supports_color()

        context.progress.show_progress(1, 10)
        context.progress.update_status("test")
        op_id = context.progress.start_operation("test")
        context.progress.finish_operation(op_id)
