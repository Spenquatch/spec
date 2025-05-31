# Implementation Plan: `spec gen` Command

## Overview
Implement the `spec gen` command following the vertical slice approach - complete implementation through testing and typing before moving to the next slice.

## Vertical Slices

### Slice 1: Basic `gen` Command Structure
**Goal**: Basic command parsing and argument handling

#### Implementation:
1. Add `cmd_gen()` function to handle command
2. Add argument parsing for file/directory paths
3. Add basic error handling for invalid paths
4. Register command in `COMMANDS` dict

#### Unit Tests (`tests/unit/test_cmd_gen.py`):
```python
def test_cmd_gen_with_no_args_shows_error()
def test_cmd_gen_with_file_path_calls_handler()
def test_cmd_gen_with_directory_path_calls_handler()
def test_cmd_gen_with_dot_calls_handler()
def test_cmd_gen_with_nonexistent_path_shows_error()
```

#### Type Hints:
- Add proper type annotations for `cmd_gen(args: List[str]) -> None`
- Import necessary types from `typing` and `pathlib`

#### Quality Assurance:
```bash
poetry run pytest tests/unit/test_cmd_gen.py -v --cov=spec_cli --cov-report=term-missing --cov-fail-under=80
poetry run mypy spec_cli/__main__.py
poetry run ruff check --fix .
poetry run pre-commit run --all-files
git add . && git commit -m "feat: implement slice 1 - basic gen command structure"
```

---

### Slice 2: File Path Resolution and Validation
**Goal**: Convert input paths to proper relative paths and validate them

#### Implementation:
1. Create `resolve_file_path(path: str) -> Path` function
2. Handle absolute vs relative paths
3. Convert paths relative to project root
4. Validate file exists and is a source file

#### Unit Tests (`tests/unit/test_path_resolution.py`):
```python
def test_resolve_file_path_with_absolute_path_returns_relative()
def test_resolve_file_path_with_relative_path_unchanged()
def test_resolve_file_path_with_nonexistent_file_raises_error()
def test_resolve_file_path_with_directory_raises_error()
```

#### Type Hints:
- `resolve_file_path(path: str) -> Path`
- Custom exception types for validation errors

#### Quality Assurance:
```bash
poetry run pytest tests/unit/test_path_resolution.py -v
poetry run mypy spec_cli/
poetry run ruff check --fix .
poetry run pre-commit run --all-files
git add . && git commit -m "feat: implement slice 2 - file path resolution and validation"
```

---

### Slice 3: Spec Directory Structure Creation
**Goal**: Create the directory structure for spec files

#### Implementation:
1. Create `create_spec_directory(file_path: Path) -> Path` function
2. Generate directory path: `.specs/path/to/file/`
3. Create directory structure with `parents=True`
4. Handle existing directories gracefully

#### Unit Tests (`tests/unit/test_directory_creation.py`):
```python
def test_create_spec_directory_creates_nested_structure()
def test_create_spec_directory_handles_existing_directory()
def test_create_spec_directory_with_permission_error()
def test_create_spec_directory_returns_correct_path()
```

#### Type Hints:
- `create_spec_directory(file_path: Path) -> Path`
- Handle `OSError` and `PermissionError` types

#### Quality Assurance:
```bash
poetry run pytest tests/unit/test_directory_creation.py -v
poetry run mypy spec_cli/
poetry run ruff check --fix .
poetry run pre-commit run --all-files
git add . && git commit -m "feat: implement slice 3 - spec directory structure creation"
```

---

### Slice 4: Template System Foundation
**Goal**: Basic template loading and default template

#### Implementation:
1. Create `TemplateConfig` Pydantic model
2. Create `load_template() -> TemplateConfig` function
3. Check for `.spectemplate` file
4. Provide default template if none exists
5. Parse YAML template structure

#### Unit Tests (`tests/unit/test_template_system.py`):
```python
def test_load_template_with_no_file_returns_default()
def test_load_template_with_valid_yaml_parses_correctly()
def test_load_template_with_invalid_yaml_raises_error()
def test_template_config_validates_required_fields()
def test_default_template_has_all_sections()
```

#### Type Hints:
- `TemplateConfig` Pydantic model with proper field types
- `load_template() -> TemplateConfig`
- Handle `yaml.YAMLError` and `pydantic.ValidationError`

#### Quality Assurance:
```bash
poetry run pytest tests/unit/test_template_system.py -v
poetry run mypy spec_cli/
poetry run ruff check --fix .
poetry run pre-commit run --all-files
git add . && git commit -m "feat: implement slice 4 - template system foundation"
```

---

### Slice 5: Basic Content Generation
**Goal**: Generate placeholder content for index.md and history.md

#### Implementation:
1. Create `generate_spec_content(file_path: Path, template: TemplateConfig) -> Tuple[str, str]`
2. Template substitution for basic placeholders
3. Generate both `index.md` and `history.md` content
4. Handle placeholder replacement logic

#### Unit Tests (`tests/unit/test_content_generation.py`):
```python
def test_generate_spec_content_replaces_placeholders()
def test_generate_spec_content_returns_index_and_history()
def test_generate_spec_content_with_custom_template()
def test_placeholder_substitution_with_special_characters()
def test_content_generation_with_missing_template_fields()
```

#### Type Hints:
- `generate_spec_content(file_path: Path, template: TemplateConfig) -> Tuple[str, str]`
- Define placeholder types and substitution mappings

#### Quality Assurance:
```bash
poetry run pytest tests/unit/test_content_generation.py -v
poetry run mypy spec_cli/
poetry run ruff check --fix .
poetry run pre-commit run --all-files
git add . && git commit -m "feat: implement slice 5 - basic content generation"
```

---

### Slice 6: File Type Detection and Filtering
**Goal**: Detect source code files and filter appropriately

#### Implementation:
1. Create `is_source_file(file_path: Path) -> bool` function
2. Define `SUPPORTED_EXTENSIONS` constant
3. Create `find_source_files(directory: Path) -> List[Path]` function
4. Handle directory traversal for `spec gen .`

#### Unit Tests (`tests/unit/test_file_filtering.py`):
```python
def test_is_source_file_with_python_file_returns_true()
def test_is_source_file_with_text_file_returns_false()
def test_find_source_files_in_directory_finds_all()
def test_find_source_files_excludes_non_source()
def test_find_source_files_handles_nested_directories()
```

#### Type Hints:
- `is_source_file(file_path: Path) -> bool`
- `find_source_files(directory: Path) -> List[Path]`
- `SUPPORTED_EXTENSIONS: frozenset[str]`

#### Quality Assurance:
```bash
poetry run pytest tests/unit/test_file_filtering.py -v
poetry run mypy spec_cli/
poetry run ruff check --fix .
poetry run pre-commit run --all-files
git add . && git commit -m "feat: implement slice 6 - file type detection and filtering"
```

---

### Slice 7: Duplicate Detection and Handling
**Goal**: Detect existing specs and handle gracefully

#### Implementation:
1. Create `spec_exists(file_path: Path) -> bool` function
2. Check for existing `index.md` files
3. Create `handle_existing_spec(file_path: Path) -> bool` function
4. Provide clear messaging for existing specs

#### Unit Tests (`tests/unit/test_duplicate_detection.py`):
```python
def test_spec_exists_with_existing_index_returns_true()
def test_spec_exists_with_no_index_returns_false()
def test_handle_existing_spec_shows_appropriate_message()
def test_spec_exists_handles_permission_errors()
```

#### Type Hints:
- `spec_exists(file_path: Path) -> bool`
- `handle_existing_spec(file_path: Path) -> bool`

#### Quality Assurance:
```bash
poetry run pytest tests/unit/test_duplicate_detection.py -v
poetry run mypy spec_cli/
poetry run ruff check --fix .
poetry run pre-commit run --all-files
git add . && git commit -m "feat: implement slice 7 - duplicate detection and handling"
```

---

### Slice 8: Debug Mode and Logging Integration
**Goal**: Add debug mode support and comprehensive logging

#### Implementation:
1. Add debug logging to all gen functions using `SPEC_DEBUG` environment variable
2. Create `setup_logging()` function to configure logging levels
3. Add debug output for template loading, file discovery, content generation
4. Ensure debug output matches existing pattern from other commands

#### Unit Tests (`tests/unit/test_debug_logging.py`):
```python
def test_debug_mode_enabled_when_spec_debug_set()
def test_debug_logging_outputs_template_info()
def test_debug_logging_outputs_file_discovery_info()
def test_debug_mode_disabled_by_default()
def test_setup_logging_configures_correct_level()
```

#### Quality Assurance:
```bash
poetry run pytest tests/unit/test_debug_logging.py -v --cov=spec_cli --cov-report=term-missing --cov-fail-under=80
poetry run mypy spec_cli/
poetry run ruff check --fix .
poetry run pre-commit run --all-files
git add . && git commit -m "feat: implement slice 8 - debug mode and logging integration"
```

---

### Slice 9: Integration and End-to-End Testing
**Goal**: Complete integration of all slices

#### Implementation:
1. Wire all functions together in `cmd_gen()`
2. Add comprehensive error handling
3. Add progress reporting for multiple files
4. Final integration testing

#### Unit Tests (`tests/unit/test_gen_integration.py`):
```python
def test_cmd_gen_end_to_end_single_file()
def test_cmd_gen_end_to_end_directory()
def test_cmd_gen_end_to_end_current_directory()
def test_cmd_gen_with_existing_specs_shows_warnings()
def test_cmd_gen_with_mixed_file_types_filters_correctly()
```

#### Integration Test (temporary script):
```bash
# Create test_gen_integration.py in root, run, then delete
poetry run python test_gen_integration.py
rm test_gen_integration.py
```

#### Type Hints:
- Final type checking with `mypy --strict`
- Ensure all functions are properly typed

#### Quality Assurance:
```bash
poetry run pytest tests/unit/ -v
poetry run mypy spec_cli/ --strict
poetry run ruff check --fix .
poetry run pre-commit run --all-files
git add . && git commit -m "feat: implement slice 9 - complete gen command integration"
```

---

### Slice 10: Debug Logging Cleanup (Technical Debt)
**Goal**: Remove legacy debug print statements and standardize on stderr logging

#### Background:
During Slice 8 implementation, legacy `print()` debug statements were maintained for backwards compatibility with existing tests. This slice cleans up the dual logging system and standardizes on proper stderr logging.

#### Implementation:
1. **Remove Legacy Functions**:
   - Delete `legacy_debug_print()` function from `spec_cli/__main__.py`
   - Remove all calls to `legacy_debug_print()` throughout the codebase

2. **Update Debug Logging Calls**:
   - Remove duplicate legacy calls in all functions:
     - `create_spec_directory()` - line ~335
     - `load_template()` - lines ~366, ~363  
     - `generate_spec_content()` - lines ~424-425
     - `load_specignore_patterns()` - line ~608
     - `should_generate_spec()` - lines ~639, ~647, ~731
     - `check_existing_specs()` - lines ~753-755
     - `create_backup()` - line ~786
     - `handle_spec_conflict()` - line ~820
   - Keep only the structured `debug_log()` calls

3. **Update All Test Files**:
   - Change `capsys.readouterr().out` to `capsys.readouterr().err` in debug output tests
   - Update assertion strings to match new structured format
   - Files to update:
     - `tests/unit/test_content_generation.py` - lines ~242-244
     - `tests/unit/test_directory_creation.py` - debug output tests
     - `tests/unit/test_duplicate_handling.py` - debug output tests  
     - `tests/unit/test_file_filtering.py` - debug output tests
     - `tests/unit/test_template_system.py` - debug output tests

4. **Update Test Assertions**:
   - Change from: `assert "🔍 Debug: Generated index.md" in captured.out`
   - Change to: `assert "Generated spec content files" in captured.err`
   - Update all debug assertions to match structured logging format

#### Files to Modify:
- `spec_cli/__main__.py` - Remove legacy function and calls (~12 locations)
- `tests/unit/test_content_generation.py` - Update debug test assertions
- `tests/unit/test_directory_creation.py` - Update debug test assertions  
- `tests/unit/test_duplicate_handling.py` - Update debug test assertions
- `tests/unit/test_file_filtering.py` - Update debug test assertions
- `tests/unit/test_template_system.py` - Update debug test assertions

#### Expected Changes:
- **Lines removed**: ~15-20 lines of legacy debug calls
- **Lines modified**: ~25-30 test assertion lines
- **Net effect**: Cleaner, more maintainable debug system

#### Quality Assurance:
```bash
# Ensure all tests still pass with stderr logging
poetry run pytest tests/unit/ -v --cov=spec_cli --cov-report=term-missing --cov-fail-under=80

# Verify type checking still passes
poetry run mypy spec_cli/

# Check code quality
poetry run ruff check --fix .
poetry run pre-commit run --all-files

# Commit the cleanup
git add . && git commit -m "refactor: remove legacy debug logging, standardize on stderr"
```

#### Benefits:
- **Single responsibility**: One debug logging system instead of two
- **Standards compliance**: Debug output goes to stderr as expected
- **Cleaner codebase**: Removes ~20 lines of redundant code
- **Future-proof**: New debug statements will use proper logging
- **Better UX**: Users can redirect debug output separately from main output

#### Testing Strategy:
```bash
# Manual verification that debug output works correctly:
cd test_area
SPEC_DEBUG=1 spec gen test.py 2> debug.log 1> output.log

# debug.log should contain structured debug messages
# output.log should contain user-facing messages
```

---

## Implementation Order

1. **Slice 1** → Basic command structure
2. **Slice 2** → Path handling  
3. **Slice 3** → Directory creation
4. **Slice 4** → Template system
5. **Slice 5** → Content generation
6. **Slice 6** → File filtering
7. **Slice 7** → Duplicate handling
8. **Slice 8** → Debug mode and logging
9. **Slice 9** → Integration and testing
10. **Slice 10** → Debug logging cleanup (technical debt)

## Success Criteria per Slice

-  **Unit tests pass**: `poetry run pytest tests/unit/ -v`
-  **Type checking passes**: `poetry run mypy spec_cli/`
-  **Linting passes**: `poetry run ruff check .`
-  **Pre-commit hooks pass**: `poetry run pre-commit run --all-files`
-  **Function works as intended**: Manual testing in test_area/
-  **Committed**: Clean git commit with descriptive message

## Final Deliverable

A fully functional `spec gen` command that:
- Generates documentation for individual files
- Handles directory traversal
- Creates proper directory structure
- Uses template system
- Provides clear user feedback
- Integrates with existing Git workflow
- Has comprehensive pytest test coverage (>90%)
- Is fully typed and passes mypy --strict
- Passes all pre-commit hooks