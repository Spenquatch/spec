"""Integration test for slice P1.1a dependency analysis using real codebase.

Tests that dependency analysis works correctly against the actual spec-cli codebase
to validate SpecContext requirements generation.
"""

from pathlib import Path

from spec_cli.utils.dependency_analysis import (
    DependencyReport,
    analyze_current_usage,
    generate_dependency_report,
    validate_dependency_exists,
)

# Integration test constants
SPEC_CLI_ROOT = Path(__file__).parent.parent.parent / "spec_cli"
TARGET_DEPENDENCIES = ["settings", "console", "progress"]
MINIMUM_EXPECTED_USAGE_COUNTS = {
    "settings": 20,  # Should have many usage points
    "console": 15,  # Should have substantial usage
    "progress": 5,  # Should have some usage
}
EXPECTED_IMPORT_PATHS = {
    "settings": "spec_cli.config.settings",
    "console": "spec_cli.ui.console",
}


class TestDependencyAnalysisIntegration:
    """Integration tests for dependency analysis using real codebase."""

    def test_dependency_analysis_integration_when_real_codebase_then_validates_context_requirements(
        self,
    ):
        """End-to-end dependency analysis using actual spec-cli codebase."""
        # Execute comprehensive dependency analysis on real codebase
        reports = generate_dependency_report(TARGET_DEPENDENCIES, SPEC_CLI_ROOT)

        # Validate report structure
        assert len(reports) == len(TARGET_DEPENDENCIES)
        assert all(dep_name in reports for dep_name in TARGET_DEPENDENCIES)
        assert all(isinstance(report, DependencyReport) for report in reports.values())

        # Validate settings dependency (critical)
        settings_report = reports["settings"]
        assert settings_report.dependency_name == "settings"
        assert settings_report.exists is True, "SpecSettings should exist in codebase"
        assert (
            len(settings_report.usage_patterns)
            >= MINIMUM_EXPECTED_USAGE_COUNTS["settings"]
        )
        assert EXPECTED_IMPORT_PATHS["settings"] in settings_report.import_paths
        assert settings_report.requirements["required"] is True
        assert (
            "debug_enabled: bool"
            in settings_report.requirements["interface_requirements"]
        )
        assert len(settings_report.analysis_errors) == 0

        # Validate console dependency (high priority)
        console_report = reports["console"]
        assert console_report.dependency_name == "console"
        assert console_report.exists is True, "SpecConsole should exist in codebase"
        assert (
            len(console_report.usage_patterns)
            >= MINIMUM_EXPECTED_USAGE_COUNTS["console"]
        )
        assert EXPECTED_IMPORT_PATHS["console"] in console_report.import_paths
        assert console_report.requirements["required"] is True
        assert (
            "print_message(text: str) -> None"
            in console_report.requirements["interface_requirements"]
        )
        assert len(console_report.analysis_errors) == 0

        # Validate progress dependency (may not have unified interface yet)
        progress_report = reports["progress"]
        assert progress_report.dependency_name == "progress"
        assert (
            len(progress_report.usage_patterns)
            >= MINIMUM_EXPECTED_USAGE_COUNTS["progress"]
        )
        assert progress_report.requirements["required"] is True
        assert (
            "show_progress(current: int, total: int) -> None"
            in progress_report.requirements["interface_requirements"]
        )
        # Note: progress may not exist as unified interface yet, so don't assert exists=True

    def test_validate_dependency_exists_integration_when_real_dependencies_then_returns_correct_status(
        self,
    ):
        """Test dependency validation against real codebase imports."""
        # Test known existing dependency
        settings_exists = validate_dependency_exists("spec_cli.config.settings")
        assert settings_exists is True, "SpecSettings import should be valid"

        console_exists = validate_dependency_exists("spec_cli.ui.console")
        assert console_exists is True, "SpecConsole import should be valid"

        # Test non-existent dependency
        fake_exists = validate_dependency_exists("spec_cli.nonexistent.fake")
        assert fake_exists is False, "Non-existent import should be invalid"

    def test_analyze_current_usage_integration_when_real_files_then_finds_actual_usage(
        self,
    ):
        """Test usage analysis against real codebase files."""
        # Analyze settings usage in real codebase
        settings_files = analyze_current_usage("settings", SPEC_CLI_ROOT)

        # Validate realistic usage counts
        assert len(settings_files) >= MINIMUM_EXPECTED_USAGE_COUNTS["settings"]

        # Validate expected key files are included
        expected_files_patterns = [
            "config/settings.py",  # Settings implementation
            "ui/console.py",  # Console uses settings
            "git/repository.py",  # Repository uses settings
        ]

        settings_files_str = [str(f) for f in settings_files]
        found_patterns = []
        for pattern in expected_files_patterns:
            if any(pattern in file_str for file_str in settings_files_str):
                found_patterns.append(pattern)

        assert len(found_patterns) >= 2, (
            f"Should find at least 2 expected patterns, found: {found_patterns}"
        )

    def test_cross_slice_integration_when_dependency_requirements_then_validates_p1_1b_compatibility(
        self,
    ):
        """Validate dependency requirements are compatible with P1.1b SpecContext implementation."""
        reports = generate_dependency_report(TARGET_DEPENDENCIES, SPEC_CLI_ROOT)

        # Validate SpecContext interface requirements are complete
        for _dep_name, report in reports.items():
            requirements = report.requirements

            # Essential fields for SpecContext implementation
            assert "name" in requirements
            assert "required" in requirements
            assert "interface_requirements" in requirements
            assert "injection_points" in requirements

            # Interface requirements should be non-empty for required dependencies
            if requirements["required"]:
                assert len(requirements["interface_requirements"]) > 0
                assert len(requirements["injection_points"]) > 0

                # Each interface requirement should be a valid method signature or property
                for interface_req in requirements["interface_requirements"]:
                    # Check for either property type (contains ":") or method signature (contains "->")
                    has_type_info = ":" in interface_req or "->" in interface_req
                    assert has_type_info, (
                        f"Interface requirement should have type information: {interface_req}"
                    )

    def test_singleton_pattern_detection_integration_when_current_codebase_then_identifies_migration_points(
        self,
    ):
        """Validate detection of current singleton usage patterns for migration planning."""
        reports = generate_dependency_report(TARGET_DEPENDENCIES, SPEC_CLI_ROOT)

        # Validate injection points contain actual file paths from codebase
        all_injection_points = []
        for report in reports.values():
            all_injection_points.extend(report.requirements.get("injection_points", []))

        # Should have substantial number of injection points across dependencies
        assert len(all_injection_points) >= 50, (
            "Should identify many injection points for migration"
        )

        # Validate injection points reference real files
        for injection_point in all_injection_points[:5]:  # Check first 5
            assert "file" in injection_point
            assert "type" in injection_point
            file_path = injection_point["file"]

            # File path might be absolute, convert to relative for validation
            if file_path.startswith("/"):
                # Extract relative path from absolute path
                relative_path = (
                    file_path.split("spec_cli/")[-1]
                    if "spec_cli/" in file_path
                    else file_path
                )
                assert relative_path != file_path, (
                    f"Should contain spec_cli in path: {file_path}"
                )
            else:
                assert file_path.startswith("spec_cli/"), (
                    f"Relative path should start with spec_cli/: {file_path}"
                )

            # Validate file actually exists (use absolute path)
            if file_path.startswith("/"):
                full_path = Path(file_path)
            else:
                full_path = SPEC_CLI_ROOT.parent / file_path
            assert full_path.exists(), f"Injection point file should exist: {full_path}"

    def test_context_injection_requirements_analysis_when_comprehensive_scan_then_validates_complete_coverage(
        self,
    ):
        """Validate analysis identifies specific context injection requirements."""
        reports = generate_dependency_report(TARGET_DEPENDENCIES, SPEC_CLI_ROOT)

        # Aggregate all requirements across dependencies
        total_usage_count = sum(
            report.requirements.get("usage_count", 0) for report in reports.values()
        )
        total_injection_points = sum(
            len(report.requirements.get("injection_points", []))
            for report in reports.values()
        )

        # Validate comprehensive coverage
        assert total_usage_count >= 80, (
            f"Should identify substantial usage patterns, found: {total_usage_count}"
        )
        assert total_injection_points >= 60, (
            f"Should identify many injection points, found: {total_injection_points}"
        )

        # Validate key architectural components are included
        all_files = set()
        for report in reports.values():
            for injection_point in report.requirements.get("injection_points", []):
                all_files.add(injection_point["file"])

        expected_component_patterns = [
            "cli/",  # CLI layer
            "ui/",  # UI layer
            "config/",  # Configuration layer
            "git/",  # Git operations
            "templates/",  # Template processing
            "file_processing/",  # File processing
        ]

        found_components = []
        for pattern in expected_component_patterns:
            if any(pattern in file_path for file_path in all_files):
                found_components.append(pattern)

        assert len(found_components) >= 4, (
            f"Should cover major architectural components, found: {found_components}"
        )

    def test_dependency_interface_completeness_when_real_usage_then_validates_sufficient_methods(
        self,
    ):
        """Validate that generated interfaces cover real usage patterns comprehensively."""
        reports = generate_dependency_report(TARGET_DEPENDENCIES, SPEC_CLI_ROOT)

        # Settings interface validation
        settings_interface = reports["settings"].requirements["interface_requirements"]
        essential_settings_methods = [
            "debug_enabled",
            "console_width",
            "use_color",
            "get_setting",
        ]

        for method in essential_settings_methods:
            assert any(
                method in interface_req for interface_req in settings_interface
            ), f"Settings interface should include {method} method"

        # Console interface validation
        console_interface = reports["console"].requirements["interface_requirements"]
        essential_console_methods = [
            "print_message",
            "print_error",
            "get_width",
            "supports_color",
        ]

        for method in essential_console_methods:
            assert any(
                method in interface_req for interface_req in console_interface
            ), f"Console interface should include {method} method"

        # Progress interface validation
        progress_interface = reports["progress"].requirements["interface_requirements"]
        essential_progress_methods = ["show_progress", "update_status", "finish"]

        for method in essential_progress_methods:
            assert any(
                method in interface_req for interface_req in progress_interface
            ), f"Progress interface should include {method} method"
