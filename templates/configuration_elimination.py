"""Template for Configuration Manager Singleton Elimination

This template shows the before/after patterns for eliminating configuration singletons.
"""

# ===== BEFORE: Singleton Pattern =====

from spec_cli.config.settings import get_settings


def old_process_files():
    """OLD: Function using singleton configuration access."""
    # Anti-pattern: Global singleton access
    settings = get_settings()

    max_file_size = settings.max_file_size
    debug_mode = settings.debug_enabled
    output_format = settings.output_format

    for file_path in settings.input_files:
        if file_path.stat().st_size > max_file_size:
            if debug_mode:
                print(f"Skipping large file: {file_path}")
            continue

        process_single_file(file_path, output_format)


def process_single_file(file_path, format):
    """Helper function that also needs configuration."""
    # Anti-pattern: Nested singleton access
    settings = get_settings()

    if settings.validate_files:
        validate_file_content(file_path)

    # Process file logic here
    pass


# ===== AFTER: Factory Pattern with Injection =====

from spec_cli.core.context import SpecContext


def new_process_files(context: SpecContext):
    """NEW: Function using injected configuration."""
    # Target pattern: Configuration through context
    settings = context.settings

    max_file_size = settings.max_file_size
    debug_mode = settings.debug_enabled

    for file_path in settings.input_files:
        if file_path.stat().st_size > max_file_size:
            if debug_mode:
                context.console.show_debug(f"Skipping large file: {file_path}")
            continue

        process_single_file(file_path, format, context)


def process_single_file(file_path, format, context: SpecContext):
    """Helper function with injected configuration."""
    # Target pattern: Configuration passed through
    settings = context.settings

    if settings.validate_files:
        validate_file_content(file_path, context)

    # Process file logic here
    pass


# ===== CONTEXT FACTORY PATTERN =====

from spec_cli.config.settings import SettingsFactory


class SpecContext:
    """Context with factory-based configuration."""

    def __init__(self, config_path=None, overrides=None):
        self._settings_factory = SettingsFactory(config_path, overrides)
        self._settings = None

    @property
    def settings(self):
        """Lazy-loaded settings from factory."""
        if self._settings is None:
            self._settings = self._settings_factory.create_settings()
        return self._settings


# ===== MIGRATION STEPS =====

"""
Step 1: Create SettingsFactory
- Move configuration loading logic to factory
- Support configuration overrides and validation
- Implement lazy loading for performance

Step 2: Update Context
- Add settings property that uses factory
- Remove any global settings access from context
- Support configuration hot-reloading if needed

Step 3: Update Function Signatures
- Add context parameter to all functions needing configuration
- Remove get_settings() calls
- Access configuration through context.settings

Step 4: Update Helper Functions
- Pass context through to helper functions
- Avoid passing individual config values (pass context instead)
- Maintain single source of configuration truth

Step 5: Update Tests
- Use factory pattern in test fixtures
- Support configuration overrides for testing
- Validate configuration isolation between tests
"""

# ===== TEST MIGRATION EXAMPLE =====


# OLD TEST:
def test_old_process_files():
    """OLD: Test with global configuration setup."""
    from spec_cli.config.settings import configure_settings

    # Anti-pattern: Global configuration setup
    configure_settings(
        {
            "max_file_size": 1024,
            "debug_enabled": True,
            "input_files": [Path("test.txt")],
        }
    )

    old_process_files()
    # Validation logic


# NEW TEST:
def test_new_process_files():
    """NEW: Test with factory-based configuration."""
    # Target pattern: Configuration through factory
    settings_factory = SettingsFactory(
        overrides={
            "max_file_size": 1024,
            "debug_enabled": True,
            "input_files": [Path("test.txt")],
        }
    )

    context = SpecContext()
    context._settings_factory = settings_factory

    new_process_files(context)
    # Validation logic


# FIXTURE EXAMPLE:
@pytest.fixture
def context_with_config():
    """Test fixture providing configured context."""
    factory = SettingsFactory(
        overrides={
            "debug_enabled": True,
            "max_file_size": 2048,
            "validate_files": False,
        }
    )

    context = SpecContext()
    context._settings_factory = factory
    return context
