import sys

sys.path.append("/workspace")

from pathlib import Path

from slice_3_4_accuracy_validation 

# Define real known patterns based on our test files
known_patterns = [
    "test_data/accuracy_validation/user_service.py:8",      # UserService.__new__
    "test_data/accuracy_validation/config_manager.py:6",   # ConfigManager.__new__
    "test_data/accuracy_validation/database_connection.py:5", # get_connection function
    "test_data/accuracy_validation/missed_singleton.py:10"    # This will be false negative
]

try:
    # Run real accuracy validation
    target_dir = Path("/workspace/test_data/accuracy_validation")
    accuracy_report = validate_singleton_detection_accuracy(
        target_dir,
        known_patterns,
        0.95
    )

    print("SUCCESS:Accuracy validation completed")
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
