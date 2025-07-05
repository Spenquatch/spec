"""Tests for migration utilities for dependency injection transitions."""

import inspect
from unittest.mock import Mock

import pytest

from spec_cli.utils.migration_utils import (
    MigrationError,
    get_migration_requirements,
    migrate_command_signature,
    validate_migration_behavior,
)

# Test constants
CONTEXT_PARAM_NAME = "context"
DEFAULT_FUNC_NAME = "test_function"
CLICK_ATTR_NAMES = ["__click_params__", "__click_group__", "__click_command__"]


class TestMigrationUtils:
    """Test command migration utilities."""

    def test_migrate_command_signature_when_valid_function_then_adds_context_param(
        self,
    ):
        """Test migration adds context parameter to valid function signature."""

        def original_func(debug: bool, verbose: bool) -> str:
            return "result"

        # Migrate function signature
        migrated = migrate_command_signature(original_func, CONTEXT_PARAM_NAME)

        # Verify signature modification
        migrated_sig = inspect.signature(migrated)
        param_names = list(migrated_sig.parameters.keys())

        assert param_names[0] == CONTEXT_PARAM_NAME
        assert param_names[1:] == ["debug", "verbose"]
        assert len(migrated_sig.parameters) == 3

    def test_validate_migration_behavior_when_identical_behavior_then_returns_true(
        self,
    ):
        """Test validation returns True when migration preserves behavior."""

        def original_func(debug: bool) -> str:
            return "result"

        # Migrate function
        migrated_func = migrate_command_signature(original_func, CONTEXT_PARAM_NAME)

        # Validate migration behavior
        result = validate_migration_behavior(original_func, migrated_func)

        assert result is True

    def test_migrate_command_signature_when_invalid_function_then_raises_type_error(
        self,
    ):
        """Test migration raises TypeError for invalid function input."""
        with pytest.raises(TypeError, match="Expected callable"):
            migrate_command_signature("not_a_function", CONTEXT_PARAM_NAME)  # type: ignore[arg-type]

    def test_migrate_command_signature_when_invalid_context_param_then_raises_type_error(
        self,
    ):
        """Test migration raises TypeError for invalid context parameter name."""

        def valid_func() -> None:
            pass

        with pytest.raises(TypeError, match="context_param must be a non-empty string"):
            migrate_command_signature(valid_func, "")

    def test_migrate_command_signature_when_empty_context_param_then_raises_type_error(
        self,
    ):
        """Test migration raises TypeError for empty context parameter name."""

        def valid_func() -> None:
            pass

        with pytest.raises(TypeError, match="context_param must be a non-empty string"):
            migrate_command_signature(valid_func, "   ")

    def test_migrate_command_signature_preserves_function_metadata(self):
        """Test migration preserves original function metadata."""

        def original_func(debug: bool) -> str:
            """Original function docstring."""
            return "result"

        original_func.__module__ = "test_module"

        # Migrate function
        migrated = migrate_command_signature(original_func, CONTEXT_PARAM_NAME)

        # Verify metadata preservation
        assert migrated.__name__ == "original_func"
        assert migrated.__doc__ == "Original function docstring."
        assert migrated.__module__ == "test_module"

    def test_migrate_command_signature_preserves_click_attributes(self):
        """Test migration preserves Click decorator attributes."""

        def original_func() -> None:
            pass

        # Add Click attributes
        original_func.__click_params__ = ["param1", "param2"]  # type: ignore[attr-defined]
        original_func.__click_command__ = True  # type: ignore[attr-defined]

        # Migrate function
        migrated = migrate_command_signature(original_func, CONTEXT_PARAM_NAME)

        # Verify Click attributes preserved
        assert hasattr(migrated, "__click_params__")
        assert hasattr(migrated, "__click_command__")
        assert migrated.__click_params__ == ["param1", "param2"]  # type: ignore[attr-defined]
        assert migrated.__click_command__ is True  # type: ignore[attr-defined]

    def test_migrated_function_execution_skips_context_parameter(self):
        """Test migrated function properly skips context parameter during execution."""

        def original_func(debug: bool, verbose: bool) -> str:
            return f"debug={debug}, verbose={verbose}"

        # Migrate function
        migrated = migrate_command_signature(original_func, CONTEXT_PARAM_NAME)

        # Execute with context as first argument
        mock_context = Mock()
        result = migrated(mock_context, True, False)

        # Verify original function received correct arguments
        assert result == "debug=True, verbose=False"

    def test_migrated_function_when_no_args_then_raises_migration_error(self):
        """Test migrated function raises error when called without context."""

        def original_func() -> str:
            return "result"

        # Migrate function
        migrated = migrate_command_signature(original_func, CONTEXT_PARAM_NAME)

        # Execute without arguments
        with pytest.raises(MigrationError, match="Context parameter required"):
            migrated()

    def test_validate_migration_behavior_when_parameter_count_mismatch_then_raises_error(
        self,
    ):
        """Test validation raises error when parameter counts don't match expected pattern."""

        def original_func(debug: bool) -> None:
            pass

        def invalid_migrated(context: str, debug: bool, extra: str) -> None:
            pass

        with pytest.raises(MigrationError, match="Parameter count mismatch"):
            validate_migration_behavior(original_func, invalid_migrated)

    def test_validate_migration_behavior_when_parameter_names_mismatch_then_raises_error(
        self,
    ):
        """Test validation raises error when parameter names don't match."""

        def original_func(debug: bool) -> None:
            pass

        def invalid_migrated(
            context: str, verbose: bool
        ) -> None:  # Wrong parameter name
            pass

        with pytest.raises(MigrationError, match="Parameter names mismatch"):
            validate_migration_behavior(original_func, invalid_migrated)

    def test_validate_migration_behavior_when_non_callable_original_then_raises_type_error(
        self,
    ):
        """Test validation raises TypeError for non-callable original."""

        def valid_migrated(context: str) -> None:
            pass

        with pytest.raises(TypeError, match="Expected callable original"):
            validate_migration_behavior("not_callable", valid_migrated)  # type: ignore[arg-type]

    def test_validate_migration_behavior_when_non_callable_migrated_then_raises_type_error(
        self,
    ):
        """Test validation raises TypeError for non-callable migrated."""

        def valid_original() -> None:
            pass

        with pytest.raises(TypeError, match="Expected callable migrated"):
            validate_migration_behavior(valid_original, "not_callable")  # type: ignore[arg-type]

    def test_validate_migration_behavior_preserves_docstring(self):
        """Test validation checks that docstring is preserved."""

        def original_func() -> None:
            """Original docstring."""
            pass

        def migrated_func(context: str) -> None:
            """Different docstring."""
            pass

        with pytest.raises(MigrationError, match="Attribute __doc__ not preserved"):
            validate_migration_behavior(original_func, migrated_func)

    def test_validate_migration_behavior_preserves_click_attributes(self):
        """Test validation checks that Click attributes are preserved."""

        def original_func() -> None:
            pass

        def migrated_func(context: str) -> None:
            pass

        # Add Click attribute only to original
        original_func.__click_params__ = ["param1"]  # type: ignore[attr-defined]

        with pytest.raises(
            MigrationError, match="Click attribute __click_params__ not preserved"
        ):
            validate_migration_behavior(original_func, migrated_func)

    def test_get_migration_requirements_when_simple_function_then_returns_basic_requirements(
        self,
    ):
        """Test migration requirements analysis for simple function."""

        def simple_func(debug: bool) -> None:
            """Simple function."""
            pass

        # Analyze migration requirements
        requirements = get_migration_requirements(simple_func)

        # Verify requirements
        assert requirements["function_name"] == "simple_func"
        assert requirements["parameter_count"] == 1
        assert requirements["parameters"] == ["debug"]
        assert requirements["has_click_decorators"] is False
        assert requirements["has_docstring"] is True
        assert requirements["migration_complexity"] == "low"

    def test_get_migration_requirements_when_complex_function_then_returns_high_complexity(
        self,
    ):
        """Test migration requirements analysis for complex function."""

        def complex_func(a: str, b: int, c: bool, d: float, e: list, f: dict) -> None:
            pass

        # Analyze migration requirements
        requirements = get_migration_requirements(complex_func)

        # Verify high complexity detection
        assert requirements["migration_complexity"] == "high"
        assert requirements["parameter_count"] == 6

    def test_get_migration_requirements_when_medium_complexity_then_returns_medium(
        self,
    ):
        """Test migration requirements analysis for medium complexity function."""

        def medium_func(debug: bool, verbose: bool, force: bool) -> None:
            pass

        # Analyze migration requirements
        requirements = get_migration_requirements(medium_func)

        # Verify medium complexity detection
        assert requirements["migration_complexity"] == "medium"
        assert requirements["parameter_count"] == 3

    def test_get_migration_requirements_when_var_args_then_returns_high_complexity(
        self,
    ):
        """Test migration requirements detects high complexity for var args."""

        def var_args_func(*args, **kwargs) -> None:  # type: ignore[no-untyped-def]
            pass

        # Analyze migration requirements
        requirements = get_migration_requirements(var_args_func)

        # Verify high complexity and var args detection
        assert requirements["migration_complexity"] == "high"
        assert requirements["has_var_args"] is True

    def test_get_migration_requirements_when_click_decorators_then_detects_click_usage(
        self,
    ):
        """Test migration requirements detects Click decorator usage."""

        def click_func() -> None:
            pass

        # Add Click attributes
        click_func.__click_params__ = []  # type: ignore[attr-defined]

        # Analyze migration requirements
        requirements = get_migration_requirements(click_func)

        # Verify Click detection
        assert requirements["has_click_decorators"] is True

    def test_get_migration_requirements_when_non_callable_then_raises_type_error(self):
        """Test migration requirements raises TypeError for non-callable."""
        with pytest.raises(TypeError, match="Expected callable"):
            get_migration_requirements("not_callable")  # type: ignore[arg-type]
