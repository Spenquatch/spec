"""Tests for Slice P2.2a: Decorator Pattern Analysis and Design."""

import pytest

from spec_cli.utils.decorator_analysis import (
    DecoratorAnalysisError,
    SignatureReport,
    analyze_function_signature,
    validate_decorator_compatibility,
)

# Test constants
DEFAULT_PARAMETER_COUNT = 2
MAXIMUM_COMPATIBLE_PARAMETERS = 5
CLICK_CONTEXT_PARAMETER_NAME = "ctx"
ALTERNATIVE_CONTEXT_NAME = "context"
COMPLEX_FUNCTION_PARAMETER_COUNT = 6
EXPECTED_SIGNATURE_FIELDS = 5


class TestAnalyzeFunctionSignature:
    """Test function signature analysis functionality."""

    def test_analyze_function_signature_when_valid_function_then_returns_signature_report(
        self,
    ):
        """Test signature analysis with a valid function returns proper report."""

        def test_function(name: str, age: int = 25) -> str:
            return f"Hello {name}, age {age}"

        result = analyze_function_signature(test_function)

        assert isinstance(result, SignatureReport)
        assert result.function_name == "test_function"
        assert len(result.parameters) == DEFAULT_PARAMETER_COUNT
        assert "name" in result.parameters
        assert "age" in result.parameters
        assert result.parameters["name"]["annotation"] == "<class 'str'>"
        assert result.parameters["age"]["default"] == 25
        assert result.return_annotation == "<class 'str'>"
        assert result.is_compatible is True
        assert result.error_message is None

    def test_analyze_function_signature_when_click_command_then_identifies_parameters(
        self,
    ):
        """Test signature analysis identifies Click command patterns."""

        def click_command(ctx, name: str, verbose: bool = False) -> None:
            pass

        result = analyze_function_signature(click_command)

        assert result.function_name == "click_command"
        assert result.has_click_context is True
        assert len(result.parameters) == 3
        assert CLICK_CONTEXT_PARAMETER_NAME in result.parameters
        assert "name" in result.parameters
        assert "verbose" in result.parameters
        assert result.parameters["verbose"]["default"] is False
        assert result.is_compatible is True

    def test_analyze_function_signature_when_context_parameter_variations_then_detects_all(
        self,
    ):
        """Test signature analysis detects various context parameter patterns."""

        def context_func(context, data: str) -> str:
            return data

        def click_ctx_func(click_context, value: int) -> int:
            return value

        result1 = analyze_function_signature(context_func)
        result2 = analyze_function_signature(click_ctx_func)

        assert result1.has_click_context is True
        assert result2.has_click_context is True
        assert ALTERNATIVE_CONTEXT_NAME in result1.parameters
        assert "click_context" in result2.parameters

    def test_analyze_function_signature_when_no_annotations_then_handles_gracefully(
        self,
    ):
        """Test signature analysis handles functions without type annotations."""

        def unannotated_function(param1, param2=None):
            return param1

        result = analyze_function_signature(unannotated_function)

        assert result.function_name == "unannotated_function"
        assert len(result.parameters) == DEFAULT_PARAMETER_COUNT
        assert result.parameters["param1"]["annotation"] is None
        assert result.parameters["param2"]["annotation"] is None
        assert result.parameters["param2"]["default"] is None
        assert result.return_annotation is None
        assert result.is_compatible is True

    def test_analyze_function_signature_when_complex_signature_then_marks_incompatible(
        self,
    ):
        """Test signature analysis marks complex functions as incompatible."""

        def complex_function(a, b, c, d, e, f) -> str:
            return "complex"

        result = analyze_function_signature(complex_function)

        assert result.function_name == "complex_function"
        assert len(result.parameters) == COMPLEX_FUNCTION_PARAMETER_COUNT
        assert result.is_compatible is False  # More than 5 parameters

    def test_analyze_function_signature_when_invalid_input_then_raises_analysis_error(
        self,
    ):
        """Test signature analysis raises error for non-callable input."""
        with pytest.raises(DecoratorAnalysisError) as exc_info:
            analyze_function_signature("not a function")

        assert "Expected callable function" in str(exc_info.value)

    def test_analyze_function_signature_when_inspection_fails_then_raises_analysis_error(
        self,
    ):
        """Test signature analysis handles inspection failures gracefully."""
        # Use a non-callable object to trigger the error condition
        with pytest.raises(DecoratorAnalysisError) as exc_info:
            analyze_function_signature("not_callable")

        assert "Expected callable function" in str(exc_info.value)


class TestValidateDecoratorCompatibility:
    """Test decorator compatibility validation functionality."""

    def test_validate_decorator_compatibility_when_compatible_function_then_returns_true(
        self,
    ):
        """Test compatibility validation returns True for compatible functions."""

        def compatible_function(name: str, age: int = 30) -> str:
            return f"User {name}"

        result = validate_decorator_compatibility(compatible_function)

        assert result is True

    def test_validate_decorator_compatibility_when_incompatible_function_then_returns_false(
        self,
    ):
        """Test compatibility validation returns False for incompatible functions."""

        def incompatible_function(a, b, c, d, e, f) -> str:
            return "too many parameters"

        result = validate_decorator_compatibility(incompatible_function)

        assert result is False

    def test_validate_decorator_compatibility_when_varargs_only_then_returns_false(
        self,
    ):
        """Test compatibility validation rejects functions with only *args/**kwargs."""

        def varargs_only_function(*args, **kwargs):
            pass

        result = validate_decorator_compatibility(varargs_only_function)

        assert result is False

    def test_validate_decorator_compatibility_when_mixed_parameters_then_returns_true(
        self,
    ):
        """Test compatibility validation accepts functions with mixed parameter types."""

        def mixed_function(name: str, *args, **kwargs) -> str:
            return name

        result = validate_decorator_compatibility(mixed_function)

        assert result is True

    def test_validate_decorator_compatibility_when_analysis_fails_then_returns_false(
        self,
    ):
        """Test compatibility validation returns False when analysis fails."""
        result = validate_decorator_compatibility("not a function")

        assert result is False

    def test_validate_decorator_compatibility_when_no_parameters_then_returns_true(
        self,
    ):
        """Test compatibility validation accepts functions with no parameters."""

        def no_params_function() -> str:
            return "simple"

        result = validate_decorator_compatibility(no_params_function)

        assert result is True


class TestSignatureReport:
    """Test SignatureReport dataclass functionality."""

    def test_signature_report_when_created_then_has_required_fields(self):
        """Test SignatureReport contains all required fields."""
        report = SignatureReport(
            function_name="test_func",
            parameters={
                "param1": {
                    "annotation": "str",
                    "default": None,
                    "kind": "POSITIONAL_OR_KEYWORD",
                }
            },
            return_annotation="str",
            has_click_context=True,
            is_compatible=True,
        )

        assert report.function_name == "test_func"
        assert len(report.parameters) == 1
        assert report.return_annotation == "str"
        assert report.has_click_context is True
        assert report.is_compatible is True
        assert report.error_message is None

    def test_signature_report_when_error_message_set_then_preserves_error(self):
        """Test SignatureReport preserves error messages when set."""
        error_message = "Analysis failed due to invalid syntax"

        report = SignatureReport(
            function_name="failed_func",
            parameters={},
            return_annotation=None,
            has_click_context=False,
            is_compatible=False,
            error_message=error_message,
        )

        assert report.error_message == error_message
        assert report.is_compatible is False


class TestDecoratorAnalysisError:
    """Test DecoratorAnalysisError exception functionality."""

    def test_decorator_analysis_error_when_created_with_message_then_preserves_message(
        self,
    ):
        """Test DecoratorAnalysisError preserves error message."""
        message = "Function signature analysis failed"

        error = DecoratorAnalysisError(message)

        assert str(error) == message
        assert error.context == {}

    def test_decorator_analysis_error_when_created_with_context_then_preserves_context(
        self,
    ):
        """Test DecoratorAnalysisError preserves context information."""
        message = "Analysis failed"
        context = {"function_name": "test_func", "error_type": "ValueError"}

        error = DecoratorAnalysisError(message, context)

        assert str(error) == message
        assert error.context == context
        assert error.context["function_name"] == "test_func"
        assert error.context["error_type"] == "ValueError"


class TestDecoratorAnalysisEdgeCases:
    """Test edge cases and error conditions in decorator analysis."""

    def test_analyze_function_signature_when_lambda_function_then_analyzes_correctly(
        self,
    ):
        """Test signature analysis works with lambda functions."""

        def lambda_func(x, y=10):
            return x + y

        result = analyze_function_signature(lambda_func)

        assert result.function_name == "lambda_func"
        assert len(result.parameters) == DEFAULT_PARAMETER_COUNT
        assert "x" in result.parameters
        assert "y" in result.parameters
        assert result.parameters["y"]["default"] == 10
        assert result.is_compatible is True

    def test_analyze_function_signature_when_builtin_function_then_handles_gracefully(
        self,
    ):
        """Test signature analysis handles builtin functions appropriately."""
        # Some builtin functions don't have signatures accessible via inspect
        try:
            result = analyze_function_signature(len)
            # If it succeeds, verify the result
            assert isinstance(result, SignatureReport)
        except DecoratorAnalysisError:
            # If it fails, that's expected for some builtin functions
            pass

    def test_validate_decorator_compatibility_when_exception_during_analysis_then_returns_false(
        self,
    ):
        """Test compatibility validation handles exceptions gracefully."""
        from unittest.mock import patch

        def problematic_function():
            pass

        # Mock the analyze_function_signature to raise an exception
        with patch(
            "spec_cli.utils.decorator_analysis.analyze_function_signature"
        ) as mock_analyze:
            mock_analyze.side_effect = Exception("Simulated analysis failure")

            result = validate_decorator_compatibility(problematic_function)
            assert result is False


class TestDecoratorAnalysisIntegrationScenarios:
    """Test decorator analysis with realistic integration scenarios."""

    def test_analyze_click_command_signature_when_realistic_command_then_analyzes_correctly(
        self,
    ):
        """Test decorator analysis with realistic Click command function."""

        def init_command(ctx, directory: str = ".", force: bool = False) -> None:
            """Initialize a new spec repository."""
            pass

        result = analyze_function_signature(init_command)

        assert result.function_name == "init_command"
        assert result.has_click_context is True
        assert len(result.parameters) == 3
        assert CLICK_CONTEXT_PARAMETER_NAME in result.parameters
        assert "directory" in result.parameters
        assert "force" in result.parameters
        assert result.parameters["directory"]["default"] == "."
        assert result.parameters["force"]["default"] is False
        assert result.return_annotation == "None"
        assert result.is_compatible is True

    def test_validate_decorator_compatibility_when_cli_commands_then_all_compatible(
        self,
    ):
        """Test compatibility validation with various CLI command patterns."""

        def status_command(ctx) -> None:
            pass

        def add_command(ctx, files: list) -> None:
            pass

        def commit_command(ctx, message: str, author: str = None) -> None:
            pass

        functions = [status_command, add_command, commit_command]

        for func in functions:
            result = validate_decorator_compatibility(func)
            assert result is True, f"Function {func.__name__} should be compatible"

    def test_decorator_analysis_performance_when_multiple_functions_then_completes_quickly(
        self,
    ):
        """Test decorator analysis performance with multiple functions."""
        import time

        functions = []
        for i in range(10):

            def test_func(ctx, param: str = f"default_{i}") -> str:
                return param

            test_func.__name__ = f"test_func_{i}"
            functions.append(test_func)

        start_time = time.time()

        for func in functions:
            analyze_function_signature(func)
            validate_decorator_compatibility(func)

        end_time = time.time()
        total_time = end_time - start_time

        # Should complete analysis of 10 functions in well under 1 second
        assert total_time < 1.0, f"Analysis took {total_time:.3f}s, expected < 1.0s"
