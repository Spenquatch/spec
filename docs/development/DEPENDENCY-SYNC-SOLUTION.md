# Poetry/Pre-commit Dependency Synchronization Solution

## Overview

This document describes our implementation of automatic synchronization between Poetry dependencies and pre-commit hook configurations, solving the common pain point of maintaining consistency between these tools.

## The Problem

In Python projects using both Poetry and pre-commit, you often need the same tools (mypy, ruff, black, etc.) configured in both places:

- **Poetry**: Manages Python package dependencies with version ranges
- **Pre-commit**: Manages git hooks with exact versions from different repositories

This leads to configuration drift and inconsistencies, especially for type checking tools that require matching type stub dependencies.

## Complexity Assessment: Medium

### Why Not Simple?
1. **Different Versioning Schemes**:
   ```toml
   # Poetry (pyproject.toml)
   ruff = "^0.11.12"

   # Pre-commit (.pre-commit-config.yaml)
   - repo: https://github.com/astral-sh/ruff-pre-commit
     rev: v0.11.12
   ```

2. **Repository Mapping**:
   ```python
   # Need to map package names to GitHub repositories
   "mypy" -> "https://github.com/pre-commit/mirrors-mypy"
   "ruff" -> "https://github.com/astral-sh/ruff-pre-commit"
   ```

3. **Dependency Injection**:
   ```yaml
   # Type stubs need to be injected into mypy hook
   additional_dependencies: [types-click, types-PyYAML, pydantic]
   ```

### Why Not Complex?
1. **Finite Mapping**: Limited set of tools commonly used in pre-commit
2. **Standard Patterns**: Most tools follow predictable versioning conventions
3. **One-Way Sync**: Poetry is source of truth, pre-commit is generated

## Our Solution: `sync-pre-commit.py`

### Architecture

```python
# 1. Mapping Configuration
HOOK_MAPPINGS = {
    "mypy": HookConfig(
        repo="https://github.com/pre-commit/mirrors-mypy",
        rev_pattern="v{version}",  # v1.16.0
        hook_id="mypy",
        additional_deps=["types-PyYAML", "types-click", ...],
        args=["--python-version=3.10"],
        files="^spec_cli/"
    ),
    # ... more tools
}

# 2. Version Extraction
def extract_version(version_spec: str) -> str:
    # "^1.16.0" -> "1.16.0"
    # ">=1.16.0,<2.0" -> "1.16.0"

# 3. Config Generation
def generate_pre_commit_config(poetry_deps: Dict[str, str]) -> Dict:
    # Read poetry deps -> Generate pre-commit YAML
```

### Key Features

1. **Automatic Type Stub Detection**:
   ```python
   # Finds all types-* packages in poetry and adds them to mypy
   type_deps = [dep for dep in poetry_deps if dep.startswith("types-")]
   ```

2. **Version Pattern Mapping**:
   ```python
   # Converts poetry versions to git tags
   "^1.16.0" -> "v1.16.0"  # for mypy
   "^0.11.12" -> "v0.11.12"  # for ruff
   ```

3. **Smart Hook Configuration**:
   ```python
   # Ruff gets both linting and formatting hooks
   if package == "ruff":
       hooks = [{"id": "ruff", "args": ["--fix"]}, {"id": "ruff-format"}]
   ```

4. **Safe Updates**:
   ```python
   # Backs up existing config before updating
   # Only updates if changes detected
   ```

## Usage

### Manual Sync
```bash
python scripts/sync-pre-commit.py
```

### Automatic Integration Options

#### 1. Pre-commit Hook (Recommended)
```yaml
# Add to .pre-commit-config.yaml
- repo: local
  hooks:
    - id: sync-pre-commit-deps
      name: Sync pre-commit dependencies with poetry
      entry: python scripts/sync-pre-commit.py
      language: system
      pass_filenames: false
      files: ^pyproject\.toml$
```

#### 2. Makefile Target
```makefile
sync-deps:
	python scripts/sync-pre-commit.py
	pre-commit autoupdate

install:
	poetry install
	pre-commit install
	$(MAKE) sync-deps
```

#### 3. GitHub Action
```yaml
name: Sync Dependencies
on:
  push:
    paths: ['pyproject.toml']
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Sync pre-commit config
        run: python scripts/sync-pre-commit.py
      - name: Create PR if changes
        # ... create PR with updated config
```

## Example Output

Running the script on our project:
```bash
$ python scripts/sync-pre-commit.py
📖 Loaded 29 dependencies from pyproject.toml
📦 Backed up existing config to .pre-commit-config.yaml.backup
✅ Generated new .pre-commit-config.yaml from poetry dependencies!

🛠️  Configured pre-commit hooks for: ruff, mypy, bandit
📝 Added type dependencies: types-PyYAML, types-click
```

Generated config:
```yaml
repos:
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.11.12
  hooks:
  - id: ruff
    args: [--fix]
  - id: ruff-format
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.16.0
  hooks:
  - id: mypy
    additional_dependencies: [types-PyYAML, types-click, pydantic, tomli, rich, rich-click]
    args: [--python-version=3.10]
    files: ^spec_cli/
```

## Extensibility

### Adding New Tools

```python
# Add to HOOK_MAPPINGS in sync-pre-commit.py
"black": HookConfig(
    repo="https://github.com/psf/black-pre-commit-mirror",
    rev_pattern="{version}",  # No 'v' prefix for black
    hook_id="black",
    additional_deps=[],
    args=["--line-length=88"]
),
```

### Custom Configuration

```python
# Override default behavior
if package == "mypy":
    # Project-specific mypy configuration
    hook_data["hooks"][0]["args"] = ["--config-file=pyproject.toml"]
```

## Comparison with Alternative Approaches

| Approach | Pros | Cons | Complexity |
|----------|------|------|------------|
| **Manual Sync** | Simple, explicit | Error-prone, forgettable | Low |
| **Our Script** | Automated, consistent, extensible | One-time setup | Medium |
| **sync-pre-commit-lock** | Third-party tool | Limited scope, extra dependency | Low |
| **Renovate/Dependabot** | Handles updates | Doesn't sync configurations | Medium |

## Lessons Learned

1. **Poetry as Source of Truth**: Using poetry dependencies as the canonical source simplifies the model
2. **Mapping is Key**: The core complexity is in the package-to-repo mapping
3. **Type Stubs Matter**: Automatic type stub detection is crucial for type checking tools
4. **Backup and Validate**: Always backup existing configs and validate changes
5. **Extensibility Wins**: Making it easy to add new tools is worth the initial investment

## Recommendations

1. **For Small Projects** (< 5 dev dependencies): Manual sync is fine
2. **For Medium Projects** (5-15 dev dependencies): Use our script manually
3. **For Large Projects** (15+ dev dependencies): Automate with pre-commit hook or CI
4. **For Organizations**: Consider creating a shared package with common mappings

## Future Enhancements

1. **Config Validation**: Verify generated configs work before committing
2. **Dependency Resolution**: Handle version conflicts between tools
3. **Template System**: Allow project-specific hook templates
4. **CI Integration**: Automatic PR creation when configs drift
5. **Community Mappings**: Shared repository of tool mappings

## Conclusion

Our sync script successfully bridges the gap between Poetry and pre-commit with medium complexity but high value. It's a practical solution that scales from manual usage to full automation, solving a real pain point in modern Python development workflows.

The key insight is that most projects use a similar set of tools, so the one-time investment in mapping configuration pays dividends across many projects.
