import sys
sys.path.append("/workspace")

from pathlib import Path
from slice_3_4_accuracy_validation import generate_accuracy_validation_report, SingletonBaseline
from spec_cli.utils.validation.detection_accuracy_validator import AccuracyReport

try:
    # Create complete baseline for report generation
    accuracy_report = AccuracyReport(
        true_positives=4,
        false_positives=1,
        false_negatives=1,
        total_known_patterns=5,
        total_detected_patterns=5,
        precision=0.8,
        recall=0.8,
        f1_score=0.8,
        accuracy_percentage=0.96,
        validation_passed=True,
        accuracy_threshold_met=True,
        false_positive_details=[{"file_path": "fp.py", "issue": "Not singleton"}],
        false_negative_details=[{"file_path": "fn.py", "issue": "Missed pattern"}],
        baseline_approved=True
    )
    
    baseline = SingletonBaseline(
        total_patterns=5,
        validated_patterns=[
            {
                "file_path": "test1.py",
                "line_number": 10,
                "pattern_type": "class_singleton",
                "validation_status": "validated"
            }
        ],
        accuracy_report=accuracy_report,
        completeness_metrics={
            "completeness_score": 0.92,
            "baseline_ready": True,
            "approval_criteria": {"accuracy_approved": True}
        },
        migration_readiness=True,
        baseline_timestamp="2024-01-01T10:00:00",
        approval_status=True
    )
    
    # Generate report with real file output
    output_path = Path("/workspace/test_results/validation_report.json")
    report = generate_accuracy_validation_report(baseline, output_path)
    
    print(f"SUCCESS:Report generation completed")
    print(f"Report sections: {list(report.keys())}")
    print(f"Output file exists: {output_path.exists()}")
    baseline_approved = report["validation_summary"]["baseline_approved"]
    print(f"Baseline approved in report: {baseline_approved}")
    
    # Verify file content
    if output_path.exists():
        with open(output_path, "r") as f:
            import json
            saved_report = json.load(f)
            validation_passed = saved_report["validation_summary"]["validation_passed"]
        print(f"Saved report validation summary: {validation_passed}")
    
except Exception as e:
    print(f"ERROR:{e}")
    import traceback
    traceback.print_exc()
