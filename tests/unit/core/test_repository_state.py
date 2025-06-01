import pytest
from pathlib import Path
from unittest.mock import Mock, patch, call
from spec_cli.core.repository_state import (
    RepositoryStateChecker, 
    RepositoryHealth, 
    BranchStatus
)
from spec_cli.config.settings import SpecSettings
from spec_cli.git.repository import SpecGitRepository

class TestRepositoryStateChecker:
    """Tests for RepositoryStateChecker class."""
    
    @pytest.fixture
    def mock_settings(self, tmp_path):
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
    def state_checker(self, mock_settings):
        """Create RepositoryStateChecker instance for testing."""
        with patch('spec_cli.core.repository_state.get_settings', return_value=mock_settings):
            checker = RepositoryStateChecker(mock_settings)
            return checker
    
    def test_repository_state_checker_initialization(self, state_checker, mock_settings):
        """Test RepositoryStateChecker initializes correctly."""
        assert state_checker.settings == mock_settings
        assert isinstance(state_checker.git_repo, SpecGitRepository)
    
    def test_repository_health_check_comprehensive(self, state_checker, tmp_path):
        """Test comprehensive repository health check."""
        # Setup healthy repository
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        spec_dir.mkdir()
        specs_dir.mkdir()
        (spec_dir / "HEAD").write_text("ref: refs/heads/main")
        
        with patch.object(state_checker.git_repo, 'is_initialized', return_value=True):
            with patch.object(state_checker.git_repo, 'get_current_branch', return_value="main"):
                with patch.object(state_checker.git_repo, 'get_recent_commits', return_value=[{"hash": "abc123"}]):
                    health = state_checker.check_repository_health()
        
        # Verify health report structure
        assert "overall_health" in health
        assert "issues" in health
        assert "warnings" in health
        assert "checks" in health
        assert "details" in health
        
        # Verify checks performed
        checks = health["checks"]
        assert "spec_repo_exists" in checks
        assert "spec_dir_exists" in checks
        assert "git_repo_valid" in checks
        assert "branch_status" in checks
        assert "work_tree_valid" in checks
        assert "permissions_ok" in checks
    
    def test_repository_health_check_missing_repository(self, state_checker, tmp_path):
        """Test health check when repository is missing."""
        # Don't create repository directories
        health = state_checker.check_repository_health()
        
        assert health["checks"]["spec_repo_exists"] is False
        assert health["checks"]["git_repo_valid"] is False
        assert len(health["issues"]) > 0
        assert health["overall_health"] in [RepositoryHealth.ERROR, RepositoryHealth.CRITICAL]
    
    def test_repository_health_check_invalid_git_repo(self, state_checker, tmp_path):
        """Test health check when Git repository is invalid."""
        # Create directory but no HEAD file
        spec_dir = tmp_path / ".spec"
        spec_dir.mkdir()
        
        health = state_checker.check_repository_health()
        
        assert health["checks"]["spec_repo_exists"] is True
        assert "not a valid Git repository" in " ".join(health["issues"])
    
    def test_branch_cleanliness_detection(self, state_checker):
        """Test branch cleanliness detection."""
        # Test clean branch
        with patch.object(state_checker.git_repo, 'has_uncommitted_changes', return_value=False):
            with patch.object(state_checker.git_repo, 'has_untracked_files', return_value=False):
                with patch.object(state_checker.git_repo, 'has_staged_changes', return_value=False):
                    status = state_checker.check_branch_cleanliness()
                    assert status == BranchStatus.CLEAN
        
        # Test uncommitted changes
        with patch.object(state_checker.git_repo, 'has_uncommitted_changes', return_value=True):
            status = state_checker.check_branch_cleanliness()
            assert status == BranchStatus.UNCOMMITTED_CHANGES
        
        # Test untracked files
        with patch.object(state_checker.git_repo, 'has_uncommitted_changes', return_value=False):
            with patch.object(state_checker.git_repo, 'has_untracked_files', return_value=True):
                status = state_checker.check_branch_cleanliness()
                assert status == BranchStatus.UNTRACKED_FILES
        
        # Test staged changes
        with patch.object(state_checker.git_repo, 'has_uncommitted_changes', return_value=False):
            with patch.object(state_checker.git_repo, 'has_untracked_files', return_value=False):
                with patch.object(state_checker.git_repo, 'has_staged_changes', return_value=True):
                    status = state_checker.check_branch_cleanliness()
                    assert status == BranchStatus.STAGED_CHANGES
    
    def test_branch_cleanliness_exception_handling(self, state_checker):
        """Test branch cleanliness check handles exceptions."""
        with patch.object(state_checker.git_repo, 'has_uncommitted_changes', side_effect=Exception("Git error")):
            status = state_checker.check_branch_cleanliness()
            assert status == BranchStatus.UNKNOWN
    
    def test_safety_validation_for_operations(self, state_checker):
        """Test safety validation for spec operations."""
        # Test safe repository
        with patch.object(state_checker, 'check_repository_health') as mock_health:
            mock_health.return_value = {
                "overall_health": RepositoryHealth.HEALTHY,
                "checks": {
                    "spec_repo_exists": True,
                    "git_repo_valid": True,
                    "permissions_ok": True,
                }
            }
            
            assert state_checker.is_safe_for_spec_operations() is True
        
        # Test unsafe repository (critical health)
        with patch.object(state_checker, 'check_repository_health') as mock_health:
            mock_health.return_value = {
                "overall_health": RepositoryHealth.CRITICAL,
                "checks": {}
            }
            
            assert state_checker.is_safe_for_spec_operations() is False
        
        # Test missing repository
        with patch.object(state_checker, 'check_repository_health') as mock_health:
            mock_health.return_value = {
                "overall_health": RepositoryHealth.WARNING,
                "checks": {
                    "spec_repo_exists": False,
                    "git_repo_valid": False,
                    "permissions_ok": True,
                }
            }
            
            assert state_checker.is_safe_for_spec_operations() is False
        
        # Test permission issues
        with patch.object(state_checker, 'check_repository_health') as mock_health:
            mock_health.return_value = {
                "overall_health": RepositoryHealth.WARNING,
                "checks": {
                    "spec_repo_exists": True,
                    "git_repo_valid": True,
                    "permissions_ok": False,
                }
            }
            
            assert state_checker.is_safe_for_spec_operations() is False
    
    def test_safety_validation_exception_handling(self, state_checker):
        """Test safety validation handles exceptions."""
        with patch.object(state_checker, 'check_repository_health', side_effect=Exception("Health check failed")):
            assert state_checker.is_safe_for_spec_operations() is False
    
    def test_pre_operation_state_validation(self, state_checker):
        """Test pre-operation state validation."""
        # Test validation for clean operation
        with patch.object(state_checker, 'check_repository_health') as mock_health:
            mock_health.return_value = {
                "overall_health": RepositoryHealth.HEALTHY,
                "checks": {
                    "spec_repo_exists": True,
                    "git_repo_valid": True,
                    "permissions_ok": True,
                    "branch_status": BranchStatus.CLEAN,
                },
                "issues": []
            }
            
            issues = state_checker.validate_pre_operation_state("commit")
            assert len(issues) == 0
        
        # Test validation with critical health
        with patch.object(state_checker, 'check_repository_health') as mock_health:
            mock_health.return_value = {
                "overall_health": RepositoryHealth.CRITICAL,
                "checks": {},
                "issues": []
            }
            
            issues = state_checker.validate_pre_operation_state("commit")
            assert len(issues) > 0
            assert any("critical state" in issue for issue in issues)
        
        # Test validation with missing repository
        with patch.object(state_checker, 'check_repository_health') as mock_health:
            mock_health.return_value = {
                "overall_health": RepositoryHealth.ERROR,
                "checks": {
                    "spec_repo_exists": False,
                    "git_repo_valid": False,
                    "permissions_ok": False,
                },
                "issues": ["Repository missing"]
            }
            
            issues = state_checker.validate_pre_operation_state("add")
            assert len(issues) > 0
            assert any("not initialized" in issue for issue in issues)
            assert any("not valid" in issue for issue in issues)
            assert any("permissions" in issue for issue in issues)
        
        # Test operation-specific validation (dirty branch for commit)
        with patch.object(state_checker, 'check_repository_health') as mock_health:
            mock_health.return_value = {
                "overall_health": RepositoryHealth.WARNING,
                "checks": {
                    "spec_repo_exists": True,
                    "git_repo_valid": True,
                    "permissions_ok": True,
                    "branch_status": BranchStatus.UNCOMMITTED_CHANGES,
                },
                "issues": []
            }
            
            issues = state_checker.validate_pre_operation_state("commit")
            assert len(issues) > 0
            assert any("not clean" in issue for issue in issues)
    
    def test_pre_operation_validation_exception_handling(self, state_checker):
        """Test pre-operation validation handles exceptions."""
        with patch.object(state_checker, 'check_repository_health', side_effect=Exception("Validation failed")):
            issues = state_checker.validate_pre_operation_state("test")
            assert len(issues) > 0
            assert any("validation failed" in issue.lower() for issue in issues)
    
    def test_repository_summary_generation(self, state_checker):
        """Test repository summary generation."""
        with patch.object(state_checker, 'check_repository_health') as mock_health:
            with patch.object(state_checker, 'is_safe_for_spec_operations', return_value=True):
                mock_health.return_value = {
                    "overall_health": RepositoryHealth.HEALTHY,
                    "checks": {
                        "spec_repo_exists": True,
                        "spec_dir_exists": True,
                        "branch_status": BranchStatus.CLEAN,
                    },
                    "issues": [],
                    "warnings": ["Minor warning"],
                    "details": {"current_branch": "main"}
                }
                
                summary = state_checker.get_repository_summary()
                
                assert summary["initialized"] is True
                assert summary["healthy"] is True
                assert summary["safe_for_operations"] is True
                assert summary["branch_clean"] is True
                assert summary["specs_dir_exists"] is True
                assert summary["issue_count"] == 0
                assert summary["warning_count"] == 1
                assert summary["current_branch"] == "main"
    
    def test_repository_summary_exception_handling(self, state_checker):
        """Test repository summary handles exceptions."""
        with patch.object(state_checker, 'check_repository_health', side_effect=Exception("Summary failed")):
            summary = state_checker.get_repository_summary()
            
            assert summary["initialized"] is False
            assert summary["healthy"] is False
            assert summary["safe_for_operations"] is False
            assert "error" in summary
    
    def test_permission_checking(self, state_checker, tmp_path):
        """Test permission checking functionality."""
        # Create directories for testing
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        spec_dir.mkdir()
        specs_dir.mkdir()
        
        health_report = {
            "checks": {},
            "issues": [],
            "details": {}
        }
        
        # Test with proper permissions
        state_checker._check_permissions(health_report)
        
        # Should detect permissions properly
        assert "permissions_ok" in health_report["checks"]
        assert "permission_issues" in health_report["details"]
    
    @patch('os.access')
    def test_permission_checking_failure(self, mock_access, state_checker, tmp_path):
        """Test permission checking when access is denied."""
        # Setup directories
        spec_dir = tmp_path / ".spec"
        specs_dir = tmp_path / ".specs"
        spec_dir.mkdir()
        specs_dir.mkdir()
        
        # Mock access to return False (no permissions)
        mock_access.return_value = False
        
        health_report = {
            "checks": {},
            "issues": [],
            "details": {}
        }
        
        state_checker._check_permissions(health_report)
        
        assert health_report["checks"]["permissions_ok"] is False
        assert len(health_report["issues"]) > 0
        assert len(health_report["details"]["permission_issues"]) > 0
    
    def test_specs_directory_content_counting(self, state_checker, tmp_path):
        """Test .specs directory content counting."""
        # Create .specs directory with some content
        specs_dir = tmp_path / ".specs"
        specs_dir.mkdir()
        (specs_dir / "file1.md").write_text("content")
        (specs_dir / "subdir").mkdir()
        (specs_dir / "subdir" / "file2.md").write_text("content")
        
        health_report = {
            "checks": {},
            "details": {},
            "warnings": []
        }
        
        state_checker._check_specs_directory(health_report)
        
        assert health_report["checks"]["spec_dir_exists"] is True
        assert health_report["details"]["specs_content_count"] == 3  # 2 files + 1 dir
    
    def test_git_repository_additional_info_gathering(self, state_checker, tmp_path):
        """Test additional Git repository information gathering."""
        with patch.object(state_checker.git_repo, 'is_initialized', return_value=True):
            with patch.object(state_checker.git_repo, 'get_current_branch', return_value="feature-branch"):
                with patch.object(state_checker.git_repo, 'get_recent_commits', return_value=[{"hash": "abc"}, {"hash": "def"}]):
                    
                    health_report = {
                        "checks": {},
                        "details": {},
                        "warnings": []
                    }
                    
                    state_checker._check_git_repository(health_report)
                    
                    assert health_report["checks"]["git_repo_valid"] is True
                    assert health_report["details"]["current_branch"] == "feature-branch"
                    assert health_report["details"]["recent_commits"] == 2
    
    def test_git_repository_info_gathering_errors(self, state_checker):
        """Test Git repository info gathering handles errors."""
        with patch.object(state_checker.git_repo, 'is_initialized', return_value=True):
            with patch.object(state_checker.git_repo, 'get_current_branch', side_effect=Exception("Branch error")):
                with patch.object(state_checker.git_repo, 'get_recent_commits', side_effect=Exception("Commit error")):
                    
                    health_report = {
                        "checks": {},
                        "details": {},
                        "warnings": []
                    }
                    
                    state_checker._check_git_repository(health_report)
                    
                    assert health_report["checks"]["git_repo_valid"] is True
                    assert len(health_report["warnings"]) == 2  # One for branch, one for commits
                    assert any("current branch" in warning for warning in health_report["warnings"])
                    assert any("recent commits" in warning for warning in health_report["warnings"])