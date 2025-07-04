"""Unit tests for template test infrastructure helpers."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

import yaml

from spec_cli.templates.config import TemplateConfig
from spec_cli.templates.prompt_generator import PromptStructure
from spec_cli.utils.test_helpers.template_test_helpers import (
    AITemplateMocker,
    TemplateFixture,
    TemplateFixtureGenerator,
    VariableSubstitutionMocker,
)


class TestTemplateFixture:
    """Unit tests for TemplateFixture dataclass."""

    def test_template_fixture_initialization(self):
        """Test basic template fixture initialization."""
        fixture = TemplateFixture(
            name="test",
            content="# {{title}}\nContent: {{content}}",
            variables={"title": "Test", "content": "Example"},
        )

        assert fixture.name == "test"
        assert fixture.content == "# {{title}}\nContent: {{content}}"
        assert fixture.variables == {"title": "Test", "content": "Example"}
        assert fixture.config is None
        assert fixture.expected_output is None
        assert fixture.should_fail is False
        assert fixture.error_type is None

    def test_template_fixture_with_config(self):
        """Test template fixture with configuration."""
        config = TemplateConfig(
            index="# {{filename}}\nIndex content",
            history="# {{filename}} History\nHistory content",
            version="1.0",
        )

        fixture = TemplateFixture(
            name="configured",
            content="{{default}}",
            config=config,
        )

        assert fixture.config == config
        assert fixture.config.index == "# {{filename}}\nIndex content"
        assert fixture.config.history == "# {{filename}} History\nHistory content"

    def test_template_fixture_error_configuration(self):
        """Test template fixture configured for errors."""
        fixture = TemplateFixture(
            name="error_test",
            content="{{invalid}}",
            should_fail=True,
            error_type=ValueError,
        )

        assert fixture.should_fail is True
        assert fixture.error_type is ValueError


class TestTemplateFixtureGenerator:
    """Unit tests for TemplateFixtureGenerator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.generator = TemplateFixtureGenerator()

    def test_generator_initialization(self):
        """Test generator initialization."""
        assert isinstance(self.generator.fixtures, dict)
        assert len(self.generator.fixtures) == 0

    def test_create_basic_template_default(self):
        """Test creating basic template with defaults."""
        fixture = self.generator.create_basic_template()

        assert fixture.name == "basic"
        assert "{{filename}}" in fixture.content
        assert "{{purpose}}" in fixture.content
        assert "{{current_date}}" in fixture.content
        assert fixture.variables["filename"] == "test_file.py"
        assert fixture.variables["purpose"] == "Testing"
        assert fixture.expected_output is not None
        assert "test_file.py" in fixture.expected_output
        assert "Testing" in fixture.expected_output

    def test_create_basic_template_custom_variables(self):
        """Test creating basic template with custom variables."""
        variables = {"filename": "custom.py", "purpose": "Custom testing"}
        fixture = self.generator.create_basic_template("custom", variables)

        assert fixture.name == "custom"
        assert fixture.variables == variables
        assert "custom.py" in fixture.expected_output
        assert "Custom testing" in fixture.expected_output

    def test_fixture_registration(self):
        """Test that fixtures are registered in generator."""
        fixture1 = self.generator.create_basic_template("test1")
        fixture2 = self.generator.create_basic_template("test2")

        assert len(self.generator.fixtures) == 2
        assert "test1" in self.generator.fixtures
        assert "test2" in self.generator.fixtures
        assert self.generator.fixtures["test1"] == fixture1
        assert self.generator.fixtures["test2"] == fixture2

    def test_create_ai_enhanced_template(self):
        """Test creating AI-enhanced template."""
        fixture = self.generator.create_ai_enhanced_template()

        assert fixture.name == "ai_enhanced"
        assert "{{ai:analyze_complexity}}" in fixture.content
        assert "{{ai:suggest_patterns}}" in fixture.content
        assert "{{ai:generate_docs}}" in fixture.content
        assert fixture.variables["filename"] == "ai_test.py"
        assert fixture.variables["complexity"] == "high"

    def test_create_ai_enhanced_template_custom(self):
        """Test creating AI-enhanced template with custom variables."""
        variables = {"filename": "ai_custom.py", "complexity": "low"}
        fixture = self.generator.create_ai_enhanced_template("custom_ai", variables)

        assert fixture.name == "custom_ai"
        assert fixture.variables == variables

    def test_create_error_template(self):
        """Test creating error template."""
        fixture = self.generator.create_error_template()

        assert fixture.name == "error"
        assert fixture.content == "{{invalid_syntax}}"
        assert fixture.should_fail is True
        assert fixture.error_type is None

    def test_create_error_template_with_type(self):
        """Test creating error template with specific error type."""
        fixture = self.generator.create_error_template("custom_error", ValueError)

        assert fixture.name == "custom_error"
        assert fixture.should_fail is True
        assert fixture.error_type is ValueError

    def test_create_template_file(self):
        """Test creating template file from fixture."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            fixture = self.generator.create_basic_template("file_test")

            file_path = self.generator.create_template_file(fixture, temp_path)

            assert file_path.exists()
            assert file_path.name == "file_test.spectemplate"
            assert file_path.parent == temp_path

            content = file_path.read_text(encoding="utf-8")
            assert content == fixture.content

    def test_create_template_file_no_temp_dir(self):
        """Test creating template file without specifying temp directory."""
        fixture = self.generator.create_basic_template("auto_temp")

        file_path = self.generator.create_template_file(fixture)

        assert file_path.exists()
        assert file_path.name == "auto_temp.spectemplate"

        # Clean up
        file_path.unlink()
        file_path.parent.rmdir()

    def test_create_config_file(self):
        """Test creating config file from template config."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            config_path = self.generator.create_config_file(
                index_content="# {{filename}}\nTest index",
                history_content="# {{filename}} History\nTest history",
                temp_dir=temp_path,
            )

            assert config_path.exists()
            assert config_path.name == ".spectemplate"
            assert config_path.parent == temp_path

            content = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            assert content["index"] == "# {{filename}}\nTest index"
            assert content["history"] == "# {{filename}} History\nTest history"
            assert content["version"] == "1.0"
            assert content["ai_enabled"] is False


class TestVariableSubstitutionMocker:
    """Unit tests for VariableSubstitutionMocker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mocker = VariableSubstitutionMocker()

    def test_mocker_initialization(self):
        """Test mocker initialization."""
        assert isinstance(self.mocker.substitution_history, list)
        assert len(self.mocker.substitution_history) == 0
        assert isinstance(self.mocker.mock_substitution, Mock)

    def test_mock_substitute_success(self):
        """Test mocking successful substitution."""
        content = "Hello {{name}}"
        variables = {"name": "World"}
        expected = "Hello World"

        mock_sub = self.mocker.mock_substitute(content, variables, expected)

        assert mock_sub.substitute.return_value == expected
        assert len(self.mocker.substitution_history) == 1

        history = self.mocker.substitution_history[0]
        assert history["content"] == content
        assert history["variables"] == variables
        assert history["result"] == expected
        assert history["failed"] is False

    def test_mock_substitute_failure(self):
        """Test mocking failed substitution."""
        content = "{{invalid}}"
        variables = {}

        mock_sub = self.mocker.mock_substitute(
            content, variables, should_fail=True, error_type=ValueError
        )

        assert mock_sub.substitute.side_effect is not None
        assert len(self.mocker.substitution_history) == 1

        history = self.mocker.substitution_history[0]
        assert history["failed"] is True

    def test_mock_substitute_default_result(self):
        """Test mocking substitution with default result."""
        content = "Test {{test}} content"
        variables = {"test": "value"}

        mock_sub = self.mocker.mock_substitute(content, variables)

        # Should use default mocked result
        assert mock_sub.substitute.return_value == "Test mocked content"

    def test_mock_validate_variables_valid(self):
        """Test mocking valid variable validation."""
        variables = {"valid": "value"}

        mock_sub = self.mocker.mock_validate_variables(variables, True)

        assert mock_sub.validate_variables.return_value is True

    def test_mock_validate_variables_invalid(self):
        """Test mocking invalid variable validation."""
        variables = {"invalid": None}
        errors = ["Variable 'invalid' cannot be None"]

        mock_sub = self.mocker.mock_validate_variables(variables, False, errors)

        assert mock_sub.validate_variables.return_value is False
        assert mock_sub.get_validation_errors.return_value == errors

    def test_reset_history(self):
        """Test resetting substitution history."""
        # Add some history
        self.mocker.mock_substitute("test", {}, "result")
        assert len(self.mocker.substitution_history) == 1

        # Reset
        self.mocker.reset_history()
        assert len(self.mocker.substitution_history) == 0
        assert self.mocker.mock_substitution.reset_mock.called


class TestAITemplateMocker:
    """Unit tests for AITemplateMocker."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mocker = AITemplateMocker()

    def test_mocker_initialization(self):
        """Test mocker initialization."""
        assert isinstance(self.mocker.generation_history, list)
        assert isinstance(self.mocker.mock_results, dict)
        assert len(self.mocker.generation_history) == 0
        assert len(self.mocker.mock_results) == 0

    def test_create_mock_result_success(self):
        """Test creating successful mock result."""
        result = self.mocker.create_mock_result("test_success")

        assert result.success is True
        assert result.traditional_content == "Mock traditional content"
        assert result.ai_prompt is not None
        assert result.ai_prompt.template_content == "Mock template content"
        assert result.ai_prompt.ai_instructions == "Mock AI instructions"
        assert result.variables == {}
        assert result.error is None
        assert result.processing_time_ms == 100
        assert "test_success" in self.mocker.mock_results

    def test_create_mock_result_failure(self):
        """Test creating failed mock result."""
        result = self.mocker.create_mock_result(
            "test_failure",
            success=False,
            traditional_content="",
            error="Mock error message",
        )

        assert result.success is False
        assert result.traditional_content == ""
        assert result.ai_prompt is None
        assert result.error == "Mock error message"

    def test_create_mock_result_custom_parameters(self):
        """Test creating mock result with custom parameters."""
        variables = {"custom": "value"}
        ai_prompt = PromptStructure(
            template_content="Custom template content",
            variables=variables,
            placeholders=["custom"],
            sections={"custom": "section"},
            ai_instructions="Custom AI instructions",
        )

        result = self.mocker.create_mock_result(
            "custom",
            traditional_content="Custom content",
            ai_prompt=ai_prompt,
            variables=variables,
            processing_time_ms=200,
        )

        assert result.traditional_content == "Custom content"
        assert result.ai_prompt == ai_prompt
        assert result.variables == variables
        assert result.processing_time_ms == 200

    def test_mock_ai_enhancement_success(self):
        """Test mocking successful AI enhancement."""
        content = "Template content with {{ai:enhance}}"
        expected_result = self.mocker.create_mock_result("enhancement")

        result = self.mocker.mock_ai_enhancement(content, expected_result)

        assert result == expected_result
        assert len(self.mocker.generation_history) == 1

        history = self.mocker.generation_history[0]
        assert history["input_content"] == content
        assert history["result"] == result

    def test_mock_ai_enhancement_failure(self):
        """Test mocking failed AI enhancement."""
        content = "Invalid template"

        result = self.mocker.mock_ai_enhancement(content, should_fail=True)

        assert result.success is False
        assert result.error == "Mock AI enhancement error"
        assert len(self.mocker.generation_history) == 1

    def test_mock_ai_enhancement_default(self):
        """Test mocking AI enhancement with default result."""
        content = "Default template"

        result = self.mocker.mock_ai_enhancement(content)

        assert result.success is True
        assert result.traditional_content == "Mock traditional content"
        assert "default_enhancement" in self.mocker.mock_results

    def test_reset_history(self):
        """Test resetting generation history."""
        # Add some history
        self.mocker.mock_ai_enhancement("test content")
        self.mocker.create_mock_result("test")

        assert len(self.mocker.generation_history) == 1
        assert len(self.mocker.mock_results) == 2

        # Reset
        self.mocker.reset_history()
        assert len(self.mocker.generation_history) == 0
        assert len(self.mocker.mock_results) == 0


class TestTemplateFixtures:
    """Integration tests for template test fixtures."""

    def test_template_fixture_generator_integration(self):
        """Test template fixture generator with file creation."""
        generator = TemplateFixtureGenerator()

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create fixtures
            basic = generator.create_basic_template("integration_basic")
            ai_enhanced = generator.create_ai_enhanced_template("integration_ai")
            error = generator.create_error_template("integration_error")

            # Create files
            basic_file = generator.create_template_file(basic, temp_path)
            ai_file = generator.create_template_file(ai_enhanced, temp_path)
            error_file = generator.create_template_file(error, temp_path)

            # Verify files
            assert basic_file.exists()
            assert ai_file.exists()
            assert error_file.exists()

            # Verify content
            assert "{{filename}}" in basic_file.read_text()
            assert "{{ai:analyze_complexity}}" in ai_file.read_text()
            assert "{{invalid_syntax}}" in error_file.read_text()

    def test_variable_substitution_mocker_integration(self):
        """Test variable substitution mocker with multiple operations."""
        mocker = VariableSubstitutionMocker()

        # Mock successful substitution
        mock1 = mocker.mock_substitute(
            "Hello {{name}}", {"name": "Alice"}, "Hello Alice"
        )

        # Mock failed substitution
        mocker.mock_substitute("{{invalid}}", {}, should_fail=True, error_type=KeyError)

        # Mock validation
        mock3 = mocker.mock_validate_variables({"valid": "value"}, True)

        # Verify history
        assert len(mocker.substitution_history) == 2
        assert mocker.substitution_history[0]["content"] == "Hello {{name}}"
        assert mocker.substitution_history[1]["failed"] is True

        # Verify mocks work
        assert mock1.substitute.return_value == "Hello Alice"
        assert mock3.validate_variables.return_value is True

    def test_ai_template_mocker_integration(self):
        """Test AI template mocker with multiple operations."""
        mocker = AITemplateMocker()

        # Create multiple results
        success_result = mocker.create_mock_result("success_test")
        mocker.create_mock_result("failure_test", success=False, error="Test error")

        # Mock enhancements
        enhancement1 = mocker.mock_ai_enhancement("Template 1", success_result)
        enhancement2 = mocker.mock_ai_enhancement("Template 2", should_fail=True)

        # Verify results
        assert enhancement1 == success_result
        assert enhancement2.success is False
        assert len(mocker.generation_history) == 2
        assert len(mocker.mock_results) == 2  # Only success_test and failure_test


class TestTemplateTestHelperFixtures:
    """Test the pytest fixtures provided by template test helpers."""

    def test_template_fixture_generator_fixture(self, template_fixture_generator):
        """Test template fixture generator pytest fixture."""
        assert isinstance(template_fixture_generator, TemplateFixtureGenerator)

        fixture = template_fixture_generator.create_basic_template()
        assert fixture.name == "basic"

    def test_variable_substitution_mocker_fixture(self, variable_substitution_mocker):
        """Test variable substitution mocker pytest fixture."""
        assert isinstance(variable_substitution_mocker, VariableSubstitutionMocker)

        mock = variable_substitution_mocker.mock_substitute("test", {}, "result")
        assert mock.substitute.return_value == "result"

    def test_ai_template_mocker_fixture(self, ai_template_mocker):
        """Test AI template mocker pytest fixture."""
        assert isinstance(ai_template_mocker, AITemplateMocker)

        result = ai_template_mocker.create_mock_result("fixture_test")
        assert result.success is True

    def test_temp_template_dir_fixture(self, temp_template_dir):
        """Test temporary template directory pytest fixture."""
        assert isinstance(temp_template_dir, Path)
        assert temp_template_dir.exists()
        assert temp_template_dir.is_dir()

    def test_mock_template_environment_fixture(self, mock_template_environment):
        """Test complete mock template environment fixture."""
        env = mock_template_environment

        assert "temp_dir" in env
        assert "basic_template" in env
        assert "ai_template" in env
        assert "basic_file" in env
        assert "ai_file" in env
        assert "generator" in env

        assert isinstance(env["temp_dir"], Path)
        assert isinstance(env["basic_template"], TemplateFixture)
        assert isinstance(env["ai_template"], TemplateFixture)
        assert env["basic_file"].exists()
        assert env["ai_file"].exists()
        assert isinstance(env["generator"], TemplateFixtureGenerator)
