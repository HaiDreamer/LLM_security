
"""Validation utilities for the Vietnamese Attack Dataset seed cases.

Schema reference:
    docs/data_dictionary_v0.1.md

This module validates JSONL records against the Seed Case scope,
using the I1-I7 definitions from the Seed Case section only.
"""

import json
from pathlib import Path
from typing import Any


# Fields defined by data_dictionary_v0.1.md.
# The snake_case JSON keys are a proposed naming convention because
# the dictionary does not explicitly define the serialized key names.
REQUIRED_FIELDS = {
    "case_id",
    "threat_category",
    "attack_intent",
    "language_variant",
    "modality",
    "prompt_form",
    "communication_style",
    "ambiguity_level",
    "deployment_context",
    "prompt",
    "expected_policy_behavior",
}

# Allowed threat categories in the Seed Case scope.
ALLOWED_CATEGORIES = {
    "Direct prompt injection",
    "Jailbreaking",
}

# Attack-intent mapping from the Seed Case section.
# Do not replace this mapping with the Full version mapping.
VALID_INTENTS_BY_CATEGORY = {
    "Direct prompt injection": {"I1", "I2", "I3", "I5", "I6"},
    "Jailbreaking": {"I4", "I5"},
}

ALLOWED_VALUES = {
    "language_variant": {"Vietnamese"},
    "modality": {"Text-only"},
    "prompt_form": {"Direct"},
    "communication_style": {"Neutral"},
    "ambiguity_level": {"Low", "Medium", "High"},
    "deployment_context": {"Standalone"},
    "expected_policy_behavior": {"Refuse"},
}


def load_jsonl(
    file_path: str | Path,
) -> tuple[list[dict[str, Any]], list[int], list[str]]:
    path = Path(file_path)
    records: list[dict[str, Any]] = []
    line_numbers: list[int] = []
    errors: list[str] = []

    if not path.exists():
        return [], [], [f"File not found: {path}"]

    if not path.is_file():
        return [], [], [f"Path is not a file: {path}"]

    try:
        with path.open("r", encoding="utf-8") as file:
            for line_number, raw_line in enumerate(file, start=1):
                # Ignore blank lines; they are not counted as records.
                if not raw_line.strip():
                    continue

                try:
                    record = json.loads(raw_line)
                except json.JSONDecodeError as exc:
                    errors.append(
                        f"Line {line_number}: invalid JSON "
                        f"(column {exc.colno}: {exc.msg})"
                    )
                    continue

                if not isinstance(record, dict):
                    errors.append(
                        f"Line {line_number}: expected a JSON object."
                    )
                    continue

                records.append(record)
                line_numbers.append(line_number)

    except UnicodeDecodeError as exc:
        errors.append(f"File is not valid UTF-8: {exc}")

    except OSError as exc:
        errors.append(f"Could not read file: {exc}")

    return records, line_numbers, errors


def validate_record(
    record: dict[str, Any],
    line_number: int,
) -> list[str]:
    """Validate one record against the Seed Case schema."""
    errors: list[str] = []

    # Check required fields.
    missing_fields = REQUIRED_FIELDS - record.keys()

    for field in sorted(missing_fields):
        errors.append(
            f"Line {line_number}: missing required field '{field}'."
        )

    # Check string fields when present.
    string_fields = REQUIRED_FIELDS

    for field in sorted(string_fields & record.keys()):
        value = record[field]

        if not isinstance(value, str):
            errors.append(
                f"Line {line_number}: '{field}' must be a string."
            )
        elif not value.strip():
            errors.append(
                f"Line {line_number}: '{field}' must not be empty."
            )

    # Check the unique identifier format at the basic level.
    # The dictionary requires uniqueness but does not define an ID pattern.
    case_id = record.get("case_id")

    if isinstance(case_id, str) and case_id.strip():
        pass  # Uniqueness is checked across the full dataset below.

    # Check allowed categorical values.
    for field, allowed_values in ALLOWED_VALUES.items():
        value = record.get(field)

        if field in record and isinstance(value, str):
            if value not in allowed_values:
                allowed_text = ", ".join(sorted(allowed_values))
                errors.append(
                    f"Line {line_number}: invalid '{field}' value "
                    f"{value!r}. Allowed values: {allowed_text}."
                )

    # Check threat category and attack-intent compatibility.
    category = record.get("threat_category")
    intent = record.get("attack_intent")

    if isinstance(category, str):
        if category not in ALLOWED_CATEGORIES:
            allowed_text = ", ".join(sorted(ALLOWED_CATEGORIES))
            errors.append(
                f"Line {line_number}: invalid 'threat_category' "
                f"value {category!r}. Allowed values: {allowed_text}."
            )
        elif isinstance(intent, str):
            valid_intents = VALID_INTENTS_BY_CATEGORY[category]

            if intent not in valid_intents:
                allowed_text = ", ".join(sorted(valid_intents))
                errors.append(
                    f"Line {line_number}: attack intent {intent!r} "
                    f"is not valid for category {category!r}. "
                    f"Allowed intents: {allowed_text}."
                )

    return errors


def validate_records(
    records: list[dict[str, Any]],
    line_numbers: list[int] | None = None,
) -> list[str]:
    """Validate all records, including dataset-wide ID uniqueness."""
    errors: list[str] = []

    if line_numbers is None:
        line_numbers = list(range(1, len(records) + 1))

    if len(line_numbers) != len(records):
        raise ValueError(
            "line_numbers must have the same length as records."
        )

    seen_ids: dict[str, int] = {}

    for record, line_number in zip(records, line_numbers):
        errors.extend(validate_record(record, line_number))

        case_id = record.get("case_id")

        if isinstance(case_id, str) and case_id.strip():
            if case_id in seen_ids:
                errors.append(
                    f"Line {line_number}: duplicate case_id "
                    f"{case_id!r}; first seen on line "
                    f"{seen_ids[case_id]}."
                )
            else:
                seen_ids[case_id] = line_number

    return errors
