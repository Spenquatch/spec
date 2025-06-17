# Slice 2a: AI Provider Interface

## Goal
Implement the abstract AI provider interface with data structures for documentation generation requests and results.

## Scope
- Abstract base class for AI providers
- Data structures for generation requests and results
- Provider interface specification only (no implementation)
- Foundation for provider implementations

## Files to Create (≤3)
- `spec_cli/ai/providers/base.py` (≤100 lines, complexity ≤5)

## Classes/Services (≤2)
1. **AIProvider** - Abstract base class defining provider interface
2. **GenerationRequest/GenerationResult** - Data structures (dataclasses, count as 1 logical unit)

## McCabe Complexity (≤7 per function)
- **Abstract methods**: ≤2 decision points each (simple interface definitions)
- **Data structure validation**: ≤3 decision points (basic type and content validation)
- **No complex logic** - Pure interface and data structure definitions

## External Integrations (≤1)
- **0 external integrations** - Pure abstract interface and data structures

## Implementation

```python
# spec_cli/ai/providers/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

@dataclass
class GenerationRequest:
    """Request for AI-powered documentation generation."""
    source_file: Path
    content: str
    context: Dict[str, Any] = field(default_factory=dict)
    doc_type: str = "comprehensive"
    template_content: Optional[str] = None

    def __post_init__(self):
        """Validate request after initialization."""
        if not self.source_file:
            raise ValueError("source_file is required")
        if not self.content:
            raise ValueError("content cannot be empty")
        if not isinstance(self.context, dict):
            raise ValueError("context must be a dictionary")

    def get_file_extension(self) -> str:
        """Get file extension for language-specific processing."""
        return self.source_file.suffix.lower()

    def get_content_size(self) -> int:
        """Get content size in characters."""
        return len(self.content)

@dataclass
class GenerationResult:
    """Result of AI documentation generation."""
    success: bool
    content: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None

    def __post_init__(self):
        """Validate result after initialization."""
        if self.success and not self.content:
            raise ValueError("Successful result must have content")
        if not self.success and not self.error:
            raise ValueError("Failed result must have error message")

    def get_main_content(self) -> str:
        """Get the main documentation content."""
        return self.content.get('index.md', '')

    def get_history_content(self) -> str:
        """Get the history documentation content."""
        return self.content.get('history.md', '')

    def has_complete_documentation(self) -> bool:
        """Check if result contains complete documentation."""
        return 'index.md' in self.content and len(self.get_main_content().strip()) > 0

class AIProvider(ABC):
    """Abstract base class for AI documentation providers."""

    def __init__(self):
        """Initialize provider with logging."""
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available and configured.

        Returns:
            bool: True if provider can process requests
        """
        pass

    @abstractmethod
    def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate documentation for source code.

        Args:
            request: Documentation generation request

        Returns:
            GenerationResult: Documentation generation result
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Clean up provider resources.

        Should be called when provider is no longer needed.
        """
        pass

    def validate_request(self, request: GenerationRequest) -> None:
        """Validate generation request.

        Args:
            request: Request to validate

        Raises:
            ValueError: If request is invalid
        """
        if not isinstance(request, GenerationRequest):
            raise ValueError("request must be a GenerationRequest instance")

        # Additional validation can be added by subclasses
        self.logger.debug(f"Validating request for {request.source_file}")

    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information.

        Returns:
            Dict[str, Any]: Provider metadata
        """
        return {
            "provider_class": self.__class__.__name__,
            "available": self.is_available(),
            "supports_cleanup": hasattr(self, 'cleanup')
        }
```

## Inputs - EXPLICIT
- **source_file: Path** - Path to source code file for documentation generation
- **content: str** - Source code content to analyze
- **context: Dict[str, Any]** - Additional context information (default: empty dict)
- **doc_type: str** - Documentation type ("comprehensive", "brief", etc.) (default: "comprehensive")
- **template_content: Optional[str]** - Template content for guided generation (default: None)

## Actions - UNAMBIGUOUS
1. Define GenerationRequest dataclass with validation in __post_init__
2. Define GenerationResult dataclass with success/failure validation
3. Define abstract AIProvider interface with required methods
4. Provide utility methods for common request/result operations
5. Include logging setup for provider implementations

## Outputs - WELL-DEFINED
- **GenerationRequest**: Validated request object with source file, content, and context
- **GenerationResult**: Result object with content dict, metadata, and error handling
- **AIProvider interface**: Abstract base class for provider implementations
- **Validation errors**: Clear ValueError messages for invalid requests/results

## Helper Dependencies
- **Existing helpers**: None required (pure interface definitions)
- **Standard library**: `abc`, `dataclasses`, `typing`, `pathlib`, `logging`
- **No external dependencies**: Pure Python standard library usage

## Individual Test Scenarios (100% coverage achievable)
1. **test_generation_request_validation** - Test request validation in __post_init__
2. **test_generation_request_utility_methods** - Test file extension and content size methods
3. **test_generation_result_validation** - Test result validation for success/failure states
4. **test_generation_result_utility_methods** - Test content retrieval methods
5. **test_generation_result_complete_documentation_check** - Test completeness validation
6. **test_ai_provider_abstract_methods** - Test that abstract methods cannot be instantiated
7. **test_ai_provider_request_validation** - Test provider request validation
8. **test_ai_provider_info_method** - Test provider info metadata
9. **test_invalid_request_creation** - Test various invalid request scenarios
10. **test_invalid_result_creation** - Test various invalid result scenarios

## Quality Assurance
- **Poetry compliance**: No external dependencies, pure Python standard library
- **Type safety**: Complete type annotations for all methods and data structures
- **Security clearance**: No sensitive data handling, pure interface definitions
- **Documentation ready**: Comprehensive docstrings for all public methods

## Integration with Other Slices
- **Used by Slice 2b**: Local AI provider will implement this interface
- **Used by future provider slices**: All AI providers will inherit from AIProvider
- **Interface for templates**: Template enhancement will use GenerationRequest/Result
- **Foundation**: Provides stable interface for all AI provider implementations

## Delivery Requirements
- **Independent execution**: Can be implemented without dependencies on other AI slices
- **Interface stability**: Designed for long-term stability across provider implementations
- **Clear contracts**: Abstract methods define clear provider responsibilities
- **Ready for implementation**: Complete interface for provider development

## Quality Gates
```bash
poetry run pytest tests/unit/ai/providers/test_base.py -v --cov=spec_cli.ai.providers.base --cov-fail-under=100
poetry run mypy spec_cli/ai/providers/base.py --strict
poetry run ruff check spec_cli/ai/providers/base.py
```

## Status
**READY for single AI agent implementation** - All granularity and quality limits met individually.
**No dependencies**: Can be implemented immediately without waiting for other slices.
