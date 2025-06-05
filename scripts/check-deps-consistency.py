#!/usr/bin/env python3
"""
Check consistency between poetry dependencies and pre-commit hooks.

This script verifies that type checking dependencies (like mypy, types-*)
are consistent between pyproject.toml and .pre-commit-config.yaml.
"""

import sys

import tomli
import yaml


def load_poetry_deps():
    """Load dependencies from pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        data = tomli.load(f)

    deps = {}
    # Main dependencies
    deps.update(data.get("tool", {}).get("poetry", {}).get("dependencies", {}))
    # Dev dependencies
    deps.update(
        data.get("tool", {})
        .get("poetry", {})
        .get("group", {})
        .get("dev", {})
        .get("dependencies", {})
    )

    return deps


def load_precommit_deps():
    """Load dependencies from .pre-commit-config.yaml."""
    with open(".pre-commit-config.yaml") as f:
        data = yaml.safe_load(f)

    deps = set()
    for repo in data.get("repos", []):
        for hook in repo.get("hooks", []):
            # Get additional_dependencies
            for dep in hook.get("additional_dependencies", []):
                # Handle version specifiers
                dep_name = dep.split("[")[0].split(">")[0].split("<")[0].split("=")[0]
                deps.add(dep_name)

    return deps


def check_consistency():
    """Check if pre-commit deps are in poetry deps."""
    poetry_deps = load_poetry_deps()
    precommit_deps = load_precommit_deps()

    # Type-related dependencies that should be consistent
    type_deps = {
        dep
        for dep in precommit_deps
        if dep.startswith("types-") or dep in ["mypy", "pydantic"]
    }

    missing_in_poetry = []
    for dep in type_deps:
        if dep not in poetry_deps:
            missing_in_poetry.append(dep)

    if missing_in_poetry:
        print("❌ Inconsistency detected!")
        print("\nDependencies in .pre-commit-config.yaml but not in pyproject.toml:")
        for dep in missing_in_poetry:
            print(f"  - {dep}")
        print("\nTo fix, run:")
        for dep in missing_in_poetry:
            print(f"  poetry add --group dev {dep}")
        return 1
    else:
        print("✅ Dependencies are consistent between poetry and pre-commit!")
        return 0


if __name__ == "__main__":
    sys.exit(check_consistency())
