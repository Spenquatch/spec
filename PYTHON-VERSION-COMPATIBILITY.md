# Python Version Compatibility Best Practices

## Overview

When supporting multiple Python versions (e.g., Python 3.8 through 3.12), you'll encounter situations where newer Python versions have built-in modules that older versions lack. This guide explains how to handle these cases properly for both runtime execution and static type checking.

## Common Scenarios

### 1. New Standard Library Modules

Python regularly adds new modules to the standard library. Common examples:
- `tomllib` (added in Python 3.11) - TOML parser
- `zoneinfo` (added in Python 3.9) - Timezone support
- `graphlib` (added in Python 3.9) - Graph operations

### 2. Backport Packages

For many new standard library modules, the community provides backport packages:
- `tomllib` → `tomli` (for Python < 3.11)
- `zoneinfo` → `backports.zoneinfo` (for Python < 3.9)
- `importlib.metadata` → `importlib-metadata` (for Python < 3.8)

## Best Practice Pattern

### Step 1: Import at Module Level

Handle version-specific imports at the module level using `sys.version_info`:

```python
import sys

# Handle tomllib import for multiple Python versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # Backport with same API
    except ImportError:
        tomllib = None  # type: ignore[assignment]
```

### Step 2: Handle Missing Dependencies

Always handle the case where the backport isn't installed:

```python
def load_toml_file(path: Path) -> Dict[str, Any]:
    """Load TOML file with appropriate parser."""
    if tomllib is None:
        raise RuntimeError(
            "No TOML parser available. "
            "Install 'tomli' for Python < 3.11 support."
        )

    with path.open("rb") as f:
        return tomllib.load(f)
```

### Step 3: Type Checking Considerations

#### Issue: Type Checker Version Mismatch

When mypy is configured for an older Python version (e.g., 3.8), it won't recognize newer modules:
```
error: Cannot find implementation or library stub for module named "tomllib"
```

#### Solution: Conditional Imports with Type Guards

The pattern above handles this by:
1. Using `sys.version_info` to conditionally import
2. Aliasing the backport to the same name
3. Using `type: ignore[assignment]` only when necessary

#### Why This Works:
- **Runtime**: Python executes only the appropriate branch
- **Type Checking**: MyPy understands `sys.version_info` checks and analyzes each branch separately
- **Consistency**: Both modules use the same variable name (`tomllib`)

## Anti-Patterns to Avoid

### ❌ Don't: Try/Except for Version Detection
```python
# Bad - mypy can't understand this pattern
try:
    import tomllib
except ImportError:
    import tomli as tomllib
```

### ❌ Don't: Inline Imports
```python
# Bad - makes code harder to understand and test
def load_config():
    try:
        import tomllib
    except ImportError:
        import tomli as tomllib
    # ...
```

### ❌ Don't: Ignore All Import Errors
```python
# Bad - hides real issues
import tomllib  # type: ignore
```

## Complete Example

Here's a complete example handling TOML parsing across Python versions:

```python
import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Version-specific imports
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore[assignment]


class ConfigLoader:
    """Load configuration from various sources."""

    def load_toml(self, path: Path) -> Dict[str, Any]:
        """Load TOML configuration file."""
        if tomllib is None:
            # Friendly error message with installation instructions
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
            raise RuntimeError(
                f"No TOML parser available for Python {python_version}. "
                "Please install 'tomli' package: pip install tomli"
            )

        try:
            with path.open("rb") as f:
                return tomllib.load(f)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML in {path}: {e}") from e
```

## Testing Across Versions

### 1. CI/CD Configuration

Test against all supported Python versions:

```yaml
# .github/workflows/test.yml
strategy:
  matrix:
    python-version: ["3.8", "3.9", "3.10", "3.11", "3.12"]
```

### 2. Conditional Dependencies

In `pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = "^3.8"
tomli = { version = "^2.0.0", python = "<3.11" }
```

### 3. Type Checking

Configure mypy for the minimum supported version:

```toml
[tool.mypy]
python_version = "3.8"
```

## Environment-Specific Issues

### Pre-commit vs Local Environment

Pre-commit runs in isolated environments, which may have different Python versions. If you see different behavior:

1. **Check Python versions**: Pre-commit might use a different Python
2. **Check installed packages**: Pre-commit installs only specified dependencies
3. **Use consistent type ignores**: Some type ignores may be needed only in certain environments

### Handling Environment Differences

When mypy behaves differently in different environments:

```python
# May need type: ignore in some environments but not others
if tomllib is None:
    # This might be "unreachable" in Python 3.11+ environments
    # but reachable in Python 3.8-3.10 environments
    logger.warning("No TOML parser available")  # type: ignore[unreachable]
    return {}
```

## Summary

1. **Use `sys.version_info` checks** for version-specific imports
2. **Alias backports** to standard library names for consistency
3. **Handle missing dependencies gracefully** with clear error messages
4. **Test across all supported versions** in CI/CD
5. **Configure type checkers** for the minimum supported version
6. **Document version requirements** clearly in your project

This approach ensures your code works correctly across all supported Python versions while maintaining type safety and clear error messages.
