
"""Command-line entry point for validating the seed-case JSONL dataset."""

import argparse
import sys
from pathlib import Path

# Allow running this script directly from the repository root.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from project.src.validate_seed import load_jsonl, validate_records


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a seed-case dataset stored in JSONL format."
    )
    parser.add_argument(
        "jsonl_path",
        nargs="?",
        default=PROJECT_ROOT
        / "datasets"
        / "raw"
        / "seed_cases_v0.1.jsonl",
        help="Path to the JSONL file dataset to validate.",
    )
    args = parser.parse_args()

    jsonl_path = Path(args.jsonl_path)

    records, line_numbers, load_errors = load_jsonl(jsonl_path)

    # Stop if the file cannot be loaded or contains invalid JSONL records.
    if load_errors:
        print("DATASET LOADING FAILED")
        print(f"Input file: {jsonl_path}")
        for error in load_errors:
            print(f"ERROR: {error}")
        return 1

    # Validate records and collect both errors and language-review warnings.
    validation_errors, validation_warnings = validate_records(
        records, line_numbers
    )

    # Count IDs only when they are non-empty strings.
    valid_ids = [
        record.get("case_id")
        for record in records
        if isinstance(record.get("case_id"), str)
        and record["case_id"].strip()
    ]
    unique_ids = len(set(valid_ids))

    print("SEED DATASET VALIDATION")
    print(f"Input file: {jsonl_path}")
    print(f"Records loaded: {len(records)}")
    print(f"Non-empty case IDs: {len(valid_ids)}")
    print(f"Unique case IDs: {unique_ids}")
    print(f"Validation errors: {len(validation_errors)}")
    print(f"Validation warnings: {len(validation_warnings)}")

    if validation_errors:
        print("\nValidation errors:")
        for error in validation_errors:
            print(f"- {error}")

    if validation_warnings:
        print("\nItems requiring manual review:")
        for warning in validation_warnings:
            print(f"- {warning}")

    # Errors fail validation. Warnings require human review.
    if validation_errors:
        print("\nRESULT: FAILED")
        return 1

    if validation_warnings:
        print("\nRESULT: REVIEW REQUIRED")
        return 2

    print("\nRESULT: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
