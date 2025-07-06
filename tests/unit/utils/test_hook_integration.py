"""Unit tests for hook integration utilities."""

import pytest

from spec_cli.utils.hook_integration import (
    HookIntegration,
    HookIntegrationError,
    create_hook_script,
    create_pre_commit_hook,
    get_singleton_detection_hook,
    validate_hook_configuration,
)


class TestHookIntegrationError:
    """Test HookIntegrationError exception class."""

    def test_hook_integration_error_when_message_provided_then_stores_message(self):
        """Test HookIntegrationError stores message correctly."""
        message = "Hook integration failed"
        error = HookIntegrationError(message)

        assert str(error) == message
        assert error.hook_config is None

    def test_hook_integration_error_when_config_provided_then_stores_config(self):
        """Test HookIntegrationError stores hook config correctly."""
        message = "Hook integration failed"
        config = {"hook_name": "test"}
        error = HookIntegrationError(message, config)

        assert str(error) == message
        assert error.hook_config == config


class TestCreatePreCommitHook:
    """Test create_pre_commit_hook function."""

    def test_create_pre_commit_hook_when_valid_path_then_returns_yaml_config(
        self, tmp_path
    ):
        """Test create_pre_commit_hook with valid detection tool path."""
        # Create a test detection tool file
        tool_path = tmp_path / "check_singletons.py"
        tool_path.write_text("#!/usr/bin/env python3\nprint('test')")

        config = create_pre_commit_hook(tool_path)

        assert "singleton-detection" in config
        assert str(tool_path) in config
        assert "repos:" in config
        assert "language: system" in config
        assert "files: ^spec_cli/.*\\.py$" in config

    def test_create_pre_commit_hook_when_invalid_type_then_raises_error(self):
        """Test create_pre_commit_hook with invalid type raises error."""
        with pytest.raises(HookIntegrationError) as exc_info:
            create_pre_commit_hook("invalid_path")

        assert "Expected Path object" in str(exc_info.value)

    def test_create_pre_commit_hook_when_tool_not_exists_then_raises_error(
        self, tmp_path
    ):
        """Test create_pre_commit_hook with non-existent tool raises error."""
        tool_path = tmp_path / "nonexistent.py"

        with pytest.raises(HookIntegrationError) as exc_info:
            create_pre_commit_hook(tool_path)

        assert "Detection tool not found" in str(exc_info.value)
        assert exc_info.value.hook_config is not None
        assert "tool_path" in exc_info.value.hook_config


class TestValidateHookConfiguration:
    """Test validate_hook_configuration function."""

    def test_validate_hook_configuration_when_valid_config_then_returns_true(self):
        """Test validate_hook_configuration with valid configuration."""
        config = {
            "repos": [
                {
                    "repo": "local",
                    "hooks": [
                        {
                            "id": "test-hook",
                            "name": "Test Hook",
                            "entry": "python test.py",
                        }
                    ],
                }
            ]
        }

        result = validate_hook_configuration(config)
        assert result is True

    def test_validate_hook_configuration_when_invalid_type_then_raises_error(self):
        """Test validate_hook_configuration with invalid type raises error."""
        with pytest.raises(HookIntegrationError) as exc_info:
            validate_hook_configuration("invalid")

        assert "Expected dictionary" in str(exc_info.value)

    def test_validate_hook_configuration_when_missing_repos_then_returns_false(self):
        """Test validate_hook_configuration with missing repos returns false."""
        config = {"invalid": "config"}

        result = validate_hook_configuration(config)
        assert result is False

    def test_validate_hook_configuration_when_empty_repos_then_returns_false(self):
        """Test validate_hook_configuration with empty repos returns false."""
        config = {"repos": []}

        result = validate_hook_configuration(config)
        assert result is False

    def test_validate_hook_configuration_when_invalid_repo_type_then_returns_false(
        self,
    ):
        """Test validate_hook_configuration with invalid repo type returns false."""
        config = {"repos": ["invalid"]}

        result = validate_hook_configuration(config)
        assert result is False

    def test_validate_hook_configuration_when_missing_repo_fields_then_returns_false(
        self,
    ):
        """Test validate_hook_configuration with missing repo fields returns false."""
        config = {
            "repos": [
                {"repo": "local"}  # Missing hooks
            ]
        }

        result = validate_hook_configuration(config)
        assert result is False

    def test_validate_hook_configuration_when_invalid_hooks_type_then_returns_false(
        self,
    ):
        """Test validate_hook_configuration with invalid hooks type returns false."""
        config = {"repos": [{"repo": "local", "hooks": "invalid"}]}

        result = validate_hook_configuration(config)
        assert result is False

    def test_validate_hook_configuration_when_invalid_hook_type_then_returns_false(
        self,
    ):
        """Test validate_hook_configuration with invalid hook type returns false."""
        config = {"repos": [{"repo": "local", "hooks": ["invalid"]}]}

        result = validate_hook_configuration(config)
        assert result is False

    def test_validate_hook_configuration_when_missing_hook_fields_then_returns_false(
        self,
    ):
        """Test validate_hook_configuration with missing hook fields returns false."""
        config = {
            "repos": [
                {
                    "repo": "local",
                    "hooks": [
                        {"id": "test"}  # Missing name and entry
                    ],
                }
            ]
        }

        result = validate_hook_configuration(config)
        assert result is False

    def test_validate_hook_configuration_when_invalid_hook_field_types_then_returns_false(
        self,
    ):
        """Test validate_hook_configuration with invalid hook field types returns false."""
        config = {
            "repos": [
                {
                    "repo": "local",
                    "hooks": [
                        {
                            "id": 123,  # Should be string
                            "name": "Test",
                            "entry": "test",
                        }
                    ],
                }
            ]
        }

        result = validate_hook_configuration(config)
        assert result is False


class TestGetSingletonDetectionHook:
    """Test get_singleton_detection_hook function."""

    def test_get_singleton_detection_hook_when_called_then_returns_hook_integration(
        self,
    ):
        """Test get_singleton_detection_hook returns correct HookIntegration."""
        hook = get_singleton_detection_hook()

        assert isinstance(hook, HookIntegration)
        assert hook.hook_name == "singleton-detection"
        assert "check_singletons.py" in hook.hook_command
        assert "^spec_cli/.*\\.py$" in hook.hook_files
        assert hook.hook_language == "system"
        assert "check_singletons.py" in hook.hook_entry


class TestCreateHookScript:
    """Test create_hook_script function."""

    def test_create_hook_script_when_valid_path_then_returns_script_content(
        self, tmp_path
    ):
        """Test create_hook_script with valid detection module path."""
        module_path = tmp_path / "singleton_detection.py"

        script = create_hook_script(module_path)

        assert "#!/usr/bin/env python3" in script
        assert "scan_for_singleton_patterns" in script
        assert "sys.exit" in script
        assert 'if __name__ == "__main__":' in script

    def test_create_hook_script_when_invalid_type_then_raises_error(self):
        """Test create_hook_script with invalid type raises error."""
        with pytest.raises(HookIntegrationError) as exc_info:
            create_hook_script("invalid_path")

        assert "Expected Path object" in str(exc_info.value)

    def test_create_hook_script_when_path_provided_then_includes_error_handling(
        self, tmp_path
    ):
        """Test create_hook_script includes proper error handling."""
        module_path = tmp_path / "singleton_detection.py"

        script = create_hook_script(module_path)

        # Check for import error handling
        assert "except ImportError as e:" in script
        assert "Cannot import singleton detection" in script

        # Check for file checking logic
        assert "Only check Python files" in script
        assert 'if not file_path.suffix == ".py":' in script

        # Check for violation reporting
        assert "Singleton violations found" in script
        assert "FAILED: Found" in script

    def test_create_hook_script_when_path_provided_then_handles_file_operations(
        self, tmp_path
    ):
        """Test create_hook_script handles file operations correctly."""
        module_path = tmp_path / "singleton_detection.py"

        script = create_hook_script(module_path)

        # Check for file existence checks
        assert "if not file_path.exists():" in script
        assert "WARNING: File not found" in script

        # Check for exception handling during scanning
        assert "except Exception as e:" in script
        assert "ERROR checking" in script


class TestHookIntegration:
    """Test HookIntegration dataclass."""

    def test_hook_integration_when_created_then_stores_all_fields(self):
        """Test HookIntegration dataclass stores all fields correctly."""
        hook = HookIntegration(
            hook_name="test-hook",
            hook_command="python test.py",
            hook_files="*.py",
            hook_language="system",
            hook_entry="python test.py",
        )

        assert hook.hook_name == "test-hook"
        assert hook.hook_command == "python test.py"
        assert hook.hook_files == "*.py"
        assert hook.hook_language == "system"
        assert hook.hook_entry == "python test.py"


class TestHookIntegrationErrorHandling:
    """Test error handling scenarios in hook integration."""

    def test_hook_integration_when_detection_system_unavailable_then_handles_gracefully(
        self, tmp_path
    ):
        """Test hook integration handles missing detection system gracefully."""
        # This tests the scenario where the detection system from P3.2b is not available
        script = create_hook_script(tmp_path / "nonexistent.py")

        # The script should include proper error handling for import failures
        assert "except ImportError as e:" in script
        assert "sys.exit(1)" in script

    def test_hook_integration_when_configuration_error_then_raises_hook_integration_error(
        self,
    ):
        """Test hook integration raises HookIntegrationError for configuration errors."""
        # Test invalid configuration scenarios
        with pytest.raises(HookIntegrationError):
            validate_hook_configuration(None)

        with pytest.raises(HookIntegrationError):
            create_pre_commit_hook(None)


class TestHookExecutionScenarios:
    """Test hook execution scenarios."""

    def test_hook_execution_when_singleton_detected_then_prevents_commit(
        self, tmp_path
    ):
        """Test hook script logic prevents commit when singletons detected."""
        script = create_hook_script(tmp_path / "singleton_detection.py")

        # Check that violations cause exit code 1
        assert "return 1" in script
        assert "FAILED: Found" in script
        assert "singleton pattern violations" in script

    def test_hook_execution_when_clean_code_then_allows_commit(self, tmp_path):
        """Test hook script logic allows commit when no singletons detected."""
        script = create_hook_script(tmp_path / "singleton_detection.py")

        # Check that clean code results in exit code 0
        assert "return 0" in script
        lines = script.split("\n")
        return_0_found = any("return 0" in line for line in lines)
        assert return_0_found
