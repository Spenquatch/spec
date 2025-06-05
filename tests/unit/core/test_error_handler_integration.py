"""Integration tests for ErrorHandler with actual modules."""

from unittest.mock import patch

from spec_cli.cli.utils import cli_error_handler


class TestCliUtilsIntegration:
    """Test ErrorHandler integration in CLI utils."""

    def test_cli_error_handler_when_created_then_has_correct_context(self):
        """Test that CLI error handler has the expected default context."""
        assert cli_error_handler.default_context["module"] == "cli"
        assert cli_error_handler.default_context["component"] == "utils"

    def test_cli_error_handler_when_used_then_includes_context_in_reports(self):
        """Test that CLI error handler includes module context in reports."""
        with patch("spec_cli.utils.error_handler.debug_logger") as mock_logger:
            exc = ValueError("Test CLI error")
            cli_error_handler.report(exc, "test CLI operation")

            mock_logger.log.assert_called_once()
            call_args = mock_logger.log.call_args
            kwargs = call_args[1]
            assert kwargs["module"] == "cli"
            assert kwargs["component"] == "utils"
            assert kwargs["operation"] == "test CLI operation"
