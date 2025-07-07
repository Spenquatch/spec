# Test Fixture Migration Requirements

## Analysis Summary

Based on comprehensive analysis of the existing test suite, the following migration requirements have been identified for converting singleton-dependent test fixtures to context-based dependency injection patterns.

## Critical Findings

### Baseline Status
- **54 critical errors** in test collection due to missing `spec_cli.utils.singleton` module
- **High priority migration required** to restore test suite functionality
- All errors stem from singleton infrastructure dependencies that have been removed

### Test Fixture Analysis Results

#### Singleton-Dependent Fixtures Identified

**Primary Singleton Access Patterns:**
- `get_settings()` - Direct singleton settings access
- `get_console()` - Direct singleton console access
- `reset_console()` - Singleton state manipulation
- `spec_console.` - Direct singleton instance usage
- `SpecSettings()` - Direct singleton class instantiation
- `@singleton` decorators and `SingletonMeta` metaclass usage

**Files Requiring Fixture Migration:**
- `tests/conftest.py` - Main configuration with autouse fixtures
- `tests/unit/utils/test_helpers/conftest.py` - Test helper fixtures
- All test files importing from singleton-dependent modules

#### Test Isolation Issues

**Current Isolation Mechanisms:**
1. `isolate_working_directory()` - Working directory restoration
2. `isolate_environment_variables()` - Environment variable cleanup
3. `clean_mock_state()` - Mock/patch state cleanup

**State Contamination Risks:**
- Global singleton state persisting between tests
- Environment variable modifications affecting subsequent tests
- Mock patches not properly cleaned up
- Module-level imports caching singleton instances

## Migration Requirements

### Phase 1: Context Fixture Infrastructure

**Required Context-Based Fixtures:**

```python
@pytest.fixture
def spec_context():
    """Primary dependency injection context for tests."""
    return SpecContext(
        settings=MockSpecSettings(),
        console=MockSpecConsole(),
        progress=MockProgressManager()
    )

@pytest.fixture
def mock_spec_settings():
    """Mock settings for test isolation."""
    return MockSpecSettings(
        root_path=Path("/test/root"),
        spec_dir=Path(".spec"),
        specs_dir=Path(".specs"),
        debug_enabled=False
    )

@pytest.fixture
def mock_spec_console():
    """Mock console for test isolation."""
    return MockSpecConsole()

@pytest.fixture
def isolated_test_context(tmp_path):
    """Fully isolated test context with temporary directories."""
    return SpecContext(
        settings=MockSpecSettings(root_path=tmp_path),
        console=MockSpecConsole(),
        progress=MockProgressManager()
    )
```

### Phase 2: Fixture Pattern Migration

**Migration Patterns Required:**

1. **Settings Access Migration**
   ```python
   # OLD: Singleton access
   def test_old_pattern():
       settings = get_settings()  # Fails - singleton removed

   # NEW: Context injection
   def test_new_pattern(spec_context):
       settings = spec_context.settings  # Context-based access
   ```

2. **Console Access Migration**
   ```python
   # OLD: Singleton access
   def test_old_console():
       console = get_console()  # Fails - singleton removed

   # NEW: Context injection
   def test_new_console(spec_context):
       console = spec_context.console  # Context-based access
   ```

3. **Command Testing Migration**
   ```python
   # OLD: Command with singleton dependencies
   def test_old_command():
       result = init_command(["--debug"])  # Fails - internal singleton access

   # NEW: Command with context injection
   def test_new_command(spec_context):
       result = init_command(["--debug"], context=spec_context)
   ```

### Phase 3: Test Helper Infrastructure Updates

**Test Helper Migration Requirements:**

1. **CLI Test Helpers**
   - Update `create_cli_command_runner()` to accept context
   - Modify `isolated_cli_environment()` to use context-based isolation
   - Replace singleton-dependent mock patterns

2. **Git Test Helpers**
   - Update `create_git_repository_mocker()` to use context settings
   - Modify `git_environment_isolator()` for context-based configuration

3. **Template Test Helpers**
   - Update `ai_template_mocker()` to use context settings
   - Modify `mock_template_environment()` for context injection

### Phase 4: Integration Test Updates

**Integration Test Migration Requirements:**

**Command Integration Tests:**
- `test_init_command_integration.py` - Replace `Mock(spec=SpecSettingsInterface)` with `spec_context.settings`
- `test_gen_command_migration.py` - Update mock settings/console to use context
- `test_add_command_migration.py` - Replace singleton elimination tests with context validation
- `test_commit_command_migration.py` - Update context injection validation

**CLI Integration Tests:**
- `test_cli_app_integration.py` - Replace singleton app creation with context-based app
- `test_context_injection_integration.py` - Update decorator tests for new context patterns

## Specific Migration Actions Required

### 1. Replace Autouse Fixtures in `tests/conftest.py`

**Current autouse fixtures need context integration:**
- `isolate_working_directory()` - Update to use context.settings.root_path
- `isolate_environment_variables()` - Integrate with context.settings
- `clean_mock_state()` - Add context mock cleanup

### 2. Update Test Helper Fixtures in `tests/unit/utils/test_helpers/conftest.py`

**All imported fixtures need context support:**
- AI test doubles → Accept context for settings
- CLI test helpers → Use context for command execution
- File system helpers → Use context.settings for path resolution
- Template helpers → Use context for template configuration
- Workflow helpers → Use context for state management

### 3. Migration Validation Requirements

**Each migrated fixture must:**
1. Accept `spec_context` parameter or create isolated context
2. Use `context.settings`, `context.console`, `context.progress` instead of singletons
3. Provide proper test isolation without global state
4. Support both unit and integration test patterns
5. Include proper cleanup mechanisms

### 4. Cross-Platform Compatibility

**Context-based fixtures must support:**
- Windows, macOS, Linux path handling via context.settings
- Environment variable isolation via context configuration
- Cross-platform test execution without singleton state leakage

## Implementation Validation

### Success Criteria

1. **Test Collection Success**: All 54 import errors resolved
2. **Fixture Isolation**: No test failures due to state contamination
3. **Context Integration**: All singleton access patterns replaced with context
4. **Backward Compatibility**: Existing test patterns work with context injection
5. **Performance**: No significant test execution time increase

### Validation Commands

```bash
# Test collection should succeed
poetry run pytest --collect-only

# All tests should pass with context fixtures
poetry run test

# No singleton patterns should remain in test code
rg "get_settings|get_console|reset_console" tests/ --type py
```

## Migration Priority

**Phase Priority:**
1. **CRITICAL**: Core context fixtures (`spec_context`, mock objects)
2. **HIGH**: Main conftest.py autouse fixture updates
3. **MEDIUM**: Test helper infrastructure updates
4. **LOW**: Integration test pattern updates

**Timeline Estimate:**
- Phase 1: 1 slice (context fixture creation)
- Phase 2: 2-3 slices (pattern migration)
- Phase 3: 2 slices (test helper updates)
- Phase 4: 1-2 slices (integration test updates)

This migration will restore full test suite functionality while establishing the foundation for maintainable, isolated, context-based testing patterns.
