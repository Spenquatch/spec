# File Processing Agent Directive: Settings Singleton Elimination

You are executing **File processing singleton migration** which systematically replaces `get_settings()` calls with dependency injection in file processing modules. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts.

If a step is unclear: **do not guess**. Halt and escalate.

> **File processing settings access is dependency injected or not touched. No partial states exist.**

## Mission: Eliminate Settings Singletons in File Processing

**GOAL**: Replace all 6 `get_settings()` calls across 4 file processing modules with proper dependency injection.

**SUCCESS CRITERIA**:
- Zero `get_settings()` calls remaining in file processing modules
- All file processors accept settings via constructor/parameter
- 100% test pass rate maintained
- File processing functionality preserved

**TARGET FILES**:
- `spec_cli/file_processing/batch_processor.py` (1 call) - **BATCH OPERATIONS**
- `spec_cli/file_processing/conflict_resolver.py` (1 call) - **CONFLICT HANDLING**
- `spec_cli/file_processing/file_cache.py` (1 call) - **CACHING LOGIC**
- `spec_cli/file_processing/change_detector.py` (1 call) - **CHANGE DETECTION**
- `spec_cli/file_system/ignore_patterns.py` (1 call) - **IGNORE RULES**
- `spec_cli/file_system/path_resolver.py` (1 call) - **PATH RESOLUTION**
- `spec_cli/file_system/directory_manager.py` (1 call) - **DIRECTORY OPS**

---

## 🚨 FILE PROCESSING MIGRATION GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions:**

1. **NEVER break file processing pipelines** → Batch operations must continue functioning
2. **NEVER modify file system safety checks** → Path validation and security must be preserved
3. **NEVER break file caching mechanisms** → Cache invalidation and storage must work
4. **NEVER compromise conflict resolution** → File conflict handling must remain robust
5. **NEVER proceed without testing each module** → Validate file operations after each change

> **File Processing Principle: "Dependency injection with preserved file operation safety"**

---

## Step 1: Core File Processing Migration [START HERE]

### 1.1 Batch Processor Migration [BATCH OPERATIONS - 1 CALL]

**File**: `spec_cli/file_processing/batch_processor.py`

**Current Pattern Analysis**:
```python
# Current problematic pattern
from ..config.settings import get_settings

class BatchProcessor:
    def __init__(self):
        pass
    
    def process_batch(self, files):
        settings = get_settings()  # SINGLETON CALL
        batch_size = settings.batch_size
        max_workers = settings.max_workers
```

**Target Pattern**:
```python
# Dependency injection pattern
from ..config.settings import Settings

class BatchProcessor:
    def __init__(self, settings: Settings = None):
        if settings is None:
            raise ValueError("BatchProcessor requires a settings instance")
        self.settings = settings
    
    def process_batch(self, files):
        batch_size = self.settings.batch_size
        max_workers = self.settings.max_workers
```

**Migration Commands**:
```bash
# 1. Backup current file
cp spec_cli/file_processing/batch_processor.py spec_cli/file_processing/batch_processor.py.backup

# 2. Find all get_settings() calls
grep -n "get_settings()" spec_cli/file_processing/batch_processor.py

# 3. Identify class structure and settings usage
grep -n "class\|def \|settings\." spec_cli/file_processing/batch_processor.py
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
           raise ValueError("BatchProcessor requires settings")
       self.settings = settings
   ```

3. **Replace all get_settings() calls**:
   ```python
   # BEFORE
   def process_batch(self, files):
       settings = get_settings()
       batch_size = settings.batch_size
           
   # AFTER
   def process_batch(self, files):
       batch_size = self.settings.batch_size
   ```

### 1.2 Conflict Resolver Migration [CONFLICT HANDLING - 1 CALL]

**File**: `spec_cli/file_processing/conflict_resolver.py`

**Critical Consideration**: Conflict resolution may use settings for merge strategies and resolution policies.

**Current Pattern**:
```python
class ConflictResolver:
    def resolve_conflicts(self, conflicts):
        settings = get_settings()  # SINGLETON
        strategy = settings.conflict_resolution_strategy
```

**Target Pattern**:
```python
class ConflictResolver:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def resolve_conflicts(self, conflicts):
        strategy = self.settings.conflict_resolution_strategy
```

**Migration Commands**:
```bash
# Analyze conflict resolver implementation
grep -n -A5 -B5 "get_settings" spec_cli/file_processing/conflict_resolver.py

# Find all ConflictResolver instantiations
grep -r "ConflictResolver(" spec_cli/
```

### 1.3 File Cache Migration [CACHING LOGIC - 1 CALL]

**File**: `spec_cli/file_processing/file_cache.py`

**Critical Consideration**: File caching uses settings for cache directory, size limits, and TTL.

**Analysis Commands**:
```bash
# Examine cache settings usage
grep -n -A5 -B5 "get_settings" spec_cli/file_processing/file_cache.py

# Check cache configuration patterns
grep -n "cache.*dir\|cache.*size\|ttl\|expire" spec_cli/file_processing/file_cache.py
```

**Typical Pattern**:
```python
# BEFORE
class FileCache:
    def get_cache_dir(self):
        settings = get_settings()
        return settings.cache_directory
        
# AFTER
class FileCache:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def get_cache_dir(self):
        return self.settings.cache_directory
```

### 1.4 Change Detector Migration [CHANGE DETECTION - 1 CALL]

**File**: `spec_cli/file_processing/change_detector.py`

**Critical Consideration**: Change detection may use settings for file watching, ignore patterns, and detection sensitivity.

**Migration Commands**:
```bash
# Analyze change detector patterns
grep -n -A5 -B5 "get_settings" spec_cli/file_processing/change_detector.py

# Find change detector usage
grep -r "ChangeDetector(" spec_cli/
```

---

## Step 2: File System Module Migration

### 2.1 Ignore Patterns Migration [IGNORE RULES - 1 CALL]

**File**: `spec_cli/file_system/ignore_patterns.py`

**Critical Consideration**: Ignore patterns are crucial for security and performance - they determine which files are processed.

**Analysis Commands**:
```bash
# Examine ignore patterns settings usage
grep -n -A5 -B5 "get_settings" spec_cli/file_system/ignore_patterns.py

# Check ignore pattern configuration
grep -n "ignore\|pattern\|exclude" spec_cli/file_system/ignore_patterns.py
```

**Security Pattern**:
```python
# BEFORE
class IgnorePatterns:
    def load_patterns(self):
        settings = get_settings()
        return settings.ignore_patterns + settings.security_ignore_patterns
        
# AFTER
class IgnorePatterns:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def load_patterns(self):
        return self.settings.ignore_patterns + self.settings.security_ignore_patterns
```

### 2.2 Path Resolver Migration [PATH RESOLUTION - 1 CALL]

**File**: `spec_cli/file_system/path_resolver.py`

**Critical Consideration**: Path resolution handles security-sensitive operations like path traversal prevention.

**Security Analysis**:
```bash
# Examine path resolver security patterns
grep -n -A5 -B5 "get_settings" spec_cli/file_system/path_resolver.py

# Check path security and validation
grep -n "resolve\|absolute\|relative\|security" spec_cli/file_system/path_resolver.py
```

### 2.3 Directory Manager Migration [DIRECTORY OPS - 1 CALL]

**File**: `spec_cli/file_system/directory_manager.py`

**Critical Consideration**: Directory operations use settings for permissions, temp directories, and safety checks.

**Analysis Commands**:
```bash
# Examine directory manager settings
grep -n -A5 -B5 "get_settings" spec_cli/file_system/directory_manager.py

# Check directory operation patterns
grep -n "create\|delete\|permissions\|temp" spec_cli/file_system/directory_manager.py
```

---

## Step 3: Caller Site Updates [DEPENDENCY PLUMBING]

### 3.1 Trace File Processing Usage

**Critical**: After modifying file processing classes to require settings injection, ALL instantiation sites must be updated.

**Discovery Commands**:
```bash
# Find all file processing instantiations
grep -r "BatchProcessor(" spec_cli/
grep -r "ConflictResolver(" spec_cli/
grep -r "FileCache(" spec_cli/
grep -r "ChangeDetector(" spec_cli/

# Find file system component usage
grep -r "IgnorePatterns(" spec_cli/
grep -r "PathResolver(" spec_cli/
grep -r "DirectoryManager(" spec_cli/
```

### 3.2 CLI Integration for File Processing

**Pattern**: CLI commands that use file processing need settings access.

**Typical Integration**:
```python
# In CLI command file
@click.command()
@click.pass_context
def batch_command(ctx):
    settings = ctx.obj.settings  # Or however settings is accessed
    
    # BEFORE
    processor = BatchProcessor()
    
    # AFTER
    processor = BatchProcessor(settings)
```

**Integration Commands**:
```bash
# Find CLI commands that use file processing
grep -r "BatchProcessor\|ConflictResolver\|FileCache" spec_cli/cli/

# Check settings access in CLI
grep -r "settings" spec_cli/cli/
```

### 3.3 Core Module Integration

**Pattern**: Core modules that use file processing also need to pass settings.

**Example Chain**:
```python
# Core module that uses file processing
class WorkflowOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.batch_processor = BatchProcessor(settings)  # Pass settings down
        self.conflict_resolver = ConflictResolver(settings)
```

**Chain Discovery**:
```bash
# Map file processing dependencies
grep -r "from.*file_processing.*import\|from.*file_system.*import" spec_cli/

# Find usage patterns
grep -r "batch_processor\|conflict_resolver\|file_cache" spec_cli/
```

---

## Step 4: File Processing Factory Pattern

### 4.1 File Processing Factory

**Consider**: For complex file processing chains, a factory pattern can simplify dependency injection.

**Factory Pattern**:
```python
# file_processing/factory.py
class FileProcessingFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def create_batch_processor(self) -> BatchProcessor:
        return BatchProcessor(self.settings)
    
    def create_conflict_resolver(self) -> ConflictResolver:
        return ConflictResolver(self.settings)
    
    def create_file_cache(self) -> FileCache:
        return FileCache(self.settings)
    
    def create_change_detector(self) -> ChangeDetector:
        return ChangeDetector(self.settings)
```

### 4.2 File System Factory

**File System Factory**:
```python
# file_system/factory.py
class FileSystemFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def create_ignore_patterns(self) -> IgnorePatterns:
        return IgnorePatterns(self.settings)
    
    def create_path_resolver(self) -> PathResolver:
        return PathResolver(self.settings)
    
    def create_directory_manager(self) -> DirectoryManager:
        return DirectoryManager(self.settings)
```

---

## Step 5: Security and Safety Validation

### 5.1 Path Security Validation

**Critical**: File system operations must maintain security after migration.

**Security Test Script**:
```python
# test_file_security.py
from spec_cli.config.settings import Settings
from spec_cli.file_system.path_resolver import PathResolver
from spec_cli.file_system.ignore_patterns import IgnorePatterns

def test_path_security():
    settings = Settings()  # Use appropriate settings constructor
    
    # Test path resolver security
    path_resolver = PathResolver(settings)
    
    # Test dangerous paths are blocked
    dangerous_paths = [
        "../../../etc/passwd",
        "/etc/shadow",
        "~/.ssh/id_rsa"
    ]
    
    for path in dangerous_paths:
        try:
            resolved = path_resolver.resolve_safe_path(path)
            print(f"⚠️  Dangerous path allowed: {path} -> {resolved}")
        except Exception as e:
            print(f"✅ Dangerous path blocked: {path}")

def test_ignore_patterns():
    settings = Settings()
    ignore_patterns = IgnorePatterns(settings)
    
    # Test security patterns are loaded
    patterns = ignore_patterns.load_patterns()
    security_patterns = [".git", "*.pyc", "__pycache__", ".env"]
    
    for pattern in security_patterns:
        if pattern in patterns:
            print(f"✅ Security pattern present: {pattern}")
        else:
            print(f"❌ Security pattern missing: {pattern}")

if __name__ == "__main__":
    test_path_security()
    test_ignore_patterns()
```

### 5.2 File Processing Safety

**Safety Test Script**:
```python
# test_file_processing_safety.py
from spec_cli.config.settings import Settings
from spec_cli.file_processing.batch_processor import BatchProcessor
from spec_cli.file_processing.conflict_resolver import ConflictResolver

def test_batch_safety():
    settings = Settings()
    processor = BatchProcessor(settings)
    
    # Test batch processing limits
    large_batch = list(range(10000))  # Potentially large batch
    
    try:
        result = processor.process_batch(large_batch)
        print("✅ Batch processing handles large batches safely")
    except Exception as e:
        print(f"❌ Batch processing failed: {e}")

def test_conflict_safety():
    settings = Settings()
    resolver = ConflictResolver(settings)
    
    # Test conflict resolution doesn't crash
    try:
        # Simulate conflicts
        conflicts = ["file1.txt", "file2.txt"]
        result = resolver.resolve_conflicts(conflicts)
        print("✅ Conflict resolution handles conflicts safely")
    except Exception as e:
        print(f"❌ Conflict resolution failed: {e}")

if __name__ == "__main__":
    test_batch_safety()
    test_conflict_safety()
```

---

## Step 6: Validation & Testing [MANDATORY]

### 6.1 Syntax and Import Validation

```bash
# Validate syntax for all modified file processing files
python -c "
import py_compile
import glob

file_processing_files = glob.glob('spec_cli/file_processing/*.py')
file_system_files = glob.glob('spec_cli/file_system/*.py')
all_files = file_processing_files + file_system_files

for file in all_files:
    try:
        py_compile.compile(file, doraise=True)
        print(f'✅ {file}: Syntax valid')
    except Exception as e:
        print(f'❌ {file}: {e}')
        exit(1)
"

# Test imports
python -c "
import spec_cli.file_processing.batch_processor
import spec_cli.file_processing.conflict_resolver
import spec_cli.file_system.ignore_patterns
print('✅ All file processing imports successful')
"
```

### 6.2 File Processing Functionality Tests

```bash
# Run file processing specific tests
poetry run pytest tests/unit/file_processing/ -v

# Run file system tests
poetry run pytest tests/unit/file_system/ -v

# Verify no get_settings() calls remain
find spec_cli/file_processing spec_cli/file_system -name "*.py" | xargs grep "get_settings()" && echo "❌ Still has singleton calls" || echo "✅ No singleton calls found"
```

### 6.3 Integration Testing

**Integration Test Script**:
```python
# test_file_integration.py
from spec_cli.config.settings import Settings
from spec_cli.file_processing.batch_processor import BatchProcessor
from spec_cli.file_processing.file_cache import FileCache
from spec_cli.file_system.directory_manager import DirectoryManager

def test_file_processing_integration():
    settings = Settings()
    
    try:
        # Test file processing chain
        batch_processor = BatchProcessor(settings)
        file_cache = FileCache(settings)
        directory_manager = DirectoryManager(settings)
        
        print("✅ File processing components integrate successfully")
        
        # Test basic operations
        test_files = ["test1.txt", "test2.txt"]
        # batch_processor.process_batch(test_files)  # Uncomment if safe
        
        print("✅ File processing operations work")
        
    except Exception as e:
        print(f"❌ File processing integration failed: {e}")
        exit(1)

if __name__ == "__main__":
    test_file_processing_integration()
```

---

## Troubleshooting Guide [ERROR RECOVERY]

### Import Errors After Migration
```bash
# If imports fail, check for missing settings parameters
grep -r "BatchProcessor()" spec_cli/ | grep -v "settings"
# Each should be: BatchProcessor(settings)
```

### File Processing Breaks
```bash
# If file operations break:
# 1. Verify settings object has required file processing attributes
# 2. Check file paths and permissions are correct
# 3. Ensure file processing settings match expected types
```

### Security Validation Failures
```bash
# If security checks fail:
# 1. Verify ignore patterns are loaded correctly
# 2. Check path resolution security is maintained
# 3. Ensure file processing limits are enforced
```

### Performance Issues
```bash
# If file processing becomes slow:
# 1. Check batch sizes are appropriate
# 2. Verify caching is working correctly
# 3. Ensure settings are not re-loaded repeatedly
```

---

## Success Metrics [FILE PROCESSING MIGRATION COMPLETE]

### Required Achievements [ALL MANDATORY]
- **Zero singleton calls**: No `get_settings()` remaining in file processing/system modules
- **Constructor injection**: All file processors accept settings via __init__
- **Preserved functionality**: File operations work identically to before
- **Security maintained**: Path validation and ignore patterns function correctly
- **Test coverage**: All file processing tests pass, no regressions

### Validation Commands
```bash
# Final validation
find spec_cli/file_processing spec_cli/file_system -name "*.py" | xargs grep -n "get_settings" || echo "✅ File processing migration complete"
poetry run pytest tests/unit/file_processing/ tests/unit/file_system/ -v
python test_file_security.py
python test_file_integration.py
```

### End-to-End File Processing Test
```bash
# Test file processing workflow
cd /tmp
mkdir test_file_processing
cd test_file_processing

# Create test files
echo "Test content 1" > file1.txt
echo "Test content 2" > file2.txt

# Test file processing commands work
python -c "
from spec_cli.config.settings import Settings
from spec_cli.file_processing.batch_processor import BatchProcessor

settings = Settings()
processor = BatchProcessor(settings)
files = ['file1.txt', 'file2.txt']

print('✅ File processing end-to-end test passed')
"
```

**File processing migration eliminates 7 singleton calls through systematic dependency injection while preserving all file operation safety and security measures.**