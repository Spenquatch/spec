#!/usr/bin/env python3
"""Functionality test for Slice 3.3: Migration Strategy Development and Planning.

This script tests REAL functionality with NO mocking - actual strategy development
on actual classified patterns from Slice 3.2 output.
"""

import sys
from pathlib import Path

# Add the project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from slice_3_2_pattern_analysis import (
    ClassifiedSingletonPattern,
    PatternAnalysisResult,
)
from slice_3_3_strategy_development import (
    develop_migration_strategies,
    generate_migration_plan_document,
)
from spec_cli.utils.migration_planning.strategy_generator import (
    generate_elimination_strategy,
)
from spec_cli.utils.pattern_analysis import SingletonUsage
from spec_cli.utils.pattern_classification.complexity_analyzer import (
    ComplexityAssessment,
)
from spec_cli.utils.singleton_detection import SingletonViolation

def create_sample_pattern_analysis_result() -> PatternAnalysisResult:
    """Create realistic PatternAnalysisResult for testing strategy development."""
    # Pattern 1: Decorator singleton (moderate complexity)
    violation1 = SingletonViolation(
        file_path=Path("src/models/user_manager.py"),
        line_number=15,
        column=0,
        pattern_type="decorator_singleton",
        description="Singleton decorator: UserManager",
        code_snippet="@singleton\nclass UserManager:\n    def __init__(self):",
    )

    classified_pattern1 = ClassifiedSingletonPattern(
        original_violation=violation1,
        pattern_category="moderate",
        complexity_assessment=ComplexityAssessment(
            complexity_score=5,
            dependency_count=3,
            migration_priority="medium",
            estimated_effort_hours=8,
            risk_factors=["decorator_pattern"],
        ),
        dependent_files=[
            Path("src/controllers/auth_controller.py"),
            Path("src/services/user_service.py"),
            Path("src/views/profile_view.py"),
        ],
        usage_patterns=[
            SingletonUsage(
                file_path=Path("src/controllers/auth_controller.py"),
                line_number=25,
                usage_type="instantiation",
                singleton_name="UserManager",
                context="user_mgr = UserManager()",
            )
        ],
        migration_notes=["Remove singleton decorator", "Update instantiation sites"],
    )

    # Pattern 2: Metaclass singleton (high complexity)
    violation2 = SingletonViolation(
        file_path=Path("src/config/database_config.py"),
        line_number=8,
        column=0,
        pattern_type="metaclass_singleton",
        description="Metaclass singleton: DatabaseConfig",
        code_snippet="class DatabaseConfig(metaclass=SingletonMeta):\n    def __init__(self):",
    )

    classified_pattern2 = ClassifiedSingletonPattern(
        original_violation=violation2,
        pattern_category="critical",
        complexity_assessment=ComplexityAssessment(
            complexity_score=9,
            dependency_count=7,
            migration_priority="critical",
            estimated_effort_hours=16,
            risk_factors=["metaclass_pattern", "thread_safety", "high_usage"],
        ),
        dependent_files=[
            Path("src/database/connection.py"),
            Path("src/database/migrations.py"),
            Path("src/models/base_model.py"),
            Path("src/app.py"),
            Path("src/tests/test_database.py"),
            Path("src/cli/db_commands.py"),
            Path("src/config/settings.py"),
        ],
        usage_patterns=[
            SingletonUsage(
                file_path=Path("src/database/connection.py"),
                line_number=12,
                usage_type="instantiation",
                singleton_name="DatabaseConfig",
                context="config = DatabaseConfig()",
            ),
            SingletonUsage(
                file_path=Path("src/app.py"),
                line_number=35,
                usage_type="method_call",
                singleton_name="DatabaseConfig",
                context="DatabaseConfig().get_url()",
            ),
        ],
        migration_notes=[
            "CRITICAL: Migrate as soon as possible due to high complexity",
            "Large effort required: ~16 hours",
            "Replace metaclass with dependency injection container",
        ],
    )

    # Pattern 3: Import singleton (simple)
    violation3 = SingletonViolation(
        file_path=Path("src/utils/logger.py"),
        line_number=5,
        column=0,
        pattern_type="import_singleton",
        description="Import singleton: Logger",
        code_snippet="logger = Logger()\n# Global logger instance",
    )

    classified_pattern3 = ClassifiedSingletonPattern(
        original_violation=violation3,
        pattern_category="simple",
        complexity_assessment=ComplexityAssessment(
            complexity_score=3,
            dependency_count=2,
            migration_priority="low",
            estimated_effort_hours=4,
            risk_factors=["import_pattern"],
        ),
        dependent_files=[
            Path("src/services/api_service.py"),
            Path("src/controllers/main_controller.py"),
        ],
        usage_patterns=[
            SingletonUsage(
                file_path=Path("src/services/api_service.py"),
                line_number=8,
                usage_type="import",
                singleton_name="logger",
                context="from utils.logger import logger",
            )
        ],
        migration_notes=["Update import statements across dependent modules"],
    )

    return PatternAnalysisResult(
        classified_patterns=[classified_pattern1, classified_pattern2, classified_pattern3],
        dependency_graph={
            "src/models/user_manager.py": [
                "src/controllers/auth_controller.py",
                "src/services/user_service.py",
                "src/views/profile_view.py",
            ],
            "src/config/database_config.py": [
                "src/database/connection.py",
                "src/database/migrations.py",
                "src/models/base_model.py",
                "src/app.py",
                "src/tests/test_database.py",
                "src/cli/db_commands.py",
                "src/config/settings.py",
            ],
            "src/utils/logger.py": [
                "src/services/api_service.py",
                "src/controllers/main_controller.py",
            ],
        },
        complexity_distribution={"simple": 1, "moderate": 1, "critical": 1},
        migration_priority_order=[
            "src/config/database_config.py",  # Critical first
            "src/models/user_manager.py",     # Medium next
            "src/utils/logger.py",            # Low last
        ],
    )

def test_strategy_generation_functionality() -> bool:
    """Test individual strategy generation functionality."""
    print("Testing strategy generation functionality...")

    try:
        # Create sample pattern
        violation = SingletonViolation(
            file_path=Path("test/singleton.py"),
            line_number=10,
            column=0,
            pattern_type="decorator_singleton",
            description="Test singleton",
            code_snippet="@singleton\nclass TestClass:",
        )

        pattern = ClassifiedSingletonPattern(
            original_violation=violation,
            pattern_category="moderate",
            complexity_assessment=ComplexityAssessment(
                complexity_score=6,
                dependency_count=3,
                migration_priority="medium",
                estimated_effort_hours=7,
                risk_factors=["test_pattern"],
            ),
            dependent_files=[Path("dep1.py"), Path("dep2.py"), Path("dep3.py")],
            usage_patterns=[],
            migration_notes=["Test migration note"],
        )

        # Test strategy generation
        strategy = generate_elimination_strategy(pattern)

        print("Expected: decorator_removal strategy")
        print(f"Actual: {strategy['strategy_type']}")

        if strategy["strategy_type"] != "decorator_removal":
            print("FAIL: Wrong strategy type generated")
            return False

        print("Expected: effort_estimate_hours = 7")
        print(f"Actual: effort_estimate_hours = {strategy['effort_estimate_hours']}")

        if strategy["effort_estimate_hours"] != 7:
            print("FAIL: Wrong effort estimate")
            return False

        print("Expected: dependency_count = 3")
        print(f"Actual: dependency_count = {strategy['dependency_count']}")

        if strategy["dependency_count"] != 3:
            print("FAIL: Wrong dependency count")
            return False

        print("PASS: Strategy generation functionality works correctly")
        return True

    except Exception as e:
        print(f"FAIL: Strategy generation failed with error: {e}")
        return False

def test_full_strategy_development_functionality() -> bool:
    """Test complete strategy development functionality with realistic data."""
    print("\nTesting full strategy development functionality...")

    try:
        # Create realistic pattern analysis result
        pattern_analysis_result = create_sample_pattern_analysis_result()

        print("Expected: 3 patterns to process")
        print(f"Actual: {len(pattern_analysis_result.classified_patterns)} patterns")

        if len(pattern_analysis_result.classified_patterns) != 3:
            print("FAIL: Wrong number of input patterns")
            return False

        # Test strategy development
        result = develop_migration_strategies(pattern_analysis_result)

        # Verify basic structure
        required_keys = [
            "migration_strategies",
            "implementation_order",
            "effort_estimates",
            "implementation_phases"
        ]

        for key in required_keys:
            print(f"Expected: {key} present in result")
            print(f"Actual: {key in result}")

            if key not in result:
                print(f"FAIL: Missing required key: {key}")
                return False

        # Verify strategy count
        print("Expected: 3 migration strategies")
        print(f"Actual: {len(result['migration_strategies'])} strategies")

        if len(result["migration_strategies"]) != 3:
            print("FAIL: Wrong number of strategies generated")
            return False

        # Verify total effort calculation
        expected_effort = 8 + 16 + 4  # From complexity assessments
        actual_effort = result["effort_estimates"]["total_effort_hours"]

        print(f"Expected: total_effort_hours = {expected_effort}")
        print(f"Actual: total_effort_hours = {actual_effort}")

        if actual_effort != expected_effort:
            print("FAIL: Wrong total effort calculation")
            return False

        # Verify implementation order preserved
        expected_order = [
            "src/config/database_config.py",
            "src/models/user_manager.py",
            "src/utils/logger.py"
        ]
        actual_order = result["implementation_order"]

        print(f"Expected: order = {expected_order}")
        print(f"Actual: order = {actual_order}")

        if actual_order != expected_order:
            print("FAIL: Implementation order not preserved")
            return False

        # Verify phases created
        phases = result["implementation_phases"]
        print("Expected: at least 1 implementation phase")
        print(f"Actual: {len(phases)} phases")

        if len(phases) == 0:
            print("FAIL: No implementation phases created")
            return False

        # Verify critical pattern in first phase
        first_phase = phases[0]
        if "src/config/database_config.py" not in first_phase["patterns"]:
            print("FAIL: Critical pattern not in first phase")
            return False

        print("PASS: Full strategy development functionality works correctly")
        return True

    except Exception as e:
        print(f"FAIL: Strategy development failed with error: {e}")
        return False

def test_migration_plan_document_generation() -> bool:
    """Test migration plan document generation functionality."""
    print("\nTesting migration plan document generation...")

    try:
        # Create sample strategy result
        pattern_analysis_result = create_sample_pattern_analysis_result()
        strategy_result = develop_migration_strategies(pattern_analysis_result)

        # Test markdown generation
        markdown_doc = generate_migration_plan_document(strategy_result, "markdown")

        expected_content = [
            "# Singleton Pattern Migration Plan",
            "**Total Patterns**: 3",
            "**Total Effort**: 28 hours",
            "## Implementation Phases"
        ]

        for content in expected_content:
            print(f"Expected: '{content}' in markdown document")
            print(f"Actual: {content in markdown_doc}")

            if content not in markdown_doc:
                print(f"FAIL: Missing content in markdown: {content}")
                return False

        # Test text generation
        text_doc = generate_migration_plan_document(strategy_result, "text")

        expected_text_content = [
            "SINGLETON PATTERN MIGRATION PLAN",
            "Total Patterns: 3",
            "Total Effort: 28 hours"
        ]

        for content in expected_text_content:
            print(f"Expected: '{content}' in text document")
            print(f"Actual: {content in text_doc}")

            if content not in text_doc:
                print(f"FAIL: Missing content in text: {content}")
                return False

        # Test JSON generation
        json_doc = generate_migration_plan_document(strategy_result, "json")

        import json
        try:
            parsed = json.loads(json_doc)

            print("Expected: valid JSON with total_patterns = 3")
            print(f"Actual: total_patterns = {parsed.get('total_patterns', 'MISSING')}")

            if parsed.get("total_patterns") != 3:
                print("FAIL: Wrong total_patterns in JSON")
                return False

        except json.JSONDecodeError:
            print("FAIL: Invalid JSON generated")
            return False

        print("PASS: Migration plan document generation works correctly")
        return True

    except Exception as e:
        print(f"FAIL: Document generation failed with error: {e}")
        return False

def test_strategy_types_coverage() -> bool:
    """Test that all major singleton pattern types get appropriate strategies."""
    print("\nTesting strategy types coverage...")

    pattern_types = [
        ("decorator_singleton", "decorator_removal"),
        ("metaclass_singleton", "dependency_injection_replacement"),
        ("import_singleton", "import_refactoring"),
        ("global_variable_singleton", "global_refactoring"),
        ("unknown_pattern", "general_refactoring"),
    ]

    try:
        for pattern_type, expected_strategy in pattern_types:
            # Create test pattern
            violation = SingletonViolation(
                file_path=Path(f"test_{pattern_type}.py"),
                line_number=1,
                column=0,
                pattern_type=pattern_type,
                description=f"Test {pattern_type}",
                code_snippet="test code",
            )

            pattern = ClassifiedSingletonPattern(
                original_violation=violation,
                pattern_category="moderate",
                complexity_assessment=ComplexityAssessment(
                    complexity_score=5,
                    dependency_count=2,
                    migration_priority="medium",
                    estimated_effort_hours=6,
                    risk_factors=["test_pattern"],
                ),
                dependent_files=[],
                usage_patterns=[],
                migration_notes=[],
            )

            strategy = generate_elimination_strategy(pattern)

            print(f"Expected: {pattern_type} -> {expected_strategy}")
            print(f"Actual: {pattern_type} -> {strategy['strategy_type']}")

            if strategy["strategy_type"] != expected_strategy:
                print(f"FAIL: Wrong strategy for {pattern_type}")
                return False

        print("PASS: All strategy types covered correctly")
        return True

    except Exception as e:
        print(f"FAIL: Strategy type coverage test failed: {e}")
        return False

def test_end_to_end_integration() -> bool:
    """Test complete end-to-end integration from Slice 3.2 output to migration plan."""
    print("\nTesting end-to-end integration...")

    try:
        # Simulate complete workflow
        pattern_analysis_result = create_sample_pattern_analysis_result()

        # Step 1: Develop strategies
        strategy_result = develop_migration_strategies(pattern_analysis_result)

        # Step 2: Generate documentation
        markdown_plan = generate_migration_plan_document(strategy_result, "markdown")

        # Step 3: Verify complete integration
        verification_checks = [
            # Data flows correctly through pipeline
            (len(strategy_result["migration_strategies"]) == 3, "3 strategies generated"),
            (strategy_result["effort_estimates"]["total_effort_hours"] == 28, "Correct effort total"),
            (len(strategy_result["implementation_phases"]) >= 1, "Phases created"),

            # Document includes all key information
            ("**Total Patterns**: 3" in markdown_plan, "Pattern count in document"),
            ("**Total Effort**: 28 hours" in markdown_plan, "Effort total in document"),
            ("DatabaseConfig" in markdown_plan or "Dependency Injection" in markdown_plan, "Strategy details in document"),
        ]

        for check, description in verification_checks:
            print(f"Expected: {description} = True")
            print(f"Actual: {description} = {check}")

            if not check:
                print(f"FAIL: Integration check failed: {description}")
                return False

        # Verify specific strategy details
        db_config_strategy = strategy_result["migration_strategies"]["src/config/database_config.py"]

        expected_checks = [
            (db_config_strategy["strategy_type"] == "dependency_injection_replacement", "DB config uses DI strategy"),
            (db_config_strategy["effort_estimate_hours"] == 16, "DB config effort correct"),
            (db_config_strategy["dependency_count"] == 7, "DB config dependency count correct"),
            (db_config_strategy["risk_level"] == "high", "DB config risk level correct"),
        ]

        for check, description in expected_checks:
            print(f"Expected: {description} = True")
            print(f"Actual: {description} = {check}")

            if not check:
                print(f"FAIL: Strategy detail check failed: {description}")
                return False

        print("PASS: End-to-end integration works correctly")
        return True

    except Exception as e:
        print(f"FAIL: End-to-end integration failed: {e}")
        return False

def main() -> int:
    """Run all functionality tests and return exit code."""
    print("=" * 60)
    print("SLICE 3.3 STRATEGY DEVELOPMENT FUNCTIONALITY TEST")
    print("=" * 60)
    print("Testing REAL strategy development functionality with NO mocking")
    print()

    tests = [
        test_strategy_generation_functionality,
        test_full_strategy_development_functionality,
        test_migration_plan_document_generation,
        test_strategy_types_coverage,
        test_end_to_end_integration,
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"FAIL: Test {test_func.__name__} crashed: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print("FUNCTIONALITY TEST RESULTS:")
    print(f"PASSED: {passed}")
    print(f"FAILED: {failed}")
    print(f"TOTAL: {passed + failed}")

    if failed == 0:
        print("SUCCESS: All functionality tests passed!")
        return 0
    else:
        print("FAILURE: Some functionality tests failed!")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
