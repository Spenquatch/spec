# Core Modules Agent Directive: Settings Singleton Elimination

You are executing **Core module singleton migration** which systematically replaces `get_settings()` calls with dependency injection in core business logic. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts.

If a step is unclear: **do not guess**. Halt and escalate.

> **Core settings access is dependency injected or not touched. No partial states exist.**

## Mission: Eliminate Settings Singletons in Core Layer

**GOAL**: Replace all 12 `get_settings()` calls across 7 core module files with proper dependency injection.

**SUCCESS CRITERIA**:
- Zero `get_settings()` calls remaining in core modules
- All core managers accept settings via constructor/parameter
- 100% test pass rate maintained
- Core business logic functionality preserved

**TARGET FILES**:
- `spec_cli/core/workflow_orchestrator.py` (2 calls) - **WORKFLOW CRITICAL**
- `spec_cli/core/repository_state.py` (2 calls) - **STATE MANAGEMENT**
- `spec_cli/core/repository_init.py` (2 calls) - **INITIALIZATION**
- `spec_cli/core/commit_manager.py` (2 calls) - **GIT OPERATIONS**
- `spec_cli/core/context_bridge.py` (2 calls) - **BRIDGE LOGIC**
- `spec_cli/core/context.py` (1 call) - **CONTEXT SETUP**
- `spec_cli/git/repository.py` (1 call) - **GIT INTERFACE**

---

## 🚨 CORE MIGRATION GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions:**

1. **NEVER break core business logic** → Settings-dependent behavior must remain identical
2. **NEVER modify settings interface contracts** → Preserve existing settings API usage
3. **NEVER inject settings into static methods** → Convert to instance methods first
4. **NEVER break workflow orchestration** → Core workflows must continue functioning
5. **NEVER proceed without testing each file** → Validate core functionality after each change

> **Core Principle: "Dependency injection with preserved business logic behavior"**

---

## Step 1: Workflow-Critical File Migration [START HERE]

### 1.1 Workflow Orchestrator Migration [CRITICAL - 2 CALLS]

**File**: `spec_cli/core/workflow_orchestrator.py`

**Current Pattern Analysis**:
```python
# Current problematic pattern
from ..config.settings import get_settings

class WorkflowOrchestrator:
    def __init__(self):
        pass
    
    def execute_workflow(self):
        settings = get_settings()  # SINGLETON CALL
        if settings.debug_mode:
            # workflow logic
```

**Target Pattern**:
```python
# Dependency injection pattern
from ..config.settings import Settings

class WorkflowOrchestrator:
    def __init__(self, settings: Settings = None):
        if settings is None:
            raise ValueError("WorkflowOrchestrator requires a settings instance")
        self.settings = settings
    
    def execute_workflow(self):
        if self.settings.debug_mode:  # Use injected settings
            # workflow logic
```

**Migration Commands**:
```bash
# 1. Backup current file
cp spec_cli/core/workflow_orchestrator.py spec_cli/core/workflow_orchestrator.py.backup

# 2. Find all get_settings() calls
grep -n "get_settings()" spec_cli/core/workflow_orchestrator.py

# 3. Identify class structure and dependencies
grep -n "class\|def \|import.*settings" spec_cli/core/workflow_orchestrator.py
```

**Transformation Steps**:

1. **Remove singleton import**:
   ```python
   # REMOVE
   from ..config.settings import get_settings
   
   # ADD (if not present)
   from ..config.settings import Settings
   ```

2. **Modify class constructor**:
   ```python
   # BEFORE
   def __init__(self):
       # No settings parameter
   
   # AFTER  
   def __init__(self, settings: Settings = None):
       if settings is None:
           raise ValueError("WorkflowOrchestrator requires settings")
       self.settings = settings
   ```

3. **Replace all get_settings() calls**:
   ```python
   # BEFORE
   def some_method(self):
       settings = get_settings()
       if settings.some_config:
           
   # AFTER
   def some_method(self):
       if self.settings.some_config:
   ```

### 1.2 Repository State Migration [STATE CRITICAL - 2 CALLS]

**File**: `spec_cli/core/repository_state.py`

**Critical Consideration**: Repository state manages git repository configuration and paths.

**Current Pattern**:
```python
class RepositoryState:
    def get_spec_dir(self):
        settings = get_settings()  # SINGLETON
        return settings.spec_directory
```

**Target Pattern**:
```python
class RepositoryState:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def get_spec_dir(self):
        return self.settings.spec_directory
```

**Migration Commands**:
```bash
# Analyze repository state implementation
grep -n -A5 -B5 "get_settings" spec_cli/core/repository_state.py

# Find all RepositoryState instantiations
grep -r "RepositoryState(" spec_cli/
```

### 1.3 Repository Init Migration [INIT CRITICAL - 2 CALLS]

**File**: `spec_cli/core/repository_init.py`

**Critical Consideration**: Repository initialization creates the .spec directory structure.

**Current Pattern**:
```python
class RepositoryInit:
    def initialize(self):
        settings = get_settings()  # SINGLETON
        spec_dir = settings.spec_directory
```

**Target Pattern**:
```python
class RepositoryInit:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def initialize(self):
        spec_dir = self.settings.spec_directory
```

### 1.4 Commit Manager Migration [GIT CRITICAL - 2 CALLS]

**File**: `spec_cli/core/commit_manager.py`

**Critical Consideration**: Manages git commits with spec repository settings.

**Migration Commands**:
```bash
# Analyze commit manager patterns
grep -n -A5 -B5 "get_settings" spec_cli/core/commit_manager.py

# Find commit manager usage
grep -r "CommitManager(" spec_cli/
```

---

## Step 2: Bridge and Context Migration

### 2.1 Context Bridge Migration [BRIDGE LOGIC - 2 CALLS]

**File**: `spec_cli/core/context_bridge.py`

**Special Consideration**: This is the facade bridge that may be providing the get_settings() function itself.

**Analysis Commands**:
```bash
# Examine bridge implementation carefully
grep -n -A10 -B10 "get_settings" spec_cli/core/context_bridge.py

# Check if this file DEFINES get_settings
grep -n "def get_settings" spec_cli/core/context_bridge.py
```

**Potential Pattern**:
```python
# If context_bridge provides get_settings facade:
def get_settings():
    return _original_get_settings()  # INTERNAL CALL

# May need different approach - could be the facade implementation
```

### 2.2 Context Module Migration [CONTEXT SETUP - 1 CALL]

**File**: `spec_cli/core/context.py`

**Simple Pattern**:
```python
# BEFORE
def setup_context():
    settings = get_settings()
    
# AFTER
def setup_context(settings: Settings):
    # Use settings parameter
```

---

## Step 3: Git Interface Migration

### 3.1 Git Repository Migration [GIT INTERFACE - 1 CALL]

**File**: `spec_cli/git/repository.py`

**Analysis Commands**:
```bash
# Examine git repository settings usage
grep -n -A5 -B5 "get_settings" spec_cli/git/repository.py

# Check git repository class structure
grep -n "class.*Repository\|def " spec_cli/git/repository.py
```

**Typical Pattern**:
```python
# BEFORE
class GitRepository:
    def get_repo_path(self):
        settings = get_settings()
        return settings.git_repository_path
        
# AFTER
class GitRepository:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def get_repo_path(self):
        return self.settings.git_repository_path
```

---

## Step 4: Caller Site Updates [DEPENDENCY PLUMBING]

### 4.1 Trace Core Component Usage

**Critical**: After modifying core classes to require settings injection, ALL instantiation sites must be updated.

**Discovery Commands**:
```bash
# Find all core component instantiations
grep -r "WorkflowOrchestrator(" spec_cli/
grep -r "RepositoryState(" spec_cli/
grep -r "RepositoryInit(" spec_cli/
grep -r "CommitManager(" spec_cli/

# Trace back to CLI command entry points
grep -r "from.*core.*import" spec_cli/cli/
```

### 4.2 CLI Command Integration

**Pattern**: CLI commands need settings access to pass to core components.

**Typical Integration**:
```python
# In CLI command file
@click.command()
@click.pass_context
def some_command(ctx):
    settings = ctx.obj.settings  # Or however settings is accessed
    
    # BEFORE
    orchestrator = WorkflowOrchestrator()
    
    # AFTER
    orchestrator = WorkflowOrchestrator(settings)
```

**Integration Commands**:
```bash
# Find CLI context patterns for settings
grep -r "settings.*=" spec_cli/cli/

# Find settings access patterns
grep -r "get_settings\|Settings" spec_cli/cli/
```

### 4.3 Core-to-Core Dependencies

**Complex Case**: Core modules that depend on other core modules.

**Example**:
```python
# If WorkflowOrchestrator uses RepositoryState:
class WorkflowOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.repo_state = RepositoryState(settings)  # Pass settings down
```

**Dependency Mapping Commands**:
```bash
# Map core module interdependencies
grep -r "from.*core.*import" spec_cli/core/

# Create dependency graph
python -c "
import ast
import glob

for file in glob.glob('spec_cli/core/*.py'):
    with open(file) as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and 'core' in str(node.module):
            print(f'{file} imports from {node.module}')
"
```

---

## Step 5: Special Cases and Edge Conditions

### 5.1 Static Methods and Utility Functions

**Problem**: Static methods and module-level functions can't easily receive injected dependencies.

**Solutions**:
```python
# OPTION 1: Convert static to instance method
# BEFORE
@staticmethod
def utility_method():
    settings = get_settings()

# AFTER  
def utility_method(self):
    # Use self.settings

# OPTION 2: Add parameter to function
# BEFORE
def module_function():
    settings = get_settings()
    
# AFTER
def module_function(settings: Settings):
    # Use settings parameter
```

### 5.2 Factory Methods and Builders

**Pattern**: Factory methods that create core objects.

```python
# Factory method pattern
class CoreFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def create_orchestrator(self) -> WorkflowOrchestrator:
        return WorkflowOrchestrator(self.settings)
    
    def create_commit_manager(self) -> CommitManager:
        return CommitManager(self.settings)
```

### 5.3 Lazy Initialization

**Problem**: Some core components may use lazy initialization with singletons.

**Solution**:
```python
# BEFORE (lazy singleton)
class SomeManager:
    def get_settings_when_needed(self):
        if not hasattr(self, '_settings'):
            self._settings = get_settings()
        return self._settings

# AFTER (eager injection)
class SomeManager:
    def __init__(self, settings: Settings):
        self.settings = settings
```

---

## Step 6: Validation & Testing [MANDATORY]

### 6.1 Syntax and Import Validation

```bash
# Validate syntax for all modified core files
python -c "
import py_compile
import glob

core_files = glob.glob('spec_cli/core/*.py') + ['spec_cli/git/repository.py']
for file in core_files:
    try:
        py_compile.compile(file, doraise=True)
        print(f'✅ {file}: Syntax valid')
    except Exception as e:
        print(f'❌ {file}: {e}')
        exit(1)
"

# Test imports
python -c "
import spec_cli.core.workflow_orchestrator
import spec_cli.core.repository_state
import spec_cli.core.commit_manager
print('✅ All core imports successful')
"
```

### 6.2 Core Functionality Tests

```bash
# Run core-specific tests
poetry run pytest tests/unit/core/ -v

# Run git repository tests
poetry run pytest tests/unit/git/ -v

# Verify no get_settings() calls remain in core modules
find spec_cli/core spec_cli/git/repository.py -name "*.py" | xargs grep "get_settings()" && echo "❌ Still has singleton calls" || echo "✅ No singleton calls found"
```

### 6.3 Integration Testing

**Test Script**:
```python
# test_core_injection.py
from spec_cli.config.settings import Settings
from spec_cli.core.workflow_orchestrator import WorkflowOrchestrator
from spec_cli.core.repository_state import RepositoryState
from spec_cli.core.commit_manager import CommitManager

# Test dependency injection works
settings = Settings()  # Use appropriate settings constructor

try:
    orchestrator = WorkflowOrchestrator(settings)
    repo_state = RepositoryState(settings)
    commit_manager = CommitManager(settings)
    print("✅ All core components accept settings injection")
except Exception as e:
    print(f"❌ Core injection failed: {e}")
    exit(1)
```

### 6.4 Business Logic Validation

```bash
# Test that core workflows still function
poetry run pytest tests/ -k "workflow" -v
poetry run pytest tests/ -k "commit" -v
poetry run pytest tests/ -k "repository" -v

# Run end-to-end CLI tests to ensure core logic works
poetry run pytest tests/integration/ -v
```

---

## Troubleshooting Guide [ERROR RECOVERY]

### Import Errors After Migration
```bash
# If imports fail, check for missing settings parameters
grep -r "WorkflowOrchestrator()" spec_cli/ | grep -v "settings"
# Each should be: WorkflowOrchestrator(settings)
```

### Business Logic Breaks
```bash
# If core functionality breaks:
# 1. Verify settings object has required attributes
# 2. Check settings values match expected types
# 3. Ensure no settings mutations were lost in migration
```

### Circular Dependencies
```bash
# If core modules have circular dependencies:
# 1. Consider dependency inversion
# 2. Extract shared interfaces
# 3. Use factory pattern to break cycles
```

### Context Bridge Issues
```bash
# If context bridge breaks:
# 1. May need to preserve get_settings() in bridge temporarily
# 2. Migrate internal bridge implementation separately
# 3. Ensure bridge facade still works for non-migrated code
```

---

## Success Metrics [CORE MIGRATION COMPLETE]

### Required Achievements [ALL MANDATORY]
- **Zero singleton calls**: No `get_settings()` remaining in core modules
- **Constructor injection**: All core classes accept settings via __init__
- **Preserved functionality**: Core business logic works identically to before
- **Test coverage**: All core tests pass, no regressions
- **Clean imports**: No hanging singleton import statements

### Validation Commands
```bash
# Final validation
find spec_cli/core spec_cli/git/repository.py -name "*.py" | xargs grep -n "get_settings" || echo "✅ Core migration complete"
poetry run pytest tests/unit/core/ tests/unit/git/ -v
python -c "from spec_cli.core.workflow_orchestrator import WorkflowOrchestrator; from spec_cli.config.settings import Settings; WorkflowOrchestrator(Settings())"
```

**Core module migration eliminates 12 singleton calls through systematic dependency injection while preserving all business logic and workflow functionality.**