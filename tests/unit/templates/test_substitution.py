from datetime import datetime

from spec_cli.templates.substitution import TemplateSubstitution


class TestTemplateSubstitution:
    """Test TemplateSubstitution class."""

    def test_substitution_replaces_simple_variables(self) -> None:
        """Test that simple variable substitution works."""
        substitution = TemplateSubstitution()
        template = "Hello {{name}}, welcome to {{project}}!"
        variables = {"name": "Developer", "project": "spec-cli"}

        result = substitution.substitute(template, variables)
        assert result == "Hello Developer, welcome to spec-cli!"

    def test_substitution_handles_missing_variables(self) -> None:
        """Test that missing variables are left as placeholders."""
        substitution = TemplateSubstitution()
        template = "Hello {{name}}, your score is {{score}} out of {{total}}."
        variables = {"name": "Alice", "score": 95}

        result = substitution.substitute(template, variables)
        assert result == "Hello Alice, your score is 95 out of {{total}}."

    def test_substitution_preserves_unresolved_placeholders(self) -> None:
        """Test that unresolved placeholders are preserved."""
        substitution = TemplateSubstitution()
        template = "File: {{filename}}, Author: {{author}}, Status: {{status}}"
        variables = {"filename": "test.py"}

        result = substitution.substitute(template, variables)
        assert "test.py" in result
        assert "{{author}}" in result
        assert "{{status}}" in result

    def test_substitution_handles_empty_template(self) -> None:
        """Test substitution with empty template."""
        substitution = TemplateSubstitution()
        result = substitution.substitute("", {"name": "test"})
        assert result == ""

    def test_substitution_handles_no_variables(self) -> None:
        """Test substitution with no variables in template."""
        substitution = TemplateSubstitution()
        template = "This is a plain text template with no variables."
        result = substitution.substitute(template, {"unused": "value"})
        assert result == template


class TestBuiltinVariables:
    """Test built-in variable generation."""

    def test_builtin_variables_generation(self) -> None:
        """Test that built-in variables are generated correctly."""
        substitution = TemplateSubstitution()
        template = "Date: {{date}}, Year: {{year}}, Month: {{month}}"

        result = substitution.substitute(template, {})

        # Check that placeholders were replaced
        assert "{{date}}" not in result
        assert "{{year}}" not in result
        assert "{{month}}" not in result

        # Check format
        assert len(result.split("Date: ")[1].split(",")[0]) == 10  # YYYY-MM-DD format
        assert str(datetime.now().year) in result
        assert datetime.now().strftime("%B") in result

    def test_builtin_variables_user_override(self) -> None:
        """Test that user variables override built-in variables."""
        substitution = TemplateSubstitution()
        template = "Date: {{date}}, Custom: {{custom}}"
        variables = {"date": "2023-01-01", "custom": "value"}

        result = substitution.substitute(template, variables)
        assert "Date: 2023-01-01" in result
        assert "Custom: value" in result

    def test_custom_builtin_generator_addition(self) -> None:
        """Test adding custom built-in generators."""
        substitution = TemplateSubstitution()

        # Add custom generator
        substitution.add_builtin_generator("project_name", lambda: "spec-cli")

        template = "Project: {{project_name}}, Date: {{date}}"
        result = substitution.substitute(template, {})

        assert "Project: spec-cli" in result
        assert "{{project_name}}" not in result

        # Test removal
        removed = substitution.remove_builtin_generator("project_name")
        assert removed is True

        # Test that it's no longer available
        result2 = substitution.substitute(template, {})
        assert "{{project_name}}" in result2


class TestVariableFormatting:
    """Test variable value formatting."""

    def test_variable_value_formatting_types(self) -> None:
        """Test formatting of different variable value types."""
        substitution = TemplateSubstitution()

        # Test None
        assert substitution.test_variable_substitution("test", None) == "[To be filled]"

        # Test boolean
        assert substitution.test_variable_substitution("test", True) == "Yes"
        assert substitution.test_variable_substitution("test", False) == "No"

        # Test string
        assert substitution.test_variable_substitution("test", "hello") == "hello"

        # Test number
        assert substitution.test_variable_substitution("test", 42) == "42"

        # Test list
        list_result = substitution.test_variable_substitution(
            "test", ["item1", "item2"]
        )
        assert "- item1" in list_result
        assert "- item2" in list_result

        # Test dict
        dict_result = substitution.test_variable_substitution(
            "test", {"key1": "val1", "key2": "val2"}
        )
        assert "**key1**: val1" in dict_result
        assert "**key2**: val2" in dict_result

    def test_variable_value_formatting_edge_cases(self) -> None:
        """Test edge cases in variable formatting."""
        substitution = TemplateSubstitution()

        # Empty list
        assert substitution.test_variable_substitution("test", []) == "[None specified]"

        # Empty dict
        assert substitution.test_variable_substitution("test", {}) == "[None specified]"

        # Empty string
        assert substitution.test_variable_substitution("test", "") == ""


class TestTemplateAnalysis:
    """Test template analysis functionality."""

    def test_template_syntax_validation(self) -> None:
        """Test template syntax validation."""
        substitution = TemplateSubstitution()

        # Valid template
        valid_template = "Hello {{name}}, today is {{date}}."
        issues = substitution.validate_template_syntax(valid_template)
        assert issues == []

        # Unmatched delimiters
        bad_template1 = "Hello {{name}, missing close delimiter"
        issues1 = substitution.validate_template_syntax(bad_template1)
        assert len(issues1) > 0
        assert "mismatched delimiters" in issues1[0].lower()

        # Empty variables
        bad_template2 = "Hello {{}}, empty variable"
        issues2 = substitution.validate_template_syntax(bad_template2)
        assert len(issues2) > 0
        assert "empty variable" in " ".join(issues2).lower()

    def test_variable_extraction_from_template(self) -> None:
        """Test extraction of variables from templates."""
        substitution = TemplateSubstitution()

        template = (
            "File: {{filename}}, Author: {{author}}, Date: {{date}}, Status: {{status}}"
        )
        variables = substitution.get_variables_in_template(template)

        expected = {"filename", "author", "date", "status"}
        assert variables == expected

        # Test with no variables
        empty_template = "This has no variables"
        empty_vars = substitution.get_variables_in_template(empty_template)
        assert empty_vars == set()

    def test_substitution_preview_functionality(self) -> None:
        """Test substitution preview functionality."""
        substitution = TemplateSubstitution()

        template = "Project: {{project}}, Date: {{date}}, Author: {{author}}"
        variables = {"project": "spec-cli", "author": "Developer"}

        preview = substitution.preview_substitution(template, variables)

        assert preview["template_length"] == len(template)
        assert "project" in preview["variables_found"]
        assert "date" in preview["variables_found"]
        assert "author" in preview["variables_found"]
        assert "project" in preview["variables_resolved"]
        assert "author" in preview["variables_resolved"]
        assert "date" in preview["builtin_variables_used"]
        assert preview["syntax_issues"] == []

    def test_substitution_statistics_calculation(self) -> None:
        """Test substitution statistics calculation."""
        substitution = TemplateSubstitution()

        template = (
            "Name: {{name}}, Date: {{date}}, Score: {{score}}, Max: {{max_score}}"
        )
        variables = {"name": "Alice", "score": 95}

        stats = substitution.get_substitution_stats(template, variables)

        assert stats["template_length"] == len(template)
        assert stats["unique_variables"] == 4
        assert stats["provided_variables"] == 2
        assert stats["builtin_variables_needed"] == 1  # date
        assert stats["resolvable_variables"] == 3  # name, score, date
        assert stats["unresolvable_variables"] == 1  # max_score
        assert stats["substitution_coverage"] == 75.0  # 3/4 * 100
        assert stats["syntax_valid"] is True


class TestCustomDelimiters:
    """Test custom delimiter functionality."""

    def test_custom_delimiters_initialization(self) -> None:
        """Test initialization with custom delimiters."""
        substitution = TemplateSubstitution("[[", "]]")

        template = "Hello [[name]], welcome to [[project]]!"
        variables = {"name": "Developer", "project": "spec-cli"}

        result = substitution.substitute(template, variables)
        assert result == "Hello Developer, welcome to spec-cli!"

    def test_delimiter_change_at_runtime(self) -> None:
        """Test changing delimiters at runtime."""
        substitution = TemplateSubstitution()

        # Test with default delimiters
        result1 = substitution.substitute("Hello {{name}}", {"name": "World"})
        assert result1 == "Hello World"

        # Change delimiters
        substitution.change_delimiters("[[", "]]")

        # Test with new delimiters
        result2 = substitution.substitute("Hello [[name]]", {"name": "Universe"})
        assert result2 == "Hello Universe"

        # Old delimiters should not work
        result3 = substitution.substitute("Hello {{name}}", {"name": "Galaxy"})
        assert result3 == "Hello {{name}}"  # Not substituted


class TestIntegrationScenarios:
    """Test integration scenarios and edge cases."""

    def test_real_template_substitution(self) -> None:
        """Test substitution with realistic template content."""
        substitution = TemplateSubstitution()

        template = """# {{filename}}

**Location**: {{filepath}}
**Purpose**: {{purpose}}
**Date**: {{date}}

## Overview

{{overview}}

## Usage

```{{file_extension}}
{{example_usage}}
```

## Notes

{{notes}}
"""

        variables = {
            "filename": "user_model.py",
            "filepath": "src/models/user_model.py",
            "purpose": "User data model and validation",
            "overview": "Defines the User class with validation methods",
            "file_extension": "python",
            "example_usage": "user = User(name='Alice', email='alice@example.com')",
            "notes": "Implements Pydantic validation for user data",
        }

        result = substitution.substitute(template, variables)

        # Check that all variables were substituted
        assert "user_model.py" in result
        assert "src/models/user_model.py" in result
        assert "User data model" in result
        assert "```python" in result
        assert "user = User(" in result
        assert "{{" not in result  # No placeholders should remain

    def test_builtin_variables_list(self) -> None:
        """Test getting list of built-in variables."""
        substitution = TemplateSubstitution()
        builtin_vars = substitution.get_builtin_variables()

        expected_vars = ["date", "datetime", "timestamp", "year", "month", "day"]
        for var in expected_vars:
            assert var in builtin_vars

    def test_substitution_error_handling(self) -> None:
        """Test error handling in substitution."""
        substitution = TemplateSubstitution()

        # Mock an error in built-in generator
        def error_generator() -> str:
            raise ValueError("Test error")

        substitution.add_builtin_generator("error_var", error_generator)

        # Should not raise error, just log warning
        template = "Test: {{error_var}}"
        result = substitution.substitute(template, {})
        assert "{{error_var}}" in result  # Should remain unresolved

    def test_multiple_same_variable(self) -> None:
        """Test template with multiple instances of same variable."""
        substitution = TemplateSubstitution()

        template = "{{name}} says hello. {{name}} is happy. {{name}} waves goodbye."
        variables = {"name": "Alice"}

        result = substitution.substitute(template, variables)
        assert result == "Alice says hello. Alice is happy. Alice waves goodbye."
        assert "{{name}}" not in result
