# AI Integration Vertical Slices - Detailed Plan

This document outlines comprehensive vertical slices for implementing AI-powered documentation generation using LangChain and modern AI/ML libraries.

## Technology Stack

### Core AI/ML Libraries
- **LangChain**: Framework for LLM applications, prompt management, and provider abstraction
- **LangChain Community**: Additional provider integrations
- **Pydantic**: Data validation and settings management (already included)
- **tiktoken**: Token counting for OpenAI models
- **transformers**: For local model support and tokenization
- **asyncio**: Concurrent processing
- **tenacity**: Retry logic with exponential backoff

### Provider Libraries
- **openai**: OpenAI API client
- **anthropic**: Anthropic Claude API
- **ollama**: Local model inference
- **huggingface_hub**: Hugging Face model access

## Vertical Slice Breakdown

### Slice 1: AI Foundation and Configuration System
**Goal**: Establish the foundational AI infrastructure with comprehensive configuration

**Implementation Details**:
- Create AI module structure with proper abstractions
- Implement configuration management using Pydantic models
- Set up LangChain integration foundation
- Create custom exceptions hierarchy
- Implement logging and debugging utilities

**Files to Create**:
```
spec_cli/ai/
├── __init__.py           # Public API exports
├── config.py             # Configuration models and loading
├── exceptions.py         # Custom exception hierarchy
├── base.py              # Abstract base classes
├── utils.py             # Utility functions
└── constants.py         # AI-related constants
```

**Detailed Implementation**:

**spec_cli/ai/config.py**:
```python
from typing import Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator
from pathlib import Path

class OpenAIConfig(BaseModel):
    api_key_env: str = Field(default="OPENAI_API_KEY")
    model: str = Field(default="gpt-4")
    temperature: float = Field(default=0.3, ge=0, le=1)
    max_tokens: int = Field(default=4000, ge=100, le=16000)
    timeout: int = Field(default=30, ge=5, le=300)

class AnthropicConfig(BaseModel):
    api_key_env: str = Field(default="ANTHROPIC_API_KEY")
    model: str = Field(default="claude-3-sonnet-20240229")
    temperature: float = Field(default=0.3, ge=0, le=1)
    max_tokens: int = Field(default=4000, ge=100, le=16000)
    timeout: int = Field(default=30, ge=5, le=300)

class LocalConfig(BaseModel):
    model_name: str = Field(default="llama2")
    base_url: str = Field(default="http://localhost:11434")
    timeout: int = Field(default=60, ge=10, le=600)

class AIConfig(BaseModel):
    provider: Literal["openai", "anthropic", "local"] = Field(default="openai")
    max_concurrency: int = Field(default=5, ge=1, le=20)
    retry_attempts: int = Field(default=3, ge=1, le=10)
    fallback_to_placeholder: bool = Field(default=True)

    openai: OpenAIConfig = Field(default_factory=OpenAIConfig)
    anthropic: AnthropicConfig = Field(default_factory=AnthropicConfig)
    local: LocalConfig = Field(default_factory=LocalConfig)
```

**Tests to Write** (15 comprehensive tests):
- `tests/unit/ai/test_config_loading.py`:
  - `test_config_loads_from_pyproject_toml_when_file_exists`
  - `test_config_loads_from_specconfig_yaml_when_file_exists`
  - `test_config_uses_defaults_when_no_config_file`
  - `test_config_pyproject_overrides_defaults`
  - `test_config_environment_variables_override_config_files`
  - `test_config_handles_missing_environment_variables`
  - `test_config_invalid_provider_raises_validation_error`
  - `test_config_invalid_temperature_raises_validation_error`

- `tests/unit/ai/test_config_validation.py`:
  - `test_openai_config_validates_temperature_bounds`
  - `test_anthropic_config_validates_model_format`
  - `test_local_config_validates_url_format`
  - `test_ai_config_validates_concurrency_limits`
  - `test_config_validates_timeout_ranges`

- `tests/unit/ai/test_exceptions.py`:
  - `test_ai_exception_hierarchy_inheritance`
  - `test_provider_not_found_exception_message_formatting`

**Quality Checks**:
```bash
poetry run pytest tests/unit/ai/test_config*.py tests/unit/ai/test_exceptions.py -v --cov=spec_cli.ai --cov-report=term-missing --cov-fail-under=80
poetry run mypy spec_cli/ai/
poetry run ruff check --fix spec_cli/ai/
```

**Commit**: `feat: implement slice 1 - AI foundation and configuration system`

### Slice 2: Source Code Analysis Engine with Language Support
**Goal**: Create comprehensive source code analysis using AST parsing and pattern recognition

**Implementation Details**:
- Implement multi-language code analysis using AST parsing
- Extract meaningful metadata (complexity, dependencies, patterns)
- Create structured code representation for AI consumption
- Add caching for analysis results
- Support Python, JavaScript, TypeScript, Java, and generic text analysis

**Files to Create**:
```
spec_cli/ai/analysis/
├── __init__.py
├── base.py              # Abstract analyzer interface with dataclasses
├── analyzer.py          # Main analysis orchestrator
├── extractors.py        # Content extraction utilities
├── cache.py            # Analysis result caching
└── languages/
    ├── __init__.py
    ├── python.py        # Python AST analysis
    ├── javascript.py    # JS/TS analysis
    ├── java.py         # Java analysis
    └── generic.py      # Generic text analysis
```

**Detailed Implementation**:

**spec_cli/ai/analysis/base.py**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pathlib import Path
from dataclasses import dataclass

@dataclass
class FunctionInfo:
    name: str
    signature: str
    docstring: Optional[str]
    complexity: int
    line_start: int
    line_end: int
    decorators: List[str]
    is_async: bool = False

@dataclass
class ClassInfo:
    name: str
    docstring: Optional[str]
    methods: List[FunctionInfo]
    inheritance: List[str]

@dataclass
class CodeAnalysis:
    file_path: Path
    language: str
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    imports: List[str]
    complexity_score: int
    line_count: int
    documentation_coverage: float
    patterns: List[str]
```

**spec_cli/ai/analysis/analyzer.py**:
```python
class CodeAnalyzer:
    def __init__(self, use_cache: bool = True):
        self.analyzers = [PythonAnalyzer(), JavaScriptAnalyzer(), GenericAnalyzer()]
        self.cache = AnalysisCache() if use_cache else None

    def analyze_file(self, file_path: Path) -> CodeAnalysis:
        """Analyze source code file and return structured metadata."""

    def batch_analyze(self, file_paths: List[Path]) -> Dict[Path, CodeAnalysis]:
        """Analyze multiple files efficiently."""

    def _find_analyzer(self, file_path: Path) -> Optional[LanguageAnalyzer]:
        """Find appropriate analyzer for file type."""
```

**spec_cli/ai/analysis/languages/python.py**:
```python
class PythonAnalyzer(LanguageAnalyzer):
    def analyze(self, content: str, file_path: Path) -> CodeAnalysis:
        tree = ast.parse(content)
        visitor = PythonASTVisitor()
        visitor.visit(tree)
        return CodeAnalysis(...)

    def _calculate_complexity(self, tree: ast.AST) -> int:
        """Calculate cyclomatic complexity using AST."""

    def _calculate_doc_coverage(self, visitor) -> float:
        """Calculate percentage of documented functions/classes."""
```

**Tests to Write** (22 comprehensive tests):
- `tests/unit/ai/analysis/test_analyzer.py`:
  - `test_analyzer_detects_python_language_from_py_extension`
  - `test_analyzer_detects_javascript_language_from_js_extension`
  - `test_analyzer_handles_unknown_file_extension_gracefully`
  - `test_analyzer_analyzes_python_file_with_functions_and_classes`
  - `test_analyzer_extracts_import_statements_correctly`
  - `test_analyzer_calculates_complexity_score_accurately`
  - `test_analyzer_handles_syntax_errors_in_source_code`
  - `test_analyzer_caches_analysis_results_for_performance`
  - `test_analyzer_handles_empty_files_gracefully`
  - `test_analyzer_handles_binary_files_gracefully`
  - `test_analyzer_batch_analyzes_multiple_files`

- `tests/unit/ai/analysis/test_python_analyzer.py`:
  - `test_python_analyzer_extracts_function_signatures`
  - `test_python_analyzer_extracts_class_definitions`
  - `test_python_analyzer_extracts_docstrings_when_present`
  - `test_python_analyzer_identifies_decorators`
  - `test_python_analyzer_calculates_function_complexity`
  - `test_python_analyzer_handles_nested_classes`
  - `test_python_analyzer_identifies_async_functions`
  - `test_python_analyzer_calculates_documentation_coverage`

- `tests/unit/ai/analysis/test_javascript_analyzer.py`:
  - `test_javascript_analyzer_extracts_function_declarations`
  - `test_javascript_analyzer_extracts_arrow_functions`
  - `test_javascript_analyzer_identifies_export_statements`

**Test Fixtures**:
```
tests/fixtures/sample_code/
├── python/simple_module.py, complex_class.py, async_functions.py, syntax_error.py
├── javascript/simple_functions.js, es6_features.js, typescript_example.ts
└── java/SimpleClass.java, ComplexApplication.java
```

**Quality Checks**: 80%+ coverage including error handling paths

**Commit**: `feat: implement slice 2 - comprehensive source code analysis engine`

### Slice 3: LangChain Integration and Prompt Engineering
**Goal**: Implement LangChain-based prompt management and provider abstraction

**Implementation Details**:
- Create LangChain prompt templates for documentation generation
- Implement provider-agnostic LLM interface using LangChain
- Add prompt optimization and token management
- Create few-shot learning examples
- Implement output parsing and validation

**Files to Create**:
```
spec_cli/ai/prompts/
├── __init__.py
├── templates.py         # LangChain prompt templates
├── examples.py         # Few-shot examples
├── optimization.py     # Prompt optimization
└── schemas.py         # Output schemas and parsing
```

**Detailed Implementation**:

**spec_cli/ai/prompts/templates.py**:
```python
from langchain.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.schema import BaseOutputParser
from typing import Dict, Any, List
from pydantic import BaseModel

class DocumentationOutput(BaseModel):
    purpose: str
    responsibilities: str
    requirements: str
    example_usage: str
    notes: str

class DocumentationPromptTemplate:
    BASE_SYSTEM_PROMPT = "You are an expert software documentation analyst..."

    ANALYSIS_TEMPLATE = PromptTemplate(
        input_variables=["filename", "language", "file_content", "analysis_data"],
        template="Analyze this {language} code..."
    )

    PYTHON_SPECIFIC_TEMPLATE = PromptTemplate(...)
```

**spec_cli/ai/prompts/optimization.py**:
```python
class PromptOptimizer:
    def __init__(self, model_name: str = "gpt-4"):
        self.encoding = tiktoken.encoding_for_model(model_name)
        self.max_tokens = 8000

    def optimize_prompt(self, template: str, variables: Dict) -> str:
        """Optimize prompt by reducing tokens while preserving meaning."""

    def count_tokens(self, text: str) -> int:
        """Count tokens in text."""
```

**Tests to Write** (18 comprehensive tests):
- `tests/unit/ai/prompts/test_templates.py`:
  - `test_base_template_formats_with_all_required_variables`
  - `test_base_template_raises_error_when_missing_variables`
  - `test_python_specific_template_includes_language_features`
  - `test_javascript_template_handles_es6_syntax_properly`
  - `test_template_token_count_stays_within_limits`
  - `test_template_optimization_reduces_token_usage`
  - `test_template_handles_unicode_characters`
  - `test_template_preserves_code_block_formatting`

- `tests/unit/ai/prompts/test_examples.py`:
  - `test_few_shot_examples_load_correctly`
  - `test_examples_match_expected_format`
  - `test_examples_include_diverse_code_patterns`
  - `test_examples_handle_different_languages`

- `tests/unit/ai/prompts/test_optimization.py`:
  - `test_prompt_optimization_preserves_meaning`
  - `test_optimization_reduces_token_count`
  - `test_optimization_handles_long_code_files`
  - `test_optimization_respects_model_token_limits`

- `tests/unit/ai/prompts/test_schemas.py`:
  - `test_documentation_schema_validates_required_fields`
  - `test_schema_parsing_handles_malformed_llm_output`

**Quality Checks**: 80%+ coverage with mock LLM responses

**Commit**: `feat: implement slice 3 - LangChain integration and prompt engineering`

### Slice 4: OpenAI Provider with LangChain
**Goal**: Implement OpenAI provider using LangChain abstractions

**Implementation Details**:
- Create OpenAI provider using LangChain's OpenAI integration
- Implement token counting and cost estimation
- Add streaming support for large responses
- Handle rate limiting and API errors with retry logic
- Implement comprehensive error handling and logging

**Files to Create**:
```
spec_cli/ai/providers/
├── __init__.py
├── base.py             # Abstract provider interface
├── openai_provider.py  # OpenAI implementation
└── utils.py           # Provider utilities
```

**Detailed Implementation**:

**spec_cli/ai/providers/base.py**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

@dataclass
class GenerationRequest:
    file_path: Path
    file_content: str
    analysis: CodeAnalysis
    template_variables: Dict[str, Any]

@dataclass
class GenerationResult:
    success: bool
    content: Dict[str, str]
    error: Optional[str] = None
    tokens_used: int = 0
    cost_estimate: float = 0.0
    response_time: float = 0.0

class DocumentationProvider(ABC):
    @abstractmethod
    async def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        pass
```

**spec_cli/ai/providers/openai_provider.py**:
```python
class OpenAIProvider(DocumentationProvider):
    def __init__(self, config: OpenAIConfig):
        self.config = config
        self.chat_model = ChatOpenAI(...)
        self.encoding = tiktoken.encoding_for_model(config.model)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(...))
    async def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate documentation using OpenAI with retry logic."""

    def _prepare_prompt(self, request: GenerationRequest) -> str:
        """Prepare language-specific prompt for OpenAI."""

    def _calculate_cost(self, tokens: int) -> float:
        """Calculate API cost based on token usage."""
```

**Tests to Write** (24 comprehensive tests):
- `tests/unit/ai/providers/test_openai_provider.py`:
  - `test_openai_provider_initializes_with_valid_config`
  - `test_openai_provider_raises_error_with_invalid_api_key`
  - `test_openai_provider_generates_documentation_successfully`
  - `test_openai_provider_handles_api_rate_limit_errors`
  - `test_openai_provider_retries_on_temporary_failures`
  - `test_openai_provider_respects_max_retry_attempts`
  - `test_openai_provider_calculates_token_count_accurately`
  - `test_openai_provider_estimates_api_costs_correctly`
  - `test_openai_provider_handles_timeout_errors`
  - `test_openai_provider_validates_model_availability`
  - `test_openai_provider_streams_responses_for_large_outputs`
  - `test_openai_provider_truncates_input_when_exceeding_limits`
  - `test_openai_provider_logs_api_usage_metrics`
  - `test_openai_provider_handles_malformed_api_responses`
  - `test_openai_provider_supports_temperature_adjustment`
  - `test_openai_provider_supports_custom_system_prompts`
  - `test_openai_provider_handles_content_filtering_errors`
  - `test_openai_provider_supports_different_gpt_models`

- `tests/unit/ai/providers/test_base_provider.py`:
  - `test_base_provider_interface_enforces_required_methods`
  - `test_base_provider_validates_implementation_completeness`
  - `test_base_provider_handles_provider_registration`
  - `test_base_provider_supports_capability_checking`
  - `test_base_provider_validates_configuration_format`
  - `test_base_provider_handles_initialization_errors`

**Quality Checks**: 80%+ coverage including all error scenarios

**Commit**: `feat: implement slice 4 - OpenAI provider with LangChain integration`

### Slice 5: Anthropic Provider Implementation
**Goal**: Add Anthropic Claude provider to validate pluggable architecture

**Implementation Details**:
- Implement Anthropic provider using LangChain's Anthropic integration
- Handle Claude-specific features and limitations
- Add provider-specific prompt optimization
- Implement token counting for Claude models
- Add support for Claude's longer context windows

**Files to Create**:
```
spec_cli/ai/providers/anthropic_provider.py
```

**Detailed Implementation**:

**spec_cli/ai/providers/anthropic_provider.py**:
```python
class AnthropicProvider(DocumentationProvider):
    def __init__(self, config: AnthropicConfig):
        self.config = config
        self.client = anthropic.Anthropic(api_key=...)
        self.chat_model = ChatAnthropic(...)

    async def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate documentation using Claude with optimizations."""

    def _get_claude_system_prompt(self) -> str:
        """Get Claude-optimized system prompt."""

    def _prepare_claude_prompt(self, request: GenerationRequest) -> str:
        """Prepare Claude-specific prompt leveraging its strengths."""

    def _estimate_cost(self, tokens: int) -> float:
        """Estimate cost for Claude API usage."""
```

**Tests to Write** (21 comprehensive tests):
- `tests/unit/ai/providers/test_anthropic_provider.py`:
  - `test_anthropic_provider_initializes_with_valid_config`
  - `test_anthropic_provider_handles_different_claude_models`
  - `test_anthropic_provider_generates_documentation_successfully`
  - `test_anthropic_provider_handles_api_errors_gracefully`
  - `test_anthropic_provider_respects_token_limits`
  - `test_anthropic_provider_handles_rate_limiting`
  - `test_anthropic_provider_optimizes_prompts_for_claude`
  - `test_anthropic_provider_calculates_costs_accurately`
  - `test_anthropic_provider_handles_timeout_scenarios`
  - `test_anthropic_provider_validates_api_key_format`
  - `test_anthropic_provider_supports_streaming_responses`
  - `test_anthropic_provider_handles_content_filtering`
  - `test_anthropic_provider_logs_usage_metrics`
  - `test_anthropic_provider_handles_model_unavailability`
  - `test_anthropic_provider_supports_custom_instructions`
  - `test_anthropic_provider_handles_malformed_responses`
  - `test_anthropic_provider_compares_performance_with_openai`
  - `test_anthropic_provider_maintains_conversation_context`
  - `test_anthropic_provider_handles_unicode_content`
  - `test_anthropic_provider_supports_long_context_windows`
  - `test_anthropic_provider_validates_message_format`

**Quality Checks**: 80%+ coverage with mocked API calls

**Commit**: `feat: implement slice 5 - Anthropic provider implementation`

### Slice 6: Local Model Provider with Ollama
**Goal**: Add local model support for privacy and offline usage

**Implementation Details**:
- Implement local provider using Ollama or similar local inference
- Add model management and health checking
- Handle local model limitations and performance characteristics
- Implement fallback mechanisms for model unavailability
- Add support for multiple local model formats

**Files to Create**:
```
spec_cli/ai/providers/local_provider.py
spec_cli/ai/providers/model_manager.py
```

**Detailed Implementation**:

**spec_cli/ai/providers/local_provider.py**:
```python
class LocalProvider(DocumentationProvider):
    def __init__(self, config: LocalConfig):
        self.config = config
        self.model_manager = ModelManager(config)
        self.client = self._initialize_client()

    async def generate_documentation(self, request: GenerationRequest) -> GenerationResult:
        """Generate documentation using local models."""

    def _initialize_client(self):
        """Initialize connection to local inference server."""

    def _validate_model_availability(self) -> bool:
        """Check if configured model is available locally."""
```

**spec_cli/ai/providers/model_manager.py**:
```python
class ModelManager:
    def __init__(self, config: LocalConfig):
        self.config = config
        self.base_url = config.base_url

    def list_available_models(self) -> List[str]:
        """List models available on local server."""

    def check_model_health(self, model_name: str) -> bool:
        """Check if specific model is healthy and responsive."""

    def download_model_if_missing(self, model_name: str) -> bool:
        """Download model if not available locally."""
```

**Tests to Write** (19 comprehensive tests):
- `tests/unit/ai/providers/test_local_provider.py`:
  - `test_local_provider_connects_to_ollama_service`
  - `test_local_provider_handles_service_unavailable`
  - `test_local_provider_validates_model_availability`
  - `test_local_provider_downloads_models_when_missing`
  - `test_local_provider_generates_documentation_locally`
  - `test_local_provider_handles_insufficient_memory`
  - `test_local_provider_respects_timeout_settings`
  - `test_local_provider_handles_model_loading_errors`
  - `test_local_provider_supports_multiple_model_formats`
  - `test_local_provider_manages_concurrent_requests`
  - `test_local_provider_logs_performance_metrics`
  - `test_local_provider_handles_context_length_limits`
  - `test_local_provider_validates_model_compatibility`

- `tests/unit/ai/providers/test_model_manager.py`:
  - `test_model_manager_lists_available_models`
  - `test_model_manager_checks_model_health`
  - `test_model_manager_handles_model_updates`
  - `test_model_manager_manages_model_storage`
  - `test_model_manager_validates_model_requirements`
  - `test_model_manager_handles_download_failures`

**Quality Checks**: 80%+ coverage with mocked local services

**Commit**: `feat: implement slice 6 - local model provider with Ollama`

### Slice 7: Provider Factory and Dynamic Loading
**Goal**: Create dynamic provider loading and management system

**Implementation Details**:
- Implement provider factory with plugin architecture
- Add provider discovery and registration system
- Create provider health monitoring and automatic failover
- Implement dynamic provider switching based on availability
- Add provider capability detection and validation

**Files to Create**:
```
spec_cli/ai/factory.py
spec_cli/ai/registry.py
spec_cli/ai/health.py
```

**Detailed Implementation**:

**spec_cli/ai/factory.py**:
```python
class ProviderFactory:
    def __init__(self):
        self.registry = ProviderRegistry()
        self.health_checker = HealthChecker()
        self._provider_cache = {}

    def create_provider(self, provider_name: str, config: AIConfig) -> DocumentationProvider:
        """Create and configure provider instance."""

    def get_best_available_provider(self, config: AIConfig) -> DocumentationProvider:
        """Get the best available provider based on health and capabilities."""

    def _validate_provider_config(self, provider_name: str, config: Any) -> bool:
        """Validate provider-specific configuration."""
```

**spec_cli/ai/registry.py**:
```python
class ProviderRegistry:
    def __init__(self):
        self._providers = {}
        self._register_builtin_providers()

    def register_provider(self, name: str, provider_class: Type[DocumentationProvider]):
        """Register a provider class."""

    def get_provider_class(self, name: str) -> Type[DocumentationProvider]:
        """Get provider class by name."""

    def list_available_providers(self) -> List[str]:
        """List all registered provider names."""
```

**spec_cli/ai/health.py**:
```python
class HealthChecker:
    def __init__(self):
        self._health_cache = {}
        self._cache_ttl = 300  # 5 minutes

    async def check_provider_health(self, provider: DocumentationProvider) -> HealthStatus:
        """Check provider health and performance."""

    def get_health_score(self, provider_name: str) -> float:
        """Get cached health score for provider."""

    def should_use_fallback(self, primary_provider: str) -> bool:
        """Determine if fallback provider should be used."""
```

**Tests to Write** (25 comprehensive tests):
- `tests/unit/ai/test_factory.py`:
  - `test_factory_creates_openai_provider_with_valid_config`
  - `test_factory_creates_anthropic_provider_with_valid_config`
  - `test_factory_creates_local_provider_with_valid_config`
  - `test_factory_raises_error_for_unknown_provider`
  - `test_factory_validates_provider_configuration`
  - `test_factory_handles_provider_initialization_failures`
  - `test_factory_caches_provider_instances`
  - `test_factory_supports_provider_reconfiguration`
  - `test_factory_handles_missing_dependencies`

- `tests/unit/ai/test_registry.py`:
  - `test_registry_registers_providers_correctly`
  - `test_registry_prevents_duplicate_registrations`
  - `test_registry_lists_available_providers`
  - `test_registry_validates_provider_interfaces`
  - `test_registry_handles_provider_deregistration`
  - `test_registry_supports_provider_metadata`
  - `test_registry_handles_plugin_loading`

- `tests/unit/ai/test_health.py`:
  - `test_health_checker_validates_provider_connectivity`
  - `test_health_checker_detects_api_key_issues`
  - `test_health_checker_monitors_response_times`
  - `test_health_checker_handles_provider_failures`
  - `test_health_checker_provides_health_scores`
  - `test_health_checker_triggers_fallback_providers`
  - `test_health_checker_logs_health_metrics`
  - `test_health_checker_supports_custom_health_checks`
  - `test_health_checker_handles_intermittent_failures`

**Quality Checks**: 80%+ coverage including edge cases

**Commit**: `feat: implement slice 7 - provider factory and dynamic loading`

### Slice 8: Concurrent Processing with Progress Tracking
**Goal**: Implement high-performance concurrent AI generation with real-time progress

**Implementation Details**:
- Create async processing engine with semaphore-based concurrency control
- Implement rich progress display with file-by-file tracking like pytest
- Add error handling and partial failure recovery
- Create performance monitoring and optimization
- Add user interruption handling and graceful shutdown

**Files to Create**:
```
spec_cli/ai/processing.py
spec_cli/ai/progress.py
spec_cli/ai/performance.py
```

**Detailed Implementation**:

**spec_cli/ai/processing.py**:
```python
class ConcurrentProcessor:
    def __init__(self, provider: DocumentationProvider, max_concurrency: int = 5):
        self.provider = provider
        self.semaphore = asyncio.Semaphore(max_concurrency)
        self.progress_tracker = ProgressTracker()
        self.performance_monitor = PerformanceMonitor()

    async def process_files(self, requests: List[GenerationRequest]) -> List[GenerationResult]:
        """Process multiple files concurrently with progress tracking."""

    async def _process_single_file(self, request: GenerationRequest) -> GenerationResult:
        """Process single file with semaphore control."""

    def _handle_user_interruption(self):
        """Handle Ctrl+C gracefully."""
```

**spec_cli/ai/progress.py**:
```python
class ProgressTracker:
    def __init__(self, total_files: int):
        self.total_files = total_files
        self.completed = 0
        self.failed = 0
        self.start_time = time.time()

    def update_progress(self, file_path: Path, status: str):
        """Update progress display like pytest output."""

    def estimate_remaining_time(self) -> float:
        """Estimate time remaining based on current progress."""

    def display_summary(self):
        """Display final summary of processing results."""
```

**Tests to Write** (28 comprehensive tests):
- `tests/unit/ai/test_processing.py`:
  - `test_processor_handles_single_file_generation`
  - `test_processor_processes_multiple_files_concurrently`
  - `test_processor_respects_concurrency_limits`
  - `test_processor_handles_individual_file_failures`
  - `test_processor_continues_processing_after_partial_failures`
  - `test_processor_tracks_successful_completions`
  - `test_processor_tracks_failed_attempts`
  - `test_processor_retries_failed_generations`
  - `test_processor_respects_maximum_retry_attempts`
  - `test_processor_handles_timeout_scenarios`
  - `test_processor_cancels_processing_on_interrupt`
  - `test_processor_cleans_up_resources_properly`
  - `test_processor_handles_memory_pressure`
  - `test_processor_balances_load_across_providers`

- `tests/unit/ai/test_progress.py`:
  - `test_progress_tracker_initializes_with_file_list`
  - `test_progress_tracker_updates_completion_status`
  - `test_progress_tracker_calculates_percentage_complete`
  - `test_progress_tracker_estimates_remaining_time`
  - `test_progress_tracker_displays_current_file`
  - `test_progress_tracker_shows_error_counts`
  - `test_progress_tracker_handles_zero_files_gracefully`
  - `test_progress_tracker_supports_custom_formatters`
  - `test_progress_tracker_handles_rapid_updates`

- `tests/unit/ai/test_performance.py`:
  - `test_performance_monitor_tracks_processing_times`
  - `test_performance_monitor_measures_token_throughput`
  - `test_performance_monitor_calculates_cost_metrics`
  - `test_performance_monitor_identifies_bottlenecks`
  - `test_performance_monitor_provides_optimization_suggestions`

**Quality Checks**: 80%+ coverage with async testing

**Commit**: `feat: implement slice 8 - concurrent processing with progress tracking`

### Slice 9: Integration with Existing Gen Command
**Goal**: Seamlessly integrate AI generation into existing spec gen workflow

**Implementation Details**:
- Add `--ai` flag to cmd_gen function
- Modify generation pipeline to use AI when enabled
- Implement fallback to placeholder content on AI failures
- Add configuration validation and user guidance
- Preserve existing template structure and conflict resolution

**Files to Modify**:
```
spec_cli/__main__.py - Update cmd_gen function
Integration points throughout generation pipeline
```

**Detailed Implementation**:

**spec_cli/__main__.py updates**:
```python
def cmd_gen(args: List[str]) -> None:
    """Generate spec documentation for file(s) or directory."""
    # Parse arguments for --ai flag
    use_ai = "--ai" in args
    paths = [arg for arg in args if not arg.startswith("--")]

    if use_ai:
        ai_config = load_ai_config()
        provider_factory = ProviderFactory()
        provider = provider_factory.create_provider(ai_config.provider, ai_config)
        processor = ConcurrentProcessor(provider, ai_config.max_concurrency)

    # Enhanced generation with AI integration

async def generate_with_ai(file_path: Path, spec_dir: Path, template: TemplateConfig) -> bool:
    """Generate content using AI provider with fallback."""

def fallback_to_placeholder(file_path: Path, spec_dir: Path, template: TemplateConfig):
    """Fallback to existing placeholder generation."""
```

**Tests to Write** (23 comprehensive tests):
- `tests/unit/test_cmd_gen_ai_integration.py`:
  - `test_cmd_gen_with_ai_flag_uses_ai_provider`
  - `test_cmd_gen_without_ai_flag_uses_placeholder_content`
  - `test_cmd_gen_ai_handles_provider_configuration_errors`
  - `test_cmd_gen_ai_falls_back_to_placeholder_on_ai_failure`
  - `test_cmd_gen_ai_respects_concurrent_processing_limits`
  - `test_cmd_gen_ai_validates_api_keys_before_processing`
  - `test_cmd_gen_ai_displays_progress_for_multiple_files`
  - `test_cmd_gen_ai_handles_mixed_success_and_failure_scenarios`
  - `test_cmd_gen_ai_preserves_existing_template_structure`
  - `test_cmd_gen_ai_logs_generation_metrics`
  - `test_cmd_gen_ai_handles_user_interruption_gracefully`
  - `test_cmd_gen_ai_validates_file_types_before_processing`
  - `test_cmd_gen_ai_handles_empty_directories`
  - `test_cmd_gen_ai_supports_dry_run_mode`

- `tests/unit/test_ai_content_integration.py`:
  - `test_ai_content_replaces_placeholder_variables`
  - `test_ai_content_preserves_template_formatting`
  - `test_ai_content_handles_unicode_and_special_characters`
  - `test_ai_content_validates_generated_content_length`
  - `test_ai_content_sanitizes_potentially_harmful_content`
  - `test_ai_content_maintains_markdown_formatting`
  - `test_ai_content_handles_code_blocks_properly`
  - `test_ai_content_preserves_template_metadata`
  - `test_ai_content_handles_incomplete_ai_responses`

**Quality Checks**: 80%+ coverage including integration paths

**Commit**: `feat: implement slice 9 - AI integration with gen command`

### Slice 10: Advanced Configuration and CLI Enhancements
**Goal**: Complete AI configuration system with CLI improvements and diagnostics

**Implementation Details**:
- Add comprehensive configuration validation and interactive setup
- Implement AI-specific CLI commands for configuration and testing
- Create troubleshooting and diagnostic tools
- Add configuration templates and examples
- Implement configuration migration and validation

**Files to Create**:
```
spec_cli/ai/cli.py - AI-specific CLI commands
spec_cli/ai/diagnostics.py - Troubleshooting tools
spec_cli/ai/setup.py - Interactive configuration
```

**Detailed Implementation**:

**spec_cli/ai/cli.py**:
```python
def cmd_ai_config(args: List[str]):
    """Manage AI configuration settings."""

def cmd_ai_test(args: List[str]):
    """Test AI provider connectivity and configuration."""

def cmd_ai_setup(args: List[str]):
    """Interactive AI configuration setup wizard."""

def cmd_ai_providers(args: List[str]):
    """List available AI providers and their status."""
```

**spec_cli/ai/diagnostics.py**:
```python
class DiagnosticRunner:
    def __init__(self):
        self.checks = [
            self._check_api_keys,
            self._check_network_connectivity,
            self._check_model_availability,
            self._check_configuration_validity
        ]

    def run_diagnostics(self) -> DiagnosticReport:
        """Run comprehensive diagnostics and return report."""

    def _check_api_keys(self) -> CheckResult:
        """Validate API key configuration and access."""

    def _generate_troubleshooting_suggestions(self, issues: List[str]) -> List[str]:
        """Generate actionable troubleshooting suggestions."""
```

**spec_cli/ai/setup.py**:
```python
class SetupWizard:
    def __init__(self):
        self.config_builder = ConfigBuilder()

    def run_interactive_setup(self) -> AIConfig:
        """Guide user through AI configuration setup."""

    def _prompt_provider_selection(self) -> str:
        """Interactive provider selection with explanations."""

    def _validate_and_test_configuration(self, config: AIConfig) -> bool:
        """Test configuration before saving."""
```

**Tests to Write** (21 comprehensive tests):
- `tests/unit/ai/test_cli.py`:
  - `test_ai_config_command_displays_current_configuration`
  - `test_ai_config_command_validates_provider_settings`
  - `test_ai_config_command_updates_configuration_values`
  - `test_ai_config_command_handles_invalid_values_gracefully`
  - `test_ai_setup_command_guides_user_through_configuration`
  - `test_ai_test_command_validates_provider_connectivity`
  - `test_ai_list_command_shows_available_providers`

- `tests/unit/ai/test_diagnostics.py`:
  - `test_diagnostics_checks_api_key_validity`
  - `test_diagnostics_measures_provider_response_times`
  - `test_diagnostics_validates_model_availability`
  - `test_diagnostics_checks_network_connectivity`
  - `test_diagnostics_provides_troubleshooting_suggestions`
  - `test_diagnostics_generates_configuration_report`
  - `test_diagnostics_identifies_common_issues`

- `tests/unit/ai/test_setup.py`:
  - `test_setup_wizard_guides_provider_selection`
  - `test_setup_wizard_validates_api_credentials`
  - `test_setup_wizard_creates_working_configuration`
  - `test_setup_wizard_handles_user_cancellation`
  - `test_setup_wizard_provides_helpful_guidance`
  - `test_setup_wizard_supports_advanced_options`
  - `test_setup_wizard_handles_existing_configuration`

**Quality Checks**: 80%+ coverage including CLI interactions

**Commit**: `feat: implement slice 10 - advanced configuration and CLI enhancements`

## Dependencies to Add

### Core Dependencies
```toml
[tool.poetry.dependencies]
# LangChain ecosystem
langchain = "^0.1.0"
langchain-community = "^0.0.20"
langchain-openai = "^0.0.5"
langchain-anthropic = "^0.1.0"

# AI/ML libraries
openai = "^1.12.0"
anthropic = "^0.18.0"
tiktoken = "^0.6.0"
transformers = "^4.37.0"
huggingface-hub = "^0.20.0"

# Async and networking
aiohttp = "^3.9.0"
httpx = "^0.26.0"

# Progress and UI
rich = "^13.7.0"
```

### Development Dependencies
```toml
[tool.poetry.group.dev.dependencies]
pytest-asyncio = "^0.23.0"
pytest-mock = "^3.12.0"
pytest-httpx = "^0.28.0"
respx = "^0.20.0"  # HTTP mocking for tests
```

## Quality Standards Summary

### Test Coverage Requirements
- **Total Tests Planned**: 213 comprehensive tests across all slices
- **Overall Coverage**: Minimum 80% per slice
- **Branch Coverage**: All conditional paths tested
- **Error Path Coverage**: All exception scenarios tested
- **Integration Coverage**: End-to-end AI generation flows tested

### Performance Requirements
- [ ] Generate docs for 100 files in under 5 minutes
- [ ] Handle files up to 10MB in size
- [ ] Support up to 20 concurrent requests
- [ ] Graceful degradation under API rate limits
- [ ] Memory usage stays under 500MB during processing

### Success Criteria
- [ ] All 10 slices implemented with 80%+ test coverage
- [ ] Type checking passes with mypy --strict
- [ ] All providers (OpenAI, Anthropic, Local) working
- [ ] Concurrent processing with configurable limits
- [ ] Comprehensive error handling and recovery
- [ ] Rich progress display during generation
- [ ] Configuration validation and user guidance
