# Slice 8C: AI Integration Hooks and Infrastructure

## Goal

Stub out ask_llm() function with retry/backoff logic and create AI integration infrastructure, leaving model calls mocked in tests.

## Context

Building on the spec generator from slice-8b and substitution engine from slice-8a, this slice creates the AI integration infrastructure. It focuses on establishing the interfaces, retry logic, and extension points for AI content generation without implementing actual LLM calls. This provides the foundation for future AI enhancement while keeping the current implementation testable and deterministic.

## Scope

**Included in this slice:**
- AIContentProvider abstract interface for AI implementations
- PlaceholderAIProvider for non-AI operation (default)
- AIContentManager with provider registration and fallback
- Retry logic and backoff for API calls (without actual API calls)
- Extension points for AI content generation in templates
- Mock-friendly design for comprehensive testing

**NOT included in this slice:**
- Actual LLM API implementations (Claude, GPT, etc.)
- Real API key management or authentication
- Production AI content generation
- Complex prompt engineering or content optimization

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for AI errors)
- `spec_cli.logging.debug` (debug_logger for AI operations)
- `spec_cli.config.settings` (SpecSettings for AI configuration)
- `spec_cli.templates.substitution` (TemplateSubstitution from slice-8a)
- `spec_cli.templates.generator` (SpecContentGenerator from slice-8b)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` from slice-3a-settings-console
- `TemplateSubstitution` from slice-8a-template-substitution
- `SpecContentGenerator` from slice-8b-spec-generator

## Files to Create

```
spec_cli/templates/
├── ai_integration.py       # AI provider interfaces and manager
└── __init__.py            # Updated exports
```

## Implementation Steps

### Step 1: Create spec_cli/templates/ai_integration.py

```python
import asyncio
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from functools import wraps
from ..exceptions import SpecTemplateError, SpecConfigurationError
from ..logging.debug import debug_logger
from ..config.settings import get_settings, SpecSettings

# Retry decorator with exponential backoff
def retry_with_backoff(max_retries: int = 3,
                      base_delay: float = 1.0,
                      max_delay: float = 60.0,
                      exponential_base: float = 2.0,
                      jitter: bool = True):
    """Decorator for retrying AI API calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Base for exponential backoff
        jitter: Whether to add random jitter to delays
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        debug_logger.log("ERROR", "Max retries reached for AI call",
                                       function=func.__name__,
                                       attempts=attempt + 1,
                                       error=str(e))
                        break
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    if jitter:
                        import random
                        delay *= (0.5 + random.random() * 0.5)  # Add ±25% jitter
                    
                    debug_logger.log("WARNING", "AI call failed, retrying",
                                   function=func.__name__,
                                   attempt=attempt + 1,
                                   delay=delay,
                                   error=str(e))
                    
                    time.sleep(delay)
            
            # Re-raise the last exception if all retries failed
            if last_exception:
                raise last_exception
                
        return wrapper
    return decorator

class AIContentProvider(ABC):
    """Abstract interface for AI content generation providers."""
    
    @abstractmethod
    def generate_content(self, 
                        file_path: Path, 
                        context: Dict[str, Any],
                        content_type: str,
                        max_tokens: int = 1000) -> str:
        """Generate content for a specific context.
        
        Args:
            file_path: Path to the file being documented
            context: Context information about the file
            content_type: Type of content to generate (e.g., 'purpose', 'overview')
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated content string
            
        Raises:
            SpecTemplateError: If content generation fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if AI provider is available and configured."""
        pass
    
    @abstractmethod
    def get_supported_content_types(self) -> List[str]:
        """Get list of supported content types."""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get information about this provider."""
        pass
    
    def validate_configuration(self) -> List[str]:
        """Validate provider configuration.
        
        Returns:
            List of configuration issues (empty if valid)
        """
        return []

class PlaceholderAIProvider(AIContentProvider):
    """Placeholder AI provider that generates template placeholders instead of AI content."""
    
    def __init__(self):
        self.supported_types = [
            "purpose", "overview", "responsibilities", "dependencies",
            "api_interface", "example_usage", "configuration", 
            "error_handling", "testing_notes", "performance_notes",
            "security_notes", "future_enhancements", "related_docs", 
            "notes", "context", "initial_purpose", "decisions", 
            "implementation_notes", "architecture", "patterns"
        ]
        debug_logger.log("INFO", "PlaceholderAIProvider initialized")
    
    def generate_content(self, 
                        file_path: Path, 
                        context: Dict[str, Any],
                        content_type: str,
                        max_tokens: int = 1000) -> str:
        """Generate placeholder content that mimics AI output."""
        debug_logger.log("DEBUG", "Generating placeholder AI content",
                        file_path=str(file_path),
                        content_type=content_type)
        
        # Create descriptive placeholder based on content type and context
        file_name = file_path.name
        file_type = context.get("file_type", "unknown")
        
        if content_type == "purpose":
            return f"This {file_type} file '{file_name}' serves a specific purpose in the project. [AI-generated content would analyze the file and provide detailed purpose description]"
        elif content_type == "overview":
            return f"## Overview\n\nThe {file_name} file contains {file_type} code that [AI would analyze structure and provide overview]. Key components and functionality would be identified and summarized here."
        elif content_type == "responsibilities":
            return f"### Key Responsibilities\n\n- [AI would analyze code and identify primary responsibilities]\n- [Secondary responsibilities would be listed]\n- [Dependencies and interactions would be noted]"
        elif content_type == "dependencies":
            return f"### Dependencies\n\n[AI would scan imports/includes and identify:]\n- External libraries used\n- Internal modules referenced\n- System dependencies required"
        elif content_type == "api_interface":
            return f"### API Interface\n\n[AI would identify and document:]\n- Public functions/methods\n- Input parameters and types\n- Return values and types\n- Usage examples"
        elif content_type == "example_usage":
            return f"### Example Usage\n\n```\n# [AI would generate relevant usage examples]\n# Based on the file type and detected patterns\n```"
        else:
            # Generic placeholder for other content types
            formatted_type = content_type.replace("_", " ").title()
            return f"### {formatted_type}\n\n[AI-generated {content_type} content for {file_name} would appear here. This would be tailored to the specific {file_type} file and its role in the project.]"
    
    def is_available(self) -> bool:
        """Placeholder provider is always available."""
        return True
    
    def get_supported_content_types(self) -> List[str]:
        """Return all supported content types."""
        return self.supported_types.copy()
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information."""
        return {
            "name": "PlaceholderProvider",
            "type": "placeholder",
            "description": "Generates placeholder content instead of AI content",
            "version": "1.0.0",
            "supports_async": False,
            "requires_api_key": False,
        }

class MockAIProvider(AIContentProvider):
    """Mock AI provider for testing that can be configured with responses."""
    
    def __init__(self):
        self.responses: Dict[str, str] = {}
        self.call_count = 0
        self.should_fail = False
        self.failure_message = "Mock AI provider failure"
        debug_logger.log("INFO", "MockAIProvider initialized")
    
    def set_response(self, content_type: str, response: str) -> None:
        """Set a mock response for a content type."""
        self.responses[content_type] = response
        debug_logger.log("DEBUG", "Mock response set",
                        content_type=content_type,
                        response_length=len(response))
    
    def set_failure(self, should_fail: bool, message: str = "Mock failure") -> None:
        """Configure the provider to simulate failures."""
        self.should_fail = should_fail
        self.failure_message = message
        debug_logger.log("DEBUG", "Mock failure configured",
                        should_fail=should_fail,
                        message=message)
    
    @retry_with_backoff(max_retries=2, base_delay=0.1)  # Fast retries for testing
    def generate_content(self, 
                        file_path: Path, 
                        context: Dict[str, Any],
                        content_type: str,
                        max_tokens: int = 1000) -> str:
        """Generate mock content or simulate failure."""
        self.call_count += 1
        
        debug_logger.log("DEBUG", "Mock AI content generation",
                        file_path=str(file_path),
                        content_type=content_type,
                        call_count=self.call_count)
        
        if self.should_fail:
            raise SpecTemplateError(self.failure_message)
        
        if content_type in self.responses:
            return self.responses[content_type]
        
        # Default mock response
        return f"Mock AI generated content for {content_type} in {file_path.name}"
    
    def is_available(self) -> bool:
        """Mock provider availability."""
        return not self.should_fail
    
    def get_supported_content_types(self) -> List[str]:
        """Return supported types (all types for testing)."""
        return list(self.responses.keys()) if self.responses else ["purpose", "overview"]
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get mock provider information."""
        return {
            "name": "MockProvider",
            "type": "mock",
            "description": "Mock provider for testing",
            "version": "1.0.0",
            "supports_async": False,
            "requires_api_key": False,
            "call_count": self.call_count,
        }
    
    def reset(self) -> None:
        """Reset mock state."""
        self.responses.clear()
        self.call_count = 0
        self.should_fail = False
        self.failure_message = "Mock AI provider failure"
        debug_logger.log("DEBUG", "Mock provider reset")

class AIContentManager:
    """Manages AI content generation with provider registration and fallback strategies."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.providers: Dict[str, AIContentProvider] = {}
        self.default_provider = PlaceholderAIProvider()
        self.enabled = False
        self.preferred_provider: Optional[str] = None
        
        debug_logger.log("INFO", "AIContentManager initialized",
                        enabled=self.enabled)
    
    def register_provider(self, name: str, provider: AIContentProvider) -> None:
        """Register an AI content provider.
        
        Args:
            name: Name of the provider
            provider: AIContentProvider instance
        """
        self.providers[name] = provider
        debug_logger.log("INFO", "AI provider registered",
                        provider_name=name,
                        provider_type=provider.get_provider_info().get("type", "unknown"))
        
        # Set as preferred if it's the first available provider
        if self.preferred_provider is None and provider.is_available():
            self.preferred_provider = name
            debug_logger.log("INFO", "Set preferred AI provider",
                           provider_name=name)
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable AI content generation."""
        self.enabled = enabled
        debug_logger.log("INFO", "AI content generation toggled",
                        enabled=enabled)
    
    def set_preferred_provider(self, provider_name: Optional[str]) -> bool:
        """Set the preferred AI provider.
        
        Args:
            provider_name: Name of the provider to prefer (None for auto-selection)
            
        Returns:
            True if provider was set, False if provider not found
        """
        if provider_name is None:
            self.preferred_provider = None
            debug_logger.log("INFO", "Cleared preferred AI provider")
            return True
        
        if provider_name in self.providers:
            self.preferred_provider = provider_name
            debug_logger.log("INFO", "Set preferred AI provider",
                           provider_name=provider_name)
            return True
        
        debug_logger.log("WARNING", "Attempted to set unknown AI provider",
                        provider_name=provider_name)
        return False
    
    def generate_ai_content(self, 
                           file_path: Path,
                           context: Dict[str, Any],
                           content_requests: List[str],
                           max_tokens_per_request: int = 1000) -> Dict[str, str]:
        """Generate AI content for multiple content types.
        
        Args:
            file_path: Path to the file being documented
            context: Context information
            content_requests: List of content types to generate
            max_tokens_per_request: Maximum tokens per content generation
            
        Returns:
            Dictionary mapping content types to generated content
        """
        debug_logger.log("INFO", "Generating AI content",
                        file_path=str(file_path),
                        content_types=content_requests,
                        enabled=self.enabled)
        
        if not self.enabled:
            return {
                content_type: f"[{content_type.replace('_', ' ').title()} - AI disabled]"
                for content_type in content_requests
            }
        
        # Find available provider
        provider = self._get_available_provider()
        if not provider:
            debug_logger.log("WARNING", "No AI providers available, using placeholder")
            provider = self.default_provider
        
        results = {}
        
        with debug_logger.timer("ai_content_generation"):
            for content_type in content_requests:
                try:
                    content = provider.generate_content(
                        file_path, context, content_type, max_tokens_per_request
                    )
                    results[content_type] = content
                    
                    debug_logger.log("DEBUG", "AI content generated",
                                   content_type=content_type,
                                   content_length=len(content))
                    
                except Exception as e:
                    # Fallback to placeholder for failed generation
                    fallback_content = self.default_provider.generate_content(
                        file_path, context, content_type, max_tokens_per_request
                    )
                    results[content_type] = fallback_content
                    
                    debug_logger.log("WARNING", "AI content generation failed, using fallback",
                                   content_type=content_type,
                                   error=str(e))
        
        debug_logger.log("INFO", "AI content generation complete",
                        content_types_generated=len(results))
        
        return results
    
    def _get_available_provider(self) -> Optional[AIContentProvider]:
        """Get the best available AI provider."""
        # Try preferred provider first
        if self.preferred_provider and self.preferred_provider in self.providers:
            provider = self.providers[self.preferred_provider]
            if provider.is_available():
                return provider
            else:
                debug_logger.log("WARNING", "Preferred provider not available",
                               provider_name=self.preferred_provider)
        
        # Try any available provider
        for name, provider in self.providers.items():
            if provider.is_available():
                debug_logger.log("DEBUG", "Using available AI provider",
                               provider_name=name)
                return provider
        
        return None
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all registered providers."""
        status = {
            "enabled": self.enabled,
            "preferred_provider": self.preferred_provider,
            "providers": {},
        }
        
        for name, provider in self.providers.items():
            try:
                provider_info = provider.get_provider_info()
                status["providers"][name] = {
                    "available": provider.is_available(),
                    "info": provider_info,
                    "supported_types": len(provider.get_supported_content_types()),
                }
            except Exception as e:
                status["providers"][name] = {
                    "available": False,
                    "error": str(e),
                }
        
        return status
    
    def validate_configuration(self) -> List[str]:
        """Validate AI configuration and providers."""
        issues = []
        
        if not self.providers:
            issues.append("No AI providers registered")
        
        available_providers = []
        for name, provider in self.providers.items():
            try:
                if provider.is_available():
                    available_providers.append(name)
                else:
                    # Check for configuration issues
                    provider_issues = provider.validate_configuration()
                    if provider_issues:
                        issues.extend([f"{name}: {issue}" for issue in provider_issues])
            except Exception as e:
                issues.append(f"{name}: Error checking availability - {e}")
        
        if not available_providers and self.enabled:
            issues.append("AI enabled but no providers are available")
        
        if self.preferred_provider and self.preferred_provider not in available_providers:
            issues.append(f"Preferred provider '{self.preferred_provider}' is not available")
        
        return issues
    
    def clear_providers(self) -> None:
        """Clear all registered providers (useful for testing)."""
        self.providers.clear()
        self.preferred_provider = None
        debug_logger.log("INFO", "All AI providers cleared")

# Global AI content manager instance
ai_content_manager = AIContentManager()

# Convenience function for ask_llm pattern
@retry_with_backoff(max_retries=3, base_delay=1.0)
def ask_llm(prompt: str, 
           context: Optional[Dict[str, Any]] = None,
           max_tokens: int = 1000,
           provider_name: Optional[str] = None) -> str:
    """Ask LLM a question with retry logic (currently returns placeholder).
    
    This function provides the interface for future LLM integration.
    Currently returns placeholder content but includes the retry logic
    and error handling that will be needed for real AI calls.
    
    Args:
        prompt: The prompt/question to send to the LLM
        context: Optional context information
        max_tokens: Maximum tokens to generate
        provider_name: Specific provider to use (None for default)
        
    Returns:
        Generated response string
        
    Raises:
        SpecTemplateError: If generation fails after retries
    """
    debug_logger.log("INFO", "LLM query requested",
                    prompt_length=len(prompt),
                    context_provided=context is not None,
                    provider=provider_name)
    
    try:
        # In the future, this would dispatch to actual LLM providers
        # For now, we provide a structured placeholder response
        
        if not ai_content_manager.enabled:
            return "[LLM query disabled - enable AI to get generated responses]"
        
        # Simulate processing time for realistic testing
        time.sleep(0.1)
        
        # Generate structured placeholder based on prompt content
        if "purpose" in prompt.lower():
            return "The purpose of this component is to [AI would analyze and provide detailed purpose based on code analysis]."
        elif "overview" in prompt.lower():
            return "## Overview\n\nThis provides [AI would generate comprehensive overview based on code structure and patterns identified]."
        elif "how" in prompt.lower():
            return "This works by [AI would explain the mechanism and flow based on code analysis]."
        else:
            return f"[AI response to: {prompt[:50]}{'...' if len(prompt) > 50 else ''}]"
            
    except Exception as e:
        error_msg = f"LLM query failed: {e}"
        debug_logger.log("ERROR", error_msg)
        raise SpecTemplateError(error_msg) from e
```

### Step 2: Update spec_cli/templates/__init__.py

```python
"""Template system for spec CLI.

This package provides template configuration, loading, substitution, and content generation
for creating consistent documentation across different contexts, with AI integration support.
"""

from .config import TemplateConfig, TemplateValidator
from .loader import TemplateLoader, load_template
from .defaults import get_default_template_config, get_template_preset
from .substitution import TemplateSubstitution
from .generator import SpecContentGenerator, generate_spec_content
from .ai_integration import (
    AIContentProvider, 
    PlaceholderAIProvider, 
    MockAIProvider,
    AIContentManager,
    ai_content_manager, 
    ask_llm,
    retry_with_backoff
)

__all__ = [
    "TemplateConfig",
    "TemplateValidator",
    "TemplateLoader",
    "load_template",
    "get_default_template_config",
    "get_template_preset", 
    "TemplateSubstitution",
    "SpecContentGenerator",
    "generate_spec_content",
    "AIContentProvider",
    "PlaceholderAIProvider",
    "MockAIProvider",
    "AIContentManager",
    "ai_content_manager",
    "ask_llm",
    "retry_with_backoff",
]
```

## Test Requirements

Create comprehensive tests for AI integration infrastructure:

### Test Cases (12 tests total)

**Provider Interface Tests:**
1. **test_placeholder_provider_generates_content**
2. **test_placeholder_provider_always_available**
3. **test_mock_provider_configurable_responses**
4. **test_mock_provider_failure_simulation**

**AI Content Manager Tests:**
5. **test_ai_manager_registers_providers**
6. **test_ai_manager_handles_disabled_state**
7. **test_ai_manager_fallback_on_provider_failure**
8. **test_ai_manager_preferred_provider_selection**
9. **test_ai_manager_provider_status_reporting**

**Retry Logic Tests:**
10. **test_retry_decorator_exponential_backoff**
11. **test_ask_llm_function_with_placeholders**
12. **test_ai_integration_comprehensive_workflow**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/templates/test_ai_integration.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/templates/test_ai_integration.py --cov=spec_cli.templates.ai_integration --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/templates/ai_integration.py

# Check code formatting
poetry run ruff check spec_cli/templates/ai_integration.py
poetry run ruff format spec_cli/templates/ai_integration.py

# Verify imports work correctly
python -c "from spec_cli.templates.ai_integration import AIContentProvider, PlaceholderAIProvider, ai_content_manager, ask_llm; print('Import successful')"

# Test placeholder provider
python -c "
from spec_cli.templates.ai_integration import PlaceholderAIProvider
from pathlib import Path

provider = PlaceholderAIProvider()
print(f'Placeholder provider available: {provider.is_available()}')
print(f'Supported content types: {len(provider.get_supported_content_types())}')

test_content = provider.generate_content(
    Path('test.py'), 
    {'file_type': 'python'}, 
    'purpose'
)
print(f'Generated content: {test_content[:100]}...')

info = provider.get_provider_info()
print(f'Provider info: {info["name"]} v{info["version"]}')
"

# Test AI content manager
python -c "
from spec_cli.templates.ai_integration import ai_content_manager, PlaceholderAIProvider
from pathlib import Path

print(f'AI manager enabled: {ai_content_manager.enabled}')
ai_content_manager.set_enabled(True)
print(f'AI manager enabled after setting: {ai_content_manager.enabled}')

# Register a provider
provider = PlaceholderAIProvider()
ai_content_manager.register_provider('placeholder', provider)

# Test content generation
content = ai_content_manager.generate_ai_content(
    Path('test.py'),
    {'file_type': 'python'},
    ['purpose', 'overview']
)
print(f'Generated content types: {list(content.keys())}')
print(f'Purpose content: {content["purpose"][:80]}...')

# Get status
status = ai_content_manager.get_provider_status()
print(f'Providers registered: {len(status["providers"])}')
print(f'Enabled: {status["enabled"]}')
"

# Test mock provider for testing
python -c "
from spec_cli.templates.ai_integration import MockAIProvider
from pathlib import Path

mock = MockAIProvider()
mock.set_response('purpose', 'This is a mock purpose response')

content = mock.generate_content(
    Path('test.py'),
    {'file_type': 'python'},
    'purpose'
)
print(f'Mock content: {content}')
print(f'Call count: {mock.call_count}')

# Test failure simulation
mock.set_failure(True, 'Simulated API failure')
try:
    mock.generate_content(Path('test.py'), {}, 'purpose')
except Exception as e:
    print(f'Expected failure: {e}')

mock.reset()
print(f'After reset - call count: {mock.call_count}')
"

# Test ask_llm function
python -c "
from spec_cli.templates.ai_integration import ask_llm, ai_content_manager

# Enable AI for testing
ai_content_manager.set_enabled(True)

response = ask_llm('What is the purpose of this file?', {'file_type': 'python'})
print(f'LLM response: {response}')

response2 = ask_llm('How does this component work?')
print(f'LLM response 2: {response2}')

# Test with disabled AI
ai_content_manager.set_enabled(False)
response3 = ask_llm('This should indicate AI is disabled')
print(f'Disabled response: {response3}')
"

# Test retry logic simulation
python -c "
from spec_cli.templates.ai_integration import retry_with_backoff
import time

# Create a function that fails then succeeds
class FailCounter:
    def __init__(self, fail_times=2):
        self.fail_times = fail_times
        self.call_count = 0
    
    @retry_with_backoff(max_retries=3, base_delay=0.1)
    def flaky_function(self):
        self.call_count += 1
        if self.call_count <= self.fail_times:
            raise Exception(f'Failure {self.call_count}')
        return f'Success after {self.call_count} calls'

counter = FailCounter(2)
start_time = time.time()
try:
    result = counter.flaky_function()
    elapsed = time.time() - start_time
    print(f'Retry test result: {result}')
    print(f'Total calls: {counter.call_count}')
    print(f'Elapsed time: {elapsed:.2f}s (should show backoff delay)')
except Exception as e:
    print(f'Retry failed: {e}')
"

# Test configuration validation
python -c "
from spec_cli.templates.ai_integration import ai_content_manager, PlaceholderAIProvider, MockAIProvider

# Clear any existing providers
ai_content_manager.clear_providers()

# Test validation with no providers
issues = ai_content_manager.validate_configuration()
print(f'Validation issues (no providers): {issues}')

# Register providers and test
ai_content_manager.register_provider('placeholder', PlaceholderAIProvider())
ai_content_manager.register_provider('mock', MockAIProvider())

issues = ai_content_manager.validate_configuration()
print(f'Validation issues (with providers): {issues}')

# Test with enabled AI
ai_content_manager.set_enabled(True)
issues = ai_content_manager.validate_configuration()
print(f'Validation issues (AI enabled): {issues}')

status = ai_content_manager.get_provider_status()
print(f'Provider status summary:')
for name, info in status['providers'].items():
    print(f'  {name}: available={info["available"]}, types={info.get("supported_types", 0)}')
"
```

## Definition of Done

- [ ] AIContentProvider abstract interface for AI implementations
- [ ] PlaceholderAIProvider for non-AI operation (default behavior)
- [ ] MockAIProvider for comprehensive testing scenarios
- [ ] AIContentManager with provider registration and fallback logic
- [ ] Retry decorator with exponential backoff for API resilience
- [ ] ask_llm() function with placeholder implementation and retry logic
- [ ] Provider status monitoring and configuration validation
- [ ] Mock-friendly design for deterministic testing
- [ ] All 12 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration points for future AI enhancement
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice completes **PHASE-3** (Template System) by providing:
- AI integration infrastructure that can be enhanced in future phases
- Template system ready for both manual and AI-assisted content generation
- Extension points for LLM providers without current implementation complexity
- Testing infrastructure that supports both mocked and real AI scenarios

This enables **PHASE-4** (Git and Core Logic) which can optionally use AI content generation during file processing, and provides the foundation for future AI-enhanced workflows.