# Phase Decomposition: Complete Singleton to Dependency Injection Migration

This directory contains the complete phase decomposition for migrating spec-cli from singleton pattern to dependency injection architecture, eliminating **484+ singleton violations** identified by automated detection.

## Migration Overview

**Feature**: Complete Singleton to Dependency Injection Architecture Migration
**Business Value**: Eliminate 58+ systematic test failures, 484+ singleton violations, and production reliability risks
**Technical Objective**: Replace global singleton pattern with immutable dependency injection throughout entire codebase
**Success Metrics**: 100% test reliability, zero singleton patterns, concurrent CLI operation support, improved maintainability

## Detection-Driven Migration Strategy

Our singleton detection system identified violations in critical areas:
- **Core UI Services**: ConsoleManager, ThemeManager, ProgressManager (58 violations)
- **Configuration Services**: SettingsManager (23 violations)
- **Application Infrastructure**: Context, workflow, and service layers (180+ violations)
- **Test Infrastructure**: Singleton-dependent fixtures and helpers (95+ violations)
- **Third-party Dependencies**: External library singletons (128+ violations)

## Phase Structure

### Phase 1: Context Infrastructure Foundation ✅ COMPLETED
**Duration**: 2 days
**Objective**: Establish core dependency injection infrastructure
**Status**: Implementation complete, foundation established

**Key Deliverables**:
- ✅ Immutable SpecContext dataclass implementation
- ✅ Environment-specific factory methods (CLI and testing)
- ✅ Backward compatibility layer for existing singleton usage

**Slice Breakdown**:
- **P1.1**: ✅ SpecContext Core Implementation
- **P1.2**: ✅ Factory Method Implementation
- **P1.3**: ✅ Compatibility Layer Foundation

### Phase 2: CLI Integration and Command Migration ✅ COMPLETED
**Duration**: 2 days
**Objective**: Integrate context system with Click CLI framework
**Status**: CLI commands migrated to dependency injection

**Key Deliverables**:
- ✅ Click framework integration for SpecContext
- ✅ Command decorator system for automatic context injection
- ✅ Core CLI command migration (init, add, commit, gen, status)

**Slice Breakdown**:
- **P2.1**: ✅ Click Framework Integration
- **P2.2**: ✅ Command Decorator System
- **P2.3**: ✅ Core Command Migration

### Phase 3: Detection Infrastructure and Prevention ✅ PARTIALLY COMPLETED
**Duration**: 2 days
**Objective**: Build detection systems and prevent singleton reintroduction
**Status**: Detection system complete, prevention infrastructure in progress

**Key Deliverables**:
- ✅ Advanced command migration (remaining CLI commands)
- ✅ **Singleton detection system with AST analysis** (484+ violations identified)
- 🚧 Pre-commit hook integration for prevention
- 📋 Test fixture analysis and migration planning

**Slice Breakdown**:
- **P3.1**: ✅ Remaining Command Migration (add, commit, gen commands)
- **P3.2a**: ✅ Singleton Infrastructure Removal (cleanup utilities)
- **P3.2b**: ✅ **Singleton Detection System Implementation** (comprehensive AST-based detection)
- **P3.2c**: 🚧 Pre-commit Hook Integration (prevent reintroduction)
- **P3.3a**: 📋 Test Fixture Analysis and Documentation
- **P3.3b**: 📋 Context-Based Fixture Migration

### Phase 4: Core Service Singleton Elimination 📋 PLANNED
**Duration**: 3 days
**Objective**: Systematically eliminate high-priority singleton services identified by detection system
**Status**: Planned based on detection system findings

**Critical Violations to Address** (58 core service violations):
- `spec_cli/ui/console.py` - ConsoleManager singleton (3 violations)
- `spec_cli/ui/theme.py` - ThemeManager singleton (3 violations)
- `spec_cli/ui/progress_manager.py` - ProgressManagerSingleton (3 violations)
- `spec_cli/config/settings.py` - SettingsManager singleton (3 violations)
- Core workflow and context managers (46+ violations)

**Key Deliverables**:
- Core UI service migration to dependency injection
- Configuration service migration to context-based patterns
- Application infrastructure singleton elimination
- Consumer update for dependency injection patterns

**Slice Breakdown**:
- **P4.1a**: Settings and Configuration Migration (SettingsManager → context injection)
- **P4.1b**: Configuration Consumer Migration (update all settings usage)
- **P4.2a**: UI Service Migration (Console, Theme, Progress managers)
- **P4.2b**: UI Consumer Migration (update all UI service usage)
- **P4.3a**: Core Infrastructure Migration (workflow, context managers)
- **P4.3b**: Infrastructure Consumer Migration (update all infrastructure usage)

### Phase 5: Comprehensive Singleton Elimination 📋 PLANNED
**Duration**: 4 days
**Objective**: Eliminate remaining 426+ singleton violations across entire codebase
**Status**: Planned based on systematic detection analysis

**Remaining Violations by Category**:
- **Application Code**: 180+ internal singleton patterns
- **Test Infrastructure**: 95+ singleton-dependent test patterns
- **Integration Points**: 23+ external service singleton wrappers
- **Third-party Mitigation**: 128+ external library singleton isolation

**Key Deliverables**:
- Complete application singleton elimination
- Test infrastructure context migration
- External singleton isolation patterns
- Validation of zero singleton patterns

**Slice Breakdown**:
- **P5.1a**: Application Singleton Elimination (business logic singletons)
- **P5.1b**: Application Consumer Migration (update business logic consumers)
- **P5.2a**: Integration Point Migration (external service wrappers)
- **P5.2b**: Integration Consumer Migration (update integration usage)
- **P5.3a**: Test Infrastructure Singleton Elimination (test helpers, fixtures)
- **P5.3b**: Test Consumer Migration (update all test singleton usage)
- **P5.4a**: Third-party Singleton Isolation (external library patterns)
- **P5.4b**: Validation and Cleanup (ensure zero singleton patterns)

### Phase 6: Architecture Validation and Performance Optimization 📋 PLANNED
**Duration**: 2 days
**Objective**: Validate complete singleton elimination and optimize dependency injection performance
**Status**: Planned for final validation

**Key Deliverables**:
- Comprehensive singleton detection validation (zero violations)
- Performance optimization of dependency injection patterns
- Architecture documentation and migration completion
- Production readiness validation

**Slice Breakdown**:
- **P6.1**: Comprehensive Architecture Validation (detection system validation)
- **P6.2**: Performance Optimization and Production Readiness

## Implementation Timeline

**Total Duration**: 13 days + 1 day buffer = 14 days

**Days 1-2**: ✅ Phase 1 - Context Infrastructure Foundation (COMPLETED)
**Days 3-4**: ✅ Phase 2 - CLI Integration and Command Migration (COMPLETED)
**Days 5-6**: 🚧 Phase 3 - Detection Infrastructure and Prevention (IN PROGRESS)
**Days 7-9**: 📋 Phase 4 - Core Service Singleton Elimination (PLANNED)
**Days 10-13**: 📋 Phase 5 - Comprehensive Singleton Elimination (PLANNED)
**Day 14**: 📋 Phase 6 - Architecture Validation and Performance Optimization (PLANNED)

## Slice Constraint Validation

### P0-ABSOLUTE Compliance
All phases and slices comply with ultra-focused agent constraints:

**File Constraints**: Each slice affects ≤3 files maximum
**Class Constraints**: Each slice creates/modifies ≤2 classes maximum
**Complexity Constraints**: Each slice maintains ≤7 McCabe complexity per function
**Independence**: Each slice is independently implementable and testable

### Detection-Driven Implementation
**Systematic Approach**: Use singleton detection system to identify all violations
**Priority-Based**: Address high-impact violations first (core services, then infrastructure)
**Validation-Driven**: Verify elimination with detection system after each phase
**Zero-Tolerance**: Achieve complete singleton elimination, not partial migration

## Success Metrics by Phase

### Phase 1-2 Success Metrics ✅ ACHIEVED
- SpecContext creation: <1ms for CLI contexts, <10ms for test contexts ✅
- Memory usage: <100KB per context instance ✅
- Context injection success: 100% for all decorated commands ✅
- CLI performance: No regression in startup or execution times ✅

### Phase 3 Success Metrics 🚧 IN PROGRESS
- Detection system accuracy: 100% singleton pattern identification ✅
- Violation detection: 484+ patterns correctly identified ✅
- Pre-commit integration: Prevent singleton reintroduction 🚧
- Test fixture analysis: Complete migration requirements 📋

### Phase 4-5 Success Metrics 📋 TARGET
- Core service migration: 100% of 58 critical violations eliminated
- Application migration: 100% of 180+ internal singleton patterns eliminated
- Test infrastructure migration: 100% of 95+ test singleton patterns eliminated
- External isolation: 100% of 128+ third-party singleton patterns isolated

### Phase 6 Final Success Metrics 📋 TARGET
- **Singleton elimination**: 100% singleton pattern removal (0/484 violations)
- **Test success rate**: 100% (eliminating all systematic failures)
- **Detection validation**: Zero singleton patterns detected by automated system
- **Concurrent support**: Multiple CLI processes work independently
- **Architecture quality**: Clean dependency graphs throughout

## Automated Detection Integration

### Continuous Validation
- **Pre-commit hooks**: Prevent singleton pattern reintroduction
- **CI/CD integration**: Automated detection in pull requests
- **Regression prevention**: Block commits containing singleton patterns
- **Progress tracking**: Monitor violation count reduction over time

### Detection System Capabilities
- **AST-based analysis**: Comprehensive Python code analysis
- **Pattern recognition**: Metaclass, decorator, and import-based singletons
- **Violation reporting**: File paths, line numbers, pattern types, code snippets
- **Integration ready**: CI-friendly output formats and exit codes

## Risk Mitigation

### Technical Risks
- **Migration Complexity**: Mitigated through detection-driven systematic approach
- **Performance Impact**: Mitigated through context reuse and optimization
- **Test Reliability**: Mitigated through context-based fixture migration
- **Architecture Consistency**: Mitigated through comprehensive validation

### Business Risks
- **Development Velocity**: Mitigated through incremental migration and validation
- **User Experience**: Mitigated through transparent migration with no interface changes
- **Production Stability**: Mitigated through extensive testing and rollback capability

## Quality Assurance

### Detection-Driven Quality Gates
- **Pre-Implementation**: Detection system validation, violation count baseline
- **Implementation**: Real-time violation reduction tracking
- **Post-Implementation**: Zero violation validation, architecture compliance
- **Continuous**: Automated prevention of singleton pattern reintroduction

### Testing Strategy
- **Unit Testing**: 95% code coverage, 90% branch coverage maintained
- **Integration Testing**: 100% CLI command integration validation
- **Singleton Detection**: 100% pattern elimination validation
- **Performance Testing**: No regression in CLI performance
- **Regression Testing**: Complete functionality preservation

## Current Status Summary

### ✅ Completed Infrastructure (Phases 1-2)
- Core dependency injection framework established
- CLI commands migrated to context-based patterns
- Backward compatibility maintained
- Foundation ready for systematic singleton elimination

### ✅ Detection System Deployed (Phase 3 Partial)
- **484+ singleton violations identified** across entire codebase
- Automated detection system operational
- Clear roadmap for systematic elimination established
- Prevention infrastructure partially deployed

### 📋 Systematic Elimination Required (Phases 4-6)
- **58 critical core service violations** requiring immediate attention
- **426 additional violations** across application and test infrastructure
- **Complete architectural transformation** needed for production readiness
- **Zero-tolerance validation** required for migration completion

---

*This updated phase decomposition provides a detection-driven systematic approach to complete singleton elimination, addressing all 484+ identified violations while maintaining full backward compatibility and user transparency.*
