"""Template for CLI Context Singleton Elimination

This template shows the before/after patterns for eliminating CLI context singletons.
"""

# ===== BEFORE: Singleton Pattern =====

import click

from spec_cli.core.context import get_context


@click.command()
@click.argument("file_path")
def old_add_command(file_path):
    """OLD: Command using singleton context access."""
    # Anti-pattern: Global singleton access
    context = get_context()
    settings = context.settings
    console = context.console

    try:
        console.show_message(f"Adding {file_path}...")
        # Process file with settings
        if settings.debug_enabled:
            console.show_debug(f"Debug mode active for {file_path}")

        # File processing logic here
        console.show_success(f"Added {file_path} successfully")

    except Exception as e:
        console.show_error(f"Failed to add {file_path}: {e}")


# ===== AFTER: Dependency Injection Pattern =====

import click

from spec_cli.core.context import SpecContext
from spec_cli.core.decorators import inject_context


@inject_context
@click.argument("file_path")
def new_add_command(file_path: str, context: SpecContext):
    """NEW: Command using dependency injection."""
    # Target pattern: Injected dependencies
    settings = context.settings
    console = context.console

    try:
        console.show_message(f"Adding {file_path}...")
        # Process file with settings
        if settings.debug_enabled:
            console.show_debug(f"Debug mode active for {file_path}")

        # File processing logic here
        console.show_success(f"Added {file_path} successfully")

    except Exception as e:
        console.show_error(f"Failed to add {file_path}: {e}")


# ===== MIGRATION STEPS =====

"""
Step 1: Update function signature
- Add context parameter with type hint
- Remove any get_context() calls

Step 2: Replace decorator
- Remove @click.command()
- Add @inject_context before @click.argument()

Step 3: Update context access
- Replace get_context() with context parameter
- Access dependencies through context.settings, context.console, etc.

Step 4: Update tests
- Replace singleton context setup with mock context injection
- Use context factories in test fixtures
"""

# ===== TEST MIGRATION EXAMPLE =====


# OLD TEST:
def test_old_add_command():
    """OLD: Test with singleton context setup."""
    from spec_cli.core.context import initialize_context

    # Anti-pattern: Global context setup
    initialize_context(debug=True)

    result = runner.invoke(old_add_command, ["test.txt"])
    assert result.exit_code == 0


# NEW TEST:
def test_new_add_command(mock_context):
    """NEW: Test with injected mock context."""
    # Target pattern: Injected mock context
    mock_context.settings.debug_enabled = True

    result = runner.invoke(new_add_command, ["test.txt"], obj=mock_context)
    assert result.exit_code == 0
