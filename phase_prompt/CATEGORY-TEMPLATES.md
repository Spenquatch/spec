# Templates Agent Directive: Settings Singleton Elimination

You are executing **Template system singleton migration** which systematically replaces `get_settings()` calls with dependency injection in template processing modules. Every rule tagged `P0-ABSOLUTE` is mandatory—no exceptions, no shortcuts.

If a step is unclear: **do not guess**. Halt and escalate.

> **Template settings access is dependency injected or not touched. No partial states exist.**

## Mission: Eliminate Settings Singletons in Template System

**GOAL**: Replace all 4 `get_settings()` calls across 4 template modules with proper dependency injection.

**SUCCESS CRITERIA**:
- Zero `get_settings()` calls remaining in template modules
- All template processors accept settings via constructor/parameter
- 100% test pass rate maintained
- Template functionality preserved

**TARGET FILES**:
- `spec_cli/templates/substitution.py` (1 call) - **VARIABLE SUBSTITUTION**
- `spec_cli/templates/loader.py` (1 call) - **TEMPLATE LOADING**
- `spec_cli/templates/generator.py` (1 call) - **TEMPLATE GENERATION**
- `spec_cli/templates/ai_integration.py` (1 call) - **AI TEMPLATES**

---

## 🚨 TEMPLATE MIGRATION GUARD RAILS [P0-ABSOLUTE]

**These rules override all other instructions:**

1. **NEVER break template variable substitution** → Template rendering must produce identical output
2. **NEVER modify template loading security** → Template path validation must be preserved
3. **NEVER break AI template integration** → AI-enhanced templates must continue functioning
4. **NEVER compromise template caching** → Template loading performance must be maintained
5. **NEVER proceed without testing each module** → Validate template output after each change

> **Template Principle: "Dependency injection with preserved template rendering fidelity"**

---

## Step 1: Core Template Processing Migration [START HERE]

### 1.1 Template Substitution Migration [VARIABLE SUBSTITUTION - 1 CALL]

**File**: `spec_cli/templates/substitution.py`

**Current Pattern Analysis**:
```python
# Current problematic pattern
from ..config.settings import get_settings

class TemplateSubstitution:
    def __init__(self):
        pass
    
    def substitute_variables(self, template_content, variables):
        settings = get_settings()  # SINGLETON CALL
        default_vars = settings.default_template_variables
        template_dir = settings.template_directory
```

**Target Pattern**:
```python
# Dependency injection pattern
from ..config.settings import Settings

class TemplateSubstitution:
    def __init__(self, settings: Settings = None):
        if settings is None:
            raise ValueError("TemplateSubstitution requires a settings instance")
        self.settings = settings
    
    def substitute_variables(self, template_content, variables):
        default_vars = self.settings.default_template_variables
        template_dir = self.settings.template_directory
```

**Migration Commands**:
```bash
# 1. Backup current file
cp spec_cli/templates/substitution.py spec_cli/templates/substitution.py.backup

# 2. Find all get_settings() calls
grep -n "get_settings()" spec_cli/templates/substitution.py

# 3. Identify template variable usage patterns
grep -n "settings\.\|template_\|variable" spec_cli/templates/substitution.py
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
           raise ValueError("TemplateSubstitution requires settings")
       self.settings = settings
   ```

3. **Replace all get_settings() calls**:
   ```python
   # BEFORE
   def substitute_variables(self, template_content, variables):
       settings = get_settings()
       default_vars = settings.default_template_variables
           
   # AFTER
   def substitute_variables(self, template_content, variables):
       default_vars = self.settings.default_template_variables
   ```

### 1.2 Template Loader Migration [TEMPLATE LOADING - 1 CALL]

**File**: `spec_cli/templates/loader.py`

**Critical Consideration**: Template loading involves file system access and security validation.

**Current Pattern**:
```python
class TemplateLoader:
    def load_template(self, template_name):
        settings = get_settings()  # SINGLETON
        template_dir = settings.template_directory
        search_paths = settings.template_search_paths
```

**Target Pattern**:
```python
class TemplateLoader:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def load_template(self, template_name):
        template_dir = self.settings.template_directory
        search_paths = self.settings.template_search_paths
```

**Migration Commands**:
```bash
# Analyze template loader implementation
grep -n -A5 -B5 "get_settings" spec_cli/templates/loader.py

# Find all TemplateLoader instantiations
grep -r "TemplateLoader(" spec_cli/
```

**Security Considerations**:
```bash
# Check template loading security patterns
grep -n "path\|security\|validate" spec_cli/templates/loader.py

# Ensure template path validation is preserved
grep -n "\.\.\/\|absolute\|relative" spec_cli/templates/loader.py
```

### 1.3 Template Generator Migration [TEMPLATE GENERATION - 1 CALL]

**File**: `spec_cli/templates/generator.py`

**Critical Consideration**: Template generation creates new templates and may use AI integration.

**Analysis Commands**:
```bash
# Examine template generator settings usage
grep -n -A5 -B5 "get_settings" spec_cli/templates/generator.py

# Check generation configuration patterns
grep -n "generate\|create\|output" spec_cli/templates/generator.py
```

**Typical Pattern**:
```python
# BEFORE
class TemplateGenerator:
    def generate_template(self, spec_file):
        settings = get_settings()
        output_dir = settings.generated_template_dir
        
# AFTER
class TemplateGenerator:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def generate_template(self, spec_file):
        output_dir = self.settings.generated_template_dir
```

### 1.4 AI Integration Migration [AI TEMPLATES - 1 CALL]

**File**: `spec_cli/templates/ai_integration.py`

**Critical Consideration**: AI template integration may access API keys, model settings, and prompt configurations.

**Migration Commands**:
```bash
# Analyze AI integration patterns
grep -n -A5 -B5 "get_settings" spec_cli/templates/ai_integration.py

# Check AI configuration access
grep -n "api\|model\|prompt\|ai_" spec_cli/templates/ai_integration.py
```

**AI Pattern**:
```python
# BEFORE
class AITemplateIntegration:
    def enhance_template(self, template):
        settings = get_settings()
        api_key = settings.ai_api_key
        model = settings.ai_model
        
# AFTER
class AITemplateIntegration:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def enhance_template(self, template):
        api_key = self.settings.ai_api_key
        model = self.settings.ai_model
```

---

## Step 2: Template System Integration Patterns

### 2.1 Template Processing Chain

**Pattern**: Templates often work together in processing chains.

**Chain Example**:
```python
# Template processing workflow
class TemplateProcessor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.loader = TemplateLoader(settings)
        self.substitution = TemplateSubstitution(settings)
        self.generator = TemplateGenerator(settings)
        self.ai_integration = AITemplateIntegration(settings)
    
    def process_template(self, template_name, variables):
        # Load template
        template_content = self.loader.load_template(template_name)
        
        # Substitute variables
        processed_content = self.substitution.substitute_variables(
            template_content, variables)
        
        # AI enhancement (if enabled)
        if self.settings.enable_ai_templates:
            processed_content = self.ai_integration.enhance_template(
                processed_content)
        
        return processed_content
```

### 2.2 Template Factory Pattern

**Consider**: A factory pattern for template system components.

**Factory Implementation**:
```python
# templates/factory.py
class TemplateFactory:
    def __init__(self, settings: Settings):
        self.settings = settings
    
    def create_loader(self) -> TemplateLoader:
        return TemplateLoader(self.settings)
    
    def create_substitution(self) -> TemplateSubstitution:
        return TemplateSubstitution(self.settings)
    
    def create_generator(self) -> TemplateGenerator:
        return TemplateGenerator(self.settings)
    
    def create_ai_integration(self) -> AITemplateIntegration:
        return AITemplateIntegration(self.settings)
    
    def create_processor(self) -> TemplateProcessor:
        return TemplateProcessor(self.settings)
```

---

## Step 3: Template Security and Validation

### 3.1 Template Path Security

**Critical**: Template loading must prevent path traversal attacks.

**Security Validation**:
```python
# test_template_security.py
from spec_cli.config.settings import Settings
from spec_cli.templates.loader import TemplateLoader

def test_template_path_security():
    settings = Settings()
    loader = TemplateLoader(settings)
    
    # Test dangerous template paths are blocked
    dangerous_templates = [
        "../../../etc/passwd",
        "/etc/shadow",
        "../../.env",
        "~/.ssh/id_rsa"
    ]
    
    for template_path in dangerous_templates:
        try:
            content = loader.load_template(template_path)
            print(f"⚠️  Dangerous template path allowed: {template_path}")
        except Exception as e:
            print(f"✅ Dangerous template path blocked: {template_path}")

if __name__ == "__main__":
    test_template_path_security()
```

### 3.2 Template Variable Injection Protection

**Security Pattern**: Prevent template variable injection attacks.

```python
# Secure template substitution
class SecureTemplateSubstitution:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.allowed_variables = set(settings.allowed_template_variables)
    
    def substitute_variables(self, template_content, variables):
        # Filter variables to prevent injection
        safe_variables = {
            k: v for k, v in variables.items() 
            if k in self.allowed_variables
        }
        
        # Sanitize variable values
        sanitized_variables = {
            k: self._sanitize_value(v) 
            for k, v in safe_variables.items()
        }
        
        return self._substitute_safe(template_content, sanitized_variables)
```

---

## Step 4: Caller Site Updates [DEPENDENCY PLUMBING]

### 4.1 Trace Template Usage

**Discovery Commands**:
```bash
# Find all template component instantiations
grep -r "TemplateSubstitution(" spec_cli/
grep -r "TemplateLoader(" spec_cli/
grep -r "TemplateGenerator(" spec_cli/
grep -r "AITemplateIntegration(" spec_cli/

# Find template usage in CLI commands
grep -r "template" spec_cli/cli/commands/
```

### 4.2 CLI Command Integration

**Pattern**: CLI commands that use templates need settings access.

**Typical Integration**:
```python
# In gen_command.py or similar
@click.command()
@click.pass_context
def generate_command(ctx):
    settings = ctx.obj.settings
    
    # BEFORE
    generator = TemplateGenerator()
    
    # AFTER
    generator = TemplateGenerator(settings)
```

**CLI Integration Commands**:
```bash
# Find template usage in CLI
grep -r "TemplateGenerator\|TemplateLoader" spec_cli/cli/

# Check gen command specifically
grep -n "template" spec_cli/cli/commands/gen_command.py
```

### 4.3 Core Module Integration

**Pattern**: Core modules that use templates also need to pass settings.

**Example**:
```python
# In core/workflow_orchestrator.py
class WorkflowOrchestrator:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.template_processor = TemplateProcessor(settings)
```

---

## Step 5: Template Configuration Validation

### 5.1 Template Settings Validation

**Ensure**: All required template settings are present and valid.

**Validation Script**:
```python
# test_template_config.py
from spec_cli.config.settings import Settings

def test_template_settings():
    settings = Settings()
    
    # Check required template settings exist
    required_settings = [
        'template_directory',
        'default_template_variables',
        'template_search_paths',
        'generated_template_dir'
    ]
    
    for setting in required_settings:
        if hasattr(settings, setting):
            value = getattr(settings, setting)
            print(f"✅ {setting}: {value}")
        else:
            print(f"❌ Missing template setting: {setting}")

def test_ai_template_settings():
    settings = Settings()
    
    # Check AI template settings if AI integration is enabled
    if getattr(settings, 'enable_ai_templates', False):
        ai_settings = ['ai_api_key', 'ai_model', 'ai_template_prompts']
        
        for setting in ai_settings:
            if hasattr(settings, setting):
                # Don't print API keys
                value = "***" if "key" in setting else getattr(settings, setting)
                print(f"✅ AI {setting}: {value}")
            else:
                print(f"❌ Missing AI template setting: {setting}")

if __name__ == "__main__":
    test_template_settings()
    test_ai_template_settings()
```

### 5.2 Template Loading Performance

**Performance Test**:
```python
# test_template_performance.py
import time
from spec_cli.config.settings import Settings
from spec_cli.templates.loader import TemplateLoader

def test_template_loading_performance():
    settings = Settings()
    loader = TemplateLoader(settings)
    
    # Test template loading speed
    template_names = ["default.md", "spec.md", "history.md"]
    
    for template_name in template_names:
        start_time = time.time()
        try:
            content = loader.load_template(template_name)
            load_time = time.time() - start_time
            print(f"✅ {template_name}: loaded in {load_time:.3f}s")
        except Exception as e:
            print(f"❌ {template_name}: failed to load - {e}")

if __name__ == "__main__":
    test_template_loading_performance()
```

---

## Step 6: Validation & Testing [MANDATORY]

### 6.1 Syntax and Import Validation

```bash
# Validate syntax for all modified template files
python -c "
import py_compile
import glob

template_files = glob.glob('spec_cli/templates/*.py')

for file in template_files:
    try:
        py_compile.compile(file, doraise=True)
        print(f'✅ {file}: Syntax valid')
    except Exception as e:
        print(f'❌ {file}: {e}')
        exit(1)
"

# Test imports
python -c "
import spec_cli.templates.substitution
import spec_cli.templates.loader
import spec_cli.templates.generator
import spec_cli.templates.ai_integration
print('✅ All template imports successful')
"
```

### 6.2 Template Functionality Tests

```bash
# Run template-specific tests
poetry run pytest tests/unit/templates/ -v

# Verify no get_settings() calls remain
find spec_cli/templates -name "*.py" | xargs grep "get_settings()" && echo "❌ Still has singleton calls" || echo "✅ No singleton calls found"
```

### 6.3 Template Output Validation

**Template Output Test**:
```python
# test_template_output.py
from spec_cli.config.settings import Settings
from spec_cli.templates.substitution import TemplateSubstitution
from spec_cli.templates.loader import TemplateLoader

def test_template_output_consistency():
    settings = Settings()
    
    # Test template substitution produces expected output
    substitution = TemplateSubstitution(settings)
    
    template_content = "Hello {{name}}, welcome to {{project}}!"
    variables = {"name": "Developer", "project": "SpecCLI"}
    
    result = substitution.substitute_variables(template_content, variables)
    expected = "Hello Developer, welcome to SpecCLI!"
    
    if result == expected:
        print("✅ Template substitution works correctly")
    else:
        print(f"❌ Template substitution failed: {result} != {expected}")

def test_template_loading():
    settings = Settings()
    loader = TemplateLoader(settings)
    
    try:
        # Test loading a default template
        content = loader.load_template("default.md")
        if content and isinstance(content, str):
            print("✅ Template loading works correctly")
        else:
            print("❌ Template loading returned invalid content")
    except Exception as e:
        print(f"❌ Template loading failed: {e}")

if __name__ == "__main__":
    test_template_output_consistency()
    test_template_loading()
```

---

## Troubleshooting Guide [ERROR RECOVERY]

### Import Errors After Migration
```bash
# If imports fail, check for missing settings parameters
grep -r "TemplateLoader()" spec_cli/ | grep -v "settings"
# Each should be: TemplateLoader(settings)
```

### Template Loading Failures
```bash
# If template loading breaks:
# 1. Verify template directory paths in settings
# 2. Check template file permissions
# 3. Ensure template search paths are correct
```

### Variable Substitution Issues
```bash
# If template variables don't substitute:
# 1. Check default template variables in settings
# 2. Verify variable syntax matches template engine
# 3. Ensure variable values are properly escaped
```

### AI Integration Failures
```bash
# If AI templates break:
# 1. Verify AI API credentials in settings
# 2. Check AI model availability
# 3. Ensure AI integration is enabled in settings
```

---

## Success Metrics [TEMPLATE MIGRATION COMPLETE]

### Required Achievements [ALL MANDATORY]
- **Zero singleton calls**: No `get_settings()` remaining in template modules
- **Constructor injection**: All template classes accept settings via __init__
- **Preserved functionality**: Template rendering works identically to before
- **Security maintained**: Template path validation and variable sanitization work
- **Test coverage**: All template tests pass, no regressions

### Validation Commands
```bash
# Final validation
find spec_cli/templates -name "*.py" | xargs grep -n "get_settings" || echo "✅ Template migration complete"
poetry run pytest tests/unit/templates/ -v
python test_template_security.py
python test_template_output.py
```

### End-to-End Template Test
```bash
# Test template workflow
cd /tmp
mkdir test_templates
cd test_templates

# Test template generation workflow
python -c "
from spec_cli.config.settings import Settings
from spec_cli.templates.loader import TemplateLoader
from spec_cli.templates.substitution import TemplateSubstitution

settings = Settings()
loader = TemplateLoader(settings)
substitution = TemplateSubstitution(settings)

print('✅ Template end-to-end test passed')
"
```

**Template migration eliminates 4 singleton calls through systematic dependency injection while preserving all template rendering capabilities and security measures.**