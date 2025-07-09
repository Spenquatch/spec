#!/bin/bash
set -e

echo "======================================"
echo "DEPENDENCY INJECTION MIGRATION ROLLBACK"
echo "======================================"
echo "Started: $(date)"
echo ""

# Restore backup files
echo "=== RESTORING BACKUP FILES ==="
if [ -f spec_cli/core/context.py.backup ]; then
    cp spec_cli/core/context.py.backup spec_cli/core/context.py
    echo "Restored: spec_cli/core/context.py"
fi

if [ -f spec_cli/config/settings.py.backup ]; then
    cp spec_cli/config/settings.py.backup spec_cli/config/settings.py
    echo "Restored: spec_cli/config/settings.py"
fi

if [ -f spec_cli/ui/console.py.backup ]; then
    cp spec_cli/ui/console.py.backup spec_cli/ui/console.py
    echo "Restored: spec_cli/ui/console.py"
fi

if [ -f spec_cli/ui/progress_manager.py.backup ]; then
    cp spec_cli/ui/progress_manager.py.backup spec_cli/ui/progress_manager.py
    echo "Restored: spec_cli/ui/progress_manager.py"
fi

echo ""
echo "=== VALIDATING ROLLBACK ==="
poetry run pytest tests/unit/ -v --tb=short

echo ""
echo "=== ROLLBACK COMPLETE ==="
echo "Completed: $(date)"
echo "System restored to baseline state"