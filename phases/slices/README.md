# Slices: Hierarchical Ultra-Focused Implementation Units

This directory contains the hierarchical slice decomposition for the singleton to dependency injection migration. Each slice is designed for execution by ultra-focused AI agents following P0-ABSOLUTE constraints.

## Slice Generation Compliance

All slices have been generated following the Hierarchical Slice Generation Framework with:

- **Helper Function Reuse**: All slices include mandatory helper search evidence and reuse existing utilities
- **Granularity Compliance**: ≤3 files, ≤2 classes, ≤7 McCabe complexity per slice
- **Single-Agent Executability**: Clear inputs/actions/outputs with complete dependency documentation
- **Quality Gate Integration**: Poetry-based quality validation throughout
- **Context Integration**: Phase-level context and business value alignment

## Phase 1: Context Infrastructure Foundation

### P1.1: SpecContext Core Implementation
- **Business Value**: Immutable dependency container foundation
- **Files**: 2 (context.py, context_utils.py)
- **Complexity**: 4/7 McCabe points
- **Dependencies**: Existing error_utils, env_utils, new context_utils
- **Integration**: Ready for factory methods

### P1.2: Factory Method Implementation
- **Business Value**: Environment-specific context creation
- **Files**: 2 (extend context.py, factory_utils.py)
- **Complexity**: 6/7 McCabe points
- **Dependencies**: P1.1 SpecContext, test_helpers, factory_utils
- **Integration**: Ready for compatibility layer

### P1.3: Compatibility Layer Foundation
- **Business Value**: Backward compatibility during migration
- **Files**: 2 (compatibility.py, compatibility_utils.py)
- **Complexity**: 5/7 McCabe points
- **Dependencies**: Existing singleton.py, P1.1-P1.2 context system
- **Integration**: Foundation ready for CLI integration

## Phase 2: CLI Integration and Command Migration

### P2.1: Click Framework Integration
- **Business Value**: CLI dependency injection foundation
- **Files**: 2 (context_integration.py, click_utils.py)
- **Complexity**: 6/7 McCabe points
- **Dependencies**: Phase 1 SpecContext, existing CLI patterns
- **Integration**: Ready for command decorators

### P2.2: Command Decorator System
- **Business Value**: Automatic context injection for commands
- **Files**: 2 (decorators.py, decorator_utils.py)
- **Complexity**: 7/7 McCabe points
- **Dependencies**: P2.1 Click integration, existing decorator patterns
- **Integration**: Ready for command migration

### P2.3: Core Command Migration
- **Business Value**: Essential CLI commands with dependency injection
- **Files**: 3 (init.py, status.py, app.py)
- **Complexity**: 6/7 McCabe points
- **Dependencies**: P2.2 decorators, existing command structure
- **Integration**: Foundation for complete migration

## Phase 3: Complete Migration and Singleton Elimination

### P3.1: Remaining Command Migration
- **Business Value**: Complete CLI command dependency injection
- **Files**: 3 (add.py, commit.py, gen.py)
- **Complexity**: 6/7 McCabe points
- **Dependencies**: P2.2-P2.3 migration patterns, command structure
- **Integration**: Ready for singleton elimination

### P3.2: Singleton Class Elimination and Detection Automation
- **Business Value**: Complete singleton elimination with prevention automation
- **Files**: 3 (remove singleton.py/compatibility.py, create tools/singleton_detector.py)
- **Complexity**: 7/7 McCabe points
- **Dependencies**: Platform_utils, new singleton_detection automation
- **Integration**: Ready for test framework migration

### P3.3: Test Framework Migration
- **Business Value**: 100% test reliability through context isolation
- **Files**: 2 (conftest.py, test_migration_utils.py)
- **Complexity**: 7/7 McCabe points
- **Dependencies**: P1 testing factories, existing test_helpers
- **Integration**: Complete migration with 100% reliability

## Execution Guidelines

### Sequential Dependencies
- **Phase 1**: P1.1 → P1.2 → P1.3 (strict sequential)
- **Phase 2**: P2.1 → P2.2 → P2.3 (strict sequential)
- **Phase 3**: P3.1 → P3.2 → P3.3 (strict sequential)
- **Inter-Phase**: Phase 1 must complete before Phase 2, Phase 2 before Phase 3

### Quality Validation per Slice
Each slice must pass complete quality gates using Poetry:
```bash
poetry run mypy --strict              # Type checking
poetry run ruff check --fix           # Linting
poetry run ruff format                # Formatting
poetry run pydocstyle                 # Documentation
poetry run bandit -r spec_cli/        # Security
poetry run pip-audit                  # Vulnerability scan
poetry run pytest -v --cov=spec_cli --cov-fail-under=90  # Testing
```

### Success Metrics by Phase

**Phase 1 Success**:
- Context creation <1ms CLI, <10ms testing
- 100% existing test pass rate maintained
- Complete type safety (100% mypy compliance)

**Phase 2 Success**:
- Context injection <1ms overhead per command
- Zero user-visible behavior changes
- Core commands work with dependency injection

**Phase 3 Success**:
- 100% test success rate (eliminating all 58 systematic failures)
- Zero singleton patterns (verified by automation tool)
- Concurrent CLI operation support

## Helper Function Reuse Evidence

All slices include comprehensive helper search evidence and maximize reuse of existing utilities:

- **Existing Utils**: error_utils, env_utils, platform_utils, test_helpers, singleton.py
- **New Helpers**: context_utils, factory_utils, compatibility_utils, click_utils, decorator_utils, migration_utils, singleton_detection, test_migration_utils
- **Complexity Reduction**: Helper calls don't count toward McCabe complexity, enabling focused implementation

## Implementation Focus

Each slice focuses on core implementation without test scaffolding:
- Clear business value delivery
- Helper function reuse and complexity management
- Quality gate compliance through Poetry tooling
- Integration readiness for subsequent slices

---

*This slice decomposition provides a systematic path to eliminate singleton patterns and achieve 100% test reliability while maintaining complete backward compatibility and user transparency.*
