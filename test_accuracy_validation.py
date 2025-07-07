import sys
sys.path.append("/workspace")

from pathlib import Path
from slice_3_4_accuracy_validation 

# Define real known patterns based on our test files (unique locations only)
known_patterns = [
    "/workspace/test_data/accuracy_validation/user_service.py:10",     # UserService with SingletonMeta metaclass
    "/workspace/test_data/accuracy_validation/config_manager.py:12",   # @singleton decorator on ConfigManager 
    "/workspace/test_data/accuracy_validation/database_connection.py:3", # import statements (multiple violations on same line)
    "/workspace/test_data/accuracy_validation/database_connection.py:5", # DatabaseConnection with SingletonMeta metaclass
]

try:
    # First debug: see what patterns are actually detected
    from spec_cli.utils.singleton_detection 
    
    print("DEBUG: Scanning for patterns in test files...")
    detected_debug = []
    target_dir = Path("/workspace/test_data/accuracy_validation")
    for python_file in target_dir.glob("**/*.py"):
        violations = scan_for_singleton_patterns(python_file)
        for v in violations:
            pattern_id = f"{v.file_path.name}:{v.line_number}"
            detected_debug.append(pattern_id)
            print(f"  Detected: {pattern_id} - {v.pattern_type} - {v.description}")
    
    print(f"DEBUG: Total detected patterns: {len(detected_debug)}")
    print(f"DEBUG: Known patterns: {known_patterns}")
    print("")
    
    # Run real accuracy validation
    accuracy_report = validate_singleton_detection_accuracy(
        target_dir, 
        known_patterns, 
        0.95
    )
    
    print(f"SUCCESS:Accuracy validation completed")
    print(f"True Positives: {accuracy_report.true_positives}")
    print(f"False Positives: {accuracy_report.false_positives}")
    print(f"False Negatives: {accuracy_report.false_negatives}")
    print(f"Accuracy Percentage: {accuracy_report.accuracy_percentage:.3f}")
    print(f"Validation Passed: {accuracy_report.validation_passed}")
    print(f"Threshold Met: {accuracy_report.accuracy_threshold_met}")
    
except Exception as e:
    print(f"ERROR:{e}")
    import traceback
    traceback.print_exc()
