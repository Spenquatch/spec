import sys

sys.path.append("/workspace")

from pathlib import Path

from spec_cli.utils.validation.detection_accuracy_validator import (
    SingletonPattern,
    validate_detection_accuracy,
)

try:
    # Create exactly 95% accuracy scenario: 19 true positives, 1 false negative
    detected_patterns = [
        SingletonPattern(
            file_path=Path(f"test_{i}.py"),
            pattern_type="class_singleton",
            line_number=10,
            confidence_score=0.85,
            description=f"Pattern {i}"
        )
        for i in range(19)  # 19 detected patterns
    ]

    # 20 known patterns (19 matching + 1 false negative)
    known_patterns = [f"test_{i}.py:10" for i in range(19)] + ["missed.py:15"]

    # Run edge case validation
    accuracy_report = validate_detection_accuracy(
        detected_patterns,
        known_patterns,
        0.95  # Exactly at threshold
    )

    print("SUCCESS:Edge case validation completed")
    print(f"Accuracy: {accuracy_report.accuracy_percentage:.3f}")
    print(f"Threshold met: {accuracy_report.accuracy_threshold_met}")
    print(f"Validation passed: {accuracy_report.validation_passed}")
    print(f"True positives: {accuracy_report.true_positives}")
    print(f"False negatives: {accuracy_report.false_negatives}")

    # Verify exact threshold behavior
    if accuracy_report.accuracy_percentage == 0.95:
        print("EDGE_CASE_VERIFIED:Exactly at 95% threshold")

except Exception as e:
    print(f"ERROR:{e}")
    import traceback
    traceback.print_exc()
