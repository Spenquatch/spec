# PHASE-3: Template System

## Overview

Extracts the template system into a shared module that can be used by both cmd_gen and future git hooks. This phase creates clean interfaces for template loading, validation, and content generation while maintaining backward compatibility with existing `.spectemplate` files.

## Prerequisites

- **PHASE-1 complete**: Exception hierarchy, logging, and configuration systems
- **PHASE-2 complete**: File system operations for template file handling
- **Required modules**: All foundation and file system modules

## Slice Execution Order

Execute slices in the following order due to dependencies:

1. **slice-7-template-config.md** - Must be first (defines template structure and validation)
2. **slice-8a-template-substitution.md** - Second (core substitution engine)
3. **slice-8b-spec-generator.md** - Third (spec file generation using substitution engine)
4. **slice-8c-ai-hooks.md** - Fourth (AI integration infrastructure)

## Shared Concepts

- **Template Configuration**: Pydantic models for template validation and structure
- **Variable Substitution**: Consistent system for replacing placeholders in templates
- **Template Loading**: Unified loading from `.spectemplate` files with fallback to defaults
- **Content Generation**: Systematic generation of `index.md` and `history.md` files

## Phase Completion Criteria

- [ ] Template configuration with comprehensive validation
- [ ] Template loading from files with proper error handling
- [ ] Content generation with variable substitution
- [ ] Backward compatibility with existing `.spectemplate` files maintained
- [ ] Integration points defined for future AI content injection
- [ ] All modules have 80%+ test coverage
- [ ] Type hints throughout with mypy compliance

## Slice Files

- [slice-7-template-config.md](./slice-7-template-config.md) - Template configuration models and validation
- [slice-8a-template-substitution.md](./slice-8a-template-substitution.md) - Core substitution engine with configurable delimiters
- [slice-8b-spec-generator.md](./slice-8b-spec-generator.md) - Spec file generation workflow and file operations
- [slice-8c-ai-hooks.md](./slice-8c-ai-hooks.md) - AI integration infrastructure with retry logic
- [slice-8-template-generation.md](./slice-8-template-generation.md) - **[DEPRECATED]** Combined slice split into 8A/8B/8C

## Next Phase

Once complete, enables PHASE-4 (git and core logic) which will use the template system for documentation generation during file processing.