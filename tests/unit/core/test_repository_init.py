import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest

from spec_cli.config.settings import SpecSettings
from spec_cli.core.repository_init import SpecRepositoryInitializer
from spec_cli.core.repository_state import RepositoryHealth
from spec_cli.file_system.directory_manager import DirectoryManager
from spec_cli.git.repository import SpecGitRepository


class TestSpecRepositoryInitializer:
    """Tests for SpecRepositoryInitializer class."""

    @pytest.fixture
    def mock_settings(self, tmp_path: Path) -> Mock:
        """Create mock settings for testing."""
        settings = Mock(spec=SpecSettings)
        settings.spec_dir = tmp_path / ".spec"
        settings.specs_dir = tmp_path / ".specs"
        settings.index_file = tmp_path / ".spec-index"
        settings.ignore_file = tmp_path / ".specignore"
        settings.template_file = tmp_path / ".spectemplate"
        settings.config_file = tmp_path / ".specconfig"
        return settings

    @pytest.fixture
    def initializer(self, mock_settings: Mock) -> SpecRepositoryInitializer:
        """Create SpecRepositoryInitializer instance for testing."""
        with patch(
            "spec_cli.core.repository_init.get_settings", return_value=mock_settings
        ):
            init = SpecRepositoryInitializer(mock_settings)
            return init

    def test_repository_initializer_initialization(
        self, initializer: SpecRepositoryInitializer, mock_settings: Mock
    ) -> None:
        """Test SpecRepositoryInitializer initializes correctly."""
        assert initializer.settings == mock_settings
        assert isinstance(initializer.git_repo, SpecGitRepository)
        assert isinstance(initializer.directory_manager, DirectoryManager)
        assert hasattr(initializer, "state_checker")

    def test_repository_initialization_from_scratch(
        self, initializer: SpecRepositoryInitializer, tmp_path: Path
    ) -> None:
        """Test repository initialization from scratch."""
        # Mock state checker to indicate no existing repository
        mock_health = {
            "checks": {"spec_repo_exists": False, "spec_dir_exists": False},
            "overall_health": RepositoryHealth.ERROR,
        }

        with patch.object(
            initializer.state_checker,
            "check_repository_health",
            return_value=mock_health,
        ):
            with patch.object(initializer.git_repo, "initialize") as mock_init:
                with patch.object(
                    initializer.directory_manager, "ensure_specs_directory"
                ) as mock_ensure:
                    with patch.object(
                        initializer.directory_manager, "setup_ignore_files"
                    ) as mock_ignore:
                        with patch.object(
                            initializer.directory_manager, "update_main_gitignore"
                        ) as mock_gitignore:
                            with patch.object(
                                initializer, "_verify_initialization"
                            ) as mock_verify:
                                with patch.object(
                                    initializer, "_create_initial_commit"
                                ) as mock_commit:
                                    result = initializer.initialize_repository()

                                    assert result["success"] is True
                                    assert len(result["created"]) > 0
                                    assert len(result["errors"]) == 0

                                    # Verify all initialization steps were called
                                    mock_init.assert_called_once()
                                    mock_ensure.assert_called_once()
                                    mock_ignore.assert_called_once()
                                    mock_gitignore.assert_called_once()
                                    mock_verify.assert_called_once()
                                    mock_commit.assert_called_once()

    def test_repository_initialization_with_force(
        self, initializer: SpecRepositoryInitializer, tmp_path: Path
    ) -> None:
        """Test repository initialization with force flag."""
        # Create existing repository
        spec_dir = tmp_path / ".spec"
        spec_dir.mkdir()

        mock_health = {
            "checks": {"spec_repo_exists": True},
            "overall_health": RepositoryHealth.HEALTHY,
        }

        with patch.object(
            initializer.state_checker,
            "check_repository_health",
            return_value=mock_health,
        ):
            with patch("shutil.rmtree") as mock_rmtree:
                with patch.object(initializer.git_repo, "initialize") as mock_init:
                    with patch.object(initializer, "_initialize_specs_directory"):
                        with patch.object(initializer, "_setup_ignore_files"):
                            with patch.object(initializer, "_create_initial_commit"):
                                with patch.object(
                                    initializer, "_update_main_gitignore"
                                ):
                                    with patch.object(
                                        initializer, "_verify_initialization"
                                    ):
                                        result = initializer.initialize_repository(
                                            force=True
                                        )

                                        # Should remove existing repository and recreate
                                        mock_rmtree.assert_called_once_with(spec_dir)
                                        mock_init.assert_called_once()
                                        assert any(
                                            "Removed existing repository" in item
                                            for item in result["created"]
                                        )

    def test_repository_initialization_existing_healthy(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test initialization skips when repository is already healthy."""
        mock_health = {
            "checks": {"spec_repo_exists": True},
            "overall_health": RepositoryHealth.HEALTHY,
        }

        with patch.object(
            initializer.state_checker,
            "check_repository_health",
            return_value=mock_health,
        ):
            result = initializer.initialize_repository(force=False)

            assert result["success"] is True
            assert len(result["skipped"]) > 0
            assert any("already exists" in item for item in result["skipped"])

    def test_git_repository_configuration(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test Git repository configuration."""
        result: Dict[str, Any] = {"warnings": [], "created": []}

        with patch.object(initializer.git_repo, "run_git_command") as mock_run:
            initializer._configure_git_repository(result)

            # Verify configuration commands were called
            expected_configs = [
                ["config", "user.name", "Spec CLI"],
                ["config", "user.email", "spec-cli@local"],
                ["config", "core.autocrlf", "input"],
                ["config", "core.safecrlf", "true"],
            ]

            for expected_config in expected_configs:
                mock_run.assert_any_call(expected_config)

            assert any(
                "Configured Git repository" in item for item in result["created"]
            )

    def test_git_repository_configuration_errors(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test Git repository configuration handles errors."""
        result: Dict[str, Any] = {"warnings": [], "created": []}

        with patch.object(
            initializer.git_repo,
            "run_git_command",
            side_effect=Exception("Config failed"),
        ) as _mock_run:
            initializer._configure_git_repository(result)

            # Should add warnings for failed configurations
            assert len(result["warnings"]) > 0
            assert any(
                "Could not set Git config" in warning for warning in result["warnings"]
            )

    def test_specs_directory_creation(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test .specs directory creation."""
        result: Dict[str, Any] = {"errors": [], "created": []}

        with patch.object(
            initializer.directory_manager, "ensure_specs_directory"
        ) as mock_ensure:
            initializer._initialize_specs_directory(result)

            mock_ensure.assert_called_once()
            assert any("Created .specs directory" in item for item in result["created"])

    def test_specs_directory_creation_error(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test .specs directory creation handles errors."""
        result: Dict[str, Any] = {"errors": [], "created": []}

        with patch.object(
            initializer.directory_manager,
            "ensure_specs_directory",
            side_effect=Exception("Directory failed"),
        ):
            initializer._initialize_specs_directory(result)

            assert len(result["errors"]) > 0
            assert any(
                "Failed to create .specs directory" in error
                for error in result["errors"]
            )

    def test_ignore_files_setup(self, initializer: SpecRepositoryInitializer) -> None:
        """Test ignore files setup."""
        result: Dict[str, Any] = {"warnings": [], "created": []}

        with patch.object(
            initializer.directory_manager, "setup_ignore_files"
        ) as mock_setup:
            initializer._setup_ignore_files(result)

            mock_setup.assert_called_once()
            assert any("Created .specignore file" in item for item in result["created"])

    def test_ignore_files_setup_error(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test ignore files setup handles errors."""
        result: Dict[str, Any] = {"warnings": [], "created": []}

        with patch.object(
            initializer.directory_manager,
            "setup_ignore_files",
            side_effect=Exception("Ignore failed"),
        ):
            initializer._setup_ignore_files(result)

            assert len(result["warnings"]) > 0
            assert any(
                "Could not setup ignore files" in warning
                for warning in result["warnings"]
            )

    def test_initial_commit_creation(
        self, initializer: SpecRepositoryInitializer, tmp_path: Path
    ) -> None:
        """Test initial commit creation."""
        result: Dict[str, Any] = {"created": [], "warnings": [], "skipped": []}

        # Mock no existing commits
        with patch.object(initializer.git_repo, "get_recent_commits", return_value=[]):
            with patch.object(initializer.git_repo, "add_files") as mock_add:
                with patch.object(
                    initializer.git_repo, "commit", return_value="abc123def"
                ) as mock_commit:
                    # Mock README creation
                    with patch("pathlib.Path.exists", return_value=False):
                        with patch("pathlib.Path.write_text") as mock_write:
                            initializer._create_initial_commit(result)

                            mock_write.assert_called_once()
                            mock_add.assert_called_once_with(["README.md"])
                            mock_commit.assert_called_once_with(
                                "Initial spec repository setup"
                            )
                            assert any(
                                "Created README" in item for item in result["created"]
                            )
                            assert any(
                                "Created initial commit" in item
                                for item in result["created"]
                            )

    def test_initial_commit_skipped_existing_commits(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test initial commit is skipped when commits already exist."""
        result: Dict[str, Any] = {"created": [], "warnings": [], "skipped": []}

        # Mock existing commits
        with patch.object(
            initializer.git_repo,
            "get_recent_commits",
            return_value=[{"hash": "existing"}],
        ):
            initializer._create_initial_commit(result)

            assert any("already has commits" in item for item in result["skipped"])

    def test_initial_commit_creation_error(
        self, initializer: SpecRepositoryInitializer, tmp_path: Path
    ) -> None:
        """Test initial commit creation handles errors."""
        result: Dict[str, Any] = {"created": [], "warnings": [], "skipped": []}

        with patch.object(initializer.git_repo, "get_recent_commits", return_value=[]):
            with patch.object(
                initializer.git_repo, "add_files", side_effect=Exception("Add failed")
            ):
                with patch("pathlib.Path.exists", return_value=False):
                    with patch("pathlib.Path.write_text"):
                        initializer._create_initial_commit(result)

                        assert len(result["warnings"]) > 0
                        assert any(
                            "Could not create initial commit" in warning
                            for warning in result["warnings"]
                        )

    def test_repository_bootstrap_structure(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test repository bootstrap structure creation."""
        with patch.object(
            initializer.state_checker, "is_safe_for_spec_operations", return_value=True
        ):
            with patch.object(initializer, "_create_common_directories") as mock_dirs:
                with patch.object(
                    initializer, "_setup_configuration_files"
                ) as mock_config:
                    with patch.object(
                        initializer, "_create_example_templates"
                    ) as mock_templates:
                        result = initializer.bootstrap_repository_structure()

                        assert result["success"] is True
                        mock_dirs.assert_called_once()
                        mock_config.assert_called_once()
                        mock_templates.assert_called_once()

    def test_bootstrap_unsafe_repository(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test bootstrap fails when repository is unsafe."""
        with patch.object(
            initializer.state_checker, "is_safe_for_spec_operations", return_value=False
        ):
            result = initializer.bootstrap_repository_structure()

            assert result["success"] is False
            assert len(result["errors"]) > 0
            assert any("not safe for operations" in error for error in result["errors"])

    def test_common_directories_creation(
        self, initializer: SpecRepositoryInitializer, tmp_path: Path
    ) -> None:
        """Test common directories creation."""
        result: Dict[str, Any] = {"created": [], "warnings": []}

        initializer._create_common_directories(result)

        # Verify common directories were created
        expected_dirs = ["docs", "src", "tests", "config"]
        for dir_name in expected_dirs:
            dir_path = initializer.settings.specs_dir / dir_name
            assert dir_path.exists()
            assert any(
                f"Created directory: {dir_path}" in item for item in result["created"]
            )

    def test_common_directories_creation_error(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test common directories creation handles errors."""
        result: Dict[str, Any] = {"created": [], "warnings": []}

        # Mock mkdir to fail
        with patch("pathlib.Path.mkdir", side_effect=Exception("Mkdir failed")):
            initializer._create_common_directories(result)

            assert len(result["warnings"]) > 0
            assert any(
                "Could not create directory" in warning
                for warning in result["warnings"]
            )

    def test_configuration_files_setup(
        self, initializer: SpecRepositoryInitializer, tmp_path: Path
    ) -> None:
        """Test configuration files setup."""
        result: Dict[str, Any] = {"created": [], "warnings": []}

        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.write_text") as mock_write:
                initializer._setup_configuration_files(result)

                mock_write.assert_called_once()
                # Verify JSON structure
                written_data = mock_write.call_args[0][0]
                config_data = json.loads(written_data)
                assert config_data["version"] == "1.0"
                assert "settings" in config_data
                assert any("Created config file" in item for item in result["created"])

    def test_configuration_files_setup_error(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test configuration files setup handles errors."""
        result: Dict[str, Any] = {"created": [], "warnings": []}

        with patch("json.dumps", side_effect=Exception("JSON failed")):
            initializer._setup_configuration_files(result)

            assert len(result["warnings"]) > 0
            assert any(
                "Could not create configuration files" in warning
                for warning in result["warnings"]
            )

    def test_example_templates_creation(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test example templates creation."""
        result: Dict[str, Any] = {"created": [], "warnings": []}

        with patch("pathlib.Path.exists", return_value=False):
            with patch("pathlib.Path.write_text") as mock_write:
                initializer._create_example_templates(result)

                mock_write.assert_called_once()
                template_content = mock_write.call_args[0][0]
                assert "Example Spec Template" in template_content
                assert "{{{purpose}}}" in template_content
                assert any(
                    "Created example template" in item for item in result["created"]
                )

    def test_example_templates_creation_error(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test example templates creation handles errors."""
        result: Dict[str, Any] = {"created": [], "warnings": []}

        with patch("pathlib.Path.write_text", side_effect=Exception("Template failed")):
            initializer._create_example_templates(result)

            assert len(result["warnings"]) > 0
            assert any(
                "Could not create example templates" in warning
                for warning in result["warnings"]
            )

    def test_initialization_requirements_checking(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test initialization requirements checking."""
        with patch("subprocess.run") as mock_run:
            # Mock successful Git version check
            mock_run.return_value = Mock(stdout="git version 2.34.1")

            issues = initializer.check_initialization_requirements()

            # Should pass all checks
            assert len(issues) == 0
            mock_run.assert_called_once()

    def test_initialization_requirements_git_missing(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test requirements check when Git is missing."""
        with patch("subprocess.run", side_effect=FileNotFoundError("Git not found")):
            issues = initializer.check_initialization_requirements()

            assert len(issues) > 0
            assert any("Git is not installed" in issue for issue in issues)

    def test_initialization_requirements_permission_error(
        self, initializer: SpecRepositoryInitializer, tmp_path: Path
    ) -> None:
        """Test requirements check with permission errors."""
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(stdout="git version 2.34.1")

            # Mock permission check to fail
            with patch("os.access", return_value=False):
                issues = initializer.check_initialization_requirements()

                assert len(issues) > 0
                assert any("No write permission" in issue for issue in issues)

    def test_initialization_plan_generation(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test initialization plan generation."""
        mock_health = {"checks": {"spec_repo_exists": False, "spec_dir_exists": False}}

        with patch.object(
            initializer.state_checker,
            "check_repository_health",
            return_value=mock_health,
        ):
            with patch.object(
                initializer.state_checker,
                "get_repository_summary",
                return_value={"initialized": False},
            ):
                with patch.object(
                    initializer, "check_initialization_requirements", return_value=[]
                ):
                    plan = initializer.get_initialization_plan()

                    assert "actions" in plan
                    assert "requirements" in plan
                    assert "current_state" in plan
                    assert "estimated_time" in plan

                    # Should include creation actions for missing components
                    assert any(
                        "Create Git repository" in action for action in plan["actions"]
                    )
                    assert any(
                        "Create .specs directory" in action
                        for action in plan["actions"]
                    )

    def test_full_initialization_workflow(
        self, initializer: SpecRepositoryInitializer, tmp_path: Path
    ) -> None:
        """Test full initialization workflow integration."""
        # Mock all dependencies to succeed
        mock_health_before = {
            "checks": {"spec_repo_exists": False},
            "overall_health": RepositoryHealth.ERROR,
        }
        mock_health_after = {
            "checks": {"spec_repo_exists": True},
            "overall_health": RepositoryHealth.HEALTHY,
            "issues": [],
        }

        with patch.object(
            initializer.state_checker,
            "check_repository_health",
            side_effect=[mock_health_before, mock_health_after],
        ):
            with patch.object(initializer.git_repo, "initialize"):
                with patch.object(initializer.git_repo, "run_git_command"):
                    with patch.object(
                        initializer.git_repo, "get_recent_commits", return_value=[]
                    ):
                        with patch.object(initializer.git_repo, "add_files"):
                            with patch.object(
                                initializer.git_repo, "commit", return_value="abc123"
                            ):
                                with patch.object(
                                    initializer.directory_manager,
                                    "ensure_specs_directory",
                                ):
                                    with patch.object(
                                        initializer.directory_manager,
                                        "setup_ignore_files",
                                    ):
                                        with patch.object(
                                            initializer.directory_manager,
                                            "update_main_gitignore",
                                        ):
                                            # Mock README creation
                                            with patch(
                                                "pathlib.Path.exists",
                                                return_value=False,
                                            ):
                                                with patch("pathlib.Path.write_text"):
                                                    result = initializer.initialize_repository()

                                                    assert result["success"] is True
                                                    assert len(result["created"]) > 0
                                                    assert len(result["errors"]) == 0

    def test_error_recovery_and_cleanup(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test error recovery and cleanup during initialization."""
        # Mock state checker to fail
        with patch.object(
            initializer.state_checker,
            "check_repository_health",
            side_effect=Exception("Health check failed"),
        ):
            result = initializer.initialize_repository()

            assert result["success"] is False
            assert len(result["errors"]) > 0
            assert any(
                "Repository initialization failed" in error
                for error in result["errors"]
            )

    def test_initialization_verification_success(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test initialization verification when successful."""
        result: Dict[str, Any] = {"created": [], "errors": []}

        mock_health = {"overall_health": RepositoryHealth.HEALTHY, "issues": []}

        with patch.object(
            initializer.state_checker,
            "check_repository_health",
            return_value=mock_health,
        ):
            initializer._verify_initialization(result)

            assert any("verified" in item.lower() for item in result["created"])
            assert len(result["errors"]) == 0

    def test_initialization_verification_failure(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test initialization verification when failed."""
        result: Dict[str, Any] = {"created": [], "errors": []}

        mock_health = {
            "overall_health": RepositoryHealth.ERROR,
            "issues": ["Repository corrupted"],
        }

        with patch.object(
            initializer.state_checker,
            "check_repository_health",
            return_value=mock_health,
        ):
            initializer._verify_initialization(result)

            assert len(result["errors"]) > 0
            assert any("verification failed" in error for error in result["errors"])

    def test_initialization_verification_exception(
        self, initializer: SpecRepositoryInitializer
    ) -> None:
        """Test initialization verification handles exceptions."""
        result: Dict[str, Any] = {"created": [], "errors": [], "warnings": []}

        with patch.object(
            initializer.state_checker,
            "check_repository_health",
            side_effect=Exception("Verify failed"),
        ):
            initializer._verify_initialization(result)

            assert len(result["warnings"]) > 0
            assert any(
                "Could not verify initialization" in warning
                for warning in result["warnings"]
            )
