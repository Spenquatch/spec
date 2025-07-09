#!/bin/bash

echo "======================================"
echo "DEPENDENCY INJECTION MIGRATION MONITOR"
echo "======================================"

# Check for singleton patterns
echo "=== SINGLETON PATTERN CHECK ==="
echo "SettingsManager references:"
grep -r "SettingsManager" spec_cli/ | grep -v backup | grep -v ".pyc" | grep -v "__pycache__" | wc -l

echo "ConsoleManager references:"
grep -r "ConsoleManager" spec_cli/ | grep -v backup | grep -v ".pyc" | grep -v "__pycache__" | wc -l

echo "Module-level cache references:"
grep -r "_console_cache" spec_cli/ | grep -v backup | grep -v ".pyc" | grep -v "__pycache__" | wc -l

echo "Legacy getter calls:"
echo "  get_settings(): $(grep -r "get_settings(" spec_cli/ | grep -v backup | grep -v ".pyc" | grep -v "__pycache__" | wc -l)"
echo "  get_console(): $(grep -r "get_console(" spec_cli/ | grep -v backup | grep -v ".pyc" | grep -v "__pycache__" | wc -l)"
echo "  get_progress_manager(): $(grep -r "get_progress_manager(" spec_cli/ | grep -v backup | grep -v ".pyc" | grep -v "__pycache__" | wc -l)"

echo ""
echo "=== ARCHITECTURE CONSISTENCY CHECK ==="
echo "SpecContext usage: $(grep -r "SpecContext" spec_cli/ | grep -v backup | grep -v ".pyc" | grep -v "__pycache__" | wc -l)"
echo "Context injection decorators: $(grep -r "@context_injection" spec_cli/ | grep -v backup | grep -v ".pyc" | grep -v "__pycache__" | wc -l)"

echo ""
echo "=== LAST VALIDATION STATUS ==="
if [ -f validation_results.txt ]; then
    tail -10 validation_results.txt
else
    echo "No validation results found"
fi