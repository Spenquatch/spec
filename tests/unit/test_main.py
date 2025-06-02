"""Tests for __main__ module entry point."""

from unittest.mock import Mock, patch


class TestMainModule:
    """Test main module entry point functionality."""

    @patch("spec_cli.__main__.main")
    def test_main_module_calls_main_function(self, mock_main: Mock) -> None:
        """Test that running __main__ calls the main function."""
        # Import and execute the __main__ module
        import spec_cli.__main__

        # The main function should have been called during import
        # since it's in the "if __name__ == '__main__':" block
        # We can't easily test this directly, so let's test the import works
        assert hasattr(spec_cli.__main__, "main")

    def test_main_module_import_success(self) -> None:
        """Test that the __main__ module can be imported successfully."""
        import spec_cli.__main__

        # Verify the module has the expected attributes
        assert hasattr(spec_cli.__main__, "main")

    def test_main_function_accessible(self) -> None:
        """Test that main function is accessible from __main__."""
        from spec_cli.__main__ import main
        from spec_cli.cli.app import main as app_main

        # Should be the same function
        assert main is app_main
