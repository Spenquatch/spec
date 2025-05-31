# Slice 8: Template Generation and Content Substitution

## Goal

Create a robust template generation engine that performs variable substitution, generates index.md and history.md files, and provides extension points for AI content injection.

## Context

Building on the template configuration system from slice-7, this slice implements the actual content generation and substitution engine. It creates the core functionality that will be used by both cmd_gen and future git hooks to generate consistent documentation. The system includes placeholder substitution, content generation, and clear extension points for AI integration.

## Scope

**Included in this slice:**
- TemplateSubstitution engine for variable replacement
- SpecContentGenerator for creating documentation files
- Variable preparation and context building
- File writing with proper encoding and error handling
- Extension points for AI content injection (interfaces defined)

**NOT included in this slice:**
- AI content generation implementation (extension points only)
- Conflict resolution for existing files (comes in PHASE-4)
- User interface for generation progress (comes in PHASE-5)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for template errors)
- `spec_cli.logging.debug` (debug_logger for generation tracking)
- `spec_cli.config.settings` (SpecSettings for file operations)
- `spec_cli.file_system.directory_manager` (DirectoryManager for directory creation)
- `spec_cli.templates.config` (TemplateConfig and validation)
- `spec_cli.templates.loader` (TemplateLoader for template loading)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3-configuration
- `DirectoryManager` from slice-6-directory-management
- `TemplateConfig`, `TemplateValidator` from slice-7-template-config
- `TemplateLoader`, `load_template()` from slice-7-template-config

## Files to Create

```
spec_cli/templates/
├── substitution.py         # TemplateSubstitution engine
├── generator.py            # SpecContentGenerator class
└── ai_integration.py       # AI integration interfaces (extension points)
```

## Implementation Steps

### Step 1: Create spec_cli/templates/substitution.py

```python
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, Set, List, Callable
from ..exceptions import SpecTemplateError
from ..logging.debug import debug_logger

class TemplateSubstitution:
    """Handles variable substitution in template content."""
    
    def __init__(self):
        # Pattern for finding template variables
        self.variable_pattern = re.compile(r'\{\{(\w+)\}\}')
        
        # Built-in variable generators
        self.builtin_generators = {
            'date': self._generate_date,
            'datetime': self._generate_datetime,
            'timestamp': self._generate_timestamp,
        }
        
        debug_logger.log("INFO", "TemplateSubstitution initialized")
    
    def substitute(self, template: str, variables: Dict[str, Any]) -> str:
        """Substitute variables in template content.
        
        Args:
            template: Template content with {{variable}} placeholders
            variables: Dictionary of variable values
            
        Returns:
            Template content with variables substituted
            
        Raises:
            SpecTemplateError: If substitution fails
        """
        debug_logger.log("INFO", "Performing template substitution", 
                        template_length=len(template),
                        variable_count=len(variables))
        
        try:
            # Find all variables in the template
            found_variables = set(self.variable_pattern.findall(template))
            debug_logger.log("DEBUG", "Found template variables", 
                           variables=sorted(found_variables))
            
            # Prepare complete variable context
            substitution_context = self._prepare_substitution_context(variables, found_variables)
            
            # Perform substitution
            result = template
            substitutions_made = 0
            
            for variable_name in found_variables:
                placeholder = f"{{{{{variable_name}}}}}"
                
                if variable_name in substitution_context:
                    value = str(substitution_context[variable_name])
                    result = result.replace(placeholder, value)
                    substitutions_made += 1
                    debug_logger.log("DEBUG", "Substituted variable", 
                                   variable=variable_name, 
                                   value_length=len(value))
                else:
                    # Leave unresolved variables as placeholders
                    debug_logger.log("WARNING", "Unresolved template variable", 
                                   variable=variable_name)
            
            debug_logger.log("INFO", "Template substitution complete", 
                           substitutions_made=substitutions_made,
                           result_length=len(result))
            
            return result
            
        except Exception as e:
            error_msg = f"Template substitution failed: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e
    
    def _prepare_substitution_context(self, variables: Dict[str, Any], found_variables: Set[str]) -> Dict[str, str]:
        """Prepare complete substitution context with built-in and provided variables.
        
        Args:
            variables: User-provided variables
            found_variables: Variables found in the template
            
        Returns:
            Complete substitution context
        """
        context = {}
        
        # Add user-provided variables
        for key, value in variables.items():
            context[key] = self._format_variable_value(value)
        
        # Generate built-in variables that are needed
        for variable_name in found_variables:
            if variable_name in self.builtin_generators and variable_name not in context:
                try:
                    generated_value = self.builtin_generators[variable_name]()
                    context[variable_name] = self._format_variable_value(generated_value)
                    debug_logger.log("DEBUG", "Generated built-in variable", 
                                   variable=variable_name, value=generated_value)
                except Exception as e:
                    debug_logger.log("WARNING", "Failed to generate built-in variable", 
                                   variable=variable_name, error=str(e))
        
        return context
    
    def _format_variable_value(self, value: Any) -> str:
        """Format a variable value for substitution."""
        if value is None:
            return "[To be filled]"
        elif isinstance(value, bool):
            return "Yes" if value else "No"
        elif isinstance(value, (list, tuple)):
            if not value:
                return "[None specified]"
            return "\n".join(f"- {item}" for item in value)
        elif isinstance(value, dict):
            if not value:
                return "[None specified]"
            return "\n".join(f"- **{key}**: {val}" for key, val in value.items())
        else:
            return str(value)
    
    def _generate_date(self) -> str:
        """Generate current date in YYYY-MM-DD format."""
        return datetime.now().strftime("%Y-%m-%d")
    
    def _generate_datetime(self) -> str:
        """Generate current datetime in ISO format."""
        return datetime.now().isoformat()
    
    def _generate_timestamp(self) -> str:
        """Generate current Unix timestamp."""
        return str(int(datetime.now().timestamp()))
    
    def get_variables_in_template(self, template: str) -> Set[str]:
        """Extract all variable names from a template.
        
        Args:
            template: Template content to analyze
            
        Returns:
            Set of variable names found in template
        """
        return set(self.variable_pattern.findall(template))
    
    def validate_template_syntax(self, template: str) -> List[str]:
        """Validate template syntax and return issues.
        
        Args:
            template: Template content to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Check for unmatched braces
        open_singles = template.count('{') - template.count('{{') * 2
        close_singles = template.count('}') - template.count('}}') * 2
        
        if open_singles > 0:
            issues.append(f"Found {open_singles} unmatched opening braces {{")
        if close_singles > 0:
            issues.append(f"Found {close_singles} unmatched closing braces }}")
        
        # Check for malformed variables
        malformed = re.findall(r'{[^{].*?[^}]}|{[^{][^}]*}', template)
        if malformed:
            issues.append(f"Found malformed variables: {malformed}")
        
        return issues
    
    def preview_substitution(self, template: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Preview what substitution would produce without actually doing it.
        
        Args:
            template: Template content
            variables: Variables for substitution
            
        Returns:
            Dictionary with preview information
        """
        found_variables = self.get_variables_in_template(template)
        context = self._prepare_substitution_context(variables, found_variables)
        
        preview = {
            "template_length": len(template),
            "variables_found": sorted(found_variables),
            "variables_provided": sorted(variables.keys()),
            "variables_resolved": sorted([v for v in found_variables if v in context]),
            "variables_unresolved": sorted([v for v in found_variables if v not in context]),
            "substitution_context": {k: v[:50] + "..." if len(v) > 50 else v for k, v in context.items()},
        }
        
        return preview
```

### Step 2: Create spec_cli/templates/ai_integration.py

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
from ..exceptions import SpecTemplateError

class AIContentProvider(ABC):
    """Abstract interface for AI content generation."""
    
    @abstractmethod
    def generate_content(self, 
                        file_path: Path, 
                        context: Dict[str, Any],
                        content_type: str,
                        max_tokens: int = 1000) -> str:
        """Generate content for a specific context.
        
        Args:
            file_path: Path to the file being documented
            context: Context information about the file
            content_type: Type of content to generate (e.g., 'purpose', 'overview')
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated content string
            
        Raises:
            SpecTemplateError: If content generation fails
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if AI provider is available and configured."""
        pass
    
    @abstractmethod
    def get_supported_content_types(self) -> List[str]:
        """Get list of supported content types."""
        pass

class PlaceholderAIProvider(AIContentProvider):
    """Placeholder AI provider that generates template placeholders."""
    
    def generate_content(self, 
                        file_path: Path, 
                        context: Dict[str, Any],
                        content_type: str,
                        max_tokens: int = 1000) -> str:
        """Generate placeholder content."""
        return f"[AI-generated {content_type} for {file_path.name} - to be implemented]"
    
    def is_available(self) -> bool:
        """Placeholder provider is always available."""
        return True
    
    def get_supported_content_types(self) -> List[str]:
        """Return all common content types."""
        return [
            "purpose", "overview", "responsibilities", "dependencies",
            "api_interface", "example_usage", "configuration", 
            "error_handling", "testing_notes", "performance_notes",
            "security_notes", "future_enhancements", "related_docs", "notes"
        ]

class AIContentManager:
    """Manages AI content generation with fallback strategies."""
    
    def __init__(self):
        self.providers: Dict[str, AIContentProvider] = {}
        self.default_provider = PlaceholderAIProvider()
        self.enabled = False
    
    def register_provider(self, name: str, provider: AIContentProvider) -> None:
        """Register an AI content provider.
        
        Args:
            name: Name of the provider
            provider: AIContentProvider instance
        """
        self.providers[name] = provider
    
    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable AI content generation."""
        self.enabled = enabled
    
    def generate_ai_content(self, 
                           file_path: Path,
                           context: Dict[str, Any],
                           content_requests: List[str]) -> Dict[str, str]:
        """Generate AI content for multiple content types.
        
        Args:
            file_path: Path to the file being documented
            context: Context information
            content_requests: List of content types to generate
            
        Returns:
            Dictionary mapping content types to generated content
        """
        if not self.enabled:
            return {content_type: f"[{content_type} - AI disabled]" for content_type in content_requests}
        
        # Find available provider
        provider = self._get_available_provider()
        
        results = {}
        for content_type in content_requests:
            try:
                content = provider.generate_content(file_path, context, content_type)
                results[content_type] = content
            except Exception as e:
                # Fallback to placeholder
                results[content_type] = f"[Error generating {content_type}: {e}]"
        
        return results
    
    def _get_available_provider(self) -> AIContentProvider:
        """Get the first available AI provider or fallback to placeholder."""
        for provider in self.providers.values():
            if provider.is_available():
                return provider
        
        return self.default_provider

# Global AI content manager instance
ai_content_manager = AIContentManager()
```

### Step 3: Create spec_cli/templates/generator.py

```python
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from .config import TemplateConfig
from .substitution import TemplateSubstitution
from .ai_integration import ai_content_manager, AIContentManager
from ..config.settings import get_settings, SpecSettings
from ..file_system.directory_manager import DirectoryManager
from ..file_system.file_analyzer import FileAnalyzer
from ..exceptions import SpecTemplateError
from ..logging.debug import debug_logger

class SpecContentGenerator:
    """Generates spec content files using template substitution and optional AI."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.substitution = TemplateSubstitution()
        self.directory_manager = DirectoryManager(self.settings)
        self.file_analyzer = FileAnalyzer(self.settings)
        self.ai_manager = ai_content_manager
        
        debug_logger.log("INFO", "SpecContentGenerator initialized")
    
    def generate_spec_content(self,
                            file_path: Path,
                            spec_dir: Path,
                            template: TemplateConfig,
                            custom_variables: Optional[Dict[str, Any]] = None,
                            ai_enabled: bool = False) -> None:
        """Generate spec content files using template substitution.
        
        Args:
            file_path: Path to source file (relative to project root)
            spec_dir: Directory where spec files will be created
            template: Template configuration to use
            custom_variables: Optional custom variables for substitution
            ai_enabled: Whether to use AI for content generation
            
        Raises:
            SpecTemplateError: If content generation fails
        """
        debug_logger.log("INFO", "Generating spec content", 
                        source_file=str(file_path),
                        spec_dir=str(spec_dir),
                        ai_enabled=ai_enabled)
        
        try:
            with debug_logger.timer("generate_spec_content"):
                # Prepare substitution variables
                substitutions = self._prepare_substitutions(
                    file_path, custom_variables or {}, template, ai_enabled
                )
                
                # Ensure spec directory exists
                self.directory_manager.create_spec_directory(file_path)
                
                # Generate index.md content
                with debug_logger.timer("generate_index_content"):
                    index_content = self.substitution.substitute(template.index, substitutions)
                    index_file = spec_dir / "index.md"
                    self._write_content_file(index_file, index_content)
                
                # Generate history.md content
                with debug_logger.timer("generate_history_content"):
                    history_content = self.substitution.substitute(template.history, substitutions)
                    history_file = spec_dir / "history.md"
                    self._write_content_file(history_file, history_content)
                
                debug_logger.log("INFO", "Spec content generation complete",
                                source_file=str(file_path),
                                index_length=len(index_content),
                                history_length=len(history_content))
                
        except Exception as e:
            error_msg = f"Failed to generate spec content for {file_path}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e
    
    def _prepare_substitutions(self,
                             file_path: Path,
                             custom_variables: Dict[str, Any],
                             template: TemplateConfig,
                             ai_enabled: bool) -> Dict[str, str]:
        """Prepare complete substitution variables.
        
        Args:
            file_path: Path to the source file
            custom_variables: Custom variables provided by user
            template: Template configuration
            ai_enabled: Whether AI content generation is enabled
            
        Returns:
            Complete substitution context
        """
        debug_logger.log("DEBUG", "Preparing substitution variables",
                        file_path=str(file_path),
                        custom_count=len(custom_variables),
                        ai_enabled=ai_enabled)
        
        # Base file information
        substitutions = self._get_file_based_variables(file_path)
        
        # Add custom variables (override base variables)
        substitutions.update(custom_variables)
        
        # Generate AI content if enabled
        if ai_enabled and template.ai_enabled:
            ai_content = self._generate_ai_content(file_path, substitutions, template)
            substitutions.update(ai_content)
        else:
            # Use placeholder content for AI fields
            ai_placeholders = self._get_ai_placeholder_content(template)
            substitutions.update(ai_placeholders)
        
        debug_logger.log("DEBUG", "Substitution variables prepared",
                        total_variables=len(substitutions),
                        ai_generated=ai_enabled and template.ai_enabled)
        
        return substitutions
    
    def _get_file_based_variables(self, file_path: Path) -> Dict[str, str]:
        """Get variables based on file information.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            Dictionary of file-based variables
        """
        try:
            # Get file metadata
            file_metadata = self.file_analyzer.get_file_metadata(file_path)
            
            # Basic file information
            variables = {
                "filename": file_path.name,
                "filepath": str(file_path),
                "file_extension": file_path.suffix.lstrip(".") or "txt",
                "file_type": file_metadata.get("file_type", "unknown"),
            }
            
            # Add file size information if available
            if "size" in file_metadata:
                size_mb = file_metadata["size"] / (1024 * 1024)
                variables["file_size"] = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{file_metadata['size']} bytes"
            
            debug_logger.log("DEBUG", "File-based variables extracted",
                           filename=variables["filename"],
                           file_type=variables["file_type"])
            
            return variables
            
        except Exception as e:
            debug_logger.log("WARNING", "Could not extract file metadata",
                           file_path=str(file_path), error=str(e))
            # Return minimal variables
            return {
                "filename": file_path.name,
                "filepath": str(file_path),
                "file_extension": file_path.suffix.lstrip(".") or "txt",
                "file_type": "unknown",
            }
    
    def _generate_ai_content(self,
                           file_path: Path,
                           context: Dict[str, str],
                           template: TemplateConfig) -> Dict[str, str]:
        """Generate AI content for template variables.
        
        Args:
            file_path: Path to the source file
            context: Current substitution context
            template: Template configuration
            
        Returns:
            Dictionary of AI-generated content
        """
        debug_logger.log("INFO", "Generating AI content",
                        file_path=str(file_path),
                        ai_model=template.ai_model)
        
        # Enable AI content manager
        self.ai_manager.set_enabled(True)
        
        # Determine which content types to generate
        all_variables = template.get_placeholders_in_templates()
        ai_content_types = [
            var for var in all_variables 
            if var in self._get_ai_content_types() and var not in context
        ]
        
        if not ai_content_types:
            debug_logger.log("INFO", "No AI content types needed")
            return {}
        
        try:
            # Prepare context for AI
            ai_context = {
                "file_path": str(file_path),
                "file_type": context.get("file_type", "unknown"),
                "file_extension": context.get("file_extension", ""),
                "filename": context.get("filename", ""),
            }
            
            # Generate AI content
            ai_content = self.ai_manager.generate_ai_content(
                file_path, ai_context, ai_content_types
            )
            
            debug_logger.log("INFO", "AI content generated",
                           content_types=len(ai_content),
                           types=list(ai_content.keys()))
            
            return ai_content
            
        except Exception as e:
            debug_logger.log("WARNING", "AI content generation failed",
                           error=str(e))
            # Return placeholders for failed AI generation
            return {content_type: f"[AI generation failed: {e}]" for content_type in ai_content_types}
    
    def _get_ai_placeholder_content(self, template: TemplateConfig) -> Dict[str, str]:
        """Get placeholder content for AI-generated fields.
        
        Args:
            template: Template configuration
            
        Returns:
            Dictionary of placeholder content
        """
        all_variables = template.get_placeholders_in_templates()
        ai_content_types = [var for var in all_variables if var in self._get_ai_content_types()]
        
        placeholders = {}
        for content_type in ai_content_types:
            placeholders[content_type] = f"[{content_type.replace('_', ' ').title()} - to be filled]"
        
        return placeholders
    
    def _get_ai_content_types(self) -> List[str]:
        """Get list of content types that can be AI-generated."""
        return [
            "purpose", "overview", "responsibilities", "dependencies",
            "api_interface", "example_usage", "configuration",
            "error_handling", "testing_notes", "performance_notes",
            "security_notes", "future_enhancements", "related_docs", "notes",
            "context", "initial_purpose", "decisions", "implementation_notes"
        ]
    
    def _write_content_file(self, file_path: Path, content: str) -> None:
        """Write content to a file with proper encoding and error handling.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Raises:
            SpecTemplateError: If file writing fails
        """
        try:
            with file_path.open("w", encoding="utf-8") as f:
                f.write(content)
            
            debug_logger.log("DEBUG", "Content file written",
                           file_path=str(file_path),
                           content_length=len(content))
            
        except OSError as e:
            error_msg = f"Failed to write content to {file_path}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e
    
    def preview_generation(self,
                         file_path: Path,
                         template: TemplateConfig,
                         custom_variables: Optional[Dict[str, Any]] = None,
                         ai_enabled: bool = False) -> Dict[str, Any]:
        """Preview what content generation would produce.
        
        Args:
            file_path: Path to source file
            template: Template configuration
            custom_variables: Optional custom variables
            ai_enabled: Whether AI would be enabled
            
        Returns:
            Dictionary with preview information
        """
        substitutions = self._prepare_substitutions(
            file_path, custom_variables or {}, template, ai_enabled
        )
        
        preview = {
            "file_path": str(file_path),
            "substitution_variables": len(substitutions),
            "ai_enabled": ai_enabled,
            "template_variables": {
                "index": sorted(self.substitution.get_variables_in_template(template.index)),
                "history": sorted(self.substitution.get_variables_in_template(template.history)),
            },
            "substitution_preview": {
                k: v[:100] + "..." if len(v) > 100 else v 
                for k, v in substitutions.items()
            }
        }
        
        return preview

# Convenience function for backward compatibility
def generate_spec_content(file_path: Path, spec_dir: Path, template: TemplateConfig) -> None:
    """Generate spec content (backward compatibility function).
    
    Args:
        file_path: Path to source file
        spec_dir: Directory for spec files
        template: Template configuration
    """
    generator = SpecContentGenerator()
    generator.generate_spec_content(file_path, spec_dir, template)
```

### Step 4: Update spec_cli/templates/__init__.py

```python
"""Template system for spec CLI.

This package provides template configuration, loading, and content generation
for creating consistent documentation across different contexts.
"""

from .config import TemplateConfig, TemplateValidator
from .loader import TemplateLoader, load_template
from .defaults import get_default_template_config, get_template_preset
from .substitution import TemplateSubstitution
from .generator import SpecContentGenerator, generate_spec_content
from .ai_integration import AIContentProvider, ai_content_manager

__all__ = [
    "TemplateConfig",
    "TemplateValidator",
    "TemplateLoader",
    "load_template",
    "get_default_template_config",
    "get_template_preset", 
    "TemplateSubstitution",
    "SpecContentGenerator",
    "generate_spec_content",
    "AIContentProvider",
    "ai_content_manager",
]
```

## Test Requirements

Create comprehensive tests for the template generation system:

### Test Cases (28 tests total)

**TemplateSubstitution Tests:**
1. **test_substitution_replaces_simple_variables**
2. **test_substitution_handles_missing_variables**
3. **test_substitution_generates_builtin_variables**
4. **test_substitution_formats_different_value_types**
5. **test_substitution_validates_template_syntax**
6. **test_substitution_previews_substitution_results**
7. **test_substitution_extracts_variables_from_template**
8. **test_substitution_handles_special_characters**

**AI Integration Tests:**
9. **test_placeholder_ai_provider_generates_content**
10. **test_ai_content_manager_registers_providers**
11. **test_ai_content_manager_handles_disabled_state**
12. **test_ai_content_manager_falls_back_on_errors**

**SpecContentGenerator Tests:**
13. **test_generator_creates_index_and_history_files**
14. **test_generator_uses_file_based_variables**
15. **test_generator_applies_custom_variables**
16. **test_generator_integrates_ai_content_when_enabled**
17. **test_generator_uses_placeholders_when_ai_disabled**
18. **test_generator_handles_file_writing_errors**
19. **test_generator_creates_spec_directories**
20. **test_generator_handles_missing_file_metadata**
21. **test_generator_previews_generation_results**

**Integration Tests:**
22. **test_generation_integrates_with_template_loader**
23. **test_generation_integrates_with_directory_manager**
24. **test_generation_handles_template_validation_errors**
25. **test_generation_preserves_custom_variable_precedence**
26. **test_generation_works_with_different_file_types**

**Backward Compatibility Tests:**
27. **test_generate_spec_content_function_works**
28. **test_template_system_maintains_api_compatibility**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/templates/test_substitution.py tests/unit/templates/test_generator.py tests/unit/templates/test_ai_integration.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/templates/ --cov=spec_cli.templates --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/templates/

# Check code formatting
poetry run ruff check spec_cli/templates/
poetry run ruff format spec_cli/templates/

# Verify imports work correctly
python -c "from spec_cli.templates import TemplateSubstitution, SpecContentGenerator, generate_spec_content; print('Import successful')"

# Test template substitution functionality
python -c "
from spec_cli.templates import TemplateSubstitution
from pathlib import Path

substitution = TemplateSubstitution()
template = 'Hello {{name}}, today is {{date}}. Your file is {{filename}}.'
variables = {'name': 'Developer', 'filename': 'test.py'}

result = substitution.substitute(template, variables)
print(f'Substitution result: {result}')

# Test variable extraction
found_vars = substitution.get_variables_in_template(template)
print(f'Variables found: {sorted(found_vars)}')

# Test preview
preview = substitution.preview_substitution(template, variables)
print(f'Preview: resolved={preview[\"variables_resolved\"]}, unresolved={preview[\"variables_unresolved\"]}')
"

# Test content generation
python -c "
from spec_cli.templates import SpecContentGenerator, load_template
from pathlib import Path

generator = SpecContentGenerator()
template = load_template()

# Test generation preview
test_file = Path('test_example.py')
preview = generator.preview_generation(test_file, template, ai_enabled=False)
print(f'Generation preview:')
print(f'  File: {preview[\"file_path\"]}')
print(f'  Variables: {preview[\"substitution_variables\"]}')
print(f'  Template vars: {len(preview[\"template_variables\"][\"index\"])} index, {len(preview[\"template_variables\"][\"history\"])} history')

# Show some substitution variables
print(f'Sample variables:')
for key, value in list(preview['substitution_preview'].items())[:5]:
    print(f'  {key}: {value[:50]}...' if len(value) > 50 else f'  {key}: {value}')
"

# Test AI integration interfaces
python -c "
from spec_cli.templates.ai_integration import PlaceholderAIProvider, ai_content_manager
from pathlib import Path

# Test placeholder provider
provider = PlaceholderAIProvider()
print(f'Placeholder provider available: {provider.is_available()}')
print(f'Supported content types: {len(provider.get_supported_content_types())}')

test_content = provider.generate_content(
    Path('test.py'), 
    {'file_type': 'python'}, 
    'purpose'
)
print(f'Generated content: {test_content}')

# Test AI manager
print(f'AI manager enabled: {ai_content_manager.enabled}')
ai_content_manager.set_enabled(True)
print(f'AI manager enabled after setting: {ai_content_manager.enabled}')
"

# Test file-based variables extraction
python -c "
from spec_cli.templates.generator import SpecContentGenerator
from pathlib import Path

generator = SpecContentGenerator()

# Test with a real file (use this script file)
test_file = Path('spec_cli/__main__.py')
if test_file.exists():
    try:
        variables = generator._get_file_based_variables(test_file)
        print(f'File-based variables for {test_file}:')
        for key, value in variables.items():
            print(f'  {key}: {value}')
    except Exception as e:
        print(f'Could not extract variables: {e}')
else:
    print('Test file not found, skipping file-based variable test')
"
```

## Definition of Done

- [ ] `TemplateSubstitution` engine with comprehensive variable replacement
- [ ] Built-in variable generators for dates and timestamps
- [ ] AI integration interfaces defined with placeholder provider
- [ ] `SpecContentGenerator` for creating index.md and history.md files
- [ ] File-based variable extraction from metadata
- [ ] Custom variable support with precedence handling
- [ ] AI content generation extension points (interfaces only)
- [ ] Content preview functionality for validation
- [ ] Proper file encoding and error handling
- [ ] All 28 test cases pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with all template system components
- [ ] Backward compatibility functions maintained

## Next Slice Preparation

This slice completes **PHASE-3** (Template System) by providing:
- Complete template generation engine for content creation
- Shared template system usable by both cmd_gen and future git hooks
- AI integration extension points for future enhancement
- Template substitution and content generation capabilities

This enables **PHASE-4** (Git and Core Logic) which will use the template system to generate documentation during file processing operations.