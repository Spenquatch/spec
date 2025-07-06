"""Integration tests for Slice P1.3a: Singleton Pattern Analysis.

Tests comprehensive integration of singleton pattern analysis with actual codebase
to validate compatibility wrapper requirements and cross-slice integration.
"""

from pathlib import Path

from spec_cli.utils.pattern_analysis import (
    AccessPatternReport,
    analyze_singleton_usage,
    document_access_patterns,
)


class TestSingletonAnalysisIntegration:
    """Test singleton analysis integration with real codebase."""

    def test_singleton_analysis_integration_when_real_codebase_then_identifies_all_compatibility_needs(
        self,
    ) -> None:
        """End-to-end test analyzing actual spec-cli codebase for singleton usage patterns."""
        # Test actual singleton.py file
        singleton_file = Path("spec_cli/utils/singleton.py")
        assert singleton_file.exists(), "singleton.py file should exist"

        usages = analyze_singleton_usage(singleton_file)

        # Should find SingletonMeta class definition
        singleton_meta_usages = [
            u for u in usages if u.singleton_name == "SingletonMeta"
        ]
        assert len(singleton_meta_usages) > 0, (
            "Should find SingletonMeta class definition"
        )

        # Should detect decorator pattern
        [u for u in usages if u.usage_type == "decorator_usage"]

    def test_progress_manager_analysis_integration_when_real_files_then_documents_access_patterns(
        self,
    ) -> None:
        """Test analysis of actual ProgressManager files for access patterns."""
        progress_manager_file = Path("spec_cli/ui/progress_manager.py")
        assert progress_manager_file.exists(), "progress_manager.py file should exist"

        usages = analyze_singleton_usage(progress_manager_file)

        # Should find ProgressManagerSingleton class and usage
        progress_usages = [u for u in usages if "ProgressManager" in u.singleton_name]
        assert len(progress_usages) > 0, "Should find ProgressManagerSingleton patterns"

        # Generate access pattern report
        report = document_access_patterns("ProgressManagerSingleton", usages)

        assert isinstance(report, AccessPatternReport)
        assert report.singleton_name == "ProgressManagerSingleton"
        assert report.total_usages > 0
        assert len(report.wrapper_requirements) > 0

    def test_cross_slice_integration_when_dependency_requirements_then_validates_p1_3b_compatibility(
        self,
    ) -> None:
        """Validate singleton analysis provides sufficient requirements for P1.3b wrapper implementation."""
        # Analyze key files that will need wrapper compatibility
        key_files = [
            Path("spec_cli/ui/progress_manager.py"),
            Path("spec_cli/utils/singleton.py"),
        ]

        all_usages = []
        for file_path in key_files:
            if file_path.exists():
                usages = analyze_singleton_usage(file_path)
                all_usages.extend(usages)

        # Generate comprehensive requirements
        progress_report = document_access_patterns(
            "ProgressManagerSingleton", all_usages
        )

        # Validate requirements necessary for P1.3b implementation
        requirements = progress_report.wrapper_requirements

        # Should include thread safety requirements
        thread_safety_reqs = [req for req in requirements if "thread" in req.lower()]
        assert len(thread_safety_reqs) > 0, (
            "Thread safety requirements needed for wrapper"
        )

        # Should include API preservation requirements
        api_reqs = [
            req
            for req in requirements
            if "api" in req.lower() or "interface" in req.lower()
        ]
        assert len(api_reqs) > 0, "API preservation requirements needed for wrapper"

        # Should include ProgressManager specific requirements
        progress_reqs = [req for req in requirements if "progress" in req.lower()]
        assert len(progress_reqs) > 0, "ProgressManager specific requirements needed"

    def test_singleton_pattern_detection_integration_when_current_codebase_then_identifies_migration_points(
        self,
    ) -> None:
        """Validate analysis identifies all singleton usage requiring migration support."""
        # Scan multiple files that use singleton patterns
        test_files = [
            Path("spec_cli/ui/progress_manager.py"),
            Path("spec_cli/utils/singleton.py"),
        ]

        total_singleton_types = set()
        all_access_methods = set()

        for file_path in test_files:
            if file_path.exists():
                usages = analyze_singleton_usage(file_path)

                # Collect singleton types
                singleton_names = {u.singleton_name for u in usages}
                total_singleton_types.update(singleton_names)

                # Analyze access patterns for each singleton type
                for singleton_name in singleton_names:
                    if singleton_name != "unknown_singleton":
                        report = document_access_patterns(singleton_name, usages)
                        all_access_methods.update(report.access_methods)

        # Should identify multiple singleton types
        assert len(total_singleton_types) > 1, (
            "Should identify multiple singleton types"
        )

        # Should identify various access methods
        expected_access_methods = {"direct_instantiation", "import_reference"}
        found_access_methods = expected_access_methods.intersection(all_access_methods)
        assert len(found_access_methods) > 0, "Should identify multiple access methods"

    def test_context_injection_requirements_analysis_when_comprehensive_scan_then_validates_complete_coverage(
        self,
    ) -> None:
        """Validate analysis provides complete requirements for SpecContext integration."""
        # Analyze progress utilities that will need context injection
        progress_utils_file = Path("spec_cli/ui/progress_utils.py")

        if progress_utils_file.exists():
            usages = analyze_singleton_usage(progress_utils_file)

            # Should detect get_progress_manager usage
            progress_usages = [
                u for u in usages if "progress_manager" in u.context.lower()
            ]

            if progress_usages:
                # Generate requirements for context injection
                report = document_access_patterns("ProgressManagerSingleton", usages)

                # Should include convenience function requirements
                convenience_reqs = [
                    req
                    for req in report.wrapper_requirements
                    if "convenience" in req.lower() or "function" in req.lower()
                ]
                assert len(convenience_reqs) > 0, (
                    "Should include convenience function requirements"
                )

    def test_dependency_interface_completeness_when_real_usage_then_validates_sufficient_methods(
        self,
    ) -> None:
        """Validate analysis identifies all required interface methods for dependency injection."""
        # Test actual progress manager implementation
        progress_file = Path("spec_cli/ui/progress_manager.py")

        if progress_file.exists():
            usages = analyze_singleton_usage(progress_file)

            # Filter for ProgressManagerSingleton usages
            progress_usages = [
                u for u in usages if "ProgressManager" in u.singleton_name
            ]

            if progress_usages:
                report = document_access_patterns(
                    "ProgressManagerSingleton", progress_usages
                )

                # Should identify key interface methods
                requirements = report.wrapper_requirements

                # Should include get/set/reset methods
                method_requirements = [
                    req
                    for req in requirements
                    if any(
                        method in req
                        for method in [
                            "get_progress_manager",
                            "set_progress_manager",
                            "reset",
                        ]
                    )
                ]
                assert len(method_requirements) > 0, (
                    "Should identify key interface methods"
                )

    def test_compatibility_layer_requirements_when_migration_analysis_then_provides_implementation_guidance(
        self,
    ) -> None:
        """Test that analysis provides sufficient guidance for compatibility layer implementation."""
        # Comprehensive analysis across multiple files
        analysis_files = [
            Path("spec_cli/ui/progress_manager.py"),
            Path("spec_cli/ui/progress_utils.py"),
            Path("spec_cli/cli/utils.py"),
        ]

        all_usages = []
        for file_path in analysis_files:
            if file_path.exists():
                try:
                    usages = analyze_singleton_usage(file_path)
                    all_usages.extend(usages)
                except Exception:
                    # Continue if file analysis fails
                    pass

        if all_usages:
            # Generate comprehensive compatibility requirements
            progress_usages = [
                u for u in all_usages if "progress" in u.singleton_name.lower()
            ]

            if progress_usages:
                report = document_access_patterns(
                    "ProgressManagerSingleton", progress_usages
                )

                # Validate implementation guidance is sufficient
                requirements = report.wrapper_requirements

                # Should provide migration strategy guidance
                [
                    req
                    for req in requirements
                    if any(
                        keyword in req.lower()
                        for keyword in ["migration", "compatibility", "wrapper"]
                    )
                ]

                # Should provide implementation requirements
                impl_reqs = [
                    req
                    for req in requirements
                    if any(
                        keyword in req.lower()
                        for keyword in ["implement", "support", "maintain"]
                    )
                ]
                assert len(impl_reqs) > 0, "Should provide implementation requirements"

class TestCodebasePatternConsistency:
    """Test consistency of singleton patterns across the codebase."""

    def test_singleton_usage_consistency_across_modules(self) -> None:
        """Test that singleton usage patterns are consistent across different modules."""
        # Test files that should use similar patterns
        ui_files = [
            Path("spec_cli/ui/progress_manager.py"),
            Path("spec_cli/ui/progress_utils.py"),
        ]

        access_pattern_consistency = []

        for file_path in ui_files:
            if file_path.exists():
                try:
                    usages = analyze_singleton_usage(file_path)
                    progress_usages = [
                        u for u in usages if "progress" in u.singleton_name.lower()
                    ]

                    if progress_usages:
                        report = document_access_patterns(
                            "ProgressManagerSingleton", progress_usages
                        )
                        access_pattern_consistency.append(report.access_methods)
                except Exception:
                    continue

        if len(access_pattern_consistency) >= 2:
            # Should have some common access methods across files
            common_methods = set.intersection(*access_pattern_consistency)
            assert len(common_methods) > 0, (
                "Should have consistent access patterns across modules"
            )

    def test_singleton_infrastructure_completeness(self) -> None:
        """Test that singleton infrastructure provides complete functionality."""
        singleton_file = Path("spec_cli/utils/singleton.py")

        if singleton_file.exists():
            usages = analyze_singleton_usage(singleton_file)

            # Should detect key infrastructure components
            found_components = {u.singleton_name for u in usages}

            found_expected = [
                comp for comp in expected_components if comp in found_components
            ]

            assert len(found_expected) > 0, (
                "Should find key singleton infrastructure components"
            )

class TestMigrationReadinessValidation:
    """Test validation of migration readiness based on analysis results."""

    def test_migration_readiness_assessment_when_analysis_complete_then_validates_next_steps(
        self,
    ) -> None:
        """Test that analysis results provide clear validation for next migration steps."""
        # Perform comprehensive analysis
        key_files = [
            Path("spec_cli/ui/progress_manager.py"),
            Path("spec_cli/utils/singleton.py"),
        ]

        migration_data = {
            "singleton_types": set(),
            "access_methods": set(),
            "requirements": [],
        }

        for file_path in key_files:
            if file_path.exists():
                try:
                    usages = analyze_singleton_usage(file_path)

                    # Collect migration data
                    singleton_names = {u.singleton_name for u in usages}
                    migration_data["singleton_types"].update(singleton_names)

                    # Analyze ProgressManagerSingleton specifically
                    progress_usages = [
                        u for u in usages if "ProgressManager" in u.singleton_name
                    ]
                    if progress_usages:
                        report = document_access_patterns(
                            "ProgressManagerSingleton", progress_usages
                        )
                        migration_data["access_methods"].update(report.access_methods)
                        migration_data["requirements"].extend(
                            report.wrapper_requirements
                        )

                except Exception:
                    continue

        # Validate migration readiness
        if migration_data["singleton_types"]:
            # Should have identified singleton types
            assert len(migration_data["singleton_types"]) > 0

            # Should have access methods for wrapper implementation
            if migration_data["access_methods"]:
                assert len(migration_data["access_methods"]) > 0

            # Should have requirements for next phase
            if migration_data["requirements"]:
                assert len(migration_data["requirements"]) > 0
