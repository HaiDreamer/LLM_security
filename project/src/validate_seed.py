
"""Validation utilities for the Vietnamese Attack Dataset seed cases.

Schema reference:
    docs/data_dictionary_v0.1.md

This module validates JSONL records against the Seed Case scope,
using the I1-I7 definitions from the Seed Case section only.

Lingua is used to screen prompt content for language mismatches.
Automatic language detection cannot guarantee that every word
in a prompt is Vietnamese.
"""

import json
import re
from pathlib import Path
from typing import Any

from lingua import Language, LanguageDetectorBuilder


# Restrict language detection to Vietnamese and English.
# Other detected languages are outside the intended dataset scope.
LANGUAGE_DETECTOR = (
    LanguageDetectorBuilder
    .from_languages(
        Language.VIETNAMESE,
        Language.ENGLISH,
    )
    .build()
)


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

ALLOWED_CATEGORIES = {
    "Direct prompt injection",
    "Jailbreaking",
}

# Use the I1-I7 mapping from the Seed Case section only.
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
    """Load JSON objects from a JSONL file."""
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


def validate_prompt_language(
    prompt: str,
    line_number: int,
) -> tuple[list[str], list[str]]:
    """Screen prompt text for English or uncertain language segments.

    Returns:
        A tuple containing (errors, warnings).

    Longer segments detected as English are errors.
    Short or uncertain segments are warnings requiring review.
    """
    errors: list[str] = []
    warnings: list[str] = []

    text = prompt.strip()

    if not text:
        return errors, warnings

    # Split on sentence-ending punctuation before detection.
    # This can help identify English sentences inside longer prompts.
    segments = re.split(r"(?<=[.!?。！？])\s+", text)

    for segment in segments:
        segment = segment.strip()

        if not any(char.isalpha() for char in segment):
            continue

        word_count = len(re.findall(r"\b\w+\b", segment, flags=re.UNICODE))

        # Short segments are often unreliable for language detection.
        if word_count < 4:
            warnings.append(
                f"Line {line_number}: language review required "
                f"for short segment {segment!r}."
            )
            continue

        try:
            detections = LANGUAGE_DETECTOR.detect_multiple_languages_of(
                segment
            )
        except (ValueError, RuntimeError) as exc:
            warnings.append(
                f"Line {line_number}: language detection failed "
                f"for segment {segment!r}: {exc}"
            )
            continue

        if not detections:
            warnings.append(
                f"Line {line_number}: unable to identify language "
                f"for segment {segment!r}."
            )
            continue

        # Inspect the detected language spans within this segment.
        for detection in detections:
            detected_text = segment[
                detection.start_index:detection.end_index
            ].strip()

            if not detected_text:
                continue

            detected_word_count = len(
                re.findall(r"\b\w+\b", detected_text, flags=re.UNICODE)
            )

            if detection.language == Language.VIETNAMESE:
                continue

            if detection.language == Language.ENGLISH:
                message = (
                    f"Line {line_number}: possible English segment "
                    f"{detected_text!r}."
                )

                if detected_word_count >= 3:
                    errors.append(
                        message + " Expected Vietnamese only."
                    )
                else:
                    warnings.append(
                        message + " Manual review required."
                    )

    # Remove duplicate messages while preserving order.
    errors = list(dict.fromkeys(errors))
    warnings = list(dict.fromkeys(warnings))

    return errors, warnings


def validate_record(
    record: dict[str, Any],
    line_number: int,
) -> tuple[list[str], list[str]]:
    """Validate one record and return (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    # Check required fields.
    missing_fields = REQUIRED_FIELDS - record.keys()

    for field in sorted(missing_fields):
        errors.append(
            f"Line {line_number}: missing required field '{field}'."
        )

    # Reject fields not defined in the schema.
    extra_fields = record.keys() - REQUIRED_FIELDS

    for field in sorted(extra_fields):
        errors.append(
            f"Line {line_number}: unexpected field '{field}'."
        )

    # Check required fields are non-empty strings.
    for field in sorted(REQUIRED_FIELDS & record.keys()):
        value = record[field]

        if not isinstance(value, str):
            errors.append(
                f"Line {line_number}: '{field}' must be a string."
            )
        elif not value.strip():
            errors.append(
                f"Line {line_number}: '{field}' must not be empty."
            )

    # Check allowed categorical values.
    for field, allowed_values in ALLOWED_VALUES.items():
        value = record.get(field)

        if isinstance(value, str) and value.strip():
            if value not in allowed_values:
                allowed_text = ", ".join(sorted(allowed_values))
                errors.append(
                    f"Line {line_number}: invalid '{field}' value "
                    f"{value!r}. Allowed values: {allowed_text}."
                )

    # Check threat category and attack-intent compatibility.
    category = record.get("threat_category")
    intent = record.get("attack_intent")

    if isinstance(category, str) and category.strip():
        if category not in ALLOWED_CATEGORIES:
            allowed_text = ", ".join(sorted(ALLOWED_CATEGORIES))
            errors.append(
                f"Line {line_number}: invalid 'threat_category' "
                f"value {category!r}. Allowed values: {allowed_text}."
            )
        elif isinstance(intent, str) and intent.strip():
            valid_intents = VALID_INTENTS_BY_CATEGORY[category]

            if intent not in valid_intents:
                allowed_text = ", ".join(sorted(valid_intents))
                errors.append(
                    f"Line {line_number}: attack intent {intent!r} "
                    f"is not valid for category {category!r}. "
                    f"Allowed intents: {allowed_text}."
                )

    # Check actual prompt content, not only language metadata.
    prompt = record.get("prompt")

    if isinstance(prompt, str) and prompt.strip():
        language_errors, language_warnings = validate_prompt_language(
            prompt,
            line_number,
        )
        errors.extend(language_errors)
        warnings.extend(language_warnings)

    return errors, warnings


def validate_records(
    records: list[dict[str, Any]],
    line_numbers: list[int] | None = None,
) -> tuple[list[str], list[str]]:
    """Validate all records and dataset-wide ID uniqueness.

    Returns:
        A tuple containing (errors, warnings).
    """
    errors: list[str] = []
    warnings: list[str] = []

    if line_numbers is None:
        line_numbers = list(range(1, len(records) + 1))

    if len(line_numbers) != len(records):
        raise ValueError(
            "line_numbers must have the same length as records."
        )

    seen_ids: dict[str, int] = {}

    for record, line_number in zip(records, line_numbers):
        record_errors, record_warnings = validate_record(
            record,
            line_number,
        )
        errors.extend(record_errors)
        warnings.extend(record_warnings)

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

    return errors, warnings
