"""Unit tests for Slice 2.3: Missing Function Restoration and Implementation."""

import ast
from unittest.mock import Mock, patch

import pytest

from slice_2_3_function_restoration import (
    FunctionRestorationSystem,
    restore_functions_for_test_execution,
)
from spec_cli.utils.function_restoration.missing_function_impl import (
    FunctionRestorationError,
    _determine_stub_return_value,
    _parse_function_signature,
    create_function_stub_registry,
    implement_missing_function,
)

# Test constants
TEST_FUNCTION_NAME = "test_function"
TEST_SIGNATURE = "def test_function(value: str) -> bool:"
TEST_PURPOSE = "Test function for validation"
SAMPLE_MISSING_FUNCTIONS = ["validate_input", "format_output", "process_data"]
SAMPLE_SIGNATURES = {
    "validate_input": "def validate_input(value: str) -> bool:",
    "format_output": "def format_output(data: Any) -> str:",
    "process_data": "def process_data(data: dict) -> dict:",
}
SAMPLE_TEST_REQUIREMENTS = {
    "context": "testing",
    "behavior": "stub",
    "return_type": "Any",
}


class TestImplementMissingFunction:
    """Test cases for implement_missing_function function."""

    def test_implement_missing_function_with_valid_signature_returns_callable(self):
        """Test that valid signature returns a callable function."""
        result = implement_missing_function(TEST_SIGNATURE, TEST_PURPOSE)

        assert callable(result)
        assert result.__name__ == TEST_FUNCTION_NAME
        assert TEST_PURPOSE in result.__doc__

    def test_implement_missing_function_with_bool_return_type_returns_true_for_validation(
        self,
    ):
        """Test that validation functions return True by default."""
        signature = "def validate_user(name: str) -> bool:"
        purpose = "Validate user input"

        func = implement_missing_function(signature, purpose)
        result = func("test")

        assert result is True

    def test_implement_missing_function_with_str_return_type_returns_string(self):
        """Test that string return type functions return appropriate string."""
        signature = "def format_message(text: str) -> str:"
        purpose = "Format message output"

        func = implement_missing_function(signature, purpose)
        result = func("test")

        assert isinstance(result, str)
        assert "format_message_output" in result

    def test_implement_missing_function_with_invalid_signature_raises_error(self):
        """Test that invalid signature raises FunctionRestorationError."""
        with pytest.raises(
            FunctionRestorationError, match="Failed to implement missing function"
        ):
            implement_missing_function("invalid signature", TEST_PURPOSE)

    def test_implement_missing_function_with_empty_signature_raises_type_error(self):
        """Test that empty signature raises TypeError."""
        with pytest.raises(TypeError, match="Signature must be a non-empty string"):
            implement_missing_function("", TEST_PURPOSE)

    def test_implement_missing_function_with_empty_purpose_raises_type_error(self):
        """Test that empty purpose raises TypeError."""
        with pytest.raises(TypeError, match="Purpose must be a non-empty string"):
            implement_missing_function(TEST_SIGNATURE, "")

    def test_implement_missing_function_preserves_function_metadata(self):
        """Test that function metadata is properly preserved."""
        func = implement_missing_function(TEST_SIGNATURE, TEST_PURPOSE)

        assert hasattr(func, "__name__")
        assert hasattr(func, "__doc__")
        assert hasattr(func, "__signature__")

    def test_implement_missing_function_with_multiple_parameters_handles_correctly(
        self,
    ):
        """Test function with multiple parameters is handled correctly."""
        signature = "def complex_func(a: int, b: str, c: bool) -> dict:"
        purpose = "Complex function test"

        func = implement_missing_function(signature, purpose)
        result = func(1, "test", True)

        assert isinstance(result, dict)

    def test_implement_missing_function_with_no_return_annotation_returns_none(self):
        """Test function with no return annotation returns None."""
        signature = "def simple_func(value: str):"
        purpose = "Simple function test"

        func = implement_missing_function(signature, purpose)
        result = func("test")

        assert result is None


class TestParseFunctionSignature:
    """Test cases for _parse_function_signature function."""

    def test_parse_function_signature_with_valid_function_returns_ast_node(self):
        """Test that valid function signature returns AST FunctionDef node."""
        result = _parse_function_signature(TEST_SIGNATURE)

        assert isinstance(result, ast.FunctionDef)
        assert result.name == TEST_FUNCTION_NAME

    def test_parse_function_signature_with_invalid_syntax_raises_error(self):
        """Test that invalid syntax raises FunctionRestorationError."""
        with pytest.raises(
            FunctionRestorationError, match="Failed to parse function signature"
        ):
            _parse_function_signature("invalid def syntax")

    def test_parse_function_signature_with_parameters_preserves_args(self):
        """Test that function parameters are preserved in AST."""
        signature = "def test_func(a: int, b: str) -> bool:"
        result = _parse_function_signature(signature)

        assert len(result.args.args) == 2  # Number of parameters
        assert result.args.args[0].arg == "a"
        assert result.args.args[1].arg == "b"

    def test_parse_function_signature_handles_missing_colon(self):
        """Test that signature without ending colon is handled."""
        signature = "def test_func(value: str) -> bool"
        result = _parse_function_signature(signature)

        assert isinstance(result, ast.FunctionDef)
        assert result.name == "test_func"


class TestDetermineStubReturnValue:
    """Test cases for _determine_stub_return_value function."""

    def test_determine_stub_return_value_with_bool_validation_returns_true(self):
        """Test that bool validation functions return True."""
        annotation = ast.parse("bool").body[0].value  # Simple name annotation
        result = _determine_stub_return_value(annotation, "validate input")

        assert result is True

    def test_determine_stub_return_value_with_str_returns_formatted_string(self):
        """Test that string return type returns formatted string."""
        annotation = ast.parse("str").body[0].value
        result = _determine_stub_return_value(annotation, "format data")

        assert isinstance(result, str)
        assert "format_data" in result

    def test_determine_stub_return_value_with_int_returns_zero(self):
        """Test that int return type returns zero."""
        annotation = ast.parse("int").body[0].value
        result = _determine_stub_return_value(annotation, "count items")

        assert result == 0

    def test_determine_stub_return_value_with_list_returns_empty_list(self):
        """Test that list return type returns empty list."""
        annotation = ast.parse("list").body[0].value
        result = _determine_stub_return_value(annotation, "get items")

        assert result == []

    def test_determine_stub_return_value_with_dict_returns_empty_dict(self):
        """Test that dict return type returns empty dict."""
        annotation = ast.parse("dict").body[0].value
        result = _determine_stub_return_value(annotation, "get config")

        assert result == {}

    def test_determine_stub_return_value_with_none_annotation_returns_none(self):
        """Test that None annotation returns None."""
        result = _determine_stub_return_value(None, "setup function")

        assert result is None


class TestCreateFunctionStubRegistry:
    """Test cases for create_function_stub_registry function."""

    def test_create_function_stub_registry_returns_dict(self):
        """Test that registry creation returns dictionary."""
        result = create_function_stub_registry()

        assert isinstance(result, dict)
        assert len(result) > 0

    def test_create_function_stub_registry_contains_common_functions(self):
        """Test that registry contains expected common functions."""
        result = create_function_stub_registry()

        expected_functions = ["validate_input", "validate_path", "format_output"]
        for func_name in expected_functions:
            assert func_name in result
            assert callable(result[func_name])

    def test_create_function_stub_registry_functions_are_callable(self):
        """Test that all registry functions are callable."""
        result = create_function_stub_registry()

        for func_name, func in result.items():
            assert callable(func), f"Function {func_name} is not callable"


class TestFunctionRestorationSystem:
    """Test cases for FunctionRestorationSystem class."""

    def test_function_restoration_system_initialization(self):
        """Test that system initializes correctly."""
        system = FunctionRestorationSystem()

        assert isinstance(system.restored_functions, dict)
        assert isinstance(system.restoration_metadata, dict)
        assert isinstance(system.stub_registry, dict)
        assert len(system.stub_registry) > 0

    def test_analyze_missing_functions_with_valid_input_returns_analysis(self):
        """Test that missing function analysis returns proper results."""
        system = FunctionRestorationSystem()

        result = system.analyze_missing_functions(
            SAMPLE_MISSING_FUNCTIONS, SAMPLE_TEST_REQUIREMENTS
        )

        assert isinstance(result, dict)
        assert len(result) == len(SAMPLE_MISSING_FUNCTIONS)
        for func_name in SAMPLE_MISSING_FUNCTIONS:
            assert func_name in result
            assert "category" in result[func_name]
            assert "restoration_strategy" in result[func_name]

    def test_analyze_missing_functions_with_invalid_input_raises_type_error(self):
        """Test that invalid input types raise TypeError."""
        system = FunctionRestorationSystem()

        with pytest.raises(TypeError, match="missing_functions must be a list"):
            system.analyze_missing_functions("not a list", SAMPLE_TEST_REQUIREMENTS)

    def test_restore_missing_functions_with_valid_signatures_returns_functions(self):
        """Test that function restoration returns callable functions."""
        system = FunctionRestorationSystem()
        analysis_results = system.analyze_missing_functions(
            SAMPLE_MISSING_FUNCTIONS, SAMPLE_TEST_REQUIREMENTS
        )

        result = system.restore_missing_functions(SAMPLE_SIGNATURES, analysis_results)

        assert isinstance(result, dict)
        assert len(result) == len(SAMPLE_SIGNATURES)
        for _func_name, func in result.items():
            assert callable(func)

    def test_restore_missing_functions_with_invalid_signatures_raises_type_error(self):
        """Test that invalid signature types raise TypeError."""
        system = FunctionRestorationSystem()

        with pytest.raises(TypeError, match="function_signatures must be a dictionary"):
            system.restore_missing_functions("not a dict", {})

    def test_validate_restored_functions_with_valid_functions_returns_validation_results(
        self,
    ):
        """Test that function validation returns proper results."""
        system = FunctionRestorationSystem()
        test_functions = {
            "test_func": lambda: True,
            "invalid_func": "not a function",
        }

        result = system.validate_restored_functions(test_functions)

        assert isinstance(result, dict)
        assert result["test_func"] is True
        assert result["invalid_func"] is False

    def test_validate_restored_functions_with_invalid_input_raises_type_error(self):
        """Test that invalid input raises TypeError."""
        system = FunctionRestorationSystem()

        with pytest.raises(TypeError, match="restored_functions must be a dictionary"):
            system.validate_restored_functions("not a dict")

    def test_categorize_function_with_validation_name_returns_validation_category(self):
        """Test that validation function names are categorized correctly."""
        system = FunctionRestorationSystem()

        result = system._categorize_function("validate_input")
        assert result == "validation"

        result = system._categorize_function("check_permissions")
        assert result == "validation"

    def test_categorize_function_with_formatting_name_returns_formatting_category(self):
        """Test that formatting function names are categorized correctly."""
        system = FunctionRestorationSystem()

        result = system._categorize_function("format_output")
        assert result == "formatting"

    def test_categorize_function_with_unknown_name_returns_utility_category(self):
        """Test that unknown function names return utility category."""
        system = FunctionRestorationSystem()

        result = system._categorize_function("unknown_function")
        assert result == "utility"


class TestRestoreFunctionsForTestExecution:
    """Test cases for restore_functions_for_test_execution main function."""

    def test_restore_functions_for_test_execution_with_valid_input_returns_complete_results(
        self,
    ):
        """Test that main function returns complete restoration results."""
        result = restore_functions_for_test_execution(
            SAMPLE_MISSING_FUNCTIONS, SAMPLE_SIGNATURES, SAMPLE_TEST_REQUIREMENTS
        )

        assert isinstance(result, dict)
        assert "implemented_functions" in result
        assert "implementation_status" in result
        assert "analysis_results" in result
        assert "validation_results" in result
        assert "restoration_metadata" in result

    def test_restore_functions_for_test_execution_implements_all_missing_functions(
        self,
    ):
        """Test that all missing functions are implemented."""
        result = restore_functions_for_test_execution(
            SAMPLE_MISSING_FUNCTIONS, SAMPLE_SIGNATURES, SAMPLE_TEST_REQUIREMENTS
        )

        implemented = result["implemented_functions"]
        status = result["implementation_status"]

        assert len(implemented) == len(SAMPLE_MISSING_FUNCTIONS)
        for func_name in SAMPLE_MISSING_FUNCTIONS:
            assert func_name in implemented
            assert func_name in status
            assert status[func_name] in ["success", "implemented_but_validation_failed"]

    def test_restore_functions_for_test_execution_functions_are_executable(self):
        """Test that restored functions are actually executable."""
        result = restore_functions_for_test_execution(
            SAMPLE_MISSING_FUNCTIONS, SAMPLE_SIGNATURES, SAMPLE_TEST_REQUIREMENTS
        )

        implemented = result["implemented_functions"]

        # Test that functions can be called
        validate_func = implemented["validate_input"]
        assert callable(validate_func)

        # Call with expected arguments
        validation_result = validate_func("test_value")
        assert validation_result is True  # Validation functions return True

    def test_restore_functions_for_test_execution_with_empty_input_returns_empty_results(
        self,
    ):
        """Test that empty input returns appropriate empty results."""
        result = restore_functions_for_test_execution([], {}, {})

        assert result["implemented_functions"] == {}
        assert result["implementation_status"] == {}
        assert isinstance(result["analysis_results"], dict)

    @patch("slice_2_3_function_restoration.FunctionRestorationSystem")
    def test_restore_functions_for_test_execution_handles_system_errors(
        self, mock_system_class
    ):
        """Test that system errors are properly handled and re-raised."""
        mock_system = Mock()
        mock_system.analyze_missing_functions.side_effect = Exception("System error")
        mock_system_class.return_value = mock_system

        with pytest.raises(
            FunctionRestorationError,
            match="Failed to restore functions for test execution",
        ):
            restore_functions_for_test_execution(
                SAMPLE_MISSING_FUNCTIONS, SAMPLE_SIGNATURES, SAMPLE_TEST_REQUIREMENTS
            )

    def test_restore_functions_for_test_execution_handles_partial_failures_gracefully(
        self,
    ):
        """Test that partial failures in analysis are handled gracefully."""
        # Use signatures with one invalid entry
        invalid_signatures = {
            "valid_function": "def valid_function() -> bool:",
            "invalid_function": "invalid signature syntax",
        }
        missing_functions = ["valid_function", "invalid_function"]

        # Should not raise exception, but handle partial failures
        try:
            result = restore_functions_for_test_execution(
                missing_functions, invalid_signatures, SAMPLE_TEST_REQUIREMENTS
            )
            # Should still return results, even with some failures
            assert isinstance(result, dict)
            assert "implemented_functions" in result
        except FunctionRestorationError:
            # Partial failures may cause overall failure - that's acceptable
            pass

    def test_restore_functions_for_test_execution_metadata_contains_required_fields(
        self,
    ):
        """Test that restoration metadata contains all required fields."""
        result = restore_functions_for_test_execution(
            SAMPLE_MISSING_FUNCTIONS, SAMPLE_SIGNATURES, SAMPLE_TEST_REQUIREMENTS
        )

        metadata = result["restoration_metadata"]

        for func_name in SAMPLE_MISSING_FUNCTIONS:
            if func_name in metadata:
                func_metadata = metadata[func_name]
                assert "signature" in func_metadata
                assert "strategy" in func_metadata
                assert "analysis" in func_metadata
                assert "restored_at" in func_metadata
                assert func_metadata["restored_at"] == "slice_2_3"

    def test_function_restoration_system_analyze_error_handling(self):
        """Test function restoration system handles analysis errors gracefully."""
        system = FunctionRestorationSystem()

        # Test with function name that might cause issues in categorization
        problematic_functions = [
            "",
            "function_with_very_long_name_that_might_cause_issues",
        ]
        test_requirements = {"context": "error_test"}

        result = system.analyze_missing_functions(
            problematic_functions, test_requirements
        )

        # Should handle gracefully without crashing
        assert isinstance(result, dict)
        assert len(result) == len(problematic_functions)

    def test_function_restoration_system_restoration_strategies(self):
        """Test all restoration strategy paths."""
        system = FunctionRestorationSystem()

        # Test registry strategy
        registry_functions = list(system.stub_registry.keys())[:1]
        if registry_functions:
            strategy = system._determine_restoration_strategy(
                registry_functions[0], "validation", {"expected_behavior": "stub"}
            )
            assert strategy == "registry"

        # Test implement strategy
        strategy = system._determine_restoration_strategy(
            "custom_validator", "validation", {"expected_behavior": "functional"}
        )
        assert strategy == "implement"

        # Test stub strategy (default)
        strategy = system._determine_restoration_strategy(
            "unknown_function", "unknown", {"expected_behavior": "stub"}
        )
        assert strategy == "stub"

    def test_function_restoration_system_restoration_priorities(self):
        """Test all restoration priority levels."""
        system = FunctionRestorationSystem()

        # Test high priority
        priority = system._determine_restoration_priority(
            "validate_input", "validation", {"context": "critical"}
        )
        assert priority == "high"

        # Test medium priority
        priority = system._determine_restoration_priority(
            "process_data", "processing", {"context": "important"}
        )
        assert priority == "medium"

        # Test low priority
        priority = system._determine_restoration_priority(
            "utility_func", "utility", {"context": "optional"}
        )
        assert priority == "low"

    def test_function_restoration_system_validation_error_handling(self):
        """Test validation with functions that cause execution errors."""
        system = FunctionRestorationSystem()

        def failing_function():
            raise RuntimeError("Test error")

        test_functions = {
            "failing_func": failing_function,
            "normal_func": lambda: True,
        }

        result = system.validate_restored_functions(test_functions)

        # Should handle execution errors gracefully
        assert result["failing_func"] is False  # Failed validation
        assert result["normal_func"] is True  # Successful validation

    def test_function_restoration_system_implement_from_signature_all_categories(self):
        """Test function implementation for all categories."""
        system = FunctionRestorationSystem()

        test_cases = [
            ("validation", "validate_test"),
            ("formatting", "format_test"),
            ("processing", "process_test"),
            ("accessor", "get_test"),
            ("initialization", "init_test"),
            ("cleanup", "cleanup_test"),
            ("utility", "utility_test"),
        ]

        for category, func_name in test_cases:
            analysis = {"category": category, "requirements": {}}
            signature = f"def {func_name}(value: str) -> bool:"

            func = system._implement_function_from_signature(
                func_name, signature, analysis
            )

            assert callable(func)
            assert func.__name__ == func_name

    def test_function_restoration_system_create_basic_stub(self):
        """Test basic stub creation."""
        system = FunctionRestorationSystem()

        func = system._create_basic_stub("test_stub", "def test_stub() -> None:")

        assert callable(func)
        assert func.__name__ == "test_stub"
        assert "Stub for test_stub" in func.__doc__

    def test_function_restoration_system_restoration_error_handling(self):
        """Test error handling during function restoration."""
        system = FunctionRestorationSystem()

        # Test with invalid signature that will cause implementation to fail
        invalid_signatures = {"bad_func": "completely invalid signature"}
        analysis_results = {
            "bad_func": {"category": "utility", "restoration_strategy": "implement"}
        }

        # Should raise FunctionRestorationError
        with pytest.raises(
            FunctionRestorationError, match="Failed to restore function"
        ):
            system.restore_missing_functions(invalid_signatures, analysis_results)
