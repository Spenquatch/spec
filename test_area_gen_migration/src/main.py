"""Main application module."""

from pathlib import Path


def main():
    """Main application entry point."""
    print("Hello from main!")

    config_path = Path("config.json")
    if config_path.exists():
        print("Config found")
    else:
        print("No config found")


if __name__ == "__main__":
    main()
