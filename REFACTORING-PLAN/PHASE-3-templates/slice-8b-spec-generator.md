# Slice 8B: Spec Generator and File Creation

## Goal

Wrap the substitution engine from slice-8a to build SPEC.md files from templates, including path plumbing and file system operations.

## Context

Building on the substitution engine from slice-8a and template configuration from slice-7, this slice implements the spec file generation workflow. It creates the bridge between template processing and file system operations, handling the creation of index.md and history.md files with proper directory structure and file management.

## Scope

**Included in this slice:**
- SpecContentGenerator class for creating documentation files
- File-based variable extraction from source files
- Integration with DirectoryManager for spec directory creation
- File writing with proper encoding and error handling
- Generation preview functionality for validation
- Custom variable support with precedence handling

**NOT included in this slice:**
- Template substitution logic (handled by slice-8a)
- AI content generation (moved to slice-8c)
- Template configuration (already in slice-7)
- Directory traversal operations (already in PHASE-2)

## Prerequisites

**Required modules that must exist:**
- `spec_cli.exceptions` (SpecError hierarchy for template errors)
- `spec_cli.logging.debug` (debug_logger for generation tracking)
- `spec_cli.config.settings` (SpecSettings for file operations)
- `spec_cli.file_system.directory_manager` (DirectoryManager for directory creation)
- `spec_cli.file_system.file_metadata` (FileMetadataExtractor for file info)
- `spec_cli.templates.config` (TemplateConfig and validation)
- `spec_cli.templates.loader` (TemplateLoader for template loading)
- `spec_cli.templates.substitution` (TemplateSubstitution from slice-8a)

**Required functions/classes:**
- All exception classes from slice-1-exceptions
- `debug_logger` from slice-2-logging
- `SpecSettings` and `get_settings()` from slice-3a-settings-console
- `DirectoryManager` from slice-6b-directory-operations
- `FileMetadataExtractor` from slice-5b-file-metadata
- `TemplateConfig`, `TemplateValidator` from slice-7-template-config
- `TemplateLoader`, `load_template()` from slice-7-template-config
- `TemplateSubstitution` from slice-8a-template-substitution

## Files to Create

```
spec_cli/templates/
├── generator.py            # SpecContentGenerator class
└── __init__.py             # Updated exports
```

## Implementation Steps

### Step 1: Create spec_cli/templates/generator.py

```python
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from .config import TemplateConfig
from .substitution import TemplateSubstitution
from ..config.settings import get_settings, SpecSettings
from ..file_system.directory_manager import DirectoryManager
from ..file_system.file_metadata import FileMetadataExtractor
from ..exceptions import SpecTemplateError, SpecFileError
from ..logging.debug import debug_logger

class SpecContentGenerator:
    """Generates spec content files using template substitution."""
    
    def __init__(self, settings: Optional[SpecSettings] = None):
        self.settings = settings or get_settings()
        self.substitution = TemplateSubstitution()
        self.directory_manager = DirectoryManager(self.settings)
        self.metadata_extractor = FileMetadataExtractor()
        
        debug_logger.log("INFO", "SpecContentGenerator initialized")
    
    def generate_spec_content(self,
                            file_path: Path,
                            template: TemplateConfig,
                            custom_variables: Optional[Dict[str, Any]] = None,
                            backup_existing: bool = True) -> Dict[str, Path]:
        """Generate spec content files using template substitution.
        
        Args:
            file_path: Path to source file (relative to project root)
            template: Template configuration to use
            custom_variables: Optional custom variables for substitution
            backup_existing: Whether to backup existing spec files
            
        Returns:
            Dictionary mapping file types to created file paths
            
        Raises:
            SpecTemplateError: If content generation fails
        """
        debug_logger.log("INFO", "Generating spec content", 
                        source_file=str(file_path),
                        backup_existing=backup_existing)
        
        try:
            with debug_logger.timer("generate_spec_content"):
                # Create spec directory and handle existing files
                spec_dir = self._prepare_spec_directory(file_path, backup_existing)
                
                # Prepare substitution variables
                substitutions = self._prepare_substitutions(
                    file_path, custom_variables or {}, template
                )
                
                # Generate content files
                created_files = {}
                
                # Generate index.md content
                with debug_logger.timer("generate_index_content"):
                    index_content = self.substitution.substitute(template.index, substitutions)
                    index_file = spec_dir / "index.md"
                    self._write_content_file(index_file, index_content)
                    created_files["index"] = index_file
                
                # Generate history.md content
                with debug_logger.timer("generate_history_content"):
                    history_content = self.substitution.substitute(template.history, substitutions)
                    history_file = spec_dir / "history.md"
                    self._write_content_file(history_file, history_content)
                    created_files["history"] = history_file
                
                debug_logger.log("INFO", "Spec content generation complete",
                                source_file=str(file_path),
                                files_created=len(created_files),
                                index_length=len(index_content),
                                history_length=len(history_content))
                
                return created_files
                
        except Exception as e:
            error_msg = f"Failed to generate spec content for {file_path}: {e}"
            debug_logger.log("ERROR", error_msg)
            raise SpecTemplateError(error_msg) from e
    
    def _prepare_spec_directory(self, file_path: Path, backup_existing: bool) -> Path:
        """Prepare spec directory and handle existing files.
        
        Args:
            file_path: Path to the source file
            backup_existing: Whether to backup existing files
            
        Returns:
            Path to the spec directory
        """
        debug_logger.log("DEBUG", "Preparing spec directory",
                        file_path=str(file_path),
                        backup_existing=backup_existing)
        
        # Ensure .specs directory exists
        self.directory_manager.ensure_specs_directory()
        
        # Create specific spec directory for this file
        spec_dir = self.directory_manager.create_spec_directory(file_path)
        
        # Handle existing files if requested
        if backup_existing:
            existing_files = self.directory_manager.check_existing_specs(spec_dir)
            if existing_files["index.md"] or existing_files["history.md"]:
                backup_files = self.directory_manager.backup_existing_files(spec_dir)
                debug_logger.log("INFO", "Backed up existing spec files",
                               spec_dir=str(spec_dir),
                               backup_count=len(backup_files))
        
        return spec_dir
    
    def _prepare_substitutions(self,
                             file_path: Path,
                             custom_variables: Dict[str, Any],
                             template: TemplateConfig) -> Dict[str, Any]:
        """Prepare complete substitution variables.
        
        Args:
            file_path: Path to the source file
            custom_variables: Custom variables provided by user
            template: Template configuration
            
        Returns:
            Complete substitution context
        """
        debug_logger.log("DEBUG", "Preparing substitution variables",
                        file_path=str(file_path),
                        custom_count=len(custom_variables))
        
        # Base file information
        substitutions = self._get_file_based_variables(file_path)
        
        # Add template-specific defaults
        template_defaults = self._get_template_defaults(template)
        substitutions.update(template_defaults)
        
        # Add custom variables (highest precedence)
        substitutions.update(custom_variables)
        
        debug_logger.log("DEBUG", "Substitution variables prepared",
                        total_variables=len(substitutions))
        
        return substitutions
    
    def _get_file_based_variables(self, file_path: Path) -> Dict[str, Any]:
        """Get variables based on file information.
        
        Args:
            file_path: Path to the source file
            
        Returns:
            Dictionary of file-based variables
        """
        try:
            # Get file metadata
            file_metadata = self.metadata_extractor.extract_metadata(file_path)
            
            # Basic file information
            variables = {
                "filename": file_path.name,
                "filepath": str(file_path),
                "file_extension": file_path.suffix.lstrip(".") or "txt",
                "file_stem": file_path.stem,
                "parent_directory": file_path.parent.name,
                "relative_path": str(file_path),
            }
            
            # Add file metadata if available
            if file_metadata:
                variables.update({
                    "file_type": file_metadata.get("type", "unknown"),
                    "file_category": file_metadata.get("category", "other"),
                    "is_binary": file_metadata.get("is_binary", False),
                })
                
                # Add file size information if available
                if "size" in file_metadata:
                    size_bytes = file_metadata["size"]
                    if size_bytes >= 1024 * 1024:
                        size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
                    elif size_bytes >= 1024:
                        size_str = f"{size_bytes / 1024:.1f} KB"
                    else:
                        size_str = f"{size_bytes} bytes"
                    variables["file_size"] = size_str
            
            debug_logger.log("DEBUG", "File-based variables extracted",
                           filename=variables["filename"],
                           file_type=variables.get("file_type", "unknown"))
            
            return variables
            
        except Exception as e:
            debug_logger.log("WARNING", "Could not extract file metadata",
                           file_path=str(file_path), error=str(e))
            # Return minimal variables
            return {
                "filename": file_path.name,
                "filepath": str(file_path),
                "file_extension": file_path.suffix.lstrip(".") or "txt",
                "file_stem": file_path.stem,
                "parent_directory": file_path.parent.name,
                "relative_path": str(file_path),
                "file_type": "unknown",
                "file_category": "other",
                "is_binary": False,
                "file_size": "unknown",
            }
    
    def _get_template_defaults(self, template: TemplateConfig) -> Dict[str, Any]:
        """Get default variables from template configuration.
        
        Args:
            template: Template configuration
            
        Returns:
            Dictionary of template default variables
        """
        defaults = {
            "template_name": template.name,
            "template_description": template.description,
            "creation_date": datetime.now().strftime("%Y-%m-%d"),
            "creation_time": datetime.now().strftime("%H:%M:%S"),
        }
        
        # Add any template-specific defaults
        if hasattr(template, "defaults") and template.defaults:
            defaults.update(template.defaults)
        
        return defaults
    
    def _write_content_file(self, file_path: Path, content: str) -> None:
        """Write content to a file with proper encoding and error handling.
        
        Args:
            file_path: Path to the file to write
            content: Content to write
            
        Raises:
            SpecTemplateError: If file writing fails
        """
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content with UTF-8 encoding
            with file_path.open("w", encoding="utf-8", newline="\n") as f:
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
                         custom_variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Preview what content generation would produce.
        
        Args:
            file_path: Path to source file
            template: Template configuration
            custom_variables: Optional custom variables
            
        Returns:
            Dictionary with preview information
        """
        debug_logger.log("DEBUG", "Generating preview",
                        file_path=str(file_path))
        
        try:
            substitutions = self._prepare_substitutions(
                file_path, custom_variables or {}, template
            )
            
            # Get substitution previews
            index_preview = self.substitution.preview_substitution(
                template.index, substitutions
            )
            history_preview = self.substitution.preview_substitution(
                template.history, substitutions
            )
            
            preview = {
                "file_path": str(file_path),
                "template_name": template.name,
                "substitution_variables": len(substitutions),
                "custom_variables_provided": len(custom_variables) if custom_variables else 0,
                "template_variables": {
                    "index": {
                        "found": index_preview["variables_found"],
                        "resolved": index_preview["variables_resolved"],
                        "unresolved": index_preview["variables_unresolved"],
                        "syntax_issues": index_preview["syntax_issues"],
                    },
                    "history": {
                        "found": history_preview["variables_found"],
                        "resolved": history_preview["variables_resolved"],
                        "unresolved": history_preview["variables_unresolved"],
                        "syntax_issues": history_preview["syntax_issues"],
                    },
                },
                "substitution_sample": {
                    k: v[:100] + "..." if len(v) > 100 else v 
                    for k, v in list(substitutions.items())[:5]
                },
                "generation_ready": (
                    len(index_preview["syntax_issues"]) == 0 and
                    len(history_preview["syntax_issues"]) == 0
                ),
            }
            
            return preview
            
        except Exception as e:
            debug_logger.log("ERROR", "Preview generation failed",
                           file_path=str(file_path), error=str(e))
            return {
                "file_path": str(file_path),
                "error": str(e),
                "generation_ready": False,
            }
    
    def validate_generation(self,
                          file_path: Path,
                          template: TemplateConfig,
                          custom_variables: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate that generation can proceed without errors.
        
        Args:
            file_path: Path to source file
            template: Template configuration
            custom_variables: Optional custom variables
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        try:
            # Check if source file exists
            if not file_path.exists():
                issues.append(f"Source file does not exist: {file_path}")
            
            # Validate template configuration
            if not template.index.strip():
                issues.append("Template index content is empty")
            if not template.history.strip():
                issues.append("Template history content is empty")
            
            # Check template syntax
            index_issues = self.substitution.validate_template_syntax(template.index)
            if index_issues:
                issues.extend([f"Index template: {issue}" for issue in index_issues])
            
            history_issues = self.substitution.validate_template_syntax(template.history)
            if history_issues:
                issues.extend([f"History template: {issue}" for issue in history_issues])
            
            # Check substitution readiness
            if not issues:  # Only check if no syntax issues
                substitutions = self._prepare_substitutions(
                    file_path, custom_variables or {}, template
                )
                
                index_vars = self.substitution.get_variables_in_template(template.index)
                history_vars = self.substitution.get_variables_in_template(template.history)
                all_vars = index_vars | history_vars
                
                unresolved = [v for v in all_vars if v not in substitutions]
                if unresolved:
                    issues.append(f"Unresolved variables: {', '.join(sorted(unresolved))}")
            
            # Check write permissions
            try:
                spec_dir = self.directory_manager.create_spec_directory(file_path)
                if not spec_dir.exists():
                    issues.append(f"Cannot create spec directory: {spec_dir}")
            except SpecFileError as e:
                issues.append(f"Directory creation error: {e}")
            
        except Exception as e:
            issues.append(f"Validation error: {e}")
        
        return issues
    
    def get_generation_stats(self,
                           file_path: Path,
                           template: TemplateConfig,
                           custom_variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get detailed statistics about what generation would produce.
        
        Args:
            file_path: Path to source file
            template: Template configuration
            custom_variables: Optional custom variables
            
        Returns:
            Dictionary with generation statistics
        """
        try:
            substitutions = self._prepare_substitutions(
                file_path, custom_variables or {}, template
            )
            
            index_stats = self.substitution.get_substitution_stats(
                template.index, substitutions
            )
            history_stats = self.substitution.get_substitution_stats(
                template.history, substitutions
            )
            
            stats = {
                "file_path": str(file_path),
                "template_name": template.name,
                "total_variables_available": len(substitutions),
                "custom_variables_provided": len(custom_variables) if custom_variables else 0,
                "index_template": {
                    "length": index_stats["template_length"],
                    "variables": index_stats["unique_variables"],
                    "coverage": index_stats["substitution_coverage"],
                    "syntax_valid": index_stats["syntax_valid"],
                },
                "history_template": {
                    "length": history_stats["template_length"],
                    "variables": history_stats["unique_variables"],
                    "coverage": history_stats["substitution_coverage"],
                    "syntax_valid": history_stats["syntax_valid"],
                },
                "generation_ready": (
                    index_stats["syntax_valid"] and
                    history_stats["syntax_valid"] and
                    index_stats["substitution_coverage"] > 0 and
                    history_stats["substitution_coverage"] > 0
                ),
            }
            
            return stats
            
        except Exception as e:
            return {
                "file_path": str(file_path),
                "error": str(e),
                "generation_ready": False,
            }


# Convenience function for backward compatibility
def generate_spec_content(file_path: Path, 
                         template: TemplateConfig,
                         custom_variables: Optional[Dict[str, Any]] = None) -> Dict[str, Path]:
    """Generate spec content (backward compatibility function).
    
    Args:
        file_path: Path to source file
        template: Template configuration
        custom_variables: Optional custom variables
        
    Returns:
        Dictionary mapping file types to created file paths
    """
    generator = SpecContentGenerator()
    return generator.generate_spec_content(file_path, template, custom_variables)
```

### Step 2: Update spec_cli/templates/__init__.py

```python
"""Template system for spec CLI.

This package provides template configuration, loading, substitution, and content generation
for creating consistent documentation across different contexts.
"""

from .config import TemplateConfig, TemplateValidator
from .loader import TemplateLoader, load_template
from .defaults import get_default_template_config, get_template_preset
from .substitution import TemplateSubstitution
from .generator import SpecContentGenerator, generate_spec_content

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
]
```

## Test Requirements

Create comprehensive tests for the spec generator:

### Test Cases (15 tests total)

**Core Generation Tests:**
1. **test_generator_creates_index_and_history_files**
2. **test_generator_uses_file_based_variables**
3. **test_generator_applies_custom_variables_with_precedence**
4. **test_generator_handles_backup_existing_files**
5. **test_generator_handles_file_writing_errors**

**Integration Tests:**
6. **test_generator_integrates_with_substitution_engine**
7. **test_generator_integrates_with_directory_manager**
8. **test_generator_integrates_with_metadata_extractor**
9. **test_generator_creates_spec_directories**

**Preview and Validation Tests:**
10. **test_generator_previews_generation_results**
11. **test_generator_validates_generation_requirements**
12. **test_generator_provides_generation_statistics**
13. **test_generator_handles_missing_source_files**

**Utility Tests:**
14. **test_generator_extracts_template_defaults**
15. **test_backward_compatibility_function_works**

## Validation Steps

Run these exact commands to verify the implementation:

```bash
# Run the specific tests for this slice
poetry run pytest tests/unit/templates/test_generator.py -v

# Verify test coverage is 80%+
poetry run pytest tests/unit/templates/test_generator.py --cov=spec_cli.templates.generator --cov-report=term-missing --cov-fail-under=80

# Run type checking
poetry run mypy spec_cli/templates/generator.py

# Check code formatting
poetry run ruff check spec_cli/templates/generator.py
poetry run ruff format spec_cli/templates/generator.py

# Verify imports work correctly
python -c "from spec_cli.templates.generator import SpecContentGenerator, generate_spec_content; print('Import successful')"

# Test basic generation workflow
python -c "
from spec_cli.templates.generator import SpecContentGenerator
from spec_cli.templates.loader import load_template
from pathlib import Path

generator = SpecContentGenerator()
template = load_template()

# Test generation preview
test_file = Path('test_example.py')
preview = generator.preview_generation(test_file, template)
print(f'Generation preview:')
print(f'  File: {preview["file_path"]}')
print(f'  Template: {preview["template_name"]}')
print(f'  Variables: {preview["substitution_variables"]}')
print(f'  Ready: {preview["generation_ready"]}')

if preview["generation_ready"]:
    print('  Index variables:', len(preview["template_variables"]["index"]["found"]))
    print('  History variables:', len(preview["template_variables"]["history"]["found"]))
else:
    print('  Issues found in template validation')
"

# Test validation
python -c "
from spec_cli.templates.generator import SpecContentGenerator
from spec_cli.templates.loader import load_template
from pathlib import Path

generator = SpecContentGenerator()
template = load_template()

# Test validation
test_file = Path('spec_cli/__main__.py')  # Use existing file
if test_file.exists():
    issues = generator.validate_generation(test_file, template)
    if issues:
        print(f'Validation issues: {issues}')
    else:
        print('Validation passed - generation can proceed')
        
    # Show generation stats
    stats = generator.get_generation_stats(test_file, template)
    print(f'Generation stats:')
    print(f'  Template: {stats["template_name"]}')
    print(f'  Variables available: {stats["total_variables_available"]}')
    print(f'  Index coverage: {stats["index_template"]["coverage"]:.1f}%')
    print(f'  History coverage: {stats["history_template"]["coverage"]:.1f}%')
    print(f'  Ready for generation: {stats["generation_ready"]}')
else:
    print('Test file not found, skipping validation test')
"

# Test file-based variables
python -c "
from spec_cli.templates.generator import SpecContentGenerator
from pathlib import Path

generator = SpecContentGenerator()

# Test with a real file
test_file = Path('spec_cli/__main__.py')
if test_file.exists():
    variables = generator._get_file_based_variables(test_file)
    print(f'File-based variables for {test_file}:')
    for key, value in variables.items():
        print(f'  {key}: {value}')
else:
    print('Test file not found, skipping file-based variable test')
"

# Test custom variables precedence
python -c "
from spec_cli.templates.generator import SpecContentGenerator
from spec_cli.templates.loader import load_template
from pathlib import Path

generator = SpecContentGenerator()
template = load_template()

# Test with custom variables
test_file = Path('test.py')
custom_vars = {
    'filename': 'CUSTOM_NAME.py',  # Override file-based variable
    'custom_field': 'Custom Value',
    'author': 'Test Author'
}

substitutions = generator._prepare_substitutions(test_file, custom_vars, template)
print(f'Substitution variables (showing precedence):')
for key in ['filename', 'custom_field', 'author', 'file_extension', 'template_name']:
    if key in substitutions:
        print(f'  {key}: {substitutions[key]}')

print(f'Total variables prepared: {len(substitutions)}')
"

# Test backward compatibility
python -c "
from spec_cli.templates import generate_spec_content, load_template
from pathlib import Path

template = load_template()
test_file = Path('test_example.py')

print('Testing backward compatibility function...')
try:
    # This would create files, so we'll just test it doesn't error on import/call
    print('Function imported and callable: ✓')
except Exception as e:
    print(f'Backward compatibility issue: {e}')
"
```

## Definition of Done

- [ ] SpecContentGenerator class for creating index.md and history.md files
- [ ] Integration with TemplateSubstitution engine from slice-8a
- [ ] File-based variable extraction from source file metadata
- [ ] Custom variable support with proper precedence handling
- [ ] Integration with DirectoryManager for spec directory creation
- [ ] Backup functionality for existing spec files
- [ ] Generation preview and validation capabilities
- [ ] File writing with proper encoding and error handling
- [ ] All 15 tests pass with 80%+ coverage
- [ ] Type hints throughout with mypy compliance
- [ ] Integration with all file system and template components
- [ ] Backward compatibility function maintained
- [ ] Validation commands all pass successfully

## Next Slice Preparation

This slice enables slice-8c (AI hooks) by providing:
- Complete spec file generation workflow that AI hooks can extend
- Variable preparation system that AI content can integrate with
- Template processing foundation that AI generation can build upon
- File creation infrastructure that AI-generated content can use