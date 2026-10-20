
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
        help="Path to the JSONL file dataset to validate.",
        default=PROJECT_ROOT / "datasets" / "raw" / "data_dictionary_v0.1.jsonl",
    )
    args = parser.parse_args()

    records, line_numbers, load_errors = load_jsonl(args.jsonl_path)

    if load_errors:
        print("DATASET LOADING FAILED")
        for error in load_errors:
            print(f"ERROR: {error}")
        return 1

    validation_errors = validate_records(records, line_numbers)

    # Count IDs only when they are non-empty strings.
    valid_ids = [
        record.get("case_id")
        for record in records
        if isinstance(record.get("case_id"), str)
        and record["case_id"].strip()
    ]
    unique_ids = len(set(valid_ids))

    print("SEED DATASET VALIDATION")
    print(f"Input file: {args.jsonl_path}")
    print(f"Records loaded: {len(records)}")
    print(f"Non-empty case IDs: {len(valid_ids)}")
    print(f"Unique case IDs: {unique_ids}")
    print(f"Validation errors: {len(validation_errors)}")

    if validation_errors:
        print("\nValidation details:")
        for error in validation_errors:
            print(f"- {error}")
        print("\nRESULT: FAILED")
        return 1

    print("\nRESULT: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
