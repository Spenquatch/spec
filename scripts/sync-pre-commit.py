#!/usr/bin/env python3
"""
Generate and sync pre-commit configuration from Poetry dependencies.

This script reads pyproject.toml and generates/updates .pre-commit-config.yaml
to ensure consistency between Poetry dependencies and pre-commit hooks.
"""

import re
import sys
from dataclasses import dataclass
from pathlib import Path

import tomli
import yaml


@dataclass
class HookConfig:
    """Configuration for a pre-commit hook."""

    repo: str
    rev_pattern: str  # Pattern to convert poetry version to git tag
    hook_id: str
    additional_deps: list[str]
    args: list[str] | None = None
    files: str | None = None


# Mapping of poetry packages to pre-commit hook configurations
HOOK_MAPPINGS = {
    "mypy": HookConfig(
        repo="https://github.com/pre-commit/mirrors-mypy",
        rev_pattern="v{version}",
        hook_id="mypy",
        additional_deps=[
            "types-PyYAML",
            "types-click",
            "pydantic",
            "tomli",
            "rich",
            "rich-click",
        ],
        args=["--python-version=3.10"],
        files="^spec_cli/",
    ),
    "ruff": HookConfig(
        repo="https://github.com/astral-sh/ruff-pre-commit",
        rev_pattern="v{version}",
        hook_id="ruff",
        additional_deps=[],
        args=["--fix"],
        files="^spec_cli/",
    ),
    "black": HookConfig(
        repo="https://github.com/psf/black-pre-commit-mirror",
        rev_pattern="{version}",
        hook_id="black",
        additional_deps=[],
    ),
    "isort": HookConfig(
        repo="https://github.com/pycqa/isort",
        rev_pattern="{version}",
        hook_id="isort",
        additional_deps=[],
    ),
    "bandit": HookConfig(
        repo="https://github.com/pycqa/bandit",
        rev_pattern="{version}",
        hook_id="bandit",
        additional_deps=[],
    ),
}

# Standard pre-commit hooks that don't come from poetry
STANDARD_HOOKS = {
    "repo": "https://github.com/pre-commit/pre-commit-hooks",
    "rev": "v4.5.0",
    "hooks": [
        {"id": "trailing-whitespace"},
        {"id": "end-of-file-fixer"},
        {"id": "check-yaml"},
        {"id": "check-added-large-files"},
        {"id": "check-merge-conflict"},
    ],
}


def load_poetry_dependencies() -> dict[str, str]:
    """Load dependencies from pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        data = tomli.load(f)

    deps = {}
    poetry_config = data.get("tool", {}).get("poetry", {})

    # Main dependencies
    deps.update(poetry_config.get("dependencies", {}))

    # Dev dependencies
    dev_deps = poetry_config.get("group", {}).get("dev", {}).get("dependencies", {})
    deps.update(dev_deps)

    return deps


def load_tool_config(tool_name: str) -> dict:
    """Load tool configuration from pyproject.toml."""
    with open("pyproject.toml", "rb") as f:
        data = tomli.load(f)

    return data.get("tool", {}).get(tool_name, {})


def extract_version(version_spec: str) -> str:
    """Extract version number from poetry version specification."""
    # Handle various poetry version specs: ^1.16.0, >=1.16.0, ~1.16.0, 1.16.0
    match = re.search(r"(\d+\.\d+\.\d+)", version_spec)
    if match:
        return match.group(1)

    # Handle cases like "^1.16" -> "1.16.0"
    match = re.search(r"(\d+\.\d+)", version_spec)
    if match:
        return f"{match.group(1)}.0"

    return version_spec.strip("^~>=<")


def get_type_dependencies(poetry_deps: dict[str, str]) -> list[str]:
    """Get all types-* dependencies from poetry."""
    return [dep for dep in poetry_deps.keys() if dep.startswith("types-")]


def generate_hook_config(
    package: str, version: str, poetry_deps: dict[str, str]
) -> dict | None:
    """Generate pre-commit hook configuration for a package."""
    if package not in HOOK_MAPPINGS:
        return None

    config = HOOK_MAPPINGS[package]
    clean_version = extract_version(version)

    # Generate the repository configuration
    hook_data = {
        "repo": config.repo,
        "rev": config.rev_pattern.format(version=clean_version),
        "hooks": [{"id": config.hook_id}],
    }

    # Special case: ruff gets both ruff and ruff-format hooks
    if package == "ruff":
        ruff_format_hook = {"id": "ruff-format"}
        if config.files:
            ruff_format_hook["files"] = config.files
        hook_data["hooks"].append(ruff_format_hook)

    # Add additional dependencies (including types-* packages)
    additional_deps = config.additional_deps.copy()

    # Add types-* dependencies that exist in poetry
    type_deps = get_type_dependencies(poetry_deps)
    if package == "mypy":  # Only add type deps to mypy
        additional_deps.extend(type_deps)

    # Remove duplicates while preserving order
    seen = set()
    unique_deps = []
    for dep in additional_deps:
        if dep not in seen and dep in poetry_deps:
            seen.add(dep)
            unique_deps.append(dep)

    if unique_deps:
        hook_data["hooks"][0]["additional_dependencies"] = unique_deps

    # Add args if specified
    if config.args:
        hook_data["hooks"][0]["args"] = config.args.copy()

    # Add tool-specific configuration from pyproject.toml
    if package == "bandit":
        bandit_config = load_tool_config("bandit")
        exclude_dirs = bandit_config.get("exclude_dirs", [])
        # Initialize args if not already present
        if "args" not in hook_data["hooks"][0]:
            hook_data["hooks"][0]["args"] = []
        # Add severity filter to match the dev script behavior
        hook_data["hooks"][0]["args"].append("-lll")
        # Add exclude arguments if configured
        if exclude_dirs:
            hook_data["hooks"][0]["args"].extend(["--exclude", ",".join(exclude_dirs)])

    # Add files pattern if specified
    if config.files:
        hook_data["hooks"][0]["files"] = config.files

    return hook_data


def generate_pre_commit_config(poetry_deps: dict[str, str]) -> dict:
    """Generate complete pre-commit configuration."""
    repos = []

    # Add standard pre-commit hooks first
    repos.append(STANDARD_HOOKS)

    # Add tool-specific hooks from poetry dependencies
    for package, version in poetry_deps.items():
        if package in HOOK_MAPPINGS:
            hook_config = generate_hook_config(package, version, poetry_deps)
            if hook_config:
                repos.append(hook_config)

    # Add auto-staging hook after formatting tools
    auto_stage_repo = {
        "repo": "local",
        "hooks": [
            {
                "id": "auto-stage-formatted",
                "name": "Auto-stage formatted files",
                "entry": "python scripts/auto-stage-formatted.py",
                "language": "system",
                "pass_filenames": False,
                "always_run": True,
                "stages": ["pre-commit"],
            }
        ],
    }
    repos.append(auto_stage_repo)

    return {"repos": repos}


def update_pre_commit_config(new_config: dict, dry_run: bool = False) -> bool:
    """Update .pre-commit-config.yaml with new configuration."""
    config_path = Path(".pre-commit-config.yaml")

    # Read existing config if it exists
    existing_config = {}
    if config_path.exists():
        with open(config_path) as f:
            existing_config = yaml.safe_load(f) or {}

    # Extract just the tool-related repos for comparison (skip local hooks)
    def extract_tool_repos(config):
        repos = config.get("repos", [])
        return [repo for repo in repos if repo.get("repo") != "local"]

    existing_tools = extract_tool_repos(existing_config)
    new_tools = extract_tool_repos(new_config)

    # Check if update is needed
    if existing_tools == new_tools:
        print("✅ .pre-commit-config.yaml tool dependencies are already up to date!")
        return False

    if dry_run:
        print("🔍 Dry run mode - would update .pre-commit-config.yaml")
        return True

    # Preserve local hooks from existing config
    local_repos = [
        repo for repo in existing_config.get("repos", []) if repo.get("repo") == "local"
    ]
    if local_repos:
        new_config["repos"] = local_repos + new_config["repos"]

    # Backup existing config
    if config_path.exists():
        backup_path = config_path.with_suffix(".yaml.backup")
        import shutil

        shutil.copy2(config_path, backup_path)
        print(f"📦 Backed up existing config to {backup_path}")

    # Write new config
    with open(config_path, "w") as f:
        yaml.dump(new_config, f, default_flow_style=False, sort_keys=False)

    print("✅ Updated .pre-commit-config.yaml from poetry dependencies!")
    return True


def main():
    """Main function to sync pre-commit config with poetry."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync pre-commit configuration with poetry dependencies"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes",
    )
    parser.add_argument(
        "--quiet", action="store_true", help="Suppress informational output"
    )
    args = parser.parse_args()

    try:
        # Load poetry dependencies
        poetry_deps = load_poetry_dependencies()
        if not args.quiet:
            print(f"📖 Loaded {len(poetry_deps)} dependencies from pyproject.toml")

        # Generate pre-commit config
        new_config = generate_pre_commit_config(poetry_deps)

        # Update the file
        updated = update_pre_commit_config(new_config, dry_run=args.dry_run)

        if updated and not args.dry_run and not args.quiet:
            print("\n🔧 Next steps:")
            print("1. Review the generated .pre-commit-config.yaml")
            print("2. Run: pre-commit install")
            print("3. Test: pre-commit run --all-files")

        # Show what tools were configured
        configured_tools = [pkg for pkg in poetry_deps.keys() if pkg in HOOK_MAPPINGS]
        if configured_tools and not args.quiet:
            print(
                f"\n🛠️  Configured pre-commit hooks for: {', '.join(configured_tools)}"
            )

        type_deps = get_type_dependencies(poetry_deps)
        if type_deps and not args.quiet:
            print(f"📝 Added type dependencies: {', '.join(type_deps)}")

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
