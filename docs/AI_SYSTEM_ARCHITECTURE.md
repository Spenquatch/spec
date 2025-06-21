# AI System Architecture Documentation

This document provides a comprehensive overview of the AI system architecture in spec-cli, detailing the complete flow from user commands through AI generation to final output.

## Table of Contents

1. [System Overview](#system-overview)
2. [Core Components](#core-components)
3. [Execution Flow](#execution-flow)
4. [Component Details](#component-details)
5. [Configuration System](#configuration-system)
6. [Template Integration](#template-integration)
7. [Provider System](#provider-system)
8. [Troubleshooting Summary](#troubleshooting-summary)

## System Overview

The spec-cli AI system is designed as the primary documentation generation engine, with template-based fallback for reliability. The architecture follows a modular design with clear separation of concerns:

- **AI-First Approach**: AI generation is the primary method for creating documentation
- **Template Fallback**: Enhanced templates provide fallback when AI is unavailable
- **Modular Providers**: Pluggable AI provider system supporting local and future cloud providers
- **Cross-Platform Support**: Works on Windows, macOS, and Linux with platform-specific optimizations

## Core Components

### High-Level Architecture

```mermaid
graph TB
    subgraph "User Interface"
        CLI[CLI Command]
        CMD[spec gen command]
    end

    subgraph "Command Layer"
        GC[GenCommand]
        EXEC[_execute_single_file]
    end

    subgraph "AI Generation Layer"
        AG[AIDocumentationGenerator]
        PM[ProviderManager]
        AIR[generate_with_ai_request]
    end

    subgraph "Provider Layer"
        LAP[LocalAIProvider]
        DG[DocumentationGenerator]
        MODEL[Qwen2.5-Coder Model]
    end

    subgraph "Template System"
        AET[AIEnhancedTemplate]
        PG[PromptGenerator]
        TS[TemplateSubstitution]
    end

    subgraph "Configuration"
        CONFIG[AIConfig]
        LMC[LocalModelConfig]
        SEC[SecurityConfig]
    end

    subgraph "Output"
        FILES[.specs/ files]
        INDEX[index.md]
        HIST[history.md]
    end

    CLI --> CMD
    CMD --> GC
    GC --> EXEC
    EXEC --> AG
    AG --> PM
    PM --> LAP
    LAP --> DG
    DG --> MODEL

    EXEC --> AET
    AET --> PG
    AET --> TS

    CONFIG --> PM
    LMC --> LAP
    SEC --> LAP

    AG --> FILES
    FILES --> INDEX
    FILES --> HIST
```

## Execution Flow

### Complete Generation Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI (app.py)
    participant Gen as GenCommand
    participant AIGen as AIGenerator
    participant PM as ProviderManager
    participant Local as LocalAIProvider
    participant DocGen as DocumentationGenerator
    participant Model as AI Model
    participant Template as AIEnhancedTemplate
    participant FS as FileSystem

    User->>CLI: spec gen calculator.py
    CLI->>Gen: execute(files=['calculator.py'])
    Gen->>Gen: validate_repository_state()
    Gen->>Gen: _expand_source_files()

    loop For each file
        Gen->>Gen: _execute_single_file()
        Gen->>Template: load_and_process_template()
        Template->>Template: Load template content
        Template->>Template: Process variables
        Template-->>Gen: TemplateResult

        Gen->>Gen: _generate_with_ai_templates()
        Gen->>Template: create_generation_request()
        Template-->>Gen: GenerationRequest

        Gen->>AIGen: generate_with_ai_request()
        AIGen->>PM: get_available_provider()
        PM->>Local: new LocalAIProvider()
        PM->>Local: is_available()
        Local-->>PM: true
        PM-->>AIGen: LocalAIProvider

        AIGen->>Local: generate_documentation(request)
        Local->>DocGen: new DocumentationGenerator()
        Local->>DocGen: load_model(device)
        DocGen->>Model: Load Qwen2.5-Coder
        DocGen-->>Local: Model loaded

        Local->>DocGen: generate_documentation(request)
        DocGen->>DocGen: _create_documentation_prompt()
        DocGen->>Model: Generate with prompt
        Model-->>DocGen: Generated text
        DocGen->>DocGen: _parse_generated_content()
        DocGen-->>Local: GenerationResult
        Local-->>AIGen: GenerationResult

        AIGen-->>Gen: WorkflowResult
        Gen->>Gen: _finalize_ai_results()
        Gen->>FS: Write index.md
        Gen->>FS: Write history.md
        Gen-->>User: Success message
    end
```

### AI Generation Decision Flow

```mermaid
flowchart TD
    Start([User runs spec gen]) --> CheckNoAI{--no-ai flag?}
    CheckNoAI -->|Yes| Templates[Use Template Generation]
    CheckNoAI -->|No| LoadConfig[Load AI Configuration]

    LoadConfig --> CheckEnabled{AI Enabled?}
    CheckEnabled -->|No| Templates
    CheckEnabled -->|Yes| LoadTemplate[Load & Process Template]

    LoadTemplate --> CreateRequest[Create GenerationRequest<br/>with template as prompt]
    CreateRequest --> GetProvider[Get Available Provider]

    GetProvider --> CheckProvider{Provider<br/>Available?}
    CheckProvider -->|No| CheckFallback{Fallback<br/>Enabled?}
    CheckProvider -->|Yes| AIGen[Generate with AI]

    CheckFallback -->|Yes| Templates
    CheckFallback -->|No| Error([Error: No provider])

    AIGen --> CheckSuccess{Generation<br/>Successful?}
    CheckSuccess -->|Yes| WriteFiles[Write .specs/ files]
    CheckSuccess -->|No| CheckFallback2{Fallback<br/>Needed?}

    CheckFallback2 -->|Yes| Templates
    CheckFallback2 -->|No| Error2([Error: Generation failed])

    Templates --> WriteFiles
    WriteFiles --> End([Complete])
```

## Component Details

### 1. Command Layer (`gen_command.py`)

The entry point for AI generation, handling:
- Command argument parsing and validation
- Repository state validation
- File expansion (directories to individual files)
- Orchestration of AI generation with template fallback

Key methods:
- `execute()`: Main command entry point
- `_execute_single_file()`: Process individual file with AI-first approach
- `_generate_with_ai_templates()`: Generate using templates as AI prompts
- `_finalize_ai_results()`: Write AI-generated content to disk

### 2. AI Generation Layer (`ai_generator.py`)

Core AI orchestration logic:
- Configuration loading and validation
- Provider selection through ProviderManager
- Request/response handling
- Fallback signaling

Key classes:
- `AIDocumentationGenerator`: Main generator coordinating AI providers
- Functions: `generate_with_ai()`, `generate_with_ai_request()`

### 3. Provider System

#### Provider Manager (`manager.py`)
Selects appropriate AI provider based on configuration:
- Checks AI enabled status
- Validates provider availability
- Returns configured provider or None

#### Local AI Provider (`local.py`)
Implements AI generation using local models:
- HuggingFace transformers integration
- Cross-platform device detection (CUDA, MPS, CPU)
- Security validation through CodeSanitizer
- Resource management and cleanup

Key features:
- Automatic device selection (GPU/CPU)
- Memory optimization with 4-bit quantization
- Platform-specific optimizations

#### Documentation Generator (`generation.py`)
Handles actual model operations:
- Model loading with caching
- Prompt creation from templates
- Text generation with configurable parameters
- Output parsing and structuring

### 4. Template System

#### AI Enhanced Template (`ai_enhanced.py`)
Bridges templates with AI generation:
- Traditional variable substitution (backward compatible)
- AI prompt structure generation
- Template validation for AI compatibility
- Creation of GenerationRequest objects

#### Prompt Generator (`prompt_generator.py`)
Converts templates to AI-friendly prompts:
- Analyzes template structure
- Extracts placeholders and sections
- Generates AI instructions

## Configuration System

### AI Configuration Structure

```yaml
ai:
  enabled: true                    # AI is core feature
  provider: "local"                # Primary provider
  local:
    model_name: "Qwen/Qwen2.5-Coder-0.5B-Instruct"
    max_tokens: 512               # Generation limit
    temperature: 0.1              # Low for consistency
    use_4bit: true               # Memory optimization
    device: "auto"               # Platform detection
    cache_enabled: true          # Model caching
  security:
    sanitize_code: true          # Security scanning
    max_file_size_kb: 100        # Size limits
    blocked_patterns:            # Sensitive data
      - "api[_-]?key"
      - "secret"
      - "password"
  monitoring:
    enabled: false               # Performance tracking
    overhead_limit_percent: 5.0  # Resource limits
  fallback_to_templates: true    # Reliability fallback
```

### Configuration Loading Flow

```mermaid
graph LR
    subgraph "Configuration Sources"
        DEFAULT[Default Config]
        PROJECT[.specconfig.yaml]
        USER[User Config]
        ENV[Environment Vars]
    end

    subgraph "Configuration Loader"
        LOADER[AIConfigLoader]
        MERGE[Merge Logic]
        VALIDATE[Validation]
    end

    subgraph "Configuration Models"
        AICONF[AIConfig]
        LOCAL[LocalModelConfig]
        SEC[SecurityConfig]
        MON[MonitoringConfig]
    end

    DEFAULT --> LOADER
    PROJECT --> LOADER
    USER --> LOADER
    ENV --> LOADER

    LOADER --> MERGE
    MERGE --> VALIDATE
    VALIDATE --> AICONF

    AICONF --> LOCAL
    AICONF --> SEC
    AICONF --> MON
```

## Template Integration

### Template-to-AI Flow

```mermaid
flowchart TD
    subgraph "Template Processing"
        LOAD[Load Template File]
        PARSE[Parse Variables]
        ENHANCE[AI Enhancement]
    end

    subgraph "AI Prompt Creation"
        ANALYZE[Analyze Structure]
        EXTRACT[Extract Placeholders]
        PROMPT[Create Prompt]
    end

    subgraph "Generation Request"
        REQUEST[GenerationRequest]
        CONTEXT[Add Context]
        TEMPLATE[Template Content]
    end

    LOAD --> PARSE
    PARSE --> ENHANCE
    ENHANCE --> ANALYZE

    ANALYZE --> EXTRACT
    EXTRACT --> PROMPT

    PROMPT --> REQUEST
    REQUEST --> CONTEXT
    REQUEST --> TEMPLATE

    TEMPLATE -->|Original with<br/>placeholders| AI[AI Provider]
```

### Template Variable Flow

The system handles two types of variables:
1. **Static Variables**: Pre-filled by the system (filename, date, path)
2. **AI Variables**: Generated by AI analysis (purpose, dependencies, API)

## Provider System

### Provider Selection Logic

```python
# Simplified provider selection
def get_available_provider():
    if not ai_config.enabled:
        return None

    if ai_config.provider == "local":
        provider = LocalAIProvider(config)
        if provider.is_available():
            return provider

    return None  # Triggers fallback
```

### Local AI Provider Architecture

```mermaid
graph TB
    subgraph "LocalAIProvider"
        CHECK[is_available]
        GEN[generate_documentation]
        CLEAN[cleanup]
    end

    subgraph "Availability Checks"
        DEPS[HuggingFace Available?]
        SYS[System Requirements?]
        DEVICE[Device Available?]
    end

    subgraph "Generation Process"
        VAL[Validate Request]
        SAN[Sanitize Content]
        GDEV[Get Device]
        CREATE[Create Generator]
        LOAD[Load Model]
        GENERATE[Generate Docs]
    end

    CHECK --> DEPS
    CHECK --> SYS
    CHECK --> DEVICE

    GEN --> VAL
    VAL --> SAN
    SAN --> GDEV
    GDEV --> CREATE
    CREATE --> LOAD
    LOAD --> GENERATE
```

## Troubleshooting Summary

Based on the investigation documented in `AI_TROUBLESHOOTING.md`, the key issues resolved were:

### 1. Dual AI System Confusion
**Problem**: Two AI systems existed - old PlaceholderAIProvider and new LocalAIProvider
**Solution**: Eliminated PlaceholderAIProvider, forced new AI system usage

### 2. AI Dependencies as Optional
**Problem**: Core AI dependencies were optional extras, causing availability issues
**Solution**: Made PyTorch and transformers core dependencies

### 3. Empty AI Generation
**Problem**: Model immediately generated EOS token without content
**Root Cause**: Complex template prompt incompatible with small 0.5B model
**Solution**: Simplified prompt format for better model compatibility

### 4. Model Loading Issues
**Problem**: Model loading code not being reached despite provider availability
**Solution**: Fixed execution flow and added proper debug tracing

### Current Architecture Status

✅ **Working Components**:
- AI configuration loading
- Provider selection (LocalAIProvider)
- Template-to-prompt conversion
- Model loading and inference
- Cross-platform device detection
- File writing to .specs/ directory

❌ **Known Limitations**:
- 0.5B model size insufficient for complex templates
- Model generates minimal content with current prompts
- Need better prompt engineering for small models

🔄 **Recommended Improvements**:
- Upgrade to larger model (1B+ parameters)
- Implement hybrid approach (pre-fill static variables)
- Optimize prompts for specific model architecture
- Add model-specific prompt templates

## Future Enhancements

1. **Cloud Provider Support**: Add OpenAI, Anthropic, Cohere providers
2. **Model Selection**: Support multiple local models with auto-selection
3. **Caching Layer**: Cache generated documentation for similar files
4. **Incremental Generation**: Only regenerate changed sections
5. **Multi-File Context**: Use project-wide context for better documentation
6. **Custom Prompts**: User-defined prompt templates per project
