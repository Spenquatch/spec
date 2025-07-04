"""Template test infrastructure for comprehensive testing.

This module provides template fixtures, variable substitution mocking, and AI template
mocking utilities for testing all template functionality without external dependencies.
Supports template generation, variable substitution, and AI enhancement testing.
"""

import tempfile
from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
import yaml

from ...templates.ai_enhanced import TemplateResult
from ...templates.config import TemplateConfig
from ...templates.prompt_generator import PromptStructure
from ...templates.substitution import TemplateSubstitution


@dataclass
class TemplateFixture:
    """Template fixture for testing template operations."""

    name: str
    content: str
    variables: dict[str, Any] = field(default_factory=dict)
    config: TemplateConfig | None = None
    expected_output: str | None = None
    should_fail: bool = False
    error_type: type[Exception] | None = None


class TemplateFixtureGenerator:
    """Generates template fixtures for comprehensive testing."""

    def __init__(self) -> None:
        """Initialize the template fixture generator."""
        self.fixtures: dict[str, TemplateFixture] = {}

    def create_basic_template(
        self,
        name: str = "basic",
        variables: dict[str, Any] | None = None,
    ) -> TemplateFixture:
        """Create a basic template fixture.

        Args:
            name: Name of the template fixture
            variables: Variables for substitution

        Returns:
            TemplateFixture with basic template content
        """
        variables = variables or {"filename": "test_file.py", "purpose": "Testing"}
        content = """# {{filename}}

Purpose: {{purpose}}

Generated on: {{current_date}}

## Functions
{{#functions}}
- {{name}}: {{description}}
{{/functions}}
"""
        expected = f"""# {variables["filename"]}

Purpose: {variables["purpose"]}

Generated on: {datetime.now().strftime("%Y-%m-%d")}

## Functions

"""
        fixture = TemplateFixture(
            name=name,
            content=content,
            variables=variables,
            expected_output=expected,
        )
        self.fixtures[name] = fixture
        return fixture

    def create_ai_enhanced_template(
        self,
        name: str = "ai_enhanced",
        variables: dict[str, Any] | None = None,
    ) -> TemplateFixture:
        """Create an AI-enhanced template fixture.

        Args:
            name: Name of the template fixture
            variables: Variables for substitution

        Returns:
            TemplateFixture with AI enhancement markers
        """
        variables = variables or {"filename": "ai_test.py", "complexity": "high"}
        content = """# {{filename}}

{{ai:analyze_complexity}}
Complexity Level: {{complexity}}

{{ai:suggest_patterns}}
Recommended patterns based on analysis.

{{ai:generate_docs}}
Generated documentation content.
"""
        fixture = TemplateFixture(
            name=name,
            content=content,
            variables=variables,
        )
        self.fixtures[name] = fixture
        return fixture

    def create_error_template(
        self,
        name: str = "error",
        error_type: type[Exception] | None = None,
    ) -> TemplateFixture:
        """Create a template fixture that should cause errors.

        Args:
            name: Name of the error template fixture
            error_type: Expected exception type

        Returns:
            TemplateFixture configured to fail
        """
        content = "{{invalid_syntax}}"
        fixture = TemplateFixture(
            name=name,
            content=content,
            should_fail=True,
            error_type=error_type,
        )
        self.fixtures[name] = fixture
        return fixture

    def create_template_file(
        self,
        fixture: TemplateFixture,
        temp_dir: Path | None = None,
    ) -> Path:
        """Create a temporary template file from fixture.

        Args:
            fixture: Template fixture to write
            temp_dir: Optional temporary directory

        Returns:
            Path to created template file
        """
        if temp_dir is None:
            temp_dir = Path(tempfile.mkdtemp())

        template_file = temp_dir / f"{fixture.name}.spectemplate"
        template_file.write_text(fixture.content, encoding="utf-8")
        return template_file

    def create_config_file(
        self,
        index_content: str = "# {{filename}}\nDefault index content",
        history_content: str = "# {{filename}} History\nDefault history content",
        temp_dir: Path | None = None,
    ) -> Path:
        """Create a temporary template config file.

        Args:
            index_content: Content for index template
            history_content: Content for history template
            temp_dir: Optional temporary directory

        Returns:
            Path to created config file
        """
        if temp_dir is None:
            temp_dir = Path(tempfile.mkdtemp())

        config_file = temp_dir / ".spectemplate"
        config_data = {
            "index": index_content,
            "history": history_content,
            "version": "1.0",
            "ai_enabled": False,
        }
        config_file.write_text(yaml.dump(config_data), encoding="utf-8")
        return config_file


class VariableSubstitutionMocker:
    """Mock variable substitution operations for testing."""

    def __init__(self) -> None:
        """Initialize the variable substitution mocker."""
        self.substitution_history: list[dict[str, Any]] = []
        self.mock_substitution = Mock(spec=TemplateSubstitution)

        # Configure mock methods
        self.mock_substitution.substitute = Mock()  # type: ignore[method-assign]
        self.mock_substitution.validate_variables = Mock()  # type: ignore[method-assign]
        self.mock_substitution.get_validation_errors = Mock()  # type: ignore[method-assign]
        self.mock_substitution.reset_mock = Mock()  # type: ignore[method-assign]

    def mock_substitute(
        self,
        content: str,
        variables: dict[str, Any],
        expected_result: str | None = None,
        should_fail: bool = False,
        error_type: type[Exception] | None = None,
    ) -> Mock:
        """Mock template substitution operation.

        Args:
            content: Template content to substitute
            variables: Variables for substitution
            expected_result: Expected substitution result
            should_fail: Whether substitution should fail
            error_type: Exception type if should_fail is True

        Returns:
            Mock object configured for substitution
        """
        if should_fail and error_type:
            self.mock_substitution.substitute.side_effect = error_type("Mock error")
        else:
            result = expected_result or content.replace("{{test}}", "mocked")
            self.mock_substitution.substitute.return_value = result

        # Record substitution attempt
        self.substitution_history.append(
            {
                "content": content,
                "variables": variables,
                "result": expected_result,
                "failed": should_fail,
                "timestamp": datetime.now(),
            }
        )

        return self.mock_substitution

    def mock_validate_variables(
        self,
        variables: dict[str, Any],
        is_valid: bool = True,
        validation_errors: list[str] | None = None,
    ) -> Mock:
        """Mock variable validation.

        Args:
            variables: Variables to validate
            is_valid: Whether variables should be valid
            validation_errors: List of validation errors if invalid

        Returns:
            Mock object configured for validation
        """
        if is_valid:
            self.mock_substitution.validate_variables.return_value = True
        else:
            self.mock_substitution.validate_variables.return_value = False
            if validation_errors:
                self.mock_substitution.get_validation_errors.return_value = (
                    validation_errors
                )

        return self.mock_substitution

    def reset_history(self) -> None:
        """Reset substitution history and mock state."""
        self.substitution_history.clear()
        reset_mock = self.mock_substitution.reset_mock
        if hasattr(reset_mock, "return_value"):
            reset_mock.return_value = None  # type: ignore[attr-defined]
        reset_mock()


class AITemplateMocker:
    """Mock AI template operations for testing."""

    def __init__(self) -> None:
        """Initialize the AI template mocker."""
        self.generation_history: list[dict[str, Any]] = []
        self.mock_results: dict[str, TemplateResult] = {}

    def create_mock_result(
        self,
        name: str,
        success: bool = True,
        traditional_content: str = "Mock traditional content",
        ai_prompt: PromptStructure | None = None,
        variables: dict[str, Any] | None = None,
        error: str | None = None,
        processing_time_ms: int = 100,
    ) -> TemplateResult:
        """Create a mock template result.

        Args:
            name: Name of the mock result
            success: Whether processing was successful
            traditional_content: Traditional template content
            ai_prompt: AI prompt structure
            variables: Template variables
            error: Error message if failed
            processing_time_ms: Mock processing time

        Returns:
            TemplateResult with mock data
        """
        variables = variables or {}

        if ai_prompt is None and success:
            ai_prompt = PromptStructure(
                template_content="Mock template content",
                variables=variables,
                placeholders=["filename", "purpose"],
                sections={"main": "content"},
                ai_instructions="Mock AI instructions",
            )

        result = TemplateResult(
            success=success,
            traditional_content=traditional_content,
            ai_prompt=ai_prompt,
            variables=variables,
            error=error,
            processing_time_ms=processing_time_ms,
        )

        self.mock_results[name] = result
        return result

    def mock_ai_enhancement(
        self,
        template_content: str,
        expected_result: TemplateResult | None = None,
        should_fail: bool = False,
    ) -> TemplateResult:
        """Mock AI template enhancement.

        Args:
            template_content: Original template content
            expected_result: Expected enhancement result
            should_fail: Whether enhancement should fail

        Returns:
            TemplateResult with mocked AI enhancement
        """
        if should_fail:
            result = TemplateResult(
                success=False,
                error="Mock AI enhancement error",
            )
        elif expected_result:
            result = expected_result
        else:
            result = self.create_mock_result("default_enhancement")

        # Record enhancement attempt
        self.generation_history.append(
            {
                "input_content": template_content,
                "result": result,
                "timestamp": datetime.now(),
            }
        )

        return result

    def reset_history(self) -> None:
        """Reset generation history and mock results."""
        self.generation_history.clear()
        self.mock_results.clear()


# Pytest fixtures for template testing
@pytest.fixture
def template_fixture_generator() -> TemplateFixtureGenerator:
    """Provide template fixture generator for tests."""
    return TemplateFixtureGenerator()


@pytest.fixture
def variable_substitution_mocker() -> VariableSubstitutionMocker:
    """Provide variable substitution mocker for tests."""
    return VariableSubstitutionMocker()


@pytest.fixture
def ai_template_mocker() -> AITemplateMocker:
    """Provide AI template mocker for tests."""
    return AITemplateMocker()


@pytest.fixture
def temp_template_dir() -> Generator[Path, None, None]:
    """Provide temporary directory for template testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_template_environment(
    template_fixture_generator: TemplateFixtureGenerator,
    temp_template_dir: Path,
) -> dict[str, Any]:
    """Provide complete mock template environment.

    Returns:
        Dictionary with template environment components
    """
    # Create basic fixtures
    basic_template = template_fixture_generator.create_basic_template()
    ai_template = template_fixture_generator.create_ai_enhanced_template()

    # Create template files
    basic_file = template_fixture_generator.create_template_file(
        basic_template, temp_template_dir
    )
    ai_file = template_fixture_generator.create_template_file(
        ai_template, temp_template_dir
    )

    return {
        "temp_dir": temp_template_dir,
        "basic_template": basic_template,
        "ai_template": ai_template,
        "basic_file": basic_file,
        "ai_file": ai_file,
        "generator": template_fixture_generator,
    }
