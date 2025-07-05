"""Integration tests for Slice P2.1a Click Framework Pattern Analysis."""

from pathlib import Path

import pytest

from spec_cli.utils.click_analysis import (
    analyze_click_patterns,
    validate_context_storage_capability,
)


class TestClickAnalysisIntegration:
    """Integration tests for Click pattern analysis with real CLI directory."""

    def test_click_analysis_integration_when_real_cli_then_identifies_all_integration_requirements(
        self,
    ):
        """End-to-end test analyzing actual spec-cli Click usage."""
        # Use actual CLI directory from the project
        cli_dir = Path("spec_cli/cli")

        # Verify CLI directory exists
        assert cli_dir.exists(), f"CLI directory not found: {cli_dir}"
        assert cli_dir.is_dir(), f"CLI path is not a directory: {cli_dir}"

        # Run analysis on real CLI structure
        report = analyze_click_patterns(cli_dir)

        # Verify comprehensive analysis results
        assert len(report.commands_found) > 0, "No Click commands found in CLI"
        assert len(report.decorators_used) > 0, "No Click decorators found in CLI"
        assert len(report.integration_requirements) > 0, (
            "No integration requirements generated"
        )

        # Verify specific patterns expected in spec-cli
        assert "click_import" in report.decorators_used, "Missing click import pattern"
        assert any("group" in cmd for cmd in report.commands_found), (
            "Missing Click group pattern"
        )
        assert any("command" in cmd for cmd in report.commands_found), (
            "Missing Click command pattern"
        )

        # Verify context usage detection
        if report.context_usage:
            # If context usage found, verify it's properly documented
            for file_path, usage_patterns in report.context_usage.items():
                assert isinstance(usage_patterns, list), (
                    f"Invalid usage pattern format in {file_path}"
                )
                assert len(usage_patterns) > 0, f"Empty usage patterns in {file_path}"
                for pattern in usage_patterns:
                    assert isinstance(pattern, str), (
                        f"Invalid pattern type in {file_path}: {pattern}"
                    )

        # Verify integration requirements completeness
        requirements_text = " ".join(report.integration_requirements)

        # Must include core integration requirements
        assert "Click framework integration" in requirements_text, (
            "Missing framework integration requirement"
        )
        assert "storage" in requirements_text.lower(), "Missing storage requirement"

        # Verify storage capabilities were tested
        assert len(report.storage_capabilities) > 0, "No storage capabilities tested"
        if "custom_data_storage" in report.storage_capabilities:
            # Storage capability test was performed
            storage_result = report.storage_capabilities["custom_data_storage"]
            assert isinstance(storage_result, bool), (
                "Invalid storage capability result type"
            )

        # Verify Click decorator analysis depth
        expected_decorator_patterns = {
            "click_import",  # Basic Click import
            "click_group",  # Main CLI group
            "click_command",  # Individual commands
            "click_option",  # Command options
            "click_pass_context",  # Context passing
        }

        found_patterns = set(report.decorators_used)
        common_patterns = expected_decorator_patterns.intersection(found_patterns)
        assert len(common_patterns) >= 3, (
            f"Expected at least 3 common patterns, found: {common_patterns}"
        )

        # Verify CLI structure analysis
        assert isinstance(report.cli_structure, dict), (
            "CLI structure must be a dictionary"
        )

        print(
            f"✓ Analysis complete: {len(report.commands_found)} commands, {len(report.decorators_used)} decorators"
        )
        print(f"✓ Context usage: {len(report.context_usage)} files")
        print(
            f"✓ Integration requirements: {len(report.integration_requirements)} items"
        )
        print(f"✓ Storage capabilities: {report.storage_capabilities}")

    def test_click_context_storage_validation_integration(self):
        """Integration test for Click context storage capabilities."""
        # Test actual Click context storage functionality
        storage_capable = validate_context_storage_capability()

        # Click framework should support context storage
        assert storage_capable is True, "Click context storage validation failed"

        # Verify this result is consistent with analysis
        cli_dir = Path("spec_cli/cli")
        if cli_dir.exists():
            report = analyze_click_patterns(cli_dir)

            # Storage capability should be documented in report
            if "custom_data_storage" in report.storage_capabilities:
                assert (
                    report.storage_capabilities["custom_data_storage"]
                    == storage_capable
                )

            # Integration requirements should reflect storage capability
            requirements_text = " ".join(report.integration_requirements)
            if storage_capable:
                assert "storage verified" in requirements_text.lower()

        print(f"✓ Context storage validation: {storage_capable}")

    def test_real_cli_file_analysis_integration(self):
        """Integration test analyzing real CLI files for specific patterns."""
        cli_dir = Path("spec_cli/cli")

        if not cli_dir.exists():
            pytest.skip("CLI directory not available for integration testing")

        # Analyze specific CLI files
        app_file = cli_dir / "app.py"
        if app_file.exists():
            # Run analysis and verify app.py patterns are detected
            report = analyze_click_patterns(cli_dir)

            # app.py should contribute to Click patterns
            assert len(report.decorators_used) > 0, (
                "No decorators found in app.py analysis"
            )

            # Should find main group pattern
            if "click_group" in report.decorators_used:
                assert "group" in report.commands_found, (
                    "Group decorator found but no group command"
                )

        # Check commands directory
        commands_dir = cli_dir / "commands"
        if commands_dir.exists():
            command_files = list(commands_dir.glob("*.py"))
            if command_files:
                # Commands directory exists with Python files
                report = analyze_click_patterns(cli_dir)

                # Should find command patterns from commands directory
                assert len(report.decorators_used) > 0, (
                    "No patterns found in commands directory"
                )

        print("✓ Real CLI file analysis complete")

    def test_cross_slice_integration_requirements_validation(self):
        """Validate that Click analysis provides sufficient requirements for P2.1b."""
        cli_dir = Path("spec_cli/cli")

        if not cli_dir.exists():
            pytest.skip("CLI directory not available for cross-slice validation")

        report = analyze_click_patterns(cli_dir)

        # Verify P2.1b implementation requirements are satisfied
        requirements_text = " ".join(report.integration_requirements)

        # P2.1b needs to know about context storage
        assert "context" in requirements_text.lower(), (
            "Missing context requirements for P2.1b"
        )

        # P2.1b needs to know about decorator compatibility
        if any("option" in dec for dec in report.decorators_used):
            assert "option" in requirements_text.lower(), (
                "Missing option decorator requirements"
            )

        # P2.1b needs storage capability validation
        assert report.storage_capabilities, "Missing storage capabilities for P2.1b"

        # P2.1b needs integration approach
        assert len(report.integration_requirements) >= 3, (
            "Insufficient requirements for P2.1b implementation"
        )

        print("✓ Cross-slice integration requirements validated for P2.1b")

    def test_dependency_injection_context_analysis_integration(self):
        """Integration test validating Click analysis supports DI migration context."""
        cli_dir = Path("spec_cli/cli")

        if not cli_dir.exists():
            pytest.skip("CLI directory not available for DI context analysis")

        report = analyze_click_patterns(cli_dir)

        # Verify analysis identifies patterns needed for dependency injection

        # 1. Context injection opportunities
        if report.context_usage:
            # Found existing context usage - good for DI migration
            assert len(report.context_usage) > 0, "Context usage found but empty"

            # Verify context injection requirements generated
            requirements_text = " ".join(report.integration_requirements)
            assert "injection" in requirements_text.lower(), (
                "Missing injection requirements"
            )

        # 2. Command structure for DI integration
        if report.commands_found:
            # Commands exist - need DI integration
            assert "command" in " ".join(report.integration_requirements).lower()

        # 3. Storage mechanism for dependency container
        storage_validated = validate_context_storage_capability()
        assert storage_validated, "Storage capability required for DI container"

        # 4. Framework compatibility with DI patterns
        assert "click_import" in report.decorators_used, (
            "Click framework import required for DI"
        )

        print("✓ Dependency injection context analysis validated")
        print(f"  - Context usage opportunities: {len(report.context_usage)}")
        print(f"  - Commands for DI integration: {len(report.commands_found)}")
        print(f"  - Storage capability: {storage_validated}")
        print(f"  - DI requirements generated: {len(report.integration_requirements)}")


class TestClickFrameworkCompatibilityIntegration:
    """Integration tests for Click framework dependency injection compatibility."""

    def test_click_framework_dependency_injection_compatibility(self):
        """Validate Click framework supports dependency injection patterns."""
        # Test that Click context can store dependency container
        storage_capable = validate_context_storage_capability()
        assert storage_capable, "Click context must support dependency storage for DI"

        # Test analysis can identify injection points
        cli_dir = Path("spec_cli/cli")
        if cli_dir.exists():
            report = analyze_click_patterns(cli_dir)

            # Framework should be compatible with DI patterns
            requirements_text = " ".join(report.integration_requirements)
            assert "integration" in requirements_text.lower(), (
                "Missing DI integration capability"
            )

            # Should identify storage mechanism for DI container
            if report.storage_capabilities:
                assert any(report.storage_capabilities.values()), (
                    "No working storage mechanisms for DI"
                )

        print("✓ Click framework DI compatibility validated")

    def test_click_pattern_analysis_for_context_injection(self):
        """Validate analysis identifies Click context injection opportunities."""
        cli_dir = Path("spec_cli/cli")

        if not cli_dir.exists():
            pytest.skip("CLI directory not available for context injection analysis")

        report = analyze_click_patterns(cli_dir)

        # Look for existing context injection patterns
        context_decorators = {
            dec for dec in report.decorators_used if "context" in dec.lower()
        }

        if context_decorators:
            # Found context patterns - verify injection opportunities identified
            assert "click_pass_context" in report.decorators_used, (
                "Context passing decorator expected"
            )

            # Should generate context injection requirements
            requirements_text = " ".join(report.integration_requirements)
            assert "context" in requirements_text.lower(), (
                "Missing context injection requirements"
            )

        # Even without existing patterns, should identify injection capability
        storage_capable = validate_context_storage_capability()
        assert storage_capable, "Context injection requires storage capability"

        print("✓ Context injection opportunities analysis complete")
        print(f"  - Context decorators found: {context_decorators}")
        print(f"  - Storage capability: {storage_capable}")
        print(f"  - Context usage files: {len(report.context_usage)}")
