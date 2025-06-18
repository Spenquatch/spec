# Development Scripts

This directory contains helper scripts for development and maintenance.

## sync-pre-commit.py

Automatically synchronizes pre-commit hook configuration with Poetry dependencies.

### Features

- **Automatic dependency mapping**: Maps Poetry packages to their pre-commit repository equivalents
- **Version synchronization**: Converts Poetry version specs (`^1.16.0`) to pre-commit tags (`v1.16.0`)
- **Type stub detection**: Automatically includes `types-*` packages in mypy configuration
- **Safe updates**: Backs up existing configuration and preserves local hooks

### Usage

```bash
# Manual sync
python scripts/sync-pre-commit.py

# Show what would change
python scripts/sync-pre-commit.py --dry-run

# Quiet mode (for automation)
python scripts/sync-pre-commit.py --quiet
```

### Automatic Execution

The script runs automatically as a pre-commit hook whenever `pyproject.toml` is modified. This ensures that pre-commit configuration stays synchronized with Poetry dependencies.

### Supported Tools

- **mypy**: Type checking with automatic type stub dependencies
- **ruff**: Both linting (`ruff`) and formatting (`ruff-format`) hooks
- **black**: Code formatting
- **isort**: Import sorting
- **bandit**: Security analysis

### Adding New Tools

To add support for a new tool, update the `HOOK_MAPPINGS` dictionary in the script:

```python
"tool-name": HookConfig(
    repo="https://github.com/org/tool-pre-commit",
    rev_pattern="v{version}",  # or "{version}" without 'v' prefix
    hook_id="tool-name",
    additional_deps=[],  # Any extra dependencies needed
    args=["--option"],   # Command line arguments
    files="^pattern/"    # File pattern filter (optional)
),
```

## auto-stage-formatted.py

Automatically stages files that were modified by formatting hooks during pre-commit runs.

### Purpose

Solves the common workflow issue where:
1. Developer runs `git commit`
2. Pre-commit hooks (like ruff-format) modify files
3. Commit fails because modified files aren't staged
4. Developer must run `git add` and commit again

### How It Works

- Runs as the last pre-commit hook after all formatting tools
- Identifies files that were modified by formatting hooks
- Automatically stages only the relevant files (not all modified files)
- Allows the commit to proceed without manual intervention

### Configuration

Automatically included when using `sync-pre-commit.py`. Configured as:

```yaml
- repo: local
  hooks:
  - id: auto-stage-formatted
    name: Auto-stage formatted files
    entry: python scripts/auto-stage-formatted.py
    language: system
    pass_filenames: false
    always_run: true
    stages: [pre-commit]
```

### Important Notes

- Shows as "Failed" in pre-commit output (this is normal - pre-commit considers any hook that modifies git state as failed)
- Only stages files with relevant extensions (.py, .md, .yaml, .yml, .json, .toml)
- Safe to run - won't stage unintended files

## check-deps-consistency.py

Simple validation script to check for consistency between Poetry and pre-commit dependencies (legacy - superseded by sync-pre-commit.py).

## Other Scripts

Additional development scripts may be added here as the project grows.
