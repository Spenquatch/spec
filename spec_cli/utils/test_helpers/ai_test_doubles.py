"""AI provider test doubles for comprehensive testing infrastructure.

This module provides mock AI providers and utilities for testing all AI integrations
without external dependencies. Supports LLaMA providers, generation services,
timeout scenarios, and response fixtures.
"""

import json
import time
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest


class MockLlamaCppProvider:
    """Mock LLaMA C++ provider for testing AI model operations."""

    def __init__(self, model_path: Path | None = None):
        """Initialize mock LLaMA provider.

        Args:
            model_path: Path to mock model file
        """
        self.model_path = model_path or Path("/mock/model.gguf")
        self.is_loaded = False
        self.generation_history: list[dict[str, Any]] = []
        self.load_time = 0.1  # Simulate fast loading for tests
        self.failure_mode: str | None = None
        self._model_exists = True

    def load_model(self) -> bool:
        """Mock model loading with configurable behavior.

        Returns:
            bool: True if loading succeeds, False if failure mode set
        """
        if self.failure_mode == "load_failure":
            self.is_loaded = False
            return False

        time.sleep(self.load_time)
        self.is_loaded = True
        return True

    def generate_text(self, prompt: str, max_tokens: int = 100) -> str:
        """Mock text generation with realistic responses.

        Args:
            prompt: Input prompt text
            max_tokens: Maximum tokens to generate

        Returns:
            str: Generated response text

        Raises:
            Exception: If error mode configured or timeout scenario
        """
        self.generation_history.append(
            {"prompt": prompt, "max_tokens": max_tokens, "timestamp": time.time()}
        )

        # Simulate different failure scenarios
        if self.failure_mode == "generation_error":
            raise Exception("Model generation error")
        elif self.failure_mode == "timeout":
            time.sleep(10)  # Simulate timeout
            return ""
        elif not self.is_loaded:
            raise Exception("Model not loaded")

        # Return contextual response based on prompt
        if "error" in prompt.lower():
            raise Exception("Model generation error")
        elif "timeout" in prompt.lower():
            time.sleep(10)  # Simulate timeout
            return ""
        else:
            return f"Generated response for: {prompt[:50]}..."

    def is_available(self) -> bool:
        """Check if provider is available.

        Returns:
            bool: True if model exists and no failure mode set
        """
        if self.failure_mode == "unavailable":
            return False
        return self._model_exists

    def set_failure_mode(self, mode: str | None) -> None:
        """Set failure mode for testing error scenarios.

        Args:
            mode: Failure mode ('load_failure', 'generation_error', 'timeout', 'unavailable')
        """
        self.failure_mode = mode

    def cleanup(self) -> None:
        """Clean up mock model resources."""
        self.is_loaded = False
        self._model_exists = False


class MockGenerationProvider:
    """Mock generation provider for testing AI content generation."""

    def __init__(self) -> None:
        """Initialize mock generation provider."""
        self.responses: dict[str, str] = {}
        self.call_history: list[dict[str, Any]] = []
        self.failure_mode: str | None = None
        self.generation_count = 0

    def register_response(self, prompt_pattern: str, response: str) -> None:
        """Register a response for a prompt pattern.

        Args:
            prompt_pattern: Pattern to match in prompts
            response: Response to return for matching prompts
        """
        self.responses[prompt_pattern] = response

    def generate(self, prompt: str, **kwargs: Any) -> dict[str, Any]:
        """Mock content generation with registered responses.

        Args:
            prompt: Input prompt text
            **kwargs: Additional generation parameters

        Returns:
            Dict[str, Any]: Generation result with content and metadata

        Raises:
            ConnectionError: If network_error failure mode set
            Exception: If rate_limit failure mode set
        """
        self.call_history.append(
            {"prompt": prompt, "kwargs": kwargs, "timestamp": time.time()}
        )
        self.generation_count += 1

        # Simulate different failure scenarios
        if self.failure_mode == "network_error":
            raise ConnectionError("Network connection failed")
        elif self.failure_mode == "rate_limit":
            raise Exception("Rate limit exceeded")
        elif self.failure_mode == "api_key_error":
            raise Exception("Invalid API key")

        # Find matching response
        for pattern, response in self.responses.items():
            if pattern in prompt:
                return {
                    "content": response,
                    "tokens_used": len(response.split()),
                    "model": "mock-model",
                    "success": True,
                    "generation_id": self.generation_count,
                }

        # Default response
        return {
            "content": f"Mock response for: {prompt[:100]}",
            "tokens_used": 50,
            "model": "mock-model",
            "success": True,
            "generation_id": self.generation_count,
        }

    def set_failure_mode(self, mode: str | None) -> None:
        """Set failure mode for testing error scenarios.

        Args:
            mode: Failure mode ('network_error', 'rate_limit', 'api_key_error')
        """
        self.failure_mode = mode

    def get_generation_history(self) -> list[dict[str, Any]]:
        """Get history of all generation calls.

        Returns:
            List[Dict[str, Any]]: List of generation call records
        """
        return self.call_history.copy()


class AIResponseFixtures:
    """Manage AI response fixtures for consistent testing."""

    def __init__(self, fixtures_path: Path | None = None):
        """Initialize AI response fixtures.

        Args:
            fixtures_path: Path to fixtures file (optional)
        """
        self.fixtures_path = fixtures_path or Path("tests/fixtures/ai_responses.json")
        self.fixtures = self._load_fixtures()

    def _load_fixtures(self) -> dict[str, Any]:
        """Load AI response fixtures from file.

        Returns:
            Dict[str, Any]: Loaded fixtures or defaults
        """
        if self.fixtures_path.exists():
            try:
                with open(self.fixtures_path) as f:
                    result = json.load(f)
                    return (
                        result
                        if isinstance(result, dict)
                        else self._create_default_fixtures()
                    )
            except (json.JSONDecodeError, OSError):
                # Fall back to defaults if file is corrupted
                pass
        return self._create_default_fixtures()

    def _create_default_fixtures(self) -> dict[str, Any]:
        """Create default AI response fixtures.

        Returns:
            Dict[str, Any]: Default fixture data
        """
        return {
            "documentation_generation": {
                "prompt": "Generate documentation for function",
                "response": "# Function Documentation\n\nThis function performs...",
                "tokens": 45,
            },
            "code_explanation": {
                "prompt": "Explain this code",
                "response": "This code implements a method that...",
                "tokens": 38,
            },
            "error_response": {
                "prompt": "Generate error content",
                "response": None,
                "error": "Generation failed",
            },
            "template_completion": {
                "prompt": "Fill template with {{placeholder}}",
                "response": "Template content with actual value",
                "tokens": 25,
            },
            "large_response": {
                "prompt": "Generate comprehensive documentation",
                "response": "# Comprehensive Documentation\n\n"
                + "Content section. " * 100,
                "tokens": 250,
            },
        }

    def get_fixture(self, name: str) -> dict[str, Any]:
        """Get a specific fixture by name.

        Args:
            name: Fixture name

        Returns:
            Dict[str, Any]: Fixture data or empty dict if not found
        """
        result = self.fixtures.get(name, {})
        return result if isinstance(result, dict) else {}

    def get_response(self, name: str) -> str:
        """Get response content from fixture.

        Args:
            name: Fixture name

        Returns:
            str: Response content or default message
        """
        fixture = self.get_fixture(name)
        response = fixture.get("response", f"Mock response for {name}")
        return response if isinstance(response, str) else f"Mock response for {name}"

    def save_fixtures(self) -> None:
        """Save current fixtures to file."""
        self.fixtures_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.fixtures_path, "w") as f:
            json.dump(self.fixtures, f, indent=2)

    def add_fixture(
        self, name: str, prompt: str, response: str, tokens: int | None = None
    ) -> None:
        """Add a new fixture.

        Args:
            name: Fixture name
            prompt: Prompt text
            response: Response text
            tokens: Token count (calculated if not provided)
        """
        actual_tokens = (
            tokens if tokens is not None else (len(response.split()) if response else 0)
        )

        self.fixtures[name] = {
            "prompt": prompt,
            "response": response,
            "tokens": actual_tokens,
        }


class AITimeoutSimulator:
    """Simulate various AI timeout scenarios for testing."""

    def __init__(self) -> None:
        """Initialize timeout simulator."""
        self.timeout_scenarios = {
            "model_loading": 5.0,
            "generation_timeout": 30.0,
            "network_timeout": 10.0,
            "api_timeout": 15.0,
        }

    @contextmanager
    def simulate_timeout(self, scenario: str) -> Generator[None, None, None]:
        """Context manager to simulate timeout scenarios.

        Args:
            scenario: Timeout scenario name

        Yields:
            None: Context for timeout simulation

        Raises:
            TimeoutError: After timeout duration
        """
        timeout_duration = self.timeout_scenarios.get(scenario, 1.0)

        # Directly raise timeout without patching
        yield
        raise TimeoutError(f"Operation timed out after {timeout_duration}s")

    def set_timeout_duration(self, scenario: str, duration: float) -> None:
        """Set custom timeout duration for scenario.

        Args:
            scenario: Scenario name
            duration: Timeout duration in seconds
        """
        self.timeout_scenarios[scenario] = duration


class MockHuggingFaceModel:
    """Mock HuggingFace model for testing generation provider."""

    def __init__(self, model_name: str = "mock-model") -> None:
        """Initialize mock HF model.

        Args:
            model_name: Model name identifier
        """
        self.model_name = model_name
        self.device = "cpu"
        self.generation_history: list[dict[str, Any]] = []

    def generate(
        self, input_ids: Any, max_new_tokens: int = 100, **kwargs: Any
    ) -> list[Any]:
        """Mock model generation.

        Args:
            input_ids: Input token tensor
            max_new_tokens: Maximum tokens to generate
            **kwargs: Additional generation parameters

        Returns:
            Mock tensor output
        """
        # Record generation call
        self.generation_history.append(
            {
                "input_length": input_ids.shape[1]
                if hasattr(input_ids, "shape")
                else 0,
                "max_new_tokens": max_new_tokens,
                "kwargs": kwargs,
                "timestamp": time.time(),
            }
        )

        # Create mock output tensor
        mock_output = Mock()
        mock_output.shape = [1, 150]  # Mock output shape
        mock_output.__getitem__ = lambda self, idx: Mock()
        return [mock_output]

    def to(self, device: str) -> "MockHuggingFaceModel":
        """Mock device movement.

        Args:
            device: Target device

        Returns:
            self: For method chaining
        """
        self.device = device
        return self


# Factory functions for easy helper creation
def create_mock_llamacpp_provider(
    model_path: Path | None = None,
) -> MockLlamaCppProvider:
    """Create MockLlamaCppProvider instance.

    Args:
        model_path: Optional model path

    Returns:
        MockLlamaCppProvider: Configured mock provider
    """
    return MockLlamaCppProvider(model_path)


def create_mock_generation_provider() -> MockGenerationProvider:
    """Create MockGenerationProvider instance.

    Returns:
        MockGenerationProvider: Configured mock provider
    """
    return MockGenerationProvider()


def create_ai_response_fixtures(
    fixtures_path: Path | None = None,
) -> AIResponseFixtures:
    """Create AIResponseFixtures instance.

    Args:
        fixtures_path: Optional fixtures file path

    Returns:
        AIResponseFixtures: Configured fixtures manager
    """
    return AIResponseFixtures(fixtures_path)


def create_timeout_simulator() -> AITimeoutSimulator:
    """Create AITimeoutSimulator instance.

    Returns:
        AITimeoutSimulator: Configured timeout simulator
    """
    return AITimeoutSimulator()


# Pytest fixtures for integration
@pytest.fixture
def mock_llamacpp_provider() -> MockLlamaCppProvider:
    """Pytest fixture for LLaMA provider."""
    return create_mock_llamacpp_provider()


@pytest.fixture
def mock_generation_provider() -> MockGenerationProvider:
    """Pytest fixture for generation provider."""
    return create_mock_generation_provider()


@pytest.fixture
def ai_response_fixtures() -> AIResponseFixtures:
    """Pytest fixture for AI response fixtures."""
    return create_ai_response_fixtures()


@pytest.fixture
def ai_timeout_simulator() -> AITimeoutSimulator:
    """Pytest fixture for timeout simulator."""
    return create_timeout_simulator()


@pytest.fixture
def mock_huggingface_model() -> MockHuggingFaceModel:
    """Pytest fixture for HuggingFace model."""
    return MockHuggingFaceModel()


# Patch decorators for common mocking scenarios
def patch_llamacpp_provider(
    provider_path: str = "spec_cli.ai.providers.llamacpp.LlamaCppProvider",
) -> Any:
    """Decorate function to patch LlamaCpp provider with mock.

    Args:
        provider_path: Import path to LlamaCpp provider

    Returns:
        Decorator function
    """

    def decorator(func: Any) -> Any:
        return patch(provider_path, create_mock_llamacpp_provider)(func)

    decorator.target = provider_path  # type: ignore  # Store target for testing
    return decorator


def patch_generation_provider(
    provider_path: str = "spec_cli.ai.providers.generation.DocumentationGenerator",
) -> Any:
    """Decorate function to patch generation provider with mock.

    Args:
        provider_path: Import path to generation provider

    Returns:
        Decorator function
    """

    def decorator(func: Any) -> Any:
        return patch(provider_path, create_mock_generation_provider)(func)

    decorator.target = provider_path  # type: ignore  # Store target for testing
    return decorator
