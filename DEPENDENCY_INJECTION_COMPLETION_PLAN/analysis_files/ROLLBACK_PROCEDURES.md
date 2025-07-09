# DEPENDENCY INJECTION MIGRATION - ROLLBACK PROCEDURES

## Emergency Rollback (Any Phase)
```bash
# Immediate rollback to baseline
./rollback_migration.sh

# Validate rollback success
./validate_migration.sh
```

## Phase-Specific Rollback Procedures

### Phase 1: Analysis and Preparation
- No code changes made, rollback not needed
- If validation fails, investigate baseline environment

### Phase 2: Legacy Cleanup
1. Restore backed up files:
   ```bash
   cp spec_cli/config/settings.py.backup spec_cli/config/settings.py
   cp spec_cli/ui/console.py.backup spec_cli/ui/console.py
   cp spec_cli/ui/progress_manager.py.backup spec_cli/ui/progress_manager.py
   ```
2. Run validation: `./validate_migration.sh`
3. Verify all tests pass

### Phase 3: Singleton Call Updates
1. Use git to revert specific changes:
   ```bash
   git checkout HEAD -- spec_cli/utils/test_migration_utils.py
   git checkout HEAD -- spec_cli/cli/commands/diff.py
   git checkout HEAD -- spec_cli/cli/utils.py
   git checkout HEAD -- spec_cli/cli/commands/generation/workflows.py
   ```
2. Run validation: `./validate_migration.sh`
3. Verify all functionality restored

### Phase 4: Final Validation
1. Revert to pre-migration state:
   ```bash
   git checkout HEAD~N -- spec_cli/  # N = number of commits
   ```
2. Run validation: `./validate_migration.sh`
3. Document issues found

## Rollback Validation
After any rollback, verify:
- All 1006 tests pass
- Performance is within baseline
- No import errors
- All original functionality works