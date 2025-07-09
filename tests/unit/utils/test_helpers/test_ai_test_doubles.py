"""Unit tests for AI test doubles infrastructure.

Tests all mock AI providers, response fixtures, timeout simulation,
and helper factory functions to ensure comprehensive AI testing support.
"""

import json
import time
from pathlib import Path
from unittest.mock import Mock

import pytest

from spec_cli.utils.test_helpers.ai_test_doubles import (
    AIResponseFixtures,
    AITimeoutSimulator,
    MockGenerationProvider,
    MockHuggingFaceModel,
    MockLlamaCppProvider,
    create_ai_response_fixtures,
    create_mock_generation_provider,
    create_mock_llamacpp_provider,
    create_timeout_simulator,
    patch_generation_provider,
    patch_llamacpp_provider,
)


class TestMockLlamaCppProvider:
    """Test MockLlamaCppProvider functionality."""

    def test_init_with_default_model_path(self):
        """Test provider initialization with default model path."""
        provider = MockLlamaCppProvider()

        assert provider.model_path == Path("/mock/model.gguf")
        assert not provider.is_loaded
        assert provider.generation_history == []
        assert provider.load_time == 0.1
        assert provider.failure_mode is None
        assert provider._model_exists

    def test_init_with_custom_model_path(self):
        """Test provider initialization with custom model path."""
        custom_path = Path("/custom/model.gguf")
        provider = MockLlamaCppProvider(custom_path)

        assert provider.model_path == custom_path
        assert not provider.is_loaded

    def test_load_model_success(self):
        """Test successful model loading."""
        provider = MockLlamaCppProvider()

        start_time = time.time()
        result = provider.load_model()
        elapsed = time.time() - start_time

        assert result is True
        assert provider.is_loaded
        assert elapsed >= provider.load_time

    def test_load_model_failure_mode(self):
        """Test model loading with failure mode."""
        provider = MockLlamaCppProvider()
        provider.set_failure_mode("load_failure")

        result = provider.load_model()

        assert result is False
        assert not provider.is_loaded

    def test_generate_text_success(self):
        """Test successful text generation."""
        provider = MockLlamaCppProvider()
        provider.load_model()

        prompt = "Generate documentation for test function"
        result = provider.generate_text(prompt, max_tokens=150)

        assert isinstance(result, str)
        assert "Generated response for:" in result
        assert prompt[:50] in result
        assert len(provider.generation_history) == 1

        history_entry = provider.generation_history[0]
        assert history_entry["prompt"] == prompt
        assert history_entry["max_tokens"] == 150
        assert "timestamp" in history_entry

    def test_generate_text_model_not_loaded(self):
        """Test text generation when model not loaded."""
        provider = MockLlamaCppProvider()

        with pytest.raises(Exception, match="Model not loaded"):
            provider.generate_text("test prompt")

    def test_generate_text_error_in_prompt(self):
        """Test text generation with error keyword in prompt."""
        provider = MockLlamaCppProvider()
        provider.load_model()

        with pytest.raises(Exception, match="Model generation error"):
            provider.generate_text("generate error response")

    def test_generate_text_timeout_in_prompt(self):
        """Test text generation with timeout keyword in prompt."""
        provider = MockLlamaCppProvider()
        provider.load_model()

        start_time = time.time()
        result = provider.generate_text("simulate timeout scenario")
        elapsed = time.time() - start_time

        assert result == ""
        assert elapsed >= 9.5  # Should have slept for approximately 10 seconds

    def test_generate_text_generation_error_mode(self):
        """Test text generation with generation error failure mode."""
        provider = MockLlamaCppProvider()
        provider.load_model()
        provider.set_failure_mode("generation_error")

        with pytest.raises(Exception, match="Model generation error"):
            provider.generate_text("test prompt")

    def test_generate_text_timeout_mode(self):
        """Test text generation with timeout failure mode."""
        provider = MockLlamaCppProvider()
        provider.load_model()
        provider.set_failure_mode("timeout")

        start_time = time.time()
        result = provider.generate_text("test prompt")
        elapsed = time.time() - start_time

        assert result == ""
        assert elapsed >= 9.5

    def test_is_available_success(self):
        """Test availability check when provider is available."""
        provider = MockLlamaCppProvider()

        assert provider.is_available() is True

    def test_is_available_unavailable_mode(self):
        """Test availability check with unavailable failure mode."""
        provider = MockLlamaCppProvider()
        provider.set_failure_mode("unavailable")

        assert provider.is_available() is False

    def test_cleanup(self):
        """Test provider cleanup."""
        provider = MockLlamaCppProvider()
        provider.load_model()

        provider.cleanup()

        assert not provider.is_loaded
        assert not provider._model_exists

    def test_set_failure_mode(self):
        """Test setting different failure modes."""
        provider = MockLlamaCppProvider()

        provider.set_failure_mode("load_failure")
        assert provider.failure_mode == "load_failure"

        provider.set_failure_mode("generation_error")
        assert provider.failure_mode == "generation_error"

        provider.set_failure_mode(None)
        assert provider.failure_mode is None


class TestMockGenerationProvider:
    """Test MockGenerationProvider functionality."""

    def test_init(self):
        """Test provider initialization."""
        provider = MockGenerationProvider()

        assert provider.responses == {}
        assert provider.call_history == []
        assert provider.failure_mode is None
        assert provider.generation_count == 0

    def test_register_response(self):
        """Test response registration."""
        provider = MockGenerationProvider()

        provider.register_response("documentation", "Mock documentation content")

        assert provider.responses["documentation"] == "Mock documentation content"

    def test_generate_with_registered_response(self):
        """Test generation with registered response pattern."""
        provider = MockGenerationProvider()
        provider.register_response("documentation", "Registered documentation response")

        result = provider.generate("Generate documentation for function")

        assert result["success"] is True
        assert result["content"] == "Registered documentation response"
        assert result["model"] == "mock-model"
        assert result["tokens_used"] == 3  # "Registered documentation response"
        assert result["generation_id"] == 1
        assert provider.generation_count == 1

    def test_generate_default_response(self):
        """Test generation with default response."""
        provider = MockGenerationProvider()

        prompt = "Generate code explanation"
        result = provider.generate(prompt)

        assert result["success"] is True
        assert "Mock response for:" in result["content"]
        assert prompt[:100] in result["content"]
        assert result["tokens_used"] == 50
        assert result["generation_id"] == 1

    def test_generate_network_error_mode(self):
        """Test generation with network error failure mode."""
        provider = MockGenerationProvider()
        provider.set_failure_mode("network_error")

        with pytest.raises(ConnectionError, match="Network connection failed"):
            provider.generate("test prompt")

    def test_generate_rate_limit_mode(self):
        """Test generation with rate limit failure mode."""
        provider = MockGenerationProvider()
        provider.set_failure_mode("rate_limit")

        with pytest.raises(Exception, match="Rate limit exceeded"):
            provider.generate("test prompt")

    def test_generate_api_key_error_mode(self):
        """Test generation with API key error failure mode."""
        provider = MockGenerationProvider()
        provider.set_failure_mode("api_key_error")

        with pytest.raises(Exception, match="Invalid API key"):
            provider.generate("test prompt")

    def test_generate_records_call_history(self):
        """Test that generation calls are recorded in history."""
        provider = MockGenerationProvider()

        provider.generate("first prompt", temperature=0.7)
        provider.generate("second prompt", max_tokens=200)

        history = provider.get_generation_history()
        assert len(history) == 2

        assert history[0]["prompt"] == "first prompt"
        assert history[0]["kwargs"]["temperature"] == 0.7
        assert "timestamp" in history[0]

        assert history[1]["prompt"] == "second prompt"
        assert history[1]["kwargs"]["max_tokens"] == 200

    def test_get_generation_history_copy(self):
        """Test that generation history returns a copy."""
        provider = MockGenerationProvider()
        provider.generate("test prompt")

        history1 = provider.get_generation_history()
        history2 = provider.get_generation_history()

        # Should be separate objects
        assert history1 is not history2
        assert history1 == history2

    def test_set_failure_mode(self):
        """Test setting different failure modes."""
        provider = MockGenerationProvider()

        provider.set_failure_mode("network_error")
        assert provider.failure_mode == "network_error"

        provider.set_failure_mode(None)
        assert provider.failure_mode is None


class TestAIResponseFixtures:
    """Test AIResponseFixtures functionality."""

    def test_init_with_default_path(self):
        """Test initialization with default fixtures path."""
        fixtures = AIResponseFixtures()

        assert fixtures.fixtures_path == Path("tests/fixtures/ai_responses.json")
        assert isinstance(fixtures.fixtures, dict)

    def test_init_with_custom_path(self):
        """Test initialization with custom fixtures path."""
        custom_path = Path("/custom/fixtures.json")
        fixtures = AIResponseFixtures(custom_path)

        assert fixtures.fixtures_path == custom_path

    def test_create_default_fixtures(self):
        """Test creation of default fixtures."""
        fixtures = AIResponseFixtures()
        default_fixtures = fixtures._create_default_fixtures()

        assert "documentation_generation" in default_fixtures
        assert "code_explanation" in default_fixtures
        assert "error_response" in default_fixtures
        assert "template_completion" in default_fixtures
        assert "large_response" in default_fixtures

    def test_get_fixture_existing(self):
        """Test getting existing fixture."""
        fixtures = AIResponseFixtures()

        doc_fixture = fixtures.get_fixture("documentation_generation")

        assert "prompt" in doc_fixture
        assert "response" in doc_fixture
        assert "tokens" in doc_fixture

    def test_get_fixture_nonexistent(self):
        """Test getting non-existent fixture."""
        fixtures = AIResponseFixtures()

        result = fixtures.get_fixture("nonexistent")

        assert result == {}

    def test_get_response_existing(self):
        """Test getting response from existing fixture."""
        fixtures = AIResponseFixtures()

        response = fixtures.get_response("documentation_generation")

        assert isinstance(response, str)
        assert len(response) > 0

    def test_get_response_nonexistent(self):
        """Test getting response from non-existent fixture."""
        fixtures = AIResponseFixtures()

        response = fixtures.get_response("nonexistent")

        assert response == "Mock response for nonexistent"

    def test_add_fixture(self):
        """Test adding new fixture."""
        fixtures = AIResponseFixtures()

        fixtures.add_fixture("test_fixture", "Test prompt", "Test response content", 25)

        fixture = fixtures.get_fixture("test_fixture")
        assert fixture["prompt"] == "Test prompt"
        assert fixture["response"] == "Test response content"
        assert fixture["tokens"] == 25

    def test_add_fixture_auto_token_count(self):
        """Test adding fixture with automatic token counting."""
        fixtures = AIResponseFixtures()

        fixtures.add_fixture(
            "auto_tokens", "Test prompt", "This is a test response with multiple words"
        )

        fixture = fixtures.get_fixture("auto_tokens")
        assert fixture["tokens"] == 8  # Word count

    def test_add_fixture_with_none_response(self):
        """Test adding fixture with None response."""
        fixtures = AIResponseFixtures()

        fixtures.add_fixture("none_response", "Test prompt", None)

        fixture = fixtures.get_fixture("none_response")
        assert fixture["tokens"] == 0  # None response should have 0 tokens

    def test_save_fixtures(self, tmp_path):
        """Test saving fixtures to file."""
        fixtures_path = tmp_path / "test_fixtures.json"
        fixtures_path.parent.mkdir(parents=True, exist_ok=True)
        fixtures = AIResponseFixtures(fixtures_path)

        fixtures.add_fixture("test", "prompt", "response", 10)
        fixtures.save_fixtures()

        assert fixtures_path.exists()

        with open(fixtures_path) as f:
            saved_data = json.load(f)

        assert "test" in saved_data
        assert saved_data["test"]["prompt"] == "prompt"

    def test_load_fixtures_from_file(self, tmp_path):
        """Test loading fixtures from existing file."""
        fixtures_path = tmp_path / "existing_fixtures.json"
        fixtures_path.parent.mkdir(parents=True, exist_ok=True)
        test_data = {
            "custom_fixture": {
                "prompt": "Custom prompt",
                "response": "Custom response",
                "tokens": 15,
            }
        }

        with open(fixtures_path, "w") as f:
            json.dump(test_data, f)

        fixtures = AIResponseFixtures(fixtures_path)

        assert fixtures.get_fixture("custom_fixture")["prompt"] == "Custom prompt"

    def test_load_fixtures_corrupted_file(self, tmp_path):
        """Test loading fixtures from corrupted file falls back to defaults."""
        fixtures_path = tmp_path / "corrupted.json"
        fixtures_path.parent.mkdir(parents=True, exist_ok=True)

        with open(fixtures_path, "w") as f:
            f.write("invalid json content")

        fixtures = AIResponseFixtures(fixtures_path)

        # Should fall back to default fixtures
        assert "documentation_generation" in fixtures.fixtures


class TestAITimeoutSimulator:
    """Test AITimeoutSimulator functionality."""

    def test_init(self):
        """Test simulator initialization."""
        simulator = AITimeoutSimulator()

        assert "model_loading" in simulator.timeout_scenarios
        assert "generation_timeout" in simulator.timeout_scenarios
        assert "network_timeout" in simulator.timeout_scenarios
        assert "api_timeout" in simulator.timeout_scenarios

    def test_simulate_timeout_context_manager(self):
        """Test timeout simulation context manager."""
        simulator = AITimeoutSimulator()
        simulator.set_timeout_duration("test_scenario", 0.1)

        with pytest.raises(TimeoutError, match="Operation timed out"):
            with simulator.simulate_timeout("test_scenario"):
                pass

    def test_set_timeout_duration(self):
        """Test setting custom timeout duration."""
        simulator = AITimeoutSimulator()

        simulator.set_timeout_duration("custom_scenario", 5.5)

        assert simulator.timeout_scenarios["custom_scenario"] == 5.5

    def test_simulate_timeout_unknown_scenario(self):
        """Test timeout simulation with unknown scenario uses default."""
        simulator = AITimeoutSimulator()

        with pytest.raises(TimeoutError, match="Operation timed out"):
            with simulator.simulate_timeout("unknown_scenario"):
                pass


class TestMockHuggingFaceModel:
    """Test MockHuggingFaceModel functionality."""

    def test_init(self):
        """Test model initialization."""
        model = MockHuggingFaceModel()

        assert model.model_name == "mock-model"
        assert model.device == "cpu"
        assert model.generation_history == []

    def test_init_with_custom_name(self):
        """Test model initialization with custom name."""
        model = MockHuggingFaceModel("custom-model")

        assert model.model_name == "custom-model"

    def test_generate(self):
        """Test model generation."""
        model = MockHuggingFaceModel()

        mock_input = Mock(spec=[])
        mock_input.shape = [1, 50]

        result = model.generate(mock_input, max_new_tokens=100, temperature=0.7)

        assert len(result) == 1
        assert len(model.generation_history) == 1

        history_entry = model.generation_history[0]
        assert history_entry["input_length"] == 50
        assert history_entry["max_new_tokens"] == 100
        assert history_entry["kwargs"]["temperature"] == 0.7

    def test_to_device(self):
        """Test device movement."""
        model = MockHuggingFaceModel()

        result = model.to("cuda")

        assert result is model  # Should return self
        assert model.device == "cuda"


class TestFactoryFunctions:
    """Test factory functions for creating test doubles."""

    def test_create_mock_llamacpp_provider(self):
        """Test LLaMA provider factory function."""
        provider = create_mock_llamacpp_provider()

        assert isinstance(provider, MockLlamaCppProvider)
        assert provider.model_path == Path("/mock/model.gguf")

    def test_create_mock_llamacpp_provider_with_path(self):
        """Test LLaMA provider factory with custom path."""
        custom_path = Path("/custom/model.gguf")
        provider = create_mock_llamacpp_provider(custom_path)

        assert provider.model_path == custom_path

    def test_create_mock_generation_provider(self):
        """Test generation provider factory function."""
        provider = create_mock_generation_provider()

        assert isinstance(provider, MockGenerationProvider)
        assert provider.responses == {}

    def test_create_ai_response_fixtures(self):
        """Test response fixtures factory function."""
        fixtures = create_ai_response_fixtures()

        assert isinstance(fixtures, AIResponseFixtures)
        assert fixtures.fixtures_path == Path("tests/fixtures/ai_responses.json")

    def test_create_ai_response_fixtures_with_path(self):
        """Test response fixtures factory with custom path."""
        custom_path = Path("/custom/fixtures.json")
        fixtures = create_ai_response_fixtures(custom_path)

        assert fixtures.fixtures_path == custom_path

    def test_create_timeout_simulator(self):
        """Test timeout simulator factory function."""
        simulator = create_timeout_simulator()

        assert isinstance(simulator, AITimeoutSimulator)
        assert "model_loading" in simulator.timeout_scenarios


class TestPatchDecorators:
    """Test patch decorator functions."""

    def test_patch_llamacpp_provider_default_path(self):
        """Test LLaMA provider patch decorator with default path."""
        decorator = patch_llamacpp_provider()

        assert decorator.target == "spec_cli.ai.providers.llamacpp.LlamaCppProvider"

    def test_patch_llamacpp_provider_custom_path(self):
        """Test LLaMA provider patch decorator with custom path."""
        custom_path = "custom.module.LlamaCppProvider"
        decorator = patch_llamacpp_provider(custom_path)

        assert decorator.target == custom_path

    def test_patch_generation_provider_default_path(self):
        """Test generation provider patch decorator with default path."""
        decorator = patch_generation_provider()

        assert (
            decorator.target
            == "spec_cli.ai.providers.generation.DocumentationGenerator"
        )

    def test_patch_generation_provider_custom_path(self):
        """Test generation provider patch decorator with custom path."""
        custom_path = "custom.module.DocumentationGenerator"
        decorator = patch_generation_provider(custom_path)

        assert decorator.target == custom_path

    def test_decorator_function_execution(self):
        """Test decorator inner function execution for coverage."""

        # Test that the decorator actually works when applied
        def dummy_function():
            return "test"

        # Apply the decorator and verify it returns a patched version
        decorated_func = patch_llamacpp_provider()(dummy_function)

        # The decorated function should be different from the original
        assert decorated_func != dummy_function

        # Test generation provider decorator as well
        decorated_gen_func = patch_generation_provider()(dummy_function)
        assert decorated_gen_func != dummy_function


class TestPytestFixtures:
    """Test pytest fixture integration."""

    def test_mock_llamacpp_provider_fixture(self, mock_llamacpp_provider):
        """Test LLaMA provider pytest fixture."""
        assert isinstance(mock_llamacpp_provider, MockLlamaCppProvider)
        assert not mock_llamacpp_provider.is_loaded

    def test_mock_generation_provider_fixture(self, mock_generation_provider):
        """Test generation provider pytest fixture."""
        assert isinstance(mock_generation_provider, MockGenerationProvider)
        assert mock_generation_provider.generation_count == 0

    def test_ai_response_fixtures_fixture(self, ai_response_fixtures):
        """Test AI response fixtures pytest fixture."""
        assert isinstance(ai_response_fixtures, AIResponseFixtures)
        assert "documentation_generation" in ai_response_fixtures.fixtures

    def test_ai_timeout_simulator_fixture(self, ai_timeout_simulator):
        """Test timeout simulator pytest fixture."""
        assert isinstance(ai_timeout_simulator, AITimeoutSimulator)
        assert "model_loading" in ai_timeout_simulator.timeout_scenarios

    def test_mock_huggingface_model_fixture(self, mock_huggingface_model):
        """Test HuggingFace model pytest fixture."""
        assert isinstance(mock_huggingface_model, MockHuggingFaceModel)
        assert mock_huggingface_model.device == "cpu"


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    def test_complete_generation_workflow(
        self, mock_generation_provider, ai_response_fixtures
    ):
        """Test complete generation workflow with fixtures."""
        # Register response from fixtures
        doc_response = ai_response_fixtures.get_response("documentation_generation")
        mock_generation_provider.register_response("documentation", doc_response)

        # Simulate generation
        result = mock_generation_provider.generate(
            "Generate documentation for function"
        )

        assert result["success"] is True
        assert "Function Documentation" in result["content"]
        assert result["tokens_used"] > 0

    def test_error_handling_workflow(self, mock_llamacpp_provider):
        """Test error handling workflow."""
        # Test load failure
        mock_llamacpp_provider.set_failure_mode("load_failure")
        assert not mock_llamacpp_provider.load_model()

        # Reset and test generation error
        mock_llamacpp_provider.set_failure_mode(None)
        mock_llamacpp_provider.load_model()
        mock_llamacpp_provider.set_failure_mode("generation_error")

        with pytest.raises(Exception, match="Model generation error"):
            mock_llamacpp_provider.generate_text("test prompt")

    def test_performance_monitoring(self, mock_generation_provider):
        """Test performance monitoring capabilities."""
        # Multiple generations
        for i in range(5):
            mock_generation_provider.generate(f"Prompt {i}")

        history = mock_generation_provider.get_generation_history()
        assert len(history) == 5

        # Verify timestamps are recorded
        for entry in history:
            assert "timestamp" in entry
            assert entry["timestamp"] > 0

    def test_fixture_management(self, tmp_path):
        """Test fixture file management."""
        fixtures_path = tmp_path / "test_fixtures.json"
        fixtures_path.parent.mkdir(parents=True, exist_ok=True)
        fixtures = AIResponseFixtures(fixtures_path)

        # Add custom fixture
        fixtures.add_fixture("custom", "test prompt", "test response")
        fixtures.save_fixtures()

        # Load in new instance
        new_fixtures = AIResponseFixtures(fixtures_path)
        assert new_fixtures.get_response("custom") == "test response"
