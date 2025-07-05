"""Integration tests for Slice P2.2a: Decorator Pattern Analysis with CLI Function Patterns."""


from spec_cli.utils.decorator_analysis import (
    SignatureReport,
    analyze_function_signature,
    validate_decorator_compatibility,
)

# Test constants
EXPECTED_CLI_COMMAND_PATTERNS = 4
INTEGRATION_PERFORMANCE_THRESHOLD = 0.1


class TestDecoratorAnalysisIntegration:
    """Integration tests for decorator analysis with CLI function patterns."""

    def test_decorator_analysis_integration_when_real_cli_functions_then_validates_compatibility(self):
        """End-to-end test analyzing CLI command function patterns for decorator compatibility."""
        # Create functions that mirror actual CLI command patterns
        def init_like_command(ctx, directory: str = ".", force: bool = False) -> None:
            """Function mimicking init command pattern."""
            pass

        def status_like_command(ctx) -> None:
            """Function mimicking status command pattern."""
            pass

        def add_like_command(ctx, files: list[str]) -> None:
            """Function mimicking add command pattern."""
            pass

        def commit_like_command(ctx, message: str, author: str = None) -> None:
            """Function mimicking commit command pattern."""
            pass

        cli_functions = [
            init_like_command,
            status_like_command,
            add_like_command,
            commit_like_command
        ]

        analysis_results = []
        compatibility_results = []

        # Analyze each CLI function pattern
        for func in cli_functions:
            # Test signature analysis
            signature_report = analyze_function_signature(func)
            analysis_results.append(signature_report)

            # Test compatibility validation
            is_compatible = validate_decorator_compatibility(func)
            compatibility_results.append(is_compatible)

        # Verify all functions were analyzed successfully
        assert len(analysis_results) == EXPECTED_CLI_COMMAND_PATTERNS
        assert len(compatibility_results) == EXPECTED_CLI_COMMAND_PATTERNS

        # Verify all CLI functions have valid signature reports
        for i, result in enumerate(analysis_results):
            func_name = cli_functions[i].__name__
            assert isinstance(result, SignatureReport), f"Function {func_name} analysis failed"
            assert result.function_name == func_name
            assert result.error_message is None, f"Function {func_name} had analysis error: {result.error_message}"

            # Verify CLI functions have reasonable parameter counts
            param_count = len(result.parameters)
            assert param_count <= 5, f"Function {func_name} has {param_count} parameters (too complex)"

        # Verify all CLI functions are decorator-compatible
        compatible_count = sum(compatibility_results)
        assert compatible_count == EXPECTED_CLI_COMMAND_PATTERNS, f"Only {compatible_count} of {EXPECTED_CLI_COMMAND_PATTERNS} functions are compatible"

        # Verify Click context detection works with CLI patterns
        context_detected_count = sum(1 for result in analysis_results if result.has_click_context)
        assert context_detected_count == EXPECTED_CLI_COMMAND_PATTERNS, f"Click context detected in {context_detected_count} functions"

    def test_decorator_analysis_with_cli_function_signatures_when_analyzed_then_extracts_parameters(self):
        """Test decorator analysis extracts correct parameter information from CLI function patterns."""
        def init_pattern_command(ctx, directory: str = ".", force: bool = False) -> None:
            """CLI function pattern with context and optional parameters."""
            pass

        # Analyze command pattern
        result = analyze_function_signature(init_pattern_command)

        # Verify basic signature extraction
        assert result.function_name == "init_pattern_command"
        assert result.has_click_context is True
        assert len(result.parameters) == 3  # ctx, directory, force

        # Verify parameter details are extracted correctly
        assert "ctx" in result.parameters
        assert "directory" in result.parameters
        assert "force" in result.parameters

        # Verify parameter types and defaults
        assert result.parameters["directory"]["annotation"] == "<class 'str'>"
        assert result.parameters["directory"]["default"] == "."
        assert result.parameters["force"]["annotation"] == "<class 'bool'>"
        assert result.parameters["force"]["default"] is False
        assert result.return_annotation == "None"

    def test_decorator_compatibility_with_cli_patterns_when_validated_then_supports_injection(self):
        """Test compatibility validation works with CLI command patterns."""
        def simple_command(ctx) -> None:
            pass

        def complex_command(ctx, arg1: str, arg2: int = 10, flag: bool = False) -> str:
            return "result"

        def too_complex_command(ctx, a, b, c, d, e, f) -> None:
            pass

        cli_patterns = [simple_command, complex_command, too_complex_command]

        compatibility_results = {}
        signature_complexity = {}

        for func in cli_patterns:
            func_name = func.__name__

            # Check compatibility
            is_compatible = validate_decorator_compatibility(func)
            compatibility_results[func_name] = is_compatible

            # Analyze signature complexity
            signature = analyze_function_signature(func)
            signature_complexity[func_name] = {
                "param_count": len(signature.parameters),
                "has_context": signature.has_click_context,
                "return_annotation": signature.return_annotation
            }

        # Verify compatibility results
        assert compatibility_results["simple_command"] is True
        assert compatibility_results["complex_command"] is True
        assert compatibility_results["too_complex_command"] is False  # Too many parameters

        # Verify all compatible functions have Click context
        for func_name, is_compatible in compatibility_results.items():
            if is_compatible:
                complexity = signature_complexity[func_name]
                assert complexity["has_context"] is True, f"Compatible function {func_name} should have context"

    def test_decorator_analysis_performance_with_cli_patterns_when_analyzed_then_completes_quickly(self):
        """Test decorator analysis performance with CLI function patterns."""
        import time

        # Create multiple CLI-like functions
        cli_patterns = []
        for i in range(10):
            def cli_func(ctx, param: str = f"default_{i}") -> str:
                return param
            cli_func.__name__ = f"cli_command_{i}"
            cli_patterns.append(cli_func)

        # Test signature analysis performance
        start_time = time.time()
        for func in cli_patterns:
            analyze_function_signature(func)
        signature_analysis_time = time.time() - start_time

        # Test compatibility validation performance
        start_time = time.time()
        for func in cli_patterns:
            validate_decorator_compatibility(func)
        compatibility_validation_time = time.time() - start_time

        # Verify performance meets requirements
        total_time = signature_analysis_time + compatibility_validation_time
        assert total_time < INTEGRATION_PERFORMANCE_THRESHOLD, (
            f"Decorator analysis took {total_time:.3f}s, expected < {INTEGRATION_PERFORMANCE_THRESHOLD}s"
        )

    def test_decorator_analysis_error_handling_with_mixed_objects_when_issues_then_handles_gracefully(self):
        """Test error handling in decorator analysis with mixed object types."""
        def valid_cli_command(ctx, param: str) -> str:
            return param

        # Test with a list of mixed callable and non-callable objects
        test_objects = [
            valid_cli_command,  # Valid function
            "not_a_function",  # Invalid object
            lambda x: x,  # Lambda function
            len,  # Builtin function
        ]

        analysis_results = []
        compatibility_results = []

        for obj in test_objects:
            # Test signature analysis error handling
            try:
                result = analyze_function_signature(obj)
                analysis_results.append(("success", result))
            except Exception as e:
                analysis_results.append(("error", str(e)))

            # Test compatibility validation error handling (should never raise)
            is_compatible = validate_decorator_compatibility(obj)
            compatibility_results.append(is_compatible)

        # Verify error handling works correctly
        assert len(analysis_results) == len(test_objects)
        assert len(compatibility_results) == len(test_objects)

        # Valid CLI function should succeed
        assert analysis_results[0][0] == "success"
        assert compatibility_results[0] is True

        # Invalid objects should fail gracefully
        assert compatibility_results[1] is False  # String object

        # Lambda should work
        assert compatibility_results[2] is True

    def test_cross_slice_integration_p2_2a_to_p2_2b_decorator_design_handoff(self):
        """Validates decorator analysis provides sufficient design requirements for P2.2b implementation."""
        def target_init_command(ctx, directory: str = ".", force: bool = False) -> None:
            pass

        def target_add_command(ctx, files: list[str]) -> None:
            pass

        target_functions = [target_init_command, target_add_command]

        design_requirements = []

        for func in target_functions:
            signature_report = analyze_function_signature(func)
            is_compatible = validate_decorator_compatibility(func)

            # Extract design requirements from analysis
            requirement = {
                "function_name": signature_report.function_name,
                "parameter_count": len(signature_report.parameters),
                "has_context_parameter": signature_report.has_click_context,
                "is_decorator_compatible": is_compatible,
                "parameters": signature_report.parameters,
                "return_annotation": signature_report.return_annotation
            }
            design_requirements.append(requirement)

        # Verify design requirements are sufficient for P2.2b implementation
        for req in design_requirements:
            # Should have function identification
            assert req["function_name"], "Function name required for decorator application"

            # Should have parameter analysis for injection planning
            assert isinstance(req["parameters"], dict), "Parameter details required for injection"

            # Should have compatibility assessment
            assert isinstance(req["is_decorator_compatible"], bool), "Compatibility assessment required"

            # Context parameter detection should work for injection planning
            if req["has_context_parameter"]:
                # Should identify which parameter is the context
                context_params = [name for name, info in req["parameters"].items()
                                 if "ctx" in name.lower() or "context" in name.lower()]
                assert len(context_params) >= 1, f"Context parameter not identified in {req['function_name']}"

    def test_decorator_analysis_supports_p2_1b_click_integration(self):
        """Validates decorator design works with P2.1b Click context integration."""
        def click_integrated_command(ctx, name: str, verbose: bool = False) -> None:
            """Command that would be integrated with Click context."""
            pass

        def another_click_command(ctx, files: list[str] = None) -> None:
            """Another command with Click context integration."""
            pass

        cli_functions = [click_integrated_command, another_click_command]

        click_integration_compatibility = []

        for func in cli_functions:
            signature_report = analyze_function_signature(func)

            # Check Click integration compatibility
            click_compat = {
                "function_name": signature_report.function_name,
                "has_click_context": signature_report.has_click_context,
                "parameter_count": len(signature_report.parameters),
                "click_compatible": signature_report.has_click_context and signature_report.is_compatible
            }
            click_integration_compatibility.append(click_compat)

        # Verify Click integration support
        click_compatible_count = sum(1 for c in click_integration_compatibility if c["click_compatible"])
        assert click_compatible_count == 2, f"Only {click_compatible_count} functions support Click integration"

        # Verify context parameter detection for Click integration
        context_functions = [c for c in click_integration_compatibility if c["has_click_context"]]
        assert len(context_functions) == 2, "All test functions should have Click context"


class TestDecoratorPatternAnalysisForDependencyInjection:
    """Test decorator pattern analysis for dependency injection migration."""

    def test_decorator_pattern_analysis_for_dependency_injection(self):
        """Validates decorator patterns support dependency injection principles."""
        def injectable_init_command(ctx, directory: str = ".") -> None:
            pass

        def injectable_add_command(ctx, files: list[str]) -> None:
            pass

        def injectable_commit_command(ctx, message: str, author: str = None) -> None:
            pass

        injection_candidates = [injectable_init_command, injectable_add_command, injectable_commit_command]

        injection_analysis = []

        for func in injection_candidates:
            signature_report = analyze_function_signature(func)
            is_compatible = validate_decorator_compatibility(func)

            # Analyze for dependency injection suitability
            injection_info = {
                "function": func.__name__,
                "compatible": is_compatible,
                "context_param": signature_report.has_click_context,
                "param_count": len(signature_report.parameters),
                "injection_ready": is_compatible and signature_report.has_click_context
            }
            injection_analysis.append(injection_info)

        # Verify dependency injection readiness
        injection_ready_count = sum(1 for info in injection_analysis if info["injection_ready"])
        assert injection_ready_count == 3, f"Only {injection_ready_count} functions ready for dependency injection"

        # Verify suitable parameter patterns for injection
        for info in injection_analysis:
            assert info["injection_ready"], f"Function {info['function']} not ready for injection"
            assert info["param_count"] <= 5, f"Function {info['function']} too complex for injection"
            assert info["context_param"], f"Function {info['function']} missing context parameter"

    def test_context_injection_decorator_design_feasibility(self):
        """Validates context injection decorator design is feasible and implementable."""
        def feasible_init_command(ctx, directory: str = ".") -> None:
            pass

        def feasible_status_command(ctx) -> None:
            pass

        test_functions = [feasible_init_command, feasible_status_command]

        feasibility_results = []

        for func in test_functions:
            signature_report = analyze_function_signature(func)

            # Check injection feasibility
            feasibility = {
                "function_name": signature_report.function_name,
                "signature_analyzable": signature_report.error_message is None,
                "context_identifiable": signature_report.has_click_context,
                "parameter_structure_compatible": len(signature_report.parameters) <= 5,
                "injection_feasible": (
                    signature_report.error_message is None and
                    signature_report.has_click_context and
                    len(signature_report.parameters) <= 5
                )
            }
            feasibility_results.append(feasibility)

        # Verify injection feasibility
        feasible_count = sum(1 for f in feasibility_results if f["injection_feasible"])
        assert feasible_count == 2, f"Only {feasible_count} functions are injection-feasible"

        # Verify all required analysis capabilities exist
        for result in feasibility_results:
            assert result["signature_analyzable"], f"Cannot analyze {result['function_name']} signature"
            assert result["context_identifiable"], f"Cannot identify context in {result['function_name']}"
            assert result["parameter_structure_compatible"], f"Parameter structure incompatible for {result['function_name']}"
            assert result["injection_feasible"], f"Injection not feasible for {result['function_name']}"

